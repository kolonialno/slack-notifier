import os
import re
from typing import Generator

import httpx

REPO_RE = re.compile(r"[^\/]+\/[^\/]+")


def is_valid_repo(value: str) -> bool:
    return bool(REPO_RE.fullmatch(value))


class GithubAuth(httpx.Auth):
    def __init__(self, token: str) -> None:
        self.token = token

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


async def get_commit(*, repo: str, ref: str) -> httpx.Response:

    assert is_valid_repo(repo), "The repo argument must be on the <owner>/<name> format"

    async with httpx.AsyncClient(
        auth=GithubAuth(token=os.environ["GITHUB_TOKEN"])
    ) as client:
        return await client.get(f"https://api.github.com/repos/{repo}/commits/{ref}")


async def get_commit_statuses(*, repo: str, ref: str) -> httpx.Response:

    assert is_valid_repo(repo), "The repo argument must be on the <owner>/<name> format"

    async with httpx.AsyncClient(
        auth=GithubAuth(token=os.environ["GITHUB_TOKEN"])
    ) as client:
        return await client.get(
            f"https://api.github.com/repos/{repo}/commits/{ref}/statuses"
        )


async def get_commit_checks(*, repo: str, ref: str) -> httpx.Response:

    assert is_valid_repo(repo), "The repo argument must be on the <owner>/<name> format"

    async with httpx.AsyncClient(
        auth=GithubAuth(token=os.environ["GITHUB_TOKEN"])
    ) as client:
        return await client.get(
            f"https://api.github.com/repos/{repo}/commits/{ref}/check-runs",
            headers={"accept": "application/vnd.github.antiope-preview+json"},
        )
