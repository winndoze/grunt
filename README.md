# grunt

A terminal-based TODO and memo manager. Items are stored as plain Markdown files with YAML frontmatter in a git-tracked directory — no database, no cloud, just files you own.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

---

## Features

- Two-tab layout: **todos** and **memos**
- Todos have title, priority (high/medium/low), due date (with calendar picker), done state, and description
- Memos have title and freeform body
- Archive items out of the way without deleting them
- All changes auto-committed to git; git push on quit
- Sort todos by priority, due date, or created; memos by created or last updated
- Multiple built-in colour themes

---

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Or with `uv`:

```bash
uv pip install -e .
```

---

## Usage

```bash
grunt
# or
python -m grunt
```

On first run grunt asks you to choose a data directory. That directory is initialised as a git repository and every change is auto-committed.

### Quick-add from the command line

Add a todo without opening the TUI:

```bash
grunt "Buy oat milk"
grunt "Fix login bug" --priority high
grunt "Submit report" -p high -d 2026-03-01
```

| Flag | Short | Description |
|------|-------|-------------|
| `--priority` | `-p` | `high`, `medium` (default), or `low` |
| `--due` | `-d` | Due date in `YYYY-MM-DD` format |

---

## Keybindings

### Main list

| Key | Action |
|-----|--------|
| `n` | New item |
| `Enter` | Edit selected item |
| `x` | Toggle done (todos only) |
| `a` | Archive / unarchive selected item |
| `A` | Toggle visibility of archived items |
| `s` | Cycle sort order |
| `1` | Switch to todos tab |
| `2` | Switch to memos tab |
| `Tab` / `Shift+Tab` | Switch tabs |
| `T` | Cycle colour theme |
| `C` | Change data directory |
| `q` | Quit (triggers background git push) |

### Edit screen

| Key | Action |
|-----|--------|
| `Ctrl+S` | Save |
| `Escape` | Cancel |
| `Enter` (on due date field) | Open calendar picker |

### Calendar picker

| Key | Action |
|-----|--------|
| `←` / `→` | Previous / next day |
| `↑` / `↓` | Previous / next week |
| `,` | Previous month |
| `.` | Next month |
| `Enter` | Select date |
| `Escape` | Cancel |

---

## File format

**TODO** (`<data_dir>/todo/<slug>.md`):
```markdown
---
type: todo
title: Buy groceries
priority: high
due: 2026-02-20
done: false
created: 2026-02-14
---

Optional description here.
```

**Memo** (`<data_dir>/memo/<slug>.md`):
```markdown
---
type: memo
title: Project notes
created: 2026-02-14
updated: 2026-02-15
---

Content here.
```

Archived items live under `<data_dir>/archive/todo/` and `<data_dir>/archive/memo/`.

---

## Directory layout

```
<data_dir>/
├── .git/
├── todo/
│   └── buy-groceries.md
├── memo/
│   └── project-notes.md
└── archive/
    ├── todo/
    └── memo/
```

---

## Config

`~/.config/grunt/config.toml`:
```toml
data_dir = "/home/user/notes"
```

---

## Changing the data directory

The current data directory is always shown in the app header (below the title).

To switch to a different directory while grunt is running, press **`C`**. A prompt will appear pre-filled with the current path — clear it and enter a new one, then press Enter or click "Change directory". grunt will:

1. Save the new path to `~/.config/grunt/config.toml`
2. Create the directory and required subdirectories if they don't exist
3. Initialise a git repository there if one doesn't already exist
4. Reload the item lists from the new location

To change the directory manually (without opening grunt), edit `~/.config/grunt/config.toml` directly:

```toml
data_dir = "/path/to/your/new/notes"
```

---

## Development

```bash
pip install -e ".[test]"
pytest
```

154 tests covering models, storage, git operations, config, sorting, all TUI screens, widgets, and app actions.
