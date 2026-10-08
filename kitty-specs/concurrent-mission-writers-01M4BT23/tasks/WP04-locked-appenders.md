---
work_package_id: WP04
title: Locked appenders and lock keys
dependencies:
- WP01
requirement_refs:
- FR-006
- FR-007
planning_base_branch: issue-5819-concurrent-mission-writers
merge_target_branch: issue-5819-concurrent-mission-writers
branch_strategy: Planning artifacts for this mission were generated on issue-5819-concurrent-mission-writers. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5819-concurrent-mission-writers unless the human explicitly redirects the landing branch.
subtasks:
- T017
- T018
- T019
- T020
phase: Phase 2
history:
- at: '2026-10-07T19:00:00Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: python-pedro
authoritative_surface: src/specify_cli/retrospective/
create_intent:
- tests/specify_cli/cli/commands/agent/test_concurrent_appenders.py
- tests/status/test_status_lock_keys.py
execution_mode: code_change
model: claude-sonnet
owned_files:
- src/specify_cli/cli/commands/agent/tasks.py
- src/specify_cli/retrospective/tracer_writer.py
- src/specify_cli/cli/commands/agent/tasks_move_task_executor.py
- src/specify_cli/cli/commands/agent/tasks_mark_status.py
- src/specify_cli/status/lifecycle_events.py
- tests/specify_cli/cli/commands/agent/test_concurrent_appenders.py
- tests/status/test_status_lock_keys.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---

# Work Package Prompt: WP04 – Locked appenders and lock keys

## ⚡ Do This First: Load Agent Profile

Use the `/ad-hoc-profile-load` skill (or `spk-doctrine-profile-load`) to load the agent profile in the frontmatter, and behave according to its guidance before parsing the rest of this prompt.

- **Profile**: `python-pedro`
- **Role**: `implementer`
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

Fix #5820 and #5467 and close the lock-key divergence (amendments A8, A10). After this WP:

- `agent tasks add-history` re-reads and rewrites the WP file through `locked_rewrite_text` (the read happens inside the primitive).
- `agent tracer-append` holds `mission_write_lock` around the whole `write_artifact(...)` call (stage read → merge → write → commit), so overlapping appends keep both findings in the committed file.
- `tasks_move_task_executor.py:581`, `tasks_mark_status.py:317` (incl. the owned-checkout `nullcontext()`) and `status/lifecycle_events.py:302` lock on the Mission directory name, never the slug.

## Subtasks & Detailed Guidance

### T017 – Red-first reproductions

- New `tests/specify_cli/cli/commands/agent/test_concurrent_appenders.py`.
- #5820: WP01 file; writer A runs add-history and is paused after its read (hook `locate_work_package` or the moment before the write); writer B runs add-history to completion; release A. Assert both notes are in the activity log. Post-fix A's read happens inside the lock, so B blocks on the lock instead — drive B in a thread released by A's "read done" event, join with timeout, same test RED before / GREEN after.
- #5467: same shape for `append_tracer_finding` (`retrospective/tracer_writer.py:243`) on one category; assert both entries are in the committed `traces/<category>.md` (read via `git show HEAD:...` on the write surface) — test both a coord and a lanes/single_branch Mission if the fixtures allow (the bug reproduces on both).
- Lock-key: `tests/status/test_status_lock_keys.py` — for a Mission whose directory name differs from its slug (legacy shape, or slug without mid8 when the dir embeds it — construct whichever the resolver supports), assert move-task, mark-status (owned and non-owned) and the lifecycle-event writer lock the same lock file as `status.emit` (spy on `feature_status_lock_path` / `_get_thread_locks()` membership).
- Record RED in the tracer.

### T018 – add-history via `locked_rewrite_text`

- `src/specify_cli/cli/commands/agent/tasks.py` add-history (~:1157-1182): resolve `wp.path` once (as now, for error handling), then
  ```python
  def _append(current: str | None) -> str:
      wp_now = <parse current text into frontmatter/body/padding with the same splitter locate_work_package uses>
      return build_document(wp_now.frontmatter, append_activity_log(wp_now.body, history_entry), wp_now.padding)
  locked_rewrite_text(wp.path, _append, feature_dir=<mission dir>, repo_root=repo_root)
  ```
  Find the existing pure splitter (`split_frontmatter`/`parse_work_package` in `task_utils`); do not re-implement parsing. `append_activity_log` must be called only inside the transform (the WP05 gate checks this pair: `locate_work_package` read + `append_activity_log` sink must sit in one locked region — the transform satisfies it because the read of record is the primitive's).
- Encoding: match today's `write_text(..., encoding="utf-8")`.

### T019 – tracer-append under the Mission lock

- `retrospective/tracer_writer.py::append_tracer_finding`: wrap the `write_artifact(...)` call in `with mission_write_lock(<mission dir>, repo_root=repo_root):`. The `_stage` thunk keeps its position after the routability probe (do NOT resolve `write_dir` before the probe).
- The lock key must be the canonical Mission directory name derived WITHOUT materializing anything: compose it the same way `coordination/transaction._mission_specs_dir_name(slug, mid8)` / `legacy_resolution.coord_mission_dir_name` does from the resolved Mission identity (resolve the handle → slug + mid8 via the existing read-only resolver the CLI already uses in `cli/commands/agent/tracer_append.py`). Pass a `feature_dir`-shaped path whose `.name` is that dir name (e.g. `repo_root / "kitty-specs" / dir_name`) — `mission_write_lock` only uses `.name` and the lock root. Test with a slug without mid8.
- The commit router's `coord_status_lock` (now delegating to `mission_write_lock`) must re-enter the same file — assert in a test that no second lock path is held.

### T020 – Re-key the slug-keyed callers

- `tasks_move_task_executor.py:581`: `feature_status_lock(status_lock_root, st.mission_slug)` → key `st.feature_dir.name` (or `mission_write_lock(st.feature_dir, repo_root=status_lock_root)`). One-line change; PR #5876 edits this file elsewhere — keep the hunk to that line.
- `tasks_mark_status.py:317`: same; the owned path takes the lock on the owned root instead of `nullcontext()` (check `st.owned.owned_root`).
- `status/lifecycle_events.py:302`: key on the Mission directory name it writes into.
- Verify each against `status.emit`'s key in the T017 lock-key test.

## Test Strategy

```bash
.venv/bin/python -m pytest tests/specify_cli/cli/commands/agent/test_concurrent_appenders.py tests/status/test_status_lock_keys.py -q
.venv/bin/python -m pytest tests/specify_cli/retrospective tests/status -q -n auto --dist loadfile
.venv/bin/python -m pytest tests/specify_cli/cli/commands/agent -q -n auto --dist loadfile -k "history or tracer or move_task or mark_status"
make test-fast
```
Concurrency tests 20× → 20/20.

## Definition of Done

- #5820 and #5467 reproductions RED before (recorded), GREEN after; both entries kept; 20/20.
- Lock-key test proves one lock file across the five writers.

## Risks & Mitigations

- tracer-append on coord materializes the coordination surface inside `_stage`; taking the Mission lock outside first is fine (re-entrant) but `coord_seed` also takes it — same key required.

## Activity Log
