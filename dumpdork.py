#!/usr/bin/python3
# Author: Mateo Fumis (hackermater) - linkedin.com/in/mateo-gabriel-fumis
import os
import sys
import requests
import urllib.parse
import json
import argparse
import yaml
from colorama import init, Fore, Style

init(autoreset=True)

# Configuration Directory and File
CONFIG_DIR = os.path.expanduser("~/.config/dumpdork")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")

# Providers Configuration
PROVIDERS = {
    "google": {
        "host": "google-search74.p.rapidapi.com",
        "url_pattern": "https://google-search74.p.rapidapi.com/"
    },
    "brave": {
        "host": "brave-web-search.p.rapidapi.com",
        "url_pattern": "https://brave-web-search.p.rapidapi.com/search"
    },
    "github": {
        "is_official": True,
        "repo_search": "https://api.github.com/search/repositories",
        "code_search": "https://api.github.com/search/code"
    }
}

def print_banner():
    banner = rf"""
{Fore.CYAN}    ____                        ____             _    
{Fore.CYAN}   |  _ \ _   _ _ __ ___  _ __ |  _ \  ___  _ __| | __
{Fore.CYAN}   | | | | | | | '_ ` _ \| '_ \| | | |/ _ \| '__| |/ /
{Fore.CYAN}   | |_| | |_| | | | | | | |_) | |_| | (_) | |  |   < 
{Fore.CYAN}   |____/ \__,_|_| |_| |_| .__/|____/ \___/|_|  |_|\_\
{Fore.CYAN}                         |_|                          
{Fore.YELLOW}             Advanced Dorking Tool v1.2
{Fore.WHITE}       Created by: Mateo Fumis (hackermater)
    """
    print(banner)

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"{Fore.RED}Error: Configuration file '{config_file}' not found.")
        print(f"{Fore.YELLOW}Tip: Run with -w to set up your API keys.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"{Fore.RED}Error: Failed to parse configuration file. {e}")
        sys.exit(1)

def save_config(config_file, keys_dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    config = {
        'rapidapi': {
            'host': PROVIDERS["google"]["host"],
            'keys': keys_dict
        }
    }
    with open(config_file, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    print(f"{Fore.GREEN}Configuration saved to '{config_file}'")

def get_github_commits(repo_full_name, key, limit=3):
    """Fetch recent commits for a specific GitHub repository."""
    url = f"https://api.github.com/repos/{repo_full_name}/commits"
    headers = {
        'Accept': "application/vnd.github.v3+json",
        'User-Agent': 'DumpDork-Tool'
    }
    if key and key.strip() != "" and key != "Not configured":
        headers['Authorization'] = f"token {key}"

    try:
        response = requests.get(url, headers=headers, params={'per_page': limit})
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def perform_search(source, query, limit, key):
    if source not in PROVIDERS:
        return None

    provider = PROVIDERS[source]
    headers = {}
    params = {}

    if source == "github":
        is_code_search = any(x in query for x in ["filename:", "extension:", "path:", "content:"])
        url = provider["code_search"] if is_code_search else provider["repo_search"]

        params = {'q': query, 'per_page': limit}
        if key and key.strip() != "" and key != "Not configured":
            headers['Authorization'] = f"token {key}"
        headers['Accept'] = "application/vnd.github.v3+json"
        headers['User-Agent'] = 'DumpDork-Tool'

    elif source == "google":
        url = provider["url_pattern"]
        params = {'query': query, 'limit': limit}
        headers = {
            'x-rapidapi-host': provider["host"],
            'x-rapidapi-key': key
        }

    elif source == "brave":
        url = provider["url_pattern"]
        params = {'q': query, 'count': limit}
        headers = {
            'x-rapidapi-host': provider["host"],
            'x-rapidapi-key': key
        }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if source == "github" and not data.get('items') and url == provider["code_search"]:
                response = requests.get(provider["repo_search"], headers=headers, params=params)
                if response.status_code == 200:
                    return response.json()
            return data
        elif response.status_code == 401:
            print(f"{Fore.RED}Error 401: Unauthorized. Your {source} token/key is invalid.")
        elif response.status_code == 403:
            print(f"{Fore.RED}Error 403: Forbidden for {source}. Code search may require an API Token.")
        else:
            print(f"{Fore.RED}Error {response.status_code} from {source}")
    except Exception as e:
        print(f"{Fore.RED}Connection Error: {e}")
    return None

def wizard_setup():
    print(f"{Fore.YELLOW}{Style.BRIGHT}Welcome to the DumpDork API Setup Wizard!")

    keys_dict = {}
    if os.path.exists(CONFIG_FILE):
        try:
            existing_config = load_config(CONFIG_FILE)
            keys_dict = existing_config.get('rapidapi', {}).get('keys', {})
        except:
            pass

    for source in PROVIDERS.keys():
        print(f"\n{Fore.CYAN}--- {source.upper()} ---")
        if source == "github":
            print("Using official GitHub API (api.github.com)")
        else:
            print(f"RapidAPI Host: {PROVIDERS[source]['host']}")

        current_key = keys_dict.get(source, "Not configured")
        print(f"Current Key: {current_key}")

        prompt = f"Enter API key/token for {source} (leave blank to skip): "
        new_key = input(prompt).strip()

        if new_key.lower() == 'clear':
            keys_dict[source] = ""
        elif new_key:
            keys_dict[source] = new_key

    save_config(CONFIG_FILE, keys_dict)

def main():
    try:
        parser = argparse.ArgumentParser(description='Perform a search using Dorks across multiple platforms', prog='dumpdork.py')
        parser.add_argument('query', nargs='?', type=str, help='Search query or dork')
        parser.add_argument('-s', '--source', type=str, default='google', choices=['google', 'github', 'brave'], help='Search engine source')
        parser.add_argument('-l', '--limit', type=int, default=50, help='Maximum number of results')
        parser.add_argument('-o', '--output', type=str, help='Save results to a JSON file')
        parser.add_argument('-w', '--wizard', action='store_true', help='Run API configuration wizard')

        print_banner()

        if len(sys.argv) == 1:
            parser.print_usage()
            print(f"\nUse {Fore.YELLOW}-h{Fore.RESET} or {Fore.YELLOW}--help{Fore.RESET} for full details.\n")
            sys.exit(0)

        args = parser.parse_args()

        if args.wizard:
            wizard_setup()
            sys.exit(0)

        if args.query is None:
            parser.print_usage()
            print(f"{Fore.RED}Error: A search query is required unless using -w.")
            sys.exit(1)

        config = load_config(CONFIG_FILE)
        keys_dict = config.get('rapidapi', {}).get('keys', {})
        api_key = keys_dict.get(args.source)

        if not api_key and args.source != "github":
            print(f"{Fore.RED}Error: No API key found for {args.source}. Run with -w to setup.")
            sys.exit(1)

        print(f"{Fore.YELLOW}Searching {args.source} for: {args.query}...\n")
        results = perform_search(args.source, args.query, args.limit, api_key)

        if results:
            items = []
            if args.source == "github":
                items = results.get('items', [])
            elif args.source == "brave":
                items = results.get('results', []) or results.get('web', {}).get('results', [])
            else: # Google
                items = results.get('results', [])

            for item in items:
                if args.source == "github":
                    repository = item.get('repository', {}) if 'repository' in item else item
                    full_name = repository.get('full_name') or item.get('full_name') or 'No Name'
                    url = item.get('html_url') or repository.get('html_url') or 'No URL'
                    desc = item.get('description') or repository.get('description') or 'No Description'
                    owner = repository.get('owner', {}).get('login') or item.get('owner', {}).get('login', 'Unknown')

                    if desc and len(desc) > 150:
                        desc = desc[:147] + "..."

                    if 'path' in item:
                        print(f"{Fore.CYAN}File: {Style.BRIGHT}{item.get('path')} {Fore.WHITE}in {full_name}")
                    else:
                        print(f"{Fore.CYAN}Repo: {Style.BRIGHT}{full_name} ({Fore.WHITE}by @{owner}{Fore.CYAN})")

                    print(f"{Fore.GREEN}URL: {Style.BRIGHT}{urllib.parse.unquote(url)}")
                    print(f"{Fore.MAGENTA}Description: {Style.BRIGHT}{desc}")

                    commits = get_github_commits(full_name, api_key)
                    if commits:
                        print(f"{Fore.YELLOW}Recent Commits:")
                        for c in commits:
                            msg = c.get('commit', {}).get('message', '').split('\n')[0]
                            date = c.get('commit', {}).get('author', {}).get('date', '')[:10]
                            print(f"  {Fore.WHITE}- [{date}] {msg[:80]}")
                    print("")
                else:
                    title = item.get('title') or 'No Title'
                    url = item.get('url') or item.get('link') or 'No URL'
                    desc = item.get('description') or item.get('snippet') or 'No Description'

                    if desc and len(desc) > 150:
                        desc = desc[:147] + "..."

                    print(f"{Fore.CYAN}Title: {Style.BRIGHT}{title}")
                    print(f"{Fore.GREEN}URL: {Style.BRIGHT}{urllib.parse.unquote(url)}")
                    print(f"{Fore.MAGENTA}Description: {Style.BRIGHT}{desc}\n")

            print(f"{Fore.YELLOW}{Style.BRIGHT}Execution finished. Total results found: {len(items)}")

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as json_file:
                    json.dump(results, json_file, ensure_ascii=False, indent=4)
                print(f"{Fore.YELLOW}Results saved to '{args.output}'")
        else:
            print(f"{Fore.RED}No results found.")
            print(f"{Fore.YELLOW}{Style.BRIGHT}Execution finished. Total results found: 0")

    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Process interrupted by user. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
