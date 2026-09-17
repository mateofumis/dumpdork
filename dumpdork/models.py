"""Small, provider-independent search types."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class SearchRequest:
    source: str
    query: str
    limit: int = 50
    github_type: Literal["repo", "code"] | None = None
    include_commits: bool = False
    capture_raw: bool = False
    provider_type: str | None = None
    provider_options: dict[str, Any] = field(default_factory=dict)
    paginate: bool = False


@dataclass
class SearchResult:
    source: str
    kind: Literal["web", "repository", "file", "news", "image", "video", "discussion", "faq", "location"]
    url: str
    title: str
    snippet: str | None
    matched_query: str
    observed_at: str
    repository: str | None = None
    path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchFailure:
    type: str
    message: str
    retry_at: str | None = None


@dataclass
class SearchRun:
    source: str
    query: str
    requested_limit: int
    search_type: str | None = None
    results: list[SearchResult] = field(default_factory=list)
    status: Literal["success", "partial", "error"] = "success"
    total_count: int | None = None
    incomplete: bool = False
    warnings: list[str] = field(default_factory=list)
    error: SearchFailure | None = None
    raw_pages: list[dict[str, Any]] = field(default_factory=list, repr=False)
    effective_query: str | None = None

    def fail(self, failure: SearchFailure) -> None:
        self.error = failure
        self.status = "partial" if self.results else "error"


def new_run(request: SearchRequest) -> SearchRun:
    return SearchRun(
        source=request.source,
        query=request.query,
        requested_limit=request.limit,
        search_type=request.github_type if request.source == "github" else request.provider_type,
    )
