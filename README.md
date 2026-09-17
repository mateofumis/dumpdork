# DumpDork

<img alt="logo_banner" src="https://raw.githubusercontent.com/mateofumis/dumpdork/refs/heads/main/assets/dumpdork.png" />

---

DumpDork is a small, search-driven OSINT and reconnaissance command-line tool. It searches the web, news, images, and videos through the official [Brave Search API](https://api-dashboard.search.brave.com/api-reference/web/search/get), and repositories and code through GitHub's REST API. Queries stay in each provider's native syntax.

## Install

The published release is available on [PyPI](https://pypi.org/project/dumpdork/). Install it with `pipx` (recommended for a command-line tool) or `pip`:

```bash
pipx install dumpdork
# or, inside a virtual environment:
pip install dumpdork
```

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Run `.venv/bin/dumpdork` (or activate the environment to use `dumpdork`). On Windows, the executables are in `.venv\Scripts\`. You can also run `python dumpdork.py` from a checkout.

## Credentials

Set `BRAVE_API_KEY` for Brave searches and `GITHUB_TOKEN` for GitHub code search and better GitHub rate limits. GitHub repository search can run without a token. Environment variables override `~/.config/dumpdork/config.yaml`. Use `dumpdork -w` to save credentials privately and interactively. See [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md). Never put real keys in the repository's example `config.yaml`.

## Search

```bash
dumpdork 'site:*.example.com (intitle:"Swagger UI" OR inpage:"OpenAPI")' # Brave Web (default)
dumpdork -s brave --brave-type news --brave-freshness pw 'supply chain'
dumpdork -s brave --brave-type images --brave-count 100 -l 100 'public satellite imagery'
dumpdork -s brave --brave-type videos --brave-country AR 'security conference'
dumpdork --brave-paginate -l 100 'site:example.com' # explicitly fetch additional pages
dumpdork --brave-result-filter web,discussions --brave-extra-snippets 'topic'
dumpdork -s github --github-type repo 'topic:osint language:python'
dumpdork -s github --github-type code 'filename:config.php DB_PASSWORD'
```

`-s brave` and `--brave-type web` are the defaults. Brave fetches **one page** per search, even with a high `--limit`. To fetch more pages, use `--brave-paginate -l N`.

Without `--limit`, the result cap matches one Brave page: 20 for Web, 50 for News/Videos, or 200 for Images. GitHub defaults to 50 and keeps its own pagination behavior. `--limit` caps normalized results across all returned sections, not just web links.

Use `--brave-count` to set the number of results per page and `--brave-offset` to choose the starting page (0–9). Images do not support pagination. If a one-page search returns fewer results than requested and more pages are available, JSON reports `incomplete: true`. When pagination is enabled, DumpDork follows Brave's `query.more_results_available` and deduplicates overlapping results. [Brave pagination](https://api-dashboard.search.brave.com/app/documentation/web-search).

Run `dumpdork -h` to see all `--brave-*` options. They include language, location, safe search, freshness, result filters, Goggles, and response options. Unsupported options for a search type are rejected before any API request.

Boolean flags have a `--no-` form, such as `--no-brave-spellcheck`. Prefer repeatable `--brave-goggle` (up to three) over the deprecated `--brave-goggles-id`.

Rich callback responses provide a hint; DumpDork does not call the separate Rich endpoint. For option details, see Brave's [Web](https://api-dashboard.search.brave.com/api-reference/web/search/get), [News](https://api-dashboard.search.brave.com/api-reference/news/news_search/get), [Images](https://api-dashboard.search.brave.com/api-reference/images/image_search), and [Videos](https://api-dashboard.search.brave.com/api-reference/videos/video_search/get) references.

### Brave search operators

Put these operators directly in the query; DumpDork passes them through to Brave without translating Google dorks. The table follows [Brave's Search API operator reference](https://api-dashboard.search.brave.com/documentation/resources/search-operators).

| Operator | What it does | Example |
| --- | --- | --- |
| `ext:` | Filter by file extension | `config ext:yaml` |
| `filetype:` | Filter by file type | `report filetype:pdf` |
| `intitle:` | Match text in the page title | `intitle:documentation` |
| `inbody:` | Match text in the page body | `inbody:"security policy"` |
| `inpage:` | Match text in the title or body | `inpage:configuration` |
| `lang:` / `language:` | Filter by page language (two-letter code) | `research lang:es` |
| `loc:` / `location:` | Filter by country or region (two-letter code) | `research loc:ar` |
| `site:` | Restrict results to a domain or site | `site:example.com policy` |
| `+` | Require a term in the title or body | `assets +inventory` |
| `-` | Exclude a term | `assets -advertising` |
| `"..."` | Match an exact phrase | `"responsible disclosure"` |
| `AND` | Require both conditions | `policy AND site:example.com` |
| `OR` | Match either condition | `filetype:yaml OR filetype:json` |
| `NOT` | Exclude a condition | `research NOT site:example.com` |

Write `AND`, `OR`, and `NOT` in uppercase. Brave describes operators as experimental, so complex combinations may not behave exactly like Google dorks; `intext:` and wildcard domains such as `site:*.com` are not listed in Brave's reference. Use `inbody:` or `inpage:` for text matching. `--no-brave-operators` disables Brave's operator interpretation for a query.

### GitHub search qualifiers

Select `-s github --github-type repo` or `-s github --github-type code`. DumpDork sends the query unchanged to GitHub's REST search endpoints. These are common qualifiers from GitHub's [repository search](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories) and [legacy code search](https://docs.github.com/en/search-github/searching-on-github/searching-code) documentation; see those references for the full lists.

Repository search (`--github-type repo`):

| Qualifier | What it does | Example |
| --- | --- | --- |
| `in:name`, `in:description`, `in:topics`, `in:readme` | Choose which repository fields to search | `osint in:name,description` |
| `user:`, `org:`, `repo:` | Restrict by owner, organization, or repository | `topic:osint org:github` |
| `language:` | Filter by primary repository language | `osint language:python` |
| `topic:` | Filter by repository topic | `topic:threat-intelligence` |
| `stars:`, `forks:` | Filter by star or fork count | `topic:osint stars:>=100` |
| `size:` | Filter by repository size in KB | `osint size:100..1000` |
| `created:`, `pushed:` | Filter by creation or last-push date | `osint pushed:>=2025-01-01` |
| `license:` | Filter by license keyword | `osint license:apache-2.0` |
| `fork:true`, `fork:only` | Include forks or search only forks | `topic:osint fork:true` |
| `archived:`, `mirror:`, `template:` | Filter by repository state | `topic:osint archived:false` |
| `is:public`, `is:private` | Filter by visibility (subject to your access) | `osint is:public` |

Code search (`--github-type code`) uses the **legacy REST API syntax**, not the newer GitHub.com code-search syntax:

| Qualifier | What it does | Example |
| --- | --- | --- |
| `in:file`, `in:path`, `in:file,path` | Search file contents, paths, or both | `config in:file,path` |
| `user:`, `org:`, `repo:` | Restrict by owner, organization, or repository | `settings repo:owner/project` |
| `path:` | Restrict to a directory; `path:/` means repository root | `settings path:config` |
| `language:` | Filter by file language | `parser language:python` |
| `size:` | Filter by file size in bytes | `parser size:<10000` |
| `filename:` | Match a filename | `filename:config.yml settings` |
| `extension:` | Match a file extension | `settings extension:yaml` |

Numeric and date qualifiers support comparisons such as `>`, `>=`, `<`, and ranges such as `100..500`; keep the entire query quoted in your shell so `<` and `>` are not interpreted as redirection. GitHub code search requires a token in DumpDork, indexes only default branches and files smaller than 384 KB, and generally needs a search term alongside qualifiers. Repository-only qualifiers such as `stars:` do not apply to code search. The newer `content:` qualifier is not supported by the REST code endpoint; DumpDork rejects it. `--include-commits` fetches three recent commits once per distinct repository.

## Output and rate limits

Terminal text is the default. The original banner appears on interactive runs, not `-h`, and goes to stderr so stdout remains pipeline-friendly. JSON and JSONL have no banner or notices on stdout.

```bash
dumpdork 'site:example.com' --format json | jq '.results[].url'
dumpdork 'site:example.com' --format jsonl | jq -r '.url'
dumpdork 'site:example.com' -o results.json
dumpdork 'site:example.com' -o provider-pages.json --raw
```

With `-o`, DumpDork writes normalized JSON by default. Use `--format jsonl` for one result per line, or `--raw` to save redacted provider responses. Raw output also contains non-link Brave sections such as infoboxes.

Normalized JSON uses `schema_version: 2`. It includes the query, source, search type, status, counts, optional `effective_query`, and a `results` array. Results include a URL, title, source, kind, matched query, observation time, and optional snippet, repository, path, and metadata. Encoded URLs are preserved.

With `--brave-paginate`, DumpDork uses Brave's per-second rate-limit headers to pace requests. It does not retry failed requests or wait for a long quota reset. If a later page fails, collected results are kept with status `partial`. A one-page search avoids later-page errors, but its first request can still fail if quota is exhausted. [Brave rate-limit guide](https://api-dashboard.search.brave.com/documentation/guides/rate-limiting).

Errors distinguish authentication, authorization, rate limits, quota, invalid queries, network failures, and malformed responses. Exit codes are `0` for success (even with no results), `1` for failure, `2` for invalid CLI usage, and `3` for partial results. Enable `pipefail` if you want a pipeline with `jq` to report DumpDork's exit code.

Queries are passed through without rewriting. Brave documents `inbody:` rather than Google's `intext:`. See the [search operators](https://api-dashboard.search.brave.com/documentation/resources/search-operators).

## License

DumpDork is licensed under Apache License 2.0; see [LICENSE](LICENSE).
