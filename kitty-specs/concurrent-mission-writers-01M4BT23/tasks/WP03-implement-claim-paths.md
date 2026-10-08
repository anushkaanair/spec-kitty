---
work_package_id: WP03
title: spec-kitty implement and orchestrator-api claim paths
dependencies:
- WP01
requirement_refs:
- FR-005
- FR-008
planning_base_branch: issue-5819-concurrent-mission-writers
merge_target_branch: issue-5819-concurrent-mission-writers
branch_strategy: Planning artifacts for this mission were generated on issue-5819-concurrent-mission-writers. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5819-concurrent-mission-writers unless the human explicitly redirects the landing branch.
subtasks:
- T013
- T014
- T015
- T016
phase: Phase 2
history:
- at: '2026-10-07T19:00:00Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: python-pedro
authoritative_surface: src/specify_cli/cli/commands/
create_intent:
- tests/specify_cli/cli/commands/test_implement_claim_concurrency.py
execution_mode: code_change
model: claude-sonnet
owned_files:
- src/specify_cli/cli/commands/implement.py
- src/specify_cli/cli/commands/implement_phases.py
- src/specify_cli/cli/commands/implement_claim.py
- src/specify_cli/lanes/implement_support.py
- src/specify_cli/orchestrator_api/wp_lifecycle.py
- tests/specify_cli/cli/commands/test_implement_claim_concurrency.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---

# Work Package Prompt: WP03 – spec-kitty implement and orchestrator-api claim paths

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

Fix #5468 and the `implement` / `orchestrator-api` arms of #5796 (amendments A6, A7). After this WP:

- `spec-kitty implement` holds ONE `mission_write_lock` from `record_claim` (the claim emit) through `commit_claim` (the claim commit), and the `meta.json` vcs write (`ensure_vcs_locked` → `set_vcs_lock`) runs under it too. The claim row is never uncommitted while the lock is free, and the claim commit can never sweep another writer's rows.
- For single_branch repository-root lanes, `implement` and `orchestrator-api start-implementation` hold `write_checkout_claim_lock` from the occupancy scan to the claim emit (lock order: checkout lock outermost).

## Subtasks & Detailed Guidance

### T013 – Red-first reproductions

- New `tests/specify_cli/cli/commands/test_implement_claim_concurrency.py`.
- #5468: lanes Mission, `implement WP02` (A) and `move-task WP03 --to in_progress` (B) on one checkout. Hook A at the start of its claim commit (`implement_claim._commit_wp_claim_status` → `safe_commit`) and B right after its emit but before its commit. Assert afterwards: B exits 0, A exits 0, HEAD log == disk log, and B's rows are in a commit whose message is B's (not "WPxx claimed for implementation"). Drive the interleaving so the same test is RED before (A sweeps B's rows / B fails "nothing to commit") and GREEN after (A waits for B or B waits for A).
- #5796: single_branch Mission(s); `implement A WP01` paused right after its occupancy scan (hook `implement_support.refuse_repo_root_checkout_if_unavailable` return), then `implement A WP03` (same Mission) and, as a second case, `implement B WP01` (another single_branch Mission sharing the checkout) run: assert the second claim is refused `WRITE_CHECKOUT_OCCUPIED` and exactly one WP is `in_progress`. Post-fix, the second claim blocks on the checkout lock — run it in a thread, release the first, join with timeout.
- orchestrator-api arm: same race with one claim via `orchestrator-api start-implementation` (`src/specify_cli/orchestrator_api/wp_lifecycle.py`, scan ~:273, emit ~:545).
- Record RED in the tracer.

### T014 – One Mission lock hold from claim emit to claim commit

- Driver: `src/specify_cli/cli/commands/implement.py:384-430` (`allocate` :416, `record_claim` :422, `commit_claim` :430 after the try). Hold `mission_write_lock(feature_dir, repo_root=repo_root)` across `record_claim` and `commit_claim` (use an `ExitStack` to avoid a large re-indent; keep the existing exception shape — `test_implement_placement_routing.py::test_structured_error_is_not_swallowed_as_soft_warning` asserts on `implement()`'s source, run it).
- Key: the Mission's status write surface dir name (for coord topology the claim commit only bundles primary paths; the emit commits to coord via the transaction — make sure the lock you take is the one the emit re-enters: `start_implementation_status` uses `resolve_status_lock_root(feature_dir, repo_root)` + `feature_dir.name` at `work_package_lifecycle.py:203`; use the identical `feature_dir`).
- Timeout: `-1` (unbounded, same as `start_implementation_status`'s own take) for the initiating command.
- `implement_support.ensure_vcs_locked` (~:1016) / `implement_phases._ensure_vcs_in_meta` (:134): run under the same lock (it is called in `allocate` before `record_claim`; either widen the hold to start before it, or take `mission_write_lock` around the `set_vcs_lock` read-modify-write inside `ensure_vcs_locked` — re-entrant either way). Prefer the latter: local, and covers other callers.

### T015 – Checkout claim lock in `implement`

- When the resolved workspace is a single_branch repo-root lane (`implement_support.is_repo_root_lane` + topology check already used by `_ensure_repo_root_checkout_available`), enter `write_checkout_claim_lock(repo_root)` BEFORE `allocate` (the scan at `implement_phases.py:403`) and hold it through `record_claim` (and the commit — simplest: same ExitStack as T014, entered first). Non-single_branch: no-op.
- Update the docstring at `implement_support.py:170-176` ("the claim that would change the answer only lands after allocation") to say the checkout claim lock makes `occupancy_verified=True` sound.

### T016 – orchestrator-api `start-implementation`

- In `src/specify_cli/orchestrator_api/wp_lifecycle.py`, take `write_checkout_claim_lock` around `_ensure_repo_root_checkout_or_fail` (~:273) → the claim emit (~:545) for single_branch repo-root lanes. Keep its JSON envelope/error codes unchanged.
- Test via the orchestrator-api test helpers (`tests/specify_cli/orchestrator_api`, `tests/orchestrator_api`).

## Test Strategy

```bash
.venv/bin/python -m pytest tests/specify_cli/cli/commands/test_implement_claim_concurrency.py -q
.venv/bin/python -m pytest tests/specify_cli/cli/commands -q -n auto --dist loadfile -k "implement"
.venv/bin/python -m pytest tests/specify_cli/orchestrator_api tests/orchestrator_api tests/lanes tests/specify_cli/lanes -q -n auto --dist loadfile
make test-fast
```
Concurrency tests 20× → record 20/20.

## Definition of Done

- Reproductions RED before (recorded), GREEN after; 20/20.
- `implement` and orchestrator-api behaviour otherwise unchanged (existing tests green).

## Risks & Mitigations

- Holding the checkout lock across `create_lane_workspace` for repo-root lanes is cheap (no worktree is created); it must never be taken for lanes/coord missions.
- Lock order: never take the checkout lock while holding a Mission lock (WP01's guard raises).

## Activity Log
