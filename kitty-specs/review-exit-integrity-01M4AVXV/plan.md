# Implementation Plan: A WP leaves review or approval only through a recorded verdict or an operator force with a note

**Branch**: `issue-5446-review-exit-guard` (planning base and merge target; topology `single_branch`) | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)
**Input**: Mission specification from `kitty-specs/review-exit-integrity-01M4AVXV/spec.md`

## Summary

`agent action implement` hands `allow_rework=True` to the status lifecycle for every caller whose WP is `for_review`, `in_review` or `approved`. The lifecycle then emits a forced move to `in_progress` with the default reason "Re-implementing after review feedback". It skips the actor check that the `claimed` and `in_progress` branches run. The fix moves the decision of who may leave a review lane into the lifecycle (one place), driven by the existing implementer-of-record projection. The boolean is replaced by an explicit operator override (`--force` + `--note`). Four repairs follow:
- the approval deadlock a forced `in_review` exit leaves behind,
- the consolidation reader of "who implemented",
- the approval-stamp reader for forced approvals,
- the review-cycle number allocator.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: typer, rich, `spec_kitty_events` (reducer, read-only for this Mission)
**Storage**: append-only `status.events.jsonl` per Mission; `review-cycle-N.md` files under `tasks/<wp-slug>/`
**Testing**: pytest. A red-first `p0_repro(issue=5446)` CLI-level reproduction, then focused unit tests per seam. Blast radius: `tests/status`, `tests/specify_cli/cli/commands/agent`, `tests/consolidation`, `tests/review`, `tests/unit/status`, plus `make test-fast`
**Target Platform**: Linux, macOS, Windows CLI
**Project Type**: single
**Performance Goals**: no added git calls on the implement path. The bound change only filters events that are already read.
**Constraints**: do not edit spec-kitty-events; do not change `wp_state` force semantics; complexity <= 15
**Scale/Scope**: about 8 source files, 5 concerns

## Charter Check

- **Single canonical authority**: the "who may leave review" rule lives once, in `status/work_package_lifecycle.start_implementation_status`. "Who implemented" lives once, in `status/review_roles.latest_implementer_actor`, which the consolidation preflight now uses. PASS.
- **ATDD / red-first (C-011, ADR 2026-07-17-1)**: the p0_repro lands as the first commit, RED on the planning base. PASS.
- **Architectural alignment**: consolidation imports only from the `specify_cli.status` facade (SR-2). The lifecycle keeps its lazy-import seams. PASS.
- **Terminology**: Mission, never feature, in new prose and messages. PASS.
- **No global force change (C-003)**: no ADR needed. The state machine is untouched. PASS.

## Design decisions

1. **Remove `allow_rework`; add `operator_force_note: str | None`** to `start_implementation_status`. Rules, in the lifecycle, under the status lock:
   - **`in_review`**: raise `WorkPackageClaimConflict(wp, <current reviewer>, actor)`. The review claim is the reviewer's.
   - **`approved`**: raise `WorkPackageStartRejected`, naming `agent tasks move-task <WP> --to planned --review-feedback-file <file>`.
   - **`for_review`**: admit only when `_admits_implementer_of_record(...)` holds. The event is forced (no FSM edge exists for `for_review -> in_progress`), with the reason "Implementer of record withdrew <WP> from for_review to continue implementation". Any other actor gets `WorkPackageClaimConflict` naming the implementer of record.
   - **With `operator_force_note`**: any of the three lanes moves to `in_progress` as a forced event whose reason is `Operator force: <note>`.
   - The default "Re-implementing after review feedback" string is deleted.
2. **CLI**: `agent action implement` gains `--force` and `--note`. `--force` needs a non-blank `--note`, and `--note` needs `--force`. Both checks run before any status read or write. `--force` is threaded only to the lifecycle; it does not bypass dependency, charter or workspace gates.
3. **Deadlock**:
   - `ReviewResultLookup` gains `cleared_without_verdict: bool`. It is true when the reduced slot is present and raw `None`, which the reducer writes only on an `in_review` exit with no verdict.
   - `resolve_review_verdict_facts` treats a cleared slot as "no verdict on record", the same as a never-reviewed WP. Approval then proceeds, and the approval event writes a fresh `review_result` that repairs the slot.
   - A truly malformed slot still refuses. Its message no longer names the synthetic `review-cycle-damaged-event-record.md` as something to repair. It names the unreadable recorded verdict and the reject-and-re-review route.
4. **#5340**: `consolidation/preflight._independent_reviewer_confirmed` reads the implementer through `latest_implementer_actor` / `is_latest_implementer` (facade imports), so a reviewer's rework verdict is no longer counted as the implementer. The reducer's `implementer_of_record` slot is documented as claim provenance. Changing it would require a snapshot generation bump; that is out of scope and named in the PR.
5. **#5721 (forced approvals)**:
   - `approved_bound._newest_approval` counts a move into `approved` only when it is unforced or an arbiter override (`review.arbiter.is_arbiter_override_history` over the prior events). Approved-reviewed attestations still count.
   - A forced non-arbiter approval is skipped, so the bound falls back to the newest review approval (lenient and sound), or to `APPROVAL_STAMP_MISSING` when there is none.
   - A one-line warning prints at `move-task` / `status emit` time.
6. **#5194**:
   - The allocator computes the next cycle number from the union of every surface the readers consult (write surface plus the coordination/primary read candidates).
   - `ReviewCycleArtifact.write` creates the file exclusively (`xb`), so an existing cycle file is never replaced.

## Project Structure

### Documentation (this mission)

```
kitty-specs/review-exit-integrity-01M4AVXV/
├── spec.md
├── plan.md
├── tasks.md
└── tasks/
```

### Source Code (repository root)

```
src/specify_cli/status/work_package_lifecycle.py      # IC-01 guard
src/specify_cli/cli/commands/agent/workflow_executor.py, workflow.py   # IC-01 CLI flags
src/specify_cli/status/reducer.py (ReviewResultLookup) # IC-02
src/specify_cli/cli/commands/agent/tasks_verdict_persistence.py, tasks_transition_core.py  # IC-02
src/specify_cli/consolidation/preflight.py, status/review_roles.py  # IC-03
src/specify_cli/consolidation/approved_bound.py, tasks_move_task_executor.py, agent/status.py  # IC-04
src/specify_cli/review/artifacts.py, review/cycle.py   # IC-05
```

**Structure Decision**: single project; existing modules only, no new packages.

## Implementation Concern Map

### IC-01 — Review-exit guard and operator override

- **Purpose**: close #5446 at its seam: the implement lifecycle decides who may leave a review lane, and the CLI offers an explicit operator force with a note.
- **Relevant requirements**: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-002
- **Affected surfaces**: `status/work_package_lifecycle.py`, `cli/commands/agent/workflow_executor.py`, the `agent action implement` typer command, `tests/status/test_work_package_lifecycle.py` (invert :476), a new p0_repro CLI test
- **Sequencing/depends-on**: none
- **Risks**: the #5377 resume path and `test_rework_guard_ratchets.py` must stay green; the `in_progress` branch is untouched.

### IC-02 — Approval deadlock repair

- **Purpose**: a WP forced out of `in_review` with no verdict can be approved after a new review cycle; an unreadable slot gets an honest message.
- **Relevant requirements**: FR-006, FR-007
- **Affected surfaces**: `status/reducer.py` (`ReviewResultLookup`, `review_result_from_state`), `tasks_verdict_persistence.py`, `tasks_transition_core.py`
- **Sequencing/depends-on**: none (the operator force of IC-01 can still create the state)
- **Risks**: readers that inject `(True, None)` as "damaged" must keep their meaning; the new flag is additive.

### IC-03 — One implementer-of-record authority

- **Purpose**: the consolidation hollow-review check uses the status projection (#5340).
- **Relevant requirements**: FR-008
- **Affected surfaces**: `consolidation/preflight.py`, `status/review_roles.py` (doc), `status/reducer.py` (doc of `implementer_of_record`)
- **Sequencing/depends-on**: none
- **Risks**: the raw-dict fixtures in `test_hollow_review_warnings.py` lack `at`/`execution_mode`; the reader must stay tolerant.

### IC-04 — Forced approvals do not restamp the bound

- **Purpose**: close the forced-approval residual of #5721.
- **Relevant requirements**: FR-009
- **Affected surfaces**: `consolidation/approved_bound.py`, `tasks_move_task_executor.py`, `cli/commands/agent/status.py`
- **Sequencing/depends-on**: none
- **Risks**: arbiter overrides and attestations must still count; the import direction from `consolidation` to `review.arbiter` must be checked against the layer gates.

### IC-05 — Review-cycle artifacts are never overwritten

- **Purpose**: close #5194.
- **Relevant requirements**: FR-010
- **Affected surfaces**: `review/artifacts.py`, `review/cycle.py`
- **Sequencing/depends-on**: none
- **Risks**: the adopt-existing-candidate path must keep working; exclusive create must not break idempotent re-runs.
