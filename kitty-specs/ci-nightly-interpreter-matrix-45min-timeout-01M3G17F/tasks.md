---
description: "Work package task list for the nightly interpreter-matrix shard split (issue #4951)"
---

# Work Packages: Nightly interpreter-matrix leg completes within its time cap

**Inputs**: Design documents from `kitty-specs/ci-nightly-interpreter-matrix-45min-timeout-01M3G17F/`
**Prerequisites**: plan.md (required, already authored), spec.md (user stories, already authored), research.md (already authored)

**Tests**: Explicitly requested by spec.md (FR-004/FR-009/FR-010/FR-015/FR-016 and their required mutation tests) — testing work is in scope for this mission, not optional.

**Organization**: Fine-grained subtasks (`Txxx`) roll up into work packages (`WPxx`). Subtask completion is event-sourced via `spec-kitty agent tasks mark-status <Txxx> --status done`; the rows below are reference rows, not checkboxes.

**Prompt Files**: `tasks/WP01-interpreter-matrix-shard-split.md`.

---

## WP granularity: ONE work package (WP01), by explicit decision — not the default

Per plan.md §I ("Phasing"), this plan RECOMMENDS, without requiring, a single WP01
covering Implementation Concerns IC-01 through IC-04. This tasks phase adopts that
recommendation, for the same structural reasons the plan gives (mirrored here per
the mission brief's instruction not to split silently without restating the
reasoning):

1. **Forward-only status model, no reopen transition.** IC-03's dispatch-run output
   (run 1's real per-shard wall-clock and collection counts) feeds back into
   *finalizing* IC-01 (the shard split's real `timeout-minutes`/boundaries) and
   IC-02 (the coverage-completeness check's roster data) — see plan.md's IC-01/IC-02
   "Sequencing/depends-on" lines and §I steps 2→3→4→4a. CLAUDE.md's 9-lane status
   model (`planned → claimed → in_progress → for_review → in_review → approved → done`,
   plus `blocked`/`canceled`) has no "reopen an approved/done WP" transition —
   dependency gating is forward-only (a dependent WP waits for its dependency to
   reach `approved`/`done`, never the reverse). A per-IC WP split would require a
   downstream WP (IC-03) to trigger reopening an already-closed upstream WP
   (IC-01/IC-02), which the status model cannot express.
2. **Ownership-overlap validation.** `finalize-tasks --validate-only` rejects two
   *narrow* WPs claiming the same files, even when linked by a dependency chain —
   only a `scope: codebase-wide` WP is exempt. IC-01/IC-02/IC-04 all touch
   `.github/workflows/ci-nightly.yml` and/or the roster/coverage test files across
   the "author initial guess → revisit after IC-03" boundary. A per-IC split would
   either collide on ownership or require an artificial `codebase-wide` scope this
   mission does not otherwise need.

A single WP01 sidesteps both problems: it is never "closed" until the
dispatch-driven finalization (steps 3→4→4a) is also complete, so there is nothing
to reopen, and one WP naturally owns the whole touched-file set with no overlap to
adjudicate.

**This is also a deliberate deviation from the generic task-authoring guideline**
("target 3–7 subtasks per WP, hard limit 10") — WP01 below has 13 subtasks. This is
not oversight: each subtask traces back to exactly one specific plan.md §I concern
— plan.md §I's own numbered phasing sequence (steps 1, 2, 3, 4, 4a, 5, 6, 7, 8) plus
the explicit baseline-capture and initial-parseability-check steps §F and §A point 6
require *before* step 1 — rather than inventing an artificial split of a single,
tightly sequenced dispatch-driven workflow across multiple WPs, which would
reintroduce the exact forward-only-status-model problem point 1 above describes, one
level down. This is one-to-many, not 1:1, at at least one point: plan.md §I step 2
alone is a single numbered item bundling roster authoring, the shard-split edit, and
the guard update, and was deliberately split into four subtasks (T004-T007) here for
reviewability — one subtask per reviewable concern inside that step, not a
one-step-one-subtask correspondence throughout. The mission's own diff is bounded
(one workflow file, one extended test file, two new small files) and remains
reviewable in one sitting despite the subtask count.

**PR shape**: this mission ships as **ONE PR** (spec-kitty's one-PR-per-mission
default, confirmed applicable by plan.md §I). The single-WP01 decision above does
not change this — a several-WP split, had one been chosen, would still merge
through the same one PR.

## Chokepoint

`.github/workflows/ci-nightly.yml` is a **shared CI workflow file** — any other
in-flight mission editing it would serialize with this one. Because this mission
is single-WP, there is no *internal* WP-to-WP conflict to sequence around, but the
implementer must re-check for external collisions before every push (see the
Write-scope / open-PR overlap section below, and subtasks T008/T011/T013's
pre-push re-verification requirement).

`tests/architectural/test_performance_marker_guard.py` is a second, narrower
shared surface: it is a shared architectural guard covering every nightly job
(`performance`, `e2e`, `stress`, and now every interpreter shard), not scoped to
this mission alone. Any other in-flight mission touching this guard file would
also serialize with this one, for the same reason as `ci-nightly.yml` above.

## Write-scope / open-PR overlap (short shelf life — re-verify before every push)

Checked prior to this tasks-authoring session:
`gh pr list --repo spec-kitty/spec-kitty --state open --limit 100 --json number,files`
returned **7 open PRs**; none of their changed-file lists include
`.github/workflows/ci-nightly.yml`, `tests/architectural/test_performance_marker_guard.py`,
`scripts/ci/nightly_escalation.py`, or this mission's two new files
(`tests/architectural/test_interpreter_shard_coverage.py`,
`tests/architectural/_interpreter_shard_roster.py`). **This check has a short
shelf life** — PRs open and close continuously — and MUST be re-run by the
build/implement phase immediately before every push this WP performs (T008, T011,
T013), not trusted from this snapshot. This is not hypothetical: the count already
drifted once within this mission's own authoring window, from 7 to 8 open PRs
(re-checked at review time), with zero overlap confirmed against all 8 — a future
reader should not treat "7" as a durable number, only as a point-in-time snapshot.

## Path Conventions

- Single project (this repo, spec-kitty itself). CI-infrastructure-only change:
  `.github/workflows/ci-nightly.yml` (edited), `tests/architectural/*.py` (one
  edited, two new). Zero `src/` changes.

**This TASKS phase (this document) performed none of the dispatching or pushing
it describes**, mirroring plan.md §B's self-attestation: no `workflow_dispatch`,
no `git push`, and no branch mutation happened while authoring this tasks
document — confirmed by this session's own tool history (only `Read`/`Bash`
read-only commands, `spec-kitty agent tasks`/`finalize-tasks` CLI invocations,
and local file writes under `kitty-specs/`). Everything in this document is
sequencing for the BUILD/IMPLEMENT phase to execute.

---

## Work Package WP01: Nightly interpreter-matrix shard split (IC-01..IC-04) (Priority: P1)

**Goal**: Split the single, always-timing-out `interpreter-matrix` nightly job into
N independently-budgeted, coverage-complete, non-vacuously-guarded shard jobs, with
real GitHub-hosted-runner timing evidence proving every shard reaches a genuine
`success`/`failure` verdict within its own `timeout-minutes` cap.
**Independent Test**: A manually dispatched `ci-nightly.yml` run (`workflow_dispatch`,
`mode: full`) on this mission's branch shows N independent shard job entries, each
reaching `success` or `failure` (never `cancelled`) — SC-001/SC-002.
**Prompt**: `tasks/WP01-interpreter-matrix-shard-split.md`
**Requirement Refs**: registered via `map-requirements` (see below) — covers
FR-001 through FR-017 in full (this is the mission's only WP).

### Included Subtasks

T001 Baseline architectural-suite capture and pre-existing-failure classification, before any workflow-file edit (plan §F)
T002 Empirical gate-parseability re-derivation against the CURRENT `ci-nightly.yml` (plan §A point 6, checkpoint 0 of 4) — read-only use of `_gate_coverage.py` primitives only
T003 Campsite-clean commit: rewrite the single-job's descriptive comments to describe the incoming shard shape (plan §I step 1 / §C)
T004 Author shard-identity roster + coverage-completeness/roster-diff test module, red-first against the not-yet-split workflow (plan §I step 2, part A; IC-02)
T005 Author the shard split in `ci-nightly.yml` against T004's initial N/timeout guess; update `nightly-summary`'s `needs:` (plan §I step 2, part B; IC-01)
T006 Update the architectural guard: dynamic shard enumeration, non-vacuity mutation tests, suite-key-uniqueness assertion + its 4 mutation tests (plan §I step 2, part C; IC-04)
T007 Empirical gate-parseability re-derivation against the AUTHORED shard job YAML (checkpoint 1 of 4, mandatory) + full local gate run (plan §A point 6 / §E / §F / C-004 / C-005)
T008 Binding pre-push leak check + push branch #1 + dispatch run 1 (baseline/timing-capture) (plan §I step 3 / §B point 1; IC-03)
T009 Finalize N/timeout from run 1's real numbers; redraw boundaries if imbalanced; conditional parseability re-check (checkpoint 2 of 4, fires only if boundaries are redrawn) (plan §I step 4 / §B point 2)
T010 Remove IC-03's temporary `--collect-only` scaffolding; unconditional parseability re-check (checkpoint 3 of 4, mandatory/unconditional) (plan §I step 4a)
T011 Binding pre-push leak check + push #2 + dispatch run 2 (validation); conditional run 3 (spare) under the explicit stop rule (plan §I steps 5-6 / §B points 3-4-4a)
T012 Record dispatch evidence in the PR body and `tracer-approach.md` (plan §I step 7 / §B point 5 / NFR-005)
T013 Binding pre-push leak check + final open-PR-overlap re-check + open the PR (plan §I step 8)

### Implementation Notes

See `tasks/WP01-interpreter-matrix-shard-split.md` for the full per-subtask
guidance, including the exact red-first table (mirroring plan §G), the binding
pre-push leak-check command, the up-to-3-dispatch-run stop rule, and the
`_gate_coverage.py` read-only-use boundary (the `_FLAG_TOKENS` regex defect is
explicitly out of scope for this mission).

### Parallel Opportunities

None declared. This WP is a single, tightly sequenced, dispatch-driven chain —
T001/T002 must precede T003; T003 must precede T004-T006 (campsite-clean lands
first); T004 must be authored red-first before T005 makes it green; T007-T013
form one linear push/dispatch/finalize sequence with hard ordering constraints
(a push cannot precede its leak check; run 2 cannot precede run 1's finalized
numbers). One caveat: T001 and T002 are both read-only checks with no data
dependency on each other (T002 does not need T001's baseline counts, and T001
does not need T002's gate-parseability result) — they are independently
orderable relative to each other and could run in either order, they simply
both must precede T003. This mission has no other WP and executes under a
single-agent execution model, so the distinction is moot in practice; beyond
that one pair, no subtask in this WP is parallel-safe with another.

### Dependencies

None (this is the mission's only WP; no upstream WP to depend on).

### Risks & Mitigations

- **A shard boundary silently drops or duplicates tests** → mitigated by T004's
  coverage-completeness check (FR-004), which is itself mutation-tested (SC-003).
- **A future change silently drops a shard or reverts to one job** → mitigated by
  T006's non-vacuity mutation tests (Standing Order #5, SC-004).
- **Local 24-core numbers or `.github/ci-shard-timings.json` leak into sizing** →
  explicitly forbidden; T009 sources timeout-minutes exclusively from T008's real
  `ubuntu-24.04` dispatch-run 1 data (plan §A "Fresh measurement source").
- **A 4th dispatch run is attempted** → explicitly forbidden under any
  circumstance (T011); the mission STOPS and escalates to the operator instead.
- **An absolute local path leaks into a pushed commit** → mitigated by the
  binding pre-push leak check embedded in T008, T011, and T013 (this repo is
  public; a leak already happened once in this mission's own artifacts. The
  file CONTENT was redacted first, and the OS username was then removed from
  git HISTORY too via an orchestrator-authorized rewrite of this branch's
  history, carried out as part of this mission's own remediation work — see
  the "Known Issue" section immediately below for the full detail).

### Known Issue — tasks-phase git-history leak (remediation completed)

This documents a real, now-remediated defect that lived in this mission's OWN
git history. It is recorded here — rather than deleted — so no later reader
mistakes the leak as never having happened, or mistakes it as still open.
T008/T011/T013's binding leak check cannot fix this by editing files; it
never could, and that was never its job.

- **No fixed count is recorded here, by design.** The binding check defined
  in T008 (`git log -p main..HEAD | grep -cE '/home/|/tmp/'`) returns a
  running total that keeps growing every time this file or
  `tasks/WP01-interpreter-matrix-shard-split.md` is edited: every place in
  either document that quotes the check's own regex pattern in prose (to
  explain or discuss it) is itself a textual match for that same blunt
  pattern, even though it names no real path. Writing a specific number here
  would go stale the moment either document is next edited — including by
  this very edit — so this section deliberately does not do that. Never
  compare a fresh run's total against a number recorded in an earlier
  revision of this file; instead, re-run the check yourself and trace every
  hit to its introducing commit (`git show <sha> | grep -nE '/home/|/tmp/'`),
  classifying each hit per the two categories in "Exact commits responsible"
  below. The check itself is NOT vacuous: an unclassifiable hit, or a
  category-(a)-shaped hit, still blocks the push.
- **Exact commits responsible (historical record — pre-rewrite identities):**
  two categories existed, and only the first was a real leak.
  - **(a) Real leaked path (REMEDIATED).** Pre-rewrite commit `afcf3bcd6`
    ("docs(tasks): record SK-237 confirmation and tasks-phase
    StartupAssetError occurrences") introduced 3 leaked absolute local paths
    (each under the operator's home directory, the exact shape the pre-push
    check's pattern is designed to catch) into `tracer-tooling-friction.md`.
    The later pre-rewrite commit `13dc5d966` ("fix(tasks): redact leaked
    absolute local paths from tracer-tooling-friction.md") first redacted
    the file's CONTENT only (replacing the raw paths with `~/...`) via a
    new, additive commit — content redaction alone, not a history rewrite,
    so `git log -p` kept replaying `afcf3bcd6`'s raw-path diff regardless of
    the file's later content. That was the state of affairs when this
    section was first written. It is no longer the current state: on
    2026-09-27 an orchestrator-authorized history rewrite, carried out during
    this mission's own remediation work, removed the leaked OS username from
    this unpushed branch's git history itself (see
    `tracer-tooling-friction.md`'s "History rewrite note (2026-09-27)" for
    the authoritative record). The rewrite gave every commit on the branch a
    new hash, so `afcf3bcd6` and `13dc5d966` are now dangling, non-ancestor
    objects — pre-rewrite identities kept here purely for historical
    record-keeping, not as current or actionable commit references. Do not
    look them up with `git show`/`git merge-base --is-ancestor` expecting
    them to resolve against `HEAD`; they won't, by design.
  - **(b) Self-referential quotation of the check's own regex pattern.** Any
    commit whose diff shows the check's literal pattern appearing inside
    markdown prose/backticks — explaining or discussing the check — rather
    than inside a real filesystem path. This is an open-ended, growing set:
    both this "Known Issue" section and the T008/T011/T013 fallback guidance
    in `tasks/WP01-interpreter-matrix-shard-split.md` have to quote the
    pattern to explain it, so every future edit to either document
    (including the one that produced this text) mechanically adds another
    commit to this category. Do not try to enumerate it exhaustively by SHA;
    that growth is expected and harmless, and must never be mistaken for a
    new leak. This category is unaffected by the history rewrite and remains
    ongoing.
- **Current file content is clean, and so is history.** The working tree and
  HEAD's tree both show only the redacted `~/...` form, and — since the
  2026-09-27 rewrite — the raw path no longer survives anywhere in
  `main..HEAD`'s reachable git history either. There is no live leak in any
  file's current content, and no known leak remaining in reachable history.
- **Remediation status: DONE.** The orchestrator-authorized history rewrite
  described above, carried out as part of this mission's own remediation
  work, has already been performed. No further history rewrite is needed or
  authorized for this leak. Every agent session in this mission — including
  this fix-round session — remains explicitly forbidden from performing
  `git rebase`/`amend`/`reset`/`checkout`/`restore`/`clean` under any
  circumstance; that prohibition is not what closed this item, the mission's
  own orchestrator-authorized rewrite is. The branch has still not been
  pushed to
  `origin` (`git ls-remote --heads origin` shows no matching ref as of this
  writing); when it is pushed, it will carry the rewritten (clean) history,
  not the pre-rewrite one.
- **What this means for T008 (the first push point):** T008's binding
  pre-push leak check may still read nonzero the first time it runs, but
  only from category (b) — self-referential quotation hits this document and
  the WP file accumulate as they are edited — never from the category (a)
  leak, which is resolved. The baseline is not a fixed number and will keep
  growing as this very document is edited; trace every hit to its
  introducing commit and classify it per the two categories above rather
  than comparing the total to any fixed count. Any hit that traces to a real
  filesystem path under the operator's home directory (i.e. does NOT
  classify as (b)) at this point would be a genuinely NEW leak, not a
  recurrence of the remediated one — treat it accordingly. See T008/T011/T013's
  fallback clause in `tasks/WP01-interpreter-matrix-shard-split.md` for the
  exact classification procedure.

---

## Dependency & Execution Summary

- **Sequence**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 →
  T010 → T011 → T012 → T013 (strictly linear; see "Parallel Opportunities" above).
- **Parallelization**: None within this WP (see above). No other WP exists in
  this mission to parallelize against.
- **MVP Scope**: WP01 in full — there is no smaller shippable slice; the shard
  split, its coverage-completeness proof, and its non-vacuous guard update are
  all required together for SC-001 through SC-010.

---

## Requirements Coverage Summary

| Requirement ID | Covered By Work Package(s) |
|----------------|----------------------------|
| FR-001 | WP01 |
| FR-002 | WP01 |
| FR-003 | WP01 |
| FR-004 | WP01 |
| FR-005 | WP01 |
| FR-006 | WP01 |
| FR-007 | WP01 |
| FR-008 | WP01 |
| FR-009 | WP01 |
| FR-010 | WP01 |
| FR-011 | WP01 |
| FR-012 | WP01 |
| FR-013 | WP01 |
| FR-014 | WP01 |
| FR-015 | WP01 |
| FR-016 | WP01 |
| FR-017 | WP01 |

---

## Subtask Index (Reference)

| Subtask ID | Summary | Work Package | Priority | Parallel? |
|------------|---------|--------------|----------|-----------|
| T001 | Baseline architectural-suite capture + pre-existing-failure classification | WP01 | P1 | No |
| T002 | Empirical gate-parseability re-derivation vs. CURRENT `ci-nightly.yml` | WP01 | P1 | No |
| T003 | Campsite-clean commit (descriptive comments) | WP01 | P1 | No |
| T004 | Author shard roster + coverage-completeness/roster-diff test (red-first) | WP01 | P1 | No |
| T005 | Author the shard split in `ci-nightly.yml` (initial N/timeout guess) | WP01 | P1 | No |
| T006 | Update architectural guard + non-vacuity + suite-key-uniqueness tests | WP01 | P1 | No |
| T007 | Parseability re-check (authored shape) + full local gate run | WP01 | P1 | No |
| T008 | Leak check + push #1 + dispatch run 1 (baseline/timing-capture) | WP01 | P1 | No |
| T009 | Finalize N/timeout from run 1; conditional redraw + parseability re-check | WP01 | P1 | No |
| T010 | Remove `--collect-only` scaffolding; unconditional parseability re-check | WP01 | P1 | No |
| T011 | Leak check + push #2 + dispatch run 2; conditional run 3 (stop rule) | WP01 | P1 | No |
| T012 | Record dispatch evidence (PR body + tracer-approach.md) | WP01 | P1 | No |
| T013 | Leak check + final PR-overlap re-check + open the PR | WP01 | P1 | No |

---

> This tasks.md was authored by the tasks phase of mission
> `ci-nightly-interpreter-matrix-45min-timeout-01M3G17F` (issue #4951), following
> `packs/built-in/missions/mission-steps/software-dev/tasks/prompt.md`'s canonical
> flow — NOT the unwired `tasks-outline`/`tasks-packages` steps (ledger SK-237).
