import functools
from typing import Generator

import httpx


def _color(value: str, *, color_code: str) -> str:
    return f"\033[{color_code}m{value}\033[0m"


red = functools.partial(_color, color_code="91")


class BearerAuth(httpx.Auth):
    """
    A Bearer authenticator.

    Sets the Authorization header to "Bearer <token>" on each request.
    """

    def __init__(self, token: str) -> None:
        self.token = token

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request
