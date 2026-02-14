"""Screen for creating and editing grunt todo items."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Input, Label, Select, TextArea
from textual.containers import Horizontal, VerticalScroll

from ..models import Todo
from .date_picker import DatePickerScreen


class EditTodoScreen(Screen[Todo | None]):
    """Full-screen view for creating or editing a TODO."""

    CSS = """
    EditTodoScreen {
        padding: 0 2;
    }
    #edit-box {
        height: 1fr;
    }
    #edit-box Label {
        height: 1;
        margin: 0;
        padding: 0;
    }
    #edit-box Input {
        height: 1;
        border: none;
        padding: 0 1;
        margin: 0 0 1 0;
    }
    #edit-box Select {
        margin: 0 0 1 0;
    }
    #description-area {
        height: 1fr;
        margin: 0 0 1 0;
    }
    #due-row {
        height: 1;
        margin: 0 0 1 0;
    }
    #due-row Input {
        width: 1fr;
        height: 1;
        border: none;
        padding: 0 1;
        margin: 0;
    }
    #btn-row {
        height: 1;
        margin: 0;
        padding: 0;
    }
    #btn-row Button {
        height: 1;
        border: none;
        padding: 0 2;
        min-width: 10;
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, todo: Todo | None = None) -> None:
        """Prepare the screen for creating a new todo or editing an existing one."""
        super().__init__()
        self._todo = todo
        self._is_new = todo is None

    def on_mount(self) -> None:
        """Focus the title input field when the screen is first displayed."""
        self.set_focus(self.query_one("#title-input", Input))

    def compose(self) -> ComposeResult:
        """Build the edit form with fields for title, priority, due date, done status, and description."""
        todo = self._todo
        with VerticalScroll(id="edit-box"):
            yield Label("New TODO" if self._is_new else f"Edit: {todo.title}")
            yield Label("Title")
            yield Input(
                value=todo.title if todo else "",
                placeholder="Title",
                id="title-input",
            )
            yield Label("Priority")
            priority_options = [("High", "high"), ("Medium", "medium"), ("Low", "low")]
            current_priority = todo.priority if todo else "medium"
            yield Select(
                priority_options,
                value=current_priority,
                id="priority-select",
            )
            yield Label("Due date")
            with Horizontal(id="due-row"):
                yield Input(
                    value=todo.due or "" if todo else "",
                    placeholder="YYYY-MM-DD  (enter: calendar)",
                    id="due-input",
                )
            yield Checkbox("Done", value=todo.done if todo else False, id="done-check")
            yield Label("Description")
            yield TextArea(
                text=todo.description if todo else "",
                id="description-area",
            )
            with Horizontal(id="btn-row"):
                yield Button("Save  [ctrl+s]", variant="primary", id="save-btn")
                yield Button("Cancel  [esc]", id="cancel-btn")
                if not self._is_new:
                    label = "Unarchive" if todo.archived else "Archive"
                    yield Button(label, variant="warning", id="archive-btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dispatch button presses to save, cancel, or archive."""
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "archive-btn":
            self.dismiss("archive")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Open the calendar picker when Enter is pressed in the due date field."""
        if event.input.id == "due-input":
            event.stop()
            current = event.input.value.strip()
            self.app.push_screen(DatePickerScreen(current or None), self._on_date_picked)

    def _on_date_picked(self, result: str | None) -> None:
        """Set the due date input to the date returned from the calendar picker."""
        if result is not None:
            self.query_one("#due-input", Input).value = result

    def action_save(self) -> None:
        """Validate form fields and dismiss the screen with the updated or new Todo."""
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return
        priority_widget = self.query_one("#priority-select", Select)
        priority = str(priority_widget.value) if priority_widget.value else "medium"
        due = self.query_one("#due-input", Input).value.strip() or None
        done = self.query_one("#done-check", Checkbox).value
        description = self.query_one("#description-area", TextArea).text

        if self._todo:
            self._todo.title = title
            self._todo.priority = priority
            self._todo.due = due
            self._todo.done = done
            self._todo.description = description
            self.dismiss(self._todo)
        else:
            from datetime import date
            self.dismiss(Todo(
                title=title,
                priority=priority,
                due=due,
                done=done,
                description=description,
                created=date.today().isoformat(),
            ))

    def action_cancel(self) -> None:
        """Dismiss the screen without saving any changes."""
        self.dismiss(None)
