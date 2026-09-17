"""GitHub repository and legacy REST code search."""

import re
from urllib.parse import quote

import requests

from ..errors import ProviderError, _retry_at, request_json
from ..models import SearchRequest, SearchResult, SearchRun, new_run, utc_now


API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"


class GitHubProvider:
    def __init__(self, session: requests.Session, token: str | None):
        self.session = session
        self.token = token

    def _headers(self, code: bool = False) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.text-match+json" if code else "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "DumpDork",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def search(self, request: SearchRequest) -> SearchRun:
        run = new_run(request)
        if request.github_type not in ("repo", "code"):
            run.fail(ProviderError("invalid_query", "Choose --github-type repo or code.").failure)
            return run
        if request.github_type == "code" and not self.token:
            run.fail(ProviderError("authentication", "GitHub code search requires GITHUB_TOKEN or a saved token.").failure)
            return run
        if request.github_type == "code" and re.search(r"(?:^|\s)content:", request.query):
            run.fail(ProviderError("invalid_query", "GitHub REST code search uses legacy syntax; use in:file instead of content:.").failure)
            return run

        endpoint = "code" if request.github_type == "code" else "repositories"
        page = 1
        seen_urls: set[str] = set()
        while len(run.results) < min(request.limit, 1000) and page <= 10:
            page_size = min(100, request.limit - len(run.results), 1000 - len(run.results))
            try:
                data, response = request_json(
                    self.session,
                    f"{API_URL}/search/{endpoint}",
                    source="github",
                    params={"q": request.query, "per_page": page_size, "page": page},
                    headers=self._headers(code=request.github_type == "code"),
                )
                if request.capture_raw:
                    run.raw_pages.append(data)
                items = data.get("items")
                if not isinstance(items, list):
                    raise ProviderError("malformed_response", "GitHub returned invalid search results.")
                if isinstance(data.get("total_count"), int):
                    run.total_count = data["total_count"]
                run.incomplete = run.incomplete or data.get("incomplete_results") is True

                added = 0
                valid = 0
                for item in items:
                    result = self._normalize(item, request)
                    if result is None:
                        run.warnings.append("Skipped an invalid GitHub search result.")
                        continue
                    valid += 1
                    if result.url in seen_urls:
                        continue
                    seen_urls.add(result.url)
                    run.results.append(result)
                    added += 1
                    if len(run.results) >= request.limit:
                        break

                if response.headers.get("X-RateLimit-Remaining") == "0":
                    run.warnings.append(f"GitHub search rate limit exhausted; retry after {_retry_at(response) or 'the provider reset'}.")
                    if len(run.results) < request.limit and items:
                        run.fail(ProviderError("rate_limit", "GitHub search rate limit exhausted.", _retry_at(response)).failure)
                        break
                if items and valid == 0:
                    raise ProviderError("malformed_response", "GitHub returned results without usable URLs.")
                if items and added == 0:
                    run.warnings.append("Stopped after GitHub repeated a page of results.")
                    break
                if not items or len(run.results) >= request.limit:
                    break
                if run.total_count is not None and page * page_size >= min(run.total_count, 1000):
                    break
                if len(items) < page_size:
                    break
                page += 1
            except ProviderError as exc:
                run.fail(exc.failure)
                break

        if request.limit > 1000 and run.total_count and run.total_count > 1000:
            run.incomplete = True
            run.warnings.append("GitHub exposes at most 1,000 results for one search.")
        if run.incomplete:
            run.warnings.append("GitHub marked these search results as incomplete.")
        if request.include_commits and run.results and (run.error is None or run.error.type not in ("rate_limit", "quota")):
            self._add_commits(run)
        return run

    def _normalize(self, item: object, request: SearchRequest) -> SearchResult | None:
        if not isinstance(item, dict):
            return None
        url = item.get("html_url")
        if not isinstance(url, str) or not url:
            return None
        code = request.github_type == "code"
        repository = item.get("repository") if code else item
        if not isinstance(repository, dict):
            return None
        repo_name = repository.get("full_name")
        if not isinstance(repo_name, str) or not repo_name:
            return None
        owner = repository.get("owner") or {}
        owner_name = owner.get("login") if isinstance(owner, dict) else None
        metadata = {"owner": owner_name} if isinstance(owner_name, str) else {}
        if code:
            path = item.get("path") if isinstance(item.get("path"), str) else None
            matches = item.get("text_matches") or []
            fragment = next(
                (match.get("fragment") for match in matches if isinstance(match, dict) and isinstance(match.get("fragment"), str)),
                None,
            ) if isinstance(matches, list) else None
            if isinstance(item.get("sha"), str):
                metadata["sha"] = item["sha"]
            return SearchResult(
                source="github", kind="file", url=url, title=path or str(item.get("name") or url),
                snippet=fragment, matched_query=request.query, observed_at=utc_now(),
                repository=repo_name, path=path, metadata=metadata,
            )
        for key in ("stargazers_count", "updated_at", "language"):
            if isinstance(item.get(key), (str, int)):
                metadata[key] = item[key]
        return SearchResult(
            source="github", kind="repository", url=url, title=repo_name,
            snippet=item.get("description") if isinstance(item.get("description"), str) else None,
            matched_query=request.query, observed_at=utc_now(), repository=repo_name, metadata=metadata,
        )

    def _add_commits(self, run: SearchRun) -> None:
        by_repo: dict[str, list[SearchResult]] = {}
        for result in run.results:
            if result.repository:
                by_repo.setdefault(result.repository, []).append(result)
        for repo, results in by_repo.items():
            try:
                data, _ = self._commits(repo)
            except ProviderError as exc:
                run.warnings.append(f"Recent commits unavailable for {repo}: {exc.failure.type}.")
                if exc.failure.type in ("rate_limit", "quota"):
                    break
                continue
            commits = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                info = item.get("commit") or {}
                if not isinstance(info, dict):
                    continue
                author = info.get("author") or {}
                commits.append({
                    "message": str(info.get("message") or "").splitlines()[0] if info.get("message") else "",
                    "date": author.get("date") if isinstance(author, dict) else None,
                    "url": item.get("html_url"),
                })
            for result in results:
                result.metadata["recent_commits"] = commits

    def _commits(self, repo: str) -> tuple[list, requests.Response]:
        # request_json expects a mapping; commit lists use the same HTTP rules.
        url = f"{API_URL}/repos/{quote(repo, safe='/')}/commits"
        try:
            response = self.session.get(url, params={"per_page": 3}, headers=self._headers(), timeout=(5, 20))
        except requests.RequestException as exc:
            raise ProviderError("network", "Network failure while fetching GitHub commits.") from exc
        if response.status_code != 200:
            limited = response.status_code == 429 or (
                response.status_code == 403 and (
                    response.headers.get("X-RateLimit-Remaining") == "0" or bool(response.headers.get("Retry-After"))
                )
            )
            raise ProviderError("rate_limit" if limited else "provider_error", "GitHub commit lookup failed.", _retry_at(response))
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError("malformed_response", "GitHub returned invalid commit JSON.") from exc
        if not isinstance(data, list):
            raise ProviderError("malformed_response", "GitHub returned invalid commit results.")
        return data, response
