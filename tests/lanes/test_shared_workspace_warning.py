"""Advisory shared-workspace warning (#5099; concurrent-mission-writers WP02, T012).

``agent action implement`` and ``agent action review`` name every OTHER actor that
holds a WP ``in_progress`` / ``in_review`` in the same resolved workspace: the
repository root checkout of a single_branch Mission (across Missions), or the
lane worktree for lanes Missions. Advisory only: nothing is refused (C-004).

Neither command has a JSON mode (their output is the prompt text), so the warning
is human output only; the structured entries are :class:`SharedWorkspaceWriter`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.cli.commands.agent import workflow_executor
from specify_cli.lanes.checkout_occupancy import SharedWorkspaceWriter, in_progress_wps_in_write_checkout, shared_workspace_writers
from specify_cli.lanes.compute import PLANNING_LANE_ID
from tests.lanes.test_checkout_occupancy import _init_repo, _write_lanes, _write_repo_root_lane, _write_single_branch_meta
from specify_cli.workspace.context import ResolvedWorkspace
from tests.utils import write_wp

pytestmark = [pytest.mark.fast, pytest.mark.git_repo]

MISSION = "shared-ws-mission"
OTHER_MISSION = "shared-ws-other"


def _single_branch_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write_single_branch_meta(repo, MISSION, "01SHAREDWSMISSION000000001")
    _write_repo_root_lane(repo, MISSION, "WP01", "WP02")
    return repo


def _workspace(lane_id: str, wp_ids: tuple[str, ...]) -> ResolvedWorkspace:
    return ResolvedWorkspace(
        mission_slug=MISSION,
        wp_id=wp_ids[0],
        execution_mode="code_change",
        mode_source="test",
        resolution_kind="repo_root" if lane_id == PLANNING_LANE_ID else "lane_workspace",
        workspace_name=lane_id,
        worktree_path=Path("."),
        branch_name=None,
        lane_id=lane_id,
        lane_wp_ids=list(wp_ids),
    )


def _repo_root_workspace(wp_ids: tuple[str, ...] = ("WP01", "WP02")) -> ResolvedWorkspace:
    return _workspace(PLANNING_LANE_ID, wp_ids)


def test_review_arm_names_the_other_actor_holding_a_wp_in_progress(tmp_path: Path) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "in_progress", "WP01", agent="alice")
    write_wp(repo, MISSION, "for_review", "WP02", agent="bob")

    writers = shared_workspace_writers(repo, MISSION, "WP02", _repo_root_workspace(), "bob")

    assert writers == [SharedWorkspaceWriter(MISSION, "WP01", "in_progress", "alice")]
    assert writers[0].warning() == f"Warning: {MISSION}/WP01 is in_progress by alice in this workspace; one writer per checkout (#5099)."


def test_implement_arm_names_a_wp_another_actor_has_in_review(tmp_path: Path) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "in_review", "WP01", agent="reviewer-rae")
    write_wp(repo, MISSION, "planned", "WP02", agent="alice")

    writers = shared_workspace_writers(repo, MISSION, "WP02", _repo_root_workspace(), "alice")

    assert [(w.wp_id, w.lane, w.actor) for w in writers] == [("WP01", "in_review", "reviewer-rae")]


def test_single_branch_scan_crosses_missions(tmp_path: Path) -> None:
    repo = _single_branch_repo(tmp_path)
    _write_single_branch_meta(repo, OTHER_MISSION, "01SHAREDWSOTHER0000000001")
    _write_repo_root_lane(repo, OTHER_MISSION, "WP01")
    write_wp(repo, OTHER_MISSION, "in_progress", "WP01", agent="carol")

    writers = shared_workspace_writers(repo, MISSION, "WP01", _repo_root_workspace(), "alice")

    assert [(w.mission_slug, w.wp_id, w.actor) for w in writers] == [(OTHER_MISSION, "WP01", "carol")]


def test_lanes_arm_names_the_other_actor_on_the_same_lane_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "kitty-specs" / "lanes-ws-mission").mkdir(parents=True)
    _write_lanes(repo, "lanes-ws-mission", {"lane-a": ("WP01", "WP02"), "lane-b": ("WP03",)})
    write_wp(repo, "lanes-ws-mission", "in_progress", "WP01", agent="alice")
    write_wp(repo, "lanes-ws-mission", "planned", "WP02", agent="bob")
    write_wp(repo, "lanes-ws-mission", "in_progress", "WP03", agent="dana")  # another lane worktree: not shared
    lane_a = _workspace("lane-a", ("WP01", "WP02"))

    writers = shared_workspace_writers(repo, "lanes-ws-mission", "WP02", lane_a, "bob")

    assert [(w.wp_id, w.lane, w.actor) for w in writers] == [("WP01", "in_progress", "alice")]


def test_no_concurrent_writer_means_no_warning(tmp_path: Path) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "planned", "WP01", agent="alice")
    write_wp(repo, MISSION, "for_review", "WP02", agent="bob")

    assert shared_workspace_writers(repo, MISSION, "WP02", _repo_root_workspace(), "bob") == []


def test_same_actor_is_not_a_shared_writer(tmp_path: Path) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "in_progress", "WP01", agent="alice")
    write_wp(repo, MISSION, "planned", "WP02", agent="alice")

    assert shared_workspace_writers(repo, MISSION, "WP02", _repo_root_workspace(), "alice") == []


def test_the_calling_wp_itself_is_never_reported(tmp_path: Path) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "in_progress", "WP01", agent="alice")

    assert shared_workspace_writers(repo, MISSION, "WP01", _repo_root_workspace(("WP01",)), "bob") == []


def test_unknown_calling_actor_counts_as_different(tmp_path: Path) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "in_progress", "WP01", agent="alice")

    assert len(shared_workspace_writers(repo, MISSION, "WP02", _repo_root_workspace(), None)) == 1


def test_in_progress_scan_keeps_its_public_behaviour_and_ignores_in_review(tmp_path: Path) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "in_progress", "WP01", agent="alice")
    write_wp(repo, MISSION, "in_review", "WP02", agent="bob")

    assert in_progress_wps_in_write_checkout(repo, repo) == [(MISSION, "WP01")]


def test_warn_helper_prints_each_warning_and_returns_the_lines(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "in_progress", "WP01", agent="alice")
    write_wp(repo, MISSION, "planned", "WP02", agent="bob")

    lines = workflow_executor.warn_shared_workspace_writers(repo, MISSION, "WP02", _repo_root_workspace(), "bob")

    assert lines == [f"Warning: {MISSION}/WP01 is in_progress by alice in this workspace; one writer per checkout (#5099)."]
    assert capsys.readouterr().out.splitlines() == lines


def test_warn_helper_prints_nothing_without_a_concurrent_writer(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _single_branch_repo(tmp_path)
    write_wp(repo, MISSION, "planned", "WP01", agent="alice")

    assert workflow_executor.warn_shared_workspace_writers(repo, MISSION, "WP01", _repo_root_workspace(), "alice") == []
    assert capsys.readouterr().out == ""
