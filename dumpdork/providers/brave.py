"""Official Brave Search API adapter; GitHub transport stays independent."""

from datetime import date, datetime, timedelta, timezone
import re
import time
from typing import Any

import requests

from ..errors import ProviderError
from ..models import SearchRequest, SearchResult, SearchRun, new_run, utc_now


API_BASE = "https://api.search.brave.com/res/v1"
ENDPOINTS = {"web": "web/search", "news": "news/search", "images": "images/search", "videos": "videos/search"}
MAX_COUNT = {"web": 20, "news": 50, "images": 200, "videos": 50}
COMMON = {"country", "search_lang", "safesearch", "count", "spellcheck"}
PAGED = {"offset", "ui_lang", "freshness", "operators", "include_fetch_metadata"}
PARAMETERS = {
    "web": COMMON | PAGED | {"text_decorations", "result_filter", "units", "goggles", "goggles_id", "extra_snippets", "enable_rich_callback"},
    "news": COMMON | PAGED | {"extra_snippets", "goggles"},
    "images": COMMON,
    "videos": COMMON | PAGED,
}
WEB_SECTIONS = {"web": "web", "news": "news", "videos": "video", "discussions": "discussion", "faq": "faq", "locations": "location"}
FILTER_VALUES = set(WEB_SECTIONS) | {"infobox", "query"}
BOOLEAN_PARAMS = {"spellcheck", "operators", "include_fetch_metadata", "text_decorations", "extra_snippets", "enable_rich_callback"}
LOCATION_HEADERS = {"x-loc-lat", "x-loc-long", "x-loc-timezone", "x-loc-city", "x-loc-state", "x-loc-state-name", "x-loc-country", "x-loc-postal-code"}
COMMON_HEADERS = {"api-version", "accept", "cache-control", "user-agent"}
FRESHNESS = re.compile(r"(?:pd|pw|pm|py|\d{4}-\d{2}-\d{2}to\d{4}-\d{2}-\d{2})\Z")


def _retry_at(response: requests.Response, quota: bool = False) -> str | None:
    values = response.headers.get("X-RateLimit-Reset", "")
    try:
        seconds = [float(part.strip()) for part in values.split(",") if part.strip()]
    except ValueError:
        seconds = []
    if seconds:
        delay = max(seconds) if quota else min(seconds)
        return (datetime.now(timezone.utc) + timedelta(seconds=max(0, delay))).isoformat(timespec="seconds")
    retry = response.headers.get("Retry-After")
    if retry:
        try:
            return (datetime.now(timezone.utc) + timedelta(seconds=max(0, float(retry)))).isoformat(timespec="seconds")
        except ValueError:
            return None
    return None


def _rate_windows(response: requests.Response) -> list[tuple[float, float, int | None]]:
    try:
        remaining = [float(value.strip()) for value in response.headers.get("X-RateLimit-Remaining", "").split(",")]
        reset = [float(value.strip()) for value in response.headers.get("X-RateLimit-Reset", "").split(",")]
    except ValueError:
        return []
    policy = response.headers.get("X-RateLimit-Policy", "").split(",")
    limits = response.headers.get("X-RateLimit-Limit", "").split(",")
    windows = []
    for index, (left, delay) in enumerate(zip(remaining, reset)):
        policy_entry = policy[index] if index < len(policy) else ""
        limit_entry = limits[index].strip() if index < len(limits) else ""
        if limit_entry:
            try:
                capacity = float(limit_entry)
            except ValueError:
                capacity = None
        else:
            policy_limit = re.match(r"\s*(\d+)\s*;", policy_entry)
            capacity = float(policy_limit.group(1)) if policy_limit else None
        if capacity == 0:
            continue  # Brave uses a zero limit for an unlimited window.
        match = re.search(r"\bw=(\d+)", policy_entry)
        windows.append((left, delay, int(match.group(1)) if match else None))
    return windows


class BraveProvider:
    def __init__(self, session: requests.Session, api_key: str | None):
        self.session = session
        self.api_key = api_key

    @staticmethod
    def validate(request: SearchRequest) -> tuple[str, dict[str, Any], dict[str, str]]:
        kind = request.provider_type or "web"
        if kind not in ENDPOINTS:
            raise ProviderError("invalid_query", "Choose a Brave type: web, news, images, or videos.")
        if not request.query.strip() or len(request.query) > (600 if kind == "web" else 400) or len(request.query.split()) > (75 if kind == "web" else 50):
            raise ProviderError("invalid_query", f"Brave {kind} query exceeds its length or word limit.")
        options = dict(request.provider_options)
        headers = options.pop("headers", {})
        if not isinstance(headers, dict) or set(headers) - (COMMON_HEADERS | (LOCATION_HEADERS if kind == "web" else set())):
            raise ProviderError("invalid_query", f"Unsupported Brave {kind} header.")
        if any(not isinstance(value, str) or not value or "\n" in value or "\r" in value for value in headers.values()):
            raise ProviderError("invalid_query", "Brave headers must be non-empty single-line strings.")
        unsupported = set(options) - PARAMETERS[kind]
        if unsupported:
            raise ProviderError("invalid_query", f"Unsupported Brave {kind} option: {', '.join(sorted(unsupported))}.")
        count = options.get("count")
        if count is None:
            count = min(request.limit, MAX_COUNT[kind])
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_COUNT[kind]:
            raise ProviderError("invalid_query", f"Brave {kind} count must be between 1 and {MAX_COUNT[kind]}.")
        offset = options.get("offset", 0)
        if kind != "images" and (not isinstance(offset, int) or isinstance(offset, bool) or not 0 <= offset <= 9):
            raise ProviderError("invalid_query", "Brave offset must be between 0 and 9.")
        if kind == "images" and "offset" in options:
            raise ProviderError("invalid_query", "Brave Images is not paginated.")
        if options.get("safesearch") not in (None, "off", "strict") and kind == "images":
            raise ProviderError("invalid_query", "Brave Images safesearch supports off or strict.")
        if options.get("safesearch") not in (None, "off", "moderate", "strict"):
            raise ProviderError("invalid_query", "Invalid Brave safesearch level.")
        if options.get("units") not in (None, "metric", "imperial"):
            raise ProviderError("invalid_query", "Invalid Brave measurement units.")
        if options.get("country") is not None and not re.fullmatch(r"[A-Z]{2}|ALL", str(options["country"])):
            raise ProviderError("invalid_query", "Brave country must be an uppercase two-letter code or ALL.")
        if options.get("search_lang") is not None and not re.fullmatch(r"[a-z]{2,5}(?:-[A-Za-z0-9]+)*", str(options["search_lang"])):
            raise ProviderError("invalid_query", "Invalid Brave search language.")
        if options.get("ui_lang") is not None and not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{2,8})*", str(options["ui_lang"])):
            raise ProviderError("invalid_query", "Invalid Brave UI language.")
        if options.get("freshness") is not None and not FRESHNESS.fullmatch(str(options["freshness"])):
            raise ProviderError("invalid_query", "Brave freshness must be pd, pw, pm, py, or YYYY-MM-DDtoYYYY-MM-DD.")
        if options.get("freshness") and "to" in options["freshness"]:
            start_date, end_date = options["freshness"].split("to")
            try:
                if date.fromisoformat(start_date) > date.fromisoformat(end_date):
                    raise ValueError("reversed range")
            except ValueError as exc:
                raise ProviderError("invalid_query", "Invalid Brave freshness date range.") from exc
        if options.get("result_filter") is not None:
            if not isinstance(options["result_filter"], str):
                raise ProviderError("invalid_query", "Brave result filter must be comma-separated text.")
            filters = [part.strip() for part in options["result_filter"].split(",")]
            if not filters or any(value not in FILTER_VALUES for value in filters):
                raise ProviderError("invalid_query", "Invalid Brave result filter.")
            options["result_filter"] = ",".join(dict.fromkeys(filters))
        if options.get("goggles") and options.get("goggles_id"):
            raise ProviderError("invalid_query", "Use --brave-goggle or deprecated --brave-goggles-id, not both.")
        if options.get("goggles") and (not isinstance(options["goggles"], list) or len(options["goggles"]) > 3 or any(not isinstance(value, str) or not value for value in options["goggles"])):
            raise ProviderError("invalid_query", "Brave accepts at most three Goggles.")
        for name in BOOLEAN_PARAMS & options.keys():
            if not isinstance(options[name], bool):
                raise ProviderError("invalid_query", f"Brave {name} must be true or false.")
            options[name] = str(options[name]).lower()
        if kind == "web":
            for name in ("x-loc-lat", "x-loc-long"):
                if name in headers:
                    try:
                        value = float(headers[name])
                    except (TypeError, ValueError) as exc:
                        raise ProviderError("invalid_query", f"Invalid {name} coordinate.") from exc
                    if not (-90 <= value <= 90 if name.endswith("lat") else -180 <= value <= 180):
                        raise ProviderError("invalid_query", f"Invalid {name} coordinate.")
            if "x-loc-country" in headers and not re.fullmatch(r"[A-Z]{2}", headers["x-loc-country"]):
                raise ProviderError("invalid_query", "Brave location country must be an uppercase two-letter code.")
            if "x-loc-state" in headers and len(headers["x-loc-state"]) > 3:
                raise ProviderError("invalid_query", "Brave location state code must be at most three characters.")
        if headers.get("accept") not in (None, "application/json", "*/*"):
            raise ProviderError("invalid_query", "Brave Accept must be application/json or */*.")
        if headers.get("api-version") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", headers["api-version"]):
            raise ProviderError("invalid_query", "Brave API version must be YYYY-MM-DD.")
        if headers.get("cache-control") not in (None, "no-cache"):
            raise ProviderError("invalid_query", "Brave Cache-Control supports only no-cache.")
        params: dict[str, Any] = {"q": request.query, **options, "count": count}
        if kind != "images":
            params["offset"] = offset
        return kind, params, {"Accept": "application/json", **headers}

    def _get(self, path: str, params: dict[str, Any], headers: dict[str, str]) -> tuple[dict[str, Any], requests.Response]:
        try:
            response = self.session.get(f"{API_BASE}/{path}", params=params, headers=headers, timeout=(5, 20))
        except requests.RequestException as exc:
            raise ProviderError("network", f"Network failure contacting Brave ({type(exc).__name__}).") from exc
        try:
            data = response.json()
        except ValueError as exc:
            if response.status_code == 200:
                raise ProviderError("malformed_response", "Brave returned invalid JSON.") from exc
            data = {}
        if response.status_code == 200:
            if not isinstance(data, dict):
                raise ProviderError("malformed_response", "Brave returned an unexpected JSON structure.")
            return data, response
        error = data.get("error", {}) if isinstance(data, dict) else {}
        code = error.get("code", "") if isinstance(error, dict) else ""
        if response.status_code == 401:
            category = "authentication"
        elif code == "QUOTA_LIMITED":
            category = "quota"
        elif response.status_code == 429 or code == "RATE_LIMITED":
            category = "rate_limit"
        elif response.status_code == 403:
            category = "authorization"
        elif response.status_code in (400, 422):
            category = "invalid_query"
        elif response.status_code >= 500:
            category = "provider_unavailable"
        else:
            category = "provider_error"
        message = {
            "authentication": "Check BRAVE_API_KEY.", "authorization": "Access is forbidden for this key or plan.",
            "quota": "Brave search quota was exhausted.", "rate_limit": "Brave rate limit was reached.",
            "invalid_query": "Brave rejected the query or options.", "provider_unavailable": "Brave is temporarily unavailable.",
        }.get(category, "Brave rejected the request.")
        raise ProviderError(category, f"Brave HTTP {response.status_code}: {message}", _retry_at(response, category == "quota"))

    @staticmethod
    def _pace(response: requests.Response) -> None:
        windows = _rate_windows(response)
        for remaining, reset, window in windows:
            if remaining <= 0 and window is not None and window > 2:
                raise ProviderError("quota", "Brave search quota is exhausted.", (datetime.now(timezone.utc) + timedelta(seconds=max(0, reset))).isoformat(timespec="seconds"))
        for remaining, reset, _ in windows:
            if remaining <= 0:
                if reset > 2:
                    category = "quota" if reset > 60 else "rate_limit"
                    raise ProviderError(category, "Brave rate window is exhausted.", (datetime.now(timezone.utc) + timedelta(seconds=reset)).isoformat(timespec="seconds"))
                if reset > 0:
                    time.sleep(reset)

    @staticmethod
    def _normalize(item: object, kind: str, query: str) -> SearchResult | None:
        if not isinstance(item, dict):
            return None
        image = kind == "image"
        properties = item.get("properties") if isinstance(item.get("properties"), dict) else {}
        thumbnail = item.get("thumbnail") if isinstance(item.get("thumbnail"), dict) else {}
        url = (properties.get("url") or thumbnail.get("src") or item.get("url")) if image else item.get("url")
        if not isinstance(url, str) or not url:
            return None
        title = item.get("question") if kind == "faq" else item.get("title")
        description = item.get("description") or (item.get("answer") if kind == "faq" else None)
        metadata = {key: item[key] for key in ("page_age", "page_fetched", "age", "language", "extra_snippets", "breaking", "source", "is_live", "content_type") if isinstance(item.get(key), (str, int, bool, list))}
        if image:
            metadata.update({"page_url": item.get("url"), "thumbnail_url": thumbnail.get("src"), "width": properties.get("width"), "height": properties.get("height")})
        if kind == "video" and isinstance(item.get("video"), dict):
            metadata["video"] = {key: item["video"][key] for key in ("duration", "views", "creator", "publisher") if key in item["video"]}
        return SearchResult("brave", kind, url, title if isinstance(title, str) and title else url, description if isinstance(description, str) else None, query, utc_now(), metadata={key: value for key, value in metadata.items() if value is not None})

    def search(self, request: SearchRequest) -> SearchRun:
        run = new_run(request)
        if not self.api_key:
            run.fail(ProviderError("authentication", "Set BRAVE_API_KEY or run dumpdork -w.").failure)
            return run
        try:
            kind, params, headers = self.validate(request)
        except ProviderError as exc:
            run.fail(exc.failure)
            return run
        if kind == "images" and request.paginate:
            run.fail(ProviderError("invalid_query", "Brave Images does not support pagination.").failure)
            return run
        headers["X-Subscription-Token"] = self.api_key
        if "goggles_id" in params:
            run.warnings.append("Brave goggles_id is deprecated; prefer --brave-goggle.")
        if kind == "web" and params.get("result_filter") and set(params["result_filter"].split(",")).isdisjoint(WEB_SECTIONS):
            run.warnings.append("Requested Brave sections have no normalized links; use --raw to inspect them.")
        offset = params.get("offset", 0)
        previous: requests.Response | None = None
        seen: set[tuple[str, str]] = set()
        while len(run.results) < request.limit:
            try:
                if previous is not None:
                    self._pace(previous)
                if kind != "images":
                    params["offset"] = offset
                data, response = self._get(ENDPOINTS[kind], params, headers)
                previous = response
                if request.capture_raw:
                    run.raw_pages.append(data)
                if kind == "web":
                    if not isinstance(data.get("query"), dict):
                        raise ProviderError("malformed_response", "Brave returned no query metadata.")
                    query_info = data["query"]
                    sections = [(name, data.get(name, {}), result_kind) for name, result_kind in WEB_SECTIONS.items()]
                else:
                    query_info = data.get("query", {})
                    sections = [(kind, {"results": data.get("results")}, "image" if kind == "images" else "video" if kind == "videos" else "news")]
                if isinstance(query_info, dict) and isinstance(query_info.get("altered"), str):
                    run.effective_query = query_info["altered"]
                if kind == "web" and data.get("rich") and not request.capture_raw:
                    run.warnings.append("Brave returned a rich callback hint; use --raw to inspect it.")
                added = 0
                present = 0
                valid = 0
                for name, section, result_kind in sections:
                    if section is None or section == {}:
                        continue
                    if not isinstance(section, dict) or not isinstance(section.get("results"), list):
                        raise ProviderError("malformed_response", f"Brave returned invalid {name} results.")
                    for item in section["results"]:
                        present += 1
                        result = self._normalize(item, result_kind, request.query)
                        if result is None:
                            run.warnings.append(f"Skipped an invalid Brave {name} result.")
                            continue
                        valid += 1
                        identity = (result.kind, result.url)
                        if identity in seen:
                            continue
                        seen.add(identity)
                        run.results.append(result)
                        added += 1
                        if len(run.results) >= request.limit:
                            break
                    if len(run.results) >= request.limit:
                        break
                if present and valid == 0:
                    raise ProviderError("malformed_response", "Brave returned results without usable URLs.")
                if present and added == 0:
                    run.warnings.append("Stopped after Brave repeated a page of results.")
                    break
                if kind == "images":
                    if len(run.results) < request.limit and present >= MAX_COUNT["images"]:
                        run.incomplete = True
                        run.warnings.append("Brave Images exposes at most 200 results for one query.")
                    break
                if not present or len(run.results) >= request.limit:
                    break
                if not request.paginate:
                    can_continue_web = kind == "web" and query_info.get("more_results_available") is True and (not params.get("result_filter") or "web" in params["result_filter"].split(","))
                    if can_continue_web or kind != "web" and present >= params["count"]:
                        run.incomplete = True
                        run.warnings.append("Only one Brave page fetched; use --brave-paginate to request more.")
                    break
                if offset >= 9:
                    if kind != "web" or query_info.get("more_results_available") is True:
                        run.incomplete = True
                        run.warnings.append("Brave pagination stops at offset 9.")
                    break
                if kind == "web" and (params.get("result_filter") and "web" not in params["result_filter"].split(",") or query_info.get("more_results_available") is not True):
                    break
                offset += 1
            except ProviderError as exc:
                run.fail(exc.failure)
                break
        return run
