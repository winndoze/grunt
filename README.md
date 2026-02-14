# grunt

A terminal-based TODO and Memo manager with git-backed storage.

## Install

```bash
pip install -e .
```

Or with `uv`:

```bash
uv pip install -e .
```

## Usage

```bash
grunt
# or
python -m grunt
```

On first run, grunt prompts you to choose a directory to store your notes. That directory is initialized as a git repository and all changes are auto-committed.

## Keybindings

| Key | Action |
|-----|--------|
| `n` | New item |
| `Enter` | Edit selected item |
| `a` | Archive selected item |
| `A` | Toggle archived items visibility |
| `d` | Delete selected item (with confirmation) |
| `Tab` / `Shift+Tab` | Switch between TODOs / Memos tabs |
| `q` | Quit |

## File format

**TODO** (`<data_dir>/todo/<slug>.md`):
```markdown
---
type: todo
title: Buy groceries
priority: high
due: 2026-02-20
created: 2026-02-14
---

Description text here...
```

**Memo** (`<data_dir>/memo/<slug>.md`):
```markdown
---
type: memo
title: Project notes
created: 2026-02-14
---

Content here...
```

Archived items are moved to `<data_dir>/archive/todo/` or `<data_dir>/archive/memo/`.

## Config

`~/.config/grunt/config.toml`:
```toml
data_dir = "/home/user/notes"
```
