from __future__ import annotations

from drift_engine.api.app import app
from drift_engine.cli.commands import app as cli_app

__all__ = ["app"]


def main() -> None:
    cli_app()


if __name__ == "__main__":
    main()
