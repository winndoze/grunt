"""File-based storage layer for reading and writing grunt items as Markdown with frontmatter."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import frontmatter

from .models import Item, Memo, Todo, unique_slug


def _todo_path(data_dir: Path, slug: str, archived: bool) -> Path:
    """Return the filesystem path for a todo file given its slug and archive status."""
    if archived:
        return data_dir / "archive" / "todo" / f"{slug}.md"
    return data_dir / "todo" / f"{slug}.md"


def _memo_path(data_dir: Path, slug: str, archived: bool) -> Path:
    """Return the filesystem path for a memo file given its slug and archive status."""
    if archived:
        return data_dir / "archive" / "memo" / f"{slug}.md"
    return data_dir / "memo" / f"{slug}.md"


def item_path(data_dir: Path, item: Item) -> Path:
    """Return the filesystem path for the given item."""
    if isinstance(item, Todo):
        return _todo_path(data_dir, item.slug, item.archived)
    return _memo_path(data_dir, item.slug, item.archived)


def _ensure_dirs(data_dir: Path) -> None:
    """Create all required subdirectories under data_dir if they do not already exist."""
    for d in ["todo", "memo", "archive/todo", "archive/memo"]:
        (data_dir / d).mkdir(parents=True, exist_ok=True)


def _parse_todo(post: frontmatter.Post, slug: str, archived: bool) -> Todo:
    """Construct a Todo dataclass from a parsed frontmatter Post object."""
    return Todo(
        title=post.get("title", slug),
        priority=post.get("priority", "medium"),
        due=post.get("due", None),
        done=bool(post.get("done", False)),
        done_at=str(post["done_at"]) if post.get("done_at") else None,
        description=post.content,
        created=str(post.get("created", "")),
        slug=slug,
        archived=archived,
    )


def _parse_memo(post: frontmatter.Post, slug: str, archived: bool) -> Memo:
    """Construct a Memo dataclass from a parsed frontmatter Post object."""
    return Memo(
        title=post.get("title", slug),
        body=post.content,
        created=str(post.get("created", "")),
        updated=str(post.get("updated", "")),
        slug=slug,
        archived=archived,
    )


def _read_item(path: Path, archived: bool) -> Item | None:
    """Parse a Markdown file into an Item, returning None if the file is invalid."""
    try:
        post = frontmatter.load(str(path))
    except Exception:
        return None
    slug = path.stem
    item_type = post.get("type", "")
    if item_type == "todo":
        return _parse_todo(post, slug, archived)
    if item_type == "memo":
        return _parse_memo(post, slug, archived)
    return None


def list_items(data_dir: Path, item_type: str, include_archived: bool = False) -> list[Item]:
    """Return all items of the given type, optionally including archived ones."""
    _ensure_dirs(data_dir)
    items: list[Item] = []
    active_dir = data_dir / item_type
    for path in sorted(active_dir.glob("*.md")):
        item = _read_item(path, archived=False)
        if item:
            items.append(item)
    if include_archived:
        archive_dir = data_dir / "archive" / item_type
        for path in sorted(archive_dir.glob("*.md")):
            item = _read_item(path, archived=True)
            if item:
                items.append(item)
    return items


def _existing_slugs(data_dir: Path, item_type: str) -> set[str]:
    """Collect all existing slugs for a given item type across active and archive directories."""
    slugs: set[str] = set()
    for d in [data_dir / item_type, data_dir / "archive" / item_type]:
        for p in d.glob("*.md"):
            slugs.add(p.stem)
    return slugs


def write_item(data_dir: Path, item: Item, is_new: bool = False) -> Path:
    """Serialize an item to its Markdown file, assigning a unique slug if it is new."""
    _ensure_dirs(data_dir)
    if is_new:
        existing = _existing_slugs(data_dir, item.item_type)
        item.slug = unique_slug(item.title, existing)

    path = item_path(data_dir, item)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(item, Todo):
        metadata = {
            "type": "todo",
            "title": item.title,
            "priority": item.priority,
            "done": item.done,
            "created": item.created,
        }
        if item.due:
            metadata["due"] = item.due
        if item.done and item.done_at:
            metadata["done_at"] = item.done_at
        post = frontmatter.Post(item.description, **metadata)
    else:
        updated = date.today().isoformat()
        item.updated = updated
        metadata = {
            "type": "memo",
            "title": item.title,
            "created": item.created,
            "updated": updated,
        }
        post = frontmatter.Post(item.body, **metadata)

    path.write_text(frontmatter.dumps(post))
    return path


def move_item(data_dir: Path, item: Item) -> tuple[Path, Path]:
    """Move item between active and archive, physically moving the file.
    Returns (src, dst) paths."""
    src = item_path(data_dir, item)
    item.archived = not item.archived
    dst = item_path(data_dir, item)
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return src, dst


def delete_item(data_dir: Path, item: Item) -> Path:
    """Delete the file associated with the given item and return its path."""
    path = item_path(data_dir, item)
    path.unlink(missing_ok=True)
    return path
