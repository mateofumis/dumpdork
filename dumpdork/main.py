#!/usr/bin/python3
import sys
import requests
import urllib.parse
import json
import argparse
import yaml
from colorama import init, Fore, Style

init(autoreset=True)

def load_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

def rapidapi_search(query, limit, host, key):
    encoded_query = urllib.parse.quote(query)
    
    url = f"https://{host}/?query={encoded_query}&limit={limit}&related_keywords=true"
    
    headers = {
        'x-rapidapi-host': host,
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
    print(f"{Fore.YELLOW}Usage: dumpdork 'query' [--limit number] [--output filename.json] [--config-file config.yaml]")
    print(f"{Fore.YELLOW}Options:")
    print(f"  query                The search query.")
    print(f"  --limit              Number of results to return (default is 50).")
    print(f"  --output             Output file to save results in JSON format.")
    print(f"  --config-file        Path to the YAML config file containing API credentials.")
    print(f"{Fore.YELLOW}Example:")
    print(f"  dumpdork 'site:\"*.hackerone.com\" ext:php' --output h1_results.json --limit 100 --config-file config.yaml")
    print(f"  dumpdork 'inurl:login (ext:php | ext:asp | ext:aspx | ext:aspxh)' --output juicy_results.json --config-file config.yaml")
    print(f"  dumpdork 'intitle:\"Index of /\" | intitle:\"index of\" | intitle:\"Directory listing\"' --config-file config.yaml")

def main():
    parser = argparse.ArgumentParser(description='Perform a search using RapidAPI.')
    parser.add_argument('query', nargs='?', type=str, help='The search query.')
    parser.add_argument('--limit', type=int, default=50, help='Number of results to return (default is 50).')
    parser.add_argument('--output', type=str, help='Output file to save results in JSON format.')
    parser.add_argument('--config-file', type=str, required=True, help='Path to the YAML config file containing API credentials.')

    args = parser.parse_args()

    if args.limit > 300:
        print(f"{Fore.RED}Error: El límite máximo permitido es 300.")
        sys.exit(1)

    if args.query is None:
        print_help()
        sys.exit(1)

    config = load_config(args.config_file)
    host = config['rapidapi']['host']
    key = config['rapidapi']['key']

    response = rapidapi_search(args.query, args.limit, host, key)
    
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
    main()  # Llama a la función main
