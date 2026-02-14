"""Entry point for grunt that handles first-run setup and launches the TUI application."""

from __future__ import annotations

import asyncio
from pathlib import Path

from .config import get_data_dir, load_config, save_config
from .git_ops import git_init


def _bootstrap_setup() -> str | None:
    """Run the setup TUI and return the chosen data_dir, or None if cancelled."""
    from .screens.setup import SetupScreen
    from textual.app import App, ComposeResult

    chosen: list[str] = []

    class BootstrapApp(App):
        def on_mount(self) -> None:
            """Push the setup screen immediately on startup."""
            self.push_screen(SetupScreen(), self._on_setup_done)

        def _on_setup_done(self, data_dir: str | None) -> None:
            """Store the chosen directory and exit the bootstrap app."""
            if data_dir:
                chosen.append(data_dir)
            self.exit()

    BootstrapApp().run()
    return chosen[0] if chosen else None


def main() -> None:
    """Load or create configuration, initialise git, and start the grunt TUI."""
    config = load_config()

    if config is None:
        data_dir_str = _bootstrap_setup()
        if not data_dir_str:
            return
        save_config(data_dir_str)
        data_dir = Path(data_dir_str).expanduser()
        data_dir.mkdir(parents=True, exist_ok=True)
        asyncio.run(git_init(data_dir))
        config = load_config()
        if config is None:
            return
    else:
        data_dir = get_data_dir(config)

    data_dir.mkdir(parents=True, exist_ok=True)
    asyncio.run(git_init(data_dir))

    from .app import GruntApp
    GruntApp(data_dir, config).run()


if __name__ == "__main__":
    main()
