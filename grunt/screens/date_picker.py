"""A simple calendar date-picker modal screen."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Key
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Static
from textual.containers import Horizontal, Vertical


class CalendarWidget(Static, can_focus=True):
    """An interactive calendar grid that can be navigated with the keyboard."""

    year: reactive[int] = reactive(date.today().year)
    month: reactive[int] = reactive(date.today().month)
    day: reactive[int] = reactive(date.today().day)

    def render(self) -> str:
        """Render the calendar grid for the current month with the selected day highlighted."""
        today = date.today()
        month_name = calendar.month_name[self.month]
        header = f"  {month_name} {self.year}  "
        lines = [header, "Mo Tu We Th Fr Sa Su"]
        for week in calendar.monthcalendar(self.year, self.month):
            parts = []
            for d in week:
                if d == 0:
                    parts.append("  ")
                elif d == self.day:
                    parts.append(f"[reverse]{d:2}[/reverse]")
                elif (
                    d == today.day
                    and self.month == today.month
                    and self.year == today.year
                ):
                    parts.append(f"[bold]{d:2}[/bold]")
                else:
                    parts.append(f"{d:2}")
            lines.append(" ".join(parts))
        lines.append("")
        lines.append("  ←→ day   [ ] month   ↑↓ week")
        return "\n".join(lines)

    def on_key(self, event: Key) -> None:
        """Handle keyboard navigation of the calendar."""
        event.stop()
        if event.key == "left":
            self._shift_day(-1)
        elif event.key == "right":
            self._shift_day(1)
        elif event.key == "up":
            self._shift_day(-7)
        elif event.key == "down":
            self._shift_day(7)
        elif event.key == "[":
            self._shift_month(-1)
        elif event.key == "]":
            self._shift_month(1)

    def _shift_day(self, delta: int) -> None:
        """Move the selected day by delta days, updating month/year as needed."""
        d = date(self.year, self.month, self.day) + timedelta(days=delta)
        self.year = d.year
        self.month = d.month
        self.day = d.day

    def _shift_month(self, delta: int) -> None:
        """Move forward or backward by one month, clamping the day if needed."""
        month = self.month + delta
        year = self.year
        if month > 12:
            month, year = 1, year + 1
        elif month < 1:
            month, year = 12, year - 1
        max_day = calendar.monthrange(year, month)[1]
        self.year = year
        self.month = month
        self.day = min(self.day, max_day)

    @property
    def selected_date(self) -> date:
        """Return the currently selected date."""
        return date(self.year, self.month, self.day)


class DatePickerScreen(ModalScreen[str | None]):
    """Modal calendar picker; dismisses with a YYYY-MM-DD string or None."""

    CSS = """
    DatePickerScreen {
        align: center middle;
    }
    #picker-box {
        width: 26;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    CalendarWidget {
        height: auto;
        width: 100%;
    }
    #picker-hint {
        height: 1;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("enter", "select", "Select", priority=True),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, initial: str | None = None) -> None:
        """Prepare the picker, optionally pre-selecting an existing ISO date string."""
        super().__init__()
        if initial:
            try:
                d = date.fromisoformat(initial)
                self._init_year, self._init_month, self._init_day = d.year, d.month, d.day
            except ValueError:
                t = date.today()
                self._init_year, self._init_month, self._init_day = t.year, t.month, t.day
        else:
            t = date.today()
            self._init_year, self._init_month, self._init_day = t.year, t.month, t.day

    def compose(self) -> ComposeResult:
        """Build the calendar modal with navigation hint and action buttons."""
        with Vertical(id="picker-box"):
            cal = CalendarWidget()
            cal.year = self._init_year
            cal.month = self._init_month
            cal.day = self._init_day
            yield cal
            with Horizontal(id="picker-hint"):
                yield Label("enter: select   esc: cancel")

    def on_mount(self) -> None:
        """Focus the calendar widget so keyboard navigation works immediately."""
        self.set_focus(self.query_one(CalendarWidget))

    def action_select(self) -> None:
        """Dismiss with the selected date as an ISO string."""
        self.dismiss(self.query_one(CalendarWidget).selected_date.isoformat())

    def action_cancel(self) -> None:
        """Dismiss without selecting a date."""
        self.dismiss(None)
