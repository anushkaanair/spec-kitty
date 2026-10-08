---
work_package_id: WP01
title: Mission write primitive and verified rollback
dependencies: []
requirement_refs:
- FR-001
- FR-002
- FR-003
planning_base_branch: issue-5819-concurrent-mission-writers
merge_target_branch: issue-5819-concurrent-mission-writers
branch_strategy: Planning artifacts for this mission were generated on issue-5819-concurrent-mission-writers. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5819-concurrent-mission-writers unless the human explicitly redirects the landing branch.
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
phase: Phase 1
history:
- at: '2026-10-07T19:00:00Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: python-pedro
authoritative_surface: src/specify_cli/status/
create_intent:
- src/specify_cli/status/mission_write.py
- tests/status/test_mission_write.py
- tests/status/test_checkout_claim_lock.py
execution_mode: code_change
model: claude-sonnet
owned_files:
- src/specify_cli/status/mission_write.py
- src/specify_cli/status/locking.py
- src/specify_cli/status/__init__.py
- src/kernel/git/listing.py
- src/kernel/git/__init__.py
- src/specify_cli/coordination/status_surface_guard.py
- src/specify_cli/coordination/transaction.py
- src/specify_cli/coordination/status_transition.py
- tests/status/test_mission_write.py
- tests/status/test_checkout_claim_lock.py
- tests/architectural/test_status_events_writes_gate.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---

# Work Package Prompt: WP01 – Mission write primitive and verified rollback

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

Deliver the **Mission write primitive** (plan D1 + amendments A1–A3, A9 key/guard, A13) and move the two in-lock truncates onto it. After this WP:

- `specify_cli/status/mission_write.py` exists and is the only module in `src/specify_cli` that truncates or unlinks a Mission's `status.events.jsonl`.
- `BookkeepingTransaction._rollback` and the coord fallback arm use it; behaviour on the happy path is unchanged.
- `write_checkout_claim_lock` exists in `status/locking.py` (consumers arrive in WP02/WP03).
- `tests/architectural/test_status_events_writes_gate.py` is green with its sets updated.

## Subtasks & Detailed Guidance

### T001 – Red-first pins of the blind truncate

- `tests/status/test_mission_write.py` (new). Build a real temp git repo with a Mission dir holding `status.events.jsonl` + `status.json`.
- Pin, against the CURRENT code, before writing the primitive:
  1. `status_transition._restore_coord_status_artifacts(coord_fd, pre_emit_event_size=N, ...)` cuts a row appended and committed by "another writer" after capture (append a valid row, `git commit` it, then call the restore): assert the committed row survives on disk → RED today.
  2. Shrunk-log case: capture size N, replace the log with a shorter file (simulating an atomic rewrite), call the restore: assert no NUL bytes in the file → RED today (truncate extends with NULs).
- Record RED in the tracer. These tests then retarget the primitive (keep them as the primitive's regression pins).

### T002 – Committed-blob helper in `kernel.git`

- Lift `status_surface_guard._committed_log(worktree_root, relative)` (`src/specify_cli/coordination/status_surface_guard.py:45`) into `kernel.git` as a public helper, e.g. `blob_at(cwd: Path, ref: str, path: str) -> bytes | None` built on the existing `tree_entry` + `run_git("cat-file", "blob", oid)`; export it from `kernel/git/__init__.py` and add it to `listing.py`'s and the package's `__all__` (charter: every `src/kernel` module declares `__all__`). Raises `GitCommandError` on failure, returns `None` when the ref does not track the path.
- `status_surface_guard` calls the lifted helper (behaviour identical; its tests stay green).
- Unit-test the helper in the kernel git test dir (find it: `grep -rl "tree_entry" tests/kernel tests/ | head`).
- Decide the path form: `tree_entry`'s path is relative to the worktree root. The primitive needs the checkout root of the file: resolve with `git rev-parse --show-toplevel` from the file's directory through `kernel.git.run_git` (one call), or `git ls-tree HEAD -- ./status.events.jsonl` relative to cwd if the helper supports it. Pin whichever you choose with a coord-worktree test.

### T003 – `specify_cli/status/mission_write.py`

Public API (names fixed; exported from the status facade in T006):

```python
MISSION_WRITE_LOCK_TIMEOUT_SECONDS = BOUNDED_STATUS_LOCK_TIMEOUT_SECONDS  # reuse, do not redefine 10.0
STATUS_ROLLBACK_REFUSED = "STATUS_ROLLBACK_REFUSED"

@contextmanager
def mission_write_lock(feature_dir: Path, *, repo_root: Path | None = None, timeout: float = BOUNDED_STATUS_LOCK_TIMEOUT_SECONDS) -> Iterator[Path]
    # == feature_status_lock(resolve_status_lock_root(feature_dir, repo_root), feature_dir.name, timeout=timeout)

def locked_rewrite_text(path: Path, transform: Callable[[str | None], str], *, feature_dir: Path, repo_root: Path | None = None, timeout: float = ..., encoding: str = "utf-8") -> str
    # under mission_write_lock: read (None if missing), new = transform(current); atomic_write (kernel.atomic) only if changed; return new

@dataclass(frozen=True)
class RollbackPoint: events_path; status_path; pre_event_size: int; pre_status_bytes: bytes | None; events_existed: bool

def capture_rollback_point(feature_dir: Path, *, repo_root: Path | None = None) -> RollbackPoint
    # raises RuntimeError unless the calling thread holds the Mission write lock for feature_dir
    # (check membership of feature_status_lock_path(resolve_status_lock_root(...), feature_dir.name) in status.locking._get_thread_locks(); compare resolved paths)

class RollbackRefusal(StrEnum): LOG_VANISHED, LOG_SHRANK, TAIL_UNPARSEABLE, TAIL_NOT_OWNED, TAIL_ALREADY_COMMITTED, HEAD_UNREADABLE

@dataclass(frozen=True)
class RollbackOutcome: rolled_back: bool; refusal: RollbackRefusal | None; events_path: Path
    def message(self) -> str  # "STATUS_ROLLBACK_REFUSED: <reason>; <log> left unchanged. Inspect with: git diff HEAD -- <log>"

def rollback_events_log(point, *, expected_event_ids: Sequence[str] | None = None, repo_root: Path | None = None) -> RollbackOutcome
def rollback_status_artifacts(point, *, expected_event_ids=None, repo_root=None) -> RollbackOutcome  # log + status.json only when the log half succeeded
```

Rollback algorithm (inside `mission_write_lock`, re-entrant):
1. Log missing: `events_existed` false → nothing to undo (`rolled_back=True`); existed → refuse `LOG_VANISHED`.
2. Open `r+b` once; `size = os.fstat(fd).st_size`. `size < pre_event_size` → refuse `LOG_SHRANK`. `size == pre_event_size` → nothing appended, `rolled_back=True`.
3. Read `[pre_event_size:]` from the same fd; parse as whole JSON objects, skipping blank lines (a leading `\n` inserted by `store.append_raw_rows_atomic` is legal); any parse failure / non-dict / missing trailing newline on the last row → refuse `TAIL_UNPARSEABLE`.
4. `expected_event_ids` given and multiset(tail ids) ≠ multiset(expected) → refuse `TAIL_NOT_OWNED`.
5. Committed-at-HEAD check via the T002 helper: any tail event id present in the log committed at HEAD of the file's checkout → refuse `TAIL_ALREADY_COMMITTED`. Git error → refuse `HEAD_UNREADABLE` (fail closed). Not a git repo / path not tracked → no committed rows.
6. `os.ftruncate(fd, pre_event_size)` on that same fd (never larger than fstat size), fsync. If `events_existed` is false and pre size is 0, unlink instead (the BookkeepingTransaction arm) — still after steps 3–5.
7. Every refusal logs WARNING with the outcome message and leaves both files byte-identical.

`rollback_status_artifacts`: on log success, restore `status.json` to `pre_status_bytes` (unlink when `None`) using `kernel.atomic.atomic_write`.

Keep each function ≤ 15 complexity (split the checks into small helpers).

### T004 – `write_checkout_claim_lock`

In `status/locking.py` next to `project_event_log_lock`:

```python
CHECKOUT_CLAIM_LOCK_TIMEOUT_SECONDS: float = 120.0
@contextmanager
def write_checkout_claim_lock(write_checkout: Path, *, timeout: float = CHECKOUT_CLAIM_LOCK_TIMEOUT_SECONDS) -> Iterator[Path]
```

- Key: `__checkout-<sha1(os.path.normcase(str(write_checkout.resolve())))[:16]>__` under `_git_common_dir(write_checkout) / LOCK_DIRECTORY`, via `_named_status_lock` (re-entrant, holder sidecar, `FeatureStatusLockTimeoutError` naming holder on timeout).
- Lock-order guard: if the calling thread already holds any `*.status.lock` other than a checkout claim lock (inspect `_get_thread_locks()` keys) and does not already hold this checkout lock, raise `RuntimeError("checkout claim lock must be taken before any Mission lock")`.
- Tests: re-entrancy, cross-thread exclusion (thread B blocks until A releases, deterministic with Events), timeout names holder, lock-order guard raises.

### T005 – Migrate the two in-lock truncates

- `coordination/transaction.py::_rollback` (~:1280-1325): build a `RollbackPoint` from `_pre_emit_size`/existence it already captured (capture runs inside its lock at ~:873, so either call `capture_rollback_point` there or construct the dataclass directly with a short comment), call `rollback_events_log(point, expected_event_ids=self._event_ids or None)`; keep its own lazy `status.json` snapshot restore but only when the log half rolled back. Keep the "nothing appended" fast path. Surface a refusal: log it and attach the outcome message to the raised `BookkeepingCommitFailed`/existing error text (do not swallow).
- `coordination/status_transition.py`: `_snapshot_coord_status_artifacts` → `capture_rollback_point` (it runs inside `coord_status_lock`); `_restore_coord_status_artifacts` → `rollback_status_artifacts`. `coord_status_lock` delegates to `mission_write_lock(coord_feature_dir, repo_root=repo_root, timeout=BOUNDED_STATUS_LOCK_TIMEOUT_SECONDS)` — same lock file (test it).
- Existing tests: `tests/status/test_writer_serialization.py`, `tests/specify_cli/coordination/` (rollback/transaction tests), `tests/coordination` if present — all green.

### T006 – Facade and the existing writes gate

- `src/specify_cli/status/__init__.py`: export the T003/T004 names in **their own import block and their own `__all__` region** (append at the end of `__all__` with a comment line) so #5876's additions do not collide.
- `tests/architectural/test_status_events_writes_gate.py` (set equality — all in this commit):
  - remove `("specify_cli.coordination.transaction","Path.open","self._events_path")` and the `status_transition` entry from `ALLOWED_OUT_OF_STORE_WRITE_SITES` (adjust counts if they hold other sites);
  - add the primitive's site(s) to `EXPECTED_UNRESOLVED_EVENT_NAMED_WRITE_SITES` (or the allowlist, whichever the scanner classifies it as);
  - add `"specify_cli.status.mission_write"` to `EXPECTED_LOCK_COMPOSITION_SITES`; extend `has_lock_call_site` to count `mission_write_lock(` as a lock composition, and add any module that now composes via `mission_write_lock` (in this WP: `coordination.status_transition` already listed?) — run the gate and make the census exact.
  - The workflow `events_path` entry stays until WP02.

## Test Strategy

```bash
.venv/bin/python -m pytest tests/status/test_mission_write.py tests/status/test_writer_serialization.py tests/status/test_locking_key.py tests/status/test_locking_reentrancy_migration.py -q
.venv/bin/python -m pytest tests/specify_cli/coordination -q -x -n auto --dist loadfile
.venv/bin/python -m pytest tests/architectural/test_status_events_writes_gate.py tests/architectural/test_status_module_boundary.py tests/architectural/test_lock_primitive_ban.py tests/architectural/test_layer_rules.py -q
.venv/bin/python -m pytest <kernel git tests> -q
make test-fast
uv run --frozen ruff check <files>; uv run --frozen ruff format --check --force-exclude <files>; uv run --frozen mypy <files>
```

## Definition of Done

- T001 pins were RED on the old code (recorded) and are GREEN now; NUL padding impossible by construction.
- All listed test files green; gates green; ruff/format/mypy clean.

## Risks & Mitigations

- The holder check in `capture_rollback_point` must agree with how callers took the lock (`owned_root`, `repo_root`, `resolve_status_lock_root`); compare `feature_status_lock_path(...)` resolved paths and test owned + coord + flat arms.
- Status package must not import `specify_cli.coordination` (cycle); parse ids with `json` locally.

## Review Guidance

- Verify the rollback never calls `truncate` with a size above the fd's current size and never runs outside the lock.
- Verify refusals leave files byte-identical (tests compare bytes).

## Activity Log
