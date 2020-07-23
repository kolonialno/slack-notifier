import argparse
import asyncio
import os
import sys
from typing import List, cast

from .checker import status_updates
from .github import is_valid_repo
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
        "--timeout",
        type=int,
        default=30,
        help=(
            "Maximum number of minutes to run before giving up, "
            "defaults to 30 minutes"
        ),
        metavar="<minutes>",
    )

    args = parser.parse_args()

    commit = cast(str, args.commit)
    channel = cast(str, args.channel)
    repo = cast(str, args.repo)
    timeout = cast(int, args.timeout) * 60

    if "SLACK_TOKEN" not in os.environ:
        sys.exit(red("Please set the $SLACK_TOKEN environment variable"))

    if "GITHUB_TOKEN" not in os.environ:
        sys.exit(red("Please set the $GITHUB_TOKEN environment variable"))

    message_ts = None
    async for status in status_updates(repo=repo, commit=commit, timeout=timeout):

        attachments: List[MessageAttachment] = [
            {"text": f"❌ *{check.name}*: {check.summary}", "color": "danger"}
            for check in status.checks
            if check.finished and not check.success
        ]

        is_finished = all(check.finished for check in status.checks)
        is_success = all(check.success for check in status.checks)

        num_checks = len(status.checks)
        num_successful_checks = sum(1 for check in status.checks if check.success)

        summary: MessageAttachment
        commit_color = None
        if is_finished:
            commit_color = "good" if is_success else "danger"
            summary = {
                "text": (
                    "✅ *All checks passed*" if is_success else "⚠️ *Some checks failed*"
                ),
                "color": "good" if is_success else "danger",
                "footer": f"{num_successful_checks}/{num_checks} checks have succeeded",
            }
        else:
            summary = {
                "text": "⏳ *Some checks are pending*",
                "color": "warning",
                "footer": f"{num_successful_checks}/{num_checks} checks have succeeded",
            }

        response = await post_message(
            channel=channel,
            ts=message_ts,
            icon_emoji=":package:",
            attachments=[
                {
                    "text": status.message,
                    "author_name": status.author.login,
                    "author_icon": status.author.avatar_url,
                    "footer": f"Commit: <{status.url}|`{status.sha[:7]}`>",
                    "color": commit_color,  # type: ignore
                },
                *attachments,
                summary,
            ],
        )

        data = response.json()
        message_ts = data["ts"]
        channel = data["channel"]


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()

#    pending_statues: List[MessageAttachment] = [
#        {"text": "❌ *flake8*", "color": "danger"},
#        {
#            "text": "⏳ *Some checks are pending*",
#            "color": "warning",
#            "footer": "1/14 checks have succeeded",
#        },
#    ]
#
#    success_statues: List[MessageAttachment] = [
#        {
#            "text": "✅ *All checks passed*",
#            "color": "good",
#            "footer": "14/14 checks have succeeded",
#        },
#    ]
