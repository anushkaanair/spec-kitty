---
work_package_id: WP02
title: agent action implement / review — one lock hold, honest reporting, shared-workspace warning
dependencies:
- WP01
requirement_refs:
- FR-003
- FR-004
- FR-008
- FR-009
planning_base_branch: issue-5819-concurrent-mission-writers
merge_target_branch: issue-5819-concurrent-mission-writers
branch_strategy: Planning artifacts for this mission were generated on issue-5819-concurrent-mission-writers. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5819-concurrent-mission-writers unless the human explicitly redirects the landing branch.
subtasks:
- T007
- T008
- T009
- T010
- T011
- T012
phase: Phase 2
history:
- at: '2026-10-07T19:00:00Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: python-pedro
authoritative_surface: src/specify_cli/cli/commands/agent/
create_intent:
- tests/status/test_concurrent_mission_writers.py
- tests/lanes/test_shared_workspace_warning.py
- tests/architectural/test_status_events_writes_gate.py
execution_mode: code_change
model: claude-sonnet
owned_files:
- src/specify_cli/cli/commands/agent/workflow.py
- src/specify_cli/cli/commands/agent/workflow_executor.py
- src/specify_cli/lanes/checkout_occupancy.py
- tests/status/test_concurrent_mission_writers.py
- tests/lanes/test_shared_workspace_warning.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---

# Work Package Prompt: WP02 – agent action implement / review — one lock hold, honest reporting, shared-workspace warning

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

Fix #5819 and #5804 on the `agent action implement` path, the single_branch race on that path (#5796, agent arm), and add the #5099 advisory warning. After this WP:

- `agent action implement` captures the rollback point, emits, commits and rolls back inside ONE `mission_write_lock` hold keyed on the status write surface (`wf_feature_dir`), mirroring `review_claim_transition` (`workflow_executor.py:1729`).
- No blind truncate remains in `workflow.py`.
- A claim already committed (coord transactional emit) is never reported as failed or "rolled back".
- single_branch repo-root claims on this path hold `write_checkout_claim_lock` from `_guard_repo_root_claim` through the claim emit.
- `agent action implement` and `agent action review` warn (human + JSON) when another actor holds a WP `in_progress`/`in_review` in the same resolved workspace.

## Subtasks & Detailed Guidance

### T007 – Red-first reproductions (#5819, #5804)

- New `tests/status/test_concurrent_mission_writers.py`. Read #5819's reproducer (issue body, shell) and translate it into an in-process deterministic test:
  - Fixture: a lanes Mission with WP01..WP03 finalized in a temp git repo (reuse helpers from `tests/status/conftest.py`, `tests/specify_cli/cli/commands/agent/` implement tests, or `tests.unit.migration._backfill_fixture.build_mission` — search for an existing "implement claim" integration fixture first: `grep -rl "implement_claim_transition\|agent action implement" tests | head`).
  - Arm A ("implement"): call the `implement_claim_transition` path (or the CLI via typer `CliRunner`) for WP01, with a monkeypatched hook that (1) signals once A has captured its pre-emit state and (2) forces A's status commit to fail (monkeypatch the commit leaf, e.g. `_commit_via_legacy_safe_commit`/`safe_commit`, to raise the same staging error as `.git/index.lock` contention).
  - Arm B ("move-task"): between A's capture and A's failing commit, run the real move-task WP03 → canceled with a note to completion (exit 0, committed).
  - Assert: B's committed transition and annotation rows are on disk after A's rollback and remain in HEAD after a subsequent status write (run one more move-task).
  - Transition mode and annotation mode (see issue) — two parametrized cases.
  - Today the capture happens BEFORE the lock, so the hook can be placed there; after the fix the capture is inside the lock and B blocks until A releases — the test must therefore drive B in a thread that waits on A's "captured" event and must not deadlock post-fix: assert B completes after A exits (join with timeout), and assert the final state. Design the hooks so the SAME test is RED before and GREEN after.
- #5804 coord case: coord topology Mission, two `agent action implement` claims (WP01, WP03) interleaved so that A's follow-up commit fails while B appends; assert the coord log parses line by line (no NUL / whitespace-only lines), contains both committed claim rows, and A's output does not say "rolled back" when its claim row is in coord HEAD.
- Record RED in the tracer before fixing.

### T008 – Replace `_restore_status_artifacts` in place (`workflow.py:283`)

- Keep the function name/signature callers use, but make it take/build a `RollbackPoint` and call `rollback_status_artifacts`; return the `RollbackOutcome`. Do not move the function (PR #5876 does not touch these lines; keep it that way).
- Update `tests/architectural/test_status_events_writes_gate.py`: remove `("specify_cli.cli.commands.agent.workflow","Path.open","events_path")` from `EXPECTED_UNRESOLVED_EVENT_NAMED_WRITE_SITES` (out-of-map one-line edit of WP01's file; note it in the Activity Log).

### T009 – One lock hold for the claim (`workflow_executor.py:949`)

- Rename the current body to `_implement_claim_transition_body(...)` UNCHANGED except: the two capture lines at ~:1003-1004 become `rollback_point = capture_rollback_point(wf_feature_dir, repo_root=main_repo_root)` and the rollback inputs are threaded as that point (through `_CommitFailureContext`, which can hold the point instead of the four fields).
- `implement_claim_transition(...)` becomes a thin wrapper: resolve `wf_feature_dir` exactly as the body does (extract a small helper if needed so both use one resolution), then `with mission_write_lock(wf_feature_dir, repo_root=main_repo_root, timeout=-1):` (same unbounded wait as review) and delegate. The lane read (~:986-994) is inside the body, hence inside the hold.
- `commit_workflow_change` takes the `RollbackPoint`. Review (amendment A15): re-key the review window (`workflow_executor.py:1729`) on the same status-write-surface directory (`wf_feature_dir`-equivalent) instead of the primary `feature_dir`, and capture there with `capture_rollback_point`, so on a coord Mission the rollback point measures the coord log; add a coord review test (failing follow-up commit → only the review's own uncommitted rows are cut / committed rows are reported as committed).
- Key MUST be `wf_feature_dir` (the coord status dir on coord topology), never the primary `feature_dir`; add a test with a Mission slug without an embedded mid8 proving the window's lock path equals the coord transaction's (`_mission_specs_dir_name`).

### T010 – Committed-but-failed reporting (amendment A4)

- In `_handle_commit_failure` and the `typer.Exit` / lane-sync arms of `commit_workflow_change`: when the outcome is refused with `TAIL_ALREADY_COMMITTED`, print `"<WP> claim was committed; the follow-up <operation> commit failed: <exc>"` (no "Event log rolled back"), record the receipt as `committed` (not `refused`), still exit 1 for the failed follow-up (spec US3 scenario 2: output truthful, non-zero only for the follow-up). The T007 #5804 assertion checks the output wording, not exit 0. For other refusals print `outcome.message()` (contains `STATUS_ROLLBACK_REFUSED` and the `git diff HEAD --` remedy). Only print "Event log rolled back to pre-emit state." when `outcome.rolled_back`.
- Test the lane-sync refusal arm (`workflow_executor.py:~300-320`) and the legacy arm.

### T011 – Checkout claim lock on the agent path

- In `workflow.py::implement` around `_guard_repo_root_claim(...)` (~:1642): use a `contextlib.ExitStack` already open for the command body (or open one right before the guard) and `stack.enter_context(write_checkout_claim_lock(main_repo_root))` ONLY when the WP resolves to a single_branch repository-root lane (reuse the predicate `guard_repo_root_claim` uses: `is_repo_root_lane(workspace)` + single_branch topology). It must stay held through `implement_claim_transition`'s claim emit and is released when the command finishes. Do not re-indent the existing body (ExitStack.enter_context + close at the end/`finally`).
- Lock order: checkout lock is taken before `mission_write_lock` (the guard raises otherwise — keep it that way).
- Test: two `agent action implement` claims for WP01/WP03 of one single_branch Mission, the first paused after its guard: second waits, then is refused `WRITE_CHECKOUT_OCCUPIED`; exactly one `in_progress`. Cross-Mission arm as well.

### T012 – Shared-workspace advisory warning (#5099)

- `lanes/checkout_occupancy.py`: add
  ```python
  @dataclass(frozen=True)
  class SharedWorkspaceWriter: mission_slug: str; wp_id: str; lane: str; actor: str | None
  def shared_workspace_writers(repo_root, mission_slug, wp_id, workspace, actor) -> list[SharedWorkspaceWriter]
  ```
  single_branch repo-root workspace: reuse the existing cross-Mission scan, generalised to lanes `{in_progress, in_review}` (refactor `in_progress_wps_in_write_checkout` to share a private helper; keep its public behaviour); lanes/coord: other WPs of the same Mission whose lane id (from `lanes.json`) equals this WP's lane and whose lane is in that set. Exclude this WP; include only entries whose actor differs from `actor` (unknown actor counts as different). Actor comes from the reduced snapshot (find the field: `grep -n "actor" src/specify_cli/status/models.py`).
- `agent action implement` (after workspace resolution, before the claim) and `review_claim_transition` (after the claim): print `Warning: <mission>/<WP> is <lane> by <actor> in this workspace; one writer per checkout (#5099).` per entry, and add `"shared_workspace_warnings": [...]` to the JSON payload where those commands emit JSON (find the JSON output path; if a command has no JSON mode, human output only and note it).
- Tests in `tests/lanes/test_shared_workspace_warning.py`: (1) review arm, single_branch: WP01 in_progress by A, review of WP02 by B → warning names WP01/A; (2) implement arm: `agent action implement` while another actor has a WP `in_review` in the same single_branch checkout → warning; (3) lanes arm: two WPs on the same lane worktree, other actor `in_progress` → warning; (4) JSON output carries `shared_workspace_warnings` with the entries; (5) absent cases: no concurrent writer, and same actor → no warning, empty list in JSON.

## Test Strategy

```bash
.venv/bin/python -m pytest tests/status/test_concurrent_mission_writers.py tests/lanes/test_shared_workspace_warning.py -q
.venv/bin/python -m pytest tests/specify_cli/cli/commands/agent -q -n auto --dist loadfile
.venv/bin/python -m pytest tests/lanes tests/specify_cli/lanes -q -n auto --dist loadfile
.venv/bin/python -m pytest tests/architectural/test_status_events_writes_gate.py tests/architectural/test_status_module_boundary.py -q
make test-fast
```
Run the concurrency tests 20× (`--count` is not installed; loop in bash) and record 20/20.

## Definition of Done

- #5819 (both modes) and #5804 reproductions RED before (recorded), GREEN after, 20/20.
- No "rolled back" message for a committed claim; refusal message carries `STATUS_ROLLBACK_REFUSED`.
- Warning tests pass both ways.

## Risks & Mitigations

- Deadlock: the window holds the Mission lock while `start_implementation_status` and `BookkeepingTransaction` re-enter — same file only if keyed on `wf_feature_dir`; a different key would self-deadlock against the bounded transaction take → `STATUS_LOCK_HELD`. The slug-without-mid8 test guards this.
- PR #5876 overlap: the wrapper/ExitStack shape is mandatory; do not reflow code it edits.

## Review Guidance

- Diff `workflow_executor.py` and `workflow.py` against main: hunks should be the wrapper, the capture lines, failure reporting, the ExitStack entry, the warning — nothing else.

## Activity Log
