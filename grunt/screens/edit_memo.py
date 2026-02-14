from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea
from textual.containers import Horizontal, Vertical

from ..models import Memo


class EditMemoScreen(ModalScreen[Memo | None]):
    """Modal screen for creating or editing a Memo."""

    CSS = """
    EditMemoScreen {
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
    #edit-box TextArea {
        height: 12;
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

    def __init__(self, memo: Memo | None = None) -> None:
        super().__init__()
        self._memo = memo
        self._is_new = memo is None

    def compose(self) -> ComposeResult:
        memo = self._memo
        with Vertical(id="edit-box"):
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
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")
                if not self._is_new:
                    label = "Unarchive" if memo.archived else "Archive"
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
        body = self.query_one("#body-area", TextArea).text

        if self._memo:
            self._memo.title = title
            self._memo.body = body
            self.dismiss(self._memo)
        else:
            from datetime import date
            memo = Memo(
                title=title,
                body=body,
                created=date.today().isoformat(),
            )
            self.dismiss(memo)
