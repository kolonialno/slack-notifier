from __future__ import annotations

import asyncio
import os
import re
from types import TracebackType
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, cast

import dacite
import httpx

from .types import (
    Author,
    CheckRunsPayload,
    CheckStatus,
    CommitPayload,
    CommitStatus,
    CommitStatusPayload,
)
from .utils import BearerAuth

E = TypeVar("E", bound=Exception)
T = TypeVar("T")

REPO_RE = re.compile(r"[^\/]+\/[^\/]+")


def is_valid_repo(value: str) -> bool:
    """
    Check if a given value is a valid repo name on the "<owner>/<name>" form
    """

    return bool(REPO_RE.fullmatch(value))


class GithubClient:
    """A simple wrapper around an HTTP client for the Github API"""

    def __init__(self, *, repo: str) -> None:

        self.repo = repo

        # We create the client here, so it's always set
        self.http_client: httpx.AsyncClient = httpx.AsyncClient(
            auth=BearerAuth(token=os.environ["GITHUB_TOKEN"])
        )

        # We cache response payloads from Github when they have an ETag header
        # NOTE: The cache is currently never emptied
        self._response_cache: Dict[str, Tuple[str, Any]] = {}

    ###################
    # Context manager #
    ###################

    async def __aenter__(self) -> GithubClient:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[E]],
        exc_value: Optional[E],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.http_client.aclose()

    ##############
    # Public API #
    ##############

    async def get_commit_status(self, *, ref: str) -> CommitStatus:
        """
        Get the status of a given commit. The returned data is the result of
        merging responses from the commit details, check runs, and commit
        status endpoints.
        """

        base_url = f"https://api.github.com/repos/{self.repo}/commits/{ref}"

        # Fetch data from the three API endpoints in parallel
        commit_data, check_runs_data, status_data = await asyncio.gather(
            self._get(url=base_url, response_type=CommitPayload),
            self._get(
                url=f"{base_url}/check-runs",
                headers={"Accept": "application/vnd.github.antiope-preview+json"},
                response_type=CheckRunsPayload,
            ),
            self._get(url=f"{base_url}/status", response_type=CommitStatusPayload),
        )

        # If we are currently in a Github check run, we need to ignore that
        # check run or we will never finish.
        ignored_check_run = os.environ.get("GITHUB_JOB", None)

        # Transform the fetched data into a useful object
        checks = tuple(
            CheckStatus(
                name=check_run.name,
                summary=check_run.output.summary or "",
                finished=check_run.conclusion is not None,
                success=check_run.conclusion in ("success", "skipped"),
            )
            for check_run in sorted(
                check_runs_data.check_runs, key=lambda check_run: check_run.id
            )
            if check_run.name != ignored_check_run
        ) + tuple(
            CheckStatus(
                name=status.context,
                summary=status.description,
                finished=status.state != "pending",
                success=status.state == "success",
            )
            for status in sorted(
                status_data.statuses, key=lambda status: status.context
            )
        )

        return CommitStatus(
            author=Author(
                login=commit_data.author.login, avatar_url=commit_data.author.avatar_url
            ),
            message=commit_data.commit.message,
            url=commit_data.html_url,
            sha=commit_data.sha,
            checks=checks,
        )

    ####################
    # Internal helpers #
    ####################

    async def _get(
        self, *, url: str, response_type: Type[T], headers: Dict[str, str] = None
    ) -> T:
        """
        Send a request and decode the response to the given dataclass type.

        This also handles caching, as we want to be a good citizen. Github uses
        the ETag header, which we can send with the request.
        """

        # Create a headers dict we can modify
        headers = headers.copy() if headers else {}

        # Check if we have data for this URL cached. If we, we send the ETag
        # with the request to Github. If the data is unchanged Github will
        # reply with a 304 Not Modifier status code.
        etag, cached_data = self._response_cache.get(url, (None, None))
        if cached_data is not None and etag is not None:
            headers["If-None-Match"] = etag

        # Send the request and verify that we got a 2xx or 3xx response.
        response = await self.http_client.get(url, headers=headers)
        response.raise_for_status()

        # Use cached data if the response status was 304 Not Modified
        data = (
            cast(Any, cached_data)
            if response.status_code == httpx.codes.NOT_MODIFIED
            else response.json()
        )

        # If the response contains an ETag header, cache the response data
        if (etag := response.headers.get("ETag", None)) is not None:
            self._response_cache[url] = (etag, data)

        # Decode the received payload to the specified type using dacite
        return dacite.from_dict(data_class=response_type, data=data)
