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
            due_str = item.due or ""
            created_str = item.created or ""
            classes = "item-row"
            if item.archived:
                classes += " item-archived"
            elif item.done:
                classes += " todo-done"
            title = item.title if len(item.title) <= 35 else item.title[:34] + "…"
            yield Label(
                f"{arc_str}{done_str}{title:<35} {priority_str:<8} {due_str:<16} {created_str:<16}",
                classes=classes,
            )
        else:
            arc_str = "▸arc  " if item.archived else "      "
            date_str = item.updated or item.created
            classes = "item-row item-archived" if item.archived else "item-row"
            title = item.title if len(item.title) <= 40 else item.title[:39] + "…"
            yield Label(
                f"{arc_str}{title:<40} {date_str}",
                classes=classes,
            )


class ItemList(ListView):
    """A ListView subclass that holds a list of grunt Items."""

    def load_items(self, items: list[Item], preserve_slug: str | None = None) -> None:
        """Replace the current list contents with the provided items, restoring cursor by slug."""
        old_index = self.index
        self.clear()
        for item in items:
            self.append(ItemRow(item))
        if not items:
            return

        target = None
        if preserve_slug is not None:
            for i, item in enumerate(items):
                if item.slug == preserve_slug:
                    target = i
                    break
        if target is None and old_index is not None:
            target = min(old_index, len(items) - 1)

        if target is not None:
            self.call_after_refresh(lambda: setattr(self, "index", target))

    @property
    def selected_item(self) -> Item | None:
        """Return the Item associated with the currently highlighted row, or None."""
        if self.index is None:
            return None
        children = list(self.query(ItemRow))
        if 0 <= self.index < len(children):
            return children[self.index].item
        return None
