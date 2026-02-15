"""Entry point for grunt that handles first-run setup and launches the TUI application."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from .config import get_data_dir, load_config, save_config
from .git_ops import git_add_commit, git_init


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


def _resolve_data_dir() -> Path | None:
    """Load config (running setup if needed) and return the resolved data directory."""
    config = load_config()

    if config is None:
        data_dir_str = _bootstrap_setup()
        if not data_dir_str:
            return None
        save_config(data_dir_str)
        data_dir = Path(data_dir_str).expanduser()
        data_dir.mkdir(parents=True, exist_ok=True)
        asyncio.run(git_init(data_dir))
        config = load_config()
        if config is None:
            return None
    else:
        data_dir = get_data_dir(config)

    data_dir.mkdir(parents=True, exist_ok=True)
    asyncio.run(git_init(data_dir))
    return data_dir


def _quick_add(title: str, priority: str, due: str | None) -> None:
    """Create a todo from the command line without opening the TUI."""
    from datetime import date
    from .models import Todo
    from .storage import write_item

    data_dir = _resolve_data_dir()
    if data_dir is None:
        return

    todo = Todo(
        title=title,
        priority=priority,
        due=due or None,
        created=date.today().isoformat(),
    )
    path = write_item(data_dir, todo, is_new=True)
    asyncio.run(git_add_commit(data_dir, path, f"Add todo: {todo.title}"))
    due_str = f"  due: {due}" if due else ""
    print(f"Added [{priority}]{due_str}: {title}")


def _parse_args() -> tuple[str | None, str, str | None]:
    """Parse sys.argv for quick-add mode. Returns (title, priority, due)."""
    import argparse
    parser = argparse.ArgumentParser(
        prog="grunt",
        description="TUI task & memo manager. Run with no arguments to open the TUI.",
    )
    parser.add_argument(
        "title",
        nargs="?",
        default=None,
        help="Todo title for quick-add (omit to open the TUI)",
    )
    parser.add_argument(
        "-p", "--priority",
        choices=["high", "medium", "low"],
        default="medium",
        help="Priority (default: medium)",
    )
    parser.add_argument(
        "-d", "--due",
        default=None,
        metavar="YYYY-MM-DD",
        help="Due date",
    )
    args = parser.parse_args()
    return args.title, args.priority, args.due


def main() -> None:
    """Parse arguments; quick-add a todo if a title is given, otherwise launch the TUI."""
    title, priority, due = _parse_args()

    if title is not None:
        _quick_add(title, priority, due)
        return

    data_dir = _resolve_data_dir()
    if data_dir is None:
        return

    config = load_config() or {}
    from .app import GruntApp
    GruntApp(data_dir, config).run()


if __name__ == "__main__":
    main()
