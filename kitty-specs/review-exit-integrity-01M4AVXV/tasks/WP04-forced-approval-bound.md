---
work_package_id: WP04
title: Forced approvals do not restamp the approval bound
dependencies: []
requirement_refs:
- FR-009
- NFR-003
- C-005
planning_base_branch: issue-5446-review-exit-guard
merge_target_branch: issue-5446-review-exit-guard
branch_strategy: Planning artifacts for this mission were generated on issue-5446-review-exit-guard. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5446-review-exit-guard unless the human explicitly redirects the landing branch.
subtasks:
- T010
- T011
history: []
agent_profile: implementer-ivan
authoritative_surface: src/specify_cli/consolidation/approved_bound.py
create_intent: []
execution_mode: code_change
owned_files:
- src/specify_cli/consolidation/approved_bound.py
- src/specify_cli/cli/commands/agent/tasks_move_task_executor.py
- src/specify_cli/cli/commands/agent/tasks_move_task.py
- src/specify_cli/cli/commands/agent/status.py
- tests/consolidation/test_approved_bound.py
- tests/consolidation/test_approved_bound_residuals.py
- tests/terminus/test_forced_approval_restamp.py
- AGENTS.md
- docs/adr/4.x/2026-10-04-5-approval-stamp-bounds-the-approved-claim.md
role: implementer
tags: []
task_type: implement
tracker_refs: []
---
# WP04 — Forced approvals do not restamp the approval bound (#5721 forced-approval residual)

## Goal
`approved_bound._is_approval_transition` (~:219) counts every move into `approved`, so `move-task <WP> --to approved --force` restamps the lane. Count a move into `approved` only when it is unforced, or an arbiter override (`review/arbiter.py::is_arbiter_override_history` over the prior events of that WP). Approved-reviewed attestations (`is_approved_reviewed_attestation`) still count. Also count (analysis H2) a forced move into `approved` that carries an approved review result / reviewer evidence (reviewer forcing past an unrelated gate; `--self-review-fallback`, which requires `--force`). FIRST verify through the real `move-task` path what a bare `move-task <WP> --to approved --force` writes for approved->approved, canceled->approved and in_progress->approved (does the hop attach a review_result?) and build the predicate on what actually distinguishes a forced restamp with no review from a recorded review. Forced approvals with no review evidence are skipped (fallback to the newest review approval; none → `APPROVAL_STAMP_MISSING`).

## Subtasks
- **T010** Red-first (own commit): parametrized cases in `test_approval_stamp_selection` (forced approved->approved, forced canceled->approved, forced in_progress->approved are not stamps; arbiter override counts; attestation counts) and one `check_lane` case: approval, late commit, forced re-approval → `LANE_MOVED_AFTER_APPROVAL`.
- **T011** Implement in `_newest_approval`/`_is_approval` (pass the event prefix). Verify `consolidation -> review.arbiter` import is allowed by the layer gates (if not, move the pure predicate). Add `forced_approval_warning(event, events, ...)` beside `unstamped_approval_warning` and wire it at `tasks_move_task_executor.py` (~:308) and `agent/status.py` (~:457): one line on stderr saying the forced approval is not a review approval and consolidate bounds the WP at its last review approval. Pass the arbiter predicate only the events strictly before the candidate approval and import it lazily (L6). In CLAUDE.md (Consolidation section) and the ADR residual list, mark the forced-approval restamp closed for forced approvals without review evidence and keep the unforced `in_progress -> approved` edge as an open residual. Update the residual notes in `test_approved_bound_residuals.py` docstring if they name this case.

## Validation
- `pytest tests/consolidation/test_approved_bound.py tests/consolidation/test_approved_bound_residuals.py tests/consolidation/test_approved_attestation.py tests/terminus/test_unstamped_approval_attestation.py tests/consolidation/test_hollow_review_warnings.py tests/review/ -q -k "arbiter or approved or attest"` plus the layer-rule gate files the import touches.
