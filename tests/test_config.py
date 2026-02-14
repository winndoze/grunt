"""Tests for loading and saving the grunt configuration file."""

import pytest
from pathlib import Path

from grunt import config as config_module


@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    """Redirect CONFIG_PATH to a temporary file for each test."""
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(config_module, "CONFIG_PATH", config_path)
    return config_path


def test_load_config_returns_none_when_no_file():
    assert config_module.load_config() is None


def test_save_config_creates_file(tmp_config):
    config_module.save_config("/tmp/notes")
    assert tmp_config.exists()


def test_save_and_load_config_roundtrip(tmp_config):
    config_module.save_config("/tmp/notes")
    cfg = config_module.load_config()
    assert cfg is not None
    assert cfg["data_dir"] == "/tmp/notes"


def test_save_config_overwrites_existing(tmp_config):
    config_module.save_config("/tmp/old")
    config_module.save_config("/tmp/new")
    cfg = config_module.load_config()
    assert cfg["data_dir"] == "/tmp/new"


def test_save_config_creates_parent_dirs(tmp_path, monkeypatch):
    deep_path = tmp_path / "a" / "b" / "config.toml"
    monkeypatch.setattr(config_module, "CONFIG_PATH", deep_path)
    config_module.save_config("/tmp/notes")
    assert deep_path.exists()


def test_get_data_dir_expands_home():
    path = config_module.get_data_dir({"data_dir": "~/notes"})
    assert path == Path.home() / "notes"


def test_get_data_dir_absolute_path():
    path = config_module.get_data_dir({"data_dir": "/tmp/notes"})
    assert path == Path("/tmp/notes")
