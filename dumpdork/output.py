"""Human and pipeline-oriented renderers."""

from dataclasses import asdict
import json
from typing import Any

from colorama import Fore, Style

from .models import SearchRun


def _clean_value(value: Any, secrets: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if str(key).lower() in {"api_key", "authorization", "token", "github_token", "brave_key", "x-subscription-token"}
            else _clean_value(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_clean_value(item, secrets) for item in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value
    return value


def normalized_document(run: SearchRun) -> dict:
    return {
        "schema_version": 2,
        "query": run.query,
        "source": run.source,
        "search_type": run.search_type,
        "effective_query": run.effective_query,
        "status": run.status,
        "requested_limit": run.requested_limit,
        "returned_count": len(run.results),
        "total_count": run.total_count,
        "incomplete": run.incomplete,
        "warnings": run.warnings,
        "error": asdict(run.error) if run.error else None,
        "results": [asdict(result) for result in run.results],
    }


def raw_document(run: SearchRun, secrets: tuple[str, ...]) -> dict:
    return {
        "source": run.source,
        "query": _clean_value(run.query, secrets),
        "status": run.status,
        "pages": _clean_value(run.raw_pages, secrets),
        "error": asdict(run.error) if run.error else None,
    }


def render(run: SearchRun, format_name: str, *, raw: bool = False, secrets: tuple[str, ...] = (), color: bool = False) -> str:
    if raw:
        return json.dumps(raw_document(run, secrets), ensure_ascii=False, indent=2) + "\n"
    if format_name == "json":
        return json.dumps(normalized_document(run), ensure_ascii=False, indent=2) + "\n"
    if format_name == "jsonl":
        return "".join(json.dumps(asdict(result), ensure_ascii=False) + "\n" for result in run.results)
    if format_name != "text":
        raise ValueError(f"Unknown output format: {format_name}")

    def mark(label: str, value: str, tone: str) -> str:
        return f"{tone}{label}{Style.RESET_ALL} {value}" if color else f"{label} {value}"

    lines = []
    if color:
        lines.extend((f"{Fore.CYAN}DumpDork{Style.RESET_ALL}", ""))
    source = f"{run.source} {run.search_type}" if run.search_type and run.source == "brave" else run.source
    lines.extend((f"Searching {source} for: {run.query}", ""))
    for result in run.results:
        if result.kind == "repository":
            lines.append(mark("Repo:", result.title, Fore.CYAN))
        elif result.kind == "file":
            lines.append(mark("File:", f"{result.path or result.title} in {result.repository}", Fore.CYAN))
        else:
            lines.append(mark(f"{result.kind.title()}:", result.title, Fore.CYAN))
        lines.append(mark("URL:", result.url, Fore.GREEN))
        if result.snippet:
            lines.append(mark("Description:", result.snippet[:150], Fore.MAGENTA))
        commits = result.metadata.get("recent_commits") or []
        if commits:
            lines.append("Recent commits:")
            lines.extend(f"  - [{commit.get('date') or ''}] {commit.get('message') or ''}" for commit in commits)
        lines.append("")
    if not run.results and run.status == "success":
        lines.append("No results found.")
    lines.append(f"Total results: {len(run.results)}" + (" (partial)" if run.status == "partial" else ""))
    return "\n".join(lines).rstrip() + "\n" if lines else ""
