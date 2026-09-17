"""Provider registry and normalized run execution."""

import requests
from typing import Callable

from .config import Credentials
from .models import SearchRequest, SearchRun
from .providers import BraveProvider, GitHubProvider
from .providers.base import SearchProvider


ProviderFactory = Callable[[requests.Session, Credentials], SearchProvider]
PROVIDERS: dict[str, ProviderFactory] = {
    "brave": lambda client, credentials: BraveProvider(client, credentials.brave_key),
    "github": lambda client, credentials: GitHubProvider(client, credentials.github_token),
}


def search(request: SearchRequest, credentials: Credentials, session: requests.Session | None = None) -> SearchRun:
    own_session = session is None
    client = session or requests.Session()
    try:
        run = PROVIDERS[request.source](client, credentials).search(request)
        seen: set[tuple[str, str, str]] = set()
        unique = []
        for result in run.results:
            identity = (result.source, result.kind, result.url)
            if identity not in seen:
                seen.add(identity)
                unique.append(result)
        run.results = unique
        return run
    finally:
        if own_session:
            client.close()
