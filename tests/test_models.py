"""Tests for grunt data models, slugification, and slug uniqueness."""

import pytest
from grunt.models import Memo, Todo, slugify, unique_slug


# --- slugify ---

def test_slugify_basic():
    assert slugify("Buy groceries") == "buy-groceries"


def test_slugify_uppercase():
    assert slugify("Hello World") == "hello-world"


def test_slugify_special_chars_stripped():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_multiple_spaces():
    assert slugify("foo   bar") == "foo-bar"


def test_slugify_leading_trailing_hyphens():
    assert slugify("  - foo - ") == "foo"


def test_slugify_empty_string():
    assert slugify("") == "untitled"


def test_slugify_only_special_chars():
    assert slugify("!!!") == "untitled"


def test_slugify_underscores_become_hyphens():
    assert slugify("foo_bar") == "foo-bar"


def test_slugify_long_title_truncated():
    long = "a" * 60
    assert len(slugify(long)) <= 50


def test_slugify_truncate_no_trailing_hyphen():
    # Place a word boundary exactly at the cut point to ensure no trailing dash
    title = "a" * 49 + " extra words here"
    result = slugify(title)
    assert not result.endswith("-")
    assert len(result) <= 50


def test_slugify_custom_max_len():
    assert len(slugify("hello world foo bar baz", max_len=10)) <= 10


# --- unique_slug ---

def test_unique_slug_no_collision():
    assert unique_slug("foo", set()) == "foo"


def test_unique_slug_first_collision():
    assert unique_slug("foo", {"foo"}) == "foo-2"


def test_unique_slug_multiple_collisions():
    assert unique_slug("foo", {"foo", "foo-2", "foo-3"}) == "foo-4"


def test_unique_slug_uses_slugify():
    assert unique_slug("My Task", set()) == "my-task"


# --- Todo ---

def test_todo_default_priority():
    assert Todo(title="Task").priority == "medium"


def test_todo_default_done():
    assert Todo(title="Task").done is False


def test_todo_default_done_at():
    assert Todo(title="Task").done_at is None


def test_todo_default_due():
    assert Todo(title="Task").due is None


def test_todo_default_archived():
    assert Todo(title="Task").archived is False


def test_todo_slug_auto_generated():
    assert Todo(title="My Task").slug == "my-task"


def test_todo_slug_not_overwritten_when_provided():
    assert Todo(title="My Task", slug="custom").slug == "custom"


def test_todo_item_type():
    assert Todo(title="Task").item_type == "todo"


def test_todo_created_set_today():
    from datetime import date
    assert Todo(title="Task").created == date.today().isoformat()


def test_todo_stores_explicit_values():
    t = Todo(title="Fix bug", priority="high", due="2026-03-01", done=True, done_at="2026-02-14T10:00:00")
    assert t.priority == "high"
    assert t.due == "2026-03-01"
    assert t.done is True
    assert t.done_at == "2026-02-14T10:00:00"


# --- Memo ---

def test_memo_default_body():
    assert Memo(title="Notes").body == ""


def test_memo_default_updated():
    assert Memo(title="Notes").updated == ""


def test_memo_default_archived():
    assert Memo(title="Notes").archived is False


def test_memo_slug_auto_generated():
    assert Memo(title="Project Notes").slug == "project-notes"


def test_memo_item_type():
    assert Memo(title="Notes").item_type == "memo"


def test_memo_created_set_today():
    from datetime import date
    assert Memo(title="Notes").created == date.today().isoformat()
