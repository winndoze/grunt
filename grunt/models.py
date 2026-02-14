"""Data models for grunt todos and memos."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional, Union


def slugify(title: str) -> str:
    """Convert a title string into a URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug or "untitled"


def unique_slug(title: str, existing: set[str]) -> str:
    """Generate a slug from title that does not collide with any existing slugs."""
    base = slugify(title)
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


@dataclass
class Todo:
    title: str
    priority: str = "medium"  # high | medium | low
    due: Optional[str] = None  # YYYY-MM-DD or None
    done: bool = False
    done_at: Optional[str] = None  # YYYY-MM-DD, set when done=True
    description: str = ""
    created: str = field(default_factory=lambda: date.today().isoformat())
    slug: str = ""
    archived: bool = False

    def __post_init__(self):
        """Auto-generate the slug from the title if one was not provided."""
        if not self.slug:
            self.slug = slugify(self.title)

    @property
    def item_type(self) -> str:
        """Return the string identifier for this item type."""
        return "todo"


@dataclass
class Memo:
    title: str
    body: str = ""
    created: str = field(default_factory=lambda: date.today().isoformat())
    updated: str = ""
    slug: str = ""
    archived: bool = False

    def __post_init__(self):
        """Auto-generate the slug from the title if one was not provided."""
        if not self.slug:
            self.slug = slugify(self.title)

    @property
    def item_type(self) -> str:
        """Return the string identifier for this item type."""
        return "memo"


Item = Union["Todo", "Memo"]
