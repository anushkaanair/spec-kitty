---
work_package_id: WP01
title: One canonical Mission lock key for every lock caller
dependencies: []
requirement_refs:
- FR-005
- C-002
- NFR-002
- NFR-003
- C-006
planning_base_branch: issue-5883-mission-writer-followups
merge_target_branch: issue-5883-mission-writer-followups
branch_strategy: Planning artifacts for this mission were generated on issue-5883-mission-writer-followups. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5883-mission-writer-followups unless the human explicitly redirects the landing branch.
subtasks:
- T001
- T002
- T003
- T004
- T005
phase: Phase 1 - Lock key
history:
- at: '2026-10-08T12:00:00Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: python-pedro
authoritative_surface: src/specify_cli/status/
create_intent:
- tests/status/test_mission_lock_key.py
execution_mode: code_change
model: claude-sonnet
owned_files:
- src/specify_cli/status/mission_write.py
- src/specify_cli/status/locking.py
- src/specify_cli/status/__init__.py
- src/specify_cli/missions/_read_path_resolver.py
- src/specify_cli/coordination/transaction.py
- src/specify_cli/coordination/status_transition.py
- src/specify_cli/coordination/coord_seed.py
- src/specify_cli/lanes/branch_naming.py
- src/specify_cli/status/emit.py
- src/specify_cli/status/work_package_lifecycle.py
- src/specify_cli/status/lifecycle_events.py
- src/specify_cli/status/migrate_lifecycle_envelope.py
- src/specify_cli/cli/commands/agent/tasks_move_task_executor.py
- src/specify_cli/cli/commands/agent/tasks_mark_status.py
- src/specify_cli/cli/commands/agent/status.py
- src/specify_cli/cli/commands/agent/finalize_status_surface.py
- src/specify_cli/decisions/emit.py
- src/specify_cli/retrospective/lifecycle_events.py
- src/specify_cli/review/cycle.py
- src/specify_cli/migration/backfill_runtime_state.py
- src/specify_cli/migration/rebuild_state.py
- src/specify_cli/migration/verdict_provenance_backfill.py
- tests/status/test_mission_lock_key.py
tags: []
tracker_refs: []
---
# Work Package Prompt: WP01 – One canonical Mission lock key for every lock caller

## Objective

`mission_lock_key(feature_dir)` is the one key every per-Mission lock caller uses (`mission_write_lock`, `hold_mission_write_lock`, every direct `feature_status_lock` caller, `BookkeepingTransaction`, `coord_status_lock`, `_holds_mission_lock`/`capture_rollback_point`), so a legacy bare-directory coordination Mission (`060-test` primary with a `060-test-<mid8>` coordination surface) locks one file from every door, in one order.

## Independent test

`tests/status/test_mission_lock_key.py`: key equality across primary, coordination and flat Missions plus the bare-directory coordination fixture; the mid8 cascade; the empty-mid8 typed error; key stability inside a hold; a cross-thread lock-order test (lifecycle path vs implement claim path) that does not deadlock; the subprocess-count check.

## Subtasks

- **T001**: Red-first: the bare-directory coordination fixture shows the transaction and `mission_write_lock`/emit resolving different lock files, and `capture_rollback_point` raising under a held primary lock after a naive rekey (plan A1, A2)
- **T002**: `mission_lock_key(feature_dir)` in `status/mission_write.py`, using the transaction's mid8 cascade through one shared helper (with `branch_naming`/`resolve_transaction_mid8`); a typed error for a coordination-routed Mission with no resolvable mid8; the key read from the canonical primary `meta.json` via the read-path resolver (A3, A4)
- **T003**: Thread-local held-key reuse: nested entries for the same Mission reuse the held key; a test with `flatten_coordination_metadata`-style meta mutation inside a hold (A4)
- **T004**: Route every per-Mission lock caller through the key: `mission_write_lock`, `hold_mission_write_lock`, `_holds_mission_lock`/`capture_rollback_point`, `mission_write_lock_dir`, `BookkeepingTransaction._mission_specs_dir_name`, `coord_status_lock` and every direct `feature_status_lock(root, X.name)` caller listed in A1 (emit, work_package_lifecycle, lifecycle_events, migrate_lifecycle_envelope, move-task, mark-status, agent status, decisions emit, finalize status surface, retrospective lifecycle events, review cycle, the migrations)
- **T005**: Disposition the two Rule 1 whole-file rewrites in files this WP owns: `migration/rebuild_state.py` (`os.replace` onto the events log) and `status/migrate_lifecycle_envelope.py` run their rewrite under the Mission lock (plan A7). Cross-thread lock-order test on the bare-directory coordination fixture (lifecycle path vs implement claim path); NFR-003 subprocess delta with a warmed `git_common_dir` cache (A12)

## Notes and risks

This WP changes which file a writer locks on legacy Missions; it never adds a second mechanism (C-002). Keep `feature_status_lock`'s signature; callers pass `mission_lock_key(...)`. Re-derive the caller list with `grep -rn "feature_status_lock(\|mission_write_lock(\|hold_mission_write_lock(" src`.

## Dependencies

None.

## Rules for every WP in this Mission

- Read `.kittify/charter/charter.md`, then `kitty-specs/mission-writer-followups-01M4CYWW/spec.md` and `plan.md`. The plan's "Amendments after the post-plan squad" section (A*, B*, C* items) is binding and overrides D1–D10 where they disagree. `research.md` line numbers are indicative; re-derive them.
- **Red-first (C-006).** For every requirement marked "no-op passable: no", commit the reproduction first and show it failing against the pre-fix code; record the command and the failing output in the Activity Log. Compound requirements are proven part by part.
- **Concurrency tests (NFR-001).** Run the two writers on distinct threads or processes (the lock is re-entrant per thread), use injected pause points rather than sleeps, and pass 5 of 5 repeated runs. Mutation-check each one: remove the lock and confirm the test fails.
- **Quality (NFR-005).** `uv run --frozen ruff check <files>`, `uv run --frozen ruff format --check --force-exclude <files>` and `uv run --frozen mypy <files>` report no new issues. No new `noqa` or `type: ignore`. Every touched function has complexity ≤ 15. Every new branch or helper has a focused test.
- **Tests.** Run your own test files, the test directory of each owning subsystem and `make test-fast`. Never run `make test-full` or the bare `tests/architectural/` directory; run only the specific architectural gate files you implicate. Use `.venv/bin/python -m pytest ...` (not a bare `uv run` that re-syncs). Record the exact commands and the pass/fail counts in the Activity Log.
- **Baseline red.** Classify a failure you did not cause per CLAUDE.md (pre-existing P0, CI env, stale install, stale venv) before chasing it.
- **Commits.** Commit with explicit paths (never `git add -A`, never `git stash`), with a conventional subject scoped `(mission-writer-followups)`, and end every message with:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01WiYizc1WL4ic8QMezcXUiy
  ```
  Commit after each subtask so a lost session loses nothing. Do not push; the orchestrator pushes.
- **Status.** Mark each subtask with `spec-kitty agent tasks mark-status <Txxx> --status done --mission mission-writer-followups-01M4CYWW`. When the WP is complete, move it with `spec-kitty agent tasks move-task <WP> --to for_review --mission mission-writer-followups-01M4CYWW --note "<summary>"`.
- **Sources only (C-003).** Edit `packs/built-in/...` sources, never the generated agent copies.

## Definition of done

- Every subtask is done and marked; every red-first reproduction was shown failing on the pre-fix code and now passes.
- The owned tests, the owning subsystem test directories, the implicated architectural gate files and `make test-fast` pass, with the commands and counts recorded in the Activity Log.
- ruff, ruff format and mypy are clean on changed files; there are no new suppressions.
- Every change is committed with explicit paths.

## Activity Log

- 2026-10-08T12:00:00Z – system – Prompt created.
