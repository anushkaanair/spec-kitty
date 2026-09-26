"""Board-authority acceptance tests for ``runtime_bridge`` (#4980 / #4975).

Holds the P0 board-authority parity tests (review-reject re-dispatch, coord
implement dispatch, the blocked floor, snapshot immutability and the
single-authority negative guard) plus the two composed-guard fail-closed
direct-call tests. They drive the REAL engine against real on-disk mission
scaffolds (``tests/runtime/_next_mission_scaffold.py``) and never touch the
#2531 two-run parity oracle (``tests/runtime/test_bridge_parity.py`` /
``tests/runtime/_bridge_oracle.py``), so the oracle stays retirable in
isolation (#5116) and these tests never pay for its module-scoped
``ledger_results`` fixture.

The guard tests at the top of this module keep that independence
non-fakeable: they scan this module and the scaffold for any oracle import or
wide-scoped fixture, pin the expected test-function names, and confirm via
``pytest --setup-plan`` that ``ledger_results`` is never set up.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.git_repo]


# ---------------------------------------------------------------------------
# Oracle-independence guard (FR-017 / NFR-002 / US3-AS3)
# ---------------------------------------------------------------------------

_THIS_MODULE = Path(__file__).resolve()
_SCAFFOLD_MODULE = _THIS_MODULE.parent / "_next_mission_scaffold.py"
_REPO_ROOT = _THIS_MODULE.parents[2]

_ORACLE_MODULES: frozenset[str] = frozenset({"tests.runtime._bridge_oracle", "tests.runtime.test_bridge_parity"})
_ORACLE_SUBMODULE_NAMES: frozenset[str] = frozenset({"_bridge_oracle", "test_bridge_parity"})
_WIDE_FIXTURE_SCOPES: frozenset[str] = frozenset({"module", "package", "session"})
_ORACLE_FIXTURE_NAME = "ledger_results"

_GUARD_TESTS: frozenset[str] = frozenset(
    {
        "test_board_authority_module_does_not_import_the_oracle",
        "test_oracle_coupling_scan_flags_planted_imports",
        "test_board_authority_tests_never_set_up_the_oracle_fixture",
    }
)

# Hard-coded from the planning-base capture of tests/runtime/test_bridge_parity.py
# (3717c7ea): the 13 P0 board-authority functions + the 2 fail-closed
# direct-call functions. A name set, not a count, so dropping a moved test
# cannot be masked by the guard tests themselves.
_EXPECTED_BOARD_AUTHORITY_TESTS: frozenset[str] = frozenset(
    {
        "test_research_fail_closed_default_direct_call",
        "test_documentation_fail_closed_default_direct_call",
        "test_review_reject_redispatches_implement_single_branch",
        "test_coord_implement_dispatch_reaches_wp01",
        "test_review_reject_redispatches_implement_coord_family",
        "test_lanes_with_coord_implement_dispatch",
        "test_approve_control_unchanged",
        "test_early_reject_redispatches_implement",
        "test_multi_wp_dependency_order_reject_redispatch",
        "test_blocked_floor_all_in_review_has_named_recovery",
        "test_blocked_floor_no_actionable_wp_has_named_recovery",
        "test_blocked_floor_dependency_walled_has_named_recovery",
        "test_unmaterialized_coord_surfaces_typed_blocked_reason",
        "test_snapshot_byte_identical_across_redispatch",
        "test_no_advancing_path_emits_unauthorized_step",
    }
)
# 15 functions; ``test_review_reject_redispatches_implement_coord_family`` is
# parametrized x2, giving 16 collected nodes.
_EXPECTED_BOARD_AUTHORITY_NODES = 16


def _is_oracle_module(module: str) -> bool:
    return module in _ORACLE_MODULES


def _import_offenders(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [f"line {node.lineno}: import {alias.name}" for alias in node.names if _is_oracle_module(alias.name)]
    module = node.module or ""
    if _is_oracle_module(module):
        return [f"line {node.lineno}: from {module} import ..."]
    if module == "tests.runtime":
        return [f"line {node.lineno}: from tests.runtime import {alias.name}" for alias in node.names if alias.name in _ORACLE_SUBMODULE_NAMES]
    return []


def _fixture_scope(decorator: ast.expr) -> str | None:
    """Return the literal ``scope=`` of a ``pytest.fixture(...)`` decorator, if any."""
    if not isinstance(decorator, ast.Call):
        return None
    func = decorator.func
    is_fixture = (isinstance(func, ast.Attribute) and func.attr == "fixture") or (isinstance(func, ast.Name) and func.id == "fixture")
    if not is_fixture:
        return None
    for keyword in decorator.keywords:
        if keyword.arg == "scope" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
    return None


def _wide_fixture_offenders(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    offenders: list[str] = []
    for decorator in node.decorator_list:
        scope = _fixture_scope(decorator)
        if scope in _WIDE_FIXTURE_SCOPES:
            offenders.append(f"line {node.lineno}: {scope}-scoped fixture {node.name}")
    return offenders


def _oracle_coupling_offenders(source: str) -> list[str]:
    """Flag every coupling to the parity oracle in ``source``.

    Flags any ``import`` / ``from`` of ``tests.runtime._bridge_oracle`` or
    ``tests.runtime.test_bridge_parity`` (at any nesting depth, including
    function-local imports) and any fixture declared with
    ``scope="module"`` / ``"package"`` / ``"session"`` (the oracle's
    ``ledger_results`` shape).
    """
    offenders: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import | ast.ImportFrom):
            offenders.extend(_import_offenders(node))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            offenders.extend(_wide_fixture_offenders(node))
    return offenders


def _top_level_test_names(source: str) -> set[str]:
    return {node.name for node in ast.parse(source).body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test_")}


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def test_board_authority_module_does_not_import_the_oracle() -> None:
    """The board-authority tests and their scaffold never couple to the oracle,
    and every expected board-authority test function lives here (by name)."""
    module_source = _THIS_MODULE.read_text(encoding="utf-8")
    scaffold_source = _read_optional(_SCAFFOLD_MODULE)

    assert _oracle_coupling_offenders(module_source) == []
    assert _oracle_coupling_offenders(scaffold_source) == []

    moved = _top_level_test_names(module_source) - _GUARD_TESTS
    missing = sorted(_EXPECTED_BOARD_AUTHORITY_TESTS - moved)
    unexpected = sorted(moved - _EXPECTED_BOARD_AUTHORITY_TESTS)
    assert not missing, f"expected board-authority tests missing from this module: {missing}"
    assert not unexpected, f"unexpected non-guard tests in this module: {unexpected}"


def test_oracle_coupling_scan_flags_planted_imports() -> None:
    """Self-mutation: the same scanner the guard uses flags each planted coupling."""
    planted = {
        "from-oracle": "from tests.runtime._bridge_oracle import canonical\n",
        "import-parity": "import tests.runtime.test_bridge_parity\n",
        "from-package": "from tests.runtime import _bridge_oracle\n",
        "local-import": "def f() -> None:\n    from tests.runtime.test_bridge_parity import ledger_results\n",
        "module-fixture": ("import pytest\n\n\n@pytest.fixture(scope='module')\ndef heavy() -> int:\n    return 1\n"),
        "session-fixture": ("from pytest import fixture\n\n\n@fixture(scope='session')\ndef heavy() -> int:\n    return 1\n"),
    }
    for label, source in planted.items():
        assert _oracle_coupling_offenders(source), f"planted coupling not flagged: {label}"

    clean = "import pytest\nfrom tests.runtime._next_mission_scaffold import scaffold_software_dev\n\n\n@pytest.fixture\ndef light() -> int:\n    return 1\n"
    assert _oracle_coupling_offenders(clean) == []


_PLANNED_NODE_RE = re.compile(r"::(test_\w+)(\[[^\]]*\])?")


def test_board_authority_tests_never_set_up_the_oracle_fixture() -> None:
    """US3-AS3: ``--setup-plan`` (executes nothing) never plans ``ledger_results``
    for this module, and plans every moved board-authority node."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--setup-plan",
            "-q",
            "-p",
            "no:cacheprovider",
            str(_THIS_MODULE.relative_to(_REPO_ROOT)),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output

    assert _ORACLE_FIXTURE_NAME not in output
    planned = {
        match.group(1) + (match.group(2) or "") for line in output.splitlines() if (match := _PLANNED_NODE_RE.search(line)) and match.group(1) not in _GUARD_TESTS
    }
    assert len(planned) >= _EXPECTED_BOARD_AUTHORITY_NODES, f"expected >= {_EXPECTED_BOARD_AUTHORITY_NODES} board-authority nodes planned, got {sorted(planned)}"
