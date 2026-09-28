"""Live ``move-task`` coverage for coordination-born lane history (#5151).

The fixture creates a real coordination worktree, advances its canonical
mission state and task prompt, then claims a lane from that coordination tip
while the planning branch remains stale. The assertions go through the stable
``agent tasks move-task`` CLI surface, not the contamination helper alone.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli.cli.commands.agent.tasks import (
    _filter_by_planning_tip_content,
    _list_wp_branch_mission_specs_changes,
    app as tasks_app,
)
from specify_cli.coordination.workspace import CoordinationWorkspace
from specify_cli.status.models import Lane, StatusEvent
from specify_cli.status.reducer import materialize
from specify_cli.status.store import append_event
from specify_cli.workspace.context import WorkspaceContext, save_context
from tests.characterization.test_trio_json_envelope import _build_mission_repo
from tests.lane_test_utils import lane_branch_name, lane_worktree_path

pytestmark = [pytest.mark.integration, pytest.mark.git_repo]

_runner = CliRunner()


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _commit_all(cwd: Path, message: str) -> None:
    _git(cwd, "add", "-A")
    _git(cwd, "commit", "-q", "-m", message)


def _build_handoff_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    lane_edit: str | None = None,
    missing_planning_ref: bool = False,
    planning_drift_after_lane_merge: bool = False,
    missing_workspace_base_commit: bool = False,
) -> tuple[Path, str, Path, list[str]]:
    """Create a coord-parented lane with a later planning-tip commit.

    The coordination branch contains the current status files, matrices,
    mission event log, and WP prompt. The planning branch advances separately
    with a planning commit; the lane merges that commit after forking from the
    coordination branch, matching the production claim-time topology.
    """
    repo_root, mission_slug = _build_mission_repo(
        tmp_path,
        monkeypatch,
        coord=True,
        mission_slug="issue-5151-handoff",
        wp_lane="planned",
        materialize_coord=True,
    )
    primary_dir = repo_root / "kitty-specs" / mission_slug
    meta = json.loads((primary_dir / "meta.json").read_text(encoding="utf-8"))
    mission_id = str(meta["mission_id"])
    coord_branch = str(meta["coordination_branch"])
    coord_worktree = CoordinationWorkspace.worktree_path(repo_root, mission_slug, mission_id[:8])
    coord_dir = coord_worktree / "kitty-specs" / mission_slug

    append_event(
        coord_dir,
        StatusEvent(
            event_id="01KX5151HANDOFFINPROGRESS0001",
            mission_slug=mission_slug,
            mission_id=mission_id,
            wp_id="WP01",
            from_lane=Lane.PLANNED,
            to_lane=Lane.IN_PROGRESS,
            at="2026-09-28T12:00:00+00:00",
            actor="test-runner",
            force=False,
            execution_mode="worktree",
            reason="seed live handoff fixture",
        ),
    )
    materialize(coord_dir)

    # These updates are owned by the live coordination branch. Two of them
    # are classified as COORD artifacts; the event log and WP prompt are not.
    (coord_dir / "acceptance-matrix.json").write_text(
        (coord_dir / "acceptance-matrix.json").read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    (coord_dir / "issue-matrix.md").write_text(
        "# Issue Matrix\n\nCoordination-owned fixture row.\n",
        encoding="utf-8",
    )
    (coord_dir / "mission-events.jsonl").write_text('{"event":"coordination-update"}\n', encoding="utf-8")
    wp_prompt = coord_dir / "tasks" / "WP01.md"
    wp_prompt.write_text(
        wp_prompt.read_text(encoding="utf-8") + "\nCoordinator-owned prompt update after planning target moved.\n",
        encoding="utf-8",
    )
    _commit_all(coord_worktree, "coord: record current mission state")
    coord_tip = _git(coord_worktree, "rev-parse", "HEAD")

    # Move the planning target after the coordination snapshot. The lane will
    # merge this recorded planning commit, while the current coordinator state
    # remains its actual fork base.
    plan_path = primary_dir / "plan.md"
    plan_path.write_text(
        plan_path.read_text(encoding="utf-8") + "\nPlanning target advanced after coordination snapshot.\n",
        encoding="utf-8",
    )
    if missing_planning_ref:
        meta["planning_base_branch"] = "missing-planning-ref"
        (primary_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    _commit_all(repo_root, "planning: advance after coordination snapshot")
    recorded_planning_commit = _git(repo_root, "rev-parse", "HEAD")
    if planning_drift_after_lane_merge:
        from specify_cli.lanes.persistence import read_lanes_json, write_lanes_json

        lanes_manifest = read_lanes_json(primary_dir)
        assert lanes_manifest is not None
        lanes_manifest.planning_commit_sha = recorded_planning_commit
        write_lanes_json(primary_dir, lanes_manifest)
        _commit_all(repo_root, "planning: persist recorded planning commit")

    lane_branch = lane_branch_name(mission_slug, "lane-a")
    lane_worktree = lane_worktree_path(repo_root, mission_slug, "lane-a")
    _git(repo_root, "worktree", "add", "-b", lane_branch, str(lane_worktree), coord_branch)
    _git(lane_worktree, "merge", "--no-edit", recorded_planning_commit)

    if planning_drift_after_lane_merge:
        plan_path.write_text(
            plan_path.read_text(encoding="utf-8") + "\nPlanning target advanced again after lane claim (P2).\n",
            encoding="utf-8",
        )
        _commit_all(repo_root, "planning: advance target to P2 after lane claim")

    # A real source commit satisfies move-task's implementation-commit guard.
    (lane_worktree / "src").mkdir(parents=True, exist_ok=True)
    (lane_worktree / "src" / "handoff_impl.py").write_text("def ready() -> bool:\n    return True\n", encoding="utf-8")
    changed_paths: list[str] = []
    if lane_edit == "primary":
        spec_path = lane_worktree / "kitty-specs" / mission_slug / "spec.md"
        spec_path.write_text(
            spec_path.read_text(encoding="utf-8") + "\nLane-authored planning change.\n",
            encoding="utf-8",
        )
        changed_paths.append(f"kitty-specs/{mission_slug}/spec.md")
    elif lane_edit == "plan":
        plan_path = lane_worktree / "kitty-specs" / mission_slug / "plan.md"
        plan_path.write_text(
            plan_path.read_text(encoding="utf-8") + "\nLane-authored plan edit.\n",
            encoding="utf-8",
        )
        changed_paths.append(f"kitty-specs/{mission_slug}/plan.md")
    elif lane_edit == "coord":
        matrix_path = lane_worktree / "kitty-specs" / mission_slug / "acceptance-matrix.json"
        matrix_path.write_text(
            matrix_path.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        changed_paths.append(f"kitty-specs/{mission_slug}/acceptance-matrix.json")
    elif lane_edit == "coord-match-planning":
        matrix_path = lane_worktree / "kitty-specs" / mission_slug / "acceptance-matrix.json"
        planning_matrix = primary_dir / "acceptance-matrix.json"
        matrix_path.write_bytes(planning_matrix.read_bytes())
        changed_paths.append(f"kitty-specs/{mission_slug}/acceptance-matrix.json")
    _commit_all(lane_worktree, "lane: implement WP01")

    save_context(
        repo_root,
        WorkspaceContext(
            wp_id="WP01",
            mission_slug=mission_slug,
            worktree_path=lane_worktree.relative_to(repo_root).as_posix(),
            branch_name=lane_branch,
            base_branch=coord_branch,
            base_commit=None if missing_workspace_base_commit else coord_tip,
            dependencies=[],
            created_at="2026-09-28T12:01:00+00:00",
            created_by="test-fixture",
            vcs_backend="git",
            lane_id="lane-a",
            lane_wp_ids=["WP01"],
            current_wp="WP01",
        ),
    )
    return repo_root, mission_slug, lane_worktree, changed_paths


def _move_for_review(repo_root: Path, mission_slug: str):
    result = _runner.invoke(
        tasks_app,
        [
            "move-task",
            "WP01",
            "--to",
            "for_review",
            "--mission",
            mission_slug,
            "--no-auto-commit",
        ],
        catch_exceptions=False,
    )
    return result


def test_clean_coordination_inheritance_passes_move_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(tmp_path, monkeypatch)
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code == 0, result.output


def test_recorded_p1_plan_stays_clean_after_planning_target_advances_to_p2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        planning_drift_after_lane_merge=True,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code == 0, result.output


def test_lane_plan_edit_after_recorded_p1_is_still_rejected_after_p2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, changed_paths = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        lane_edit="plan",
        planning_drift_after_lane_merge=True,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert changed_paths[0] in result.output


def test_quoted_kitty_specs_path_fails_closed(tmp_path: Path) -> None:
    """A quoted path from ``git diff --name-only`` must not disappear cleanly."""
    repo = tmp_path / "quoted-path-repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test Runner")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "README.md").write_text("anchor\n", encoding="utf-8")
    _commit_all(repo, "anchor")

    _git(repo, "checkout", "-q", "-b", "lane")
    mission_dir = repo / "kitty-specs" / "test-mission"
    mission_dir.mkdir(parents=True)
    (mission_dir / "odd\tname.json").write_text("lane content\n", encoding="utf-8")
    _commit_all(repo, "lane: add quoted path")

    output = _git(repo, "diff", "--name-only", "main", "HEAD", "--", "kitty-specs/")
    assert output.startswith('"kitty-specs/')

    flagged = _list_wp_branch_mission_specs_changes(repo, "main")

    assert flagged is None
    assert _filter_by_planning_tip_content(repo, [], "main") is None


def test_lane_authored_coordination_matrix_change_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, changed_paths = _build_handoff_repo(tmp_path, monkeypatch, lane_edit="coord")
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert changed_paths[0] in result.output
    assert "git restore --source" not in result.output


def test_lane_coord_edit_that_matches_planning_tip_is_still_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, changed_paths = _build_handoff_repo(tmp_path, monkeypatch, lane_edit="coord-match-planning")
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert changed_paths[0] in result.output


def test_lane_authored_primary_planning_change_remains_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, changed_paths = _build_handoff_repo(tmp_path, monkeypatch, lane_edit="primary")
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert changed_paths[0] in result.output


def test_unresolvable_planning_ref_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(tmp_path, monkeypatch, missing_planning_ref=True)
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "could not verify" in result.output.lower()
    assert "kitty-specs/" in result.output


def test_missing_claim_time_workspace_snapshot_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        missing_workspace_base_commit=True,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "could not verify" in result.output.lower()
    assert "claim-time workspace snapshot" in result.output.lower()
