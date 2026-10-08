---
work_package_id: WP09
title: Built-in software-dev prompts, steps and contracts describe what the CLI does
dependencies:
- WP07
requirement_refs:
- FR-015
- FR-022
- C-003
planning_base_branch: issue-5883-mission-writer-followups
merge_target_branch: issue-5883-mission-writer-followups
branch_strategy: Planning artifacts for this mission were generated on issue-5883-mission-writer-followups. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5883-mission-writer-followups unless the human explicitly redirects the landing branch.
subtasks:
- T038
- T039
- T040
- T041
- T042
- T043
phase: Phase 5 - Pack
history:
- at: '2026-10-08T12:00:00Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: python-pedro
authoritative_surface: packs/built-in/missions/mission-steps/software-dev/
create_intent:
- tests/doctrine/test_software_dev_prompt_walk.py
execution_mode: code_change
model: claude-sonnet
owned_files:
- packs/built-in/missions/mission-steps/software-dev/**
- packs/built-in/missions/software-dev/README.md
- packs/built-in/missions/software-dev/expected-artifacts.yaml
- packs/built-in/missions/software-dev/governance-profile.yaml
- packs/built-in/missions/software-dev/templates/**
- packs/built-in/missions/software-dev/actions/**
- packs/built-in/missions/README.md
- packs/built-in/missions/built_in_step_contracts/**
- packs/built-in/pack-manifest.yaml
- tests/architectural/_builtin_pack_provenance_baseline.yaml
- tests/doctrine/test_software_dev_prompt_walk.py
- tests/doctrine/mission_step_contracts/test_shipped_contracts.py
- tests/specify_cli/test_command_template_cleanliness.py
- tests/prompts/test_tasks_prompt_ownership_metadata.py
- tests/contract/test_tasks_packages_prompt_guards.py
- tests/prompts/test_prompt_fragment_rendering.py
- tests/doctrine/missions/test_mission_steps_layout.py
- tests/specify_cli/cli/commands/test_analyze_surface_agreement.py
- tests/dossier/test_manifest_guard_parity.py
- tests/specify_cli/regression/_twelve_agent_baseline/**
- tests/specify_cli/skills/__snapshots__/**
tags: []
tracker_refs: []
---
# Work Package Prompt: WP09 – Built-in software-dev prompts, steps and contracts describe what the CLI does

## Objective

Every shipped software-dev step prompt, `step.yaml`, step contract, `expected-artifacts.yaml`, README and governance profile describes what the CLI actually does. The tasks and tasks-finalize prompts name `/spec-kitty.analyze` as required before implement, with its staleness rule. The scripted prompt walk (SC-008) finds 0 refused instructions and 0 non-existent references. The provenance ratchet counts go down.

## Independent test

`tests/doctrine/test_software_dev_prompt_walk.py` (SC-008, C12): command paths and each `--option` resolve against Click; rendered step-contract bootstrap commands parse; every "next advances to X" claim matches the runtime order; consumer paths resolve against a `spec-kitty init` fixture with an explicit placeholder list; covers the CLI-driven implement, review, accept and tasks-finalize prompts.

## Subtasks

- **T038**: Red-first: the prompt walk gate fails on today's files (refused `charter context --profile/--tool`, missing `--mission`, false "next advances" claims, nonexistent paths)
- **T039**: Step contracts: drop `--profile`/`--tool` bootstrap inputs in every built-in contract (C1, the one Locality exception); fix the C2 items; update `test_shipped_contracts.py`
- **T040**: Tasks family prompts (tasks, tasks-outline, tasks-packages, tasks-finalize, `tasks/guidelines.md`): analyze required with its staleness rule (FR-015), dedupe, false "next advances" claims, the template reference (C6), the dependency command, the provenance tokens, "feature" wording, `/ad-hoc-profile-load`
- **T041**: Other prompts (analyze, accept, implement, review, plan, specify): the R7 items plus C3 (`--mission` boilerplate), C4, C5, C10 (recovery recipe outside the checkout)
- **T042**: Pack files: `software-dev/README.md`, `missions/README.md`, `expected-artifacts.yaml` (retired tasks_* ids, analysis report on implement), `governance-profile.yaml`, the `step.yaml` chain (tasks-finalize depends on tasks-packages, analyze depends on tasks)
- **T043**: Ratchet baseline lowered by hand per entry (diff only goes down, C8); pinning tests and snapshots updated (C7); `spec-kitty doctrine regenerate-graph`; reinstall, then the roundtrip test

## Notes and risks

Run the specific gates: `tests/architectural/test_builtin_pack_provenance_ratchet.py`, `tests/doctrine/test_builtin_cli_command_references.py`, `tests/doctrine/test_doctrine_regenerate_graph_roundtrip.py` and the pinning tests listed in R7/C7. Owned paths that do not exist under these names: find the real ones and record them in the Activity Log.

## Dependencies

WP07

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
