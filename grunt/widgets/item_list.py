from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import ListItem, ListView, Label
from textual.reactive import reactive

from ..models import Item, Todo, Memo


class ItemRow(ListItem):
    def __init__(self, item: Item) -> None:
        super().__init__()
        self.item = item

    def compose(self) -> ComposeResult:
        item = self.item
        if isinstance(item, Todo):
            priority_str = item.priority.upper() if item.priority == "high" else item.priority
            due_str = f"  due: {item.due}" if item.due else ""
            archived_str = " [archived]" if item.archived else ""
            yield Label(
                f"{item.title:<30} {priority_str:<8}{due_str}{archived_str}",
                classes="item-row",
            )
        else:
            archived_str = " [archived]" if item.archived else ""
            yield Label(f"{item.title}{archived_str}", classes="item-row")


class ItemList(ListView):
    """A ListView subclass that holds a list of grunt Items."""

    def load_items(self, items: list[Item]) -> None:
        self.clear()
        for item in items:
            self.append(ItemRow(item))

    @property
    def selected_item(self) -> Item | None:
        if self.index is None:
            return None
        children = list(self.query(ItemRow))
        if 0 <= self.index < len(children):
            return children[self.index].item
        return None
