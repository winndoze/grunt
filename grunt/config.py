"""Handles loading and saving the grunt user configuration file."""

from __future__ import annotations

import tomllib
from pathlib import Path

import tomli_w

CONFIG_PATH = Path.home() / ".config" / "grunt" / "config.toml"


def load_config() -> dict | None:
    """Return config dict or None if no config file exists."""
    if not CONFIG_PATH.exists():
        return None
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def save_config(data_dir: str) -> None:
    """Write the given data_dir path to the config file, creating it if necessary."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = {"data_dir": data_dir}
    CONFIG_PATH.write_bytes(tomli_w.dumps(config).encode())


def get_data_dir(config: dict) -> Path:
    """Extract and expand the data directory path from the config dictionary."""
    return Path(config["data_dir"]).expanduser()
