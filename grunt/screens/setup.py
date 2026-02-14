"""First-run setup screen that prompts the user to choose a data directory."""

from __future__ import annotations

from textual.app import ComposeResult
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

    def compose(self) -> ComposeResult:
        """Build the setup form with a directory input field and submit button."""
        with Static(id="setup-box"):
            yield Label("Welcome to grunt!", id="welcome")
            yield Label("Where should grunt store your notes?")
            yield Input(
                placeholder="e.g. /home/user/notes",
                id="data-dir-input",
            )
            yield Button("Set up", variant="primary", id="setup-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Trigger form submission when the setup button is pressed."""
        if event.button.id == "setup-btn":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Trigger form submission when the user presses Enter in the input field."""
        self._submit()

    def _submit(self) -> None:
        """Validate and dismiss the screen with the entered directory path."""
        input_widget = self.query_one("#data-dir-input", Input)
        value = input_widget.value.strip()
        if value:
            self.dismiss(value)
