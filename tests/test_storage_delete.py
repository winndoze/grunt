"""Tests for storage.delete_item."""

import pytest
from pathlib import Path
from datetime import date

from grunt.models import Memo, Todo
from grunt.storage import delete_item, item_path, write_item


@pytest.fixture
def data_dir(tmp_path):
    for d in ["todo", "memo", "archive/todo", "archive/memo"]:
        (tmp_path / d).mkdir(parents=True)
    return tmp_path


def test_delete_todo_removes_file(data_dir):
    todo = Todo(title="To delete", created=date.today().isoformat())
    write_item(data_dir, todo, is_new=True)
    path = item_path(data_dir, todo)
    assert path.exists()
    deleted = delete_item(data_dir, todo)
    assert not path.exists()
    assert deleted == path


def test_delete_memo_removes_file(data_dir):
    memo = Memo(title="Delete me", created=date.today().isoformat())
    write_item(data_dir, memo, is_new=True)
    path = item_path(data_dir, memo)
    assert path.exists()
    delete_item(data_dir, memo)
    assert not path.exists()


def test_delete_missing_file_does_not_raise(data_dir):
    todo = Todo(title="Ghost", slug="ghost", created=date.today().isoformat())
    # File never written — should not raise
    delete_item(data_dir, todo)


def test_delete_archived_todo(data_dir):
    todo = Todo(title="Archive then delete", created=date.today().isoformat())
    write_item(data_dir, todo, is_new=True)
    todo.archived = True
    # Move file manually
    src = data_dir / "todo" / f"{todo.slug}.md"
    dst = data_dir / "archive" / "todo" / f"{todo.slug}.md"
    src.rename(dst)
    path = item_path(data_dir, todo)
    assert path.exists()
    delete_item(data_dir, todo)
    assert not path.exists()
