---
work_package_id: WP01
title: Demote the per-PR charter length assertion
dependencies: []
requirement_refs:
- FR-001
- FR-002
- FR-003
- FR-004
- C-001
- C-002
- C-005
- NFR-001
planning_base_branch: issue-5189-per-pr-shard-timings-recapture-friction
merge_target_branch: issue-5189-per-pr-shard-timings-recapture-friction
branch_strategy: Planning artifacts for this mission were generated on issue-5189-per-pr-shard-timings-recapture-friction. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5189-per-pr-shard-timings-recapture-friction unless the human explicitly redirects the landing branch.
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
- T007
- T008
phase: Phase 1 - Core demotion (User Stories 1 & 3)
history:
- at: '2026-09-27T22:00:54Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: ''
authoritative_surface: tests/architectural/test_module_length_agreement.py
create_intent: []
execution_mode: code_change
model: ''
owned_files:
- tests/architectural/test_module_length_agreement.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---

# Work Package Prompt: WP01 – Demote the per-PR charter length assertion

## ⚡ Do This First: Load Agent Profile

Use the `/ad-hoc-profile-load` skill to load the agent profile specified in the frontmatter (or any
user-defined profile), and behave according to its guidance before parsing the rest of this prompt.

- **Profile**: `{{agent_profile}}`
- **Role**: `implementer`
- **Agent/tool**: `{{agent}}`

If no profile is specified, run `spec-kitty agent profile list` and select the best match for
`task_type: implement` and `authoritative_surface: tests/architectural/test_module_length_agreement.py`.

---

## ⚠️ IMPORTANT: Review Feedback

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_ref` field in the event log (via
  `spec-kitty agent tasks status` or the Activity Log below).
- **You must address all feedback** before your work is complete.
- **Report progress**: As you address each feedback item, update the Activity Log.

---

## Markdown Formatting

Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``. Use language identifiers in code
blocks: ` ```python `, ` ```bash `.

---

## Objectives & Success Criteria

Demote `test_charter_is_not_allowlisted_and_agrees`
(`tests/architectural/test_module_length_agreement.py`) from a hard, blocking assertion to a
visible-but-non-blocking `pytest.xfail`, so a bare charter test-count change no longer reds the
per-PR architectural-battery shard — while keeping drift visibly reported and a genuine
infrastructure break still fatal. This is this mission's core deliverable: **FR-001, FR-002,
FR-003, FR-004** (User Stories 1 and 3), plus **C-001** (charter-only scope) and **C-002** (no
allowlist-mutation feature).

**Success criteria** (this WP is done when all hold):
- SC-001: a synthetic charter length disagreement no longer fails the architectural-battery run —
  it reports `xfailed` with a message carrying both counts (proven by T004/T007).
- SC-002: `charter` is still absent from `_MISMATCH_ALLOWLIST` (unconditional `assert`, unchanged).
- SC-006: the four other tests in this file (`test_allowlist_does_not_exceed_baseline`,
  `test_allowlisted_modules_still_genuinely_mismatch`, `test_allowlist_entries_are_real_registry_modules`,
  `test_non_allowlisted_modules_agree_with_live_collection`) and the 19-entry
  `_MISMATCH_ALLOWLIST` are byte-identical before/after (diff review, T008).

**This WP does NOT**: touch `_MISMATCH_ALLOWLIST`'s contents, touch `_BASELINE_ALLOWLIST_COUNT`,
touch `capture_shard_timings.py` (it is deliberately unmodified — plan.md item (e)), or touch any
module other than `charter`.

## Context & Constraints

- **Read in full before editing**: `tests/architectural/test_module_length_agreement.py` (421
  lines). You are editing exactly one test function and adding one small pure helper plus 3 new
  test functions — the file's existing session-scoped-fixture / pure-`_find_mismatches`-helper /
  self-mutation-test idiom (see the file's own bottom section,
  `test_mismatch_detection_fires_on_synthetic_length_disagreement`) is the shape your additions
  should match. **No campsite-clean commit is needed** — plan.md item (e) read this file in full
  and found no debt in scope; this mission's addition is additive, in the file's own idiom.
- **Supporting docs**: `.kittify/charter/charter.md` (Standing Order #5 — architectural gate
  discipline: relocate, don't drop), `kitty-specs/per-pr-shard-timings-recapture-friction-01M3H7V8/spec.md`
  (FR-001..FR-004, User Stories 1 & 3, Charter Tension section), `.../plan.md` (§"Concrete Design
  Decisions (d)" for the exact code shapes below), `.../reviews/spec.ruling.md` and
  `.../reviews/plan.ruling.md` (binding operator rulings — do not relitigate).
- **Why this matters (Charter Tension, Standing Order #5)**: this demotion is an operator ruling
  (CL-001/CL-002/CL-003 in spec.md), not a green-wash, because (1) the exact-count invariant is
  relocated to a scheduled recapture (WP02/WP03), never dropped; (2) `charter` never enters
  `_MISMATCH_ALLOWLIST`; (3) the other four tests are untouched; (4) drift stays visible via
  `xfail`, never a silent pass.

## Branch Strategy

- **Strategy**: `SINGLE_BRANCH` — this mission has no lane topology beyond the one planning/target
  branch.
- **Planning base branch**: `issue-5189-per-pr-shard-timings-recapture-friction`
- **Merge target branch**: `issue-5189-per-pr-shard-timings-recapture-friction`

> These fields are populated automatically by `spec-kitty agent mission finalize-tasks`. Do NOT
> change them manually unless you are certain the branch topology has changed.

## Subtasks & Detailed Guidance

### Subtask T001 – Capture the RED-FIRST baseline (before ANY edit)

- **Purpose**: Per plan.md item (f) / `NO_FULL_HEAVY_SUITES_IN_MISSION`, this WP is the first (and
  only) WP to touch `tests/architectural/test_module_length_agreement.py`. The baseline MUST be
  captured on current HEAD, before your own edit, so a pre-existing red is never misattributed to
  this mission's change.
- **Steps**:
  1. Confirm you are on current HEAD with no uncommitted changes to this file yet.
  2. Run **exactly** this command (scoped to the one targeted file — never a bare
     `tests/architectural/` directory run, never `make test-full`):
     ```
     .venv/bin/python -m pytest tests/architectural/test_module_length_agreement.py -q
     ```
     (Use `.venv/bin/python -m pytest`, NOT `uv run --frozen pytest` — this checkout's own hard
     rule is never a bare `uv run`, since it re-syncs the environment and can destroy a hand-built
     `.venv`.)
  3. Record the full pass/fail counts and any failure output in this WP's Activity Log.
- **Files**: none changed by this subtask — read-only baseline capture.
- **Parallel?**: Must run before T002-T008 (sequential prerequisite within this WP); safe to run in
  parallel with WP02's subtasks (different files).
- **Notes — MANDATORY escalation path, not a WP decision**: if this baseline surfaces ANY
  pre-existing red (a failure unrelated to a charter change you have not made yet), **do NOT fix
  it and do NOT file a GitHub issue.** Per plan.md item (f), filing an issue for a pre-existing
  failure per the charter's Pre-existing Failure Reporting Rule is an **ORCHESTRATOR action**, not
  something a WP task may do. Record the exact failure in this WP's Activity Log and report it to
  the orchestrator; do not proceed with T002-T008 until the orchestrator has acknowledged (unless
  the orchestrator has pre-authorized proceeding despite the red — record that authorization if
  given).

### Subtask T002 – Add `_charter_disposition()` helper

- **Purpose**: Extract a pure helper distinguishing "lengths agree" from "lengths disagree" so both
  the production test body (T003) and two new fast tests (T004/T005) can exercise the same logic
  independently.
- **Steps**: Add this function near the file's other pure helpers (e.g. immediately before or after
  `_find_mismatches`), verbatim from plan.md item (d):
  ```python
  _CHARTER_AGREE = None  # sentinel: lengths agree, no xfail needed

  def _charter_disposition(committed: int, collected: int) -> str | None:
      """None => lengths agree (clean pass). Otherwise: the xfail reason string."""
      if committed == collected:
          return _CHARTER_AGREE
      return f"charter length disagreement: committed={committed} collected={collected} (see FR-001, scheduled recapture workflow)"
  ```
- **Files**: `tests/architectural/test_module_length_agreement.py`.
- **Parallel?**: Depends on T001 completing first (sequential within this WP).
- **Notes**: `_CHARTER_AGREE` is just `None` under a descriptive name — do not overthink the
  sentinel; it exists so the consuming `if disposition is not _CHARTER_AGREE:` reads clearly.

### Subtask T003 – Demote `test_charter_is_not_allowlisted_and_agrees`

- **Purpose**: Wire the helper into the actual gate function, replacing the hard `assert committed
  == collected` with a call to `_charter_disposition` and a conditional `pytest.xfail`.
- **Steps**: Replace the function body's tail (after the existing
  `assert "charter" not in _MISMATCH_ALLOWLIST, ...` line, which stays **unchanged** — this is
  FR-002's unconditional invariant) with:
  ```python
  disposition = _charter_disposition(committed, collected)
  if disposition is not _CHARTER_AGREE:
      pytest.xfail(disposition)
  ```
  removing the old `assert committed == collected, f"charter regressed: ..."` line. Keep the
  function's `@pytest.mark.slow` decorator and its `_live_timings_state`/`_collected_counts`
  fixture parameters unchanged — only the assertion tail changes.
- **Files**: `tests/architectural/test_module_length_agreement.py`.
- **Parallel?**: Depends on T002.
- **Notes**: This is the ONE behavioral edit this mission makes to the gate itself. Do **not**
  touch `_MISMATCH_ALLOWLIST`, `_BASELINE_ALLOWLIST_COUNT`, or any of the other four test
  functions in this pass (C-002, FR-003) — that is a separate, deliberate non-goal.

### Subtask T004 – Add `test_charter_disposition_flags_length_disagreement`

- **Purpose**: Fast, synthetic proof that the extracted helper flags a disagreement — and that this
  test fails if the demotion is ever reverted to a bare hard `assert` (the helper would no longer
  exist / no longer be called).
- **Steps**: Add, mirroring the file's existing self-mutation-test section at the bottom
  (`@pytest.mark.fast`, no subprocess, no session fixture):
  ```python
  @pytest.mark.fast
  def test_charter_disposition_flags_length_disagreement() -> None:
      """FR-001/FR-004: a disagreement produces a non-None, count-carrying disposition."""
      disposition = _charter_disposition(10, 11)
      assert disposition is not None
      assert "10" in disposition and "11" in disposition
  ```
- **Files**: `tests/architectural/test_module_length_agreement.py`.
- **Parallel?**: Independent of T005/T006/T007 (can be written in any order once T002 exists), but
  written sequentially in this WP for review clarity.

### Subtask T005 – Add `test_charter_disposition_is_none_on_agreement`

- **Purpose**: The FR-004 "drift stays visible, not silent" claim is falsifiable — proves the
  agreeing case never enters the `xfail` path (still a plain, clean `PASSED`).
- **Steps**: Add:
  ```python
  @pytest.mark.fast
  def test_charter_disposition_is_none_on_agreement() -> None:
      """FR-004: agreeing lengths never trigger xfail — a clean pass stays a clean pass."""
      assert _charter_disposition(10, 10) is _CHARTER_AGREE
  ```
- **Files**: `tests/architectural/test_module_length_agreement.py`.
- **Parallel?**: Independent of T004/T006/T007.

### Subtask T006 – Add `test_load_timings_fails_loudly_when_artefact_missing`

- **Purpose**: Proves a genuine infrastructure break (missing timings artefact) still fails/errors
  visibly — never silently folded into the new `xfail` path — because `_load_timings()` is a
  session-scoped-fixture-level failure that happens BEFORE
  `test_charter_is_not_allowlisted_and_agrees`'s own body (and its new `_charter_disposition` call)
  ever runs.
- **Steps**: Add a test that monkeypatches `_TIMINGS_PATH` to a nonexistent file and asserts
  `_load_timings()` raises the exception class `pytest.fail(...)` raises
  (`_pytest.outcomes.Failed`). Use `monkeypatch` (pytest's built-in fixture) to patch the
  module-level `_TIMINGS_PATH` constant for the duration of the test only:
  ```python
  def test_load_timings_fails_loudly_when_artefact_missing(monkeypatch, tmp_path) -> None:
      """FR-004: a genuine infra break (missing artefact) still fails, never xfails."""
      import tests.architectural.test_module_length_agreement as this_module  # or module-relative reference per this file's own import style

      monkeypatch.setattr(this_module, "_TIMINGS_PATH", tmp_path / "does-not-exist.json")
      with pytest.raises(Exception):  # _load_timings() calls pytest.fail(...), raising _pytest.outcomes.Failed
          this_module._load_timings()
  ```
  Adjust the self-import idiom to match how this test file already references its own
  module-level names in other tests in the same file (it may be simpler to monkeypatch the
  bare module-level name directly via `monkeypatch.setattr(sys.modules[__name__], "_TIMINGS_PATH", ...)`
  if a self-import proves awkward — pick whichever is idiomatic given the file's existing imports;
  the observable requirement is what matters: `_load_timings()` raises when the artefact is
  missing, not that any particular monkeypatch idiom is used).
- **Files**: `tests/architectural/test_module_length_agreement.py`.
- **Parallel?**: Independent of T004/T005/T007.
- **Notes**: Mark this test `@pytest.mark.fast` if it introduces no subprocess/session-fixture
  dependency (it should not — `_load_timings()` only reads a path and raises via `pytest.fail`).

### Subtask T007 – Add `test_charter_is_not_allowlisted_and_agrees_xfails_on_disagreement`

- **Purpose**: Closes the "test-the-helper-not-the-integration-point" gap: T004/T005 only pin the
  extracted helper's own correctness. A revert that restores
  `test_charter_is_not_allowlisted_and_agrees`'s body to a bare hard `assert` (leaving the
  now-orphaned `_charter_disposition` helper and T004/T005 untouched and still passing) would leave
  both of those tests green, because neither exercises the production test body. This test
  exercises the **consuming test body itself**.
- **Steps**: Construct a disagreeing pair and assert the production test function raises pytest's
  `xfail` outcome (`_pytest.outcomes.XFailed`, the exception `pytest.xfail()` raises), never a bare
  `AssertionError`. The exact mechanism (monkeypatching the session-scoped
  `_live_timings_state`/`_collected_counts` fixture values, or calling
  `test_charter_is_not_allowlisted_and_agrees` directly with constructed fixture-shaped arguments)
  is your implementation choice — the observable requirement is fixed: a disagreeing `committed`
  vs. `collected` pair for `charter`, run through the actual (post-T003) test function body, raises
  `XFailed`, never `AssertionError`. One viable approach:
  ```python
  def test_charter_is_not_allowlisted_and_agrees_xfails_on_disagreement() -> None:
      """FR-001: a revert of the xfail wiring back to a hard assert is caught here,
      independent of the helper's own survival (T004/T005)."""
      from _pytest.outcomes import XFailed

      fake_timings = {"module_test_durations": {"charter": [0.0] * 10}}
      fake_collected = {"charter": 11}
      with pytest.raises(XFailed):
          test_charter_is_not_allowlisted_and_agrees(fake_timings, fake_collected)
  ```
- **Files**: `tests/architectural/test_module_length_agreement.py`.
- **Parallel?**: Depends on T003 (the production function must already be demoted for this test to
  be meaningful — but write it in the same edit pass as T003 for red-first discipline: this test
  should FAIL against the pre-T003 hard-`assert` body with `AssertionError` instead of `XFailed`,
  proving it actually exercises the demotion).

### Subtask T008 – Post-edit targeted test run + diff review

- **Purpose**: Confirm the demotion is green, confirm FR-002/FR-003/SC-006 hold (the four untouched
  tests and the 19-entry allowlist are byte-identical), and confirm the new tests actually run and
  pass.
- **Steps**:
  1. Run the same targeted command as T001 again, post-edit:
     ```
     .venv/bin/python -m pytest tests/architectural/test_module_length_agreement.py -q
     ```
  2. Confirm `test_charter_is_not_allowlisted_and_agrees` reports either a clean pass (if
     `charter`'s current committed/collected lengths agree) or `xfailed` (never a hard failure).
  3. Confirm all 4 new tests (T004-T007) pass.
  4. Run `git diff tests/architectural/test_module_length_agreement.py` and confirm the bodies of
     `test_allowlist_does_not_exceed_baseline`, `test_allowlisted_modules_still_genuinely_mismatch`,
     `test_allowlist_entries_are_real_registry_modules`, and
     `test_non_allowlisted_modules_agree_with_live_collection`, plus every entry in
     `_MISMATCH_ALLOWLIST` and the value of `_BASELINE_ALLOWLIST_COUNT`, are unchanged (SC-006).
  5. Record the final pass/fail counts in the Activity Log, alongside the T001 baseline counts for
     comparison.
- **Files**: `tests/architectural/test_module_length_agreement.py` (read-only verification pass).
- **Parallel?**: Must run last, after T002-T007.

## Test Strategy

- **Baseline (T001)**: `.venv/bin/python -m pytest tests/architectural/test_module_length_agreement.py -q`
  on current HEAD, before any edit.
- **Post-edit (T008)**: the same command, after all edits.
- **Never** run a bare `tests/architectural/` directory sweep or `make test-full` — this file alone
  is the complete, correctly-scoped blast radius for this WP (`NO_FULL_HEAVY_SUITES_IN_MISSION`).
- This file includes the `slow`-marked live-collection tests — running this one named file,
  however slow its own tests are individually, is not the "full/heavy suite" the rule forbids.

## Risks & Mitigations

- **Risk**: monkeypatching `_TIMINGS_PATH` (T006) or constructing fake fixture values (T007) in a
  way that doesn't match this file's existing idioms, producing an inconsistent style.
  **Mitigation**: read the file's existing tests bottom-to-top before writing T004-T007; match
  naming, marker usage (`@pytest.mark.fast`), and docstring style exactly.
- **Risk**: accidentally editing one of the four untouched tests' bodies while nearby.
  **Mitigation**: T008's diff review is the explicit safeguard — run it before considering this WP
  done.
- **Risk**: pre-existing red at baseline (T001) gets silently "fixed" instead of escalated.
  **Mitigation**: T001's Notes section states the escalation path explicitly; do not skip it.

## Review Guidance

- Confirm T001's baseline output is recorded in the Activity Log BEFORE the diff shows any edit to
  this file.
- Confirm the only functional change to `test_charter_is_not_allowlisted_and_agrees` is the
  assertion tail (hard `assert` -> `_charter_disposition` + `pytest.xfail`); the
  `"charter" not in _MISMATCH_ALLOWLIST"` assert stays.
- Confirm `_MISMATCH_ALLOWLIST` (all 19 entries), `_BASELINE_ALLOWLIST_COUNT`, and the four other
  test bodies are byte-identical (`git diff` review, SC-006).
- Confirm all 4 new tests are present, correctly marked, and actually fail against a
  pre-demotion (hard-`assert`) version of the file — reviewer should mentally (or actually) revert
  T003 and confirm T007 goes red, proving it is not vacuous.
- No compiler/typecheck step applies here (Python, no static typed-build gate beyond `ruff`).
- **C-005 self-check**: run `grep -rn "/home/" tests/architectural/test_module_length_agreement.py`
  and confirm no match, before marking this WP done — no absolute local paths or credentials may
  land in this committed artifact.

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

**Initial entry**:

- 2026-09-27T22:00:54Z – system – Prompt created.
