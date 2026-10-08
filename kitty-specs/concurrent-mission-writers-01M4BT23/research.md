# Research: Concurrent writers to a Mission's files

Brownfield scout squad (three read-only lenses, 2026-10-07) on HEAD `0108c24b`.

## R1 — Which lock already exists, and do all status writers share it?

- **Decision**: reuse `feature_status_lock` as the Mission write lock.
- **Rationale**: lock file `<git-common-dir>/spec-kitty-locks/<mission-dir-name>.status.lock`, re-entrant per thread. `BookkeepingTransaction` (`coordination/transaction.py:558`), `coord_status_lock` (`status_transition.py:435`) and `status.emit` (`emit.py:976`) all resolve to `<slug>-<mid8>` under the same common dir for coord and primary, so nesting re-enters instead of deadlocking. `review_claim_transition` (`workflow_executor.py:1729`) already holds it across capture, emit, commit and rollback, and is the model.
- **Alternatives**: per-file locks (rejected: parallel authority, C-001); git `index.lock` only (rejected: does not cover the working-copy read-modify-write).

## R2 — Where are the blind truncates?

- `workflow.py:283` `_restore_status_artifacts` — capture at `workflow_executor.py:1003` with no lock; truncate after the transaction released its lock (#5819, #5804).
- `status_transition.py:403` coord fallback arm — capture and truncate inside `coord_status_lock`; still blind (no tail check, no size check).
- `transaction.py:1280` `_rollback` — inside the transaction lock; truncates even when nothing was appended and never checks the size did not shrink.
- `runtime/next/runtime_bridge.py:1086` — `run.events.jsonl`, not a Mission file; follow-up.
- **Decision**: one verified rollback replaces the first three. `truncate()` to a size larger than the file pads with NULs, the likely origin of #5804's NUL block once the log was replaced by an atomic rewrite (`store.append_raw_rows_atomic`, `os.replace`) in the window.

## R3 — Claim commit outside the lock (#5468)

- `implement_claim._commit_wp_claim_status` runs `safe_commit` after `start_implementation_status` released the lock; it commits `status.events.jsonl`/`status.json` on primary topologies and so can sweep another writer's appended rows. `agent action implement`'s `_implement_write_claim_and_commit` has the same shape.
- **Decision**: both run inside the Mission write lock.

## R4 — Unlocked read-modify-writes (#5467, #5820)

- `tracer_writer.py:308-316` read → merge → `write_text` inside the `write_artifact` stage thunk; `write_seam.write_artifact` takes no lock; the commit router's `coord_status_lock` covers status files only and runs after the stage.
- `agent/tasks.py:1165-1182` add-history: locate → `append_activity_log` → `write_text`.
- Correct models: `issue_verdict._locked_reread_splice_and_write` (#4884), `acceptance/matrix.locked_reread_splice_and_write` (#4887).
- **Decision**: a generic `locked_rewrite_text` in the primitive; the two domain helpers above stay (they also commit under the lock) and may migrate later.

## R5 — Single_branch occupancy (#5796)

- `implement_phases.allocate` (`:403`) scans with no lock; `record_claim` emits `in_progress` later under the per-mission lock only; two Missions use two different locks.
- The verdict-save queue (`review/verdict_commit_queue.py:51-112`) is the existing checkout-wide lock model.
- **Decision**: a checkout claim lock held from scan to claim emit, lock order checkout → Mission.

## R6 — Shared-workspace warning (#5099)

- `review_claim_transition` has no occupancy notice; `in_progress_wps_in_write_checkout` (`lanes/checkout_occupancy.py:139`) is the only scan and only reports `in_progress`.
- **Decision**: extend the scan into a `shared_workspace_writers` query (advisory).

## R7 — Gate models

- `test_status_events_writes_gate.py` (path-resolving AST census, per-site allowlist), `test_acceptance_matrix_write_seam.py` (caller-qualname allowlist), `test_lock_primitive_ban.py` (content-addressed exemptions).
- **Decision**: new `test_mission_write_discipline.py` with empty allowlists and synthetic non-vacuity sources.
