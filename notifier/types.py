from __future__ import annotations

import dataclasses
from typing import List, Literal, Optional, Sequence, TypedDict


class MessageAttachment(TypedDict, total=False):
    text: str
    mrkdwn: bool
    author_name: str
    author_icon: str
    author_link: str
    color: Literal["danger", "warning", "good"]
    footer: Optional[str]


#
# Github response:
# /repos/<owner>/<name>/commits/<ref>
#


@dataclasses.dataclass(frozen=True, eq=True)
class CommitPayload:
    sha: str
    html_url: str
    commit: _Commit
    author: _Author


@dataclasses.dataclass(frozen=True, eq=True)
class _Commit:
    message: str


@dataclasses.dataclass(frozen=True, eq=True)
class _Author:
    login: str
    avatar_url: str


#
# Github response:
# /repos/<owner>/<name>/commits/<ref>/status
#


@dataclasses.dataclass(frozen=True, eq=True)
class CommitStatusPayload:
    statuses: List[_Status]


@dataclasses.dataclass(frozen=True, eq=True)
class _Status:
    id: int
    target_url: str
    context: str
    state: str
    description: str


#
# Github response:
# /repos/<owner>/<name>/commits/<ref>/check-runs
#


@dataclasses.dataclass(frozen=True, eq=True)
class CheckRunsPayload:
    check_runs: List[_CheckRun]


@dataclasses.dataclass(frozen=True, eq=True)
class _CheckRun:
    id: int
    name: str
    html_url: str
    status: str
    conclusion: Optional[str]
    output: _CheckRunOutput


@dataclasses.dataclass(frozen=True, eq=True)
class _CheckRunOutput:
    title: Optional[str]
    summary: Optional[str]


#
# Parsed commit status
#


@dataclasses.dataclass(frozen=True, eq=True)
class Author:
    login: str
    avatar_url: str


@dataclasses.dataclass(frozen=True, eq=True)
class CheckStatus:
    name: str
    summary: str
    finished: bool
    success: Optional[bool] = None


@dataclasses.dataclass(frozen=True, eq=True)
class CommitStatus:
    author: Author
    message: str
    url: str
    sha: str
    checks: Sequence[CheckStatus]

    @property
    def is_done(self) -> bool:
        return all(check.finished for check in self.checks)
