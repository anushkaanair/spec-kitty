---
work_package_id: WP05
title: Review-cycle artifacts are never overwritten
dependencies: []
requirement_refs:
- FR-010
- NFR-003
planning_base_branch: issue-5446-review-exit-guard
merge_target_branch: issue-5446-review-exit-guard
branch_strategy: Planning artifacts for this mission were generated on issue-5446-review-exit-guard. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5446-review-exit-guard unless the human explicitly redirects the landing branch.
subtasks:
- T012
- T013
history: []
agent_profile: implementer-ivan
authoritative_surface: src/specify_cli/review/
create_intent:
- tests/review/test_review_cycle_no_overwrite_5194.py
execution_mode: code_change
owned_files:
- src/specify_cli/review/artifacts.py
- src/specify_cli/review/cycle.py
- src/specify_cli/cli/commands/agent/workflow.py
- tests/agent/test_workflow_review_lane_gate.py
- tests/review/test_review_cycle_no_overwrite_5194.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---
# WP05 — Review-cycle artifacts are never overwritten (#5194)

## Goal
`ReviewCycleArtifact.next_cycle_number` (`review/artifacts.py:~385-422`) counts only the directory being written. On a coordination Mission cycle 1 can live on PRIMARY while the next rejection writes to COORD and mints cycle 1 again (in-tree note `consolidation/drivers.py:~1140-1150`). `ReviewCycleArtifact.write` (~:255) uses plain `write_bytes`.

## Subtasks
- **T012** Red-first `@pytest.mark.regression` reproduction (own commit) via `create_rejected_review_cycle` (`review/cycle.py:~1273`) or the move-task rejection path: cycle 1 present on the primary WP dir, write surface resolves to the coordination WP dir → today the new cycle is numbered 1. After the fix: numbered 2, cycle 1 bytes unchanged.
- **T013** In `_allocate_and_write_review_cycle_while_locked` (~:977) compute the next number from the union of the write dir and every read candidate `_review_cycle_wp_dir` consults (coord + primary). Make `ReviewCycleArtifact.write` create exclusively (`open(..., "xb")`) when asked to write a new cycle, so an existing file is never replaced; keep the adopt-existing-candidate path working.

## Notes
- Read candidates come from `_review_cycle_wp_dir` / its candidate list in `review/cycle.py:~176-285`; reuse that resolver, do not re-derive placement (gate `tests/architectural/test_no_write_side_rederivation.py`).
- Also run `tests/coordination/test_verdict_dir_co_resolution.py` and `tests/architectural/test_no_write_side_rederivation.py`.

## Validation
- `pytest tests/review/ -q` (owning subsystem) plus `tests/specify_cli/cli/commands/agent/test_tasks_move_task_seam.py`.
