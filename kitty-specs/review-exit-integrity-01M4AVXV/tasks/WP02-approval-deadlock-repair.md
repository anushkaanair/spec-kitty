---
work_package_id: WP02
title: Approval works after a forced review exit
dependencies: []
requirement_refs:
- FR-006
- FR-007
- NFR-003
- C-001
planning_base_branch: issue-5446-review-exit-guard
merge_target_branch: issue-5446-review-exit-guard
branch_strategy: Planning artifacts for this mission were generated on issue-5446-review-exit-guard. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5446-review-exit-guard unless the human explicitly redirects the landing branch.
subtasks:
- T005
- T006
- T007
history: []
agent_profile: implementer-ivan
authoritative_surface: src/specify_cli/cli/commands/agent/tasks_verdict_persistence.py
create_intent:
- tests/specify_cli/cli/commands/agent/test_approval_after_forced_review_exit.py
execution_mode: code_change
owned_files:
- src/specify_cli/status/reducer.py
- src/specify_cli/cli/commands/agent/tasks_verdict_persistence.py
- src/specify_cli/cli/commands/agent/tasks_transition_core.py
- tests/status/test_reducer.py
- src/specify_cli/agent_utils/status.py
- src/specify_cli/cli/commands/agent/tasks_parsing_validation.py
- tests/review/test_verdict_seam_reader_collapse.py
- tests/specify_cli/cli/commands/agent/test_tasks_transition_core.py
- tests/specify_cli/cli/commands/agent/test_approval_after_forced_review_exit.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---
# WP02 — Approval works after a forced review exit

## Goal
After a forced `in_review -> in_progress` with no verdict, the reduced state holds `review_result: null` (spec-kitty-events `diary.py` ~1156; do NOT edit that package). `resolve_review_verdict_facts` (`tasks_verdict_persistence.py:~608-613`) maps it to the synthetic `review-cycle-damaged-event-record.md` and `_guard_rejected_verdict` (`tasks_transition_core.py:~598-603`) refuses every later approval. Repair it CLI-side.

## Subtasks
- **T005** Red-first test (its own commit) through the real `move-task` path: forced in_review exit with no verdict, resubmit, review claim, approve → today refused. After the fix: approval succeeds and the approval event carries a populated `review_result`.
- **T006** `status/reducer.py`: add `cleared_without_verdict: bool = False` to `ReviewResultLookup`; `review_result_from_state` sets it for a raw `None` value (the reducer writes `None` only on an in_review exit with no verdict); malformed values keep `(slot_present=True, result=None, cleared_without_verdict=False)`. In `resolve_review_verdict_facts` treat `cleared_without_verdict` as "no verdict on record" (same as absent). Check `_persist_approved_review_cycle` so a first-pass-style approval artifact is still written.
- **T007** Malformed slot refusal: stop naming the synthetic file as the thing to repair. Keep the substring "no parseable review verdict" (tests depend on it); say the recorded review result in the status event log is unreadable and name the route `spec-kitty agent tasks move-task <WP> --to planned --review-feedback-file <file>` followed by a new review.

## Notes from analysis
- `tests/status/test_reducer.py:~1150-1152` asserts equality with `(True, None)`; update it for the new field (L2).
- The status board (`agent_utils/status.py:~255`) must not label a cleared slot as damaged (L3).
- Accepted: a cleared slot hides an earlier cycle's rejection from the verdict facts (the events keep it); record this in the PR (L4).

## Validation
- `pytest tests/status/test_reducer.py tests/specify_cli/cli/commands/agent/test_tasks_transition_core.py tests/specify_cli/cli/commands/agent/test_approval_after_forced_review_exit.py tests/review/test_verdict_seam_reader_collapse.py tests/specify_cli/cli/commands/agent/test_tasks.py tests/specify_cli/cli/commands/agent/test_tasks_parsing_validation.py tests/specify_cli/cli/commands/agent/test_tasks_move_task_seam.py -q`
