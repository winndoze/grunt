"""Screen for creating and editing grunt memo items."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, TextArea
from textual.containers import Horizontal, VerticalScroll

from ..models import Memo


class EditMemoScreen(Screen[Memo | None]):
    """Full-screen view for creating or editing a Memo."""

    CSS = """
    EditMemoScreen {
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
    #body-area {
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

    def __init__(self, memo: Memo | None = None) -> None:
        """Prepare the screen for creating a new memo or editing an existing one."""
        super().__init__()
        self._memo = memo
        self._is_new = memo is None

    def on_mount(self) -> None:
        """Focus the title input field when the screen is first displayed."""
        self.set_focus(self.query_one("#title-input", Input))

    def compose(self) -> ComposeResult:
        """Build the edit form with fields for title and body."""
        memo = self._memo
        with VerticalScroll(id="edit-box"):
            yield Label("New Memo" if self._is_new else f"Edit: {memo.title}")
            yield Label("Title")
            yield Input(
                value=memo.title if memo else "",
                placeholder="Title",
                id="title-input",
            )
            yield Label("Body")
            yield TextArea(
                text=memo.body if memo else "",
                id="body-area",
            )
            with Horizontal(id="btn-row"):
                yield Button("Save  [ctrl+s]", variant="primary", id="save-btn")
                yield Button("Cancel  [esc]", id="cancel-btn")
                if not self._is_new:
                    label = "Unarchive" if memo.archived else "Archive"
                    yield Button(label, variant="warning", id="archive-btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dispatch button presses to the appropriate save, cancel, or archive action."""
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "archive-btn":
            self.dismiss("archive")

    def action_save(self) -> None:
        """Validate form fields and dismiss the screen with the updated or new Memo."""
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return
        body = self.query_one("#body-area", TextArea).text

        if self._memo:
            self._memo.title = title
            self._memo.body = body
            self.dismiss(self._memo)
        else:
            from datetime import date
            self.dismiss(Memo(
                title=title,
                body=body,
                created=date.today().isoformat(),
            ))

    def action_cancel(self) -> None:
        """Dismiss the screen without saving any changes."""
        self.dismiss(None)
