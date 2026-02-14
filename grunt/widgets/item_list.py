"""Custom Textual widgets for rendering and selecting grunt items in a list."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import ListItem, ListView, Label

from ..models import Item, Todo, Memo


class ItemRow(ListItem):
    def __init__(self, item: Item) -> None:
        """Store the item this row represents."""
        super().__init__()
        self.item = item

    def compose(self) -> ComposeResult:
        """Render the item's fields as a formatted Label."""
        item = self.item
        if isinstance(item, Todo):
            arc_str  = "▸arc  " if item.archived else "      "
            done_str = "✓ " if item.done else "  "
            priority_str = item.priority.upper() if item.priority == "high" else item.priority
            due_str = f"  due: {item.due}" if item.due else ""
            created_str = f"  created: {item.created}" if item.created else ""
            classes = "item-row"
            if item.archived:
                classes += " item-archived"
            elif item.done:
                classes += " todo-done"
            yield Label(
                f"{arc_str}{done_str}{item.title:<30} {priority_str:<8}{due_str}{created_str}",
                classes=classes,
            )
        else:
            arc_str = "▸arc  " if item.archived else "      "
            date_str = item.updated or item.created
            classes = "item-row item-archived" if item.archived else "item-row"
            yield Label(
                f"{arc_str}{item.title:<40} {date_str}",
                classes=classes,
            )


class ItemList(ListView):
    """A ListView subclass that holds a list of grunt Items."""

    def load_items(self, items: list[Item]) -> None:
        """Replace the current list contents with the provided items."""
        self.clear()
        for item in items:
            self.append(ItemRow(item))

    @property
    def selected_item(self) -> Item | None:
        """Return the Item associated with the currently highlighted row, or None."""
        if self.index is None:
            return None
        children = list(self.query(ItemRow))
        if 0 <= self.index < len(children):
            return children[self.index].item
        return None
