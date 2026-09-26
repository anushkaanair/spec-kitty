"""Kernel domain-agnostic sibling-path-resolution gate (FR-004, SC-002, NFR-002).

The documented dependency direction is::

    kernel (root) <- charter <- glossary/runtime/mission_runtime <- specify_cli

so no module under ``src/kernel/`` may hold a string identifying ``charter``,
``specify_cli``, or any mission-type name -- kernel must not know the
vocabulary of the layers above it.

Note (charter-code-topology-01M152G1, S5): the former ``src/doctrine``
package relocated to ``src/charter/offering`` (S2a), collapsing the
landscape chain from ``kernel <- doctrine <- charter <- ...`` to
``kernel <- charter <- ...``. This gate's forbidden vocabulary tracks that
collapse -- it now names ``"charter"`` (the layer that actually sits above
kernel today) rather than the retired ``"doctrine"`` name, so a real
``import charter`` / ``files("charter...")`` edge cannot slip through
vacuously just because the package was renamed.

Why this gate exists, given ``test_layer_rules.py`` already owns a pytestarch
``LayerRule`` for the same direction (``TestKernelIsolation.test_kernel_does_not_import_charter``):
**that rule is vacuous against the violation this gate targets.** pytestarch's
``LayerRule`` resolves *import edges* — it cannot see a string-literal
``importlib.resources.files("charter...")`` call, which is exactly the shape
``kernel.paths.get_package_asset_root()`` used before FR-004 (mission
``doctrine-consumer-surface-missions-extraction-01KZ6G6H``, back when the
package was still named ``doctrine``). Likewise
``test_charter_no_specify_cli_import.py`` (scoped to ``src/charter/``) and
``test_doctrine_wheel_closure.py`` (scoped to ``pyproject.toml`` manifest
declarations) do not cover a kernel-string-literal edge either (NFR-002) — a
gate that cannot fail on the one real violation it is nominally guarding is
worse than no gate, since it manufactures false confidence.

This module therefore mirrors ``collect_specify_cli_imports`` from
``test_charter_no_specify_cli_import.py``: it walks the **full AST**
(``ast.walk``), so an in-function, in-``try``, or f-string-embedded
occurrence is caught, not merely a module-level ``import`` statement.

Scope of the claim this gate proves (read this before citing it): it proves
zero occurrences of the literal strings ``"charter"``, ``"specify_cli"``, or
a mission-type name, in *code* positions (import statements, call arguments,
and f-string components) anywhere under ``src/kernel/``. Docstrings and
comments are explicitly out of scope -- ``ast`` does not expose comments at
all, and a docstring is excluded by position (the first statement of a
module/class/function body) rather than by content, so prose explaining the
boundary (e.g. "kernel/ must not import specify_cli") is never flagged. This
gate does not prove the absence of runtime coupling by other indirection
(``__import__``, environment-variable-supplied strings, etc.) -- those are
out of scope here by construction, same as the charter gate this mirrors.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple

import pytest

from tests.architectural._content_identity import with_blank_line_at_top, with_probe_above_statement
from tests.architectural._ratchet_keys import composite_key

pytestmark = pytest.mark.architectural

_SRC = Path(__file__).resolve().parents[2] / "src"
_KERNEL_ROOT = _SRC / "kernel"

#: The exact forbidden literals (SC-002 / the mission's kernel-resolution-
#: primitive.md contract): the two upward-layer package names, plus the four
#: mission-type identifiers kernel.paths used to hard-code.
#:
#: ``"doctrine"`` was replaced by ``"charter"`` (charter-code-topology-01M152G1,
#: S5): the former ``src/doctrine`` package relocated to
#: ``src/charter/offering`` (S2a), collapsing the landscape chain to
#: ``kernel <- charter <- ...``. The forbidden vocabulary must name the layer
#: that now actually sits above kernel -- ``doctrine`` no longer exists as a
#: top-level package, so keeping it here would let a real
#: ``import charter`` / ``files("charter...")`` edge slip through vacuously.
_FORBIDDEN_STRINGS = frozenset(
    {
        "charter",
        "specify_cli",
        "software-dev",
        "documentation",
        "research",
        "plan",
    }
)

#: Import-statement module roots that are always forbidden regardless of the
#: exact-string check above (``import charter.x`` never has a bare
#: ``"charter"`` string node, but is exactly as much of a violation).
_FORBIDDEN_IMPORT_ROOTS = frozenset({"charter", "specify_cli"})

#: Pre-existing violations this gate discovers but that are OUT OF SCOPE for
#: FR-004 (mission doctrine-consumer-surface-missions-extraction-01KZ6G6H,
#: WP04 -- owned_files: src/kernel/paths.py, and the (since-relocated)
#: doctrine pack-paths / missions-repository modules, now
#: src/charter/offering/pack_paths.py, src/charter/offering/missions/repository.py).
#: ``schema_utils.py`` was promoted to kernel by an unrelated, already-merged
#: mission (charter-mediated-doctrine-selection-01KRTZCA, WP07); its
#: ``_resolve_schema_path`` helper names "charter" at BOTH exempted sites
#: below -- this gate's segment-aware ``ast.Constant`` matcher (``value ==
#: root or value.startswith(root + ".")``) catches both:
#:
#: * line 88 -- ``files("charter.offering.schemas")``, the installed-wheel resource
#:   lookup. A dotted-module-path string literal (the string-literal
#:   equivalent of ``import charter.offering.schemas``) -- exactly the shape an
#:   exact-equality match cannot see, since ``"charter.offering.schemas" !=
#:   "charter"``.
#: * line 97 -- the dev-checkout fallback path segment
#:   (``Path(__file__).resolve().parent.parent / "charter" / "offering" / "schemas"``),
#:   an exact ``"charter"`` literal on the first path segment.
#:
#: Retargeted (charter-code-topology-01M152G1, S5) from the pre-S2a lines
#: (88, 96) that named the retired ``"doctrine"`` literal: the S2a relocation
#: (``src/doctrine`` -> ``src/charter/offering``) rewrote both sites in place,
#: which shifted the dev-checkout fallback onto line 97 (three chained path
#: segments -- ``"charter"``, ``"offering"``, ``"schemas"`` -- instead of the
#: original two) and changed the resource string from ``"charter.offering.schemas"``
#: to ``"charter.offering.schemas"``. Both sites are still the SAME real,
#: disclosed, pre-existing coupling: a kernel schema-loading utility loads
#: charter-owned schema files, and full decoupling (relocating the schemas
#: themselves out of ``charter``, or injecting the resolved root from a
#: caller above kernel) is a deferred design decision -- NOT resolved by this
#: gate. Exempted here (not silently fixed, not hidden by weakening the gate)
#: so the gate stays non-vacuous for *new* violations. Full decoupling is
#: tracked as Follow-up: #3206 (retire these two exemptions once the schemas
#: are relocated or the root is injected); do not widen this set for any file
#: this WP or a future one actually owns.
_PRE_EXISTING_EXEMPTIONS = frozenset(
    {
        ("kernel/schema_utils.py", 88),
        ("kernel/schema_utils.py", 97),
    }
)


def _matches_forbidden_vocabulary(value: str) -> bool:
    """True if ``value`` IS a forbidden root, or dot-segments into one.

    Segment/prefix-aware: catches both an exact forbidden literal
    (``"doctrine"``) and a dotted-module-path literal rooted in one
    (``"charter.offering.schemas"``) -- the string-literal shape
    ``importlib.resources.files("charter.offering.schemas")`` uses, which is the
    literal-string equivalent of ``import charter.offering.schemas`` already caught
    by the ``ast.Import``/``ast.ImportFrom`` branches below via
    ``_module_root``. A bare exact-equality check (``value in
    _FORBIDDEN_STRINGS``) misses this dotted form entirely -- exactly the
    escape this gate exists to close (see ``src/kernel/schema_utils.py:88``).
    """
    return any(value == root or value.startswith(f"{root}.") for root in _FORBIDDEN_STRINGS)


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Return ``id()`` of every AST node that is a docstring (excluded from the scan).

    A docstring is the first statement of a Module/ClassDef/FunctionDef/
    AsyncFunctionDef body, expressed as ``ast.Expr(value=ast.Constant(str))``.
    ``ast`` does not expose comments at all, so only docstrings need explicit
    exclusion here.
    """
    docstring_ids: set[int] = set()
    scopes = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if not isinstance(node, scopes):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            docstring_ids.add(id(first.value))
    return docstring_ids


def _module_root(name: str) -> str:
    return name.split(".", 1)[0]


def _scan_source(source: str, rel: str) -> list[tuple[str, int, str]]:
    """Return ``(rel, lineno, detail)`` violations found in one module's *source*."""
    found: list[tuple[str, int, str]] = []
    tree = ast.parse(source)
    docstring_ids = _docstring_nodes(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _module_root(alias.name) in _FORBIDDEN_IMPORT_ROOTS:
                    found.append((rel, node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.module and _module_root(node.module) in _FORBIDDEN_IMPORT_ROOTS:
                found.append((rel, node.lineno, f"from {node.module} import ..."))
        elif isinstance(node, ast.Constant):
            if id(node) in docstring_ids:
                continue
            if isinstance(node.value, str) and _matches_forbidden_vocabulary(node.value):
                found.append((rel, node.lineno, f"string literal {node.value!r}"))
    return found


def _scan_file(path: Path, relative_to: Path) -> list[tuple[str, int, str]]:
    """Return ``(relative_path, lineno, detail)`` violations found in a single file."""
    return _scan_source(path.read_text(encoding="utf-8"), str(path.relative_to(relative_to)))


def collect_forbidden_vocabulary(root: Path, *, relative_to: Path | None = None) -> list[tuple[str, int, str]]:
    """Return ``(relative_path, lineno, detail)`` for every violation under ``root``.

    Walks the full AST (``ast.walk``) so lazy in-function imports and
    call-argument/f-string string literals are all caught, excluding
    docstring positions. ``relative_path`` is relative to ``relative_to``
    (default: ``src/``), so this stays usable against a synthetic
    ``tmp_path`` tree in the non-vacuity tests below.
    """
    anchor = relative_to if relative_to is not None else _SRC
    found: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        found.extend(_scan_file(path, anchor))
    return found


def test_kernel_holds_no_doctrine_or_specify_cli_vocabulary() -> None:
    """FR-004 / SC-002: no ``src/kernel/**`` module names doctrine/specify_cli/mission-types.

    This is the FR-004 / SC-002 / NFR-002 gate. It fails on module-level
    imports, in-function imports, and any exact string literal (including as
    a call argument or f-string component) matching the forbidden vocabulary.
    See ``test_walker_catches_in_function_call_argument`` for the committed
    proof that the string-literal leg is real (mirrors the charter gate's own
    NFR-004-style self-mutation discipline).

    ``_PRE_EXISTING_EXEMPTIONS`` filters out exactly one already-tracked,
    out-of-scope pre-existing site (see its own docstring) -- any *other*
    violation, including a new one at a different line of the same file,
    still reds this gate.
    """
    violations = [(rel, lineno, detail) for rel, lineno, detail in collect_forbidden_vocabulary(_KERNEL_ROOT) if (rel, lineno) not in _PRE_EXISTING_EXEMPTIONS]

    assert violations == [], (
        "src/kernel/** must hold no doctrine-/specify_cli-identifying string or "
        "mission-type vocabulary, at any scope (kernel is the root layer; "
        "FR-004, SC-002, NFR-002).\nResolve via the domain-agnostic "
        "kernel.sibling_paths.resolve_installed_sibling primitive instead, "
        "with the caller supplying its own __file__ and sibling-relative "
        "path.\nViolations:\n" + "\n".join(f"  {rel}:{lineno} — {detail}" for rel, lineno, detail in violations)
    )


def test_pre_existing_exemption_is_still_a_real_violation() -> None:
    """Anti-vacuity for the exemption itself: it must exempt a REAL finding.

    Guards against ``_PRE_EXISTING_EXEMPTIONS`` silently becoming a no-op
    (e.g. if the exempted line ever moves or the violation is fixed) without
    anyone noticing -- if that happens, this test fails as a prompt to shrink
    the exemption set, not the other way around.
    """
    unfiltered = collect_forbidden_vocabulary(_KERNEL_ROOT)
    exempted_sites = {(rel, lineno) for rel, lineno, _detail in unfiltered}

    assert exempted_sites >= _PRE_EXISTING_EXEMPTIONS, (
        "Every entry in _PRE_EXISTING_EXEMPTIONS must correspond to an actual "
        "violation collect_forbidden_vocabulary() finds today; shrink the "
        "exemption set instead of leaving a stale, vacuous entry."
    )


def test_walker_catches_in_function_call_argument(tmp_path: Path) -> None:
    """Non-vacuity (NFR-002/NFR-004): a call-argument string literal IS detected.

    Reproduces the exact shape ``kernel.paths.get_package_asset_root()`` used
    before FR-004 -- ``importlib.resources.files("charter")`` nested inside a
    function -- and asserts the walker flags it. Were the walker downgraded to
    a module-body-only or import-only scan (what the pre-existing pytestarch
    ``LayerRule`` effectively does), this test goes red, proving that rule's
    vacuity against this exact shape.
    """
    module = tmp_path / "paths.py"
    module.write_text(
        'import importlib.resources\n\n\ndef get_package_asset_root():\n    resource = importlib.resources.files("charter") / "missions"\n    return resource\n',
        encoding="utf-8",
    )

    violations = collect_forbidden_vocabulary(tmp_path, relative_to=tmp_path)

    assert violations == [("paths.py", 5, "string literal 'charter'")]


def test_walker_ignores_docstrings_and_prose(tmp_path: Path) -> None:
    """No false positives: docstrings/comments explaining the boundary are prose.

    Mirrors the mission's own trap #3 -- ``src/kernel/paths.py`` legitimately
    mentions "charter" and "specify_cli" in docstrings/comments explaining
    the layering rule (e.g. "kernel/ must not import specify_cli"); those are
    explanatory prose, not code, and must never be flagged.
    """
    (tmp_path / "clean.py").write_text(
        '"""This module about charter and specify_cli lives in kernel.\n\n'
        "kernel/ must not import specify_cli (architectural layer rule).\n"
        '"""\n'
        "from __future__ import annotations\n"
        "\n"
        "# import charter  <- a comment, not an import\n"
        "# Mirrors specify_cli.paths.render_runtime_path with identical semantics.\n"
        "\n"
        "\n"
        "def helper() -> None:\n"
        '    """Also mentions charter and specify_cli, but is a docstring."""\n'
        "    return None\n",
        encoding="utf-8",
    )

    assert collect_forbidden_vocabulary(tmp_path, relative_to=tmp_path) == []


# ---------------------------------------------------------------------------
# Line-drift tolerance (NFR-001): the exemptions must survive line drift
# ---------------------------------------------------------------------------


class _KernelFinding(NamedTuple):
    """One kernel vocabulary finding: its content identity plus its current line."""

    key: tuple[str, str, str]
    lineno: int
    detail: str


def _kernel_sources() -> dict[str, str]:
    """``{src-relative path: source}`` for every module under ``src/kernel/``."""
    return {str(path.relative_to(_SRC)): path.read_text(encoding="utf-8") for path in sorted(_KERNEL_ROOT.rglob("*.py")) if "__pycache__" not in path.parts}


def _kernel_findings(sources: Mapping[str, str]) -> list[_KernelFinding]:
    """Every vocabulary finding in *sources*, keyed by ``(rel, qualname, token_line)``."""
    findings: list[_KernelFinding] = []
    for rel, source in sorted(sources.items()):
        for _rel, lineno, detail in _scan_source(source, rel):
            findings.append(_KernelFinding((rel, *composite_key(source, lineno)), lineno, detail))
    return findings


def _split_kernel_findings(sources: Mapping[str, str]) -> tuple[list[_KernelFinding], list[_KernelFinding]]:
    """Split the findings in *sources* into ``(unexpected, suppressed)``."""
    unexpected: list[_KernelFinding] = []
    suppressed: list[_KernelFinding] = []
    for finding in _kernel_findings(sources):
        target = suppressed if (finding.key[0], finding.lineno) in _PRE_EXISTING_EXEMPTIONS else unexpected
        target.append(finding)
    return unexpected, suppressed


def _kernel_partition(sources: Mapping[str, str]) -> tuple[Counter[tuple[tuple[str, str, str], str]], Counter[tuple[tuple[str, str, str], str]]]:
    """The gate's detection path as content identities (line numbers dropped)."""
    unexpected, suppressed = _split_kernel_findings(sources)
    return Counter((f.key, f.detail) for f in unexpected), Counter((f.key, f.detail) for f in suppressed)


#: The distinct files the kernel exemptions name -- the drift test's parameters.
_DRIFT_FILES: tuple[str, ...] = tuple(sorted({rel for rel, _lineno in _PRE_EXISTING_EXEMPTIONS}))

#: Floor on ``_DRIFT_FILES`` so the drift proof cannot pass over a shrunken set.
_DRIFT_FILES_FLOOR = 1


def _exemption_count_for(rel: str) -> int:
    return sum(1 for exempt_rel, _lineno in _PRE_EXISTING_EXEMPTIONS if exempt_rel == rel)


def _count_for(identities: Counter[tuple[tuple[str, str, str], str]], rel: str) -> int:
    return sum(count for (key, _detail), count in identities.items() if key[0] == rel)


def _probe_every_site(source: str, linenos: list[int]) -> str:
    """Insert a drift probe above each site's statement, bottom-up so lines stay valid."""
    for lineno in sorted(set(linenos), reverse=True):
        source = with_probe_above_statement(source, lineno)
    return source


def test_kernel_drift_files_meet_floor() -> None:
    """NFR-002: the drift parameter set is non-trivial and every file in it is live."""
    assert len(_DRIFT_FILES) >= _DRIFT_FILES_FLOOR
    _, suppressed = _kernel_partition(_kernel_sources())
    empty = [rel for rel in _DRIFT_FILES if _count_for(suppressed, rel) < 1]
    assert not empty, f"Drift files with no suppressed finding on the unmutated tree: {empty}"


@pytest.mark.parametrize("rel", _DRIFT_FILES)
def test_kernel_exemptions_survive_line_drift(rel: str) -> None:
    """NFR-001: line drift above or around the exempted sites changes nothing the gate sees.

    Two mutations of *rel*, each rescanned: (i) a blank line at the top of the
    file, (ii) a ``# drift-probe`` / ``pass`` pair above every exempted site's
    statement. The ``(unexpected, suppressed)`` identities must be unchanged
    and the per-file suppressed count must equal the per-file exemption count.
    """
    sources = _kernel_sources()
    baseline = _kernel_partition(sources)
    expected = _exemption_count_for(rel)
    assert _count_for(baseline[1], rel) == expected, f"{rel}: {_count_for(baseline[1], rel)} suppressed finding(s) unmutated, expected {expected}"

    site_lines = [f.lineno for f in _split_kernel_findings(sources)[1] if f.key[0] == rel]
    mutations = {
        "blank line at top": with_blank_line_at_top(sources[rel]),
        "probe above each site": _probe_every_site(sources[rel], site_lines),
    }
    for label, mutated_source in mutations.items():
        mutated = dict(sources)
        mutated[rel] = mutated_source
        drifted = _kernel_partition(mutated)
        assert drifted == baseline, f"{rel} ({label}): drift changed the gate's partition.\nbefore: {baseline}\nafter:  {drifted}"
        assert _count_for(drifted[1], rel) == expected
