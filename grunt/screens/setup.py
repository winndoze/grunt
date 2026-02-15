"""First-run setup screen that prompts the user to choose a data directory."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static


class SetupScreen(Screen):
    """First-run setup screen to configure data_dir."""

    CSS = """
    SetupScreen {
        align: center middle;
    }
    #setup-box {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 2 4;
    }
    #setup-box Label {
        margin-bottom: 1;
    }
    #setup-box Input {
        margin-bottom: 1;
    }
    #setup-box Button {
        margin-top: 1;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, current: str | None = None) -> None:
        super().__init__()
        self._current = current

    def compose(self) -> ComposeResult:
        """Build the setup form with a directory input field and submit button."""
        is_change = self._current is not None
        heading = "Change data directory" if is_change else "Welcome to grunt!"
        hint = (
            f"Current: {self._current}\nEnter a new path to switch directories:"
            if is_change
            else "Where should grunt store your notes?"
        )
        with Static(id="setup-box"):
            yield Label(heading, id="welcome")
            yield Label(hint)
            yield Input(
                value=self._current or "",
                placeholder="e.g. /home/user/notes",
                id="data-dir-input",
            )
            btn_label = "Change directory" if is_change else "Set up"
            yield Button(btn_label, variant="primary", id="setup-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Trigger form submission when the setup button is pressed."""
        if event.button.id == "setup-btn":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Trigger form submission when the user presses Enter in the input field."""
        self._submit()

    def action_cancel(self) -> None:
        """Dismiss without making any change (only applicable in change-dir mode)."""
        if self._current is not None:
            self.dismiss(None)

    def _submit(self) -> None:
        """Validate and dismiss the screen with the entered directory path."""
        input_widget = self.query_one("#data-dir-input", Input)
        value = input_widget.value.strip()
        if value:
            self.dismiss(value)
