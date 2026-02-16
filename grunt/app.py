"""The main Textual TUI application class and supporting sort helpers for grunt."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Label, ListView, TabbedContent, TabPane
from textual.containers import Horizontal

from .config import get_data_dir, save_config
from .git_ops import git_add_commit, git_init, git_mv_commit, git_push
from .models import Item, Memo, Todo
from .screens.edit_memo import EditMemoScreen
from .screens.edit_todo import EditTodoScreen
from .screens.setup import SetupScreen
from .storage import list_items, move_item, write_item
from .widgets.item_list import ItemList


TODO_SORTS = ["priority", "due date", "created"]
MEMO_SORTS = ["created", "updated"]
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
THEMES = ["textual-dark", "textual-light", "nord", "gruvbox", "catppuccin-mocha", "dracula", "tokyo-night", "solarized-light"]


def _sort_todos(todos: list[Todo], sort_by: str) -> list[Todo]:
    """Return todos sorted by the given field name."""
    if sort_by == "due date":
        return sorted(todos, key=lambda t: (
            t.due or "9999-99-99",
            PRIORITY_ORDER.get(t.priority, 1),
        ))
    elif sort_by == "created":
        return sorted(todos, key=lambda t: t.created, reverse=True)
    else:  # priority
        return sorted(todos, key=lambda t: (
            PRIORITY_ORDER.get(t.priority, 1),
            t.due or "9999-99-99",
        ))


def _sort_memos(memos: list[Memo], sort_by: str) -> list[Memo]:
    """Return memos sorted by the given field name."""
    if sort_by == "updated":
        return sorted(memos, key=lambda m: m.updated or m.created, reverse=True)
    else:  # created
        return sorted(memos, key=lambda m: m.created, reverse=True)



class GruntApp(App):
    """Main grunt TUI application."""

    TITLE = "grunt"

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    ItemList {
        height: 1fr;
    }
    .item-row {
        width: 100%;
    }
    .sort-label {
        height: 1;
        padding: 0 1;
        color: $text-muted;
        background: $boost;
    }
    .todo-done {
        color: $text-muted;
    }
    .item-archived {
        color: $text-muted;
        text-style: italic;
    }
    .list-header {
        height: 1;
        padding: 0 1;
        color: $text;
        text-style: bold;
        background: $boost;
    }
    """

    BINDINGS = [
        Binding("n", "new_item", "New", priority=True),
        Binding("enter", "edit_item", "Edit", show=False),
        Binding("x", "toggle_done", "Done", priority=True),
        Binding("a", "archive_item", "Archive", priority=True),
        Binding("A", "toggle_archive", "Toggle archive", priority=True),
        Binding("s", "cycle_sort", "Sort", priority=True),
        Binding("1", "show_todos", "todos", priority=True),
        Binding("2", "show_memos", "memos", priority=True),
        Binding("tab", "next_tab", "Next tab", show=False),
        Binding("shift+tab", "prev_tab", "Prev tab", show=False),
        Binding("T", "cycle_theme", "Theme", priority=True),
        Binding("C", "change_dir", "Change dir", priority=True),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, data_dir: Path, config: dict) -> None:
        """Initialise the app with the resolved data directory and loaded config."""
        super().__init__()
        self.data_dir = data_dir
        self.config = config
        self._show_archive = False
        self._todo_sort = "priority"
        self._memo_sort = "created"
        self._theme_index = 0

    def compose(self) -> ComposeResult:
        """Build the top-level widget tree with a tabbed layout for todos and memos."""
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("todos", id="tab-todos"):
                yield Label("", id="todo-sort-label", classes="sort-label")
                yield Label(
                    f"       {'Title':<35} {'Priority':<8} {'Due':<16} {'Created':<16}",
                    classes="list-header",
                )
                yield ItemList(id="todo-list")
            with TabPane("memos", id="tab-memos"):
                yield Label("", id="memo-sort-label", classes="sort-label")
                yield Label(
                    f"     {'Title':<40} {'Date':<16}",
                    classes="list-header",
                )
                yield ItemList(id="memo-list")
        yield Footer()

    def on_mount(self) -> None:
        """Populate item lists and focus the todo list on startup."""
        self.sub_title = str(self.data_dir)
        self._refresh_lists()
        self.set_focus(self.query_one("#todo-list", ItemList))

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Move focus to the item list of the newly activated tab."""
        self.set_focus(self._active_list())

    def _refresh_lists(self, preserve_slug: str | None = None) -> None:
        """Reload and re-sort both item lists from disk, then update the UI."""
        todos = _sort_todos(
            list_items(self.data_dir, "todo", self._show_archive),
            self._todo_sort,
        )
        memos = _sort_memos(
            list_items(self.data_dir, "memo", self._show_archive),
            self._memo_sort,
        )
        self.query_one("#todo-list", ItemList).load_items(todos, preserve_slug)
        self.query_one("#memo-list", ItemList).load_items(memos, preserve_slug)
        self._update_sort_label()
        status = " [showing archive]" if self._show_archive else ""
        self.title = f"grunt{status}"

    def _update_sort_label(self) -> None:
        """Refresh the sort/archive hint labels above both item lists."""
        item = self._active_list().selected_item
        archive_action = "unarchive" if (item and item.archived) else "archive"
        archive_hint = "  [A: hide archive]" if self._show_archive else "  [A: show archive]"
        self.query_one("#todo-sort-label", Label).update(
            f"sort: {self._todo_sort}{archive_hint}  [s: cycle]  [a: {archive_action}]"
        )
        self.query_one("#memo-sort-label", Label).update(
            f"sort: {self._memo_sort}{archive_hint}  [s: cycle]  [a: {archive_action}]"
        )

    def _active_list(self) -> ItemList:
        """Return the ItemList widget belonging to the currently active tab."""
        tabs = self.query_one("#tabs", TabbedContent)
        active = tabs.active
        if active == "tab-todos":
            return self.query_one("#todo-list", ItemList)
        return self.query_one("#memo-list", ItemList)

    def _is_todo_tab(self) -> bool:
        """Return True if the todos tab is currently active."""
        tabs = self.query_one("#tabs", TabbedContent)
        return tabs.active == "tab-todos"

    def action_new_item(self) -> None:
        """Open the appropriate edit screen to create a new todo or memo."""
        if self._is_todo_tab():
            self.push_screen(EditTodoScreen(), self._on_todo_saved)
        else:
            self.push_screen(EditMemoScreen(), self._on_memo_saved)

    def on_list_view_selected(self, event: ItemList.Selected) -> None:
        """Open the edit screen for the item that was activated by selection."""
        self.action_edit_item()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update the sort label whenever the highlighted item changes."""
        self._update_sort_label()

    def action_edit_item(self) -> None:
        """Open the edit screen for the currently highlighted item."""
        item = self._active_list().selected_item
        if item is None:
            return
        if isinstance(item, Todo):
            self.push_screen(EditTodoScreen(item), self._on_todo_saved)
        else:
            self.push_screen(EditMemoScreen(item), self._on_memo_saved)

    def action_toggle_done(self) -> None:
        """Toggle the done state of the highlighted todo and persist the change."""
        from datetime import datetime
        item = self._active_list().selected_item
        if not isinstance(item, Todo):
            return
        slug = item.slug
        item.done = not item.done
        item.done_at = datetime.now().isoformat(timespec="seconds") if item.done else None
        path = write_item(self.data_dir, item)
        asyncio.ensure_future(
            git_add_commit(self.data_dir, path, f"Update todo: {item.title}")
        )
        self._refresh_lists(preserve_slug=slug)

    def action_archive_item(self) -> None:
        """Archive or unarchive the currently highlighted item."""
        item = self._active_list().selected_item
        if item is None:
            return
        self._do_archive(item)

    def action_toggle_archive(self) -> None:
        """Toggle visibility of archived items in both lists."""
        self._show_archive = not self._show_archive
        self._refresh_lists()

    def action_cycle_sort(self) -> None:
        """Advance to the next sort mode for the active tab and refresh."""
        if self._is_todo_tab():
            idx = TODO_SORTS.index(self._todo_sort)
            self._todo_sort = TODO_SORTS[(idx + 1) % len(TODO_SORTS)]
        else:
            idx = MEMO_SORTS.index(self._memo_sort)
            self._memo_sort = MEMO_SORTS[(idx + 1) % len(MEMO_SORTS)]
        self._refresh_lists()


    def action_show_todos(self) -> None:
        """Switch directly to the todos tab."""
        self.query_one("#tabs", TabbedContent).active = "tab-todos"

    def action_show_memos(self) -> None:
        """Switch directly to the memos tab."""
        self.query_one("#tabs", TabbedContent).active = "tab-memos"

    def action_next_tab(self) -> None:
        """Switch to the next tab."""
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab-memos" if tabs.active == "tab-todos" else "tab-todos"

    def action_prev_tab(self) -> None:
        """Switch to the previous tab."""
        self.action_next_tab()

    def action_cycle_theme(self) -> None:
        """Cycle to the next available Textual theme."""
        self._theme_index = (self._theme_index + 1) % len(THEMES)
        self.theme = THEMES[self._theme_index]

    def action_change_dir(self) -> None:
        """Open the setup screen to switch to a different data directory."""
        self.push_screen(SetupScreen(current=str(self.data_dir)), self._on_dir_changed)

    def _on_dir_changed(self, new_dir: str | None) -> None:
        """Switch to the new data directory, saving config and re-initialising git."""
        self.set_focus(self.query_one("#todo-list", ItemList))
        if not new_dir or new_dir == str(self.data_dir):
            return
        from .config import save_config
        from .git_ops import git_init
        save_config(new_dir)
        self.data_dir = Path(new_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        for sub in ["todo", "memo", "archive/todo", "archive/memo"]:
            (self.data_dir / sub).mkdir(parents=True, exist_ok=True)
        asyncio.ensure_future(git_init(self.data_dir))
        self.sub_title = str(self.data_dir)
        self._refresh_lists()

    def action_quit(self) -> None:
        """Kick off a background git push then exit the app."""
        git_push(self.data_dir)
        self.exit()

    # --- Callbacks ---

    def _on_todo_saved(self, result: Todo | str | None) -> None:
        """Handle the result from the EditTodoScreen, persisting or archiving as needed."""
        if result is None:
            return
        if result == "archive":
            item = self._active_list().selected_item
            if item:
                self._do_archive(item)
            return
        todo: Todo = result
        is_new = not todo.slug or not (
            (self.data_dir / "todo" / f"{todo.slug}.md").exists()
            or (self.data_dir / "archive" / "todo" / f"{todo.slug}.md").exists()
        )
        path = write_item(self.data_dir, todo, is_new=is_new)
        verb = "Add" if is_new else "Update"
        asyncio.ensure_future(
            git_add_commit(self.data_dir, path, f"{verb} todo: {todo.title}")
        )
        self._refresh_lists(preserve_slug=todo.slug)

    def _on_memo_saved(self, result: Memo | str | None) -> None:
        """Handle the result from the EditMemoScreen, persisting or archiving as needed."""
        if result is None:
            return
        if result == "archive":
            item = self._active_list().selected_item
            if item:
                self._do_archive(item)
            return
        memo: Memo = result
        is_new = not memo.slug or not (
            (self.data_dir / "memo" / f"{memo.slug}.md").exists()
            or (self.data_dir / "archive" / "memo" / f"{memo.slug}.md").exists()
        )
        path = write_item(self.data_dir, memo, is_new=is_new)
        verb = "Add" if is_new else "Update"
        asyncio.ensure_future(
            git_add_commit(self.data_dir, path, f"{verb} memo: {memo.title}")
        )
        self._refresh_lists(preserve_slug=memo.slug)

    def _do_archive(self, item: Item) -> None:
        """Move the item to or from the archive directory and commit the change."""
        slug = item.slug
        action_verb = "Unarchive" if item.archived else "Archive"
        src, dst = move_item(self.data_dir, item)
        asyncio.ensure_future(
            git_mv_commit(
                self.data_dir,
                src,
                dst,
                f"{action_verb} {item.item_type}: {item.title}",
            )
        )
        self._refresh_lists(preserve_slug=slug)
