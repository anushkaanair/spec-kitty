# Work Packages: Concurrent writers to a Mission's files never lose or steal a write

**Inputs**: Design documents from `/kitty-specs/concurrent-mission-writers-01M4BT23/`
**Prerequisites**: plan.md (incl. "Amendments after the post-plan squad", binding), spec.md, research.md, data-model.md

**Tests**: Required. Every bug fix is red-first: a deterministic interleaving reproduction is committed and shown RED on the pre-fix code before the fix (ADR 2026-07-17-1); afterwards it stays as a focused unit/regression test.

**Topology**: single_branch — WPs run sequentially in the repository root checkout.

## Subtask Format: `[Txxx] [P?] Description`

Subtasks are reference rows; record completion with `spec-kitty agent tasks mark-status <Txxx> --status done`.

---

## Work Package WP01: Mission write primitive and verified rollback (Priority: P1)

**Goal**: One canonical primitive for Mission-file mutation on the existing per-mission lock; a lock-held, fd-based, tail- and HEAD-verified rollback; the BookkeepingTransaction and coord-fallback truncates move onto it; the checkout claim lock primitive exists.
**Independent Test**: `tests/status/test_mission_write.py` — rollback cuts only own uncommitted rows, refuses on foreign/committed/shrunk/vanished/torn tails, never pads; capture refuses outside the lock.
**Prompt**: `/tasks/WP01-mission-write-primitive.md`
**Requirement Refs**: FR-001, FR-002, FR-003

### Included Subtasks

T001 Red-first: unit tests pinning the blind-truncate defects (foreign committed row cut, NUL padding on shrunk log) against the current coord-fallback restore and BookkeepingTransaction rollback (WP01)
T002 `kernel.git` committed-blob helper lifted from `status_surface_guard._committed_log`; guard uses it (WP01)
T003 `specify_cli/status/mission_write.py`: `mission_write_lock`, `locked_rewrite_text`, `RollbackPoint`, `capture_rollback_point`, `rollback_events_log`, `rollback_status_artifacts`, `RollbackOutcome`, `STATUS_ROLLBACK_REFUSED` (WP01)
T004 `status/locking.py`: `write_checkout_claim_lock` with lock-order guard (WP01)
T005 Migrate `BookkeepingTransaction._rollback` and `status_transition._restore_coord_status_artifacts` onto the primitive; `coord_status_lock` delegates to `mission_write_lock` (WP01)
T006 Facade exports in `status/__init__.py`; `test_status_events_writes_gate.py` allowlist/census edits (WP01)

### Dependencies

- None.

### Risks & Mitigations

- `capture_rollback_point` holder check must compute the same lock path the holder used (owned, coord, legacy) — test all arms.

---

## Work Package WP02: agent action implement / review — one lock hold, honest reporting, shared-workspace warning (Priority: P1)

**Goal**: `agent action implement` captures, emits, commits and rolls back inside one Mission lock hold keyed on the status write surface; a committed-but-failed claim is reported honestly; single_branch claims hold the checkout claim lock from the occupancy guard to the claim emit; implement and review warn about another actor in the same workspace.
**Independent Test**: `tests/status/test_concurrent_mission_writers.py` (#5819 transition + annotation modes, #5804 coord), `tests/lanes/test_shared_workspace_warning.py`.
**Prompt**: `/tasks/WP02-agent-action-claim-window.md`
**Requirement Refs**: FR-003, FR-004, FR-008, FR-009

### Included Subtasks

T007 Red-first: deterministic #5819 reproduction (both modes) and #5804 coord reproduction (WP02)
T008 `_restore_status_artifacts` body replaced in place by the primitive; refusal reporting (WP02)
T009 `implement_claim_transition` thin locked wrapper over `_implement_claim_transition_body`; capture via `capture_rollback_point`; keyed on `wf_feature_dir` (WP02)
T010 Committed-but-failed reporting in `_handle_commit_failure` / lane-sync arm (A4) (WP02)
T011 Checkout claim lock via `ExitStack` from `_guard_repo_root_claim` through the claim (WP02)
T012 `shared_workspace_writers` in `lanes/checkout_occupancy.py`; warnings in implement and review (human + JSON) (WP02)

### Dependencies

- Depends on WP01.

### Risks & Mitigations

- PR #5876 edits `workflow.py` / `workflow_executor.py`: keep hunks out of its regions (thin wrapper, ExitStack, in-place body replacement).

---

## Work Package WP03: spec-kitty implement and orchestrator-api claim paths (Priority: P1)

**Goal**: `implement` holds one Mission lock from `record_claim` through `commit_claim` (and the `meta.json` vcs write); single_branch claims in `implement` and `orchestrator-api start-implementation` hold the checkout claim lock from scan to claim emit.
**Independent Test**: `tests/specify_cli/cli/commands/test_implement_claim_concurrency.py` (#5468 steal, #5796 same- and cross-Mission races, orchestrator-api arm).
**Prompt**: `/tasks/WP03-implement-claim-paths.md`
**Requirement Refs**: FR-005, FR-008

### Included Subtasks

T013 Red-first: #5468 claim-commit steal and #5796 overlapping-claims reproductions (WP03)
T014 One Mission lock hold `record_claim` → `commit_claim`; `ensure_vcs_locked` under it (WP03)
T015 Checkout claim lock around `allocate` → `record_claim` for single_branch repo-root lanes (WP03)
T016 orchestrator-api `start-implementation` takes the checkout claim lock (WP03)

### Dependencies

- Depends on WP01.

---

## Work Package WP04: Locked appenders and lock keys (Priority: P1)

**Goal**: add-history and tracer-append are locked read-modify-writes; the three slug-keyed status-lock callers key on the Mission directory name.
**Independent Test**: `tests/specify_cli/cli/commands/agent/test_concurrent_appenders.py` (#5820, #5467), `tests/status/test_status_lock_keys.py`.
**Prompt**: `/tasks/WP04-locked-appenders.md`
**Requirement Refs**: FR-006, FR-007

### Included Subtasks

T017 Red-first: #5820 and #5467 overlap reproductions (WP04)
T018 add-history through `locked_rewrite_text` (WP04)
T019 tracer-append under `mission_write_lock` around `write_artifact` (WP04)
T020 Re-key `tasks_move_task_executor`, `tasks_mark_status` (incl. owned nullcontext), `status/lifecycle_events` to the directory name (WP04)

### Dependencies

- Depends on WP01.

---

## Work Package WP05: Architectural gate and one-writer doctrine (Priority: P2)

**Goal**: An empty-allowlist gate keeps raw truncates/unlinks of Mission status files, unlocked read-modify-write pairs and slug-keyed status locks out; the shipped implement/review prompts state the one-writer-per-checkout rule.
**Independent Test**: `tests/architectural/test_mission_write_discipline.py` incl. non-vacuity and self-mutation tests.
**Prompt**: `/tasks/WP05-gate-and-doctrine.md`
**Requirement Refs**: FR-010, FR-011

### Included Subtasks

T021 Gate rule 1 (truncate/unlink forms) with floor and synthetic positives (WP05)
T022 Gate rule 2 (read/sink pairs in one locked region) with self-mutation test (WP05)
T023 Gate rule 3 (no slug-keyed `feature_status_lock`) (WP05)
T024 One-writer sentence in the software-dev implement and review mission-step prompts (WP05)

### Dependencies

- Depends on WP02, WP03, WP04.

---

## Work Package WP06: CHANGELOG and docs (Priority: P3)

**Goal**: `[Unreleased]` CHANGELOG entry and the status-model doc describe the Mission write lock and the verified rollback.
**Independent Test**: docs freshness check and terminology guard pass.
**Prompt**: `/tasks/WP06-changelog-and-docs.md`
**Requirement Refs**: FR-001

### Included Subtasks

T025 `docs/changelog/CHANGELOG.md` `[Unreleased]` entries (WP06)
T026 `docs/architecture/status-model.md` section on the Mission write lock and rollback (WP06)

### Dependencies

- Depends on WP05.
