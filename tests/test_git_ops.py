"""Tests for async git subprocess helpers."""

import subprocess
from pathlib import Path
from unittest.mock import call, patch

import pytest

from grunt.git_ops import git_add_commit, git_init, git_mv_commit, git_push


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repository with user identity configured."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@grunt.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Grunt Test"], cwd=tmp_path, check=True)
    return tmp_path


def _log(repo: Path) -> str:
    """Return the one-line git log for a repo."""
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=repo, capture_output=True, text=True,
    )
    return result.stdout


# --- git_init ---

async def test_git_init_creates_dot_git(tmp_path):
    await git_init(tmp_path)
    assert (tmp_path / ".git").is_dir()


async def test_git_init_idempotent(tmp_path):
    await git_init(tmp_path)
    await git_init(tmp_path)
    assert (tmp_path / ".git").is_dir()


async def test_git_init_skips_if_already_repo(git_repo):
    """git_init should not reinitialise an existing repo."""
    mtime_before = (git_repo / ".git" / "HEAD").stat().st_mtime
    await git_init(git_repo)
    mtime_after = (git_repo / ".git" / "HEAD").stat().st_mtime
    assert mtime_before == mtime_after


# --- git_add_commit ---

async def test_git_add_commit_creates_commit(git_repo):
    f = git_repo / "note.md"
    f.write_text("hello")
    await git_add_commit(git_repo, f, "Add note")
    assert "Add note" in _log(git_repo)


async def test_git_add_commit_records_correct_message(git_repo):
    f = git_repo / "task.md"
    f.write_text("body")
    await git_add_commit(git_repo, f, "Add todo: My task")
    assert "Add todo: My task" in _log(git_repo)


async def test_git_add_commit_second_edit_produces_second_commit(git_repo):
    f = git_repo / "note.md"
    f.write_text("v1")
    await git_add_commit(git_repo, f, "Add note")
    f.write_text("v2")
    await git_add_commit(git_repo, f, "Update note")
    log = _log(git_repo)
    assert "Add note" in log
    assert "Update note" in log


# --- git_mv_commit ---

async def test_git_mv_commit_records_rename(git_repo):
    f = git_repo / "old.md"
    f.write_text("content")
    subprocess.run(["git", "add", "old.md"], cwd=git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial"],
        cwd=git_repo, check=True, capture_output=True,
    )
    new_f = git_repo / "new.md"
    f.rename(new_f)
    await git_mv_commit(git_repo, f, new_f, "Archive todo: Old")
    assert "Archive todo: Old" in _log(git_repo)


async def test_git_mv_commit_destination_tracked(git_repo):
    f = git_repo / "task.md"
    f.write_text("body")
    subprocess.run(["git", "add", "task.md"], cwd=git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial"],
        cwd=git_repo, check=True, capture_output=True,
    )
    dst = git_repo / "archive" / "task.md"
    dst.parent.mkdir(parents=True)
    f.rename(dst)
    await git_mv_commit(git_repo, f, dst, "Archive task")
    result = subprocess.run(
        ["git", "show", "--name-only", "HEAD"],
        cwd=git_repo, capture_output=True, text=True,
    )
    assert "archive/task.md" in result.stdout


# --- git_push ---

def test_git_push_calls_popen_with_correct_args(tmp_path):
    with patch("grunt.git_ops.subprocess.Popen") as mock_popen:
        git_push(tmp_path)
        mock_popen.assert_called_once_with(
            ["git", "push"],
            cwd=str(tmp_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


def test_git_push_uses_start_new_session(tmp_path):
    with patch("grunt.git_ops.subprocess.Popen") as mock_popen:
        git_push(tmp_path)
        _, kwargs = mock_popen.call_args
        assert kwargs["start_new_session"] is True
