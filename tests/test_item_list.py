"""Tests for ItemRow and ItemList widgets."""

import pytest
from datetime import date

from grunt.models import Memo, Todo
from grunt.widgets.item_list import ItemList, ItemRow


@pytest.fixture
def todos():
    return [
        Todo(title="Alpha", priority="high", slug="alpha", created="2026-01-01"),
        Todo(title="Beta", priority="medium", slug="beta", done=True, created="2026-01-02"),
        Todo(title="Gamma", priority="low", slug="gamma", archived=True, created="2026-01-03"),
    ]


@pytest.fixture
def memos():
    return [
        Memo(title="Note A", slug="note-a", created="2026-01-01"),
        Memo(title="Note B", slug="note-b", created="2026-01-02", archived=True),
    ]


async def _make_list(items):
    from textual.app import App, ComposeResult
    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ItemList(id="lst")
    app = TestApp()
    async with app.run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(items)
        await pilot.pause(0.1)
        return pilot, lst


@pytest.fixture
def _app_class():
    from textual.app import App, ComposeResult
    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ItemList(id="lst")
    return TestApp


async def test_load_items_count(_app_class, todos):
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(todos)
        await pilot.pause(0.1)
        rows = list(lst.query(ItemRow))
        assert len(rows) == 3


async def test_load_items_stores_items(_app_class, todos):
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(todos)
        await pilot.pause(0.1)
        rows = list(lst.query(ItemRow))
        assert rows[0].item.title == "Alpha"
        assert rows[1].item.title == "Beta"
        assert rows[2].item.title == "Gamma"


async def test_selected_item_returns_highlighted(_app_class, todos):
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(todos)
        await pilot.pause(0.1)
        lst.index = 1
        await pilot.pause(0.05)
        assert lst.selected_item.title == "Beta"


async def test_selected_item_none_when_empty(_app_class):
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items([])
        await pilot.pause(0.1)
        assert lst.selected_item is None


async def test_load_items_replace_previous(_app_class, todos, memos):
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(todos)
        await pilot.pause(0.1)
        lst.load_items(memos)
        await pilot.pause(0.1)
        rows = list(lst.query(ItemRow))
        assert len(rows) == 2
        assert rows[0].item.title == "Note A"


async def test_preserve_slug_restores_cursor(_app_class, todos):
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(todos, preserve_slug="beta")
        await pilot.pause(0.2)
        assert lst.index == 1


async def test_preserve_slug_missing_falls_back_to_index(_app_class, todos):
    """If slug not found (item removed), fall back to same row index."""
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(todos)
        await pilot.pause(0.1)
        lst.index = 1
        # Reload without Beta (it was archived/removed)
        remaining = [todos[0], todos[2]]
        lst.load_items(remaining, preserve_slug="beta")
        await pilot.pause(0.2)
        assert lst.index == 1  # clamped to last item (index 1 of 2)


async def test_item_row_todo_archived_label(_app_class, todos):
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(todos)
        await pilot.pause(0.1)
        rows = list(lst.query(ItemRow))
        # Gamma is archived — check the item flag
        assert rows[2].item.archived is True


async def test_item_row_todo_done_label(_app_class, todos):
    async with _app_class().run_test(headless=True) as pilot:
        lst = pilot.app.query_one("#lst", ItemList)
        lst.load_items(todos)
        await pilot.pause(0.1)
        rows = list(lst.query(ItemRow))
        assert rows[1].item.done is True
