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
from specify_cli.cli.commands.agent.tasks_shared import _lane_authored_kitty_specs_paths
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


def _git_bytes(cwd: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)
    return result.stdout


def _commit_all(cwd: Path, message: str) -> None:
    _git(cwd, "add", "-A")
    _git(cwd, "commit", "-q", "-m", message)


def _merge_coordination_update(lane_worktree: Path, coord_tip: str, *, force_merge_commit: bool) -> None:
    if force_merge_commit:
        (lane_worktree / "src").mkdir(parents=True, exist_ok=True)
        (lane_worktree / "src" / "pre_coord_sync.py").write_text("def anchor() -> None: pass\n", encoding="utf-8")
        _commit_all(lane_worktree, "lane: add pre-sync implementation anchor")
        _git(lane_worktree, "merge", "--no-edit", "--no-ff", coord_tip)
        assert len(_git(lane_worktree, "show", "-s", "--format=%P", "HEAD").split()) == 2
        return
    _git(lane_worktree, "merge", "--no-edit", coord_tip)


def _merge_planning_commit(
    lane_worktree: Path,
    planning_commit: str,
    *,
    fork_commit: str,
    resolve_path_to_fork: str | None,
) -> None:
    if resolve_path_to_fork is None:
        _git(lane_worktree, "merge", "--no-edit", planning_commit)
        return

    result = subprocess.run(
        ["git", "merge", "--no-edit", planning_commit],
        cwd=lane_worktree,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert f"UU {resolve_path_to_fork}" in _git(lane_worktree, "status", "--porcelain")
    target_path = lane_worktree / resolve_path_to_fork
    target_path.write_bytes(_git_bytes(lane_worktree, "show", f"{fork_commit}:{resolve_path_to_fork}"))
    _git(lane_worktree, "add", resolve_path_to_fork)
    _git(lane_worktree, "commit", "-q", "-m", "lane: resolve planning conflict to fork bytes")
    parents = _git(lane_worktree, "show", "-s", "--format=%P", "HEAD").split()
    assert len(parents) == 2
    resolved_bytes = target_path.read_bytes()
    assert resolved_bytes == _git_bytes(lane_worktree, "show", f"{fork_commit}:{resolve_path_to_fork}")
    assert all(resolved_bytes != _git_bytes(lane_worktree, "show", f"{parent}:{resolve_path_to_fork}") for parent in parents)


def _add_planning_conflict_revision(repo_root: Path, rel_path: str, *, enabled: bool) -> None:
    if not enabled:
        return
    planning_matrix = repo_root / rel_path
    planning_matrix.write_text(
        planning_matrix.read_text(encoding="utf-8") + "\nPlanning-owned matrix revision.\n",
        encoding="utf-8",
    )


def _apply_lane_edit(
    lane_worktree: Path,
    primary_dir: Path,
    mission_slug: str,
    lane_edit: str | None,
    *,
    fork_commit: str,
    planning_commit: str,
) -> list[str]:
    """Apply one deliberate kitty-specs edit and return its exact path."""
    changed_paths: list[str] = []
    if lane_edit == "primary":
        spec_path = lane_worktree / "kitty-specs" / mission_slug / "spec.md"
        spec_path.write_text(spec_path.read_text(encoding="utf-8") + "\nLane-authored planning change.\n", encoding="utf-8")
        changed_paths.append(f"kitty-specs/{mission_slug}/spec.md")
    elif lane_edit == "plan":
        plan_path = lane_worktree / "kitty-specs" / mission_slug / "plan.md"
        plan_path.write_text(plan_path.read_text(encoding="utf-8") + "\nLane-authored plan edit.\n", encoding="utf-8")
        changed_paths.append(f"kitty-specs/{mission_slug}/plan.md")
    elif lane_edit == "plan-match-p2":
        plan_path = lane_worktree / "kitty-specs" / mission_slug / "plan.md"
        plan_path.write_bytes((primary_dir / "plan.md").read_bytes())
        changed_paths.append(f"kitty-specs/{mission_slug}/plan.md")
    elif lane_edit == "coord":
        matrix_path = lane_worktree / "kitty-specs" / mission_slug / "acceptance-matrix.json"
        matrix_path.write_text(matrix_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        changed_paths.append(f"kitty-specs/{mission_slug}/acceptance-matrix.json")
    elif lane_edit == "coord-match-planning":
        matrix_path = lane_worktree / "kitty-specs" / mission_slug / "acceptance-matrix.json"
        matrix_path.write_bytes((primary_dir / "acceptance-matrix.json").read_bytes())
        changed_paths.append(f"kitty-specs/{mission_slug}/acceptance-matrix.json")
    elif lane_edit == "mission-events":
        events_path = lane_worktree / "kitty-specs" / mission_slug / "mission-events.jsonl"
        events_path.write_text(events_path.read_text(encoding="utf-8") + '{"event":"lane-edit"}\n', encoding="utf-8")
        changed_paths.append(f"kitty-specs/{mission_slug}/mission-events.jsonl")
    elif lane_edit in {
        "coord-revert",
        "wp-prompt-revert",
        "wp-prompt-match-p1",
        "mission-events-delete",
        "status-events-delete",
        "status-json-delete",
    }:
        rel_path = {
            "coord-revert": f"kitty-specs/{mission_slug}/acceptance-matrix.json",
            "wp-prompt-revert": f"kitty-specs/{mission_slug}/tasks/WP01.md",
            "wp-prompt-match-p1": f"kitty-specs/{mission_slug}/tasks/WP01.md",
            "mission-events-delete": f"kitty-specs/{mission_slug}/mission-events.jsonl",
            "status-events-delete": f"kitty-specs/{mission_slug}/status.events.jsonl",
            "status-json-delete": f"kitty-specs/{mission_slug}/status.json",
        }[lane_edit]
        target_path = lane_worktree / rel_path
        if lane_edit.endswith("-delete"):
            target_path.unlink()
        else:
            source_commit = planning_commit if lane_edit == "wp-prompt-match-p1" else fork_commit
            target_path.write_bytes(_git_bytes(lane_worktree, "show", f"{source_commit}:{rel_path}"))
        changed_paths.append(rel_path)
    elif lane_edit == "wp-prompt":
        prompt_path = lane_worktree / "kitty-specs" / mission_slug / "tasks" / "WP01.md"
        prompt_path.write_text(prompt_path.read_text(encoding="utf-8") + "\nLane-authored prompt edit.\n", encoding="utf-8")
        changed_paths.append(f"kitty-specs/{mission_slug}/tasks/WP01.md")
    return changed_paths


def _build_handoff_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    lane_edit: str | None = None,
    missing_planning_ref: bool = False,
    planning_drift_after_lane_merge: bool = False,
    missing_workspace_base_commit: bool = False,
    refresh_planning_commit_after_lane_merge: bool = False,
    coordination_updates_after_lane_base: bool = False,
    d07_noncoord_inherited_paths: bool = False,
    status_events_at_lane_base: bool = False,
    include_status_artifacts_after_lane_base: bool = True,
    materialize_status_snapshot_after_lane_base: bool = True,
    include_issue_matrix_after_coord_update: bool = True,
    include_claim_time_planning_pin: bool = True,
    merge_claim_time_planning_commit: bool = True,
    lane_edit_on_side_branch: bool = False,
    force_coordination_merge_commit: bool = False,
    resolve_planning_coord_conflict_to_fork: bool = False,
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
    if status_events_at_lane_base:
        append_event(
            coord_dir,
            StatusEvent(
                event_id="01KX5151HANDOFFBASESTATE000001",
                mission_slug=mission_slug,
                mission_id=mission_id,
                wp_id="WP01",
                from_lane=Lane.PLANNED,
                to_lane=Lane.IN_PROGRESS,
                at="2026-09-28T11:00:00+00:00",
                actor="test-runner",
                force=False,
                execution_mode="worktree",
                reason="seed status log before lane fork",
            ),
        )
        _commit_all(coord_worktree, "coord: seed status log before lane fork")
    coord_base_commit = _git(coord_worktree, "rev-parse", "HEAD")

    if include_status_artifacts_after_lane_base:
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
    if materialize_status_snapshot_after_lane_base:
        materialize(coord_dir)

    if not d07_noncoord_inherited_paths:
        # These updates are owned by the live coordination branch. Two of them
        # are classified as COORD artifacts; the event log and WP prompt are not.
        (coord_dir / "acceptance-matrix.json").write_text(
            (coord_dir / "acceptance-matrix.json").read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        if include_issue_matrix_after_coord_update:
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
    conflict_path = f"kitty-specs/{mission_slug}/acceptance-matrix.json"
    _add_planning_conflict_revision(repo_root, conflict_path, enabled=resolve_planning_coord_conflict_to_fork)
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
    lane_base_commit = coord_base_commit if coordination_updates_after_lane_base else coord_tip
    _git(repo_root, "worktree", "add", "-b", lane_branch, str(lane_worktree), lane_base_commit)
    if coordination_updates_after_lane_base:
        _merge_coordination_update(lane_worktree, coord_tip, force_merge_commit=force_coordination_merge_commit)
    if merge_claim_time_planning_commit:
        _merge_planning_commit(
            lane_worktree,
            recorded_planning_commit,
            fork_commit=lane_base_commit,
            resolve_path_to_fork=conflict_path if resolve_planning_coord_conflict_to_fork else None,
        )

    if planning_drift_after_lane_merge:
        plan_path.write_text(
            plan_path.read_text(encoding="utf-8") + "\nPlanning target advanced again after lane claim (P2).\n",
            encoding="utf-8",
        )
        _commit_all(repo_root, "planning: advance target to P2 after lane claim")
        p2_commit = _git(repo_root, "rev-parse", "HEAD")
        if refresh_planning_commit_after_lane_merge:
            from specify_cli.lanes.persistence import read_lanes_json, write_lanes_json

            lanes_manifest = read_lanes_json(primary_dir)
            assert lanes_manifest is not None
            lanes_manifest.planning_commit_sha = p2_commit
            write_lanes_json(primary_dir, lanes_manifest)
            _commit_all(repo_root, "finalize: refresh planning commit to P2")

    changed_paths: list[str] = []
    if lane_edit_on_side_branch:
        side_branch = f"{lane_branch}-side"
        _git(lane_worktree, "switch", "-q", "-c", side_branch)
        changed_paths = _apply_lane_edit(
            lane_worktree,
            primary_dir,
            mission_slug,
            lane_edit,
            fork_commit=lane_base_commit,
            planning_commit=recorded_planning_commit,
        )
        _commit_all(lane_worktree, "lane-side: edit WP01 planning artifact")
        _git(lane_worktree, "switch", "-q", lane_branch)
        _git(lane_worktree, "merge", "--no-edit", "--no-ff", side_branch)

    # A real source commit satisfies move-task's implementation-commit guard.
    (lane_worktree / "src").mkdir(parents=True, exist_ok=True)
    (lane_worktree / "src" / "handoff_impl.py").write_text("def ready() -> bool:\n    return True\n", encoding="utf-8")
    if not lane_edit_on_side_branch:
        changed_paths = _apply_lane_edit(
            lane_worktree,
            primary_dir,
            mission_slug,
            lane_edit,
            fork_commit=lane_base_commit,
            planning_commit=recorded_planning_commit,
        )
    _commit_all(lane_worktree, "lane: implement WP01")

    context_path = save_context(
        repo_root,
        WorkspaceContext(
            wp_id="WP01",
            mission_slug=mission_slug,
            worktree_path=lane_worktree.relative_to(repo_root).as_posix(),
            branch_name=lane_branch,
            base_branch=coord_branch,
            base_commit=None if missing_workspace_base_commit else lane_base_commit,
            dependencies=[],
            created_at="2026-09-28T12:01:00+00:00",
            created_by="test-fixture",
            vcs_backend="git",
            lane_id="lane-a",
            lane_wp_ids=["WP01"],
            current_wp="WP01",
            planning_commit_sha=recorded_planning_commit if include_claim_time_planning_pin else None,
        ),
    )
    context_data = json.loads(context_path.read_text(encoding="utf-8"))
    if not include_claim_time_planning_pin:
        context_data.pop("planning_commit_sha", None)
    context_path.write_text(json.dumps(context_data, indent=2) + "\n", encoding="utf-8")
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


def test_lane_plan_edit_matching_p2_is_still_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, changed_paths = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        lane_edit="plan-match-p2",
        planning_drift_after_lane_merge=True,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert changed_paths[0] in result.output


def test_claim_time_p1_survives_finalize_refresh_to_p2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        planning_drift_after_lane_merge=True,
        refresh_planning_commit_after_lane_merge=True,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code == 0, result.output


def test_existing_lane_history_proves_p1_and_d07_coordination_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A legacy context can prove inherited content from its lane history."""
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        planning_drift_after_lane_merge=True,
        refresh_planning_commit_after_lane_merge=True,
        coordination_updates_after_lane_base=True,
        d07_noncoord_inherited_paths=True,
        include_claim_time_planning_pin=False,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code == 0, result.output


def test_clean_coordination_merge_commit_is_inherited(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        coordination_updates_after_lane_base=True,
        d07_noncoord_inherited_paths=True,
        include_claim_time_planning_pin=False,
        force_coordination_merge_commit=True,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code == 0, result.output


def test_conflict_resolution_to_fork_bytes_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        coordination_updates_after_lane_base=True,
        resolve_planning_coord_conflict_to_fork=True,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert f"kitty-specs/{mission_slug}/acceptance-matrix.json" in result.output


@pytest.mark.parametrize("lane_edit", ["mission-events", "wp-prompt"])
def test_lane_authored_d07_coordination_content_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lane_edit: str,
) -> None:
    repo_root, mission_slug, _lane_worktree, changed_paths = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        lane_edit=lane_edit,
        planning_drift_after_lane_merge=True,
        coordination_updates_after_lane_base=True,
        d07_noncoord_inherited_paths=True,
        include_claim_time_planning_pin=False,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert changed_paths[0] in result.output


@pytest.mark.parametrize(
    ("lane_edit", "d07_paths"),
    [
        ("coord-revert", False),
        ("wp-prompt-revert", True),
        ("wp-prompt-match-p1", True),
        ("mission-events-delete", True),
        ("status-events-delete", True),
        ("status-json-delete", True),
    ],
)
def test_lane_authored_reversal_of_post_fork_coord_content_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lane_edit: str,
    d07_paths: bool,
) -> None:
    repo_root, mission_slug, _lane_worktree, changed_paths = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        lane_edit=lane_edit,
        planning_drift_after_lane_merge=True,
        coordination_updates_after_lane_base=True,
        d07_noncoord_inherited_paths=d07_paths,
        status_events_at_lane_base=lane_edit == "status-json-delete",
        include_status_artifacts_after_lane_base=lane_edit == "status-events-delete",
        materialize_status_snapshot_after_lane_base=lane_edit == "status-json-delete",
        include_issue_matrix_after_coord_update=lane_edit != "coord-revert",
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert changed_paths[0] in result.output


@pytest.mark.parametrize("lane_edit", ["coord-revert", "wp-prompt-revert", "mission-events-delete"])
def test_side_branch_lane_authored_reversal_of_post_fork_coord_content_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lane_edit: str,
) -> None:
    repo_root, mission_slug, _lane_worktree, changed_paths = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        lane_edit=lane_edit,
        lane_edit_on_side_branch=True,
        planning_drift_after_lane_merge=True,
        coordination_updates_after_lane_base=True,
        d07_noncoord_inherited_paths=lane_edit != "coord-revert",
        include_claim_time_planning_pin=False,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "kitty-specs/ changes are not allowed on lane branches" in result.output
    assert changed_paths[0] in result.output


def test_legacy_context_without_post_fork_planning_pin_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, mission_slug, _lane_worktree, _ = _build_handoff_repo(
        tmp_path,
        monkeypatch,
        lane_edit="plan",
        planning_drift_after_lane_merge=True,
        include_claim_time_planning_pin=False,
        merge_claim_time_planning_commit=False,
    )
    monkeypatch.chdir(repo_root)

    result = _move_for_review(repo_root, mission_slug)

    assert result.exit_code != 0
    assert "could not verify" in result.output.lower()
    assert "No handoff was made" in result.output


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


def test_lane_authorship_history_command_failure_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _failed_git(*args, **_kwargs):
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="git history unavailable")

    monkeypatch.setattr("specify_cli.cli.commands.agent.tasks.subprocess.run", _failed_git)

    result = _lane_authored_kitty_specs_paths(tmp_path, "fork", ("planning", "coordination"))

    assert result is None


def test_lane_authorship_history_timeout_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _timed_out(args, **_kwargs):
        raise subprocess.TimeoutExpired(args, timeout=30)

    monkeypatch.setattr("specify_cli.cli.commands.agent.tasks.subprocess.run", _timed_out)

    result = _lane_authored_kitty_specs_paths(tmp_path, "fork", ("planning", "coordination"))

    assert result is None


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
