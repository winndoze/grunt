from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, TextArea, Static
from textual.containers import Horizontal, Vertical

from ..models import Todo


class EditTodoScreen(ModalScreen[Todo | None]):
    """Modal screen for creating or editing a TODO."""

    CSS = """
    EditTodoScreen {
        align: center middle;
    }
    #edit-box {
        width: 70;
        height: auto;
        max-height: 90vh;
        border: solid $primary;
        padding: 2 4;
        background: $surface;
    }
    #edit-box Label {
        margin-top: 1;
    }
    #edit-box Input {
        margin-bottom: 1;
    }
    #edit-box Select {
        margin-bottom: 1;
    }
    #edit-box TextArea {
        height: 10;
        margin-bottom: 1;
    }
    #btn-row {
        margin-top: 1;
        height: auto;
    }
    #btn-row Button {
        margin-right: 1;
    }
    """

    def __init__(self, todo: Todo | None = None) -> None:
        super().__init__()
        self._todo = todo
        self._is_new = todo is None

    def compose(self) -> ComposeResult:
        todo = self._todo
        with Vertical(id="edit-box"):
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
            yield Label("Due date (YYYY-MM-DD, optional)")
            yield Input(
                value=todo.due or "" if todo else "",
                placeholder="YYYY-MM-DD",
                id="due-input",
            )
            yield Label("Description")
            yield TextArea(
                text=todo.description if todo else "",
                id="description-area",
            )
            with Horizontal(id="btn-row"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")
                if not self._is_new:
                    label = "Unarchive" if todo.archived else "Archive"
                    yield Button(label, variant="warning", id="archive-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._save()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "archive-btn":
            self.dismiss("archive")

    def _save(self) -> None:
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return
        priority_widget = self.query_one("#priority-select", Select)
        priority = str(priority_widget.value) if priority_widget.value else "medium"
        due = self.query_one("#due-input", Input).value.strip() or None
        description = self.query_one("#description-area", TextArea).text

        if self._todo:
            self._todo.title = title
            self._todo.priority = priority
            self._todo.due = due
            self._todo.description = description
            self.dismiss(self._todo)
        else:
            from datetime import date
            todo = Todo(
                title=title,
                priority=priority,
                due=due,
                description=description,
                created=date.today().isoformat(),
            )
            self.dismiss(todo)
