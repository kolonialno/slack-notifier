import argparse
import asyncio
import os
import pprint
import sys
from typing import List, Optional, cast

from .github import get_commit, get_commit_checks, get_commit_statuses, is_valid_repo
from .slack import post_message
from .types import MessageAttachment
from .utils import red


def _repo_type(value: str) -> str:
    if not is_valid_repo(value):
        raise argparse.ArgumentTypeError('Invalid repo, must be "<owner>/<name>"')
    return value


async def _main() -> None:

    parser = argparse.ArgumentParser(
        description="Get commit status from the Github API and post Slack messages"
    )

    # Required arguments
    parser.add_argument(
        "--repo",
        type=_repo_type,
        required=True,
        help="Github repo",
        metavar="<owner>/<name>",
    )
    parser.add_argument(
        "--commit",
        required=True,
        help="Commit to post status for",
        metavar="<sha, branch, or tag>",
    )
    parser.add_argument(
        "--channel",
        required=True,
        help="Channel to post to",
        metavar="<channel id or name>",
    )

    # Optional arguments
    parser.add_argument(
        "--message-ts",
        help=(
            "Optional timestamp of the message to update. "
            "If this is specified --channel must be a channel id"
        ),
        metavar="<ts>",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Maximum number of minutes to run before giving up",
        metavar="<minutes>",
    )

    args = parser.parse_args()

    commit = cast(str, args.commit)
    channel = cast(str, args.channel)
    message_ts = cast(Optional[str], args.message_ts)
    repo = cast(str, args.repo)
    timeout = cast(int, args.timeout)

    if "SLACK_TOKEN" not in os.environ:
        sys.exit(red("Please set the $SLACK_TOKEN environment variable"))

    if "GITHUB_TOKEN" not in os.environ:
        sys.exit(red("Please set the $GITHUB_TOKEN environment variable"))

    response = await get_commit(repo=repo, ref=commit)
    commit_data = response.json()  # type: ignore

    commit_url: str = commit_data["html_url"]  # type: ignore
    commit_message: str = commit_data["commit"]["message"]  # type: ignore
    author_image: str = commit_data["author"]["avatar_url"]  # type: ignore
    author_username: str = commit_data["author"]["login"]  # type: ignore

    response = await get_commit_statuses(repo=repo, ref=commit)
    pprint.pprint(response.json())  # type: ignore
    print("")
    print("-" * 80)
    print("")

    response = await get_commit_checks(repo=repo, ref=commit)
    pprint.pprint(response.json())  # type: ignore
    print("")
    print("-" * 80)
    print("")

    pending_statues: List[MessageAttachment] = [
        {"text": "❌ *flake8*", "color": "danger"},
        {
            "text": "⏳ *Some checks are pending*",
            "color": "warning",
            "footer": "1/14 checks have succeeded",
        },
    ]

    success_statues: List[MessageAttachment] = [
        {
            "text": "✅ *All checks passed*",
            "color": "good",
            "footer": "14/14 checks have succeeded",
        },
    ]

    response = await post_message(
        channel=channel,
        ts=message_ts,
        icon_emoji=":package:",
        attachments=[
            {
                "text": commit_message,
                "author_name": author_username,
                "author_icon": author_image,
                "footer": f"Commit: <{commit_url}|`{commit[:7]}`>",
            },
            *pending_statues,
        ],
    )
    pprint.pprint(response.json())  # type: ignore


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
