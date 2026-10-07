"""Retired charter pack fields and their ``RETIRED_PACK_FIELD`` rejection (#3732).

The charter-pack cutover (ADR 2026-10-06-1) removes some fields from pack files
outright, with no alias (C-001). A file that still carries one is rejected with
the code :data:`RETIRED_PACK_FIELD`, naming the field and its replacement, instead
of pydantic's generic "extra fields not permitted" error (``contracts/errors.md``).

:data:`RETIRED_PACK_FIELDS` is the one table of retired fields: a loader or
validator calls :func:`reject_retired_fields` with the raw mapping and the file
kind it is reading, and a validator that only sees a pydantic
``ValidationError`` recovers the typed errors with :func:`retired_field_errors`.

This module is the only source of the ``RETIRED_PACK_FIELD`` code string. It
lives in the offering tier and imports nothing from ``charter.activation``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

__all__ = [
    "RETIRED_PACK_FIELD",
    "RETIRED_PACK_FIELDS",
    "RetiredField",
    "RetiredPackFieldError",
    "reject_retired_fields",
    "retired_field_errors",
]

#: The error code a retired pack field is rejected with (``contracts/errors.md``).
RETIRED_PACK_FIELD = "RETIRED_PACK_FIELD"

#: The runbook every rejection points at.
_MIGRATION_RUNBOOK = "docs/migrations/charter-pack-cutover.md"


@dataclass(frozen=True)
class RetiredField:
    """One retired field: the file kind that carried it, its name and its replacement."""

    file: str
    field: str
    replacement: str


#: Every retired pack field. Adding a row is the whole change for a new one.
RETIRED_PACK_FIELDS: tuple[RetiredField, ...] = (RetiredField(file="org-charter.yaml", field="doctrine_pack_id", replacement="charter_pack_id"),)


def _retired_field_message(location: str, field: str, replacement: str) -> str:
    """Return the operator message for a retired *field* found at *location*."""
    return f"{location}: field '{field}' was removed. Replacement: {replacement}. See {_MIGRATION_RUNBOOK}."


class RetiredPackFieldError(ValueError):
    """A pack file still carries a retired field (code :data:`RETIRED_PACK_FIELD`)."""

    code = RETIRED_PACK_FIELD

    def __init__(self, retired: RetiredField, *, path: Path | str | None = None) -> None:
        self.file = retired.file
        self.field = retired.field
        self.replacement = retired.replacement
        self.path = path
        location = str(path) if path is not None else retired.file
        super().__init__(_retired_field_message(location, retired.field, retired.replacement))

    @property
    def retired(self) -> RetiredField:
        """The table row this error was raised for."""
        return RetiredField(file=self.file, field=self.field, replacement=self.replacement)

    def at(self, path: Path | str) -> RetiredPackFieldError:
        """Return the same rejection located at *path* (for a caller that knows the file)."""
        return RetiredPackFieldError(self.retired, path=path)


def reject_retired_fields(raw: object, *, file: str, path: Path | str | None) -> None:
    """Raise :class:`RetiredPackFieldError` when *raw* carries a field retired from *file*.

    *raw* is the mapping as read from YAML; anything that is not a mapping is left
    to the model's own validation. *path* locates the message (the file kind
    *file* is used when it is ``None``).
    """
    if not isinstance(raw, Mapping):
        return
    data: Mapping[str, Any] = raw
    for retired in RETIRED_PACK_FIELDS:
        if retired.file == file and retired.field in data:
            raise RetiredPackFieldError(retired, path=path)


def retired_field_errors(exc: ValidationError) -> list[RetiredPackFieldError]:
    """Return the :class:`RetiredPackFieldError`\\ s pydantic wrapped into *exc*."""
    found: list[RetiredPackFieldError] = []
    for error in exc.errors():
        cause = (error.get("ctx") or {}).get("error")
        if isinstance(cause, RetiredPackFieldError):
            found.append(cause)
    return found
