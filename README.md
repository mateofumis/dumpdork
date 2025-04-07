# 🔍 DumpDork

DumpDork is a powerful command-line tool for performing Google dorking, allowing users to uncover hidden information and vulnerabilities using advanced search queries directly from the terminal.

![GitHub Release](https://img.shields.io/github/v/release/mateofumis/dumpdork)
![GitHub License](https://img.shields.io/github/license/mateofumis/dumpdork)
![PyPI - Version](https://img.shields.io/pypi/v/dumpdork)
![PyPI - Downloads](https://img.shields.io/pypi/dm/dumpdork)

![preview](https://raw.githubusercontent.com/mateofumis/dumpdork/main/preview.gif)

## Features

- **Effortless Querying**: Construct complex search queries with ease using Google's powerful search operators.
- **Customizable Results**: Specify the number of results to retrieve, with a maximum limit of 300.
- **Output Options**: Save your findings in a neatly formatted JSON file for further analysis or reporting.
- **No CAPTCHA Required**: This script does not require users to complete CAPTCHA, making it easier to retrieve results without interruptions.
- **Configurable Credentials**: Manage your API credentials securely through a simple YAML configuration file.
- **Interactive Setup Wizard**: With an user-friendly wizard which guides you through the setup process, helping you configure your API credentials settings step-by-step.

## Installation

### Manual:

1. Clone the repository:

```bash
git clone https://github.com/mateofumis/dumpdork.git
cd dumpdork
```

2. Set up a virtual environment (optional but recommended):

```bash
python3 -m venv env
source env/bin/activate  # On Windows use `.\env\Scripts\activate`
```

3. Install dependencies:

```bash
pip3 install -r requirements.txt
```

### Using pip/pipx install

1. Install dumpdork with pip3

```bash
pip3 install dumpdork
# or as well with pipx
pipx install dumpdork
```

See this project in PyPi: [https://pypi.org/project/dumpdork/](https://pypi.org/project/dumpdork/) 

## Configure your API credentials:

Create config.yaml file in `~/.config/dumpdork/config.yaml` with the following structure:

```yaml
rapidapi:
  host: google-search74.p.rapidapi.com
  key: "YOUR_RAPIDAPI_KEY"
```

### How to get your credentials

1. Visit [https://rapidapi.com/auth/login/](https://rapidapi.com/auth/login/) and create an account or sign in.
2. Once logged in, visit [https://rapidapi.com/herosAPI/api/google-search74/playground](https://rapidapi.com/herosAPI/api/google-search74/playground) and claim your FREE API credentials.
3. Done! Now you can fill your `config.yaml` with your own credentials.

**[*] See detailed instructions at: https://github.com/mateofumis/dumpdork/blob/main/API_SETUP_GUIDE.md**

## Usage

```
$: dumpdork
🔍 Welcome to DumpDork !!

Usage: dumpdork 'query' [--limit number] [--output filename.json] [--custom-config-file config.yaml]

Options:
  query                 The search query.
  --limit               Number of results to return (default is 50. Limit: 300).
  --output              Output file to save results in JSON format.
  --custom-config-file CUSTOM_CONFIG_FILE
			Path to custom YAML config file containing API credentials. Default is: ~/.config/dumpdork/config.yaml
  --wizard              Set up your API key for dumpdork, step by step with easy.

📋 Examples:
    $: dumpdork 'site:*.example.com AND (intext:"aws_access_key_id" | intext:"aws_secret_access_key" filetype:json | filetype:yaml) ' --limit 200 --output aws_credentials.json
    $: dumpdork '(site:*.example.com AND -site:docs.example.com) AND (inurl:"/login" | inurl:"/signup" | inurl:"/admin" | inurl:"/register") AND (ext:php | ext:aspx)' --limit 300 --output sqli_forms.json
    $: dumpdork 'site:*.example.com AND (intitle:"Index of /" | intitle:"index of") AND (intext:".log" | intext:".sql" | intext:".txt" | intext:".sh")' --custom-config-file ~/.config/dumpdork/config_files/credentials_01.yaml --output sensitive_files.json
```

Example Queries

- Search for AWS Leaked Credentials:

```bash
$: dumpdork 'site:*.example.com AND (intext:"aws_access_key_id" | intext:"aws_secret_access_key" filetype:json | filetype:yaml) ' --limit 200 --output aws_credentials.json
```

- Find SQL Injection Endpoints Forms:

```bash
$: dumpdork '(site:*.example.com AND -site:docs.example.com) AND (inurl:"/login" | inurl:"/signup" | inurl:"/admin" | inurl:"/register") AND (ext:php | ext:aspx)' --limit 300 --output sqli_forms.json
```

- Search for Sensitive Files or Logs:

```bash
$: dumpdork 'site:*.example.com AND (intitle:"Index of /" | intitle:"index of") AND (intext:".log" | intext:".sql" | intext:".txt" | intext:".sh")' --custom-config-file ~/.config/dumpdork/config_files/credentials_01.yaml --output sensitive_files.json
```

- Take a look at **GHDB** for more Dorks: [https://www.exploit-db.com/google-hacking-database](https://www.exploit-db.com/google-hacking-database)

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## Support me with a virtual Coffee! ❤️

If you find this tool useful, consider supporting me with a coffee!

<a href="https://ko-fi.com/hackermater">
    <img src="https://storage.ko-fi.com/cdn/brandasset/kofi_button_stroke.png" alt="Ko-Fi" width="400" />
</a>
