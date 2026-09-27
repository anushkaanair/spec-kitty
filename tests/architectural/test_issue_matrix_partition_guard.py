"""Issue-matrix partition regression guard (FR-008 / NFR-001 / SC-005, WP05).

Mission ``issue-matrix-partition-integrity-01M3H10A`` (#5171, #4943) closed a
two-partition conflation: gating-reference discovery must read the PRIMARY
partition, while authored matrix verdicts must read the coordination partition
(or its retained branch-ref content post-consolidation). Both halves are
resolved by ONE shared helper,
:func:`mission_runtime.issue_matrix_partition.resolve_issue_matrix_partition`.

This gate keeps the class shut in every guarded consumer:

* the mission-review gate (``review/__init__.py``),
* the merge completeness + terminal-verdict gates (``policy/merge_gates.py``),
* the Gate-4 doctrine (``spec-kitty-mission-review/SKILL.md``).

Rules (count of violations must be 0 — NFR-001):

* **Python, raw path** — no ``<dir> / "issue-matrix.{json,md}"`` (or
  ``.joinpath``) unless ``<dir>`` is a matrix source already resolved by the
  helper; no string literal hand-reconstructing ``kitty-specs/.../issue-matrix``.
* **Python, discovery dir fed to the matrix read** — the issue-matrix readers
  are never handed ``feature_dir`` (the primary discovery dir).
* **Python, split bypass** — every guarded gate function calls the helper.
* **Doctrine** — no executable raw read (``cat``/``jq``/``head``/... of an
  ``issue-matrix`` file) in a fenced block, and an inline raw-read span only
  inside an explicit prohibition ("Do NOT ...").

Non-vacuity: every rule is re-run against a mutated copy of the real source
(:class:`TestSelfMutation`) and must trip. Fail-closed: a missing or
unreadable guarded file, or a guarded function that no longer exists, FAILs.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural, pytest.mark.fast]

REPO_ROOT = Path(__file__).resolve().parents[2]

HELPER_NAME = "resolve_issue_matrix_partition"

REVIEW_GATE = "src/specify_cli/cli/commands/review/__init__.py"
MERGE_GATES = "src/specify_cli/policy/merge_gates.py"
GATE4_DOCTRINE = "src/charter/offering/skills/spec-kitty-mission-review/SKILL.md"

# Guarded gate functions that must resolve the partition through the helper.
HELPER_CALLERS: dict[str, tuple[str, ...]] = {
    REVIEW_GATE: ("review_mission",),
    MERGE_GATES: (
        "_evaluate_issue_matrix_completeness_gate",
        "_evaluate_issue_matrix_verdict_terminality_gate",
    ),
}

# Local names that hold a helper-resolved matrix source (never the primary
# discovery dir). ``resolved_matrix_dir`` is ``matrix_dir`` from the helper,
# falling back to the primary dir only on the legacy path where no split exists.
RESOLVED_MATRIX_NAMES = frozenset({"resolved_matrix_dir", "matrix_dir", "coord_matrix_source"})

# Readers whose first argument is the matrix location.
MATRIX_READERS = frozenset({"load_issue_matrix", "issue_matrix_artifact_present", "validate_issue_matrix"})
DISCOVERY_DIR_NAMES = frozenset({"feature_dir", "primary_discovery_dir", "_primary_discovery_dir"})

_MATRIX_FILE_RE = re.compile(r"issue-matrix\.(?:json|md)")
_HAND_BUILT_PATH_RE = re.compile(r"kitty-specs/[^\s\"'`]*issue-matrix")
_RAW_READ_RE = re.compile(r"\b(?:cat|less|more|head|tail|jq|bat|yq|sed|awk|grep|open)\b[^`\n]*issue-matrix\.(?:json|md)")
_PROHIBITION_RE = re.compile(r"\b(?:do not|don't|never)\b", re.IGNORECASE)
_FENCE_RE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.detail}"


def _read_guarded(rel: str) -> str:
    """Read a guarded file; FAIL (never skip) if it is gone or unreadable."""
    path = REPO_ROOT / rel
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        pytest.fail(f"guarded issue-matrix consumer {rel} is missing/unreadable ({exc}); update this guard, do not skip it")


def _is_matrix_filename(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and bool(_MATRIX_FILE_RE.fullmatch(node.value))


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ast.unparse(node)


def _call_name(node: ast.Call) -> str:
    return _base_name(node.func)


def _raw_path_violations(rel: str, tree: ast.AST) -> list[Violation]:
    found: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and _is_matrix_filename(node.right):
            base = _base_name(node.left)
            if base not in RESOLVED_MATRIX_NAMES:
                found.append(Violation(rel, node.lineno, "raw-path", f"{ast.unparse(node)} joins the matrix file onto a non-resolved dir"))
        elif isinstance(node, ast.Call) and _call_name(node) == "joinpath" and any(_is_matrix_filename(a) for a in node.args):
            assert isinstance(node.func, ast.Attribute)
            if _base_name(node.func.value) not in RESOLVED_MATRIX_NAMES:
                found.append(Violation(rel, node.lineno, "raw-path", f"{ast.unparse(node)} joins the matrix file onto a non-resolved dir"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and _HAND_BUILT_PATH_RE.search(node.value):
            found.append(Violation(rel, node.lineno, "raw-path", f"string literal hand-builds an issue-matrix path: {node.value[:80]!r}"))
    return found


def _discovery_dir_read_violations(rel: str, tree: ast.AST) -> list[Violation]:
    found: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) in MATRIX_READERS and node.args:
            first = node.args[0]
            if isinstance(first, ast.Name) and first.id in DISCOVERY_DIR_NAMES:
                found.append(Violation(rel, node.lineno, "discovery-dir-read", f"{ast.unparse(node)} reads the matrix from the primary discovery dir"))
    return found


def _bypass_violations(rel: str, tree: ast.AST, functions: tuple[str, ...]) -> list[Violation]:
    defs = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    found: list[Violation] = []
    for name in functions:
        fn = defs.get(name)
        if fn is None:
            found.append(Violation(rel, 0, "bypass", f"guarded function {name}() not found — update HELPER_CALLERS, do not drop it"))
            continue
        if not any(isinstance(n, ast.Call) and _call_name(n) == HELPER_NAME for n in ast.walk(fn)):
            found.append(Violation(rel, fn.lineno, "bypass", f"{name}() does not resolve the partition via {HELPER_NAME}()"))
    return found


def scan_python(rel: str, source: str) -> list[Violation]:
    tree = ast.parse(source, filename=rel)
    return [
        *_raw_path_violations(rel, tree),
        *_discovery_dir_read_violations(rel, tree),
        *_bypass_violations(rel, tree, HELPER_CALLERS.get(rel, ())),
    ]


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_doctrine(rel: str, text: str) -> list[Violation]:
    found: list[Violation] = []
    fenced_spans: list[tuple[int, int]] = []
    for fence in _FENCE_RE.finditer(text):
        fenced_spans.append(fence.span())
        for hit in _RAW_READ_RE.finditer(fence.group(1)):
            found.append(Violation(rel, _line_of(text, fence.start(1) + hit.start()), "doctrine-raw-read", hit.group(0)))
    for lineno, line in enumerate(text.splitlines(), start=1):
        offset = sum(len(x) + 1 for x in text.splitlines()[: lineno - 1])
        if any(start <= offset < end for start, end in fenced_spans):
            continue
        for span in _INLINE_CODE_RE.finditer(line):
            if _RAW_READ_RE.search(span.group(1)) and not _PROHIBITION_RE.search(line[: span.start()]):
                found.append(Violation(rel, lineno, "doctrine-raw-read", span.group(1)))
    return found


def _gate4_section(text: str) -> str:
    match = re.search(r"^### Gate 4: Issue matrix.*?(?=^### )", text, re.MULTILINE | re.DOTALL)
    if match is None:
        pytest.fail(f"{GATE4_DOCTRINE}: '### Gate 4: Issue matrix' section not found — the guard would be vacuous")
    return match.group(0)


# --------------------------------------------------------------------------- #
# The guard on the real tree
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("rel", [REVIEW_GATE, MERGE_GATES])
def test_python_consumers_have_zero_raw_issue_matrix_reads(rel: str) -> None:
    violations = scan_python(rel, _read_guarded(rel))
    assert violations == [], "issue-matrix partition bypass (route through resolve_issue_matrix_partition):\n" + "\n".join(map(str, violations))


def test_gate4_doctrine_has_zero_raw_issue_matrix_reads() -> None:
    text = _read_guarded(GATE4_DOCTRINE)
    _gate4_section(text)  # fail-closed: the guarded section must exist
    violations = scan_doctrine(GATE4_DOCTRINE, text)
    assert violations == [], "Gate-4 doctrine reads the issue-matrix raw:\n" + "\n".join(map(str, violations))


def test_gate4_doctrine_routes_through_the_resolver() -> None:
    section = _gate4_section(_read_guarded(GATE4_DOCTRINE))
    assert "spec-kitty review" in section
    assert HELPER_NAME in section


# --------------------------------------------------------------------------- #
# Self-mutation: each rule must trip on an injected regression (non-vacuity)
# --------------------------------------------------------------------------- #

_INJECTED_RAW_PATH = '\n\ndef _injected(feature_dir):\n    return (feature_dir / "issue-matrix.json").read_text()\n'
_INJECTED_JOINPATH = '\n\ndef _injected(feature_dir):\n    return feature_dir.joinpath("issue-matrix.md").read_text()\n'
_INJECTED_LITERAL = '\n\n_INJECTED = "kitty-specs/demo/issue-matrix.json"\n'
_INJECTED_DISCOVERY_READ = "\n\ndef _injected(feature_dir):\n    return load_issue_matrix(feature_dir)\n"


class TestSelfMutation:
    @pytest.mark.parametrize("rel", [REVIEW_GATE, MERGE_GATES])
    @pytest.mark.parametrize(
        ("injection", "rule"),
        [
            (_INJECTED_RAW_PATH, "raw-path"),
            (_INJECTED_JOINPATH, "raw-path"),
            (_INJECTED_LITERAL, "raw-path"),
            (_INJECTED_DISCOVERY_READ, "discovery-dir-read"),
        ],
    )
    def test_injected_raw_read_trips(self, rel: str, injection: str, rule: str) -> None:
        source = _read_guarded(rel)
        assert not [v for v in scan_python(rel, source) if v.rule == rule]
        mutated = [v for v in scan_python(rel, source + injection) if v.rule == rule]
        assert mutated, f"{rule} did not trip on an injected regression in {rel}"

    @pytest.mark.parametrize("rel", [REVIEW_GATE, MERGE_GATES])
    def test_removed_helper_call_trips_bypass(self, rel: str) -> None:
        source = _read_guarded(rel)
        assert f"{HELPER_NAME}(" in source
        mutated = scan_python(rel, source.replace(f"{HELPER_NAME}(", "_bypassed_split("))
        tripped = {v.detail.split("(")[0] for v in mutated if v.rule == "bypass"}
        assert tripped == set(HELPER_CALLERS[rel])

    def test_renamed_guarded_function_fails_closed(self) -> None:
        source = _read_guarded(MERGE_GATES).replace("def _evaluate_issue_matrix_completeness_gate(", "def _renamed_gate(")
        assert any(v.rule == "bypass" and "not found" in v.detail for v in scan_python(MERGE_GATES, source))

    @pytest.mark.parametrize(
        "injection",
        [
            "\n```bash\ncat kitty-specs/<slug>/issue-matrix.json\n```\n",
            "\n```bash\njq '.rows' kitty-specs/<slug>/issue-matrix.json\n```\n",
            "\nRead the verdicts with `cat kitty-specs/<slug>/issue-matrix.json`.\n",
        ],
    )
    def test_injected_doctrine_raw_read_trips(self, injection: str) -> None:
        text = _read_guarded(GATE4_DOCTRINE)
        assert scan_doctrine(GATE4_DOCTRINE, text) == []
        assert scan_doctrine(GATE4_DOCTRINE, text + injection), "doctrine raw-read rule did not trip"

    def test_prohibition_span_is_not_a_violation(self) -> None:
        # Pins the one carve-out so it cannot silently widen: an explicit
        # "Do NOT" ahead of the span is allowed, the same span without it is not.
        assert scan_doctrine("x.md", "Do NOT `cat kitty-specs/s/issue-matrix.json` directly.\n") == []
        assert scan_doctrine("x.md", "Then `cat kitty-specs/s/issue-matrix.json` directly.\n")

    def test_missing_gate4_section_fails_closed(self) -> None:
        with pytest.raises(pytest.fail.Exception):
            _gate4_section("# no gate here\n")

    def test_missing_guarded_file_fails_closed(self) -> None:
        with pytest.raises(pytest.fail.Exception):
            _read_guarded("src/does/not/exist.py")
