"""Contract implemented by search adapters."""

from typing import Protocol

from ..models import SearchRequest, SearchRun


class SearchProvider(Protocol):
    def search(self, request: SearchRequest) -> SearchRun: ...
