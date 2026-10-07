"""``agent action implement`` must not take a WP out of a review lane (#5446).

Before the fix, ``agent action implement <WP> --agent X`` on a WP in
``for_review`` / ``in_review`` / ``approved`` exited 0 and force-moved it to
``in_progress`` ("Re-implementing after review feedback") for *any* agent. The
only legitimate exits are the implementer of record withdrawing an unclaimed
``for_review`` submission, or an operator passing ``--force --note``.

Identities sit on DISTINCT tools (identity is compared per tool).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from click.testing import Result
from typer.testing import CliRunner

from tests.specify_cli.cli.commands.agent import _rework_loop_harness as h

# The #5446 reproduction, fixed: a regression guard now (ADR 2026-07-17-1).
pytestmark = [pytest.mark.integration, pytest.mark.git_repo, pytest.mark.regression]


def _implement_with(m: h.ReworkMission, agent: str, monkeypatch: pytest.MonkeyPatch, *extra: str) -> Result:
    """``h.implement`` with extra argv (the harness helper takes none)."""

    class _ExtraArgsRunner:
        def invoke(self, app: Any, argv: list[str]) -> Result:
            return CliRunner().invoke(app, [*argv, *extra])

    monkeypatch.setattr(h, "CliRunner", _ExtraArgsRunner)
    return h.implement(m, agent, monkeypatch)


def _lane_events(m: h.ReworkMission) -> list[dict[str, object]]:
    return [e for e in h.events(m) if "to_lane" in e]


@pytest.mark.parametrize("agent", [h.THIRD, h.IMPLEMENTER])
def test_in_review_wp_is_not_taken_over(agent: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = h.build_mission(tmp_path, monkeypatch)
    h.drive_to_for_review(m)
    claim = h.move(m, h.WP, "in_review", h.REVIEWER)
    assert claim.exit_code == 0, claim.output
    before = h.events(m)

    result = h.implement(m, agent, monkeypatch)

    assert result.exit_code != 0, result.output
    assert "by 'codex'" in result.output, "the refusal must name the reviewer holding the WP"
    assert h.events(m) == before
    assert _lane_events(m)[-1]["to_lane"] == "in_review"


def test_approved_wp_is_refused_with_the_rework_route(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = h.build_mission(tmp_path, monkeypatch)
    h.drive_to_for_review(m)
    for target in ("in_review", "approved"):
        step = h.move(m, h.WP, target, h.REVIEWER)
        assert step.exit_code == 0, step.output
    before = h.events(m)

    result = h.implement(m, h.IMPLEMENTER, monkeypatch)

    assert result.exit_code != 0, result.output
    assert "move-task" in result.output
    assert "--to planned" in result.output
    assert "--review-feedback-file" in result.output
    assert h.events(m) == before


def test_for_review_wp_is_refused_to_a_non_implementer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = h.build_mission(tmp_path, monkeypatch)
    h.drive_to_for_review(m)
    before = h.events(m)

    result = h.implement(m, h.THIRD, monkeypatch)

    assert result.exit_code != 0, result.output
    assert "implementer-ivan" in result.output, "the refusal must name the implementer of record"
    assert h.events(m) == before
    assert _lane_events(m)[-1]["to_lane"] == "for_review"


def test_implementer_of_record_withdraws_for_review_through_the_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = h.build_mission(tmp_path, monkeypatch)
    h.drive_to_for_review(m)

    result = h.implement(m, h.IMPLEMENTER, monkeypatch)

    assert result.exit_code == 0, result.output
    last = _lane_events(m)[-1]
    assert last["to_lane"] == "in_progress"
    assert str(last["reason"]).startswith("Implementer of record withdrew WP01 from for_review")


@pytest.mark.parametrize("lane", ["for_review", "in_review", "approved"])
def test_operator_force_with_note_takes_over_a_review_lane(lane: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = h.build_mission(tmp_path, monkeypatch)
    h.drive_to_for_review(m)
    for target in {"for_review": (), "in_review": ("in_review",), "approved": ("in_review", "approved")}[lane]:
        assert h.move(m, h.WP, target, h.REVIEWER).exit_code == 0

    result = _implement_with(m, h.THIRD, monkeypatch, "--force", "--note", "reviewer unavailable")

    assert result.exit_code == 0, result.output
    last = _lane_events(m)[-1]
    assert last["to_lane"] == "in_progress"
    assert last["reason"] == "Operator force: reviewer unavailable"
    assert "gemini" in str(last["actor"])


@pytest.mark.parametrize(
    "extra",
    [("--force",), ("--force", "--note", "  "), ("--note", "why")],
    ids=["force-without-note", "force-blank-note", "note-without-force"],
)
def test_invalid_force_note_pairing_is_refused_before_any_write(extra: tuple[str, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = h.build_mission(tmp_path, monkeypatch)
    h.drive_to_for_review(m)
    before = h.events(m)

    result = _implement_with(m, h.THIRD, monkeypatch, *extra)

    assert result.exit_code == 1, result.output
    assert "--note" in result.output
    assert h.events(m) == before


def test_force_outside_a_review_lane_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    m = h.build_mission(tmp_path, monkeypatch)  # WP01 is planned
    before = h.events(m)

    result = _implement_with(m, h.THIRD, monkeypatch, "--force", "--note", "why")

    assert result.exit_code == 1, result.output
    assert "--force only applies" in result.output
    assert h.events(m) == before


def test_force_without_agent_is_refused_before_any_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``--force`` names no implementer of record without ``--agent``, so it is refused before anything is read or written."""
    m = h.build_mission(tmp_path, monkeypatch)
    h.drive_to_for_review(m)
    before = h.events(m)
    monkeypatch.setenv("SPECIFY_REPO_ROOT", str(m.repo))

    result = CliRunner().invoke(h.workflow_module.app, ["implement", h.WP, "--mission", m.mission_slug, "--force", "--note", "why"])

    assert result.exit_code == 1, result.output
    assert "--force requires --agent" in result.output
    assert h.events(m) == before


@pytest.mark.parametrize(
    ("lane", "expected"),
    [
        pytest.param("in_review", "WP01 is under review: wait for the reviewer's verdict", id="in-review"),
        pytest.param("for_review", None, id="for-review-says-it-in-the-conflict"),
        pytest.param("in_progress", None, id="other-lane"),
    ],
)
def test_review_lane_hint_names_the_route(lane: str, expected: str | None, capsys: pytest.CaptureFixture[str]) -> None:
    from specify_cli.cli.commands.agent.workflow_executor import _print_review_lane_hint
    from specify_cli.status import Lane

    _print_review_lane_hint(Lane(lane), "WP01")

    out = capsys.readouterr().out
    assert (expected in out) if expected else out == ""
