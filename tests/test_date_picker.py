"""Tests for CalendarWidget and DatePickerScreen."""

import pytest
from datetime import date

from grunt.screens.date_picker import CalendarWidget, DatePickerScreen


# --- CalendarWidget unit tests (no app required) ---

def test_shift_day_forward():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2026)
    cal.set_reactive(CalendarWidget.month, 2)
    cal.set_reactive(CalendarWidget.day, 14)
    cal._shift_day(1)
    assert cal.day == 15


def test_shift_day_backward():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2026)
    cal.set_reactive(CalendarWidget.month, 2)
    cal.set_reactive(CalendarWidget.day, 14)
    cal._shift_day(-1)
    assert cal.day == 13


def test_shift_day_crosses_month_boundary():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2026)
    cal.set_reactive(CalendarWidget.month, 1)
    cal.set_reactive(CalendarWidget.day, 31)
    cal._shift_day(1)
    assert cal.month == 2
    assert cal.day == 1


def test_shift_day_crosses_year_boundary():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2025)
    cal.set_reactive(CalendarWidget.month, 12)
    cal.set_reactive(CalendarWidget.day, 31)
    cal._shift_day(1)
    assert cal.year == 2026
    assert cal.month == 1
    assert cal.day == 1


def test_shift_day_week_forward():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2026)
    cal.set_reactive(CalendarWidget.month, 2)
    cal.set_reactive(CalendarWidget.day, 14)
    cal._shift_day(7)
    assert cal.day == 21


def test_shift_month_forward():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2026)
    cal.set_reactive(CalendarWidget.month, 2)
    cal.set_reactive(CalendarWidget.day, 14)
    cal._shift_month(1)
    assert cal.month == 3
    assert cal.year == 2026


def test_shift_month_backward():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2026)
    cal.set_reactive(CalendarWidget.month, 2)
    cal.set_reactive(CalendarWidget.day, 14)
    cal._shift_month(-1)
    assert cal.month == 1


def test_shift_month_forward_wraps_year():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2025)
    cal.set_reactive(CalendarWidget.month, 12)
    cal.set_reactive(CalendarWidget.day, 1)
    cal._shift_month(1)
    assert cal.month == 1
    assert cal.year == 2026


def test_shift_month_backward_wraps_year():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2026)
    cal.set_reactive(CalendarWidget.month, 1)
    cal.set_reactive(CalendarWidget.day, 1)
    cal._shift_month(-1)
    assert cal.month == 12
    assert cal.year == 2025


def test_shift_month_clamps_day():
    """Day 31 in January should become day 28 when shifting to February 2025."""
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2025)
    cal.set_reactive(CalendarWidget.month, 1)
    cal.set_reactive(CalendarWidget.day, 31)
    cal._shift_month(1)
    assert cal.month == 2
    assert cal.day == 28


def test_selected_date():
    cal = CalendarWidget()
    cal.set_reactive(CalendarWidget.year, 2026)
    cal.set_reactive(CalendarWidget.month, 3)
    cal.set_reactive(CalendarWidget.day, 15)
    assert cal.selected_date == date(2026, 3, 15)


# --- DatePickerScreen integration tests ---

@pytest.fixture
def _app_factory():
    """Return a factory that creates a minimal App wrapping DatePickerScreen."""
    from textual.app import App, ComposeResult
    class PickerApp(App):
        def compose(self) -> ComposeResult:
            return []
    return PickerApp


async def test_date_picker_opens_with_today(_app_factory):
    async with _app_factory().run_test(headless=True) as pilot:
        await pilot.app.push_screen(DatePickerScreen())
        await pilot.pause(0.1)
        cal = pilot.app.screen.query_one(CalendarWidget)
        today = date.today()
        assert cal.year == today.year
        assert cal.month == today.month
        assert cal.day == today.day


async def test_date_picker_opens_with_initial_date(_app_factory):
    async with _app_factory().run_test(headless=True) as pilot:
        await pilot.app.push_screen(DatePickerScreen("2025-06-15"))
        await pilot.pause(0.1)
        cal = pilot.app.screen.query_one(CalendarWidget)
        assert cal.year == 2025
        assert cal.month == 6
        assert cal.day == 15


async def test_date_picker_invalid_initial_falls_back_to_today(_app_factory):
    async with _app_factory().run_test(headless=True) as pilot:
        await pilot.app.push_screen(DatePickerScreen("not-a-date"))
        await pilot.pause(0.1)
        cal = pilot.app.screen.query_one(CalendarWidget)
        assert cal.year == date.today().year


async def test_date_picker_enter_selects_date(_app_factory):
    results = []
    async with _app_factory().run_test(headless=True) as pilot:
        await pilot.app.push_screen(
            DatePickerScreen("2026-03-10"),
            lambda r: results.append(r),
        )
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.1)
    assert results == ["2026-03-10"]


async def test_date_picker_escape_cancels(_app_factory):
    results = []
    async with _app_factory().run_test(headless=True) as pilot:
        await pilot.app.push_screen(
            DatePickerScreen("2026-03-10"),
            lambda r: results.append(r),
        )
        await pilot.pause(0.1)
        await pilot.press("escape")
        await pilot.pause(0.1)
    assert results == [None]


async def test_date_picker_arrow_keys_move_day(_app_factory):
    async with _app_factory().run_test(headless=True) as pilot:
        await pilot.app.push_screen(DatePickerScreen("2026-02-14"))
        await pilot.pause(0.1)
        await pilot.press("right")
        await pilot.pause(0.05)
        cal = pilot.app.screen.query_one(CalendarWidget)
        assert cal.day == 15


async def test_date_picker_comma_dot_change_month(_app_factory):
    async with _app_factory().run_test(headless=True) as pilot:
        await pilot.app.push_screen(DatePickerScreen("2026-02-14"))
        await pilot.pause(0.1)
        await pilot.press("comma")
        await pilot.pause(0.05)
        cal = pilot.app.screen.query_one(CalendarWidget)
        assert cal.month == 1
        await pilot.press("full_stop")
        await pilot.pause(0.05)
        cal = pilot.app.screen.query_one(CalendarWidget)
        assert cal.month == 2
