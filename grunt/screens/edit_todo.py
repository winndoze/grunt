from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, Select, TextArea
from textual.containers import Horizontal, VerticalScroll

from ..models import Todo


class EditTodoScreen(Screen[Todo | None]):
    """Full-screen view for creating or editing a TODO."""

    CSS = """
    EditTodoScreen {
        padding: 1 4;
    }
    #edit-box {
        height: 1fr;
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
    #description-area {
        height: 1fr;
        margin-bottom: 1;
    }
    #btn-row {
        height: auto;
        margin-top: 1;
        padding-bottom: 1;
    }
    #btn-row Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, todo: Todo | None = None) -> None:
        super().__init__()
        self._todo = todo
        self._is_new = todo is None

    def on_mount(self) -> None:
        self.set_focus(self.query_one("#title-input", Input))

    def compose(self) -> ComposeResult:
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
                yield Button("Save  [ctrl+s]", variant="primary", id="save-btn")
                yield Button("Cancel  [esc]", id="cancel-btn")
                if not self._is_new:
                    label = "Unarchive" if todo.archived else "Archive"
                    yield Button(label, variant="warning", id="archive-btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "archive-btn":
            self.dismiss("archive")

    def action_save(self) -> None:
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
            self.dismiss(Todo(
                title=title,
                priority=priority,
                due=due,
                description=description,
                created=date.today().isoformat(),
            ))

    def action_cancel(self) -> None:
        self.dismiss(None)
