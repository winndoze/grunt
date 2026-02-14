"""Tests for the file-based storage layer: reading, writing, listing, and moving items."""

import pytest
from datetime import date
from pathlib import Path

from grunt.models import Memo, Todo
from grunt.storage import (
    _ensure_dirs,
    item_path,
    list_items,
    move_item,
    write_item,
)


@pytest.fixture
def data_dir(tmp_path):
    """Provide a clean temporary data directory for each test."""
    return tmp_path


# --- _ensure_dirs ---

def test_ensure_dirs_creates_all_subdirectories(data_dir):
    _ensure_dirs(data_dir)
    assert (data_dir / "todo").is_dir()
    assert (data_dir / "memo").is_dir()
    assert (data_dir / "archive" / "todo").is_dir()
    assert (data_dir / "archive" / "memo").is_dir()


def test_ensure_dirs_is_idempotent(data_dir):
    _ensure_dirs(data_dir)
    _ensure_dirs(data_dir)  # should not raise


# --- item_path ---

def test_item_path_active_todo(data_dir):
    todo = Todo(title="Task", slug="task")
    assert item_path(data_dir, todo) == data_dir / "todo" / "task.md"


def test_item_path_archived_todo(data_dir):
    todo = Todo(title="Task", slug="task", archived=True)
    assert item_path(data_dir, todo) == data_dir / "archive" / "todo" / "task.md"


def test_item_path_active_memo(data_dir):
    memo = Memo(title="Notes", slug="notes")
    assert item_path(data_dir, memo) == data_dir / "memo" / "notes.md"


def test_item_path_archived_memo(data_dir):
    memo = Memo(title="Notes", slug="notes", archived=True)
    assert item_path(data_dir, memo) == data_dir / "archive" / "memo" / "notes.md"


# --- write_item + list_items: Todo ---

def test_write_and_read_todo(data_dir):
    todo = Todo(title="Buy milk", priority="high", due="2026-03-01")
    write_item(data_dir, todo, is_new=True)
    items = list_items(data_dir, "todo")
    assert len(items) == 1
    t = items[0]
    assert t.title == "Buy milk"
    assert t.priority == "high"
    assert t.due == "2026-03-01"


def test_write_todo_creates_file(data_dir):
    todo = Todo(title="Task")
    path = write_item(data_dir, todo, is_new=True)
    assert path.exists()


def test_write_todo_persists_done_fields(data_dir):
    todo = Todo(title="Task", done=True, done_at="2026-02-14T10:00:00")
    write_item(data_dir, todo, is_new=True)
    items = list_items(data_dir, "todo")
    assert items[0].done is True
    assert items[0].done_at == "2026-02-14T10:00:00"


def test_write_todo_done_at_absent_when_not_done(data_dir):
    todo = Todo(title="Task", done=False)
    write_item(data_dir, todo, is_new=True)
    items = list_items(data_dir, "todo")
    assert items[0].done_at is None


def test_write_todo_persists_description(data_dir):
    todo = Todo(title="Task", description="Some details here")
    write_item(data_dir, todo, is_new=True)
    items = list_items(data_dir, "todo")
    assert items[0].description == "Some details here"


def test_write_todo_persists_created_date(data_dir):
    todo = Todo(title="Task", created="2026-01-01")
    write_item(data_dir, todo, is_new=True)
    items = list_items(data_dir, "todo")
    assert items[0].created == "2026-01-01"


# --- write_item + list_items: Memo ---

def test_write_and_read_memo(data_dir):
    memo = Memo(title="Project notes", body="Some body text")
    write_item(data_dir, memo, is_new=True)
    items = list_items(data_dir, "memo")
    assert len(items) == 1
    assert items[0].title == "Project notes"
    assert items[0].body == "Some body text"


def test_write_memo_sets_updated_to_today(data_dir):
    memo = Memo(title="Notes")
    write_item(data_dir, memo, is_new=True)
    items = list_items(data_dir, "memo")
    assert items[0].updated == date.today().isoformat()


def test_write_memo_persists_created_date(data_dir):
    memo = Memo(title="Notes", created="2026-01-01")
    write_item(data_dir, memo, is_new=True)
    items = list_items(data_dir, "memo")
    assert items[0].created == "2026-01-01"


# --- slug uniqueness ---

def test_new_todo_gets_unique_slug_on_collision(data_dir):
    t1 = Todo(title="Task")
    t2 = Todo(title="Task")
    write_item(data_dir, t1, is_new=True)
    write_item(data_dir, t2, is_new=True)
    slugs = {i.slug for i in list_items(data_dir, "todo")}
    assert "task" in slugs
    assert "task-2" in slugs


def test_new_memo_gets_unique_slug_on_collision(data_dir):
    m1 = Memo(title="Notes")
    m2 = Memo(title="Notes")
    write_item(data_dir, m1, is_new=True)
    write_item(data_dir, m2, is_new=True)
    slugs = {i.slug for i in list_items(data_dir, "memo")}
    assert "notes" in slugs
    assert "notes-2" in slugs


# --- list_items ---

def test_list_items_empty(data_dir):
    assert list_items(data_dir, "todo") == []
    assert list_items(data_dir, "memo") == []


def test_list_items_excludes_archived_by_default(data_dir):
    todo = Todo(title="Task")
    write_item(data_dir, todo, is_new=True)
    move_item(data_dir, todo)
    assert list_items(data_dir, "todo") == []


def test_list_items_includes_archived_when_requested(data_dir):
    todo = Todo(title="Task")
    write_item(data_dir, todo, is_new=True)
    move_item(data_dir, todo)
    items = list_items(data_dir, "todo", include_archived=True)
    assert len(items) == 1
    assert items[0].archived is True


def test_list_items_returns_both_active_and_archived(data_dir):
    t1 = Todo(title="Active")
    t2 = Todo(title="Archived")
    write_item(data_dir, t1, is_new=True)
    write_item(data_dir, t2, is_new=True)
    move_item(data_dir, t2)
    items = list_items(data_dir, "todo", include_archived=True)
    assert len(items) == 2


# --- move_item ---

def test_move_item_archives_todo(data_dir):
    todo = Todo(title="Task")
    write_item(data_dir, todo, is_new=True)
    src, dst = move_item(data_dir, todo)
    assert not src.exists()
    assert dst.exists()
    assert todo.archived is True


def test_move_item_unarchives_todo(data_dir):
    todo = Todo(title="Task")
    write_item(data_dir, todo, is_new=True)
    move_item(data_dir, todo)          # archive
    src, dst = move_item(data_dir, todo)  # unarchive
    assert not src.exists()
    assert dst.exists()
    assert todo.archived is False


def test_move_item_archives_memo(data_dir):
    memo = Memo(title="Notes")
    write_item(data_dir, memo, is_new=True)
    src, dst = move_item(data_dir, memo)
    assert not src.exists()
    assert dst.exists()
    assert memo.archived is True


def test_move_item_returns_correct_paths(data_dir):
    todo = Todo(title="Task", slug="task")
    write_item(data_dir, todo, is_new=True)
    src, dst = move_item(data_dir, todo)
    assert src == data_dir / "todo" / "task.md"
    assert dst == data_dir / "archive" / "todo" / "task.md"
