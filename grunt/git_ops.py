"""Async helpers for managing a git repository in the grunt data directory."""

from __future__ import annotations

import asyncio
from pathlib import Path


async def _run(cmd: list[str], cwd: Path) -> None:
    """Execute a subprocess command in the given directory, discarding its output."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()


async def git_init(data_dir: Path) -> None:
    """Initialize a git repository in data_dir if one does not already exist."""
    if not (data_dir / ".git").exists():
        await _run(["git", "init"], data_dir)


async def git_add_commit(data_dir: Path, file_path: Path, message: str) -> None:
    """Stage a single file and create a commit with the given message."""
    rel = file_path.relative_to(data_dir)
    await _run(["git", "add", str(rel)], data_dir)
    await _run(["git", "commit", "-m", message], data_dir)


async def git_mv_commit(data_dir: Path, src: Path, dst: Path, message: str) -> None:
    """Stage a file rename (already moved on disk) and create a commit with the given message."""
    src_rel = src.relative_to(data_dir)
    dst_rel = dst.relative_to(data_dir)
    # File is already moved; stage the removal and addition so git tracks the rename
    await _run(["git", "rm", "--cached", str(src_rel)], data_dir)
    await _run(["git", "add", str(dst_rel)], data_dir)
    await _run(["git", "commit", "-m", message], data_dir)
