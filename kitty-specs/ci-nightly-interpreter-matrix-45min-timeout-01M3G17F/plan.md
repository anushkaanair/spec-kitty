# Implementation Plan: Nightly interpreter-matrix leg completes within its time cap

**Branch**: `issue-4951-ci-nightly-interpreter-matrix-timeout` | **Date**: 2026-09-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `kitty-specs/ci-nightly-interpreter-matrix-45min-timeout-01M3G17F/spec.md`, `research.md`

**Note**: This template is filled in by the `/spec-kitty.plan` command. See `packs/built-in/missions/mission-steps/software-dev/plan/prompt.md` for the execution workflow.

## Summary

The nightly `interpreter-matrix` job in `.github/workflows/ci-nightly.yml` runs
`pytest -m "fast or unit"` on Python 3.13 as a single job with a 45-minute
`timeout-minutes` cap. Two real dispatch runs (serial and `-n auto`) both show
the job force-cancelled by that cap without ever producing a pass/fail
verdict. The remedy (operator Q1, binding) is to split this single job into N
independent, nightly-only shard jobs inside `ci-nightly.yml` — never via
`.github/ci-module-registry.yml`'s LPT bin-packing mechanism (ledger SK-247,
rejected) — each shard sized from a fresh measurement captured during THIS
mission's own `workflow_dispatch` runs (operator Q2, up to 3, plan/implement
phase only). Coverage-completeness (node-id union == full selection, zero
gap/zero overlap) and a shard-identity roster (deleted-shard detection) are
machine-checked gates, not manual review. The architectural guard
(`test_performance_marker_guard.py`) is updated to the new shard names and
proven non-vacuous by a mutation test. This plan makes an explicit
reuse-vs-rejection decision against `tests/architectural/_gate_coverage.py`'s
`BaselineTarget`/`collect_real_union_for_target`/`gates_for_target`
substrate (FR-017/SC-010), lands as one PR, and sequences the up-to-3
dispatch runs across the build/implement phase (never during planning).

## Technical Context

**Language/Version**: Python 3.11+ (repo baseline); the shard split itself targets Python 3.13 exclusively (the interpreter-matrix leg's own pin) — no source code (`src/`) is touched, only CI YAML + one architectural test file.
**Primary Dependencies**: GitHub Actions workflow syntax (`.github/workflows/ci-nightly.yml`); `pytest` (`-m "fast or unit"`, `--collect-only`); `scripts/ci/nightly_escalation.py` (unmodified, `--suite-key` already free-form — confirmed, see Constraint re-verification below); `tests/architectural/_gate_coverage.py`'s `Gate`/`parse_workflow`/`collect_job_nodeids` primitives (reused at the primitive level; see §B "Reuse-vs-rejection decision").
**Storage**: N/A — no persisted data model; the shard-identity roster is a small in-repo constant/YAML table, not a database.
**Testing**: `tests/architectural/test_performance_marker_guard.py` (updated + extended); a new architectural test module for the coverage-completeness check and the shard-identity roster diff; `tests/architectural/` in full as a required local gate (C-005); real `workflow_dispatch` runs of `ci-nightly.yml` as the only mechanism that can prove SC-001/SC-002 (a unit test cannot fabricate GitHub-hosted-runner wall-clock).
**Target Platform**: `ubuntu-24.04` GitHub-hosted Actions runner (the exact class the current job fails on — confirmed via the two prior dispatch runs, research.md §1).
**Project Type**: Single project (this repo, spec-kitty itself); the change is CI-infrastructure-only, not an application feature.
**Performance Goals**: Every shard reaches `success`/`failure` within its own `timeout-minutes`, each budget sized at ~1.3-1.5x real measured wall-clock headroom (NFR-001), mirroring the `#4948` perf/e2e/stress precedent (`performance`: 35min, `e2e`: 40min, `stress`: 10min — each independently re-derived from a real run, not copied unchanged).
**Constraints**: C-001 (no `pull_request` trigger anywhere); C-002 (`.github/workflows/module-tests.yml` and `.github/ci-module-registry.yml` NOT touched); C-003 (dispatch/push authorization starts at plan/implement phase, not spec/plan authoring); C-004 (ruff check + format on touched Python); C-005 (full `tests/architectural/` is a required local gate for this cross-cutting change).
**Scale/Scope**: One workflow file (`.github/workflows/ci-nightly.yml`), one architectural test file (`tests/architectural/test_performance_marker_guard.py`) extended, one new small roster/constant table, one new (or extended) architectural test module for coverage-completeness + roster-diff, zero `src/` changes, zero `module-tests.yml`/`ci-module-registry.yml` changes.

## Charter Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Single canonical authority** (DIRECTIVE_044): the shard-sizing mechanism must NOT become a second, competing "shard balancing" authority alongside `.github/ci-module-registry.yml`'s (broken) one. This plan keeps the two mechanisms structurally separate — the new roster lives in/near `ci-nightly.yml`'s own concern, never inside the module registry — satisfying C-002 and avoiding a second authority for the same concept. PASS.
- **Architectural alignment** (DIRECTIVE_001): the seam is CI-workflow-only (confirmed below); no module-seam or `src/` boundary is touched. PASS.
- **ATDD-first**: the coverage-completeness check (FR-004) and the roster diff (FR-016) are themselves the acceptance tests for User Story 2; they are authored before/alongside the shard split, not bolted on after. PASS by construction (see §G Red-first).
- **Campsite cleaning / Standing Order #2**: evaluated explicitly in §C below — one small, domain-matched tidy identified (stale single-job comments that the split rewrites anyway); no broader grab-bag debt found or fixed. PASS.
- **Mission tracer files / Standing Order #3**: seeded now (`tracer-tooling-friction.md`, `tracer-approach.md`, `tracer-design-decisions.md`), see §D. PASS.
- **Architectural gate discipline / Standing Order #5** ("a gate-unmask cannot self-validate"): both the guard update (FR-009/FR-010) and the suite-key-uniqueness assertion (FR-015) are required to ship with a mutation test proving they can fail, not merely that they currently pass. This is load-bearing in §A and §G below — not optional plan color. PASS by construction, verified at implement time.
- **Canonical sources / Standing Order #6**: this plan explicitly REJECTS reusing `scripts/ci/capture_shard_timings.py` and `.github/ci-module-registry.yml`'s `shard_count` mechanism (SK-247), and makes an explicit, cited reuse-vs-rejection call against `_gate_coverage.py`'s `BaselineTarget` substrate rather than silently building a bespoke duplicate. PASS.
- **Git & workflow discipline / Standing Order #7**: PRs only, one PR for this mission (see §I), never push `main`, dispatches run on the mission's own named branch. The standing order's worktree-isolation clause (DIRECTIVE_045, `pr-agent-worktree-isolation`) is satisfied via spec-kitty's own resolved worktree, not an ad-hoc one this plan invents: `spec-kitty implement` resolves the execution workspace through `resolve_workspace_for_wp` (CLAUDE.md's "Execution Workspace Strategy") into `.worktrees/<feature>-lane-<id>` per this mission's `lanes.json` — flat/`SINGLE_BRANCH` missions still require a `lanes.json` manifest and there is no `-WP##` fallback (a missing manifest fails closed with `MissingLanesError`), so this mission's single-PR shape — whether the tasks phase materializes it as ONE WP or SEVERAL WPs sharing the same lane/branch under `single_branch` topology (a tasks-phase decision this plan does not make; see §I's WP-granularity note) — does not exempt it from that resolver. The build/implement phase's push+dispatch+PR work (§B/§I) therefore runs from that isolated worktree, never the primary checkout. See §I for the same point restated at the phasing level. PASS.
- **Red-main & release discipline / Standing Order #9**: the interpreter-matrix leg being red/cancelled on `main` today is the honest, already-known defect this mission fixes (SC-002) — not baseline noise to suppress. See §F. PASS.

No charter violations require a Complexity Tracking justification; that section below is intentionally empty.

## Project Structure

### Documentation (this mission)

```
kitty-specs/ci-nightly-interpreter-matrix-45min-timeout-01M3G17F/
├── plan.md                          # This file
├── research.md                      # Phase 0 output (already authored)
├── spec.md                          # Mission specification (already authored)
├── tracer-tooling-friction.md       # Seeded this phase
├── tracer-approach.md               # Seeded this phase
├── tracer-design-decisions.md       # Seeded this phase
└── tasks.md                         # Phase 2 output (/spec-kitty.tasks — not this phase)
```

### Source Code (repository root)

```
.github/
└── workflows/
    └── ci-nightly.yml                 # EDITED: interpreter-matrix -> N shard jobs + updated nightly-summary needs:

tests/
└── architectural/
    ├── test_performance_marker_guard.py   # EDITED: FR-009/FR-010/FR-015 (guard updates + suite-key uniqueness + mutation tests)
    ├── test_interpreter_shard_coverage.py  # NEW: FR-004/FR-016 coverage-completeness + roster-diff checks + their mutation tests
    └── _interpreter_shard_roster.py        # NEW: FR-016's shard-identity roster (small constant table, imported by the test above and, if useful, by the guard file)

scripts/ci/
└── (no new script required; --suite-key is already free-form on nightly_escalation.py — see Constraint re-verification below. If the Q2 baseline capture needs a small dedicated timing helper, it lands here as a NEW file — see §B "Shard boundaries" — never editing capture_shard_timings.py or the registry.)
```

**Structure Decision**: Single project, CI-infrastructure-only change. No `src/` package is touched. The shard-identity roster is authored as a plain Python module under `tests/architectural/` (co-located with its only consumer) rather than a YAML file under `.github/`, so it participates in `ruff`/import-linter checks like any other test-support module and needs no new YAML-loading dependency. `_gate_coverage.py`'s own `Gate`/`parse_workflow`/`collect_job_nodeids` primitives are imported directly (already a private module used by sibling architectural tests), not copied.

## Complexity Tracking

*No Charter Check violations require justification. Table intentionally left empty.*

## Implementation Concern Map

### IC-01 — Shard split of `interpreter-matrix`

- **Purpose**: Replace the single `interpreter-matrix` job with N independent nightly-only shard jobs, each a disjoint slice of `pytest -m "fast or unit"` on Python 3.13, each with its own full step sequence and `timeout-minutes`.
- **Relevant requirements**: FR-001, FR-002, FR-003, FR-006, FR-007, FR-008, FR-011, FR-012, NFR-001, NFR-004, NFR-006, C-001, C-002.
- **Affected surfaces**: `.github/workflows/ci-nightly.yml` (`interpreter-matrix` job replaced by `interpreter-matrix-shard-<N>` jobs; `nightly-summary`'s `needs:`).
- **Sequencing/depends-on**: depends on IC-03 (shard-sizing capture, run 1) for real N/timeout values before the FINAL shape is committed; an initial draft shape (placeholder N/timeouts) can be authored before run 1 per §I phasing.
- **Risks**: a shard boundary that silently drops or duplicates tests (mitigated by IC-02); a shard's `pytest` invocation shape breaking `_gate_coverage.py`'s parser (mitigated by IC-02's parseability check, FR-017).

### IC-02 — Coverage-completeness + shard-identity roster

- **Purpose**: Machine-check that the union of every shard's collected node-ids equals the full 3.13 `fast or unit` selection (FR-004/NFR-002), and machine-check that no shard is silently dropped from the job list while remaining in an independent roster (FR-016), per the FR-017/SC-010 reuse-vs-rejection decision below.
- **Relevant requirements**: FR-004, FR-005, FR-016, FR-017, NFR-002, SC-003, SC-009, SC-010.
- **Affected surfaces**: NEW `tests/architectural/_interpreter_shard_roster.py`; NEW `tests/architectural/test_interpreter_shard_coverage.py`; reads (does not modify) `tests/architectural/_gate_coverage.py`.
- **Sequencing/depends-on**: IC-01 (needs the shard job names/selectors to exist in the workflow to validate against); can be authored test-first (red) before IC-01 lands the real jobs. **Before authoring `test_interpreter_shard_coverage.py`'s assertions against IC-01's actual shard job YAML, run `_gate_coverage.parse_workflow`/`gates_for_target` directly (not by inspection) against that YAML and confirm a non-empty `Gate` list results for each shard's `BaselineTarget`.** Parseability was previously assumed by inspection and found false for the CURRENT single job (§A point 6); this step exists specifically so that mistake is not repeated for the new shard shape. Re-run this same empirical check at BOTH §I step 4 AND step 4a — not only at 4a. Step 4 ("Finalize N and each shard's `timeout-minutes` from run 1's real numbers") is where §B point 2's boundary redraw happens whenever a shard's real wall-clock shows a badly-imbalanced partition ("the boundaries are re-drawn before run 2"): a redraw changes that shard's `paths`/`--ignore` arguments directly on the `run:` line's pytest invocation, not merely a numeric `timeout-minutes` or N value — so step 4 CAN edit `run:`-line-adjacent content, and must re-run this parseability check whenever it does. Step 4a (removing IC-03's temporary `--collect-only` measurement scaffolding) touches the `run:` line again regardless of whether step 4 redrew any boundary, so it always re-runs the check too. Relying on step 4a's check alone would miss a parse regression introduced by step 4's own boundary redraw, since that redraw could land and be exercised (or shipped) before step 4a's check runs.
- **Risks**: see §B's reuse-vs-rejection write-up — the wrong reuse choice (wiring through `BaselineTarget`/`BASELINE_TARGETS`) would silently misuse a frozen-baseline-drift mechanism for a live completeness proof.

### IC-03 — Fresh shard-sizing capture (Q2 dispatch runs)

- **Purpose**: Produce real GitHub-hosted-runner timing/collection-count data to size N and each shard's `timeout-minutes` (FR-002, NFR-001), replacing the issue's local 24-core numbers.
- **Relevant requirements**: FR-002, FR-014, NFR-001, NFR-005, C-003.
- **Affected surfaces**: `.github/workflows/ci-nightly.yml` (temporarily, for the measurement run's shape — see §B); PR body or a tracer file for evidence.
- **Sequencing/depends-on**: this is a BUILD/IMPLEMENT-phase action (C-003) — the plan phase does not dispatch anything. IC-01's final shape depends on this concern's output.
- **Risks**: pre-existing red main test failures encountered during a dispatch run being wrongly absorbed as baseline instead of filed (mitigated by re-checking issue #3284's state and searching for new Pre-existing Failure issues, per spec.md's Edge Cases — see §F).

### IC-04 — Guard update + non-vacuity proof

- **Purpose**: Update `test_performance_marker_guard.py`'s hardcoded single-job `"interpreter-matrix"` assertions to the shard shape (FR-009), and prove the update is non-vacuous against a dropped shard / reverted single job (FR-010), plus add the suite-key uniqueness assertion (FR-015) with its own mutation test.
- **Relevant requirements**: FR-009, FR-010, FR-013, FR-015, NFR-003, C-001, SC-004, SC-008.
- **Affected surfaces**: `tests/architectural/test_performance_marker_guard.py`.
- **Sequencing/depends-on**: depends on IC-01 for the real shard job names to enumerate/discover.
- **Risks**: Standing Order #5 — a guard update that is never proven capable of failing is inert scaffolding. Mitigated by the explicit mutation-test requirement in §A/§G.

---

## A. Architecture / shard design

### Seam confirmation

This change lands ENTIRELY on the CI-workflow seam:
- `.github/workflows/ci-nightly.yml` — the `interpreter-matrix` job replaced by N shard jobs; `nightly-summary`'s `needs:` updated.
- `tests/architectural/test_performance_marker_guard.py` — guard updated for the new shard names, suite-key uniqueness assertion added.
- A new small test-support module (`tests/architectural/_interpreter_shard_roster.py`) and a new test module (`tests/architectural/test_interpreter_shard_coverage.py`).

**Explicitly confirmed NOT touched** (per spec.md C-002, re-verified 2026-09-27 by direct read of both files in this checkout): `.github/workflows/module-tests.yml` and `.github/ci-module-registry.yml`. Neither file is opened for edit at any point in this mission. The `architectural` entry in `ci-module-registry.yml` (line ~839, `job: architectural-heavy`, `filter_group: null`) is metadata pointing at `ci-router.yml`'s already-existing heavy battery — it is read-only context for §E's gate table, not a file this mission edits.

### Shard partition method (never SK-247's LPT mechanism)

Shards are drawn by **test module/file/directory partition**, decided by IC-03's fresh measurement (see below), NOT by `.github/ci-module-registry.yml`'s `shard_count` LPT bin-packing. Concretely: the roster (FR-016) declares each shard as an explicit list of top-level test directories/files under `tests/` that together partition the `fast or unit` 3.13 selection with no overlap — e.g. (illustrative shape only; the real boundaries are drawn from IC-03's real per-directory collection counts and timing, not invented here):

- shard 1: `tests/unit tests/status tests/cli`
- shard 2: `tests/specify_cli/runtime tests/charter tests/kernel`
- shard 3: everything else matched by `-m "fast or unit"` not already claimed by shard 1/2 (expressed as `--ignore` globs for the directories already claimed, so the partition is complete by construction: "everything not explicitly assigned elsewhere").

This is a simple, auditable, directory-level split — never weighted by a committed, positionally-paired duration list (SK-247's exact failure mode). Boundaries are re-derived, not guessed: IC-03's run 1 emits real per-candidate-directory wall-clock and collection counts on `ubuntu-24.04`, and N + the final directory groupings are chosen from that real data (NFR-006 requires this be documented in-repo with enough detail to reproduce).

### Fresh measurement source (never local 24-core numbers, never `ci-shard-timings.json`)

Per FR-002/NFR-001/spec.md Edge Case, sizing comes exclusively from IC-03's `workflow_dispatch` run 1 on `ubuntu-24.04` (this mission's own branch). The issue's local numbers (~5036s serial / ~475.87s with `-n auto`, ~34,835 tests, 24-core workstation) are context only and are NOT used to derive N or any `timeout-minutes` value — GitHub's `ubuntu-24.04` standard runner (2 vCPU) is a categorically smaller machine, and the two real dispatch runs already prove the local numbers do not transfer (both real runs never finished in 45 minutes despite the local `-n auto` figure suggesting ~8 minutes). `.github/ci-shard-timings.json` is never read or written by this mission (it is `module-tests.yml`'s own artifact, out of scope per C-002).

### Reuse-vs-rejection decision against `_gate_coverage.py`'s coverage-oracle substrate (FR-017/SC-010)

Verified first-hand in this checkout (2026-09-27, direct read of `tests/architectural/_gate_coverage.py`):

- `Gate` (dataclass, line ~280) — `workflow`, `job`, `shard`, `paths`, `ignores`, `marker_expr`, `via`. A pure data carrier, not tied to any registry.
- `parse_workflow(path, ...)` (line ~814) — statically parses every pytest invocation in a workflow file (including `ci-nightly.yml`, already a `WORKFLOW_FILES` member) into `Gate` objects.
- `collect_job_nodeids(gate, repo_root=None)` (line ~1846) — runs a real `pytest --collect-only` for one `Gate` and returns its node-id list. A pure, `Gate`-in/list-out primitive; it does not require the `Gate` to correspond to a currently-existing workflow job entry versus a synthetic one built for comparison purposes.
- `BaselineTarget` (dataclass, line ~2606) — exactly three fields: `slug`, `workflow`, `job`. Matches gates by `(workflow, job)` string equality alone.
- `gates_for_target(gates, target)` (line ~2628) — filters `gates` to the target's `(workflow, job)`; **raises loudly** ("resolved to 0 gates ... update BASELINE_TARGETS to match") if the job no longer parses to any gate (i.e., renamed/deleted).
- `collect_real_union_for_target(target, gates, repo_root)` (line ~2677) — unions `collect_job_nodeids` over every gate `gates_for_target` returns for ONE `(workflow, job)` pair, explicitly designed so multiple MATRIX LEGS of the SAME job key are unioned transparently (per `BaselineTarget`'s class docstring, not `collect_real_union_for_target`'s own — corrected citation: "a shard split alone (same total coverage, more legs) cannot false-red" lives at `_gate_coverage.py:2605-2616`, `BaselineTarget`'s docstring, not the function's own docstring at `_gate_coverage.py:2677-2694`).
- `BASELINE_TARGETS: tuple[BaselineTarget, ...] = ()` (line ~2625) — **currently empty**. `freeze_baselines()` (its only producer-side consumer) writes one committed node-id snapshot file per target under `tests/architectural/baselines/`, read back by a day-to-day drift-detection test that compares "current real selection" against that FROZEN, committed file — i.e., this whole layer answers "has this ONE job's selection changed since we last froze it," not "do N *independently-named* jobs' selections union to exactly the live full selection right now."
- Confirmed (research.md §7, re-confirmed by this plan's own read): **no test file anywhere in `tests/` imports `collect_real_union_for_target`, `gates_for_target`, or `BaselineTarget`**, and no Makefile/workflow target invokes `--emit-census`/`--verify-census`/`--freeze-baselines`. This mechanism is unconsumed today, not merely unconfigured.

**Decision — partial reuse, explicit rejection of the frozen-baseline layer, one new consumer authored:**

1. **REUSE** the low-level primitives `Gate`, `parse_workflow`, and `collect_job_nodeids` directly. They are pure, general-purpose (parse a workflow into gates; collect real node-ids for a gate) and require no baseline-file machinery to be useful. FR-004's "full selection" side is built the same way, as a **synthetic `Gate`** (`workflow="ci-nightly.yml"`, `job="<synthetic-full-selection>"`, `marker_expr='fast or unit'`, `paths=["tests"]`, no shard) that is never inserted into the real workflow file — it exists only in the new test module, to reuse `collect_job_nodeids`'s exact collection mechanics for the ground-truth side of the comparison. This keeps both sides of FR-004's comparison collected through the IDENTICAL method (mirroring `_gate_coverage.py`'s own "both sides captured by the identical function" design principle for its E3 baselines), without requiring a job that runs the unsharded selection to still exist in the workflow.
2. **REUSE** `BaselineTarget` (the 3-field dataclass) and `gates_for_target` (the raise-loudly-on-zero-gates function) **directly, per-shard, as local values constructed inside the new test** — NOT by adding entries to the shared `BASELINE_TARGETS` tuple. Each shard name in the roster becomes one `BaselineTarget(slug=<shard_name>, workflow="ci-nightly.yml", job=<shard_job_key>)`; calling `gates_for_target` for each one gives FR-016's "job renamed/deleted" detection for free (the exact `RuntimeError` this function already raises), satisfying the deleted-shard half of FR-016 with zero new detection logic. This is the FR-016-relevant half of the decision research.md §7 flags explicitly.
3. **REJECT** wiring through `BASELINE_TARGETS` (the shared, committed-file-backed tuple) and `collect_real_union_for_target`/`freeze_baselines` (the frozen-baseline comparison layer) for BOTH FR-004 and FR-016. Rationale: that layer's semantic is "did this ONE job's selection drift since a human last froze it" (a historical-drift oracle, requiring a committed snapshot file re-generated by a human running `--freeze-baselines`), not "do these N independently-named jobs' LIVE selections union to exactly today's full selection, with zero gap/zero overlap, on every CI run." Repurposing it would either (a) silently redefine what a `BaselineTarget` means for every other future consumer of the shared tuple, or (b) require one frozen baseline file per shard that must be manually regenerated every time a shard boundary moves — reintroducing exactly the "committed data can silently drift from live reality" hazard SK-247 already burned this mission's sibling on (Clarifications, "Why Option B ... was rejected"), just one layer up.
4. This is therefore "extend AND author a new consumer," not "flip a switch," matching research.md §7's explicit caveat. The new consumer is `tests/architectural/test_interpreter_shard_coverage.py` (IC-02).
5. **FR-016's second half is NOT covered by `gates_for_target` alone** (research.md §7's "shape gap" caveat, independently re-confirmed by this plan's own read of `BaselineTarget`'s 3-field shape): `gates_for_target` only detects a shard job **key** vanishing from `jobs:` entirely. It cannot detect a shard job that still exists but whose selector was silently reassigned to the wrong subset. The roster (`_interpreter_shard_roster.py`) therefore separately declares each shard's intended test paths/selector as its own field (see roster shape below), and the new test's roster-vs-live-selector comparison (not just the roster-vs-`jobs:`-keys existence check) is what closes that second gap.
6. **Parseability corrected (empirically re-derived, not assumed)**: the CURRENT single `interpreter-matrix` job does **NOT** parse into any `Gate` today. Verified directly against this checkout (2026-09-27, `_gate_coverage.parse_workflow(Path(".github/workflows/ci-nightly.yml"))`): it resolves exactly 5 gates (`performance`, `e2e`, `stress`, `full-module-matrix`, `integration-next`) — **zero** for `interpreter-matrix`. Root cause: `_FLAG_TOKENS`'s bare `--frozen` optional-value alternative (`_gate_coverage.py:227-229`) greedily swallows the next flag's NAME (`--python`) as its own value, leaving `--python`'s quoted value (`"${{ matrix.python-version }}"`) unconsumed and breaking `_PREFIX_RE`'s prefix-strip loop (`_gate_coverage.py:240-268`) before it ever reaches `pytest` — unique to the two-flag `--frozen --python "<value>" --all-extras` shape at `ci-nightly.yml:416`; the five jobs that DO parse use the simpler `--frozen pytest ...` (or `--frozen --all-extras pytest ...`) form. **This is a pre-existing, mission-independent defect in the shared `_FLAG_TOKENS` regex — it predates this mission and this mission does NOT fix it** (`_gate_coverage.py` is read-only per this section's Seam confirmation); if some future mission needs the two-flag shape elsewhere, the regex defect remains open. Reproducing this job's exact invocation shape verbatim in every new shard, as an earlier draft of this plan assumed, would therefore make `gates_for_target` unconditionally raise "resolved to 0 gates" for EVERY shard (breaking FR-016's deleted-shard detection and FR-004's roster-vs-live-selector comparison by design). Instead, the "Per-shard job shape" template below deliberately **drops the redundant `--python "<value>"` flag** from the `uv run` line — Python is already pinned via `actions/setup-python` + `UV_PROJECT_ENVIRONMENT` earlier in the same job, so the flag is redundant on the pytest invocation itself — matching the already-parsing jobs' shape and closing the FR-017 dependency this reuse decision requires. Confirmed directly: `_gate_coverage.strip_to_command` on `uv run --frozen --all-extras pytest -m "fast or unit" ...` strips cleanly to the `pytest ...` command. **This must be re-verified empirically against the FINAL shard job YAML at implement time** (see IC-01/IC-02's sequencing note below) — inspection alone is exactly the mistake this correction fixes.

### Shard-identity roster shape (FR-016)

`tests/architectural/_interpreter_shard_roster.py` — a plain Python module (not YAML, per Project Structure decision above), shape:

```python
@dataclass(frozen=True)
class InterpreterShard:
    job_key: str            # e.g. "interpreter-matrix-shard-1" -- must match ci-nightly.yml's jobs: key exactly
    paths: tuple[str, ...]  # positional pytest args for this shard's slice, e.g. ("tests/unit", "tests/status", "tests/cli")
    ignores: tuple[str, ...] = ()  # --ignore globs, used when a shard is expressed as "everything except X/Y"
    suite_key: str = ""      # the --suite-key literal this shard's escalation step must use; defaults derived from job_key if empty

INTERPRETER_SHARDS: tuple[InterpreterShard, ...] = (
    # populated with the REAL boundaries once IC-03's run 1 data exists
)
```

The coverage-completeness check (FR-004) reads `INTERPRETER_SHARDS` to build one `Gate`/`BaselineTarget` per declared shard (independent of `ci-nightly.yml`'s live `jobs:` block), and diffs `{s.job_key for s in INTERPRETER_SHARDS}` against `parse_workflow("ci-nightly.yml")`'s real job-key set — a shard present in the roster but absent from `jobs:` fails loudly naming that shard (FR-016/SC-009); a shard present in `jobs:` whose selector's real node-ids don't match what the roster declares (or collects zero) fails loudly as a separate, distinguishable case (FR-005/AC2). This is the concrete mechanism behind Acceptance Scenario 3 of User Story 2.

### Per-shard job shape (mirrors the existing single job, FR-007/FR-008/FR-012)

Each `interpreter-matrix-shard-<N>` job keeps, independently (no shared/reused sync step across shards):

```yaml
interpreter-matrix-shard-<N>:
  name: "Interpreter matrix shard <N> (Python 3.13, nightly-only, FR-021)"
  runs-on: ubuntu-24.04
  timeout-minutes: <real-measured-wallclock * 1.3-1.5, from IC-03>
  permissions:
    contents: read
    issues: write
  strategy:
    fail-fast: false   # implicit for independent jobs; kept explicit-in-spirit via each job's own if: always()
  env:
    UV_PROJECT_ENVIRONMENT: .venv-py3.13
  steps:
    - uses: actions/checkout@... # same SHA-pin as today
    - name: Set up Python 3.13
      uses: actions/setup-python@...
      with: { python-version: '3.13' }
    - name: Install uv
      uses: astral-sh/setup-uv@...
    - name: Sync dev environment on this interpreter
      run: uv sync --frozen --all-extras --python "3.13"
    - name: Run fast/unit suite, shard <N> (full-mode, run-all-regardless)
      if: always()
      run: |
        set +e
        uv run --frozen --all-extras pytest -m "fast or unit" <shard's paths/--ignore> -q -n auto --dist loadfile --junitxml="out/reports/xunit-nightly-interpreter-3.13-shard-<N>.xml"
        code=$?
        echo "INTERPRETER_SHARD_<N>_EXIT=$code" >> "$GITHUB_ENV"
    - name: Upload interpreter-matrix shard <N> reports
      if: always()
      uses: actions/upload-artifact@...
    - name: Escalate interpreter 3.13 shard <N> red -> deduped P0 (fail-closed)
      if: always()
      run: python3 scripts/ci/nightly_escalation.py --suite-key "interpreter-3.13-shard-<N>" --conclusion "$conclusion" --run-url "..."
    - name: Fail the leg if this shard's suite was red (run-all-then-fail-loud)
      if: always()
      run: |
        if [ "${INTERPRETER_SHARD_<N>_EXIT:-1}" -ne 0 ] && [ "${INTERPRETER_SHARD_<N>_EXIT:-1}" -ne 5 ]; then
          echo "::error::interpreter 3.13 shard <N> suite exited ${INTERPRETER_SHARD_<N>_EXIT}"
          exit 1
        fi
```

**Deliberately no `--python "<value>"` flag on the `uv run ... pytest` line** (unlike the CURRENT single job's `uv run --frozen --python "${{ matrix.python-version }}" --all-extras pytest ...`): Python is already pinned for this job via `actions/setup-python` (above) and `UV_PROJECT_ENVIRONMENT` (the job's `env:`), so the flag is redundant on the pytest invocation itself, and this shape is chosen SPECIFICALLY to make each shard parseable by `_gate_coverage.py`'s `parse_workflow` — see §A "Reuse-vs-rejection decision" point 6 for the empirically-verified defect this sidesteps.

Distinct `--suite-key` per shard: `interpreter-3.13-shard-<N>` (FR-011/FR-015) — chosen deliberately to differ from the CURRENT single-job key literal `"interpreter-${{ matrix.python-version }}"` in shape (adds `-shard-<N>`), not merely in the matrix substitution, so a copy-paste that forgets to change the shard number is what FR-015's mutation test targets.

**NFR-004 (accepted cost, restated explicitly)**: splitting into N shards means `actions/checkout` + `setup-python` + `install uv` + `uv sync --frozen --all-extras --python "3.13"` now runs N times instead of once for this leg. This is accepted, documented cost (mirrors the `#4948` precedent's own NFR-005 there), not a defect this mission tries to eliminate — each shard's independent sync is precisely what FR-008 requires to avoid reopening the #4866 cross-shard environment hazard, so the N-times cost and the correctness guarantee are the same design choice, not a tradeoff to optimize away.

### `nightly-summary` update (FR-006)

`needs:` changes from `[performance, e2e, stress, interpreter-matrix, integration-next, full-module-matrix]` to `[performance, e2e, stress, interpreter-matrix-shard-1, interpreter-matrix-shard-2, ..., interpreter-matrix-shard-N, integration-next, full-module-matrix]`, and the result-echo step gains one `echo "interpreter-matrix-shard-<N>: ${{ needs.interpreter-matrix-shard-<N>.result }}"` line per shard, replacing the single `interpreter-matrix` line. SC-006 requires zero dangling reference to the old job name anywhere in the file — verified by a final `grep -n 'interpreter-matrix"' .github/workflows/ci-nightly.yml` (exact old job key, quoted, as a job reference) returning no hits outside comments that are themselves rewritten per §C.

### Guard-update plan (FR-009/FR-010) and its non-vacuity proof

`test_performance_marker_guard.py`'s three hardcoded-`"interpreter-matrix"` sites become:

1. `test_nightly_suite_steps_are_fail_loud` / `test_nightly_fail_loud_step_treats_marker_empty_exit_5_as_non_failing`'s shared `for job_name in ("performance", "e2e", "stress", "interpreter-matrix")` loop — replaced with `for job_name in ("performance", "e2e", "stress", *INTERPRETER_SHARD_JOB_KEYS)`, where `INTERPRETER_SHARD_JOB_KEYS` is imported from the new roster module (`tuple(s.job_key for s in INTERPRETER_SHARDS)`) — DYNAMIC discovery from the roster, not a second hardcoded literal list, so the roster stays the single source of truth for shard identity (avoiding yet a third place shard names must be kept in sync).
2. `test_nightly_workflow_houses_performance_and_interpreter_jobs`'s single-job lookup (`jobs.get("interpreter-matrix")`) and its `python-version` matrix assertion — replaced with an assertion that EVERY roster-declared shard job key exists in `jobs:` (reusing `gates_for_target`'s raise, per §A's reuse decision) and that the workflow file still pins Python 3.13 per shard: `actions/setup-python`'s `with: { python-version: '3.13' }` and the `uv sync --frozen --all-extras --python "3.13"` step both carry the pin (the `uv run ... pytest` line deliberately does NOT — see §A's "Per-shard job shape" note on why that flag is dropped there) — the "above-3.12" guarantee re-expressed per-shard since there is no longer a single job's `strategy.matrix.python-version` to read.
3. **Non-vacuity proof (Standing Order #5, User Story 4)**: a NEW test, `test_guard_fails_when_a_shard_is_dropped_from_the_job_list`, that loads `ci-nightly.yml`'s parsed YAML, deletes one roster-declared shard's `jobs:` entry in memory (a scratch dict, never writing to disk), and asserts the SAME job-presence assertion used in (2) above raises/fails against that mutated dict. A second mutation test, `test_guard_fails_when_shards_are_reverted_to_a_single_job`, replaces all shard entries with one synthetic `interpreter-matrix` job (the pre-split shape) and asserts the same failure. Both mutations are constructed as in-memory dict edits of the already-parsed YAML (mirroring how `test_no_pull_request_workflow_selects_performance_or_interpreter_jobs` and similar existing tests in this file already operate on parsed structures, not temp files) — no scratch file needs to be written to disk unless a test specifically needs `parse_workflow` to re-read from a path, in which case a `tmp_path`-written scratch copy is used exactly once for that test.
4. `test_nightly_workflow_never_triggers_on_pull_request` and `test_no_pull_request_workflow_selects_performance_or_interpreter_jobs` (FR-013) are left semantically unchanged — `FORBIDDEN_PR_PATH_TOKENS`'s existing `"interpreter-matrix"` substring entry still matches every new shard job name (`interpreter-matrix-shard-1`, etc., all contain the substring `"interpreter-matrix"`), so this guard continues protecting the new shape without modification. Confirmed by construction: shard job keys are deliberately named `interpreter-matrix-shard-<N>` (not e.g. `py313-shard-<N>`) specifically so this existing token keeps matching.

### Suite-key-uniqueness assertion (FR-015)

New test `test_nightly_suite_keys_are_pairwise_distinct`: commits to ONE concrete extraction method rather than leaving it undecided. It parses the already-loaded YAML `jobs:` mapping (`yaml.safe_load`, the same structured parse every sibling test in this file already uses) and, for each job, iterates its `steps[].run` string; from each FULL `run:` string (never a naive `run.splitlines()` pass — a value split across a continued physical shell line must not be able to hide from the scan; see the continuation-aware statement scoping below, which joins continuations BEFORE splitting, rather than scanning raw physical lines) it extracts every `--suite-key <literal>` value using a pattern that matches THREE forms, not two — double-quoted, single-quoted, AND bare/unquoted — e.g. `--suite-key\s+(?:"([^"]+)"|'([^']+)'|(\S+))` — **but this pattern is never applied to a job's raw `run:` string as a whole.** The bare/unquoted alternative (`(\S+)`) has no invocation anchor of its own, so applying it unscoped would let a stray comment or `echo` mentioning the literal text `--suite-key <word>` (e.g. a `#`-prefixed remark introduced by §C's campsite-clean rewrite, which explicitly touches this job's descriptive comments) be misread as a real key — a false-positive/noise risk (widening only adds spurious matches; it can never miss a real collision, so this would be a nuisance guard failure for a future maintainer to chase, not a missed collision, but it is still worth closing). To prevent it, the `run:` string is first joined across shell line-continuations (a trailing `\` immediately followed by a newline is replaced with a single space, since that is the shell's own syntax for "this is still the same statement") and then split into individual statements on unescaped newlines and `;`; the three-form pattern above is applied only to a statement that ALSO contains the literal substring `nightly_escalation.py` (or `scripts/ci/nightly_escalation.py`) — i.e., only within a statement that is itself an actual invocation of the escalation script. A statement without that substring (a bare comment, an `echo`, or any other shell line) is never scanned, so a prose mention of `--suite-key` in a comment or echo can no longer be captured as a key, regardless of quoting style, while a real `--suite-key` argument on the same statement as the script invocation is captured exactly as before. **The bare/unquoted form is not hypothetical — it is the real, committed shape of most of today's `--suite-key` literals**: verified directly against this checkout (2026-09-27), the `performance`, `e2e`, `stress`, and `integration-next` jobs' `nightly_escalation.py` calls all use bare, unquoted tokens (`--suite-key performance`, `--suite-key e2e`, `--suite-key stress`, `--suite-key integration` — `ci-nightly.yml:165,252,347,629`), while only the interpreter leg's key is quoted (CURRENT single job: `--suite-key "interpreter-${{ matrix.python-version }}"` at `ci-nightly.yml:438`; NEW per-shard shape: `--suite-key "interpreter-3.13-shard-<N>"`, §A above). An extraction limited to quoted forms alone would capture ZERO keys for the four bare-literal jobs, silently dropping them from the `keys` list even though this section's own claim is that keys are collected "across ALL nightly jobs" — a collision between a new shard's key and one of those four bare literals (e.g. an accidental `--suite-key integration` typo on a shard) would then go undetected by the very guard meant to catch it. The three-way pattern above closes that gap: the bare-token alternative (`(\S+)`) matches `performance`/`e2e`/`stress`/`integration` exactly as committed, and the quoted alternatives match the interpreter leg's and every shard's quoted keys, so all real `--suite-key` values — regardless of quoting style — land in the SAME `keys` list and are compared against EACH OTHER, not scored as separate, non-interacting pools. This is a structured traversal over the already-parsed mapping, deliberately NOT following this file's actual per-line-scan precedent — `test_nightly_fail_loud_step_treats_marker_empty_exit_5_as_non_failing`'s `run.splitlines()` scan for `-ne 0`/`-ne 5` conditions — for exactly the full-string-scope reason above. (Correction: `_spec_kitty_run_performance_leaks` is not usable as precedent here — it inspects a structured `env:` dict, not `run:` script text at all.) Keys are collected across ALL nightly jobs (`performance`, `e2e`, `stress`, every `interpreter-matrix-shard-<N>`, `integration-next`) — the four bare-unquoted keys and every quoted key alike — and the test asserts `len(keys) == len(set(keys))`. **Mutation test**: `test_suite_key_uniqueness_guard_is_non_vacuous` builds a scratch copy of the parsed jobs mapping with two shards' `--suite-key` values deliberately collided (e.g. both set to `"interpreter-3.13-shard-1"`) and asserts the same uniqueness assertion fails against that scratch mapping — the required non-vacuity proof (SC-008). A second collision variant expresses the two colliding values with DIFFERENT quote styles (one single-quoted, one double-quoted) so the extraction is proven not to accidentally key off quote character rather than the literal value. A THIRD collision variant collides an existing BARE key (e.g. `performance`) against a shard's QUOTED key given the same literal (e.g. a shard mistakenly set to `--suite-key "performance"`), proving the bare and quoted alternatives feed the identical `keys` list and are checked against each other, not held in separate, non-interacting pools by construction. **A FOURTH test, `test_suite_key_extraction_ignores_non_invocation_mentions`, proves the statement-scoping fix above rather than just quote handling**: it builds a scratch job whose `run:` string contains a `#`-prefixed comment line reading `# --suite-key convention: interpreter-3.13-shard-9` (a statement that does NOT also contain `nightly_escalation.py`) alongside a normal, correctly-scoped `--suite-key` invocation, and asserts the extracted `keys` list contains ONLY the real invocation's key — `interpreter-3.13-shard-9` must NOT appear — confirming a stray comment mentioning the literal string `--suite-key` can no longer register as a key.

## B. Dispatch-run sequence (operator Q2 — plan/implement-phase only)

**The PLAN phase (this document) performs none of this dispatching.** No `workflow_dispatch`, no `git push`, and no branch mutation happened while authoring this plan — confirmed by this session's own tool history (only `Read`/`Bash` read-only commands and local file writes under `kitty-specs/`). Everything below is sequencing for the BUILD/IMPLEMENT phase to execute.

1. **Run 1 — baseline/timing-capture** (build/implement-phase action): the build phase pushes the mission branch (`issue-4951-ci-nightly-interpreter-matrix-timeout`, the charter's named-branch rule — never `main`) after IC-01's roster + guard updates are authored against an initial N/timeout GUESS (see §I phasing), then dispatches `ci-nightly.yml` via `workflow_dispatch` (`mode: full`). For this run, the interpreter leg is shaped as: **the candidate shard jobs already split per the roster's directory boundaries, but each shard's `timeout-minutes` set generously high (e.g. the full 45 minutes each, run independently rather than as one combined 45-minute job)** — plus an ADDITIONAL lightweight step per shard (or one extra always-run job) that runs `pytest --collect-only -q -m "fast or unit" <shard paths>` to record each shard's real collected node-id count alongside its real wall-clock from the timed run. This is preferred over a separate throwaway "measurement job" shape because it directly validates the chosen directory partition's real timing AND collection counts in the same run that will also inform run 2's final budgets — avoiding a wasted dispatch that measures a shape different from what gets shipped.
2. **What run 1 measures and how it feeds N/timeout**: each shard's real wall-clock (from its own job's step duration) and real collected node-id count (from the `--collect-only` step) are read from the run's logs/artifacts. `timeout-minutes` for each shard is set to `ceil(real_wallclock_minutes * 1.3)` at minimum, `* 1.5` if the real wall-clock is close to a round number or historically variable (mirroring the e2e/performance jobs' own precedent headroom, and the stress job's documented `ceil(4m44s * ~1.5)` calculation). If any shard's real wall-clock suggests its directory partition is badly imbalanced (e.g. one shard takes 3x another), the boundaries are re-drawn before run 2 — this is exactly what NFR-006's "auditable methodology" documents.
3. **Run 2 — validation**: dispatch the FINALIZED shard split (real boundaries, real per-shard `timeout-minutes` from run 1) plus the coverage-completeness check and roster now fully populated. Must show: every shard reaches `success`/`failure` (never `cancelled`) within its own budget (SC-001/SC-002); the coverage-completeness check passes locally (run before push, per §E/§G — this is a local `pytest` gate, not something the dispatch run itself re-proves, though the dispatch run's real per-shard collection counts are cross-checked against the local check's numbers as an extra sanity pass); suite-key uniqueness holds (verified locally, C-005); each shard's escalation call is confirmed functional by inspecting the run's logs for the `nightly_escalation.py` step's printed outcome (e.g. "no open escalation issue ...; nothing to do (suite green)" on a green shard).
4. **Run 3 — spare**: reserved ONLY for a re-run if run 2 surfaces a fixable issue a second attempt can plausibly resolve without another operator round-trip — e.g. a mis-sized `timeout-minutes` that needs one more real number, a coverage gap from a boundary that needs redrawing, or a flaky escalation call (transient GitHub API error) that a clean re-run would confirm resolved. **Explicit stop rule**: if run 2 fails in a way run 3 cannot plausibly fix (a structural defect in the shard design itself, e.g. the partition method doesn't actually eliminate the timeout), OR if run 3 is also exhausted without success, OR if a 4th run would be needed for any reason — STOP and escalate to the operator per Q2's own limit. Never dispatch a 4th run under any circumstance in this mission.
4a. **Run 1 failure accounting**: a failed run 1 (one that errors, is force-cancelled for an unrelated infra reason, or otherwise fails to produce usable baseline/timing data before ever reaching its measurement purpose) still counts against the up-to-3 total in point 4 above — it is not exempt from the budget just because it never reached "baseline/timing-capture" successfully. Its replacement (a redone baseline/timing-capture attempt) consumes the NEXT run's slot — i.e., the numbered sequence above renumbers down by one (the replacement becomes what point 4 calls "run 2," validation becomes "run 3," and the spare slot is gone) — rather than being dispatched as an unbudgeted 4th attempt. The same escalate-to-operator stop rule in point 4 applies verbatim if that replacement run also fails.
5. **Evidence recording (NFR-005)**: every dispatched run's URL and every shard job's conclusion is recorded in BOTH the PR body (under a "Dispatch evidence" heading) AND `tracer-approach.md` (durable in-repo record, not only a PR comment that could be edited/lost) before the mission is considered complete. This must happen before the mission's PR is marked `ready-for-squad`.
6. **Push discipline**: the build/implement phase pushes only the mission's own named branch (`issue-4951-ci-nightly-interpreter-matrix-timeout`), never `main` — per CLAUDE.md's "Never push to `main`" rule and the charter's git/workflow Standing Order #7. `git push` and `workflow_dispatch` are both build/implement-phase-only actions (C-003); this plan phase performed neither.

## C. Campsite-clean scope

**One distinct, behaviour-preserving first step is warranted, and it is domain-matched — not a grab-bag.** The current `interpreter-matrix` job's block (lines ~365-456 of `.github/workflows/ci-nightly.yml`) carries several multi-line comments that describe the SINGLE-job shape being replaced (e.g. "Deliberately scoped to the nightly lane... interpreter-matrix job runs the fast/unit suite on every Python version ABOVE 3.12", the `#4866` per-interpreter dedicated venv comment block, the terminal fail-loud gate's comment referencing "the FR-021 interpreter lane"). These comments will need rewriting as part of the split regardless of how the split itself is shaped — updating them is not an independent grab-bag cleanup, it is the SAME surface the functional change touches, so per the charter's `RECONCILE_CHANGE_SCOPE_TENSIONS` ordering (smallest-viable-diff picks the file set first; Boy Scout Rule governs cleanup strictly inside that file set) this is proportional tidy-up inside the one file already being edited, not scope growth. Concretely: the campsite-clean commit (or the first commit of the mission, if kept as one PR per §I) rewrites the top-of-job comment block to describe the shard shape and the roster's existence, BEFORE the mechanical job-splitting edit lands, so the diff reads as "comment/doc update" then "structural split" rather than one large tangled diff. No other domain-matched debt was found in the touched surfaces (`test_performance_marker_guard.py` has no stale comments blocking this change; `_gate_coverage.py` is read-only for this mission).

## D. Tracer files

Seeded in this mission's directory (see the three files written alongside this plan): `tracer-tooling-friction.md`, `tracer-approach.md`, `tracer-design-decisions.md`. Content summarized in this report's closing section; full content is in the files themselves.

## E. Gate set

**ENFORCED** (re-verified 2026-09-27 against this checkout's own `.github/workflows/`):
- `ruff check .` + `ruff format --check .` (always-on, `ci-router.yml`/`ci-quality.yml`).
- `uv lock --check`.
- import-linter (TID251).
- `spec-kitty regen --check`.
- terminology guard (`tests/architectural/test_no_legacy_terminology.py`).
- layer-rules / pyproject-shape (`tests/architectural/test_layer_rules.py`, `test_pyproject_shape.py`).
- archive-freeze (`tests/architectural/test_archive_root_byte_identical.py`).
- **Heavy architectural battery** (`architectural-heavy` in `ci-router.yml`) — its `if:` (re-read directly, lines ~511-531) is the OR of only the SRC-BACKED filter groups (`merge`, `auth`, `missions`, `post_merge`, `release`, `status`, `review`, `next`, `lanes`, `dashboard`, `upgrade`, `cli`, `charter`, `agent`, `kernel`, `glossary`, `execution_context`, `core_misc`, `unit`, `specify_cli_runtime`) — **NONE of which this mission's diff matches** (the diff touches only `.github/workflows/**`, which maps to the `ci` filter group, and `tests/architectural/**`, which maps to no named group and is not `src/**` so it also never trips the fail-closed `unmatched` catch). **This means CI's own path-filter router will NOT select the heavy architectural battery for this mission's diff on its own.** Per spec.md C-005, this mission ADDS the full `tests/architectural/` suite as a LOCAL, manually-run verification step BEFORE pushing — distinct from, and not reliant on, what `ci-router.yml`'s path filters would otherwise select.
- **Routed test groups** (`ci-router.yml`'s `changes` job) — the diff matches the `ci` group (`scripts/ci/**` + `.github/workflows/**` globs, confirmed by direct read of the `changes.filters` block, lines ~194-196). Per that group's own design comment ("No job gates on this group BY DESIGN... the per-PR executor for this path family... is the ci-modules.yml module matrix, which runs on every PR"), no additional router-driven job fires specifically because of the `ci` group match.
- **Per-module test shards** (`ci-modules.yml`, diff-scoped) — checked against `.github/ci-module-registry.yml`'s `test_dirs`: the diff's files (`.github/workflows/ci-nightly.yml`, `tests/architectural/*.py`) do not fall under any registered module's `test_dirs` root, so no per-module shard is diff-scoped to this change. The `architectural` entry in the registry (`job: architectural-heavy`, `filter_group: null`) is the SAME heavy battery already addressed above, not a separate per-module shard.
- **diff-cover >=90% of changed critical-path lines** (`ci-aggregate.yml`) — verified by direct read of `scripts/ci/aggregate_source.py`'s `CRITICAL_PATHS` tuple: `src/kernel/*`, `src/charter/*`, `src/specify_cli/status/*`, `src/specify_cli/lanes/branch_naming.py`, `src/specify_cli/dashboard/handlers/*`, `src/specify_cli/dashboard/scanner.py`, `src/specify_cli/merge/*`, `src/runtime/next/*`, `src/mission_runtime/*`. **None of this mission's changed files (`.github/workflows/ci-nightly.yml`, `tests/architectural/*.py`) fall under any of these globs.** `critical.diff.patch` (the file diff-cover actually scores) will therefore contain ZERO lines from this mission's diff — the gate has nothing to score and is satisfied vacuously (an empty critical-path diff trivially clears any percentage threshold; `validate_diff_coverage.py` is invoked with a diff file that, for this mission, has no hunks at all).
- Wheel build + clean-install-verification (`ci-quality.yml`, always-on).
- Doctrine packs gate (`packs.yml`) — **fires on every PR unconditionally**: it deliberately carries no top-level `on.*.paths` filter (confirmed by direct read, lines 39-44 — #3008 Gate-0 avoidance, to avoid a hand-maintained path list drifting out of lockstep with the workflow's own internal `changes` filter), and its terminal `packs-gate` aggregator job (`if: always() && !cancelled()`, lines ~245-258) always runs and resolves green when nothing downstream failed. What does NOT run for this mission's diff is the per-lane verification WORK inside it: the internal `changes` job's filter does not match `.github/workflows/**` or `tests/architectural/**`, so every `built-in-*`/`internal-*` lane job reports `if: false` (skipped, not evaluated) and `packs-gate` resolves green with zero packs-specific work performed. Net practical conclusion is unchanged from an earlier draft of this plan: nothing packs-specific blocks this mission's PR — only the cited mechanism (a path filter that doesn't exist) was backwards.

**NOT ENFORCED** (named explicitly, and why):
- Commit-message lint — prints only, `|| true`.
- markdownlint — `|| true`, can never fail.
- Bandit / pip-audit — no workflow runs them.
- mypy — no workflow runs it; `make typecheck` is local-only and covers 2 files, unrelated to this mission's surfaces.
- "kernel/mission-loader >=90%" named floors — do not exist as a separate gate; the diff-cover gate above is the real, single coverage gate.
- SonarCloud — `sonar-pr` (`ci-aggregate.yml`) is `continue-on-error` and excluded from `aggregate-gate`'s `needs:`; whole-repo `sonar.yml` is schedule/dispatch-only. Neither blocks this mission's PR (spec.md C-006).
- Typer JSON error surface / `patch()` target validation / Contextive glossary freshness — no dedicated job for any of these; none apply to a CI-YAML + architectural-test-only change.

**C-005 restated as an ADDED local step**: because this mission is a cross-cutting workflow + guard-test change, the full `tests/architectural/` suite is run LOCALLY before pushing, as a verification step this plan adds — NOT because `ci-router.yml`'s own path-filter authority would select it (it would not, per the analysis above). This is the load-bearing distinction the mission brief calls for.

`make ci-parity` was not run during this plan-authoring session (read-only-fine per the mission brief, but the gate-selection analysis above was already derived by direct read of `ci-router.yml`/`ci-aggregate.yml`/`ci-module-registry.yml`/`aggregate_source.py`, which is more precise for this diff than the tool's generic preview); the build/implement phase may run it to double-check before pushing, and should record what it reports if run.

## F. Baseline

Before making any change, the build/implement phase runs, on the branch BASE (i.e., before the first commit of this mission):
- `tests/architectural/test_performance_marker_guard.py` in isolation.
- The full `tests/architectural/` suite (per C-005's added local step).
- Any test file touched for `scripts/ci/nightly_escalation.py` IF that file ends up touched (current expectation: it does not — `--suite-key` is already free-form, confirmed below — so no test file is expected to change there; this line applies only if that expectation changes during implementation).

Whatever is red on that BASE run before any change is pre-existing and must be classified per the charter's Pre-existing Failure Reporting Rule (not silently absorbed) — see spec.md's Edge Cases: issue #3284 (23 untracked failures/2 errors) is CLOSED as of 2026-09-08, so it is NOT a currently-open explanation for any base-run red; the build/implement phase must re-run `gh issue view 3284` and search for newer open Pre-existing Failure issues at the time it actually runs this baseline (not trust this plan's snapshot), per spec.md's explicit instruction.

**The nightly `interpreter-matrix` leg being red/cancelled on `main` today is NOT baseline noise to exclude — it IS this mission's acceptance criterion (SC-002).** The two prior dispatch runs (research.md §1) already establish this defect exists on `main`'s current shape; this mission's job is to make it stop being true, not to work around or suppress it.

## G. Red-first / revert discipline

For each changed behaviour, the test that fails if that behaviour is reverted:

| Changed behaviour | Test that fails on revert |
|---|---|
| Shard split exists (vs. single 45-min job) | `test_nightly_workflow_houses_performance_and_interpreter_jobs` (updated) — fails if `interpreter-matrix-shard-*` job keys are absent; a real dispatch run additionally fails to complete within budget if reverted to one job (SC-002). |
| Coverage-completeness (FR-004) | `test_interpreter_shard_coverage.py`'s node-id union check — **this is the spec's own required check, not optional plan color** (per the mission brief): it fails if a shard is dropped, a boundary shifts to drop/duplicate a test file, or a shard's selector is mutated to collect 0 tests (SC-003's own mutation-tested positive control). |
| Shard-identity roster / deleted-shard detection (FR-016) | `test_interpreter_shard_coverage.py`'s roster-vs-`jobs:`-keys diff — fails, naming the specific shard, if a shard is removed from `ci-nightly.yml`'s `jobs:` while remaining in `INTERPRETER_SHARDS` (SC-009). |
| Guard updates (FR-009/FR-010) | `test_guard_fails_when_a_shard_is_dropped_from_the_job_list` and `test_guard_fails_when_shards_are_reverted_to_a_single_job` — both explicitly constructed as the required non-vacuity proof (Standing Order #5); reverting the guard update itself (going back to the old hardcoded `"interpreter-matrix"` loop) is caught by the updated `test_nightly_workflow_houses_performance_and_interpreter_jobs` failing to find the old key meaningful against the new roster. |
| Suite-key uniqueness (FR-015) | `test_nightly_suite_keys_are_pairwise_distinct`, non-vacuity proven by `test_suite_key_uniqueness_guard_is_non_vacuous` (two collided `--suite-key` values in a scratch copy) — SC-008. |
| Per-shard sync/venv pinning preserved (FR-008) | A per-shard sync-step-presence assertion (extending `test_nightly_suite_steps_are_fail_loud`'s style) — the positive control is a shard missing the `uv sync --frozen --all-extras --python "3.13"` step, which the assertion must flag. |
| `fail-fast: false` / independent-shard isolation (FR-012) | A real dispatch run with one shard forced red (e.g. a deliberately-failing test temporarily added to one shard's slice during validation, then removed) confirming every OTHER shard still reaches its own conclusion — a unit test alone cannot prove cross-job scheduling independence; this is proven at run 2 (§B). |
| `nightly-summary` `needs:` completeness (FR-006) | A new or extended assertion (in the guard file or the coverage test module) that `nightly-summary`'s `needs:` list is a superset of every roster-declared shard job key — fails if a shard is added to the roster/workflow but not to `needs:`. |
| No `pull_request` trigger introduced (FR-013/C-001) | `test_nightly_workflow_never_triggers_on_pull_request` and `test_no_pull_request_workflow_selects_performance_or_interpreter_jobs` — unchanged, still pass; `FORBIDDEN_PR_PATH_TOKENS`'s existing `"interpreter-matrix"` token still matches every new shard name by construction (see §A). |

## H. Reflexivity

**In-flight runs / concurrent missions**: `ci-nightly.yml`'s `on:` block carries only `schedule` (`cron: '17 3 * * *'`) and `workflow_dispatch` — no `pull_request`, no `push` (verified directly, lines 40-54, matching spec.md's Corrections #3). No in-flight run is retroactively affected when this mission's PR merges: a run already executing keeps running the job graph it started with. The next scheduled `03:17 UTC` cron tick (or the next manual `workflow_dispatch`) is the first execution to pick up the new shard-job graph.

**Concurrent open PRs**: spec.md's Clarifications (#6) recorded 4 open PRs at spec-authoring time (#4995, #5009, #5028, #5137), none touching `ci-nightly.yml`, `.github/ci-module-registry.yml`, or `module-tests.yml`. **This check has a short shelf life and must be re-run by the build/implement phase at the time it actually pushes/dispatches** (`gh pr list` against `spec-kitty/spec-kitty`, re-checking each open PR's changed-file list against those same three paths) — this plan does not re-verify it now beyond citing the spec's own snapshot, since the plan phase performs no push/dispatch itself and a check performed now would be equally stale by implement time.

## I. Phasing

This mission lands as **ONE PR** (spec-kitty's default PR shape per CLAUDE.md/charter) — the diff is bounded (one workflow file, one extended test file, one small new roster module, one new test module) and does not warrant a multi-PR split.

**Worktree isolation (Standing Order #7 / DIRECTIVE_045)**: every step below that pushes, dispatches, or opens the PR runs from spec-kitty's own resolved worktree — `resolve_workspace_for_wp` (CLAUDE.md's "Execution Workspace Strategy") into `.worktrees/<feature>-lane-<id>` per this mission's `lanes.json` — never the primary checkout, regardless of how many WPs the tasks phase ends up materializing for this single-PR mission (see Charter Check §7 above for why a `single_branch`-topology mission still requires a `lanes.json`-resolved workspace either way; see the WP-granularity note immediately below for why the WP count itself is not this plan's call).

**WP granularity is a TASKS-phase decision, not this plan's — distinct from the ONE PR decision above**: `meta.json`'s `single_branch` topology governs lane/branch count, not WP count — a `single_branch` mission can still materialize multiple independently-claimable, independently-reviewable WPs sharing that one branch (CLAUDE.md's dependency-gating section describes WPs as such units regardless of topology). This plan's "ONE PR" framing above is compatible with EITHER shape `/spec-kitty.tasks` might produce: a single WP01 covering IC-01..IC-04 in full, or several WPs (e.g. one per Implementation Concern) that all merge through that same one PR — spec-kitty's own PR-shape default here is one-PR-per-mission regardless of WP count (CLAUDE.md/charter), so splitting WPs would not create a second PR.

**Caveat — a per-IC WP split is not a clean fit here.** IC-01/IC-02's final shape depends on IC-03's dispatch-run output (see IC-03's own Sequencing/depends-on line above, and §I's phasing sequence, where IC-01/IC-02's artifacts are authored in step 2 against an initial guess, IC-03 dispatches in step 3, and IC-01/IC-02's artifacts are then REVISITED in step 4 to finalize N/timeout and possibly redraw boundaries). A per-IC WP split would therefore require a downstream WP (IC-03) to trigger reopening an already-approved/done upstream WP (IC-01 and/or IC-02) so their artifacts can be finalized — and CLAUDE.md's 9-lane status model (`planned → claimed → in_progress → for_review → in_review → approved → done`, plus `blocked`/`canceled`) has no "reopen an approved/done WP" transition to support that; WP dependency gating is forward-only (a dependent WP waits for its dependency to reach `approved`/`done`), never the reverse. A single WP01 spanning all four ICs avoids this problem entirely, since it is not itself settled/approved until the dispatch-driven finalization (IC-03's output feeding back into IC-01/IC-02) is also complete — there is nothing to "reopen" because the one WP covering all of it was never closed before that finalization happened.

This plan does not mandate either shape; that call belongs to the tasks phase, which has visibility into task-level sizing this plan does not attempt to pre-empt. It RECOMMENDS, without requiring, a single WP01 — not merely because the diff is small and cohesive (one workflow file, one extended test file, one small new roster module, one new test module, all tightly coupled through the same shard-identity data), but for the concrete structural reason above: this mission leans toward single-WP01 specifically because IC-03's dispatch-driven revisit of IC-01/IC-02 has no clean expression as separate, independently-closable WPs under a forward-only status model. If the tasks phase nonetheless chooses a several-WPs shape, it should fold IC-03's dispatch/finalize step into whichever WP owns IC-01/IC-02 rather than giving IC-03 its own WP — but the final call, either way, remains the tasks phase's.

Sequence:

1. **Campsite-clean commit** (§C): rewrite the `interpreter-matrix` job's descriptive comments to describe the incoming shard shape, as a distinct, behaviour-preserving first commit.
2. **Author the shard-identity roster + coverage-completeness check + guard updates against the SPEC'd future shape**, with an INITIAL N/timeout guess (e.g. N=3, each shard `timeout-minutes: 45` unchanged, pending real data) — this makes the new tests exist and be exercisable (red-first against the not-yet-split workflow, then green once the mechanical split lands in the same or a following commit within this phase). Before treating IC-02's assertions as meaningful, run `_gate_coverage.parse_workflow`/`gates_for_target` against the actual shard job YAML as authored (not by inspection) and confirm each shard's `BaselineTarget` resolves a non-empty `Gate` list (§A point 6, IC-02 sequencing note).
3. **Push branch + dispatch run 1** (baseline/timing-capture) — build/implement-phase action, per §B.
4. **Finalize N and each shard's `timeout-minutes` from run 1's real numbers** — per §B point 2, this includes redrawing shard boundaries first if any shard's real wall-clock shows a badly-imbalanced partition (a redraw changes that shard's `paths`/`--ignore` arguments directly on the `run:` line, not just a numeric value); update the workflow and roster accordingly; **re-run the empirical parseability check here too if boundaries moved** (§A point 6 / IC-02's sequencing note — step 4a's check alone would miss a regression this step introduces); then re-run the full local gate set (§E/§F) against the finalized shape.
4a. **Remove IC-03's temporary per-shard `--collect-only` measurement scaffolding** (the additional lightweight step/job §B point 1 adds for run 1's measurement) from the workflow before run 2 is dispatched — it is a throwaway, run-1-only artifact and must not ship in the shape validated by run 2 or opened in the PR. Confirm its absence with a final grep/diff, e.g. `grep -n -- '--collect-only' .github/workflows/ci-nightly.yml` returning no hits (the permanent per-shard `pytest` invocations never use `--collect-only`), before proceeding to step 5. Re-run the empirical parseability check here as well — this is ALWAYS one of IC-02's sequencing-note checkpoints, regardless of whether step 4 above needed its own: the first check ran on the initial candidate shard shape (§I step 2, before N/timeout were finalized); step 4 above re-runs it conditionally, only if it redrew shard boundaries; this check runs unconditionally, because step 4a's own scaffolding-removal edit touches the `run:`-line-adjacent workflow content regardless of what step 4 did, and re-confirms parseability on the shape that will actually ship.
5. **Dispatch run 2** (validation) — per §B; confirm SC-001/SC-002/SC-003/SC-005.
6. **Dispatch run 3 only if needed** as the spare — per §B's explicit stop rule (and §B point 4a's run-1-failure accounting, if applicable).
7. **Record evidence** (run URLs + every shard's conclusion) in the PR body and `tracer-approach.md` (NFR-005) — before marking the PR `ready-for-squad`.
8. **Open the PR** targeting `main` from the mission branch, with the full local gate set green, the §4a scaffolding-removal check confirmed, and evidence recorded.
