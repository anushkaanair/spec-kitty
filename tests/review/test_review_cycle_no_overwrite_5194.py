"""Red-first reproduction for #5194: a later review cycle must not reuse cycle 1.

On a coordination-topology Mission whose first rejection was recorded on the
PRIMARY checkout (``--no-auto-commit`` / ``local_only``), a second rejection
writes to the COORD surface. ``ReviewCycleArtifact.next_cycle_number`` only
globbed the directory it was handed, so the COORD write minted
``review-cycle-1.md`` again and the two surfaces disagreed about cycle 1
(the reported symptom: no ``review-cycle-2.md`` ever appeared).

Each cycle must land as its own ``review-cycle-N.md``, and a file that
already exists is never replaced, on whichever surface it lives.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mission_runtime import MissionArtifactKind, placement_seam
from specify_cli.review.artifacts import ReviewCycleArtifact
from specify_cli.review.cycle import (
    _review_cycle_read_candidate_dirs,
    create_rejected_review_cycle,
    next_review_feedback_source_path,
)
from tests.review.test_cycle_write_dir import _WP_ID, _WP_SLUG, _build_coord_fixture

pytestmark = [pytest.mark.regression, pytest.mark.integration, pytest.mark.git_repo]

_FIRST_BODY = "**Issue**: first rejection, recorded on PRIMARY only.\n"
_SECOND_BODY = "**Issue**: second rejection, written to COORD.\n"


def _artifact(cycle: int, mission_slug: str, body: str) -> ReviewCycleArtifact:
    return ReviewCycleArtifact(
        cycle_number=cycle,
        wp_id=_WP_ID,
        mission_slug=mission_slug,
        reviewer_agent="reviewer-renata",
        reviewed_at="2026-10-07T00:00:00Z",
        affected_files=[],
        reproduction_command=None,
        body=body,
    )


def test_second_rejection_on_coord_surface_does_not_reuse_cycle_one_from_primary(tmp_path: Path) -> None:
    repo, mission_slug = _build_coord_fixture(tmp_path)
    primary_wp_dir = repo / "kitty-specs" / mission_slug / "tasks" / _WP_SLUG
    cycle_one = primary_wp_dir / "review-cycle-1.md"
    _artifact(1, mission_slug, _FIRST_BODY).write(cycle_one)
    before = cycle_one.read_bytes()

    created = create_rejected_review_cycle(
        main_repo_root=repo,
        mission_slug=mission_slug,
        wp_id=_WP_ID,
        wp_slug=_WP_SLUG,
        body=_SECOND_BODY,
        reviewer_agent="reviewer-renata",
        commit_router=None,
    )

    coord_wp_dir = placement_seam(repo, mission_slug).write_dir(MissionArtifactKind.REVIEW_CYCLE).path / "tasks" / _WP_SLUG
    assert coord_wp_dir != primary_wp_dir, "fixture must route the write to the COORD surface"
    assert created.artifact_path.name == "review-cycle-2.md"
    assert (coord_wp_dir / "review-cycle-2.md").is_file()
    assert not (coord_wp_dir / "review-cycle-1.md").exists()
    assert cycle_one.read_bytes() == before


def test_review_cycle_write_never_replaces_an_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "tasks" / "WP01" / "review-cycle-1.md"
    _artifact(1, "m", _FIRST_BODY).write(path)
    before = path.read_bytes()

    with pytest.raises(FileExistsError):
        _artifact(1, "m", _SECOND_BODY).write(path)

    assert path.read_bytes() == before


def test_advertised_feedback_path_matches_allocator_across_surfaces(tmp_path: Path) -> None:
    repo, mission_slug = _build_coord_fixture(tmp_path)
    primary_wp_dir = repo / "kitty-specs" / mission_slug / "tasks" / _WP_SLUG
    _artifact(1, mission_slug, _FIRST_BODY).write(primary_wp_dir / "review-cycle-1.md")
    coord_wp_dir = placement_seam(repo, mission_slug).write_dir(MissionArtifactKind.REVIEW_CYCLE).path / "tasks" / _WP_SLUG

    siblings = _review_cycle_read_candidate_dirs(repo, mission_slug, _WP_SLUG)

    assert next_review_feedback_source_path(coord_wp_dir, siblings) == coord_wp_dir / "review-feedback-2.md"
