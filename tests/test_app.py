"""Integration tests for GruntApp actions and UI behaviour."""

import pytest
from pathlib import Path
from datetime import date

from grunt.app import GruntApp
from grunt.models import Memo, Todo
from grunt.storage import write_item
from grunt.widgets.item_list import ItemList, ItemRow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def data_dir(tmp_path):
    for d in ["todo", "memo", "archive/todo", "archive/memo"]:
        (tmp_path / d).mkdir(parents=True)
    return tmp_path


@pytest.fixture
def populated_dir(data_dir):
    """Data dir with 3 todos and 2 memos."""
    for title in ["Alpha", "Beta", "Gamma"]:
        write_item(data_dir, Todo(title=title, created=date.today().isoformat()), is_new=True)
    for title in ["Note A", "Note B"]:
        write_item(data_dir, Memo(title=title, created=date.today().isoformat()), is_new=True)
    return data_dir


def make_app(data_dir):
    return GruntApp(data_dir, {})


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def test_app_starts_and_shows_todos(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        rows = list(todo_list.query(ItemRow))
        assert len(rows) == 3


async def test_app_starts_focused_on_todo_list(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        focused = pilot.app.focused
        assert isinstance(focused, ItemList)
        assert focused.id == "todo-list"


# ---------------------------------------------------------------------------
# Tab switching
# ---------------------------------------------------------------------------

async def test_2_key_switches_to_memos_from_todos(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("2")
        await pilot.pause(0.1)
        from textual.widgets import TabbedContent
        tabs = pilot.app.query_one("#tabs", TabbedContent)
        assert tabs.active == "tab-memos"


async def test_key_1_switches_to_todos(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("tab")   # go to memos
        await pilot.pause(0.1)
        await pilot.press("1")     # back to todos
        await pilot.pause(0.1)
        from textual.widgets import TabbedContent
        tabs = pilot.app.query_one("#tabs", TabbedContent)
        assert tabs.active == "tab-todos"


async def test_key_2_switches_to_memos(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("2")
        await pilot.pause(0.1)
        from textual.widgets import TabbedContent
        tabs = pilot.app.query_one("#tabs", TabbedContent)
        assert tabs.active == "tab-memos"


# ---------------------------------------------------------------------------
# New item
# ---------------------------------------------------------------------------

async def test_n_opens_edit_todo_screen(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("n")
        await pilot.pause(0.1)
        screens = [type(s).__name__ for s in pilot.app.screen_stack]
        assert "EditTodoScreen" in screens


async def test_n_on_memo_tab_opens_edit_memo_screen(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("2")
        await pilot.pause(0.1)
        await pilot.press("n")
        await pilot.pause(0.1)
        screens = [type(s).__name__ for s in pilot.app.screen_stack]
        assert "EditMemoScreen" in screens


async def test_new_todo_saved_appears_in_list(data_dir):
    async with make_app(data_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("n")
        await pilot.pause(0.1)
        await pilot.press(*"New Task")
        await pilot.press("ctrl+s")
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        titles = [r.item.title for r in todo_list.query(ItemRow)]
        assert "New Task" in titles


async def test_new_todo_written_to_disk(data_dir):
    async with make_app(data_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("n")
        await pilot.pause(0.1)
        await pilot.press(*"Disk Task")
        await pilot.press("ctrl+s")
        await pilot.pause(0.2)
    files = list((data_dir / "todo").glob("*.md"))
    assert len(files) == 1


# ---------------------------------------------------------------------------
# Edit item
# ---------------------------------------------------------------------------

async def test_enter_opens_edit_screen(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        todo_list.index = 0
        await pilot.pause(0.05)
        await pilot.press("enter")
        await pilot.pause(0.1)
        screens = [type(s).__name__ for s in pilot.app.screen_stack]
        assert "EditTodoScreen" in screens


async def test_edit_todo_updates_title_on_disk(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        todo_list.index = 0
        await pilot.pause(0.05)
        await pilot.press("enter")
        await pilot.pause(0.1)
        from textual.widgets import Input
        title_input = pilot.app.screen.query_one("#title-input", Input)
        title_input.clear()
        await pilot.press(*"Renamed")
        await pilot.press("ctrl+s")
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        titles = [r.item.title for r in todo_list.query(ItemRow)]
        assert "Renamed" in titles


# ---------------------------------------------------------------------------
# Toggle done
# ---------------------------------------------------------------------------

async def test_x_toggles_done(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        todo_list.index = 0
        await pilot.pause(0.1)
        item_before = todo_list.selected_item
        assert item_before is not None
        was_done = item_before.done
        await pilot.press("x")
        await pilot.pause(0.2)
        # Reload the item from the updated list
        todo_list2 = pilot.app.query_one("#todo-list", ItemList)
        rows = list(todo_list2.query(ItemRow))
        slug = item_before.slug
        updated = next(r.item for r in rows if r.item.slug == slug)
        assert updated.done == (not was_done)


async def test_x_preserves_cursor_position(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        todo_list.index = 1
        await pilot.pause(0.05)
        await pilot.press("x")
        await pilot.pause(0.3)
        assert todo_list.index == 1


# ---------------------------------------------------------------------------
# Archive
# ---------------------------------------------------------------------------

async def test_a_archives_item(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        todo_list.index = 0
        await pilot.pause(0.05)
        await pilot.press("a")
        await pilot.pause(0.2)
        rows = list(todo_list.query(ItemRow))
        assert len(rows) == 2  # one removed from active view


async def test_a_moves_file_to_archive(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        todo_list.index = 0
        slug = todo_list.selected_item.slug
        await pilot.press("a")
        await pilot.pause(0.2)
    assert (populated_dir / "archive" / "todo" / f"{slug}.md").exists()
    assert not (populated_dir / "todo" / f"{slug}.md").exists()


async def test_shift_a_shows_archived_items(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        todo_list.index = 0
        await pilot.press("a")
        await pilot.pause(0.2)
        await pilot.press("A")
        await pilot.pause(0.2)
        rows = list(todo_list.query(ItemRow))
        assert len(rows) == 3  # all 3 visible including archived


async def test_archive_cursor_stays_on_next_item(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        todo_list = pilot.app.query_one("#todo-list", ItemList)
        todo_list.index = 0
        await pilot.pause(0.05)
        await pilot.press("a")
        await pilot.pause(0.3)
        assert todo_list.index == 0  # cursor stays at position 0 (next item)


# ---------------------------------------------------------------------------
# Sort cycling
# ---------------------------------------------------------------------------

async def test_s_cycles_todo_sort(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        assert pilot.app._todo_sort == "priority"
        await pilot.press("s")
        await pilot.pause(0.1)
        assert pilot.app._todo_sort == "due date"
        await pilot.press("s")
        await pilot.pause(0.1)
        assert pilot.app._todo_sort == "created"
        await pilot.press("s")
        await pilot.pause(0.1)
        assert pilot.app._todo_sort == "priority"


async def test_s_cycles_memo_sort(populated_dir):
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("2")
        await pilot.pause(0.1)
        assert pilot.app._memo_sort == "created"
        await pilot.press("s")
        await pilot.pause(0.1)
        assert pilot.app._memo_sort == "updated"
        await pilot.press("s")
        await pilot.pause(0.1)
        assert pilot.app._memo_sort == "created"


# ---------------------------------------------------------------------------
# Theme cycling
# ---------------------------------------------------------------------------

async def test_T_cycles_theme(populated_dir):
    from grunt.app import THEMES
    async with make_app(populated_dir).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("T")
        await pilot.pause(0.1)
        assert pilot.app.theme == THEMES[1]
        await pilot.press("T")
        await pilot.pause(0.1)
        assert pilot.app.theme == THEMES[2]
