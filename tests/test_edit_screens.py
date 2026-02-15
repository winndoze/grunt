"""Tests for EditTodoScreen and EditMemoScreen."""

import pytest
from datetime import date

from grunt.models import Memo, Todo
from grunt.screens.edit_todo import EditTodoScreen
from grunt.screens.edit_memo import EditMemoScreen
from grunt.screens.date_picker import DatePickerScreen


# --- Helpers ---

def _app():
    from textual.app import App, ComposeResult
    class TestApp(App):
        def compose(self) -> ComposeResult:
            return []
    return TestApp()


# --- EditTodoScreen ---

async def test_edit_todo_new_focuses_title():
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen())
        await pilot.pause(0.1)
        from textual.widgets import Input
        focused = pilot.app.focused
        assert getattr(focused, "id", None) == "title-input"


async def test_edit_todo_cancel_returns_none():
    results = []
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen(), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.press("escape")
        await pilot.pause(0.1)
    assert results == [None]


async def test_edit_todo_save_empty_title_does_nothing():
    results = []
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen(), lambda r: results.append(r))
        await pilot.pause(0.1)
        # Don't type a title — press ctrl+s
        await pilot.press("ctrl+s")
        await pilot.pause(0.1)
        # Screen should still be open
        assert any(type(s).__name__ == "EditTodoScreen" for s in pilot.app.screen_stack)
    assert results == []


async def test_edit_todo_save_new_returns_todo():
    results = []
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen(), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.press(*"My Task")
        await pilot.press("ctrl+s")
        await pilot.pause(0.1)
    assert len(results) == 1
    assert isinstance(results[0], Todo)
    assert results[0].title == "My Task"


async def test_edit_todo_save_preserves_priority():
    results = []
    todo = Todo(title="Existing", priority="high", slug="existing",
                created=date.today().isoformat())
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen(todo), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.press("ctrl+s")
        await pilot.pause(0.1)
    assert results[0].priority == "high"


async def test_edit_todo_save_existing_returns_same_object():
    results = []
    todo = Todo(title="Edit me", slug="edit-me", created=date.today().isoformat())
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen(todo), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.press("ctrl+s")
        await pilot.pause(0.1)
    assert results[0] is todo


async def test_edit_todo_archive_button_returns_archive_string():
    results = []
    todo = Todo(title="Archive me", slug="archive-me", created=date.today().isoformat())
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen(todo), lambda r: results.append(r))
        await pilot.pause(0.1)
        from textual.widgets import Button
        await pilot.click("#archive-btn")
        await pilot.pause(0.1)
    assert results == ["archive"]


async def test_edit_todo_due_input_enter_opens_calendar():
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen())
        await pilot.pause(0.1)
        # Tab to priority, then tab to due-input
        await pilot.press("tab")  # title -> priority
        await pilot.press("tab")  # priority -> due-input
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.2)
        screens = [type(s).__name__ for s in pilot.app.screen_stack]
        assert "DatePickerScreen" in screens


async def test_edit_todo_calendar_sets_due_date():
    results = []
    from grunt.screens.date_picker import CalendarWidget
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditTodoScreen(), lambda r: results.append(r))
        await pilot.pause(0.1)
        # Type title first
        await pilot.press(*"Test task")
        # Tab to priority, then to due-input, open calendar
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.2)
        # Set date directly on the widget then select
        cal = pilot.app.screen.query_one(CalendarWidget)
        cal.set_reactive(CalendarWidget.year, 2026)
        cal.set_reactive(CalendarWidget.month, 6)
        cal.set_reactive(CalendarWidget.day, 15)
        await pilot.press("enter")
        await pilot.pause(0.2)
        # Save
        await pilot.press("ctrl+s")
        await pilot.pause(0.1)
    assert len(results) == 1
    assert results[0].due == "2026-06-15"


async def test_edit_todo_is_new_flag():
    async with _app().run_test(headless=True) as pilot:
        screen = EditTodoScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(0.1)
        assert screen._is_new is True


async def test_edit_todo_not_new_for_existing():
    todo = Todo(title="Existing", slug="existing", created=date.today().isoformat())
    async with _app().run_test(headless=True) as pilot:
        screen = EditTodoScreen(todo)
        await pilot.app.push_screen(screen)
        await pilot.pause(0.1)
        assert screen._is_new is False


# --- EditMemoScreen ---

async def test_edit_memo_new_focuses_title():
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditMemoScreen())
        await pilot.pause(0.1)
        focused = pilot.app.focused
        assert getattr(focused, "id", None) == "title-input"


async def test_edit_memo_cancel_returns_none():
    results = []
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditMemoScreen(), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.press("escape")
        await pilot.pause(0.1)
    assert results == [None]


async def test_edit_memo_save_empty_title_does_nothing():
    results = []
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditMemoScreen(), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.press("ctrl+s")
        await pilot.pause(0.1)
        assert any(type(s).__name__ == "EditMemoScreen" for s in pilot.app.screen_stack)
    assert results == []


async def test_edit_memo_save_new_returns_memo():
    results = []
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditMemoScreen(), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.press(*"My Note")
        await pilot.press("ctrl+s")
        await pilot.pause(0.1)
    assert len(results) == 1
    assert isinstance(results[0], Memo)
    assert results[0].title == "My Note"


async def test_edit_memo_save_existing_returns_same_object():
    results = []
    memo = Memo(title="Old title", slug="old-title", created=date.today().isoformat())
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditMemoScreen(memo), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.press("ctrl+s")
        await pilot.pause(0.1)
    assert results[0] is memo


async def test_edit_memo_archive_button_returns_archive_string():
    results = []
    memo = Memo(title="Archive memo", slug="archive-memo", created=date.today().isoformat())
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditMemoScreen(memo), lambda r: results.append(r))
        await pilot.pause(0.1)
        await pilot.click("#archive-btn")
        await pilot.pause(0.1)
    assert results == ["archive"]


async def test_edit_memo_no_archive_button_for_new():
    async with _app().run_test(headless=True) as pilot:
        await pilot.app.push_screen(EditMemoScreen())
        await pilot.pause(0.1)
        from textual.widgets import Button
        archive_btns = pilot.app.screen.query("#archive-btn")
        assert len(archive_btns) == 0
