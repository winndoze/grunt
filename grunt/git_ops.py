from __future__ import annotations

import asyncio
from pathlib import Path


async def _run(cmd: list[str], cwd: Path) -> None:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()


async def git_init(data_dir: Path) -> None:
    if not (data_dir / ".git").exists():
        await _run(["git", "init"], data_dir)


async def git_add_commit(data_dir: Path, file_path: Path, message: str) -> None:
    rel = file_path.relative_to(data_dir)
    await _run(["git", "add", str(rel)], data_dir)
    await _run(["git", "commit", "-m", message], data_dir)


async def git_mv_commit(data_dir: Path, src: Path, dst: Path, message: str) -> None:
    src_rel = src.relative_to(data_dir)
    dst_rel = dst.relative_to(data_dir)
    await _run(["git", "mv", str(src_rel), str(dst_rel)], data_dir)
    await _run(["git", "commit", "-m", message], data_dir)
