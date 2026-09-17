"""Environment-first credentials and a private YAML setup wizard."""

from dataclasses import dataclass
from getpass import getpass
import os
from pathlib import Path
import sys
import tempfile

import yaml

from .errors import ConfigError


CONFIG_FILE = Path.home() / ".config" / "dumpdork" / "config.yaml"


@dataclass(frozen=True)
class Credentials:
    brave_key: str | None = None
    github_token: str | None = None


def _read_yaml(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Cannot parse configuration at {path}.") from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read configuration at {path}.") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration at {path} must be a YAML mapping.")
    return data


def _clean(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() and value != "Not configured" else None


def _file_credentials(path: Path) -> Credentials:
    data = _read_yaml(path)
    current = data.get("credentials") or {}
    if not isinstance(current, dict):
        raise ConfigError("The 'credentials' section must be a mapping.")
    legacy = data.get("rapidapi") or {}
    if not isinstance(legacy, dict):
        legacy = {}
    legacy_keys = legacy.get("keys") or {}
    if not isinstance(legacy_keys, dict):
        legacy_keys = {}
    return Credentials(
        brave_key=_clean(current.get("brave_key")),
        github_token=_clean(current.get("github_token")) or _clean(legacy_keys.get("github")),
    )


def load_credentials(path: Path = CONFIG_FILE, environ: dict | None = None) -> Credentials:
    env = os.environ if environ is None else environ
    saved = _file_credentials(path)
    return Credentials(
        brave_key=_clean(env.get("BRAVE_API_KEY")) or saved.brave_key,
        github_token=_clean(env.get("GITHUB_TOKEN")) or saved.github_token,
    )


def save_credentials(credentials: Credentials, path: Path = CONFIG_FILE) -> None:
    directory = path.parent
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == "posix":
            directory.chmod(0o700)
        with tempfile.NamedTemporaryFile("w", dir=directory, prefix=".config-", suffix=".yaml", encoding="utf-8", delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            yaml.safe_dump(
                {"credentials": {"brave_key": credentials.brave_key or "", "github_token": credentials.github_token or ""}},
                stream,
                sort_keys=False,
            )
        os.replace(temporary, path)
    except OSError as exc:
        if "temporary" in locals():
            temporary.unlink(missing_ok=True)
        raise ConfigError(f"Cannot save configuration at {path}: {exc}") from exc


def wizard(path: Path = CONFIG_FILE) -> None:
    if not sys.stdin.isatty():
        raise ConfigError("The credential wizard requires a terminal; use environment variables for scripts.")
    current = _file_credentials(path)
    print("DumpDork credential setup (leave blank to keep a value; type 'clear' to remove it).")
    values = {}
    for label, field in (("Brave API key", "brave_key"), ("GitHub token", "github_token")):
        old = getattr(current, field)
        print(f"{label}: {'configured' if old else 'not configured'}")
        entered = getpass(f"New {label}: ").strip()
        values[field] = None if entered.lower() == "clear" else (entered or old)
    save_credentials(Credentials(**values), path)
    print(f"Credentials saved to {path}.")
