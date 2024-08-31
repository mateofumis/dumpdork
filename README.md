# 🔍 DumpDork

DumpDork is a powerful command-line tool for performing Google dorking, allowing users to uncover hidden information and vulnerabilities using advanced search queries directly from the terminal.

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

### Using pip install

1. Install dumpdork with pip3

```bash
pip3 install dumpdork
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

## Usage

```bash
$: dumpdork -h
usage: dumpdork.py [-h] [--limit LIMIT] [--output OUTPUT] [--config-file CONFIG_FILE] [--wizard] [query]

Perform a search using RapidAPI.

positional arguments:
  query                 The search query.

options:
  -h, --help            show this help message and exit
  --limit LIMIT         Number of results to return (default is 50. Limit: 300).
  --output OUTPUT       Output file to save results in JSON format.
  --config-file CONFIG_FILE
                        Path to the YAML config file containing API credentials.
  --wizard              Set up your API key for dumpdork, step by step with easy.
```

Example Queries

- Search for PHP files on HackerOne:

```bash
python3 dumpdork.py 'site:"*.hackerone.com" ext:php' --output h1_results.json --limit 100 --config-file config.yaml
```

- Find login pages:

```bash
python3 dumpdork.py 'inurl:login (ext:php | ext:asp | ext:aspx | ext:aspxh)' --output juicy_results.json --config-file config.yaml
```

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## 🧡 Support me with a virtual Coffee! 🧡

[![Ko-Fi](https://storage.ko-fi.com/cdn/brandasset/kofi_button_stroke.png)](https://ko-fi.com/hackermater)
