"""DumpDork command-line interface."""

import argparse
from pathlib import Path
import sys

from .config import load_credentials, wizard
from .core import search
from .errors import ConfigError, ProviderError
from .models import SearchRequest
from .output import render
from .providers.brave import BraveProvider, MAX_COUNT


BANNER = r"""    ____                        ____             _
   |  _ \ _   _ _ __ ___  _ __ |  _ \  ___  _ __| | __
   | | | | | | | '_ ` _ \| '_ \| | | |/ _ \| '__| |/ /
   | |_| | |_| | | | | | |_) | |_| | (_) | |  |   <
   |____/ \__,_|_| |_| |_| .__/|____/ \___/|_|  |_|\_\
                         |_|
        OSINT Search & Discovery Toolkit
        DumpDork v2.0.0 · @hackermater
"""


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search public sources for OSINT research", prog="dumpdork")
    parser.add_argument("query", nargs="?", help="Search query or dork")
    parser.add_argument("-s", "--source", choices=("brave", "github"), default="brave", help="Search source (default: brave)")
    parser.add_argument("--github-type", choices=("repo", "code"), help="Required for GitHub: repository or code search")
    parser.add_argument("-l", "--limit", type=positive_int, help="Maximum results (default: Brave page size, or 50 for GitHub); Brave needs --brave-paginate for multiple pages")
    parser.add_argument("-o", "--output", type=Path, help="Write output to a file (normalized JSON by default)")
    parser.add_argument("--format", choices=("text", "json", "jsonl"), help="Output format (text on stdout, JSON with -o)")
    parser.add_argument("--raw", action="store_true", help="Export redacted provider response pages as JSON")
    parser.add_argument("--include-commits", action="store_true", help="Fetch three recent commits per distinct GitHub repository")
    parser.add_argument("-w", "--wizard", action="store_true", help="Configure API credentials interactively")
    brave = parser.add_argument_group("Brave Search options")
    brave.add_argument("--brave-type", choices=("web", "news", "images", "videos"), help="Brave search vertical (default: web)")
    brave.add_argument("--brave-country", help="Search country (two-letter code or ALL where supported)")
    brave.add_argument("--brave-search-lang", help="Search result language")
    brave.add_argument("--brave-ui-lang", help="Response UI language, e.g. en-US")
    brave.add_argument("--brave-safesearch", choices=("off", "moderate", "strict"))
    brave.add_argument("--brave-count", type=int, help="Brave results per page; maximum depends on vertical")
    brave.add_argument("--brave-offset", type=int, help="Starting page offset (0-9; not available for images)")
    brave.add_argument("--brave-paginate", action="store_true", help="Allow additional Brave API requests to collect results beyond the first page")
    brave.add_argument("--brave-spellcheck", action=argparse.BooleanOptionalAction, default=None)
    brave.add_argument("--brave-freshness", help="pd, pw, pm, py or YYYY-MM-DDtoYYYY-MM-DD")
    brave.add_argument("--brave-operators", action=argparse.BooleanOptionalAction, default=None)
    brave.add_argument("--brave-fetch-metadata", action=argparse.BooleanOptionalAction, default=None)
    brave.add_argument("--brave-text-decorations", action=argparse.BooleanOptionalAction, default=None)
    brave.add_argument("--brave-extra-snippets", action=argparse.BooleanOptionalAction, default=None)
    brave.add_argument("--brave-result-filter", help="Comma-separated Web sections: web,news,videos,discussions,faq,locations,infobox,query")
    brave.add_argument("--brave-units", choices=("metric", "imperial"))
    brave.add_argument("--brave-goggle", action="append", help="Goggle URL or inline definition; repeat up to 3 times")
    brave.add_argument("--brave-goggles-id", help="Deprecated Goggle identifier")
    brave.add_argument("--brave-rich-callback", action=argparse.BooleanOptionalAction, default=None)
    brave.add_argument("--brave-lat", type=float, help="Location latitude for Web Search")
    brave.add_argument("--brave-long", type=float, help="Location longitude for Web Search")
    brave.add_argument("--brave-timezone", help="IANA location timezone for Web Search")
    brave.add_argument("--brave-city", help="Location city for Web Search")
    brave.add_argument("--brave-state", help="Location state/region code for Web Search")
    brave.add_argument("--brave-state-name", help="Location state/region name for Web Search")
    brave.add_argument("--brave-location-country", help="Location country header for Web Search")
    brave.add_argument("--brave-postal-code", help="Location postal code for Web Search")
    brave.add_argument("--brave-api-version", help="Brave API version, YYYY-MM-DD")
    brave.add_argument("--brave-accept", choices=("application/json", "*/*"))
    brave.add_argument("--brave-no-cache", action="store_true", help="Request uncached Brave results")
    brave.add_argument("--brave-user-agent", help="User-Agent sent to Brave")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = sys.argv[1:] if argv is None else argv
    if not arguments:
        if sys.stderr.isatty():
            print(BANNER, file=sys.stderr)
        parser.print_usage()
        return 0
    args = parser.parse_args(arguments)
    try:
        if args.wizard:
            if sys.stderr.isatty():
                print(BANNER, file=sys.stderr)
            wizard()
            return 0
        if args.query is None or not args.query.strip():
            parser.error("a non-empty query is required unless using -w")
        if args.source == "github" and args.github_type is None:
            parser.error("--github-type repo or code is required for GitHub")
        if args.source != "github" and (args.github_type or args.include_commits):
            parser.error("--github-type and --include-commits are only valid for GitHub")
        if args.brave_paginate and args.source == "github":
            parser.error("--brave-paginate is only valid for Brave")
        if args.brave_paginate and args.brave_type == "images":
            parser.error("Brave Images does not support pagination")

        query_fields = {
            "country": args.brave_country, "search_lang": args.brave_search_lang, "ui_lang": args.brave_ui_lang,
            "safesearch": args.brave_safesearch, "count": args.brave_count, "offset": args.brave_offset,
            "spellcheck": args.brave_spellcheck, "freshness": args.brave_freshness,
            "operators": args.brave_operators, "include_fetch_metadata": args.brave_fetch_metadata,
            "text_decorations": args.brave_text_decorations, "extra_snippets": args.brave_extra_snippets,
            "result_filter": args.brave_result_filter, "units": args.brave_units,
            "goggles": args.brave_goggle, "goggles_id": args.brave_goggles_id,
            "enable_rich_callback": args.brave_rich_callback,
        }
        brave_options = {key: value for key, value in query_fields.items() if value is not None}
        header_fields = {
            "x-loc-lat": args.brave_lat, "x-loc-long": args.brave_long,
            "x-loc-timezone": args.brave_timezone, "x-loc-city": args.brave_city,
            "x-loc-state": args.brave_state, "x-loc-state-name": args.brave_state_name,
            "x-loc-country": args.brave_location_country, "x-loc-postal-code": args.brave_postal_code,
            "api-version": args.brave_api_version, "accept": args.brave_accept,
            "cache-control": "no-cache" if args.brave_no_cache else None,
            "user-agent": args.brave_user_agent,
        }
        headers = {key: str(value) for key, value in header_fields.items() if value is not None}
        if headers:
            brave_options["headers"] = headers
        if args.source == "github" and (brave_options or args.brave_type):
            parser.error("--brave-* options are only valid for Brave")

        format_name = args.format or ("json" if args.output or args.raw else "text")
        if args.raw and format_name != "json":
            parser.error("--raw requires JSON output")

        limit = args.limit if args.limit is not None else MAX_COUNT[args.brave_type or "web"] if args.source == "brave" else 50
        request = SearchRequest(args.source, args.query, limit, args.github_type, args.include_commits, args.raw, args.brave_type or "web" if args.source == "brave" else None, brave_options, paginate=args.brave_paginate)
        if args.source == "brave":
            try:
                BraveProvider.validate(request)
            except ProviderError as exc:
                parser.error(exc.failure.message)
        if sys.stderr.isatty():
            print(BANNER, file=sys.stderr)
        credentials = load_credentials()
        run = search(request, credentials)
        secrets = tuple(secret for secret in (credentials.brave_key, credentials.github_token) if secret)
        content = render(run, format_name, raw=args.raw, secrets=secrets, color=format_name == "text" and args.output is None and sys.stdout.isatty())

        if args.output:
            args.output.write_text(content, encoding="utf-8")
            qualifier = " partial" if run.status == "partial" else ""
            print(f"Wrote {len(run.results)}{qualifier} results to {args.output}.", file=sys.stderr)
        else:
            sys.stdout.write(content)

        for warning in run.warnings:
            print(f"Warning: {warning}", file=sys.stderr)
        if run.error:
            print(f"Error ({run.error.type}): {run.error.message}", file=sys.stderr)
            if run.error.retry_at:
                print(f"Retry after: {run.error.retry_at}", file=sys.stderr)
        return {"success": 0, "error": 1, "partial": 3}[run.status]
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"I/O error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
