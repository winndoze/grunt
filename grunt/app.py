from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Label, ListView, TabbedContent, TabPane
from textual.screen import ModalScreen
from textual.containers import Horizontal

from .config import get_data_dir, save_config
from .git_ops import git_add_commit, git_init, git_mv_commit
from .models import Item, Memo, Todo
from .screens.edit_memo import EditMemoScreen
from .screens.edit_todo import EditTodoScreen
from .screens.setup import SetupScreen
from .storage import delete_item, list_items, move_item, write_item
from .widgets.item_list import ItemList


class ConfirmScreen(ModalScreen[bool]):
    """Simple confirmation dialog."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #confirm-box {
        width: 50;
        height: auto;
        border: solid $error;
        padding: 2 4;
        background: $surface;
    }
    #confirm-box Label {
        margin-bottom: 1;
    }
    #btn-row {
        height: auto;
    }
    #btn-row Button {
        margin-right: 1;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        from textual.widgets import Button
        from textual.containers import Vertical
        with Vertical(id="confirm-box"):
            yield Label(self._message)
            with Horizontal(id="btn-row"):
                yield Button("Yes", variant="error", id="yes-btn")
                yield Button("No", id="no-btn")

    def on_button_pressed(self, event) -> None:
        self.dismiss(event.button.id == "yes-btn")


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
    #archive-indicator {
        color: $warning;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("n", "new_item", "New", priority=True),
        Binding("enter", "edit_item", "Edit", show=False),
        Binding("a", "archive_item", "Archive", priority=True),
        Binding("A", "toggle_archive", "Toggle archive", priority=True),
        Binding("d", "delete_item", "Delete"),
        Binding("tab", "next_tab", "Next tab", show=False),
        Binding("shift+tab", "prev_tab", "Prev tab", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, data_dir: Path, config: dict) -> None:
        super().__init__()
        self.data_dir = data_dir
        self.config = config
        self._show_archive = False

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("TODOs", id="tab-todos"):
                yield ItemList(id="todo-list")
            with TabPane("Memos", id="tab-memos"):
                yield ItemList(id="memo-list")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_lists()
        self.set_focus(self.query_one("#todo-list", ItemList))

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self.set_focus(self._active_list())

    def _refresh_lists(self) -> None:
        todos = list_items(self.data_dir, "todo", self._show_archive)
        memos = list_items(self.data_dir, "memo", self._show_archive)
        self.query_one("#todo-list", ItemList).load_items(todos)
        self.query_one("#memo-list", ItemList).load_items(memos)
        status = " [showing archive]" if self._show_archive else ""
        self.title = f"grunt{status}"

    def _active_list(self) -> ItemList:
        tabs = self.query_one("#tabs", TabbedContent)
        active = tabs.active
        if active == "tab-todos":
            return self.query_one("#todo-list", ItemList)
        return self.query_one("#memo-list", ItemList)

    def _is_todo_tab(self) -> bool:
        tabs = self.query_one("#tabs", TabbedContent)
        return tabs.active == "tab-todos"

    def action_new_item(self) -> None:
        if self._is_todo_tab():
            self.push_screen(EditTodoScreen(), self._on_todo_saved)
        else:
            self.push_screen(EditMemoScreen(), self._on_memo_saved)

    def on_list_view_selected(self, event: ItemList.Selected) -> None:
        self.action_edit_item()

    def action_edit_item(self) -> None:
        item = self._active_list().selected_item
        if item is None:
            return
        if isinstance(item, Todo):
            self.push_screen(EditTodoScreen(item), self._on_todo_saved)
        else:
            self.push_screen(EditMemoScreen(item), self._on_memo_saved)

    def action_archive_item(self) -> None:
        item = self._active_list().selected_item
        if item is None:
            return
        self._do_archive(item)

    def action_toggle_archive(self) -> None:
        self._show_archive = not self._show_archive
        self._refresh_lists()

    def action_delete_item(self) -> None:
        item = self._active_list().selected_item
        if item is None:
            return
        self.push_screen(
            ConfirmScreen(f"Delete '{item.title}'?"),
            lambda confirmed: self._on_delete_confirmed(confirmed, item),
        )

    def action_next_tab(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab-memos" if tabs.active == "tab-todos" else "tab-todos"

    def action_prev_tab(self) -> None:
        self.action_next_tab()

    # --- Callbacks ---

    def _on_todo_saved(self, result: Todo | str | None) -> None:
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
        self._refresh_lists()

    def _on_memo_saved(self, result: Memo | str | None) -> None:
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
        self._refresh_lists()

    def _do_archive(self, item: Item) -> None:
        # Capture verb before move_item flips item.archived
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
        self._refresh_lists()

    def _on_delete_confirmed(self, confirmed: bool, item: Item) -> None:
        if not confirmed:
            return
        delete_item(self.data_dir, item)
        self._refresh_lists()
