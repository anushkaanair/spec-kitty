---
work_package_id: WP01
title: Nightly interpreter-matrix shard split (IC-01..IC-04)
dependencies: []
requirement_refs:
- FR-001
- FR-002
- FR-003
- FR-004
- FR-005
- FR-006
- FR-007
- FR-008
- FR-009
- FR-010
- FR-011
- FR-012
- FR-013
- FR-014
- FR-015
- FR-016
- FR-017
planning_base_branch: issue-4951-ci-nightly-interpreter-matrix-timeout
merge_target_branch: issue-4951-ci-nightly-interpreter-matrix-timeout
branch_strategy: Planning artifacts for this mission were generated on issue-4951-ci-nightly-interpreter-matrix-timeout. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-4951-ci-nightly-interpreter-matrix-timeout unless the human explicitly redirects the landing branch.
base_branch: kitty/mission-ci-nightly-interpreter-matrix-45min-timeout-01M3G17F
base_commit: ee7494599d03830624549c870523533fc913c3c1
created_at: '2026-09-27T03:53:04.555202+00:00'
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
- T007
- T008
- T009
- T010
- T011
- T012
- T013
phase: Phase 1 - Only phase (single-WP mission, see tasks.md WP-granularity note)
history:
- at: '2026-09-27T01:46:46Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: implementer-ivan
authoritative_surface: .github/workflows/ci-nightly.yml
create_intent:
- tests/architectural/test_interpreter_shard_coverage.py
- tests/architectural/_interpreter_shard_roster.py
execution_mode: code_change
model: ''
owned_files:
- .github/workflows/ci-nightly.yml
- tests/architectural/test_performance_marker_guard.py
- tests/architectural/test_interpreter_shard_coverage.py
- tests/architectural/_interpreter_shard_roster.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---

# Work Package Prompt: WP01 – Nightly interpreter-matrix shard split (IC-01..IC-04)

## ⚡ Do This First: Load Agent Profile

Use the `/ad-hoc-profile-load` skill to load the agent profile specified in the
frontmatter (or any user-defined profile), and behave according to its guidance
before parsing the rest of this prompt.

- **Profile**: `implementer-ivan`
- **Role**: `implementer`
- **Agent/tool**: `claude`

If no profile is specified, run `spec-kitty agent profile list` and select the
best match for this work package's `task_type` and `authoritative_surface`.
(Note: `python-pedro` was considered and rejected for this WP — its profile
explicitly names "infrastructure-as-code" as an avoidance boundary, and this WP
is majority GitHub Actions YAML plus Python test-support code. `implementer-ivan`
is the general-purpose implementer with no such exclusion.)

---

## ⚠️ IMPORTANT: Review Feedback

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_ref` field in the event log (via
  `spec-kitty agent tasks status` or the Activity Log below).
- **You must address all feedback** before your work is complete. Feedback items
  are your implementation TODO list.
- **Report progress**: As you address each feedback item, update the Activity Log
  explaining what you changed.

## Review Feedback

*[If this WP was returned from review, the reviewer feedback reference appears in
the Activity Log below or in the status event log.]*

---

## Markdown Formatting

Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ```` ```python ````, ```` ```bash ````

---

## Objectives & Success Criteria

Replace the single, always-timing-out `interpreter-matrix` nightly job in
`.github/workflows/ci-nightly.yml` with N independent, nightly-only shard jobs,
each a disjoint slice of `pytest -m "fast or unit"` on Python 3.13 with its own
measured `timeout-minutes`, backed by a machine-checked coverage-completeness
proof and a shard-identity roster, with the architectural guard updated and
proven non-vacuous, and real `workflow_dispatch` evidence proving every shard
reaches a genuine `success`/`failure` verdict within budget.

This WP alone satisfies **every** functional requirement in spec.md (FR-001
through FR-017) and every success criterion (SC-001 through SC-010) — it is the
mission's only work package (see `tasks.md`'s WP-granularity note for why).

**Definition of Done**:
- `.github/workflows/ci-nightly.yml`'s `interpreter-matrix` job is replaced by N
  `interpreter-matrix-shard-<N>` jobs, each independently pinned, sync'd, run,
  uploaded, escalated, and fail-loud-gated (FR-001, FR-007, FR-008, FR-011,
  FR-012).
- `nightly-summary`'s `needs:` and result-echo step name every shard (FR-006);
  zero dangling reference to the old job name remains anywhere in the file
  (SC-006).
- `tests/architectural/_interpreter_shard_roster.py` (new) and
  `tests/architectural/test_interpreter_shard_coverage.py` (new) exist, pass,
  and are proven non-vacuous by mutation tests (FR-004, FR-005, FR-016, FR-017,
  SC-003, SC-009, SC-010).
- `tests/architectural/test_performance_marker_guard.py` is updated (FR-009,
  FR-010, FR-013, FR-015) and proven non-vacuous (SC-004, SC-008).
- Up to 3 real `workflow_dispatch` runs of `ci-nightly.yml` on this mission's
  branch produce durable evidence that every shard completes within its own
  budget (FR-014, NFR-005, SC-001, SC-002).
- A PR targeting `main` is opened with the full local gate set green and
  evidence recorded (plan.md §I step 8).

## Context & Constraints

**Read first, in full**: `.kittify/charter/charter.md`,
`kitty-specs/ci-nightly-interpreter-matrix-45min-timeout-01M3G17F/spec.md`,
`kitty-specs/ci-nightly-interpreter-matrix-45min-timeout-01M3G17F/plan.md` (this
prompt translates plan.md directly — re-read §A, §B, §C, §F, §G, §I before
starting; this prompt summarizes but does not replace them).

**Hard boundaries — do not cross these**:
- `.github/workflows/module-tests.yml` and `.github/ci-module-registry.yml` are
  **NEVER touched** by this mission (C-002). Do not open them for edit.
- `tests/architectural/_gate_coverage.py` is **read-only** for this mission. You
  may import and call its exported primitives (`Gate`, `parse_workflow`,
  `collect_job_nodeids`, `BaselineTarget`, `gates_for_target`) exactly as
  plan.md §A's reuse decision specifies. You may **never** edit that file,
  and in particular **never** touch its `_FLAG_TOKENS` regex — it has a known,
  pre-existing, mission-independent defect (documented in plan.md §A point 6)
  that this mission does not fix and is out of scope for this WP entirely.
- `scripts/ci/capture_shard_timings.py` and `.github/ci-module-registry.yml`'s
  `shard_count` LPT bin-packing mechanism are explicitly **rejected** as a
  sizing method (ledger SK-247) — do not reuse or extend them (FR-003).
- No `pull_request` trigger may be introduced anywhere (C-001, FR-013).
- **This WP does not push to `main`.** Every push in this WP goes to the
  mission's own branch, `issue-4951-ci-nightly-interpreter-matrix-timeout`.

**Out-of-map edit, pre-authorized**: this WP's `owned_files` deliberately does
NOT list any `kitty-specs/` path (a `code_change` WP is hard-rejected by
`finalize-tasks` for owning one). However, T012 requires editing
`kitty-specs/ci-nightly-interpreter-matrix-45min-timeout-01M3G17F/tracer-approach.md`
to record dispatch evidence (NFR-005) — this is a small, explicitly
pre-authorized out-of-map edit with a one-line rationale ("recording
dispatch-run evidence per NFR-005"), not something requiring a separate
planning-artifact WP. Do not add it to `owned_files`.

**Chokepoint**: `.github/workflows/ci-nightly.yml` is a shared CI workflow file
across the whole repo. Any other in-flight mission editing it would serialize
with this one — re-check for such collisions before every push (see the
Write-scope/open-PR overlap note in `tasks.md`, and T008/T011/T013 below).

## Branch Strategy

- **Strategy**: single branch, no lanes/worktree split across multiple WPs
  (this mission has exactly one WP).
- **Planning base branch**: `issue-4951-ci-nightly-interpreter-matrix-timeout`
- **Merge target branch**: `main`

> These fields are populated automatically by `spec-kitty agent mission
> finalize-tasks`. Do NOT change them manually unless you are certain the
> branch topology has changed.

Per the charter's worktree-isolation standing order (DIRECTIVE_045), every step
below that pushes, dispatches, or opens the PR runs from the workspace
`spec-kitty implement WP01` resolves via `lanes.json` — never the primary
checkout.

---

## Subtasks & Detailed Guidance

### Subtask T001 – Baseline architectural-suite capture and pre-existing-failure classification

- **Purpose**: Establish, before any workflow-file edit, which tests are
  already red on the branch base — so nothing this mission introduces is
  wrongly excused as "pre-existing," and nothing pre-existing is wrongly
  chased as a regression this mission caused (plan.md §F).
- **Steps**:
  1. On the branch base (current HEAD, before this WP's first edit), run:
     `pytest tests/architectural/test_performance_marker_guard.py -q` in
     isolation.
  2. Run the full `tests/architectural/` suite:
     `pytest tests/architectural/ -q` (this is the C-005 "added local step" —
     `ci-router.yml`'s own path filters will NOT select this battery for this
     mission's diff; see plan.md §E).
  3. Whatever is red on this baseline run is pre-existing. Per spec.md's Edge
     Cases and plan.md §F, **re-verify** (do not trust the plan's snapshot):
     `gh issue view 3284` — confirm it is still CLOSED (closed 2026-09-08 per
     the plan; re-confirm at the time you actually run this).
  4. Search for any newer OPEN "Pre-existing Failure" issue that might explain
     current baseline red (e.g. `gh issue list --repo spec-kitty/spec-kitty
     --search "pre-existing failure" --state open`).
  5. If baseline red exists that is NOT explained by an existing filed issue,
     file one per the charter's binding Pre-existing Failure Reporting Rule
     (command run, failure summary, why judged pre-existing) BEFORE treating
     it as accepted baseline.
- **Files**: none changed; this is a read-only measurement subtask. Record the
  baseline pass/fail counts in `tracer-approach.md`.
- **Parallel?**: No — must precede every other subtask.
- **Notes**: The nightly `interpreter-matrix` leg being red/cancelled on `main`
  today is **NOT** baseline noise — it IS this mission's acceptance criterion
  (SC-002). Do not classify it as pre-existing-and-excused; it is the thing
  this mission fixes.

### Subtask T002 – Empirical gate-parseability re-derivation against the CURRENT `ci-nightly.yml`

- **Purpose**: Plan.md §A point 6 makes an empirically-verified claim —
  `_gate_coverage.parse_workflow` resolves exactly 5 gates (`performance`,
  `e2e`, `stress`, `full-module-matrix`, `integration-next`) against the
  CURRENT workflow, and **zero** for `interpreter-matrix` — which differs from
  a number ("4") that circulated earlier in this mission's own orchestration.
  This subtask re-runs that check directly, rather than trusting either
  number, and reports what it actually resolves to.
- **Steps**:
  1. From the repo root, run:
     ```bash
     .venv/bin/python -c "
     from pathlib import Path
     from tests.architectural._gate_coverage import parse_workflow
     gates = parse_workflow(Path('.github/workflows/ci-nightly.yml'))
     for g in gates:
         print(g.workflow, '::', g.job, '(shard=' + repr(g.shard) + ')')
     print('TOTAL:', len(gates))
     "
     ```
  2. Compare the printed job list against the plan's claim (5 gates, listed
     above; 0 for `interpreter-matrix`). Report the ACTUAL result in
     `tracer-design-decisions.md` — whichever it is — with the exact command
     and output, not a restatement of the plan's number.
  3. If the actual result differs from the plan's claim, STOP and flag the
     discrepancy in the Activity Log before proceeding to T003 — do not
     silently proceed on an unverified assumption either way.
- **Files**: read-only against `.github/workflows/ci-nightly.yml` and
  `tests/architectural/_gate_coverage.py` (never edited).
- **Parallel?**: No — precedes the shard-split design work (T004-T006), which
  depends on knowing the correct parseable shape.
- **Notes**: This is the FR-017-mandated re-derivation — checkpoint 0 of 4
  total parseability checkpoints in this WP: 0 = T002 (here, against the
  CURRENT `ci-nightly.yml`); 1 = T007 (mandatory, against the freshly-authored
  shard shape); 2 = T009 (conditional — fires only if T009 actually redraws
  shard boundaries); 3 = T010 (mandatory/unconditional, after scaffolding
  removal).

### Subtask T003 – Campsite-clean commit

- **Purpose**: Rewrite the current `interpreter-matrix` job's descriptive
  comments (lines ~365-456 of `.github/workflows/ci-nightly.yml`) to describe
  the incoming shard shape and the roster's existence, as a distinct,
  behaviour-preserving first commit — per plan.md §C, this is proportional
  tidy-up inside the one file already being edited (the SAME surface the
  functional change touches), not scope growth.
- **Steps**:
  1. Identify every multi-line comment describing the single-job shape: the
     "Deliberately scoped to the nightly lane... interpreter-matrix job runs
     the fast/unit suite on every Python version ABOVE 3.12" block, the
     `#4866` per-interpreter dedicated venv comment block, and the terminal
     fail-loud gate's comment referencing "the FR-021 interpreter lane".
  2. Rewrite each to describe the post-split shard shape and reference the new
     roster module (`tests/architectural/_interpreter_shard_roster.py`).
  3. Make **no functional change** in this commit — comments only. Verify with
     `git diff` that only comment lines changed.
  4. Commit locally (do not push yet — T008 is the first push).
- **Files**: `.github/workflows/ci-nightly.yml` (comments only).
- **Parallel?**: No — must land before T004-T006's structural edits, so the
  diff reads as "comment/doc update" then "structural split."
- **Notes**: No other domain-matched debt was found in the touched surfaces
  per plan.md §C (`test_performance_marker_guard.py` has no stale comments
  blocking this change). Do not go looking for unrelated cleanup — this is a
  single, domain-matched tidy, not a grab-bag.

### Subtask T004 – Author shard-identity roster + coverage-completeness/roster-diff test, red-first

- **Purpose**: Machine-check that the union of every shard's collected
  node-ids equals the full 3.13 `fast or unit` selection (FR-004/NFR-002), and
  that no shard is silently dropped from the job list while remaining in an
  independent roster (FR-016) — authored BEFORE the real shard jobs exist, so
  it is red-first against the not-yet-split workflow (ATDD-first, plan.md
  Charter Check).
- **Steps**:
  1. Create `tests/architectural/_interpreter_shard_roster.py` (NEW,
     `create_intent`) with exactly the shape plan.md §A "Shard-identity roster
     shape" specifies:
     ```python
     from dataclasses import dataclass

     @dataclass(frozen=True)
     class InterpreterShard:
         job_key: str
         paths: tuple[str, ...]
         ignores: tuple[str, ...] = ()
         suite_key: str = ""

     INTERPRETER_SHARDS: tuple[InterpreterShard, ...] = (
         # populated with an INITIAL guess here; T009 replaces with real
         # boundaries once T008's dispatch run 1 data exists.
     )
     ```
     Populate `INTERPRETER_SHARDS` with an initial N=3 guess and illustrative
     directory boundaries (plan.md §A gives an illustrative shape: shard 1 =
     `tests/unit tests/status tests/cli`; shard 2 = `tests/specify_cli/runtime
     tests/charter tests/kernel`; shard 3 = everything else via `--ignore`
     globs for shards 1-2's directories). Document in a module docstring that
     these are PLACEHOLDER boundaries pending T008/T009's real measurement
     (NFR-006 — auditable methodology).
  2. Create `tests/architectural/test_interpreter_shard_coverage.py` (NEW,
     `create_intent`) implementing, per plan.md §A's reuse-vs-rejection
     decision (FR-017/SC-010 — this decision is ALREADY recorded in plan.md;
     do not re-litigate it, just implement it):
     - A **synthetic full-selection `Gate`** (`workflow="ci-nightly.yml"`,
       `job="<synthetic-full-selection>"`, `marker_expr='fast or unit'`,
       `paths=["tests"]`, `shard=None`) — never inserted into the real
       workflow file, used only to reuse `collect_job_nodeids`'s exact
       collection mechanics for the ground-truth side of FR-004's comparison.
     - Per-shard `BaselineTarget(slug=<shard_name>, workflow="ci-nightly.yml",
       job=<shard_job_key>)` constructed LOCALLY inside this test module —
       **never** added to the shared `BASELINE_TARGETS` tuple. Call
       `gates_for_target` for each; its existing raise-loudly-on-zero-gates
       behavior gives FR-016's "job renamed/deleted" detection for free.
     - The node-id union check (FR-004/NFR-002/SC-003): collect the full
       selection's node-ids via the synthetic Gate, collect each shard's
       node-ids via its real Gate, assert the union of shard sets equals the
       full set with zero duplicates and zero gaps. On failure, name the
       specific missing or duplicated node id(s) (spec.md Edge Cases).
     - The roster-vs-`jobs:`-keys diff (FR-016/SC-009): diff
       `{s.job_key for s in INTERPRETER_SHARDS}` against
       `parse_workflow("ci-nightly.yml")`'s real job-key set. A shard in the
       roster but absent from `jobs:` fails loudly naming that shard.
     - The zero-collection check (FR-005): a shard whose selector collects 0
       node-ids fails loudly naming the empty shard.
     - **Required mutation tests** (Standing Order #5, non-optional per the
       mission brief):
       - A test that mutates a shard boundary (in-memory) to drop or
         duplicate a test file and asserts the coverage-completeness check
         fails (SC-003's required positive control).
       - A test that deletes one roster-declared shard's `jobs:` entry (in a
         scratch copy, never writing to disk unless a test specifically needs
         `parse_workflow` to re-read from a `tmp_path`) and asserts the
         roster-diff fails, naming that shard (SC-009's required positive
         control).
  3. Run both new test files now — confirm they are genuinely **red** against
     the not-yet-split workflow (the roster references shard job keys that
     don't exist yet in `ci-nightly.yml`). Record this red state in the
     Activity Log as the red-first proof (plan.md §G row 2/3).
- **Files**: `tests/architectural/_interpreter_shard_roster.py` (new),
  `tests/architectural/test_interpreter_shard_coverage.py` (new).
- **Parallel?**: No — T005 depends on this file's `INTERPRETER_SHARDS` shape
  existing to know what job keys to author.
- **Notes**: Do NOT wire through `BASELINE_TARGETS` or
  `collect_real_union_for_target`/`freeze_baselines` — plan.md §A explicitly
  rejects that layer for both FR-004 and FR-016 (it answers "did this ONE
  job's selection drift since a human froze it," not "do these N live
  selections union to exactly today's full selection").

### Subtask T005 – Author the shard split in `ci-nightly.yml`

- **Purpose**: Replace the single `interpreter-matrix` job with N independent
  `interpreter-matrix-shard-<N>` jobs matching T004's roster, making T004's
  red tests go green (FR-001, FR-006, FR-007, FR-008, FR-011, FR-012).
- **Steps**:
  1. For each shard in `INTERPRETER_SHARDS` (initial N=3 guess from T004),
     author a job following plan.md §A's exact "Per-shard job shape" template
     — independently, per shard, with NO shared/reused sync step:
     `actions/checkout`, `actions/setup-python` (`python-version: '3.13'`),
     `astral-sh/setup-uv`, `uv sync --frozen --all-extras --python "3.13"`,
     the `set +e` + `if: always()` run step, upload-artifact, the
     `nightly_escalation.py` escalate step, and the terminal fail-loud step.
  2. **Deliberately drop the `--python "<value>"` flag** from the `uv run ...
     pytest` line (unlike the CURRENT single job). Python is already pinned
     via `actions/setup-python` and `UV_PROJECT_ENVIRONMENT`. This is
     SPECIFICALLY required to make each shard parseable by `_gate_coverage.py`
     (plan.md §A point 6 — this is not a style preference, it fixes the
     parseability defect T002 found).
  3. Set each `timeout-minutes` to the full 45 minutes UNCHANGED for now
     (T009 finalizes real numbers from run 1's data — plan.md §I step 2).
  4. Give each shard a distinct `--suite-key`: `interpreter-3.13-shard-<N>`
     (FR-011/FR-015) — note this is a DIFFERENT SHAPE from the current
     single-job key (`interpreter-${{ matrix.python-version }}"`), not merely
     a substitution, so a copy-paste-forgot-to-renumber mistake is what T006's
     suite-key mutation test targets.
  5. Update `nightly-summary`'s `needs:` list — replace `interpreter-matrix`
     with every `interpreter-matrix-shard-<N>` key — and add one
     `echo "interpreter-matrix-shard-<N>: ${{
     needs.interpreter-matrix-shard-<N>.result }}"` line per shard, replacing
     the single `interpreter-matrix` line (FR-006).
  6. Confirm SC-006: `grep -n 'interpreter-matrix"' .github/workflows/ci-nightly.yml`
     (exact old job key, quoted, as a job reference) returns no hits outside
     comments T003 already rewrote.
  7. Run T004's tests again — confirm they now pass (green) against the newly
     split workflow.
- **Files**: `.github/workflows/ci-nightly.yml`.
- **Parallel?**: No — depends on T004's roster; T006 depends on this step's
  real job keys existing.
- **Notes**: NFR-004 (N-times checkout+sync cost) is accepted, documented
  cost — do not try to share a sync step across shards to "optimize" this
  away; FR-008 specifically requires independent per-shard sync.

### Subtask T006 – Update the architectural guard + non-vacuity + suite-key-uniqueness tests

- **Purpose**: Update `tests/architectural/test_performance_marker_guard.py`'s
  hardcoded single-job `"interpreter-matrix"` assertions to the shard shape
  (FR-009), prove the update non-vacuous (FR-010, Standing Order #5), and add
  the suite-key-uniqueness assertion (FR-015) with its own mutation tests.
- **Steps**:
  1. Replace the shared `for job_name in ("performance", "e2e", "stress",
     "interpreter-matrix")` loop (used by `test_nightly_suite_steps_are_fail_loud`
     and `test_nightly_fail_loud_step_treats_marker_empty_exit_5_as_non_failing`)
     with `for job_name in ("performance", "e2e", "stress",
     *INTERPRETER_SHARD_JOB_KEYS)`, importing `INTERPRETER_SHARD_JOB_KEYS =
     tuple(s.job_key for s in INTERPRETER_SHARDS)` from the new roster module
     — DYNAMIC discovery, not a second hardcoded literal list.
  2. Replace `test_nightly_workflow_houses_performance_and_interpreter_jobs`'s
     single-job lookup (`jobs.get("interpreter-matrix")`) and its
     `python-version` matrix assertion with: an assertion that EVERY
     roster-declared shard job key exists in `jobs:` (reuse `gates_for_target`'s
     raise, per plan.md §A), AND that the workflow still pins Python 3.13 per
     shard (`actions/setup-python`'s `with: {python-version: '3.13'}` and the
     `uv sync --frozen --all-extras --python "3.13"` step both carry the pin —
     the `uv run ... pytest` line deliberately does NOT, per T005 step 2).
  3. Add `test_guard_fails_when_a_shard_is_dropped_from_the_job_list`: load
     `ci-nightly.yml`'s parsed YAML, delete one roster-declared shard's
     `jobs:` entry in an in-memory scratch dict (never write to disk), and
     assert the SAME job-presence assertion from step 2 fails against it.
  4. Add `test_guard_fails_when_shards_are_reverted_to_a_single_job`: replace
     all shard entries with one synthetic `interpreter-matrix` job (the
     pre-split shape) in a scratch dict, and assert the same failure.
  5. Confirm `test_nightly_workflow_never_triggers_on_pull_request` and
     `test_no_pull_request_workflow_selects_performance_or_interpreter_jobs`
     (FR-013) are left semantically unchanged and still pass — do not touch
     `FORBIDDEN_PR_PATH_TOKENS`; its existing `"interpreter-matrix"` substring
     already matches every new shard name by construction.
  6. Add `test_nightly_suite_keys_are_pairwise_distinct`: parse the loaded
     YAML `jobs:` mapping; for each job, join its `steps[].run` string across
     shell line-continuations (a trailing `\` immediately followed by a
     newline becomes a single space) and split into statements on unescaped
     newlines and `;`. Apply the three-form pattern
     `--suite-key\s+(?:"([^"]+)"|'([^']+)'|(\S+))` ONLY to a statement that
     ALSO contains the literal substring `nightly_escalation.py` (this is the
     invocation-anchor that prevents a stray comment mentioning
     `--suite-key` from being misread as a real key). Collect keys across ALL
     nightly jobs (`performance`, `e2e`, `stress`, every
     `interpreter-matrix-shard-<N>`, `integration-next`) — note four of these
     (`performance`, `e2e`, `stress`, `integration-next`) use BARE unquoted
     keys today, so the bare-token alternative is not hypothetical; assert
     `len(keys) == len(set(keys))`.
  7. Add the four required mutation tests:
     - `test_suite_key_uniqueness_guard_is_non_vacuous`: two shards' keys
       deliberately collided (both `"interpreter-3.13-shard-1"`); assert the
       uniqueness assertion fails.
     - A quote-style variant: the same collision expressed with one
       single-quoted and one double-quoted value; assert it still fails
       (proves extraction doesn't key off quote style).
     - A bare-vs-quoted variant: collide an existing bare key (e.g.
       `performance`) against a shard's quoted key given the same literal
       (`--suite-key "performance"`); assert it fails (proves bare and quoted
       forms feed the SAME `keys` list, not separate pools).
     - `test_suite_key_extraction_ignores_non_invocation_mentions`: a scratch
       job's `run:` string contains a `#`-prefixed comment
       (`# --suite-key convention: interpreter-3.13-shard-9`) alongside a
       normal, correctly-scoped invocation; assert the extracted `keys` list
       does NOT contain `interpreter-3.13-shard-9` from the comment.
- **Files**: `tests/architectural/test_performance_marker_guard.py`.
- **Parallel?**: No — depends on T005's real job keys.
- **Notes**: This is Standing Order #5 in concrete form — "a gate-unmask
  cannot self-validate." Every one of the mutation tests above is a required
  deliverable per spec.md SC-004/SC-008, not optional hardening.

### Subtask T007 – Parseability re-check (authored shape) + full local gate run

- **Purpose**: Confirm the AUTHORED shard job YAML (T005) is actually
  parseable by `_gate_coverage.py` before treating T004's assertions as
  meaningful (plan.md §A point 6 / IC-02 sequencing note, checkpoint 1 of 4,
  mandatory), and confirm the full local gate set is green before the first
  push.
- **Steps**:
  1. Re-run T002's exact `parse_workflow` invocation, now against the
     AUTHORED (post-T005) `.github/workflows/ci-nightly.yml`. Confirm each
     shard's `BaselineTarget` resolves a non-empty `Gate` list — do this by
     inspection of `gates_for_target`'s return, not just by re-reading the
     YAML.
  2. If any shard fails to parse, fix the `run:` line shape (most likely
     cause: a leftover `--python` flag or an unexpected quoting) and re-run
     until every shard parses. Do NOT edit `_gate_coverage.py` to work around
     a parse failure.
  3. Run `ruff check .` and `ruff format --check .` (C-004) — must be zero
     issues on every touched Python file.
  4. Run the full `tests/architectural/` suite (C-005): `pytest
     tests/architectural/ -q`. Confirm T004's and T006's new/updated tests are
     now GREEN (they were red in T004/before T006; this confirms the
     mechanical split made them pass).
  5. Compare this run's red/green counts against T001's baseline — anything
     newly red that wasn't red at baseline is this mission's to fix before
     proceeding; anything red at baseline and still red here is already
     accounted for by T001's filed issue (if any).
- **Files**: none changed unless a parse failure requires a T005 fix.
- **Parallel?**: No — gates T008's push.
- **Notes**: This is checkpoint 1 of 4 total (0 = T002; 1 = T007, here,
  mandatory; 2 = T009, conditional on a boundary redraw; 3 = T010,
  mandatory/unconditional).

### Subtask T008 – Binding pre-push leak check + push branch #1 + dispatch run 1

- **Purpose**: Push the mission branch for the FIRST time and dispatch the
  baseline/timing-capture run (plan.md §I step 3 / §B point 1). This is a
  BUILD/IMPLEMENT-phase action — nothing before this subtask pushes or
  dispatches anything.
- **Steps**:
  1. **BINDING PRE-PUSH CHECK (non-negotiable)**: run
     `git log -p main..HEAD | grep -cE '/home/|/tmp/'` and confirm it prints
     `0`. **If it prints anything other than 0, STOP.** Do not push. Find and
     fix the leaking content (this repo is public; an absolute local path
     already leaked into a mission artifact once in this mission — the file
     CONTENT was redacted first, and the OS username was then also removed
     from git HISTORY via an orchestrator-authorized rewrite, carried out as
     part of this mission's own remediation work, of this unpushed branch on
     2026-09-27; see tasks.md's "Known Issue" section for the full,
     now-remediated record). Only proceed once the count is 0 or the
     fallback clause immediately below applies.

     > If the count is nonzero, trace every hit to its introducing commit
     > (`git show <sha> | grep -nE '/home/|/tmp/'` for each commit in
     > `main..HEAD`) and classify it per tasks.md's "Known Issue —
     > tasks-phase git-history leak" section: (a) the one already-known real
     > leak (pre-rewrite commits `afcf3bcd6`/`13dc5d966` — REMEDIATED: an
     > orchestrator-authorized history rewrite, carried out as part of this
     > mission's own remediation work on 2026-09-27, already removed this
     > leak from git history, giving every commit on the branch a new hash,
     > so those two SHAs are dangling/non-ancestor and kept here only as a
     > historical record, not as current commit references) — do NOT expect
     > to see this leak reappear, and do NOT attempt another history rewrite
     > yourself under any circumstance; or (b) a self-referential quotation
     > of this very check's own regex pattern appearing in prose (an
     > open-ended, growing category by design — never enumerate it by SHA).
     > Do not compare the total against any fixed number; only the per-commit
     > trace matters. If every hit classifies as (b), or matches the
     > already-remediated (a) pattern in the historical record above, this is
     > expected and not a defect for you to fix. If instead you find a hit
     > that is NEITHER — a real path under the operator's home directory
     > that traces to neither category — that is a genuinely NEW leak: fix
     > the file content in a new commit, then re-run the check and re-trace
     > every hit again; if any hit still fails to
     > classify as (a) or (b), STOP and escalate to the operator with the
     > specific commit SHA(s) rather than attempting any rebase/amend/reset
     > yourself.
  2. Re-verify the write-scope/open-PR overlap check from `tasks.md`:
     `gh pr list --repo spec-kitty/spec-kitty --state open --limit 100 --json
     number,files`, re-checking each open PR's changed-file list against
     `.github/workflows/ci-nightly.yml`, `tests/architectural/
     test_performance_marker_guard.py`, `scripts/ci/nightly_escalation.py`,
     and this WP's two new files. The mission-brief snapshot (7 open PRs, none
     colliding) has a short shelf life — do not trust it without re-running.
  3. Push the mission branch: `git push origin
     issue-4951-ci-nightly-interpreter-matrix-timeout` (or the resolved
     worktree's equivalent) — **never `main`**.
  4. Add IC-03's TEMPORARY per-shard `--collect-only` measurement step (or one
     extra always-run job) per plan.md §B point 1: `pytest --collect-only -q
     -m "fast or unit" <shard paths>` for each shard, recording collection
     counts alongside the timed run's real wall-clock. This is a throwaway,
     run-1-only addition — T010 removes it before run 2.
  5. Dispatch: `gh workflow run ci-nightly.yml --ref
     issue-4951-ci-nightly-interpreter-matrix-timeout -f mode=full` (or the
     GitHub UI equivalent). This is **run 1 of up to 3** — baseline/timing-capture.
  6. Record the run URL immediately (do not wait until T012) in
     `tracer-approach.md`.
- **Files**: `.github/workflows/ci-nightly.yml` (temporary scaffolding added).
- **Parallel?**: No — must not happen before T003-T007 are committed locally
  (campsite-clean + initial roster/guard/coverage-check authoring against the
  initial N/timeout guess).
- **Notes**: A failed run 1 (errors, force-cancelled for unrelated infra
  reasons, or otherwise fails to produce usable data) still counts against the
  up-to-3 total (plan.md §B point 4a) — its replacement consumes the NEXT
  slot, not an unbudgeted 4th attempt.

### Subtask T009 – Finalize N/timeout from run 1's real numbers

- **Purpose**: Replace the placeholder N/timeout guess with real,
  GitHub-hosted-runner-measured values (FR-002, NFR-001) — never the issue's
  local 24-core numbers, never `.github/ci-shard-timings.json`.
- **Steps**:
  1. Read each shard's real wall-clock (from its own job's step duration) and
     real collected node-id count (from T008's `--collect-only` step) from run
     1's logs/artifacts.
  2. Compute `timeout-minutes = ceil(real_wallclock_minutes * 1.3)` at
     minimum, `* 1.5` if the real wall-clock is close to a round number or
     historically variable (mirroring the e2e/performance/stress jobs'
     precedent headroom).
  3. If any shard's real wall-clock shows a badly-imbalanced partition (e.g.
     one shard takes ~3x another), redraw the shard boundaries: this changes
     that shard's `paths`/`--ignore` arguments directly on the `run:` line,
     not just a numeric value. Update both the roster
     (`INTERPRETER_SHARDS`) and the workflow to match.
  4. **If you redrew boundaries in step 3**, re-run T002/T007's parseability
     check again now (checkpoint 2 of 4 — conditional; this checkpoint fires
     ONLY because you redrew boundaries in step 3, do not skip it if you
     touched `run:`-line content here).
  5. Re-run the full local gate set (T007's steps 3-4) against the finalized
     shape.
- **Files**: `.github/workflows/ci-nightly.yml`,
  `tests/architectural/_interpreter_shard_roster.py`.
- **Parallel?**: No — depends on T008's dispatch-run data.
- **Notes**: This is exactly what NFR-006's "auditable methodology" requires —
  document the real numbers and the redraw rationale (if any) in
  `tracer-design-decisions.md` so a future reader can reproduce the split.

### Subtask T010 – Remove IC-03's temporary scaffolding; unconditional parseability re-check

- **Purpose**: Remove the throwaway `--collect-only` measurement step/job
  before run 2 is dispatched — it must not ship in the shape validated by run
  2 or opened in the PR (plan.md §I step 4a).
- **Steps**:
  1. Remove the temporary per-shard `--collect-only` step/job T008 added.
  2. Confirm its absence: `grep -n -- '--collect-only'
     .github/workflows/ci-nightly.yml` must return no hits (the permanent
     per-shard `pytest` invocations never use `--collect-only`).
  3. **Re-run the parseability check UNCONDITIONALLY here** (checkpoint 3 of
     4, mandatory/unconditional) — this is ALWAYS required, regardless of
     whether T009 redrew boundaries (checkpoint 2), because this step's own
     scaffolding-removal edit touches `run:`-line-adjacent content. Relying on
     T009's conditional checkpoint 2 alone would miss a parse regression this
     step's own edit could introduce.
- **Files**: `.github/workflows/ci-nightly.yml`.
- **Parallel?**: No — precedes T011's push/dispatch of run 2.
- **Notes**: Do not proceed to T011 until both the grep-for-`--collect-only`
  check and the parseability re-check are clean.

### Subtask T011 – Binding pre-push leak check + push #2 + dispatch run 2; conditional run 3

- **Purpose**: Dispatch the validation run against the finalized shard split,
  and — only if genuinely needed — the spare run, under the explicit
  never-a-4th-run stop rule (plan.md §I steps 5-6 / §B points 3-4-4a).
- **Steps**:
  1. **BINDING PRE-PUSH CHECK again**: `git log -p main..HEAD | grep -cE
     '/home/|/tmp/'` must print `0` before this push too. STOP and fix if
     nonzero, or apply the fallback clause immediately below.

     > If the count is nonzero, trace every hit to its introducing commit
     > (`git show <sha> | grep -nE '/home/|/tmp/'` for each commit in
     > `main..HEAD`) and classify it per tasks.md's "Known Issue —
     > tasks-phase git-history leak" section: (a) the one already-known real
     > leak (pre-rewrite commits `afcf3bcd6`/`13dc5d966` — REMEDIATED: an
     > orchestrator-authorized history rewrite, carried out as part of this
     > mission's own remediation work on 2026-09-27, already removed this
     > leak from git history, giving every commit on the branch a new hash,
     > so those two SHAs are dangling/non-ancestor and kept here only as a
     > historical record, not as current commit references) — do NOT expect
     > to see this leak reappear, and do NOT attempt another history rewrite
     > yourself under any circumstance; or (b) a self-referential quotation
     > of this very check's own regex pattern appearing in prose (an
     > open-ended, growing category by design — never enumerate it by SHA).
     > Do not compare the total against any fixed number; only the per-commit
     > trace matters. If every hit classifies as (b), or matches the
     > already-remediated (a) pattern in the historical record above, this is
     > expected and not a defect for you to fix. If instead you find a hit
     > that is NEITHER — a real path under the operator's home directory
     > that traces to neither category — that is a genuinely NEW leak: fix
     > the file content in a new commit, then re-run the check and re-trace
     > every hit again; if any hit still fails to
     > classify as (a) or (b), STOP and escalate to the operator with the
     > specific commit SHA(s) rather than attempting any rebase/amend/reset
     > yourself.
  2. Re-verify the open-PR write-scope overlap again (same command as T008
     step 2) — PRs open and close continuously; do not reuse T008's answer.
  3. Push the amended branch (finalized shard shape from T009/T010).
  4. Dispatch **run 2 — validation**: `gh workflow run ci-nightly.yml --ref
     issue-4951-ci-nightly-interpreter-matrix-timeout -f mode=full`.
  5. Confirm: every shard reaches `success`/`failure` — never `cancelled` by
     its own `timeout-minutes` (SC-001/SC-002); the coverage-completeness
     check passes locally and its numbers cross-check against the dispatch
     run's real per-shard collection counts; suite-key uniqueness holds
     (verified locally, C-005); each shard's escalation call is confirmed
     functional by inspecting the run's logs for the `nightly_escalation.py`
     step's printed outcome.
  6. Re-check pre-existing-failure classification per T001 (re-run `gh issue
     view 3284` and search for newer open issues) — do not trust T001's
     snapshot; a shard failure matching #3284's historical test list would
     indicate a REGRESSION of an already-closed defect, not a fresh baseline.
  7. **Conditional run 3 (spare)** — dispatch ONLY if run 2 surfaces a
     fixable issue a second attempt can plausibly resolve (a mis-sized
     `timeout-minutes` needing one more real number, a coverage gap from a
     boundary needing redrawing, or a transient escalation API error). Repeat
     the binding pre-push check and open-PR re-check before this push too, if
     any code changes are involved.
  8. **Explicit stop rule (non-negotiable)**: if run 2 fails in a way run 3
     cannot plausibly fix (a structural defect in the shard design itself),
     OR run 3 is also exhausted without success, OR a 4th run would be needed
     for ANY reason — **STOP and escalate to the operator**. **Never dispatch
     a 4th run under any circumstance in this mission.** Note: a failed run 1
     (T008) that never produced usable data already consumed a slot per
     plan.md §B point 4a — if that happened, "run 2" in this subtask is
     actually the renumbered validation attempt, and the spare slot may
     already be gone; recompute the remaining budget accordingly before
     dispatching anything here.
- **Files**: `.github/workflows/ci-nightly.yml` (only if run 3 requires a
  fix).
- **Parallel?**: No — depends on T010's clean scaffolding removal.
- **Notes**: This subtask is the ONLY place run 2 and (conditionally) run 3
  are dispatched. Do not dispatch either from any other subtask.

### Subtask T012 – Record dispatch evidence

- **Purpose**: Durable evidence recording (NFR-005) — every dispatched run's
  URL and every shard's conclusion must be recorded before the mission is
  considered complete, never left as a verbal claim.
- **Steps**:
  1. In the PR body (once opened — see T013), add a "Dispatch evidence"
     heading listing every run's URL and every shard job's conclusion.
  2. ALSO record the same in
     `kitty-specs/ci-nightly-interpreter-matrix-45min-timeout-01M3G17F/tracer-approach.md`
     (this is the pre-authorized out-of-map edit noted in Context &
     Constraints above — a one-line rationale, "recording dispatch-run
     evidence per NFR-005," suffices).
  3. Do this BEFORE marking the PR `ready-for-squad`.
- **Files**: `tracer-approach.md` (out-of-map, pre-authorized), PR body (not a
  repo file).
- **Parallel?**: No — depends on T011's dispatch results existing.
- **Notes**: This is required regardless of whether run 3 was needed —
  record run 1's and run 2's (and run 3's, if dispatched) evidence together.

### Subtask T013 – Final leak check + PR-overlap re-check + open the PR

- **Purpose**: Open the PR targeting `main` with the full local gate set
  green, scaffolding-removal confirmed, and evidence recorded (plan.md §I
  step 8).
- **Steps**:
  1. **BINDING PRE-PUSH CHECK, final time**: `git log -p main..HEAD | grep
     -cE '/home/|/tmp/'` must print `0` before this final push. STOP and fix
     if nonzero, or apply the fallback clause immediately below.

     > If the count is nonzero, trace every hit to its introducing commit
     > (`git show <sha> | grep -nE '/home/|/tmp/'` for each commit in
     > `main..HEAD`) and classify it per tasks.md's "Known Issue —
     > tasks-phase git-history leak" section: (a) the one already-known real
     > leak (pre-rewrite commits `afcf3bcd6`/`13dc5d966` — REMEDIATED: an
     > orchestrator-authorized history rewrite, carried out as part of this
     > mission's own remediation work on 2026-09-27, already removed this
     > leak from git history, giving every commit on the branch a new hash,
     > so those two SHAs are dangling/non-ancestor and kept here only as a
     > historical record, not as current commit references) — do NOT expect
     > to see this leak reappear, and do NOT attempt another history rewrite
     > yourself under any circumstance; or (b) a self-referential quotation
     > of this very check's own regex pattern appearing in prose (an
     > open-ended, growing category by design — never enumerate it by SHA).
     > Do not compare the total against any fixed number; only the per-commit
     > trace matters. If every hit classifies as (b), or matches the
     > already-remediated (a) pattern in the historical record above, this is
     > expected and not a defect for you to fix. If instead you find a hit
     > that is NEITHER — a real path under the operator's home directory
     > that traces to neither category — that is a genuinely NEW leak: fix
     > the file content in a new commit, then re-run the check and re-trace
     > every hit again; if any hit still fails to
     > classify as (a) or (b), STOP and escalate to the operator with the
     > specific commit SHA(s) rather than attempting any rebase/amend/reset
     > yourself.
  2. Final re-verification of the write-scope/open-PR overlap
     (`gh pr list --repo spec-kitty/spec-kitty --state open --limit 100
     --json number,files`), immediately before this push — do not reuse an
     earlier subtask's answer.
  3. Push (if any changes remain unpushed from T011/T012).
  4. Open the PR: target `main` from the mission branch
     (`issue-4951-ci-nightly-interpreter-matrix-timeout`), with the full
     local gate set green (T007's ruff/architectural checks re-confirmed
     current), the T010 scaffolding-removal grep re-confirmed with no hits,
     and T012's evidence included in the PR body.
  5. Do NOT push to `main` directly and do NOT use `spec-kitty merge --push`.
- **Files**: none (PR creation only; no repo file changes expected here
  beyond what T011/T012 already made).
- **Parallel?**: No — this is the final subtask.
- **Notes**: This mission ships as ONE PR (spec-kitty's default, confirmed
  applicable per plan.md §I). Nothing in this WP marks the PR "ready-for-squad"
  before T012's evidence is recorded.

---

## Test Strategy

- `pytest tests/architectural/test_performance_marker_guard.py -q` — must pass,
  including all new non-vacuity and suite-key mutation tests.
- `pytest tests/architectural/test_interpreter_shard_coverage.py -q` — must
  pass, including both required mutation tests (dropped-boundary and
  deleted-shard).
- `pytest tests/architectural/ -q` (full suite, C-005) — run at T007, T009
  (conditionally), and again before T013's PR open.
- `ruff check .` and `ruff format --check .` (C-004) — zero issues on every
  touched Python file.
- Real `workflow_dispatch` runs (T008, T011) — the ONLY mechanism that can
  prove SC-001/SC-002; a unit test cannot fabricate GitHub-hosted-runner
  wall-clock.
- No compiler/typecheck step applies (this WP touches no `mypy`-checked
  surface per AGENTS.md's "Sonar Expectations"/"Code Style" sections; `mypy`
  does not run in this repo's CI at all — see charter/AGENTS.md).

## Risks & Mitigations

See `tasks.md`'s "Risks & Mitigations" section for the full list (shard
boundary drift, guard vacuity, local-number leakage into sizing, the 4th-run
prohibition, and the absolute-path-leak hazard). This prompt's per-subtask
guidance above embeds each mitigation at the exact point it applies.

## Review Guidance

- Confirm every row of plan.md §G's red-first table has a corresponding test
  in this diff, and that each test's mutation variant is present (not just
  the happy-path assertion).
- Confirm `_gate_coverage.py` was never edited (a diff touching that file is
  an immediate reject — it is explicitly out of scope).
- Confirm `.github/workflows/module-tests.yml` and
  `.github/ci-module-registry.yml` were never opened.
- Confirm the PR body's "Dispatch evidence" section names real run URLs and
  per-shard conclusions, not a paraphrase.
- Confirm every hit from `git log -p main..HEAD | grep -cE '/home/|/tmp/'`
  classifies per tasks.md's "Known Issue — tasks-phase git-history leak"
  section into one of two categories: (a) the one already-known real leak,
  now REMEDIATED via the 2026-09-27 orchestrator-authorized history rewrite
  carried out as part of this mission's own remediation work
  (pre-rewrite commits `afcf3bcd6`/`13dc5d966` — historical record only, no
  longer reachable/ancestor SHAs), or (b) a self-referential quotation of
  this check's own regex pattern in prose (an open-ended, growing category by
  design — do not expect a fixed count or enumerate it by SHA). A nonzero
  count at review time is EXPECTED for those already-known reasons and is
  not, by itself, a reviewable defect; any hit that classifies as NEITHER (a)
  nor (b) IS a reviewable defect — the leak check itself is not vacuous, and
  is not bypassable by an unclassifiable hit.
- Confirm no more than 3 `workflow_dispatch` runs were made on this branch
  total (`gh run list --workflow=ci-nightly.yml --branch
  issue-4951-ci-nightly-interpreter-matrix-timeout`).

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest
> first, newest last).

### How to Add Activity Log Entries

**When adding an entry**:

1. Scroll to the bottom of this Activity Log section
2. **APPEND the new entry at the END** (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – <action>`
4. Timestamp MUST be current time in UTC (check with `date -u
   "+%Y-%m-%dT%H:%M:%SZ"`)
5. Agent ID should identify who made the change (claude-sonnet-4-5, codex,
   etc.)

**Format**:

```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – <brief action description>
```

**Common mistakes (DO NOT DO THIS)**:

- Adding new entry at the top (breaks chronological order)
- Using future timestamps (causes acceptance validation to fail)
- Inserting in middle instead of appending to end

**Why this matters**: The acceptance system reads the LAST activity log entry
as the current state. If entries are out of order, acceptance will fail even
when the work is complete.

**Initial entry**:

- 2026-09-27T01:46:46Z – system – Prompt created.

---

### Updating Status

Status is managed via `status.events.jsonl`. Use `spec-kitty agent tasks
move-task WP01 --to <status>` to change WP status.
- 2026-09-27T10:26:17Z – claude – T001: baseline architectural-suite capture + pre-existing-failure classification, before any workflow-file edit.
- 2026-09-27T10:26:38Z – claude – T002: empirical gate-parseability re-derivation against the CURRENT ci-nightly.yml (checkpoint 0/4).
- 2026-09-27T10:26:40Z – claude – T003: campsite-clean commit rewriting the single-job's descriptive comments to describe the incoming shard shape.
- 2026-09-27T10:26:41Z – claude – T004: authored shard-identity roster + coverage-completeness/roster-diff test module, red-first against the not-yet-split workflow.
- 2026-09-27T10:26:42Z – claude – T005: authored the shard split in ci-nightly.yml against T004's initial N/timeout guess; updated nightly-summary's needs:.
- 2026-09-27T10:26:43Z – claude – T006: updated the architectural guard for dynamic shard enumeration, non-vacuity mutation tests, and suite-key-uniqueness assertion + its mutation tests.
- 2026-09-27T10:26:44Z – claude – T007: empirical gate-parseability re-derivation against the AUTHORED shard job YAML (checkpoint 1/4) + full local gate run.
- 2026-09-27T10:26:45Z – claude – T008: binding pre-push leak check + push branch #1 + dispatch run 1 (baseline/timing-capture, run 36294808024).
- 2026-09-27T10:26:47Z – claude – T009: finalized N/timeout from run 1's real numbers, redrew boundaries 3->6 shards (imbalanced); checkpoint 2/4 parseability re-check.
- 2026-09-27T10:26:48Z – claude – T010: removed run-1's temporary --collect-only scaffolding; unconditional checkpoint 3/4 parseability re-check.
- 2026-09-27T10:26:49Z – claude – T011: binding pre-push leak check + push #2 + dispatch run 2 (validation, run 36300726806); run 3 (spare) not dispatched per the explicit stop rule.
- 2026-09-27T10:26:50Z – claude – T012: recorded dispatch evidence (run URLs, per-shard timings/conclusions) in tracer-approach.md.
- 2026-09-27T10:26:51Z – claude – T013: binding pre-push leak check + final open-PR-overlap re-check; WP moved to for_review (cycle 1).
- 2026-09-27T10:27:10Z – claude – Fix-mode cycle 2: replaced vacuous coverage-completeness mutation tests (WP01-R1-001) with real guard-path controls; backfilled this Activity Log (WP01-R1-002); closed WP01-R1-003 pre-existing-failure disposition in tracer-design-decisions.md.
