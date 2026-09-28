"""Static model of the Makefile's ``FAST_TIER_MARKERS`` vocabulary (spec-kitty#21).

``make test-fast`` selects tests under ``FAST_TIER_DIRS`` by the Makefile's
``FAST_TIER_MARKERS`` expression: ``(fast or unit) and not slow and not e2e
and not integration and not regression and not distribution and not
live_adapter and not stress and not windows_ci and not platform_darwin`` --
a *positive* selection on ``{fast, unit}``. A test placed under one of those
roots that carries NONE of the vocabulary names this expression references is
silently deselected, not loudly skipped: it never runs in the
implementer/CI fast-tier baseline and nothing says so (controller-qa audit of
PR #15, spec-kitty#21).

This module parses the Makefile -- the single source of truth for both
values, never hand-copied here -- into the ``FAST_TIER_DIRS`` root list and
the marker vocabulary ``FAST_TIER_MARKERS`` references, so the completeness
test in ``test_fast_tier_marker_completeness.py`` can assert every collected
test under those roots carries at least one vocabulary marker.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.architectural._gate_coverage import marker_names as _marker_names

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE_PATH = REPO_ROOT / "Makefile"

_DIRS_RE = re.compile(r"^FAST_TIER_DIRS\s*:=\s*(?P<value>.+)$", re.MULTILINE)
_MARKERS_RE = re.compile(r"^FAST_TIER_MARKERS\s*=\s*(?P<value>.+)$", re.MULTILINE)


def fast_tier_dirs(makefile_path: Path | None = None) -> tuple[str, ...]:
    """The ``FAST_TIER_DIRS`` roots, read from the Makefile."""
    text = (makefile_path or MAKEFILE_PATH).read_text(encoding="utf-8")
    match = _DIRS_RE.search(text)
    if not match:
        raise RuntimeError("Makefile has no `FAST_TIER_DIRS := ...` line to parse")
    return tuple(match.group("value").split())


def fast_tier_markers_expr(makefile_path: Path | None = None) -> str:
    """The raw ``FAST_TIER_MARKERS`` expression string, read from the Makefile."""
    text = (makefile_path or MAKEFILE_PATH).read_text(encoding="utf-8")
    match = _MARKERS_RE.search(text)
    if not match:
        raise RuntimeError("Makefile has no `FAST_TIER_MARKERS = ...` line to parse")
    return match.group("value").strip()


def fast_tier_marker_vocabulary(makefile_path: Path | None = None) -> frozenset[str]:
    """Every marker name ``FAST_TIER_MARKERS`` references, positive or negated.

    Delegates to the shared, canonical ``_gate_coverage.marker_names`` walker
    (landing pass #5244, LAND-PAT-004) -- previously a near-identical local
    copy (``_collect_names``) lived here; promoting it closes the
    copy-drift hazard between this module and
    ``test_interpreter_shard_coverage.py``'s own (now-removed) marker-name
    walker. Sign-blind: a test opted OUT of the fast tier by carrying
    ``slow`` is exactly as *explicitly marked* as one opted IN by carrying
    ``fast`` -- only a test with ZERO of these names is the silent drop this
    module exists to catch.
    """
    expr = fast_tier_markers_expr(makefile_path)
    return _marker_names(expr)
