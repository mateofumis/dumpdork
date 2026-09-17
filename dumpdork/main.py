"""Compatibility entry point for existing package imports."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
