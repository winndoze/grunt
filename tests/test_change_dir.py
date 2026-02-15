"""Tests for the change-directory feature (C key and SetupScreen in change mode)."""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

from grunt.app import GruntApp
from grunt.models import Todo
from grunt.screens.setup import SetupScreen
from grunt.storage import write_item
from grunt.widgets.item_list import ItemList, ItemRow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_dir(tmp_path, name):
    d = tmp_path / name
    for sub in ["todo", "memo", "archive/todo", "archive/memo"]:
        (d / sub).mkdir(parents=True)
    return d


@pytest.fixture
def dir_a(tmp_path):
    d = _make_dir(tmp_path, "dir_a")
    write_item(d, Todo(title="Task in A", created=date.today().isoformat()), is_new=True)
    return d


@pytest.fixture
def dir_b(tmp_path):
    d = _make_dir(tmp_path, "dir_b")
    write_item(d, Todo(title="Task in B", created=date.today().isoformat()), is_new=True)
    return d


def make_app(data_dir):
    return GruntApp(data_dir, {})


# ---------------------------------------------------------------------------
# SetupScreen in change-dir mode (unit)
# ---------------------------------------------------------------------------

async def test_setup_screen_shows_current_dir():
    """Input should be pre-filled with the current directory."""
    from textual.app import App, ComposeResult

    class TestApp(App):
        def compose(self) -> ComposeResult:
            return []

    async with TestApp().run_test(headless=True) as pilot:
        from textual.widgets import Input
        await pilot.app.push_screen(SetupScreen(current="/some/path"))
        await pilot.pause(0.1)
        inp = pilot.app.screen.query_one("#data-dir-input", Input)
        assert inp.value == "/some/path"


async def test_setup_screen_escape_dismisses_with_none():
    """Escape should dismiss returning None when a current dir is set."""
    from textual.app import App, ComposeResult

    results = []

    class TestApp(App):
        def compose(self) -> ComposeResult:
            return []

    async with TestApp().run_test(headless=True) as pilot:
        await pilot.app.push_screen(
            SetupScreen(current="/some/path"),
            lambda r: results.append(r),
        )
        await pilot.pause(0.1)
        await pilot.press("escape")
        await pilot.pause(0.1)
    assert results == [None]


async def test_setup_screen_submit_dismisses_with_value():
    """Submitting returns the typed path."""
    from textual.app import App, ComposeResult
    from textual.widgets import Input

    results = []

    class TestApp(App):
        def compose(self) -> ComposeResult:
            return []

    async with TestApp().run_test(headless=True) as pilot:
        await pilot.app.push_screen(
            SetupScreen(current="/old"),
            lambda r: results.append(r),
        )
        await pilot.pause(0.1)
        inp = pilot.app.screen.query_one("#data-dir-input", Input)
        inp.clear()
        await pilot.press(*"/new/path")
        await pilot.press("enter")
        await pilot.pause(0.1)
    assert results == ["/new/path"]


# ---------------------------------------------------------------------------
# GruntApp change-dir integration
# ---------------------------------------------------------------------------

async def test_C_key_opens_setup_screen(dir_a):
    """Pressing C should push a SetupScreen."""
    async with make_app(dir_a).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("C")
        await pilot.pause(0.1)
        screens = [type(s).__name__ for s in pilot.app.screen_stack]
        assert "SetupScreen" in screens


async def test_C_key_setup_prefilled_with_current_dir(dir_a):
    """SetupScreen opened via C should be pre-filled with the current data dir."""
    from textual.widgets import Input
    async with make_app(dir_a).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("C")
        await pilot.pause(0.1)
        inp = pilot.app.screen.query_one("#data-dir-input", Input)
        assert inp.value == str(dir_a)


async def test_escape_cancel_restores_focus(dir_a):
    """Pressing Escape in the change-dir prompt should restore focus to the list."""
    async with make_app(dir_a).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        await pilot.press("C")
        await pilot.pause(0.1)
        await pilot.press("escape")
        await pilot.pause(0.2)
        focused = pilot.app.focused
        assert isinstance(focused, ItemList)
        assert focused.id == "todo-list"


async def test_escape_cancel_does_not_change_data_dir(dir_a):
    """Cancelling the prompt should leave data_dir unchanged."""
    async with make_app(dir_a).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        original = pilot.app.data_dir
        await pilot.press("C")
        await pilot.pause(0.1)
        await pilot.press("escape")
        await pilot.pause(0.2)
        assert pilot.app.data_dir == original


async def test_change_dir_updates_data_dir(dir_a, dir_b):
    """Confirming a new path should update app.data_dir."""
    from textual.widgets import Input
    with patch("grunt.app.save_config"), \
         patch("grunt.app.git_init", new=AsyncMock()):
        async with make_app(dir_a).run_test(headless=True) as pilot:
            await pilot.pause(0.2)
            await pilot.press("C")
            await pilot.pause(0.1)
            inp = pilot.app.screen.query_one("#data-dir-input", Input)
            inp.clear()
            await pilot.press(*str(dir_b))
            await pilot.press("enter")
            await pilot.pause(0.3)
            assert pilot.app.data_dir == dir_b


async def test_change_dir_reloads_items_from_new_dir(dir_a, dir_b):
    """After changing directory the list should show items from the new dir."""
    from textual.widgets import Input
    with patch("grunt.app.save_config"), \
         patch("grunt.app.git_init", new=AsyncMock()):
        async with make_app(dir_a).run_test(headless=True) as pilot:
            await pilot.pause(0.2)
            await pilot.press("C")
            await pilot.pause(0.1)
            inp = pilot.app.screen.query_one("#data-dir-input", Input)
            inp.clear()
            await pilot.press(*str(dir_b))
            await pilot.press("enter")
            await pilot.pause(0.3)
            todo_list = pilot.app.query_one("#todo-list", ItemList)
            titles = [r.item.title for r in todo_list.query(ItemRow)]
            assert titles == ["Task in B"]


async def test_change_dir_restores_focus(dir_a, dir_b):
    """After a successful directory change focus should be on the todo list."""
    from textual.widgets import Input
    with patch("grunt.app.save_config"), \
         patch("grunt.app.git_init", new=AsyncMock()):
        async with make_app(dir_a).run_test(headless=True) as pilot:
            await pilot.pause(0.2)
            await pilot.press("C")
            await pilot.pause(0.1)
            inp = pilot.app.screen.query_one("#data-dir-input", Input)
            inp.clear()
            await pilot.press(*str(dir_b))
            await pilot.press("enter")
            await pilot.pause(0.3)
            focused = pilot.app.focused
            assert isinstance(focused, ItemList)
            assert focused.id == "todo-list"


async def test_change_dir_updates_subtitle(dir_a, dir_b):
    """After changing directory the app subtitle should reflect the new path."""
    from textual.widgets import Input
    with patch("grunt.app.save_config"), \
         patch("grunt.app.git_init", new=AsyncMock()):
        async with make_app(dir_a).run_test(headless=True) as pilot:
            await pilot.pause(0.2)
            await pilot.press("C")
            await pilot.pause(0.1)
            inp = pilot.app.screen.query_one("#data-dir-input", Input)
            inp.clear()
            await pilot.press(*str(dir_b))
            await pilot.press("enter")
            await pilot.pause(0.3)
            assert pilot.app.sub_title == str(dir_b)


async def test_same_dir_submitted_does_not_change_data_dir(dir_a):
    """Submitting the same directory should be a no-op."""
    from textual.widgets import Input
    async with make_app(dir_a).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        original = pilot.app.data_dir
        await pilot.press("C")
        await pilot.pause(0.1)
        # value is already pre-filled with dir_a — just hit enter
        await pilot.press("enter")
        await pilot.pause(0.3)
        assert pilot.app.data_dir == original


async def test_subtitle_shows_data_dir_on_startup(dir_a):
    """The app subtitle should be set to the data dir immediately on mount."""
    async with make_app(dir_a).run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        assert pilot.app.sub_title == str(dir_a)
