# 🔍 DumpDork

DumpDork is a powerful command-line tool for performing Google dorking, allowing users to uncover hidden information and vulnerabilities using advanced search queries directly from the terminal.

![GitHub Release](https://img.shields.io/github/v/release/mateofumis/dumpdork)
![GitHub License](https://img.shields.io/github/license/mateofumis/dumpdork)
![PyPI - Version](https://img.shields.io/pypi/v/dumpdork)
![PyPI - Downloads](https://img.shields.io/pypi/dm/dumpdork)

![preview](https://raw.githubusercontent.com/mateofumis/dumpdork/main/preview.gif)

## Features

- **Multi-Engine Support**: Perform searches across **Google**, **Brave**, and **GitHub** from a single interface.
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
$: pip3 install dumpdork
# or as well with pipx
$: pipx install dumpdork
```

See this project in PyPi: [https://pypi.org/project/dumpdork/](https://pypi.org/project/dumpdork/) 

## Configuration

DumpDork stores its configuration in `~/.config/dumpdork/config.yaml`.

### The Easy Way (Wizard)

Simply run the tool with the wizard flag to set up your keys interactively:

```bash
$: python3 dumpdork.py -w
```

### Manual Configuration

Create the file with the following structure:

```yaml
rapidapi:
  host: google-search74.p.rapidapi.com
  keys:
    google: "YOUR_RAPIDAPI_KEY"
    brave: "YOUR_RAPIDAPI_KEY"
    github: "YOUR_GITHUB_TOKEN"
```

**[*] See detailed instructions at: https://github.com/mateofumis/dumpdork/blob/main/API_SETUP_GUIDE.md**

## Usage

```
$: dumpdork
    ____                        ____             _
   |  _ \ _   _ _ __ ___  _ __ |  _ \  ___  _ __| | __
   | | | | | | | '_ ` _ \| '_ \| | | |/ _ \| '__| |/ /
   | |_| | |_| | | | | | | |_) | |_| | (_) | |  |   <
   |____/ \__,_|_| |_| |_| .__/|____/ \___/|_|  |_|\_\
                         |_|
             Advanced Dorking Tool v1.0
       Created by: Mateo Fumis (hackermater)

usage: dumpdork.py [-h] [-s {google,github,brave}] [-l LIMIT] [-o OUTPUT] [-w] [query]

Use -h or --help for full details.
```

Example Queries

- Search for AWS Leaked Credentials (Google):

```bash
$: dumpdork 'site:*.example.com AND (intext:"aws_access_key_id" | intext:"aws_secret_access_key" filetype:json | filetype:yaml) ' --limit 200 --output aws_credentials.json
```

- Find Sensitive Repositories (GitHub):

```bash
$: dumpdork -s github "filename:config.php 'DB_PASSWORD'"
```

- Search via Brave Search:

```bash
$: dumpdork -s brave "inurl:admin login"
```

- Save Results to JSON:

```bash
$: dumpdork "sensitive data" -o results.json
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
