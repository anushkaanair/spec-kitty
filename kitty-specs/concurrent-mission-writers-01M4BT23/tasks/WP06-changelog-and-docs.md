---
work_package_id: WP06
title: CHANGELOG and docs
dependencies:
- WP05
requirement_refs:
- FR-001
planning_base_branch: issue-5819-concurrent-mission-writers
merge_target_branch: issue-5819-concurrent-mission-writers
branch_strategy: Planning artifacts for this mission were generated on issue-5819-concurrent-mission-writers. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5819-concurrent-mission-writers unless the human explicitly redirects the landing branch.
subtasks:
- T025
- T026
phase: Phase 3
history:
- at: '2026-10-07T19:00:00Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: scribe-sally
authoritative_surface: docs/
create_intent: []
execution_mode: planning_artifact
model: claude-sonnet
owned_files:
- docs/changelog/CHANGELOG.md
- docs/architecture/status-model.md
- docs/development/docs-retrieval-index.yaml
role: documentarian
tags: []
task_type: implement
tracker_refs: []
---

# Work Package Prompt: WP06 – CHANGELOG and docs

## ⚡ Do This First: Load Agent Profile

Use the `/ad-hoc-profile-load` skill (or `spk-doctrine-profile-load`) to load the agent profile in the frontmatter, and behave according to its guidance before parsing the rest of this prompt.

- **Profile**: `scribe-sally`
- **Role**: `documentarian`
- **Agent/tool**: `claude`

---

## ⚠️ IMPORTANT: Review Feedback

Check `spec-kitty agent tasks status --mission concurrent-mission-writers-01M4BT23` and the Activity Log below for a `review_ref`; address every feedback item before marking the WP done.

---

## Context & Constraints (all WPs)

- Binding: `.kittify/charter/charter.md`, `CLAUDE.md`, `kitty-specs/concurrent-mission-writers-01M4BT23/plan.md` — **the "Amendments after the post-plan squad" section overrides D1–D6**. Also `spec.md`, `research.md`, `data-model.md`.
- Terminology: **Mission**, never "feature", in all new prose/identifiers (existing identifiers like `feature_dir` stay).
- Red-first (ADR 2026-07-17-1): write the reproduction test first, run it against the unchanged code and record the RED output (test id + assertion line) in the tracer via `spec-kitty agent tracer-append --mission concurrent-mission-writers-01M4BT23 --category approach --actor <you> --entry "..."`, then fix. Concurrency tests are deterministic: inject `threading.Event`/`Barrier` hooks at seams (monkeypatch), never `sleep` as synchronization; give each wait a timeout so a regression fails instead of hanging. Real git repos via existing fixtures where git matters. Mark tests `pytest.mark.unit` or `pytest.mark.git_repo` per neighbours; only real multi-process tests get `stress`.
- Code quality: ruff, `ruff format --check --force-exclude <files>`, mypy on changed files — zero new findings, no new `# noqa` / `# type: ignore`; cyclomatic complexity ≤ 15; repeated literals (≥3) become constants.
- Coordinate: PR #5876 edits `workflow.py`, `workflow_executor.py`, `status/__init__.py`, `status/store.py`, `status/emit.py`, `tasks_move_task_executor.py`. Keep hunks minimal and away from its regions. Never implement a `git add -A`/`git stash` commit-scope gate (#5443 owns it).
- Commit with explicit paths (`git add <paths>`; never `git add -A`, never `git stash`). Commit message: `fix(<area>): ... (#<issue>)` with the attribution trailer the orchestrator gives you.
- Tests to run: your new tests, the test files of every module you touch, the owning subsystem directory fast tier, plus `make test-fast`; never `make test-full` or a bare `tests/architectural/` sweep (only named gate files). Record exact commands and pass/fail counts in the Activity Log.

## Branch Strategy

- **Strategy**: single_branch (direct_repo), sequential WPs in the repository root checkout
- **Planning base branch**: issue-5819-concurrent-mission-writers
- **Merge target branch**: issue-5819-concurrent-mission-writers

## Objectives & Success Criteria

Document what shipped. After this WP the `[Unreleased]` section of `docs/changelog/CHANGELOG.md` and `docs/architecture/status-model.md` describe the Mission write lock, the verified rollback, the checkout claim lock and the shared-workspace warning.

## Subtasks & Detailed Guidance

### T025 – CHANGELOG

- Under `[Unreleased]` → `Fixed` (follow the file's existing style: bold impact-first lead with the issue number, then before → after, plain language, reader = a Spec Kitty user running parallel agents). One entry per user-visible fix, grouped where they share a cause:
  - A failed status commit no longer erases another agent's committed transition (#5819, #5804, #5468).
  - Overlapping `tracer-append` / `add-history` keep both entries (#5467, #5820).
  - Two overlapping single_branch claims can no longer both pass the shared-checkout check (#5796).
  - `agent action implement` / `review` warn when another actor works in the same checkout (#5099, partial).
- Error code `STATUS_ROLLBACK_REFUSED` named with its remedy.

### T026 – status-model doc

- Add a short section "Mission write lock and rollback" to `docs/architecture/status-model.md`: the one lock (file, key = Mission directory name), the primitive module, the rollback rules (only own uncommitted rows, refuse on doubt), the checkout claim lock and lock order, and the gate. Update the page's `updated:` frontmatter date.
- Run `scripts/docs/check_docs_freshness.py --ci` (errors=0) and `tests/architectural/test_no_legacy_terminology.py`; if the docs retrieval index needs it, `scripts/docs/docs_index.py --write`.

## Definition of Done

- Entries and section present; freshness and terminology checks pass.

## Activity Log
