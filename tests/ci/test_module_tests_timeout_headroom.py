"""Pin the per-PR ``module-tests.yml`` shard cap against its own measured-max comment.

The per-PR twin of ``tests/ci/test_nightly_timeout_headroom.py`` (#5378). Charter
shard 1 of PR #5383 was cancelled at the 40-minute cap of the reusable
``module-tests.yml`` shard job with no test failure. The workflow is the single
authority for the cap, so its one job records the measured maximum suite
wall-clock in a structured comment directly above ``timeout-minutes``::

    # headroom (#5378): max-suite>=38:03 runs=... formula=ceil((max+0:30)*1.5)

This test parses ONLY the workflow text and asserts the cap is at least
``ceil((max_suite_minutes + 0.5) * 1.5)``. No durations are committed here.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.fast]

_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "module-tests.yml"

_JOB_KEY_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$", re.MULTILINE)
# Job-level key only (4-space indent): a step-level `timeout-minutes` must never
# be read as the job cap.
_TIMEOUT_RE = re.compile(r"^    timeout-minutes:\s*(\d+)\s*$", re.MULTILINE)
_HEADROOM_RE = re.compile(r"#\s*headroom \(#5378\):\s*max-suite(>=|=)(\d+):(\d{2})\b")
_OVERHEAD_MINUTES = 0.5
_HEADROOM_FACTOR = 1.5


def _required_cap(max_suite: str) -> int:
    """Return ``ceil((max + 30s) * 1.5)`` minutes for an ``MM:SS`` maximum."""
    minutes, seconds = max_suite.split(":")
    total = int(minutes) + int(seconds) / 60
    return math.ceil((total + _OVERHEAD_MINUTES) * _HEADROOM_FACTOR)


def _job_blocks(text: str) -> dict[str, str]:
    """Map every job key under ``jobs:`` to its text block (up to the next job key)."""
    jobs_start = text.find("\njobs:")
    body = text[jobs_start:] if jobs_start >= 0 else text
    matches = list(_JOB_KEY_RE.finditer(body))
    return {match.group(1): body[match.start() : (matches[index + 1].start() if index + 1 < len(matches) else len(body))] for index, match in enumerate(matches)}


def _comment_above(block: str, offset: int) -> str:
    """Return the last non-blank line before ``offset`` in ``block``."""
    preceding = [line for line in block[:offset].splitlines() if line.strip()]
    return preceding[-1] if preceding else ""


def _cap_violations(text: str) -> list[str]:
    """Return one named message per job whose cap or comment is wrong."""
    problems: list[str] = []
    for job, block in _job_blocks(text).items():
        timeout = _TIMEOUT_RE.search(block)
        if timeout is None:
            problems.append(f"{job}: no job-level `timeout-minutes:` found")
            continue
        headroom = _HEADROOM_RE.search(_comment_above(block, timeout.start()))
        if headroom is None:
            problems.append(f"{job}: missing `# headroom (#5378): max-suite(>=|=)MM:SS` comment directly above `timeout-minutes:`")
            continue
        required = _required_cap(f"{headroom.group(2)}:{headroom.group(3)}")
        cap = int(timeout.group(1))
        if cap < required:
            problems.append(f"{job}: timeout-minutes {cap} < required {required} for max-suite{headroom.group(1)}{headroom.group(2)}:{headroom.group(3)}")
    return problems


def test_required_cap_formula() -> None:
    assert _required_cap("38:03") == 58
    assert _required_cap("36:28") == 56
    assert _required_cap("0:00") == 1


def test_violation_check_flags_low_cap_and_missing_comment() -> None:
    synthetic = (
        "jobs:\n"
        "  low:\n"
        "    # headroom (#5378): max-suite>=38:03 runs=1 formula=x\n"
        "    timeout-minutes: 40\n"
        "  uncommented:\n"
        "    timeout-minutes: 99\n"
        "  ok:\n"
        "    # headroom (#5378): max-suite>=38:03 runs=1 formula=x\n"
        "    timeout-minutes: 58\n"
    )
    problems = _cap_violations(synthetic)
    assert len(problems) == 2
    assert "low" in problems[0] and "< required 58" in problems[0]
    assert "uncommented" in problems[1] and "missing" in problems[1]


def test_violation_check_ignores_step_level_timeout() -> None:
    synthetic = "jobs:\n  test:\n    steps:\n      - name: x\n        # headroom (#5378): max-suite=1:00 runs=1 formula=x\n        timeout-minutes: 99\n"
    assert _cap_violations(synthetic) == ["test: no job-level `timeout-minutes:` found"]


def test_violation_check_rejects_comment_not_directly_above() -> None:
    synthetic = "jobs:\n  test:\n    # headroom (#5378): max-suite=1:00 runs=1 formula=x\n    runs-on: ubuntu-24.04\n    timeout-minutes: 99\n"
    problems = _cap_violations(synthetic)
    assert len(problems) == 1 and "missing" in problems[0]


def test_module_tests_timeout_cap_meets_recorded_headroom() -> None:
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    blocks = _job_blocks(text)
    assert "test" in blocks, f"non-vacuity: expected the reusable shard job `test`, found {sorted(blocks)}"
    assert _TIMEOUT_RE.search(blocks["test"]) is not None, "non-vacuity: shard job has no job-level cap"
    assert _cap_violations(text) == []
