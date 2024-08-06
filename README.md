# DumpDork

DumpDork is a powerful command-line tool for performing Google dorking, allowing users to uncover hidden information and vulnerabilities using advanced search queries directly from the terminal.

## Features

- **Effortless Querying**: Construct complex search queries with ease using Google's powerful search operators.
- **Customizable Results**: Specify the number of results to retrieve, with a maximum limit of 300.
- **Output Options**: Save your findings in a neatly formatted JSON file for further analysis or reporting.
- **No CAPTCHA Required**: This script does not require users to complete CAPTCHA, making it easier to retrieve results without interruptions.
- **Configurable Credentials**: Manage your API credentials securely through a simple YAML configuration file.

## Installation

1. **Clone the repository**:

```bash
git clone https://github.com/mateofumis/dumpdork.git
cd dumpdork
```

Set up a virtual environment (optional but recommended):

```bash
python3 -m venv env
source env/bin/activate  # On Windows use `.\env\Scripts\activate`
```

## Install dependencies:

```bash
pip3 install -r requirements.txt
```

Configure your API credentials:
Create a config.yaml file in the root directory with the following structure:

```yaml
rapidapi:
  host: "YOUR_RAPIDAPI_HOST"
  key: "YOUR_RAPIDAPI_KEY"
```

## Usage

To use DumpDork, run the following command in your terminal:

```bash
python3 dumpdork.py 'your search query' --limit 100 --output results.json --config-file config.yaml
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
Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.
