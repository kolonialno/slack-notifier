import os
from typing import Generator, List

import httpx

from .types import MessageAttachment


class SlackAuth(httpx.Auth):
    def __init__(self, token: str) -> None:
        self.token = token

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


async def post_message(
    *,
    channel: str,
    ts: str = None,
    text: str = None,
    attachments: List[MessageAttachment] = None,
    username: str = None,
    icon_emoji: str = None,
    icon_url: str = None,
) -> httpx.Response:

    path = "/api/chat.postMessage" if not ts else "/api/chat.update"

    payload = {
        "channel": channel,
        "username": username,
        "icon_emoji": icon_emoji,
        "icon_url": icon_url,
        "ts": ts,
        "text": text,
        "attachments": attachments,
    }

    async with httpx.AsyncClient(
        auth=SlackAuth(token=os.environ["SLACK_TOKEN"])
    ) as client:
        return await client.post(f"https://slack.com{path}", json=payload)
