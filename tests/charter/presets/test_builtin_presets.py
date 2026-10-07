"""Built-in ``default`` / ``minimal`` presets and the kind authority pin (FR-002, T035/T037/T040)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from ruamel.yaml import YAML

from charter.offering.artifact_kinds import ArtifactKind
from charter.offering.missions.mission_type_repository import builtin_mission_type_id_set
from charter.offering.pack_paths import built_in_root
from charter.offering.packs.pack_validator import validate_pack
from charter.offering.packs.presets import (
    KIND_GATE_PLURALS,
    PRESET_GOVERNED_KINDS,
    load_preset,
    preset_activation_keys,
)

pytestmark = [pytest.mark.unit, pytest.mark.fast]

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "src" / "charter" / "offering" / "schemas" / "activation-preset.schema.yaml"


def _load(path: Path) -> Any:
    return YAML(typ="safe").load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    data = _load(_SCHEMA_PATH)
    assert isinstance(data, dict)
    return data


def test_default_lists_no_ids_and_no_kind_gate() -> None:
    default = load_preset(built_in_root(), "default")
    assert default.activations == {}
    assert default.activated_kinds is None
    raw = _load(default.source)
    assert set(raw) == {"name", "description", "mission_type_activations"}


def test_default_activates_every_builtin_mission_type() -> None:
    default = load_preset(built_in_root(), "default")
    assert default.mission_type_activations
    assert set(default.mission_type_activations) == builtin_mission_type_id_set()


def test_minimal_has_no_kind_gate_and_curates_directives_and_tactics() -> None:
    minimal = load_preset(built_in_root(), "minimal")
    assert minimal.activated_kinds is None
    assert minimal.mission_type_activations == ("software-dev",)
    assert set(minimal.activations) == {"activated_directives", "activated_tactics"}
    assert len(minimal.activations["activated_directives"]) == 5
    assert minimal.activations["activated_tactics"] == ("acceptance-test-first",)
    assert "charter pack apply" not in minimal.source.read_text(encoding="utf-8")


def test_builtin_presets_resolve_against_the_offering() -> None:
    result = validate_pack(built_in_root(), check_drg_root=False)
    preset_issues = [issue for issue in result.errors + result.advisories if issue.artifact_type == "preset"]
    assert preset_issues == []


@pytest.mark.parametrize("name", ["default", "minimal"])
def test_builtin_presets_validate_against_the_schema(schema: dict[str, Any], name: str) -> None:
    jsonschema.Draft202012Validator(schema).validate(_load(built_in_root() / "presets" / f"{name}.yaml"))


def test_schema_rejects_an_ungoverned_key(schema: dict[str, Any]) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate({"name": "x", "description": "x", "activated_skills": []})


def test_governed_kinds_are_derived_from_the_authority() -> None:
    expected = {kind for kind in ArtifactKind if kind.activatable} - {ArtifactKind.SKILL, ArtifactKind.GLOSSARY_PACK}
    assert set(PRESET_GOVERNED_KINDS) == expected
    assert len(PRESET_GOVERNED_KINDS) == 9
    assert set(preset_activation_keys()) == {f"activated_{kind.plural}" for kind in expected}
    assert "activated_anti_patterns" in preset_activation_keys()
    assert tuple(kind.plural for kind in ArtifactKind) == KIND_GATE_PLURALS


def test_schema_kind_enums_equal_the_derived_sets(schema: dict[str, Any]) -> None:
    (pattern,) = schema["patternProperties"]
    match = re.fullmatch(r"\^activated_\((?P<alternatives>[a-z_|]+)\)\$", pattern)
    assert match, pattern
    assert set(match["alternatives"].split("|")) == {kind.plural for kind in PRESET_GOVERNED_KINDS}
    assert set(schema["properties"]["activated_kinds"]["items"]["enum"]) == set(KIND_GATE_PLURALS)
