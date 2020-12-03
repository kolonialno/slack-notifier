import asyncio
from typing import AsyncIterable

import httpx
import logging
from .github import CommitStatus, GithubClient

logger = logging.getLogger(__name__)


async def status_updates(
    *, repo: str, commit: str, poll_interval: int = 1, timeout: int
) -> AsyncIterable[CommitStatus]:

    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout

    async with GithubClient(repo=repo) as client:
        previous_status = None

        while True:
            try:
                status = await client.get_commit_status(ref=commit)
                if previous_status is None or status != previous_status:
                    yield status

                if loop.time() >= deadline or status.is_done:
                    return

                previous_status = status
            except httpx.HTTPError:
                logger.exception('HTTP request towards Github failed')

            time_to_sleep = min(poll_interval, max(deadline - loop.time(), 0))
            await asyncio.sleep(time_to_sleep)
