# DumpDork API setup

DumpDork uses the official [Brave Search API](https://api-dashboard.search.brave.com/api-reference/web/search/get) for web/news/image/video search and the [GitHub REST search API](https://docs.github.com/en/rest/search/search) for GitHub search.

## Brave

Create a Brave Search API account and a key in the Brave dashboard. Set it in your environment or use the private wizard:

```bash
export BRAVE_API_KEY='your-brave-key'
dumpdork -w
```

The key is sent only in Brave's `X-Subscription-Token` request header, not a query parameter. Search operators such as `site:`, `filetype:`, `inbody:`, and `intitle:` are passed through. Use `dumpdork -h` to see all named `--brave-*` filters and headers; unsupported options for a selected vertical are rejected locally. Brave fetches one page by default, even with a high `-l`; use `--brave-paginate -l N` to allow multiple API requests. Brave's short-window rate-limit headers are respected between requests; failed requests are not retried. See [Brave's rate-limit guide](https://api-dashboard.search.brave.com/documentation/guides/rate-limiting).

Brave may require an eligible plan for optional features such as rich callback hints.

## GitHub

Create a GitHub personal access token from GitHub settings if you need code search or higher limits. For public search, use the least permissions needed:

```bash
export GITHUB_TOKEN='your-github-token'
```

Repository search can run anonymously. DumpDork requires a token for code search, selected with `--github-type code`. GitHub's [REST search limits](https://docs.github.com/en/rest/search/search) are stricter for code search.

## Private config file

`dumpdork -w` prompts without echoing values and saves `~/.config/dumpdork/config.yaml` with owner-only permissions on POSIX systems:

```yaml
credentials:
  brave_key: "your-brave-key"
  github_token: "your-github-token"
```

Environment variables override this file. Do not put real credentials in the repository's example `config.yaml` or shell commands saved in history. If you used an older DumpDork config, a GitHub token stored under `rapidapi.keys.github` in this private file still works. To save it in the new format, run `dumpdork -w` and leave the GitHub token prompt blank; the wizard will keep the token and write it under `credentials.github_token`. Old RapidAPI search keys are not used.
