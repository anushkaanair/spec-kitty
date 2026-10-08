"""One canonical Mission lock key (mission-writer-followups WP01, plan D1 and A1-A4).

Every per-Mission lock door resolves the same lock file for a Mission, including a
legacy bare-directory coordination Mission: a primary directory ``060-test`` whose
``meta.json`` records a coordination branch and mid8 ``01COORD0``, with its
coordination surface in ``060-test-01COORD0``.
"""

from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Any

import pytest

from specify_cli.coordination.legacy_resolution import _mission_specs_dir_name, _transaction_lock_key
from specify_cli.lanes.branch_naming import MissionLockKeyUnresolved
from specify_cli.mission_metadata import flatten_coordination_metadata
from specify_cli.missions._read_path_resolver import mission_write_lock_dir
from specify_cli.status import FeatureStatusLockTimeoutError, mission_lock_key
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


# ---------------------------------------------------------------------------
# T002 -- the key function
# ---------------------------------------------------------------------------


def test_key_is_equal_for_primary_and_coordination_directories_of_a_bare_directory_mission(
    bare_coord_mission: tuple[Path, Path, Path],
) -> None:
    repo, primary, coord = bare_coord_mission
    assert mission_lock_key(primary, repo_root=repo) == COORD_NAME
    assert mission_lock_key(coord, repo_root=repo) == COORD_NAME
    assert mission_lock_key(primary, repo_root=repo) == _transaction_lock_key(SLUG, MID8)


def test_key_of_a_modern_coordination_mission_is_its_own_directory_name(repo: Path) -> None:
    primary = _write_meta(
        repo / "kitty-specs" / "foo-01KV6510",
        {"mission_slug": "foo-01KV6510", "mission_id": "01KV6510ABCDEFGHJKMNPQRSTV", "coordination_branch": "kitty/mission-foo-01KV6510"},
    )
    assert mission_lock_key(primary, repo_root=repo) == "foo-01KV6510"


def test_key_of_a_flat_mission_is_the_directory_name_even_when_the_slug_differs(repo: Path) -> None:
    flat = _write_meta(repo / "kitty-specs" / "foo-01AAAAAA", {"mission_slug": "foo", "mid8": "01AAAAAA"})
    assert mission_lock_key(flat, repo_root=repo) == "foo-01AAAAAA"


def test_key_of_a_directory_without_meta_is_the_directory_name(repo: Path) -> None:
    bare = repo / "kitty-specs" / "017-foo"
    bare.mkdir()
    assert mission_lock_key(bare, repo_root=repo) == "017-foo"


@pytest.mark.parametrize(
    ("meta", "expected"),
    [
        ({"mid8": "01AAAAAA", "mission_id": "01BBBBBBXXXXXXXXXXXXXXXXXX"}, "060-test-01AAAAAA"),
        ({"mission_id": "01BBBBBBXXXXXXXXXXXXXXXXXX"}, "060-test-01BBBBBB"),
    ],
)
def test_mid8_cascade_prefers_meta_mid8_then_mission_id(repo: Path, meta: dict[str, object], expected: str) -> None:
    primary = _write_meta(repo / "kitty-specs" / SLUG, {"mission_slug": SLUG, "coordination_branch": "kitty/mission-x", **meta})
    assert mission_lock_key(primary, repo_root=repo) == expected


def test_mid8_cascade_falls_back_to_the_slug_tail(repo: Path) -> None:
    primary = _write_meta(repo / "kitty-specs" / "foo-01CCCCCC", {"mission_slug": "foo-01CCCCCC", "coordination_branch": "kitty/mission-x"})
    assert mission_lock_key(primary, repo_root=repo) == "foo-01CCCCCC"


@pytest.mark.parametrize("slug", [SLUG, "modern-slug"])
def test_coordination_mission_without_a_resolvable_mid8_raises_a_typed_error(repo: Path, slug: str) -> None:
    primary = _write_meta(repo / "kitty-specs" / slug, {"mission_slug": slug, "coordination_branch": "kitty/mission-x"})
    with pytest.raises(MissionLockKeyUnresolved) as raised:
        mission_lock_key(primary, repo_root=repo)
    assert raised.value.error_code == "MISSION_LOCK_KEY_UNRESOLVED"
    assert raised.value.to_dict()["mission_slug"] == slug


def test_transaction_lock_key_has_no_trailing_dash_without_a_mid8() -> None:
    assert _transaction_lock_key("060-test", "") == "060-test"
    assert _transaction_lock_key("foo", "01AAAAAA") == "foo-01AAAAAA"
    assert _transaction_lock_key("foo-01AAAAAA", "01AAAAAA") == "foo-01AAAAAA"


def test_key_ignores_a_lane_worktree_copy_of_meta(bare_coord_mission: tuple[Path, Path, Path]) -> None:
    """The canonical primary meta decides; a stale lane copy without the coordination record does not."""
    repo, _primary, _coord = bare_coord_mission
    lane_copy = _write_meta(repo / ".worktrees" / "x-lane-a" / "kitty-specs" / SLUG, {"mission_slug": SLUG})
    assert mission_lock_key(lane_copy, repo_root=repo) == COORD_NAME


def test_write_lock_dir_is_named_by_the_key(bare_coord_mission: tuple[Path, Path, Path]) -> None:
    repo, _primary, _coord = bare_coord_mission
    assert mission_write_lock_dir(repo, SLUG).name == COORD_NAME


# ---------------------------------------------------------------------------
# T003 -- key stability inside a hold
# ---------------------------------------------------------------------------


def test_nested_entry_reuses_the_held_key_after_meta_changes_inside_the_hold(
    bare_coord_mission: tuple[Path, Path, Path],
) -> None:
    repo, primary, _coord = bare_coord_mission
    with mission_write_lock(primary, repo_root=repo) as outer:
        flatten_coordination_metadata(primary)
        assert "coordination_branch" not in json.loads((primary / "meta.json").read_text(encoding="utf-8"))
        assert mission_lock_key(primary, repo_root=repo) == COORD_NAME
        with mission_write_lock(primary, repo_root=repo) as inner:
            assert inner == outer
    # Outside the hold the key follows the (now flat) meta again.
    assert mission_lock_key(primary, repo_root=repo) == SLUG


# ---------------------------------------------------------------------------
# NFR-001 -- two threads, injected pause points, no sleeps
# ---------------------------------------------------------------------------


def test_a_hold_through_the_primary_dir_excludes_a_writer_through_the_coordination_dir(
    bare_coord_mission: tuple[Path, Path, Path],
) -> None:
    repo, primary, coord = bare_coord_mission
    holding = threading.Event()
    release = threading.Event()

    def _holder() -> None:
        with mission_write_lock(primary, repo_root=repo):
            holding.set()
            assert release.wait(timeout=30)

    thread = threading.Thread(target=_holder)
    thread.start()
    try:
        assert holding.wait(timeout=30)
        with pytest.raises(FeatureStatusLockTimeoutError), mission_write_lock(coord, repo_root=repo, timeout=0.2):
            pytest.fail("the coordination-dir writer entered while the primary-dir writer held the Mission lock")
    finally:
        release.set()
        thread.join(timeout=30)
    with mission_write_lock(coord, repo_root=repo, timeout=5):
        pass


# ---------------------------------------------------------------------------
# NFR-003 / A12 -- no subprocess on the uncontended path once the cache is warm
# ---------------------------------------------------------------------------


def test_uncontended_lock_costs_no_subprocess_once_the_git_cache_is_warm(bare_coord_mission: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    repo, primary, _coord = bare_coord_mission
    with mission_write_lock(primary, repo_root=repo):
        pass  # warm the git_common_dir cache
    calls: list[object] = []
    real_popen = subprocess.Popen

    def _counting(*args: Any, **kwargs: Any) -> Any:
        calls.append(args)
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", _counting)
    with mission_write_lock(primary, repo_root=repo):
        assert mission_lock_key(primary, repo_root=repo) == COORD_NAME
    assert calls == []
