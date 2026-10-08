# Implementation Plan: Concurrent writers to a Mission's files never lose or steal a write

**Branch**: `issue-5819-concurrent-mission-writers` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)
**Input**: Mission specification from `kitty-specs/concurrent-mission-writers-01M4BT23/spec.md`

## Summary

Every in-scope defect is the same shape: a Mission file is mutated outside the per-mission status lock, or a failed status commit is undone by a blind byte truncate to a size captured outside the lock hold. The fix reuses the lock that already exists (`feature_status_lock`, keyed on the Mission directory name under the git common dir) as the **Mission write lock**, wraps it in one canonical primitive module, routes every in-scope writer through it, and adds an architectural gate. The single_branch claim race needs a second, checkout-wide lock because two Missions share one checkout; it is modelled on the existing verdict-save queue lock.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: typer, rich; `kernel.locks.machine_file_lock` (the only raw lock door, `tests/architectural/test_lock_primitive_ban.py`); `kernel.atomic.atomic_write`
**Storage**: files in git (`status.events.jsonl`, `status.json`, `tasks/WP*.md`, `traces/*.md`)
**Testing**: pytest; deterministic in-process interleavings (threads + `threading.Event` hooks injected at seams, real git repos via existing fixtures); red-first per ADR 2026-07-17-1
**Target Platform**: Linux, macOS, Windows (lock primitive is cross-OS already)
**Project Type**: single project (`src/`, `tests/`)
**Performance Goals**: no added work on the uncontended path beyond one re-entrant lock acquire; rollback path adds one `git show`
**Constraints**: C-001..C-004 in spec; complexity ≤ 15; no new suppressions
**Scale/Scope**: ~8 production modules, 1 new module, 1 new gate, ~6 new test files

## Charter Check

- Single canonical authority: one Mission write primitive; the three truncates collapse into one verified rollback. PASS.
- Architectural alignment: the primitive lives in `specify_cli.status` next to `locking.py` (status owns the lock); callers in `cli`, `coordination`, `retrospective`, `lanes` import downward. PASS.
- ATDD / red-first: each issue gets a deterministic reproduction committed RED before its fix (recorded in the tracer). PASS.
- Gate discipline: the new gate starts with an empty allowlist and a self-mutation test. PASS.
- Locality: files in PR #5876 (`workflow.py`, `workflow_executor.py`, `status/store.py`, `status/emit.py`) receive only the minimal lock/rollback call-site changes. PASS with note.

## Design decisions

### D1 — The Mission write lock is `feature_status_lock`

`specify_cli/status/mission_write.py` (new) exposes:

- `mission_write_lock(feature_dir, *, repo_root=None, timeout=-1)` — `feature_status_lock(resolve_status_lock_root(feature_dir, repo_root), feature_dir.name, timeout=timeout)`. The single way a non-status writer takes the lock. Re-entrant per thread.
- `locked_rewrite_text(path, transform, *, feature_dir, repo_root=None, timeout=...)` — under the lock: read the current text (`None` when missing), `new = transform(current)`, `atomic_write(path, new)` when it changed. Returns the written text. The transform is the read-modify-write; it never sees a stale read.
- `RollbackPoint` + `capture_rollback_point(feature_dir)` — pre-emit event-log size and `status.json` bytes. **Refuses (RuntimeError) unless the Mission write lock for `feature_dir` is held by the calling thread**, so a capture outside the hold cannot be written.
- `rollback_status_artifacts(point, *, expected_event_ids=None) -> RollbackOutcome` — takes the lock (re-entrant), then: log vanished → refuse; size < pre size → refuse (no NUL padding); tail not whole JSON rows → refuse; `expected_event_ids` given and tail ids ≠ expected (multiset) → refuse; any tail event id present in the log committed at `HEAD` of the checkout holding the file → refuse; else truncate to the pre size and restore `status.json` bytes. Refusal leaves both files untouched and is logged at WARNING; the outcome names the reason so callers print it.
- `rollback_events_log(point, ...)` — log half only, for `BookkeepingTransaction`, which restores its own snapshot.

The HEAD check (one `git show HEAD:./status.events.jsonl` from the file's directory; any git failure = "no committed rows known") is defence in depth for writers that commit status files outside the lock: a row that is already committed is never cut, so HEAD and disk can never be made to disagree by a rollback.

Starting point: the design of closed-unmerged PR #4072 (`status/rollback.py`, `owned_emission_window`), re-implemented on current main (the branch is 12k commits off the rewritten main and not portable).

### D2 — One lock hold from capture to rollback

`agent action implement` (`workflow_executor.implement_claim_transition`, claim and resume arms) wraps capture → emit → commit → rollback in `mission_write_lock`, exactly as `review_claim_transition` already does (`workflow_executor.py:1729`). `BookkeepingTransaction` and the emit helpers re-enter the same lock file (scout-verified: coord dir name and transaction key both resolve to `<slug>-<mid8>` under the same git common dir).

`spec-kitty implement`'s `_commit_wp_claim_status` (`implement_claim.py`) collects its paths and runs `safe_commit` inside `mission_write_lock`, so it cannot sweep another writer's appended-but-uncommitted rows (#5468).

### D3 — Locked read-modify-write for add-history and tracer-append

- `agent tasks add-history`: re-locate the WP and append inside `locked_rewrite_text` (or `mission_write_lock` around locate → append → write), so the transform runs on a fresh read.
- `agent tracer-append`: hold `mission_write_lock` around the whole `write_artifact(...)` call (stage thunk read → merge → write → commit). The lock key is the Mission directory name; the commit router's `coord_status_lock` re-enters the same file.

### D4 — Checkout claim lock for single_branch

`status/locking.py` gains `write_checkout_claim_lock(write_checkout, *, timeout=120.0)`: a `_named_status_lock` keyed `__checkout-<sha1(resolved path)[:16]>__` under the git common dir. Lock order is fixed: **checkout claim lock, then Mission write lock**, never the reverse. Taken only when the WP resolves to a single_branch repository-root lane:

- `implement` (`implement.py` driver): held from `implement_phases.allocate` (the occupancy scan) through `record_claim` (the `in_progress` emit). The `occupancy_verified=True` skip stays valid because nothing can claim the checkout while the lock is held.
- `agent action implement` (`workflow.py`): held from `_guard_repo_root_claim` through `implement_claim_transition`'s claim emit.

### D5 — Advisory shared-workspace warning (#5099 half)

`lanes/checkout_occupancy.py` gains `shared_workspace_writers(repo_root, mission_slug, wp_id, workspace, actor)` returning WPs `in_progress`/`in_review` held by another actor in the same resolved workspace (single_branch repo root across Missions via the existing scan; lane worktree within the Mission for lanes). `agent action implement` and `agent action review` print one warning per occupant and include `shared_workspace_warnings` in JSON output. No refusal (C-004).

FR-010: see amendment A11 (implement/review mission-step prompts).

### D6 — Gate

`tests/architectural/test_mission_write_discipline.py`:

1. No `.truncate(` / `os.truncate` / `os.ftruncate` call in `src/specify_cli/**` outside `status/mission_write.py` (empty allowlist).
2. Every call to a registered Mission-file read-modify-write sink (`append_activity_log`, the tracer merge `_append_entry`) is lexically inside a `with mission_write_lock(...)`/`feature_status_lock(...)` block or inside a function passed to `locked_rewrite_text` (empty allowlist).
3. Non-vacuity: synthetic offending sources are fed to the same scanner and must be flagged; floor counts for the scanned sinks.

`tests/architectural/test_status_events_writes_gate.py` allowlists are updated for the moved truncates.

## Amendments after the post-plan squad (binding; they override D1–D6 where they differ)

Two read-only adversarial lenses (concurrency; boundary/gate) reviewed this plan on 2026-10-07. Every finding is folded below.

- **A1 (D1, timeout).** `mission_write_lock` defaults to `BOUNDED_STATUS_LOCK_TIMEOUT_SECONDS`, like `coord_status_lock`, `issue_verdict` and the acceptance matrix writer. The `agent action implement` window passes `timeout=-1`, the same as the existing review window (`workflow_executor.py:1729`). `coord_status_lock` delegates to `mission_write_lock` instead of being a second wrapper.
- **A2 (D1, truncate mechanics).** The rollback opens the log `r+b` once, `fstat`s that fd, verifies, and `ftruncate`s the same fd only when the fd size is at least the pre size. It never extends the file, so there is no time-of-check gap for a git reset to fall into. The tail parser skips a leading blank line, which `append_raw_rows_atomic` inserts when the pre-emit log lacked a trailing newline. The "log did not exist before → unlink" arm of `BookkeepingTransaction._rollback` moves into the primitive with the same verification.
- **A3 (D1, HEAD probe).** The committed log is read through `kernel.git` (`tree_entry` + `cat-file`), not a hand-written `git show`. The helper is lifted from `coordination/status_surface_guard._committed_log` into a shared `kernel.git` helper that both callers use. It **fails closed**: a git error refuses the rollback. `expected_event_ids` is passed wherever the caller has them (`BookkeepingTransaction._event_ids`). Every refusal prints error code `STATUS_ROLLBACK_REFUSED`, the reason, and a remedy naming `git diff HEAD -- <log>`.
- **A4 (H1, committed-but-failed).** When the rollback is refused because the tail is already committed at HEAD (always the case on a coord Mission, whose transactional emit commits the claim itself), the command prints that the claim **was committed** and only the follow-up commit or lane sync failed. It records the receipt as committed, not refused, and never prints "Event log rolled back". Exit status is non-zero only because the follow-up failed (spec US3 scenario 2).
- **A15 (review window, analysis I3).** The review window (`workflow_executor.py:1729`) is re-keyed on the status write surface (the same `wf_feature_dir` resolution as A5) and captures with `capture_rollback_point` there, so on a coord Mission it measures the coord log the emit writes; a coord review test pins it.
- **A5 (D2, key and shape).** The window is keyed on `wf_feature_dir` (the status write surface), never the primary `feature_dir`. To stay clear of #5876's hunks, `implement_claim_transition` becomes a thin wrapper that takes the lock and delegates to the unchanged body, `_implement_claim_transition_body`. The only change in the body is replacing the two capture lines with `capture_rollback_point`. The lane read moves inside the hold as a result. `_restore_status_artifacts` is replaced in place.
- **A6 (H3, implement).** `spec-kitty implement` holds one `mission_write_lock` from `record_claim` through `commit_claim`, so the claim row is never uncommitted while the lock is free. For single_branch this lock nests inside the checkout claim lock. `ensure_vcs_locked` (`set_vcs_lock`, an unlocked read-modify-write of `meta.json` that the claim commit stages) moves under the same Mission lock.
- **A7 (H2, third claim path).** `orchestrator-api start-implementation` (`orchestrator_api/wp_lifecycle.py:273` scan → `:545` emit) takes the checkout claim lock as well.
- **A8 (M2, lock keys in scope).** The three writers that key the lock on the Mission slug (`tasks_move_task_executor.py:581`, `tasks_mark_status.py:317`, `status/lifecycle_events.py:302`) are re-keyed to the Mission directory name, each a one-line change. `tasks_mark_status`'s owned-checkout `nullcontext()` takes the lock on the owned root. The gate gains a rule that no `feature_status_lock(` call passes a slug-named key.
- **A9 (D4).** The checkout claim lock key is `normcase` of the resolved checkout root, so it is stable on case-insensitive filesystems. Taking it while any Mission lock is held raises `RuntimeError` (lock-order guard, tested). In `agent action implement` it is entered through `contextlib.ExitStack` at the guard, which avoids re-indenting #5876's hunks.
- **A10 (D3).** add-history uses `locked_rewrite_text` only, so the WP read happens inside the primitive. tracer-append holds `mission_write_lock` around `write_artifact(...)`. The key is the canonical Mission directory name, derived without materializing anything (same composition as `_mission_specs_dir_name`), with a test for a slug without mid8.
- **A11 (D5 / FR-010).** The one-writer sentence goes into the shipped implement and review mission-step prompts (`packs/built-in/missions/mission-steps/software-dev/{implement,review}/prompt.md`), extending the existing single_branch "one WP in progress" line. It does not go into the PR-isolation tactic. The prompts carry no manifest hash.
- **A12 (D6, gate shape).**
  - **Rule 1.** Bans `truncate`/`ftruncate` in any form (attribute, `os`/`posix` aliases, `from os import`, `getattr(..., "truncate")`, `methodcaller`). It also bans unlinking a path named after the event log outside `status/mission_write.py`. The floor is exactly one site, inside the primitive. rich `Text.truncate` is an accepted, documented over-fire (none in scope today). `src/runtime` and `src/kernel` are out of scan scope, and the gate docstring says so.
  - **Rule 2.** Registers (read, sink) pairs: add-history (`locate_work_package`, `append_activity_log`) and tracer (`_read_current_coord_content`, `_append_entry`). Both calls of a pair must sit in one locked region. A region is the body of a lock `with` without crossing a nested def or lambda, or a callable passed as `transform` to `locked_rewrite_text`, or a callable passed as an argument to a call inside a lock `with`. Non-call references fail. Aliases resolve.
  - **Rule 3.** No slug-keyed `feature_status_lock`.
  - **Non-vacuity.** Synthetic sources, plus a self-mutation test that strips the `with` from the real module's AST.
  - **Required edits to `test_status_events_writes_gate.py`, landing in the same commit.** Remove the transaction and status_transition entries from `ALLOWED_OUT_OF_STORE_WRITE_SITES`. Remove the workflow entry from `EXPECTED_UNRESOLVED_EVENT_NAMED_WRITE_SITES`. Add the primitive's site there. Add `specify_cli.status.mission_write` to `EXPECTED_LOCK_COMPOSITION_SITES`, and count `mission_write_lock(` in `has_lock_call_site`, adding the new callers to the census.
- **A13 (facade).** The primitive's symbols are exported from `specify_cli/status/__init__.py` in their own import block and `__all__` region, so they don't land on lines adjacent to #5876's additions. Callers import from the facade (SR-2, `test_status_module_boundary.py`).
- **A14 (SC-004).** SC-004 is measured by the AST gate, not `rg`, because a docstring in `orchestrator_api/design_status.py` matches the text.
- **Accepted risk (M5).** The `agent action implement` window spans the lane auto-rebase, as review's already does. Other writers that wait on the lock for a bounded time can see `STATUS_LOCK_HELD` more often while an implement claim is in flight. This is loud and retryable, never silent. The plan accepts it, and the tracer records it.
- **Follow-ups (unchanged plus):** converge `acceptance/matrix.locked_reread_splice_and_write` and `issue_verdict._locked_reread_splice_and_write` onto `mission_write_lock` and `locked_rewrite_text`; the unlocked `mission_metadata` setters beyond `set_vcs_lock`; `run.events.jsonl`.

## Project Structure

```
src/specify_cli/status/mission_write.py              # NEW primitive (D1)
src/specify_cli/status/locking.py                    # + write_checkout_claim_lock (D4)
src/specify_cli/cli/commands/agent/workflow.py       # _restore_status_artifacts -> primitive (minimal)
src/specify_cli/cli/commands/agent/workflow_executor.py  # implement lock window (minimal)
src/specify_cli/coordination/status_transition.py    # coord fallback restore -> primitive
src/specify_cli/coordination/transaction.py          # _rollback -> rollback_events_log
src/specify_cli/cli/commands/implement_claim.py      # claim commit under lock
src/specify_cli/cli/commands/implement.py            # checkout claim lock around allocate..record_claim
src/specify_cli/cli/commands/agent/tasks.py          # add-history locked
src/specify_cli/retrospective/tracer_writer.py       # tracer-append locked
src/specify_cli/lanes/checkout_occupancy.py          # shared_workspace_writers
src/specify_cli/lanes/implement_support.py           # vcs write under lock, docstring
src/specify_cli/cli/commands/implement_phases.py     # claim hold
src/specify_cli/orchestrator_api/wp_lifecycle.py     # checkout claim lock (A7)
src/specify_cli/cli/commands/agent/tasks_move_task_executor.py, tasks_mark_status.py, status/lifecycle_events.py  # re-key (A8)
src/kernel/git/listing.py, src/specify_cli/coordination/status_surface_guard.py  # committed-blob helper (A3)
src/specify_cli/status/__init__.py                   # facade (A13)
packs/built-in/missions/mission-steps/software-dev/{implement,review}/prompt.md  # one-writer sentence
tests/status/test_mission_write.py                   # primitive unit tests
tests/status/test_concurrent_mission_writers.py      # red-first interleavings (#5819 #5804 #5468)
tests/specify_cli/cli/commands/agent/test_concurrent_appenders.py  # #5467 #5820
tests/status/test_status_lock_keys.py                # lock-key convergence (A8)
tests/specify_cli/cli/commands/test_implement_claim_concurrency.py  # #5468 #5796
tests/lanes/test_shared_workspace_warning.py         # #5099 warning
tests/status/test_checkout_claim_lock.py             # checkout claim lock
tests/architectural/test_mission_write_discipline.py # gate
```

## Implementation Concern Map

### IC-01 — Mission write primitive and verified rollback
- **Purpose**: one lock, one locked RMW, one verified rollback.
- **Relevant requirements**: FR-001, FR-002, FR-003, FR-011
- **Affected surfaces**: `status/mission_write.py`, `workflow.py::_restore_status_artifacts`, `status_transition.py::_restore_coord_status_artifacts`, `transaction.py::_rollback`, gate
- **Sequencing/depends-on**: none
- **Risks**: `BookkeepingTransaction._rollback` restores `status.json` from its own lazy snapshot; keep that, swap only the log half. Rollback refusals must surface in output, not only logs.

### IC-02 — Lock windows for claim commits
- **Purpose**: capture → emit → commit → rollback in one hold; claim commit under the lock.
- **Relevant requirements**: FR-004, FR-005
- **Affected surfaces**: `workflow_executor.implement_claim_transition`, `implement_claim._commit_wp_claim_status`
- **Sequencing/depends-on**: IC-01
- **Risks**: deadlock if any path takes the Mission lock before the checkout lock; the existing `start_implementation_status` lock must re-enter (same key).

### IC-03 — Locked appenders
- **Purpose**: add-history and tracer-append read under the lock.
- **Relevant requirements**: FR-006, FR-007, FR-011
- **Affected surfaces**: `agent/tasks.py` add-history, `retrospective/tracer_writer.py`
- **Sequencing/depends-on**: IC-01
- **Risks**: tracer write must keep the probe-before-materialize ordering of `write_artifact`.

### IC-04 — Single_branch claim atomicity and shared-workspace warning
- **Purpose**: atomic occupancy check; advisory warning; doctrine sentence.
- **Relevant requirements**: FR-008, FR-009, FR-010
- **Affected surfaces**: `status/locking.py`, `implement.py`, `workflow.py` implement path, `lanes/checkout_occupancy.py`, review claim path, built-in tactic
- **Sequencing/depends-on**: IC-02 (lock order)
- **Risks**: holding a checkout lock across a lane/workspace allocation; keep it no-op for non-single_branch.

## Complexity Tracking

None.

## Follow-ups (not in scope)

- Other unlocked Mission-file writers found by the scout (`mission_metadata` setters, `tasks_map_requirements`, finalize frontmatter flush, `scaffold_issue_matrix`) — file as `status:triage`; the gate's sink registry can grow to cover them.
- `run.events.jsonl` blind truncate in `runtime/next/runtime_bridge.py` (not a Mission file) — file as `status:triage`.
