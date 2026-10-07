---
work_package_id: WP01
title: Review-exit guard and operator force with a note
dependencies: []
requirement_refs:
- FR-001
- FR-002
- FR-003
- FR-004
- FR-005
- NFR-001
- NFR-002
- NFR-003
- C-003
- C-004
planning_base_branch: issue-5446-review-exit-guard
merge_target_branch: issue-5446-review-exit-guard
branch_strategy: Planning artifacts for this mission were generated on issue-5446-review-exit-guard. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5446-review-exit-guard unless the human explicitly redirects the landing branch.
subtasks:
- T001
- T002
- T003
- T004
history: []
agent_profile: implementer-ivan
authoritative_surface: src/specify_cli/status/work_package_lifecycle.py
create_intent:
- tests/specify_cli/cli/commands/agent/test_review_exit_guard_5446.py
execution_mode: code_change
owned_files:
- src/specify_cli/status/work_package_lifecycle.py
- src/specify_cli/cli/commands/agent/workflow_executor.py
- src/specify_cli/cli/commands/agent/workflow.py
- src/specify_cli/cli/commands/agent/workflow_cores.py
- docs/api/agent-subcommands.md
- tests/status/test_work_package_lifecycle.py
- tests/status/test_actor_identity_reconciliation_4665.py
- tests/specify_cli/cli/commands/agent/test_review_exit_guard_5446.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---
# WP01 — Review-exit guard and operator force with a note

## Goal
`agent action implement` must not move a WP out of `for_review`, `in_review` or `approved` unless (a) it is the implementer of record withdrawing an unclaimed `for_review` submission, or (b) an operator passes `--force --note <text>`. Close #5446.

## Context (verified)
- `workflow_executor.py:818` passes `allow_rework=current_lane in {FOR_REVIEW, APPROVED, IN_REVIEW}` for every caller.
- `status/work_package_lifecycle.py:295-317` rework branch: forced emit with default reason "Re-implementing after review feedback" (`:186`), no actor check.
- `_admits_implementer_of_record` (`:147`) is the implementer-of-record seam (uses `review_roles.latest_implementer_actor`).

## Subtasks
- **T001** Land first, as its own commit, a CLI-level reproduction marked `@pytest.mark.p0_repro(issue=5446)` in `tests/specify_cli/cli/commands/agent/test_review_exit_guard_5446.py`, driving the real `agent action implement` path (follow `_rework_loop_harness.py` / `test_rework_unforced_loop.py` for the fixture). It must fail on the planning base. After the fix, remove the `p0_repro` marker (ADR 2026-07-17-1: the reproduction becomes a normal passing test) — keep it as a regression test.
- **T002** In `start_implementation_status`: delete `allow_rework` and `rework_reason`; add an explicit opt-in `review_lane_exit: bool = False` and `operator_force_note: str | None = None`. Only `agent action implement` passes `review_lane_exit=True` (analysis H1): `spec-kitty implement` (`implement_claim.py:~339`) and `orchestrator-api start-implementation` (`orchestrator_api/wp_lifecycle.py:~545`) keep refusing every review lane exactly as today — add one test per caller proving the old refusal holds (in the lifecycle test file, at the lifecycle level, with review_lane_exit False). When `review_lane_exit` is False the review lanes fall through to the existing `WorkPackageStartRejected`.
  - `in_review`: `WorkPackageClaimConflict(wp_id, current_actor or "unknown", actor, review=True)` if that keyword exists (current actor is the reviewer); the CLI error names the routes (wait for the verdict, or `--force --note`).
  - `approved`: `WorkPackageStartRejected` naming `spec-kitty agent tasks move-task <WP> --to planned --review-feedback-file <file>` and `--force --note`.
  - `for_review`: admit only via `_admits_implementer_of_record`; forced event (no FSM edge), reason `"Implementer of record withdrew <WP> from for_review to continue implementation"`; else claim conflict naming the implementer of record (read via `latest_implementer_actor`).
  - With `operator_force_note` (non-blank): forced event from any of the three lanes, reason `f"Operator force: {note}"`.
  - Keep complexity <= 15 (extract a helper for the review-lane branch).
- **T003** (analysis M1/M2/M3) `--force` only applies to a WP in for_review/in_review/approved; on any other lane refuse it before writing (done/canceled stay rejected). Operator force records the `--agent` value as actor (help text: name the agent that will implement; it becomes the implementer of record). Update `docs/api/agent-subcommands.md` for the new flags. Use distinct tools (e.g. `claude` vs `codex`) in tests: identity is per tool. Then: `agent action implement` (`workflow.py:1490`): add `--force` (bool) and `--note` (str). Refuse `--force` without a non-blank `--note` and `--note` without `--force` before any status read/write (exit 1, clear message). Thread the note to `_implement_start_claim` → `start_implementation_status(operator_force_note=...)`.
- **T004** Invert `tests/status/test_work_package_lifecycle.py::test_start_implementation_allows_forced_rework_from_review_lane` (~:476): a different actor is refused on `for_review`; add the implementer-of-record withdrawal positive control, in_review/approved refusals, the operator-force path (reason carries the note), `--force` on a non-review lane refused, a generic-only implementer refused on for_review, `--note` alone refused. Update `test_actor_identity_reconciliation_4665.py` helper that passes `allow_rework`.

## Validation
- `pytest tests/status/test_work_package_lifecycle.py tests/status/test_actor_identity_reconciliation_4665.py tests/specify_cli/cli/commands/agent/test_review_exit_guard_5446.py tests/specify_cli/cli/commands/agent/test_rework_unforced_loop.py tests/specify_cli/cli/commands/agent/test_rework_guard_ratchets.py tests/specify_cli/cli/commands/agent/test_rework_override_classification.py tests/specify_cli/cli/commands/agent/test_workflow.py -q`
- ruff, `ruff format --check --force-exclude`, mypy on changed files.
