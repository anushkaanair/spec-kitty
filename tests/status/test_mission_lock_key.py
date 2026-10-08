"""One canonical Mission lock key (mission-writer-followups WP01, plan D1 and A1-A4).

Every per-Mission lock door resolves the same lock file for a Mission, including a
legacy bare-directory coordination Mission: a primary directory ``060-test`` whose
``meta.json`` records a coordination branch and mid8 ``01COORD0``, with its
coordination surface in ``060-test-01COORD0``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from specify_cli.coordination.legacy_resolution import _mission_specs_dir_name
from specify_cli.status.locking import feature_status_lock_path
from specify_cli.status.mission_write import capture_rollback_point, mission_write_lock

pytestmark = [pytest.mark.unit]

SLUG = "060-test"
MID8 = "01COORD0"
COORD_NAME = f"{SLUG}-{MID8}"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "kitty-specs").mkdir()
    return tmp_path


def _write_meta(directory: Path, meta: dict[str, object]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return directory


@pytest.fixture
def bare_coord_mission(repo: Path) -> tuple[Path, Path, Path]:
    """``(repo, primary_dir, coord_dir)`` for a legacy bare-directory coordination Mission."""
    primary = _write_meta(
        repo / "kitty-specs" / SLUG,
        {"mission_slug": SLUG, "mission_id": f"{MID8}XXXXXXXXXXXXXXXXXX", "mid8": MID8, "coordination_branch": f"kitty/mission-{COORD_NAME}"},
    )
    coord = repo / ".worktrees" / f"{COORD_NAME}-coord" / "kitty-specs" / COORD_NAME
    coord.mkdir(parents=True)
    return repo, primary, coord


def test_write_lock_on_a_bare_directory_coordination_mission_takes_the_transaction_lock_file(
    bare_coord_mission: tuple[Path, Path, Path],
) -> None:
    """The write door on the primary dir resolves the lock file the bookkeeping transaction takes (A1)."""
    repo, primary, _coord = bare_coord_mission
    transaction_lock = feature_status_lock_path(repo, _mission_specs_dir_name(SLUG, MID8))
    with mission_write_lock(primary, repo_root=repo) as held:
        assert held == transaction_lock


def test_write_lock_on_the_coordination_dir_takes_the_same_lock_file_as_the_primary_dir(
    bare_coord_mission: tuple[Path, Path, Path],
) -> None:
    repo, primary, coord = bare_coord_mission
    with mission_write_lock(primary, repo_root=repo) as via_primary:
        pass
    with mission_write_lock(coord, repo_root=repo) as via_coord:
        pass
    assert via_primary == via_coord


def test_capture_rollback_point_accepts_a_hold_taken_through_the_other_directory(
    bare_coord_mission: tuple[Path, Path, Path],
) -> None:
    """A capture on the coordination dir under a hold on the primary dir is a hold of the same Mission (A2)."""
    repo, primary, coord = bare_coord_mission
    with mission_write_lock(primary, repo_root=repo):
        point = capture_rollback_point(coord, repo_root=repo)
    assert point.events_path.parent == coord
