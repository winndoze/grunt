from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Label, ListView, TabbedContent, TabPane
from textual.containers import Horizontal

from .config import get_data_dir, save_config
from .git_ops import git_add_commit, git_init, git_mv_commit
from .models import Item, Memo, Todo
from .screens.edit_memo import EditMemoScreen
from .screens.edit_todo import EditTodoScreen
from .screens.setup import SetupScreen
from .storage import list_items, move_item, write_item
from .widgets.item_list import ItemList


TODO_SORTS = ["priority", "due date", "created"]
MEMO_SORTS = ["created", "updated"]
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _sort_todos(todos: list[Todo], sort_by: str) -> list[Todo]:
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
    """

    BINDINGS = [
        Binding("n", "new_item", "New", priority=True),
        Binding("enter", "edit_item", "Edit", show=False),
        Binding("a", "archive_item", "Archive", priority=True),
        Binding("A", "toggle_archive", "Toggle archive", priority=True),
        Binding("s", "cycle_sort", "Sort", priority=True),
        Binding("tab", "next_tab", "Next tab", show=False),
        Binding("shift+tab", "prev_tab", "Prev tab", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, data_dir: Path, config: dict) -> None:
        super().__init__()
        self.data_dir = data_dir
        self.config = config
        self._show_archive = False
        self._todo_sort = "priority"
        self._memo_sort = "created"

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("TODOs", id="tab-todos"):
                yield Label("", id="todo-sort-label", classes="sort-label")
                yield ItemList(id="todo-list")
            with TabPane("Memos", id="tab-memos"):
                yield Label("", id="memo-sort-label", classes="sort-label")
                yield ItemList(id="memo-list")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_lists()
        self.set_focus(self.query_one("#todo-list", ItemList))

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self.set_focus(self._active_list())

    def _refresh_lists(self) -> None:
        todos = _sort_todos(
            list_items(self.data_dir, "todo", self._show_archive),
            self._todo_sort,
        )
        memos = _sort_memos(
            list_items(self.data_dir, "memo", self._show_archive),
            self._memo_sort,
        )
        self.query_one("#todo-list", ItemList).load_items(todos)
        self.query_one("#memo-list", ItemList).load_items(memos)

        archive_hint = "  [A: hide archive]" if self._show_archive else "  [A: show archive]"
        self.query_one("#todo-sort-label", Label).update(
            f"sort: {self._todo_sort}{archive_hint}  [s: cycle]"
        )
        self.query_one("#memo-sort-label", Label).update(
            f"sort: {self._memo_sort}{archive_hint}  [s: cycle]"
        )

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

    def action_cycle_sort(self) -> None:
        if self._is_todo_tab():
            idx = TODO_SORTS.index(self._todo_sort)
            self._todo_sort = TODO_SORTS[(idx + 1) % len(TODO_SORTS)]
        else:
            idx = MEMO_SORTS.index(self._memo_sort)
            self._memo_sort = MEMO_SORTS[(idx + 1) % len(MEMO_SORTS)]
        self._refresh_lists()


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

