"""Patch-point guards for the identity trio: a patch of
``_primary_runtime_feature_dir`` on ``runtime_bridge_identity`` (its owner) is
observed by both intra-seam callers, so the monkeypatch-based tests in
``tests/runtime/test_runtime_bridge_identity.py`` stay effective (#2561).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.next import runtime_bridge_identity as identity

pytestmark = [pytest.mark.unit, pytest.mark.fast]


def test_resolve_coordination_branch_observes_seam_patch_of_primary_runtime_feature_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A patch of ``_primary_runtime_feature_dir`` on the identity seam is
    observed by ``_resolve_coordination_branch`` (the patch point
    ``tests/runtime/test_runtime_bridge_identity.py`` relies on)."""
    feature_dir = tmp_path / "kitty-specs" / "my-mission-01KWDABC"
    feature_dir.mkdir(parents=True)
    (feature_dir / "meta.json").write_text(
        json.dumps({"coordination_branch": "kitty/mission-my-mission-01KWDABC-lane-a"}),
        encoding="utf-8",
    )
    calls: list[str] = []

    def _spy(repo_root: Path, mission_slug: str) -> Path:
        calls.append("primary")
        return feature_dir

    monkeypatch.setattr(identity, "_primary_runtime_feature_dir", _spy)

    identity._resolve_coordination_branch("my-mission-01KWDABC", tmp_path)

    assert calls == ["primary"], (
        "_resolve_coordination_branch did not observe the patch on "
        "runtime_bridge_identity._primary_runtime_feature_dir"
    )


def test_resolve_mission_ulid_observes_seam_patch_of_primary_runtime_feature_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Same patch point as above, for ``_resolve_mission_ulid``."""
    feature_dir = tmp_path / "kitty-specs" / "my-mission-01KWDABC"
    feature_dir.mkdir(parents=True)
    ulid = "01KWDABC1234567890ABCDEFGH"
    (feature_dir / "meta.json").write_text(json.dumps({"mission_id": ulid}), encoding="utf-8")
    calls: list[str] = []

    def _spy(repo_root: Path, mission_slug: str) -> Path:
        calls.append("primary")
        return feature_dir

    monkeypatch.setattr(identity, "_primary_runtime_feature_dir", _spy)

    result = identity._resolve_mission_ulid("my-mission-01KWDABC", tmp_path)

    assert result == ulid
    assert calls == ["primary"], (
        "_resolve_mission_ulid did not observe the patch on "
        "runtime_bridge_identity._primary_runtime_feature_dir"
    )
