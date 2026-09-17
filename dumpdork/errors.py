"""Provider errors and HTTP response classification."""

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

from .models import SearchFailure


class ConfigError(Exception):
    """Invalid or inaccessible user configuration."""


class ProviderError(Exception):
    def __init__(self, kind: str, message: str, retry_at: str | None = None):
        super().__init__(message)
        self.failure = SearchFailure(kind, message, retry_at)


def _retry_at(response: requests.Response) -> str | None:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return (datetime.now(timezone.utc) + timedelta(seconds=int(retry_after))).isoformat(timespec="seconds")
        except ValueError:
            try:
                return parsedate_to_datetime(retry_after).astimezone(timezone.utc).isoformat(timespec="seconds")
            except (ValueError, TypeError, OverflowError):
                pass
    reset = response.headers.get("X-RateLimit-Reset")
    if reset:
        try:
            return datetime.fromtimestamp(int(reset), timezone.utc).isoformat(timespec="seconds")
        except (ValueError, OverflowError):
            pass
    return None


def request_json(
    session: requests.Session,
    url: str,
    *,
    source: str,
    params: dict,
    headers: dict | None = None,
    timeout: tuple[int, int] = (5, 20),
) -> tuple[dict, requests.Response]:
    """Make one bounded request without exposing secret-bearing URLs in errors."""
    try:
        response = session.get(url, params=params, headers=headers or {}, timeout=timeout)
    except requests.RequestException as exc:
        raise ProviderError("network", f"Network failure contacting {source} ({type(exc).__name__}).") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        if response.status_code == 200:
            raise ProviderError("malformed_response", f"{source} returned invalid JSON.") from exc
        payload = {}

    status = response.status_code
    if status == 200:
        if not isinstance(payload, dict):
            raise ProviderError("malformed_response", f"{source} returned an unexpected JSON structure.")
        return payload, response

    if not isinstance(payload, dict):
        payload = {}
    message = str(payload.get("message") or payload.get("error") or "").lower()
    if status == 401:
        kind = "authentication"
    elif status == 429:
        kind = "rate_limit"
    elif status == 403:
        limited = (
            response.headers.get("X-RateLimit-Remaining") == "0"
            or bool(response.headers.get("Retry-After"))
            or "rate limit" in message
        )
        kind = "rate_limit" if limited else "authorization"
    elif status in (400, 422):
        kind = "invalid_query"
    elif status >= 500:
        kind = "provider_unavailable"
    else:
        kind = "provider_error"

    detail = {
        "authentication": "Check the configured API credential.",
        "authorization": "Access is forbidden for this query or credential.",
        "rate_limit": "The provider rate limit was reached.",
        "quota": "The provider search quota was exhausted.",
        "invalid_query": "The provider rejected the query or its parameters.",
        "provider_unavailable": "The provider is temporarily unavailable.",
    }.get(kind, "The provider rejected the request.")
    raise ProviderError(kind, f"{source} HTTP {status}: {detail}", _retry_at(response))
