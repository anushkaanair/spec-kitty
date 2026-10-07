"""Retired pack fields are rejected with ``RETIRED_PACK_FIELD`` (#3732, OD-1, contracts/errors.md)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from charter.activation.activations import ActivationEntry
from charter.activation.org_charter import (
    ORG_CHARTER_SCHEMA_VERSION,
    OrgCharterPolicy,
    validate_org_charter_file,
)
from charter.activation.schemas import GovernanceConfig
from charter.offering.packs import retired_fields
from charter.offering.packs.retired_fields import (
    _MIGRATION_RUNBOOK,
    RETIRED_PACK_FIELD,
    RETIRED_PACK_FIELDS,
    RetiredField,
    RetiredPackFieldError,
    reject_retired_fields,
    retired_field_errors,
    _retired_field_message,
)

pytestmark = pytest.mark.fast

OLD = "doctrine_pack_id"
NEW = "charter_pack_id"
CONTEXT = {"mission_type": "software-dev"}


def _entry(**extra: str) -> dict[str, object]:
    return {"activation_context": CONTEXT, "artifact_id": "acceptance-test-first", "artifact_kind": "tactics", **extra}


def _retired_from(exc: ValidationError) -> RetiredPackFieldError:
    found = retired_field_errors(exc)
    assert len(found) == 1, exc
    return found[0]


# --------------------------------------------------------------------------------------
# The table and its helpers
# --------------------------------------------------------------------------------------


def test_table_holds_the_charter_pack_id_rename() -> None:
    assert RetiredField(file="org-charter.yaml", field=OLD, replacement=NEW) in RETIRED_PACK_FIELDS
    assert RETIRED_PACK_FIELD == "RETIRED_PACK_FIELD"


def test_message_names_location_field_replacement_and_runbook() -> None:
    message = _retired_field_message("org-charter.yaml", OLD, NEW)
    assert message == f"org-charter.yaml: field '{OLD}' was removed. Replacement: {NEW}. See {_MIGRATION_RUNBOOK}."


def test_reject_raises_typed_error_with_code_file_field_replacement(tmp_path: Path) -> None:
    path = tmp_path / "org-charter.yaml"
    with pytest.raises(RetiredPackFieldError) as info:
        reject_retired_fields({OLD: "built-in"}, file="org-charter.yaml", path=path)
    err = info.value
    assert (err.code, err.file, err.field, err.replacement, err.path) == (RETIRED_PACK_FIELD, "org-charter.yaml", OLD, NEW, path)
    assert str(err).startswith(f"{path}: field '{OLD}' was removed.")


def test_reject_without_path_locates_by_file_kind() -> None:
    with pytest.raises(RetiredPackFieldError, match=r"^org-charter\.yaml: field"):
        reject_retired_fields({OLD: "x"}, file="org-charter.yaml", path=None)


@pytest.mark.parametrize("raw", [{NEW: "x"}, {}, ["not", "a", "mapping"], None, "text"])
def test_reject_leaves_clean_or_non_mapping_input_alone(raw: object) -> None:
    reject_retired_fields(raw, file="org-charter.yaml", path=None)


def test_reject_is_scoped_to_the_file_kind() -> None:
    reject_retired_fields({OLD: "x"}, file="pack.yaml", path=None)


def test_at_relocates_the_same_rejection(tmp_path: Path) -> None:
    err = RetiredPackFieldError(RETIRED_PACK_FIELDS[0])
    moved = err.at(tmp_path / "x.yaml")
    assert moved.retired == err.retired
    assert str(moved).startswith(f"{tmp_path / 'x.yaml'}: field '{OLD}'")


def test_planted_second_entry_is_rejected_the_same_way(monkeypatch: pytest.MonkeyPatch) -> None:
    """Data-driven: a new row needs no code change."""
    planted = RetiredField(file="pack.yaml", field="planted_field", replacement="delete it")
    monkeypatch.setattr(retired_fields, "RETIRED_PACK_FIELDS", (*RETIRED_PACK_FIELDS, planted))
    with pytest.raises(RetiredPackFieldError) as info:
        reject_retired_fields({"planted_field": 1}, file="pack.yaml", path=None)
    assert info.value.retired == planted
    assert str(info.value) == _retired_field_message("pack.yaml", "planted_field", "delete it")


def test_retired_field_errors_recovers_errors_wrapped_by_pydantic() -> None:
    class _Model(BaseModel):
        model_config = ConfigDict(extra="forbid")
        keep: int = 0

        @model_validator(mode="before")
        @classmethod
        def _check(cls, data: object) -> object:
            reject_retired_fields(data, file="org-charter.yaml", path="planted")
            return data

    with pytest.raises(ValidationError) as info:
        _Model.model_validate({OLD: "x"})
    assert _retired_from(info.value).field == OLD


def test_retired_field_errors_is_empty_for_a_generic_failure() -> None:
    with pytest.raises(ValidationError) as info:
        ActivationEntry.model_validate(_entry(**{NEW: "x", "unrelated_field": "y"}))
    assert retired_field_errors(info.value) == []
    assert "extra" in str(info.value).lower()


# --------------------------------------------------------------------------------------
# The activation entry: project charter.yaml and org-charter.yaml
# --------------------------------------------------------------------------------------


def test_activation_entry_accepts_charter_pack_id() -> None:
    assert ActivationEntry.model_validate(_entry(**{NEW: "built-in"})).charter_pack_id == "built-in"


def test_activation_entry_has_no_alias_for_the_old_name() -> None:
    assert OLD not in ActivationEntry.model_fields
    assert not ActivationEntry.model_config.get("populate_by_name")


def test_activation_entry_rejects_old_name_naming_both_names() -> None:
    with pytest.raises(ValidationError) as info:
        ActivationEntry.model_validate(_entry(**{OLD: "built-in"}))
    err = _retired_from(info.value)
    assert (err.code, err.field, err.replacement) == (RETIRED_PACK_FIELD, OLD, NEW)
    assert OLD in str(info.value) and NEW in str(info.value)


def test_project_charter_activations_reject_old_name() -> None:
    with pytest.raises(ValidationError) as info:
        GovernanceConfig.model_validate({"activations": [_entry(**{OLD: "built-in"})]})
    assert _retired_from(info.value).replacement == NEW


def test_org_charter_activations_reject_old_name() -> None:
    with pytest.raises(ValidationError) as info:
        OrgCharterPolicy.model_validate({"activations": [_entry(**{OLD: "built-in"})]})
    assert _retired_from(info.value).field == OLD


# --------------------------------------------------------------------------------------
# org-charter schema_version 2 (data-model.md "Enforced activations")
# --------------------------------------------------------------------------------------


def test_new_org_charter_defaults_to_schema_version_2() -> None:
    assert ORG_CHARTER_SCHEMA_VERSION == 2
    assert OrgCharterPolicy().schema_version == 2


def test_schema_version_1_without_retired_field_still_validates() -> None:
    policy = OrgCharterPolicy.model_validate({"schema_version": 1, "org_name": "acme", "required_directives": ["d"]})
    assert policy.schema_version == 1


def test_schema_version_1_with_retired_field_is_rejected() -> None:
    with pytest.raises(ValidationError) as info:
        OrgCharterPolicy.model_validate({"schema_version": "1", "activations": [_entry(**{OLD: "built-in"})]})
    assert _retired_from(info.value).code == RETIRED_PACK_FIELD


# --------------------------------------------------------------------------------------
# The validator surfaces a named issue
# --------------------------------------------------------------------------------------


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_validator_names_retired_field_and_replacement(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "org-charter.yaml",
        f"schema_version: 2\nactivations:\n  - activation_context: {{mission_type: software-dev}}\n    {OLD}: built-in\n    artifact_id: a\n",
    )
    issues = validate_org_charter_file(path)
    assert len(issues) == 1
    issue = issues[0]
    assert (issue.severity, issue.category, issue.artifact_id, issue.file) == ("error", RETIRED_PACK_FIELD, OLD, str(path))
    assert issue.message == f"{RETIRED_PACK_FIELD}: {_retired_field_message(str(path), OLD, NEW)}"


def test_validator_keeps_generic_message_for_other_schema_failures(tmp_path: Path) -> None:
    path = _write(tmp_path / "org-charter.yaml", "schema_version: 2\nunknown_key: 1\n")
    issues = validate_org_charter_file(path)
    assert len(issues) == 1
    assert issues[0].category is None
    assert issues[0].message.startswith("org-charter schema validation failed:")


def test_validator_accepts_charter_pack_id(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "org-charter.yaml",
        f"schema_version: 2\nactivations:\n  - activation_context: {{mission_type: software-dev}}\n    {NEW}: built-in\n    artifact_id: a\n",
    )
    assert [i for i in validate_org_charter_file(path) if i.severity == "error"] == []
