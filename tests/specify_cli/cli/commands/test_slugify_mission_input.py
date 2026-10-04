"""Seam units for ``lifecycle._slugify_feature_input`` (#4720, #5619).

``spec-kitty specify <name>`` derives the mission slug (a storage-facing
identifier: directory, branch and lane names) from free-form operator input.
Per the charter's Identifier Safety Rules the produced slug must be ASCII-only
and deterministic, and non-ASCII input must be rejected explicitly via
``NonAsciiNameError`` -- never silently stripped or truncated (the pre-#4720
behaviour turned ``Ünïcödé`` into ``n-c-d`` and ``auth日本`` into ``auth``).

These units pin the slug rules directly; ``test_specify_json_nonascii.py``
keeps one ``--json`` end-to-end smoke for the envelope contract.
"""

from __future__ import annotations

import pytest

from specify_cli.cli.commands.lifecycle import NonAsciiNameError, _slugify_feature_input

pytestmark = [pytest.mark.unit, pytest.mark.fast]

_ALL_NON_LATIN = "日本語"
_ACCENTED_LATIN = "Ünïcödé"
_MIXED_ASCII_NON_LATIN = "auth日本"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Auth Refactor", "auth-refactor"),
        ("user-authentication", "user-authentication"),
        ("  Padded  Name  ", "padded-name"),
        ("snake_case and CamelCase", "snake-case-and-camelcase"),
        ("v2.0 release!!", "v2-0-release"),
        ("---edge---", "edge"),
        ("already-9-digits", "already-9-digits"),
    ],
)
def test_ascii_input_is_normalised_to_kebab_case(raw: str, expected: str) -> None:
    slug = _slugify_feature_input(raw)

    assert slug == expected
    assert slug.isascii()


def test_slug_is_deterministic() -> None:
    assert _slugify_feature_input("Auth Refactor") == _slugify_feature_input("Auth Refactor")


@pytest.mark.parametrize(
    "raw",
    [_ALL_NON_LATIN, _ACCENTED_LATIN, _MIXED_ASCII_NON_LATIN],
    ids=["all-non-latin", "accented-latin", "mixed-ascii-non-latin"],
)
def test_non_ascii_input_is_rejected_and_named(raw: str) -> None:
    with pytest.raises(NonAsciiNameError) as excinfo:
        _slugify_feature_input(raw)

    assert "no usable ASCII characters" in str(excinfo.value)
    assert raw in str(excinfo.value)


def test_accented_latin_is_never_silently_mangled() -> None:
    """Pre-#4720 ``Ünïcödé`` was silently accepted as ``n-c-d``."""
    with pytest.raises(NonAsciiNameError):
        _slugify_feature_input(_ACCENTED_LATIN)


def test_mixed_input_never_silently_truncates_to_ascii_prefix() -> None:
    """Pre-#4720 ``auth日本`` was silently accepted as ``auth``."""
    with pytest.raises(NonAsciiNameError):
        _slugify_feature_input(_MIXED_ASCII_NON_LATIN)


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"], ids=["empty", "spaces", "whitespace-control"])
def test_empty_or_whitespace_input_says_no_name_given(raw: str) -> None:
    with pytest.raises(NonAsciiNameError) as excinfo:
        _slugify_feature_input(raw)

    assert "no name given" in str(excinfo.value)


@pytest.mark.parametrize("raw", ["!!!", "---", "***"])
def test_ascii_input_with_no_alphanumerics_is_rejected_as_unusable(raw: str) -> None:
    with pytest.raises(NonAsciiNameError) as excinfo:
        _slugify_feature_input(raw)

    assert "no usable ASCII characters" in str(excinfo.value)
    assert "no name given" not in str(excinfo.value)
