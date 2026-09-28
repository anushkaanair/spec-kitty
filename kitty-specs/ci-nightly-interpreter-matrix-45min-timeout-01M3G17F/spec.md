# Mission Specification: Nightly interpreter-matrix leg completes within its time cap

**Mission Branch**: `issue-4951-ci-nightly-interpreter-matrix-timeout`
**Created**: 2026-09-27
**Status**: Draft
**Input**: GitHub issue #4951 (P1, `reliability`, `domain:ci`) — the nightly
`interpreter-matrix` (Python 3.13, nightly-only, FR-021) leg of
`ci-nightly.yml` cannot complete `pytest -m "fast or unit"` within its
45-minute job timeout on a GitHub-hosted runner, with or without `-n auto`. A
groom comment promoted the issue to `status:ready`; a claim comment opened
this mission.

## Summary

Two manual `workflow_dispatch` runs of `ci-nightly.yml` (used to verify
mission #4866's environment-pinning fix on a real runner) both show the
`interpreter-matrix` job's `pytest` step force-cancelled by the job's
`timeout-minutes: 45` cap before it produces a pass/fail verdict — once
serial, once with `-n auto`. This is a **third, distinct** defect from two
already-tracked issues on this leg (#4866: wrong-interpreter/wrong-extras
silent resync, now fixed; #3189: genuine 3.13 test-outcome divergence,
deferred and separate). Unlike those, this defect means the leg has **never**
produced a verdict on a GitHub-hosted runner in any configuration — sync
succeeds in ~2 seconds both times, but the suite itself never finishes before
the cap kills the job.

The operator's binding remedy (Clarifications, Q1) is to split the 3.13
suite into its own nightly-only shards inside `ci-nightly.yml`, each with a
budget sized from a fresh measurement, following the precedent set by mission
`ci-nightly-wallclock-budget-01M34HNZ` (PR #4948: perf/e2e/stress split into
three independently-budgeted jobs) and explicitly avoiding the broken
duration-weighted shard-balancing mechanism ledger entry SK-247 documents for
`.github/ci-module-registry.yml`. This mission does not touch that registry
or `module-tests.yml`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The interpreter-matrix leg produces a real pass/fail verdict within budget (Priority: P1)

As the Spec Kitty maintainer team, we want the nightly Python 3.13
`fast or unit` suite split into N independent, nightly-only shards — each
running a disjoint slice of the suite with its own `timeout-minutes` budget
sized from a fresh measurement — so the leg can actually finish and report a
genuine pass or fail, instead of racing a single 45-minute cap against the
whole suite and always losing.

**Why this priority**: P1 — the leg has never once produced a verdict on a
GitHub-hosted runner (two dispatches, two cancellations at the cap). Every
downstream FR-021 goal (interpreter-divergence visibility) is unreachable
while the leg cannot finish at all.

**Independent Test**: Dispatch `ci-nightly.yml` (`workflow_dispatch`,
`mode: full`) on the mission branch and observe N shard job entries, each
reaching a `success` or `failure` conclusion (never `cancelled` by its own
timeout).

**Acceptance Scenarios**:

1. **Given** the post-split workflow, **When** a nightly (or manually
   dispatched) run executes, **Then** every interpreter-matrix shard job
   completes with a `success` or `failure` conclusion before its own
   `timeout-minutes` elapses.
2. **Given** a shard whose slice of the suite is genuinely red, **When** that
   shard runs, **Then** only that shard fails (`fail-fast: false` preserved)
   and every other shard still reaches its own verdict.
3. **Given** the shard count N was sized from a fresh measured capture (not
   invented), **When** a reviewer asks "why N and why these boundaries",
   **Then** an in-repo comment or doc traces the answer to that capture, not
   to an unexplained constant.

---

### User Story 2 - The shard split is provably complete: zero overlap, zero gap (Priority: P1)

As the Spec Kitty maintainer team, we want a machine-checked guarantee that
the union of every shard's test selection equals the full
`pytest -m "fast or unit"` selection on Python 3.13, with no test collected
twice and no test collected by no shard, so a bad shard boundary is a loud
failure at CI time, never a silently shrinking nightly suite.

**Why this priority**: P1 — this repo's dominant failure mode is a code path
that reports success while silently doing less than it claims (see
Clarifications, Correction #1, on the provenance of this framing). A shard
split is exactly this hazard: it is trivial to draw boundaries that quietly
drop or duplicate tests while every individual shard still goes green.

**Independent Test**: Run two distinct checks. (1) The node-id
coverage-completeness check (FR-004, a pytest test or a dedicated workflow
step) — confirm it compares actual collected node-id sets, full selection
vs. the union of shard selections, not a manual review of directory lists
(this alone covers AC1-AC2). (2) The shard-identity roster diff (FR-016) —
confirm it compares the roster's declared shard names against
`ci-nightly.yml`'s `jobs:` keys and fails loudly, naming the specific
missing shard, when a shard is removed from the job list while remaining in
the roster (this is what covers AC3, which the node-id check alone cannot
prove). Together these two checks exercise the full AC1-AC3 range this
story requires.

**Acceptance Scenarios**:

1. **Given** the committed shard boundaries, **When** the coverage-
   completeness check runs, **Then** it reports the full `fast or unit`
   collection count on 3.13, the sum of each shard's collection count, and
   the deduplicated union count, and asserts all three imply zero gap and
   zero overlap.
2. **Given** a shard's selector is deliberately mutated to collect 0 tests,
   **When** the check runs, **Then** it fails loudly naming the empty shard —
   it never passes vacuously.
3. **Given** a shard is deliberately removed from the job list while it
   remains listed in the shard-identity roster (FR-016), **When** the check
   runs, **Then** a second, roster-based comparison — distinct from FR-004's
   node-id comparison, which alone proves only AC2 (a gap exists, not which
   shard produced it) — diffs the roster's shard names against the
   workflow's `jobs:` keys and fails loudly naming the missing shard.

---

### User Story 3 - A red shard escalates on its own, without merging into or masking another shard's signal (Priority: P2)

As the Spec Kitty maintainer team, we want each shard's
`scripts/ci/nightly_escalation.py` call keyed by a distinct `--suite-key`, so
a red shard opens or updates its own standing `priority:P0` issue — never
merged with another shard's escalation, and never silently skipped.

**Why this priority**: P2 — depends on User Story 1 existing (shards must
exist before they can escalate independently), but is the mechanism that
makes a post-split red actually actionable by a human, per the existing FR-007
escalation contract this mission extends rather than replaces.

**Independent Test**: Force one shard red in a dispatch run; confirm exactly
one new/updated `priority:P0` issue appears, carrying that shard's suite-key
marker, and no other shard's escalation issue is touched.

**Acceptance Scenarios**:

1. **Given** N shards each escalate with a distinct `--suite-key`, **When**
   shard 2 is red and the rest are green, **Then** only shard 2's escalation
   issue is opened/updated; shards 1, 3..N make no escalation API calls that
   open or touch an issue.
2. **Given** shard 2's issue already exists (open) from a prior red run,
   **When** shard 2 is red again, **Then** the existing issue is commented on,
   not duplicated.
3. **Given** shard 2 recovers (green) on a later run, **Then** its escalation
   issue is closed, independent of any other shard's state.

---

### User Story 4 - The architectural guard cannot be silently defeated by a future shard removal (Priority: P2)

As the Spec Kitty maintainer team, we want
`tests/architectural/test_performance_marker_guard.py`'s hardcoded
`"interpreter-matrix"`-as-a-single-job assertions updated to the post-split
shape, in a way that is provably non-vacuous — it must fail if a future
change silently drops a shard or reverts to one job — so the guard keeps
doing its job instead of becoming inert scaffolding.

**Why this priority**: P2 — a guard that still says "pass" after this
mission's structural change, without ever having been proven capable of
failing against a regression of that exact change, is Standing Order #5's
named anti-pattern ("a gate-unmask cannot self-validate").

**Independent Test**: After updating the guard, revert the job list to a
single shard (or delete one shard) in a scratch copy of the workflow YAML fed
to the guard's parsing logic, and confirm the guard's assertions fail against
that mutation.

**Acceptance Scenarios**:

1. **Given** the updated guard enumerates the real shard job names (or
   discovers them dynamically), **When** `pytest tests/architectural/test_performance_marker_guard.py`
   runs against the post-split `ci-nightly.yml`, **Then** it passes.
2. **Given** a mutated copy of the workflow with one shard job deleted,
   **When** the guard's job-presence assertion is run against that mutated
   copy, **Then** it fails.
3. **Given** the same guard file, **When**
   `test_nightly_workflow_never_triggers_on_pull_request` and
   `test_no_pull_request_workflow_selects_performance_or_interpreter_jobs`
   run, **Then** both still pass unchanged — the split introduces no
   `pull_request` trigger anywhere.

---

### Edge Cases

- What happens if a shard's pytest selection collects 0 tests? The nightly
  workflow must fail loudly (User Story 2, FR-005) — never a silent pass.
- What happens if a shard is missing entirely from the job list while its
  intended test files still exist on disk? FR-004's node-id comparison alone
  can only show a gap exists, not which shard produced it (a deleted job
  leaves nothing in the workflow file to read a shard name from); the
  roster-based comparison (FR-016) is what fails loudly naming the specific
  missing shard, not merely under-reporting the total test count.
- What happens if two shards' selectors overlap (the same test collected by
  more than one shard)? The coverage-completeness check must fail loudly
  naming the duplicate node id(s) — silently running a test twice wastes
  budget and can mask a flake as a pass in one shard while it fails in
  another.
- What happens to a nightly run that is already scheduled or mid-flight when
  this change merges? `ci-nightly.yml`'s `on:` block carries only `schedule`
  and `workflow_dispatch` (verified directly against the workflow file, lines
  40-54 as read 2026-09-27) — no `pull_request` or `push` trigger exists, so
  no in-flight run is retroactively affected. The next scheduled `03:17 UTC`
  cron (or the next manual dispatch) simply picks up the new job graph.
- What happens if the fresh 3.13 measurement capture (Q2) produces a very
  different collected-test count or per-shard wall-clock than the issue's
  local 24-core numbers (~5036s serial / ~475.87s with `-n auto`, ~34,835
  tests collected)? The shard sizing must use the freshly measured
  GitHub-hosted-runner numbers, never the local-machine figures — the issue
  itself flags those as "context only, not a substitute for the CI
  observation."
- What happens if pre-existing test failures are encountered while measuring
  or validating the shard split? Per the charter's binding Pre-existing
  Failure Reporting Rule, a GitHub issue must be filed (command run, failure
  summary, why judged pre-existing) before treating those failures as
  accepted baseline. Issue #3284 ("main full suite has 23 untracked failures
  and 2 errors after bootstrap prewarm") is the specific known-red-main issue
  named in this mission's dispatch mandate; re-verified 2026-09-27 via
  `gh issue view 3284`, it is CLOSED (closed 2026-09-08), so it is not itself
  a currently-open explanation for a Q2 dispatch-run shard failure. The
  plan/implementation phase must re-check its live state (and search for any
  newer open Pre-existing Failure issue) at Q2 dispatch time rather than
  trusting this note, before filing a new issue or accepting a shard as
  validated-green — a shard failure matching #3284's historical test list
  would indicate a regression of an already-closed defect, not a fresh
  baseline to wave through. #3283 ("pytest shared test-venv lock times out
  before editable install completes") is a separate, also-closed issue
  relevant only to LOCAL `tests/architectural/` runs the plan/implementation
  phase might perform, not to the GitHub-hosted dispatch runs (which use
  per-shard dedicated venvs and are not exposed to a local shared-lock).
- What happens if another currently-open PR touches `ci-nightly.yml`,
  `.github/ci-module-registry.yml`, or `module-tests.yml` before this
  mission's PR merges? Re-verified 2026-09-27: `gh pr list` shows 4 open PRs
  (#4995, #5009, #5028, #5137), and none of their changed-file lists touch
  any of those three paths. This must be re-checked again at plan/implement
  time since PRs open and close continuously.
- What happens to `nightly-summary`'s aggregate report if a shard's job is
  renamed or added? `needs:` and the result-echo step must name every current
  shard explicitly (FR-006) — a stale or partial `needs:` list is itself a
  silent-success hazard this mission must not introduce.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Title | User Story | Priority | Status | Delivery | No-op passable? |
|----|-------|------------|----------|--------|----------|-----------------|
| FR-001 | Split `interpreter-matrix` into N nightly-only shards | As a Spec Kitty maintainer, I want the single `interpreter-matrix` job split into N independent nightly-only shards, each running a disjoint slice of `pytest -m "fast or unit"` on Python 3.13 with its own `timeout-minutes`, so the leg can complete instead of racing one 45-minute cap against the whole suite. | High | Open | [build] | no |
| FR-002 | Size N and each shard's budget from a fresh measured capture | As a Spec Kitty maintainer, I want the shard count N and each `timeout-minutes` value derived from a fresh, real timing capture of the 3.13 `fast or unit` suite on a GitHub-hosted runner — not the issue's local 24-core numbers, not `.github/ci-shard-timings.json`, and not an invented number — so sizing reflects the runner class this leg actually executes on. | High | Open | [build] | no |
| FR-003 | Shard boundaries drawn by test module/file/directory, never by the SK-247 mechanism | As a Spec Kitty maintainer, I want shard boundaries assigned by a simple, auditable test module/file/directory partition rather than by reusing `.github/ci-module-registry.yml`'s `shard_count` LPT bin-packing, so this remedy does not inherit the balancing mechanism ledger entry SK-247 records as silently falling back to uniform/count-based weighting for 20 of 21 registry modules. | High | Open | [build] | no |
| FR-004 | Coverage-completeness is a falsifiable, machine-checked gate | As a Spec Kitty maintainer, I want a check that collects the real node-id set each shard's selector would run and asserts their union equals the full `fast or unit` collection on 3.13 with zero duplicates and zero gaps, so a wrong shard boundary is a loud CI failure, never a silent partial run. | High | Open | [build] | no |
| FR-005 | A zero-collection or missing shard is a visible failure, never a silent pass | As a Spec Kitty maintainer, I want the nightly workflow to fail loudly if any declared shard's selection collects 0 tests, or if the job list omits a shard the shard-identity roster (FR-016) expects, so an empty or dropped shard can never masquerade as "nothing to report." | High | Open | [build] | no |
| FR-006 | Update `nightly-summary`'s `needs:` to the N new shard job names | As a Spec Kitty maintainer, I want the terminal `nightly-summary` job's `needs:` list and result-echo step to name every new shard job in place of the single `interpreter-matrix` dependency, so the full-mode summary never silently omits a shard's result. | High | Open | [build] | no |
| FR-007 | Preserve the pass/exit-5-skip/fail-loud convention per shard | As a Spec Kitty maintainer, I want every shard job to keep the existing `set +e` capture + `if: always()` + terminal fail-loud pattern (pytest exit 0 or 5 both pass; any other non-zero exit fails the shard), so the split does not regress the run-all-regardless posture the single job already had. | High | Open | [ratchet] | yes — paired with FR-010's updated guard, which fails if any shard's terminal step stops excluding exit 5 |
| FR-008 | Preserve the per-interpreter dedicated venv pinning across every shard | As a Spec Kitty maintainer, I want every shard job to independently run `uv sync --frozen --all-extras --python "3.13"` and `uv run --frozen --python "3.13" --all-extras pytest ...` under its own `UV_PROJECT_ENVIRONMENT: .venv-py3.13`, so splitting into shards does not reopen the wrong-interpreter/wrong-extras silent-resync defect #4866 fixed. | High | Open | [ratchet] | yes — paired with a per-shard sync-step-presence assertion (a shard missing the sync step is the positive control) |
| FR-009 | Update the guard's hardcoded single-job `interpreter-matrix` assertions | As a Spec Kitty maintainer, I want the `tests/architectural/test_performance_marker_guard.py` assertions that hardcode the literal job key `"interpreter-matrix"` — `test_nightly_suite_steps_are_fail_loud` and `test_nightly_fail_loud_step_treats_marker_empty_exit_5_as_non_failing`'s `for job_name in ("performance", "e2e", "stress", "interpreter-matrix")` loop, plus `test_nightly_workflow_houses_performance_and_interpreter_jobs`'s single-job-with-a-`python-version`-matrix assertion — updated to enumerate (or dynamically discover) the new shard job names, so the guard keeps enforcing the same fail-loud/exit-5/job-presence guarantees against the post-split shape. | High | Open | [build] | no |
| FR-010 | The updated guard is provably non-vacuous against a dropped shard or a reverted single job | As a Spec Kitty maintainer, I want the updated guard assertions demonstrably to fail if a future change silently drops one shard from the job list, or reverts the split to a single `interpreter-matrix` job, so the guard cannot merely have been satisfied by construction (Standing Order #5). | High | Open | [build] | no |
| FR-011 | Per-shard escalation with a distinct, non-colliding suite-key | As a Spec Kitty maintainer, I want each shard's `scripts/ci/nightly_escalation.py` call to pass a distinct `--suite-key` (keyed by shard identity, not only by interpreter version) so a red shard opens/updates its own standing `priority:P0` issue, no two shards' escalations ever merge into one issue, and no shard is silently dropped from escalation coverage. | High | Open | [build] | no |
| FR-012 | `fail-fast: false` preserved across the shard set | As a Spec Kitty maintainer, I want the shard jobs to run under `fail-fast: false` semantics so one red shard never cancels the others mid-run, mirroring the #4948 perf/e2e/stress precedent. | High | Open | [ratchet] | yes — paired with a two-shard scenario where one is forced red and the other's completion is independently asserted |
| FR-013 | No `pull_request` trigger introduced by the split | As a Spec Kitty maintainer, I want `test_nightly_workflow_never_triggers_on_pull_request` and `test_no_pull_request_workflow_selects_performance_or_interpreter_jobs` to keep passing unchanged after the split, so none of the new shard jobs (or the workflow itself) gains a `pull_request` trigger putting any shard on the per-PR blocking path. | High | Open | [ratchet] | yes — paired with the existing `FORBIDDEN_PR_PATH_TOKENS` list, which already names the literal token `"interpreter-matrix"` |
| FR-014 | Up to 3 measurement/validation dispatch runs produce durable evidence | As a Spec Kitty maintainer, I want up to 3 manual `workflow_dispatch` runs of `ci-nightly.yml` on this mission's branch (a baseline timing-capture run, a validation run, one spare — operator decision Q2) with each shard's conclusion and the run URL recorded in the PR description or a mission tracer file, since the leg's real acceptance criterion — a genuine pass/fail verdict produced within budget — cannot be proven by a unit test alone. | High | Open | [build] | no |
| FR-015 | Suite-key uniqueness is a machine-checked, falsifiable assertion, not a manual review | As a Spec Kitty maintainer, I want `tests/architectural/test_performance_marker_guard.py` extended to parse every shard's literal `--suite-key` argument out of the committed `ci-nightly.yml` (plus the existing `performance`/`e2e`/`stress` jobs' keys) and assert the resulting set is pairwise distinct, backed by a mutation test (a scratch copy of the workflow with two shards' `--suite-key` values deliberately made identical) proving the assertion can fail, so a copy-paste suite-key collision across shards — an easy mistake given the current single-job step's key literal `"interpreter-${{ matrix.python-version }}"` — is caught by CI instead of relying on the human inspection NFR-003 previously specified. | High | Open | [build] | no |
| FR-016 | A shard-identity roster distinguishes a missing shard from an empty one | As a Spec Kitty maintainer, I want an in-repo shard-identity roster (shard name -> its assigned test paths/selector) that the coverage-completeness check reads independently of `ci-nightly.yml`'s job list, and diffs against the workflow's `jobs:` keys, so a shard deleted from the job list entirely (User Story 2 AC3) is detected and named distinctly from a shard that is present in the job list but whose selector collects 0 tests (AC2) — a distinction FR-004's node-id set arithmetic alone cannot make, since a deleted job leaves nothing in the workflow file to read a shard name from. | High | Open | [build] | no |
| FR-017 | Plan phase must evaluate reusing `_gate_coverage.py`'s coverage-oracle substrate for both checks | As a Spec Kitty maintainer, I want the plan phase to read `tests/architectural/_gate_coverage.py`'s `BaselineTarget` / `collect_real_union_for_target` / `gates_for_target` mechanism — `ci-nightly.yml` is already a member of its `WORKFLOW_FILES`; `collect_real_union_for_target` is purpose-built so that unioning every matching job's real `pytest --collect-only` selection means "a shard split alone (same total coverage, more legs) cannot false-red" its coverage oracle; and `gates_for_target` already raises loudly, naming the stale target, when a `BaselineTarget`'s `(workflow, job)` pairing no longer resolves to any parsed gate (i.e. the job was renamed or deleted) — and record an explicit reuse-vs-documented-rejection decision covering BOTH FR-004/NFR-002 (the node-id coverage-completeness check) AND FR-016 (the shard-identity roster's deleted-shard detection, which `gates_for_target`'s raise-loudly-on-zero-gates behavior is directly relevant to), as one combined decision or two paired decisions (mirroring the SK-247/`capture_shard_timings.py` rejection write-up below), plus confirm each new shard's `pytest` invocation in `ci-nightly.yml` remains one of the shapes `_gate_coverage.py`'s `parse_workflow` recognizes — so the split neither silently builds a bespoke roster mechanism duplicating this canonical substrate, nor breaks or mis-models the pre-existing repo-wide coverage oracle that C-005's full `tests/architectural/` run will exercise. See SC-010. | High | Open | [build] | no |

### Non-Functional Requirements

| ID | Title | Requirement | Category | Priority | Status |
|----|-------|-------------|----------|----------|--------|
| NFR-001 | Each shard's budget has real headroom over its measured wall-clock | Each shard's `timeout-minutes` must be at least that shard's own measured completion wall-clock (from the Q2 baseline capture) plus headroom (comparable to the ~1.3-1.5x headroom the e2e/performance jobs already use), never copied unchanged from the old single-job 45-minute cap without re-derivation. | Performance | High | Open |
| NFR-002 | Coverage-completeness is collection-count based, not eyeballed | The zero-overlap/zero-gap check (FR-004) must compare actual pytest-collected node-id sets between the full selection and the union of shard selections — never a manual review of directory lists or an assumption that a partition "looks complete." | Reliability | High | Open |
| NFR-003 | Escalation dedup correctness across shards | For any single red shard, exactly one open `priority:P0` issue exists for that shard's `--suite-key` after the run — no cross-shard merge, no missing escalation — proven by FR-015's automated `--suite-key` uniqueness assertion over the committed `ci-nightly.yml` (mutation-tested per Standing Order #5), never by manually inspecting each shard's escalation step. | Reliability | High | Open |
| NFR-004 | N-times checkout+sync cost is accepted | Splitting into N shards means `actions/checkout` + `setup-python` + `uv sync --frozen --all-extras --python 3.13` now runs N times instead of once for this leg; this is accepted, documented cost (mirrors the #4948 precedent's NFR-005), not a defect to eliminate in this mission. | Performance | Low | Open |
| NFR-005 | Dispatch evidence recorded durably, not just claimed | The pre-merge `workflow_dispatch` run(s)' URLs and every shard job's conclusion must be recorded in the PR description or a mission tracer file before the mission is considered complete — never left as a verbal claim a later reviewer must trust. | Reliability | Medium | Open |
| NFR-006 | Shard-sizing methodology is auditable in-repo | Whatever mechanism the plan phase chooses to assign test modules/files/directories to shards must be documented with an in-repo comment or short doc detailed enough that a future reader can reproduce or re-derive the split without re-reading this mission's history. | Process | Medium | Open |

### Constraints

| ID | Title | Constraint | Category | Priority | Status |
|----|-------|------------|----------|----------|--------|
| C-001 | No `pull_request` trigger anywhere in the split | None of the new shard jobs, and no workflow-level trigger change, may cause `ci-nightly.yml` (or any workflow) to run an interpreter-matrix shard on a `pull_request` event. Enforced by `tests/architectural/test_performance_marker_guard.py`. | Technical | High | Open |
| C-002 | The shared per-PR module-sharding infrastructure is explicitly untouched | `.github/workflows/module-tests.yml` and `.github/ci-module-registry.yml` are NOT modified by this mission. The interpreter leg's shard sizing must be self-contained to `ci-nightly.yml` (plus, if a new measurement helper is needed, a new script under `scripts/ci/`), not an extension of the registry's `shard_count` mechanism, which ledger entry SK-247 records as producing uniform/count-based fallback weighting for 20 of 21 modules because committed durations and live collected node ids are paired positionally and drift out of sync. | Technical | High | Open |
| C-003 | Design-phase dispatch authorization is plan/implementation-phase only | This spec does not authorize dispatching or pushing anything during spec authoring. Operator decision Q2's up-to-3-dispatch-run authorization applies starting at the plan/implementation phase. Reading existing run logs/timings already on GitHub (`gh run view` / `gh api`) is fine at any phase. | Process | High | Open |
| C-004 | `ruff check .` / `ruff format --check .` apply to touched Python | Any Python file this mission touches (e.g. `tests/architectural/test_performance_marker_guard.py`, a possible new measurement helper under `scripts/ci/`) must pass `ruff check .` and `ruff format --check .` with zero issues. | Technical | Medium | Open |
| C-005 | Full `tests/architectural/` suite is a required gate | Because this mission changes a cross-cutting workflow file and its guard test, the plan's gate selection must include the full `tests/architectural/` suite (not a narrow subset), per this repo's cross-cutting-change test policy. | Technical | Medium | Open |
| C-006 | SonarCloud `sonar-pr` is reported, not required | The `sonar-pr` job in `ci-aggregate.yml` runs `continue-on-error` and is excluded from the terminal `aggregate-gate`; this mission is aware of it but does not need to satisfy it as a blocking gate. | Technical | Low | Open |

### Key Entities

- **Nightly interpreter shard (post-split)**: one of N independent GitHub
  Actions jobs (or matrix legs) in `ci-nightly.yml`, each running a disjoint
  slice of `pytest -m "fast or unit"` on Python 3.13, with its own
  `timeout-minutes`, its own checkout/setup-python/install-uv/sync/run/
  upload/escalate/fail-loud steps, and its own `--suite-key`.
- **Coverage-completeness check**: the test or workflow step (FR-004) that
  proves the union of every shard's collected node-id set equals the full
  `fast or unit` collection on 3.13, with zero duplicates and zero gaps.
- **Shard-sizing capture**: the fresh, real timing measurement (Q2's up-to-3
  dispatch runs) that the plan phase uses to choose N and each shard's
  `timeout-minutes` — explicitly not `.github/ci-shard-timings.json` or the
  local 24-core numbers quoted in issue #4951.
- **Shard-identity roster** (FR-016): a small in-repo declaration (shard name
  -> its assigned test paths/selector) that the coverage-completeness check
  reads independently of `ci-nightly.yml`'s job list, so a shard's absence
  from the job list is detectable by diffing the roster's shard names
  against the workflow's `jobs:` keys — distinct from, and not derivable
  from, a present-but-empty shard's collected node-id count being 0.

## Clarifications

This section records binding operator decisions, verified corrections, and
the SK-247 rejection rationale as durable spec content, not only as prompt
context that is lost when a session's context rolls.

### Binding operator decisions (2026-09-27, the operator)

**Q1 (remedy) — "Nightly-only shards (Recommended)"**: *"Split the 3.13 suite
into its own shards inside `ci-nightly.yml`, sized from fresh timings. Leaves
the shared per-PR `module-tests.yml` untouched. Follows the #4948 precedent
(perf/e2e/stress each got their own job) and avoids the broken shard
balancing recorded in ledger SK-247."* This is FR-001 through FR-010's basis.

**Q2 (measurement) — "Yes, up to 3 runs (Recommended)"**: *"the mission may
push its feature branch and dispatch `ci-nightly.yml` on it via
`workflow_dispatch`: a baseline/timing-capture run, a validation run, and one
spare. Results go into the PR body as evidence. More than 3 comes back to the
operator."* This is FR-014's basis; it authorizes the plan/implementation
phase, not spec authoring (C-003).

### Why Option B (reuse `module-tests.yml`'s sharding) was rejected

Ledger entry SK-247 (verified first-hand in mission
`ci-nightly-wallclock-budget-01M34HNZ`) records that
`.github/ci-module-registry.yml`'s claim — that `shard_count` is chosen by
greedy LPT bin-packing of *measured* per-test durations — is **false for 20
of the registry's 21 modules**. The producer
(`scripts/ci/capture_shard_timings.py`) pairs durations to node ids
**positionally** (the committed `.github/ci-shard-timings.json` drops node
ids for compactness) and silently falls back to **uniform/count-based
weighting for the whole module** whenever the committed duration-list length
no longer matches the live collected node-id count — which it doesn't, for
20/21 modules (mismatches up to ~4x, e.g. `cli`: committed 2704 vs. collected
682). No gate catches this because the skew guard re-reads the same
committed (wrong-length) list.

Reusing `module-tests.yml`'s sharding for the interpreter leg (Option B)
would inherit this exact, documented-broken balancing mechanism. This
mission's remedy (Q1) deliberately avoids it: `capture_shard_timings.py` is
itself tightly coupled to the registry's own consumer shape (it reads
`.github/ci-module-registry.yml`, writes `.github/ci-shard-timings.json`, and
selects over the registry's own `test_dirs` — verified by reading
`scripts/ci/capture_shard_timings.py`'s module docstring and `REGISTRY_PATH`/
`TIMINGS_PATH` constants), so it is not a drop-in tool for a nightly-only,
registry-independent shard split either. The plan phase must choose (or
build) a measurement mechanism scoped to `ci-nightly.yml`'s own interpreter
leg, per C-002, and must not repeat SK-247's specific failure mode: any
producer of shard-sizing data must verify the durations-list length matches
the live collected node-id count before trusting it, and fail loud (never
silently fall back to uniform weighting) if it doesn't.

### Design-phase constraint (binding on this mission, not the operator's Q2)

This spec was authored without dispatching or pushing anything. Reading
existing run logs/timings already on GitHub via `gh run view` / `gh api` is
fine and was used for this spec's evidence review. Q2's up-to-3-dispatch-run
authorization is a plan/implementation-phase action, not exercised here.

### Corrections (verified first-hand by the orchestrator before this spec was written)

1. **No `SPEC-KITTY-LEDGER.md` file exists anywhere in this checkout**,
   confirmed by `find . -iname 'SPEC-KITTY-LEDGER.md'` (no hits) and
   `grep -n "SPEC-KITTY-LEDGER" AGENTS.md CLAUDE.md` (no matches). This
   checkout's own onboarding docs (`CLAUDE.md`, a symlink to `AGENTS.md`) do
   not reference that filename at all — the onboarding instruction they
   actually carry is "every LLM agent working in this repository MUST read
   the project charter at `.kittify/charter/charter.md` at the start of a
   session," a different file, which does exist and was read for this
   mission. There is no drift between this checkout's onboarding
   instructions and its actual contents on this point — an earlier draft of
   this correction conflated two unrelated documents (this checkout's own
   `AGENTS.md` versus the outer mission-orchestration workspace's own,
   separate `CLAUDE.md` one directory level above this checkout, outside the
   spec-kitty repo under review) and wrongly framed the conflation as
   onboarding drift; that framing is retracted here. The SK-247 ledger
   content this spec relies on (see "Why Option B ... was rejected" below)
   was supplied via the mission brief from that outer orchestration
   workspace, not re-derived from any file inside this checkout.
2. The current `interpreter-matrix` job definition was read directly from
   `.github/workflows/ci-nightly.yml` (lines 366-456 as of this writing) and
   matches the mission brief's description: `runs-on: ubuntu-24.04`,
   `timeout-minutes: 45`, `permissions: {contents: read, issues: write}`,
   matrix `python-version: ['3.13']` only, `UV_PROJECT_ENVIRONMENT:
   .venv-py${{ matrix.python-version }}`, and the sync → run (`set +e` +
   `if: always()`) → upload → escalate → terminal fail-loud step sequence.
   One detail not previously called out: the "Run fast/unit suite" step's own
   inline comment cites `#4212` for the run-all-regardless rationale — cited
   here for traceability, not as a new claim.
3. `.github/workflows/ci-nightly.yml`'s `on:` block (lines 40-54) carries only
   `schedule` (`cron: '17 3 * * *'`) and `workflow_dispatch` (with a `mode`
   input, default `full`) — no `pull_request`, no `push`. Confirmed directly.
4. `tests/architectural/test_performance_marker_guard.py` does hardcode the
   literal job key `"interpreter-matrix"` in exactly the three places the
   mission brief names: the `for job_name in ("performance", "e2e", "stress",
   "interpreter-matrix")` loop shared by
   `test_nightly_suite_steps_are_fail_loud` and
   `test_nightly_fail_loud_step_treats_marker_empty_exit_5_as_non_failing`,
   and `test_nightly_workflow_houses_performance_and_interpreter_jobs`'s
   single-job lookup (`jobs.get("interpreter-matrix")`) plus its
   `python-version` matrix assertion (`assert all(_version_tuple(v) > (3, 12)
   ...)`). Confirmed by direct read.
5. `scripts/ci/nightly_escalation.py` requires no code change for this
   mission: `--suite-key` is already a free-form CLI argument with no
   registry coupling, so per-shard escalation (FR-011) only requires each
   shard's call site to pass a distinct value — the script's dedup logic
   (`escalation_marker`, `find_open_issue_by_marker`) already operates
   generically on whatever key string it is given.
6. Re-verified 2026-09-27 (this session): `gh pr list` against
   `spec-kitty/spec-kitty` shows 4 open PRs (#4995, #5009, #5028, #5137); none
   of their changed-file lists include `.github/workflows/ci-nightly.yml`,
   `.github/ci-module-registry.yml`, or `.github/workflows/module-tests.yml`.
   This must be re-verified again at plan/implement time, since PRs open and
   close continuously and this check has a short shelf life.
7. `pyproject.toml` carries a `Programming Language :: Python :: 3.13` trove
   classifier (alongside 3.11 and 3.12), consistent with the issue's premise
   that 3.13 is the currently supported ceiling this leg targets. The repo's
   pinned `.python-version` is `3.11.15`, unrelated to and unaffected by this
   mission (the interpreter-matrix leg pins its own `--python "3.13"`
   independent of that file).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A manually dispatched `ci-nightly.yml` run (`workflow_dispatch`,
  `mode: full`) on this mission's branch shows N independent shard job
  entries in place of the single `interpreter-matrix` job, each with its own
  conclusion recorded in the PR/tracer evidence. — [build] · no-op passable: no
- **SC-002**: In that same dispatched run, every shard's conclusion is
  `success` or `failure` — a real, completed verdict — never `cancelled` by
  its own `timeout-minutes` cap. — [build] · no-op passable: no
- **SC-003**: A coverage-completeness check proves the union of every shard's
  collected node-id set equals the full `pytest -m "fast or unit"` collection
  on 3.13, with 0 duplicate and 0 missing node ids. — [build] · no-op
  passable: no — paired with a deliberately-mutated fixture (one shard
  boundary shifted to drop or duplicate a test file) proving the check can
  fail
- **SC-004**: `tests/architectural/test_performance_marker_guard.py` is
  modified per FR-009/FR-010 and still passes, still enforcing the same
  pull_request-trigger-detection and fail-loud/exit-5 guarantees against the
  new shard names, and additionally fails if a shard is silently dropped from
  the job list. — [build] · no-op passable: no
- **SC-005**: Each shard's `scripts/ci/nightly_escalation.py` call uses a
  distinct `--suite-key`; forcing one shard red in a dispatch run
  opens/updates exactly one `priority:P0` issue scoped to that shard and does
  not touch any other shard's escalation issue. — [build] · no-op passable: no
- **SC-006**: `nightly-summary`'s `needs:` list and result-echo step name
  every new shard job; no dangling reference to the prior single
  `interpreter-matrix` job name remains anywhere in `ci-nightly.yml`. —
  [build] · no-op passable: no
- **SC-007**: No pre-existing test failure encountered during this mission's
  measurement or validation work is silently absorbed as accepted baseline
  without a filed GitHub issue, per the charter's Pre-existing Failure
  Reporting Rule. — [ratchet] · no-op passable: yes — paired with the
  charter's binding rule itself as the positive control (a violation is a
  charter breach, not merely a missed nice-to-have)
- **SC-008**: FR-015's `--suite-key` uniqueness assertion in
  `tests/architectural/test_performance_marker_guard.py` passes against the
  committed post-split `ci-nightly.yml` and fails against a scratch copy with
  two shards' `--suite-key` values deliberately made identical. — [build] ·
  no-op passable: no — the mutation is the required non-vacuity proof
  (Standing Order #5)
- **SC-009**: FR-016's shard-identity roster comparison, run against a
  scratch copy of `ci-nightly.yml` with one shard job deleted but left in the
  roster, fails loudly naming that shard — distinctly from SC-003's
  node-id-based check, which alone only reports that a gap exists. — [build]
  · no-op passable: no
- **SC-010**: `plan.md` (or a mission tracer file) records an explicit,
  citable, independently-checkable reuse-vs-rejection decision against
  `tests/architectural/_gate_coverage.py`'s `BaselineTarget` /
  `collect_real_union_for_target` / `gates_for_target` mechanism, covering
  BOTH FR-004/NFR-002 (the node-id coverage-completeness check) AND FR-016
  (the shard-identity roster's deleted-shard detection) — one combined
  decision or two paired decisions — mirroring how the SK-247 Option-B
  rejection was recorded as durable spec content (Clarifications, "Why
  Option B ... was rejected") rather than left as an unverifiable intention.
  — [build] · no-op passable: no — FR-017 is satisfied only if this record
  exists and names the specific mechanism symbols it evaluated
