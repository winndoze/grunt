"""Tests for CLI quick-add and argument parsing."""

import pytest
from pathlib import Path
from unittest.mock import patch
from datetime import date

from grunt.main import _parse_args, _quick_add
from grunt.storage import list_items


@pytest.fixture
def data_dir(tmp_path):
    for d in ["todo", "memo", "archive/todo", "archive/memo"]:
        (tmp_path / d).mkdir(parents=True)
    return tmp_path


# --- _parse_args ---

def test_parse_args_no_args():
    with patch("sys.argv", ["grunt"]):
        title, priority, due = _parse_args()
    assert title is None
    assert priority == "medium"
    assert due is None


def test_parse_args_title_only():
    with patch("sys.argv", ["grunt", "Buy milk"]):
        title, priority, due = _parse_args()
    assert title == "Buy milk"
    assert priority == "medium"
    assert due is None


def test_parse_args_with_priority():
    with patch("sys.argv", ["grunt", "Urgent task", "-p", "high"]):
        title, priority, due = _parse_args()
    assert title == "Urgent task"
    assert priority == "high"


def test_parse_args_with_long_priority():
    with patch("sys.argv", ["grunt", "Low key", "--priority", "low"]):
        title, priority, due = _parse_args()
    assert priority == "low"


def test_parse_args_with_due():
    with patch("sys.argv", ["grunt", "Task", "-d", "2026-03-15"]):
        title, priority, due = _parse_args()
    assert due == "2026-03-15"


def test_parse_args_with_long_due():
    with patch("sys.argv", ["grunt", "Task", "--due", "2026-06-01"]):
        title, priority, due = _parse_args()
    assert due == "2026-06-01"


def test_parse_args_all_options():
    with patch("sys.argv", ["grunt", "Full task", "-p", "high", "-d", "2026-03-01"]):
        title, priority, due = _parse_args()
    assert title == "Full task"
    assert priority == "high"
    assert due == "2026-03-01"


def test_parse_args_invalid_priority_exits():
    with patch("sys.argv", ["grunt", "Task", "-p", "urgent"]):
        with pytest.raises(SystemExit):
            _parse_args()


# --- _quick_add ---

def test_quick_add_creates_file(data_dir, capsys):
    with patch("grunt.main._resolve_data_dir", return_value=data_dir), \
         patch("grunt.main.git_add_commit"):
        _quick_add("Buy groceries", "medium", None)
    todos = list_items(data_dir, "todo")
    assert len(todos) == 1
    assert todos[0].title == "Buy groceries"


def test_quick_add_sets_priority(data_dir, capsys):
    with patch("grunt.main._resolve_data_dir", return_value=data_dir), \
         patch("grunt.main.git_add_commit"):
        _quick_add("Urgent thing", "high", None)
    todos = list_items(data_dir, "todo")
    assert todos[0].priority == "high"


def test_quick_add_sets_due(data_dir, capsys):
    with patch("grunt.main._resolve_data_dir", return_value=data_dir), \
         patch("grunt.main.git_add_commit"):
        _quick_add("Deadline task", "medium", "2026-04-01")
    todos = list_items(data_dir, "todo")
    assert todos[0].due == "2026-04-01"


def test_quick_add_prints_confirmation(data_dir, capsys):
    with patch("grunt.main._resolve_data_dir", return_value=data_dir), \
         patch("grunt.main.git_add_commit"):
        _quick_add("Print me", "low", None)
    out = capsys.readouterr().out
    assert "Print me" in out
    assert "low" in out


def test_quick_add_prints_due_in_confirmation(data_dir, capsys):
    with patch("grunt.main._resolve_data_dir", return_value=data_dir), \
         patch("grunt.main.git_add_commit"):
        _quick_add("Due task", "medium", "2026-05-10")
    out = capsys.readouterr().out
    assert "2026-05-10" in out


def test_quick_add_no_data_dir_does_nothing(capsys):
    with patch("grunt.main._resolve_data_dir", return_value=None):
        _quick_add("Orphan task", "medium", None)
    out = capsys.readouterr().out
    assert out == ""


def test_quick_add_multiple_todos(data_dir, capsys):
    with patch("grunt.main._resolve_data_dir", return_value=data_dir), \
         patch("grunt.main.git_add_commit"):
        _quick_add("First", "medium", None)
        _quick_add("Second", "high", None)
    todos = list_items(data_dir, "todo")
    assert len(todos) == 2
    titles = {t.title for t in todos}
    assert titles == {"First", "Second"}
