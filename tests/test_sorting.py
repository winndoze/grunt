"""Tests for the todo and memo sort helper functions."""

import pytest

from grunt.app import _sort_memos, _sort_todos
from grunt.models import Memo, Todo


@pytest.fixture
def todos():
    """A mixed set of todos with varying priority, due date, and created date."""
    return [
        Todo(title="Low task",    priority="low",    created="2026-01-01"),
        Todo(title="High task",   priority="high",   due="2026-03-01", created="2026-01-02"),
        Todo(title="Medium task", priority="medium", due="2026-02-01", created="2026-01-03"),
    ]


@pytest.fixture
def memos():
    """A mixed set of memos with varying created and updated dates."""
    return [
        Memo(title="Old memo", created="2026-01-01", updated="2026-01-10"),
        Memo(title="New memo", created="2026-02-01", updated="2026-01-05"),
        Memo(title="Mid memo", created="2026-01-15", updated="2026-01-20"),
    ]


# --- _sort_todos ---

def test_sort_todos_priority_high_first(todos):
    result = _sort_todos(todos, "priority")
    assert result[0].priority == "high"


def test_sort_todos_priority_medium_second(todos):
    result = _sort_todos(todos, "priority")
    assert result[1].priority == "medium"


def test_sort_todos_priority_low_last(todos):
    result = _sort_todos(todos, "priority")
    assert result[2].priority == "low"


def test_sort_todos_due_date_earliest_first(todos):
    result = _sort_todos(todos, "due date")
    assert result[0].title == "Medium task"  # due 2026-02-01
    assert result[1].title == "High task"    # due 2026-03-01


def test_sort_todos_due_date_no_due_last(todos):
    result = _sort_todos(todos, "due date")
    assert result[-1].title == "Low task"    # no due date


def test_sort_todos_created_newest_first(todos):
    result = _sort_todos(todos, "created")
    assert result[0].created == "2026-01-03"
    assert result[1].created == "2026-01-02"
    assert result[2].created == "2026-01-01"


def test_sort_todos_unknown_key_falls_back_to_priority(todos):
    """An unrecognised sort key should fall back to priority order."""
    result = _sort_todos(todos, "unknown")
    assert result[0].priority == "high"


def test_sort_todos_priority_tiebreak_by_due_date():
    """Within the same priority, items with earlier due dates come first."""
    t1 = Todo(title="A", priority="medium", due="2026-03-01")
    t2 = Todo(title="B", priority="medium", due="2026-02-01")
    result = _sort_todos([t1, t2], "priority")
    assert result[0].title == "B"


def test_sort_todos_preserves_all_items(todos):
    assert len(_sort_todos(todos, "priority")) == 3
    assert len(_sort_todos(todos, "due date")) == 3
    assert len(_sort_todos(todos, "created")) == 3


def test_sort_todos_empty_list():
    assert _sort_todos([], "priority") == []


# --- _sort_memos ---

def test_sort_memos_created_newest_first(memos):
    result = _sort_memos(memos, "created")
    assert result[0].created == "2026-02-01"
    assert result[1].created == "2026-01-15"
    assert result[2].created == "2026-01-01"


def test_sort_memos_updated_most_recent_first(memos):
    result = _sort_memos(memos, "updated")
    assert result[0].updated == "2026-01-20"
    assert result[1].updated == "2026-01-10"
    assert result[2].updated == "2026-01-05"


def test_sort_memos_updated_falls_back_to_created_when_no_updated():
    """Memos without an updated date should fall back to created for ordering."""
    m1 = Memo(title="A", created="2026-01-01", updated="")
    m2 = Memo(title="B", created="2026-02-01", updated="")
    result = _sort_memos([m1, m2], "updated")
    assert result[0].title == "B"


def test_sort_memos_preserves_all_items(memos):
    assert len(_sort_memos(memos, "created")) == 3
    assert len(_sort_memos(memos, "updated")) == 3


def test_sort_memos_empty_list():
    assert _sort_memos([], "created") == []
