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

CONFIG_DIR = os.path.expanduser("~/.config/dumpdork")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
HOST = "google-search74.p.rapidapi.com"

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"{Fore.RED}Error: Configuration file '{config_file}' not found or is empty.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"{Fore.RED}Error: Failed to parse configuration file. {e}")
        sys.exit(1)

def save_config(config_file, key):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    config = {
        'rapidapi': {
            'host': HOST,
            'key': key
        }
    }
    with open(config_file, 'w') as file:
        yaml.dump(config, file)
    print(f"{Fore.GREEN}Configuration saved to '{config_file}'")

def rapidapi_search(query, limit, key):
    encoded_query = urllib.parse.quote(query)

    url = f"https://{HOST}/?query={encoded_query}&limit={limit}&related_keywords=true"

    headers = {
        'x-rapidapi-host': HOST,
        'x-rapidapi-key': key,
        'Content-Type': "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response
    else:
        print(f"{Fore.RED}Error: {response.status_code}")
        return None

def print_help():
    print("🔍 Welcome to DumpDork !!")
    print("\nUsage: dumpdork 'query' [--limit number] [--output filename.json] [--config-file config.yaml]")
    print("\nOptions:")
    print("  query                 The search query.")
    print("  --limit               Number of results to return (default is 50. Limit: 300).")
    print("  --output              Output file to save results in JSON format.")
    print("  --config-file         Path to custom YAML config file containing API credentials. Default is: ~/.config/dumpdork/config.yaml")
    print("  --wizard              Set up your API key for dumpdork, step by step with easy.")
    print("\n📋 Examples:")
    print("    $: dumpdork 'site:*.example.com AND (intext:\"aws_access_key_id\" | intext:\"aws_secret_access_key\" filetype:json | filetype:yaml) ' --limit 200 --output aws_credentials.json ")
    print("    $: dumpdork '(site:*.example.com AND -site:docs.example.com) AND (inurl:\"/login\" | inurl:\"/signup\" | inurl:\"/admin\" | inurl:\"/register\") AND (ext:php | ext:aspx)' --limit 300 --output sqli_forms.json")
    print("    $: dumpdork 'site:*.example.com AND (intitle:\"Index of /\" | intitle:\"index of\") AND (intext:\".log\" | intext:\".sql\" | intext:\".txt\" | intext:\".sh\")' --config-file ~/.config/dumpdork/config_files/credentials_01.yaml --output sensitive_files.json")

def wizard_setup():
    print(f"{Fore.YELLOW}Welcome to the API Key Setup Wizard!")
    print(f"\033[1m[*] See detailed instructions at: https://github.com/mateofumis/dumpdork/blob/main/API_SETUP_GUIDE.md")
    print("1. Sign up at: https://rapidapi.com/herosAPI/api/google-search74/playground")
    print("2. Subscribe for free and copy the API key.")

    key = input(f"\033[1mEnter your RapidAPI key: ").strip()
    if not key:
        print(f"{Fore.RED}Error: API key cannot be empty.")
        sys.exit(1)

    save_config(CONFIG_FILE, key)

def main():
    parser = argparse.ArgumentParser(description='Perform a search using Google Dorks')
    parser.add_argument('query', nargs='?', type=str, help='The search query.')
    parser.add_argument('--limit', type=int, default=50, help='Number of results to return (default is 50. Limit: 300).')
    parser.add_argument('--output', type=str, help='Output file to save results in JSON format.')
    parser.add_argument('--config-file', type=str, default=CONFIG_FILE, help='Path to the YAML config file containing API credentials. Default is: ~/.config/dumpdork/config.yaml')
    parser.add_argument('--wizard', action='store_true', help='Set up your API key for dumpdork, step by step with easy.')

    args = parser.parse_args()

    if args.limit > 300:
        print(f"{Fore.RED}Error: Maximum limit allowed for the API is 300.")
        sys.exit(1)

    if args.wizard:
        wizard_setup()
        sys.exit(0)

    if args.query is None:
        print_help()
        sys.exit(1)

    config = load_config(args.config_file)
    key = config['rapidapi']['key']

    response = rapidapi_search(args.query, args.limit, key)

    if response:
        results = response.json()
        items = results.get('results', [])
        for item in items:
            title = item.get('title', 'No Title')
            url = urllib.parse.unquote(item.get('url', 'No URL'))
            description = item.get('description', 'No Description')

            print(f"{Fore.CYAN}Title: {Style.BRIGHT}{title}")
            print(f"{Fore.GREEN}URL: {Style.BRIGHT}{url}")
            print(f"{Fore.MAGENTA}Description: {Style.BRIGHT}{description}\n")

        total_results = len(items)
        print(f"{Fore.YELLOW}Total results: {total_results}")

    else:
        print(f"{Fore.RED}No results found or an error occurred.")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as json_file:
            json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
        print(f"{Fore.YELLOW}Results saved to '{args.output}'")

if __name__ == "__main__":
    main()
