"""Search provider adapters."""

from .github import GitHubProvider
from .brave import BraveProvider

__all__ = ["BraveProvider", "GitHubProvider"]
