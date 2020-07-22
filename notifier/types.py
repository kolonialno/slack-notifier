from typing import Literal, Optional, TypedDict


class MessageAttachment(TypedDict, total=False):
    text: str
    mrkdwn: bool
    author_name: str
    author_icon: str
    author_link: str
    color: Literal["danger", "warning", "good"]
    footer: Optional[str]
