# Mission Specification: Concurrent writers to a Mission's files never lose or steal a write

**Mission Branch**: `issue-5819-concurrent-mission-writers`
**Created**: 2026-10-07
**Status**: Draft
**Input**: Operator brief (2026-10-07) pulling #5819, #5467, #5820, #5796, #5468, #5804 and the one-writer-per-checkout half of #5099 into one structural Mission.

## Purpose

Parallel agents routinely work on one Mission at the same moment: one claims a work package while another moves a lane, adds a history note or appends a tracer finding. Today several of these writers read a Mission file, change it in memory and write it back without the Mission's lock, or roll a failed status commit back by cutting `status.events.jsonl` to a size measured before they took the lock. A command that exited 0 can have its committed write erased, a note can vanish, a log can be padded with NUL bytes, and two implementers can both pass the single-writer check for one shared checkout. This Mission routes every Mission-file mutation in scope through one locked primitive, makes the single_branch claim check atomic, and adds an architectural gate so unlocked read-modify-writes and raw truncates do not come back.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A failed status commit never erases another agent's committed transition (Priority: P1)

Agent A runs `agent action implement WP01`; its status commit fails (another git process holds `.git/index.lock`). Meanwhile agent B ran `move-task WP03 --to canceled` and it exited 0 with two commits.

**Why this priority**: silent loss of a committed lane change, later committed into HEAD by the next writer (#5819, #5804, #5468).

**Independent Test**: deterministic interleaving test with injected hooks: B's committed rows survive A's failed commit on disk and in HEAD.

**Acceptance Scenarios**:

1. **Given** B's transition and annotation are committed, **When** A's status commit fails and A rolls back, **Then** B's rows are still in the on-disk log and the next status writer's commit keeps them in HEAD.
2. **Given** A's own rows are the only rows appended since A's capture and none is committed, **When** A's commit fails, **Then** A's rows are removed and `status.json` is restored to its pre-emit bytes.
3. **Given** the log shrank below A's captured size, or its tail no longer parses as whole rows, or a row in the tail is already committed at HEAD, **When** A rolls back, **Then** the log is left untouched (no NUL padding, no cut) and A reports that the rollback was refused.

### User Story 2 - A claim commit never takes another writer's status rows (Priority: P2)

Agent A runs `spec-kitty implement WP02` on a lanes Mission while agent B runs `move-task WP03 --to in_progress` on the same checkout.

**Why this priority**: the claim commit runs outside the Mission lock and sweeps B's half-written rows; B then fails and truncates them, leaving HEAD and disk disagreeing (#5468).

**Independent Test**: interleaving test that pauses the claim commit and B's emit; afterwards HEAD and disk agree and B exits 0.

**Acceptance Scenarios**:

1. **Given** B holds the Mission lock mid-transition, **When** A reaches its claim commit, **Then** A waits for the lock and commits only after B's commit has landed; both exit 0 and HEAD equals disk.

### User Story 3 - Concurrent coord claims do not corrupt the coordination worktree (Priority: P1)

Two agents run `agent action implement WP01` and `WP03` concurrently on one coord Mission.

**Why this priority**: the coord working copy's event log was corrupted (NUL block, whitespace line) and committed claims were reported as failures (#5804).

**Independent Test**: two claims driven concurrently; the coord log stays valid JSONL and each command's output states truthfully whether its claim committed.

**Acceptance Scenarios**:

1. **Given** two concurrent coord claims, **When** both finish, **Then** the coord log parses line by line and every committed claim row is present.
2. **Given** a claim row was committed but a later follow-up commit or lane sync of the same command failed, **When** the command exits, **Then** its output states that the claim was committed and names the failed follow-up; it exits non-zero only for that follow-up failure and never says the claim was rolled back.

### User Story 4 - Overlapping appends keep both entries (Priority: P1)

Two agents run `agent tracer-append` on the same category, or `agent tasks add-history` on the same WP, at the same moment.

**Why this priority**: both exit 0 and one entry silently disappears (#5467, #5820).

**Independent Test**: pause the first writer after it read the file, let the second finish; both entries are present afterwards.

**Acceptance Scenarios**:

1. **Given** writer 1 has started, **When** writer 2 completes first, **Then** writer 1 re-reads under the lock and both entries end up in the file (and, for tracer-append, in the committed file).

### User Story 5 - Two implementers never share one single_branch checkout by racing (Priority: P1)

Two agents start `spec-kitty implement` (or `agent action implement`) for WPs that resolve to the same single_branch repository-root checkout, in the same or in different Missions.

**Why this priority**: both pass `WRITE_CHECKOUT_OCCUPIED` and both go `in_progress` (#5796).

**Independent Test**: pause the first claim after its occupancy scan; the second claim waits and is refused once the first claim lands.

**Acceptance Scenarios**:

1. **Given** claim 1 has passed its scan but not yet recorded its claim, **When** claim 2 runs, **Then** claim 2 waits and is refused with `WRITE_CHECKOUT_OCCUPIED`; exactly one WP is `in_progress`.

### User Story 6 - A reviewer or implementer is told when another actor works in the same checkout (Priority: P3)

On a single_branch Mission WP01 is `in_progress` by actor A; actor B claims a review of WP02 (#5099, one-writer half).

**Independent Test**: `agent action review WP02 --agent B` prints a warning naming WP01 and A, in human and JSON output; with no concurrent writer it prints none.

**Acceptance Scenarios**:

1. **Given** WP01 `in_progress` by A in the shared checkout, **When** B claims review of WP02, **Then** the claim proceeds and a warning names WP01 and A.
2. **Given** no other actor holds a WP in that checkout, **When** B claims, **Then** no warning is printed.

### Edge Cases

- The rollback runs while the log file has vanished: refuse, never recreate or zero-extend it.
- A safe_commit recovery already created a commit: no rollback (existing behaviour kept).
- Lock contention past the bound (on bounded takes; the initiating implement/review windows wait unbounded, as `start_implementation_status` does today): the command fails loudly naming the lock holder; it never proceeds unlocked.
- The same thread re-enters the Mission lock (emit helpers inside a held window): re-entrant, no deadlock.
- Lock order: the checkout claim lock is always taken before a Mission lock, never after.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Title | User Story | Priority | Status | Delivery | No-op passable? |
|----|-------|------------|----------|--------|----------|-----------------|
| FR-001 | One Mission write primitive | As a maintainer, I want one canonical primitive for Mission-file mutation (the Mission write lock, a locked read-modify-write, and a lock-held rollback point) built on the existing per-mission status lock so that every writer serializes on the same lock file. | High | Open | [build] | no |
| FR-002 | Verified status rollback | As an agent, I want a failed status commit's rollback to remove only rows it appended in the same lock hold, never a row committed at HEAD, and to refuse (log untouched, loud message) when the log shrank, vanished or has an unparseable tail so that another agent's committed transition is never erased. | High | Open | [build] | no |
| FR-003 | Every status-log truncate goes through the primitive | As a maintainer, I want the three rollback truncates (workflow, coord fallback arm, BookkeepingTransaction) to use the verified rollback so that no blind byte truncate of `status.events.jsonl` remains. | High | Open | [build] | no |
| FR-004 | agent action implement holds the lock across capture, emit, commit and rollback | As an agent, I want `agent action implement`'s claim and resume paths to capture the rollback point, emit, commit and roll back inside one Mission lock hold, like `agent action review`, so that #5819 and #5804 cannot occur. | High | Open | [build] | no |
| FR-005 | implement's claim commit runs under the Mission lock | As an agent, I want `spec-kitty implement`'s claim commit to run under the Mission lock so that it never sweeps another writer's uncommitted status rows (#5468). | Medium | Open | [build] | no |
| FR-006 | tracer-append is a locked read-modify-write | As an agent, I want `agent tracer-append` to read, merge, write and commit the tracer file under the Mission lock so that overlapping appends keep both findings (#5467). | High | Open | [build] | no |
| FR-007 | add-history is a locked read-modify-write | As an agent, I want `agent tasks add-history` to re-read and rewrite the WP file under the Mission lock so that overlapping notes are both kept (#5820). | High | Open | [build] | no |
| FR-008 | Atomic single_branch claim | As an agent, I want the single_branch occupancy check and the claim write to run under one checkout-wide claim lock, for both `implement` and `agent action implement`, so that two overlapping claims cannot both pass (#5796). | High | Open | [build] | no |
| FR-009 | Shared-workspace advisory warning | As a reviewer, I want `agent action implement` and `agent action review` to warn (human and JSON output) when another actor holds a WP `in_progress`/`in_review` in the same resolved workspace, and to stay silent otherwise (#5099). | Low | Open | [build] | no — paired with the no-concurrent-writer silent case on the same fixture |
| FR-010 | One-writer doctrine sentence | As a consumer, I want the shipped software-dev implement and review mission-step prompts to state the one-writer-per-checkout rule, including reviewers and single_branch, without touching the `git add -A` / `git stash` guidance owned by #5443. | Low | Open | [build] | no |
| FR-011 | Architectural gate | As a maintainer, I want an architectural gate that refuses a raw `truncate` of a Mission file outside the primitive and refuses a Mission-file read-modify-write sink called outside the Mission lock, starting with an empty allowlist and a self-mutation (non-vacuity) test. | High | Open | [build] | no |

### Non-Functional Requirements

| ID | Title | Requirement | Category | Priority | Status |
|----|-------|-------------|----------|----------|--------|
| NFR-001 | Deterministic concurrency tests | Every concurrency reproduction uses injected hooks/barriers (no sleeps as synchronization) and passes 20/20 consecutive local runs. | Reliability | High | Open |
| NFR-002 | Bounded waits | No new lock wait is unbounded where the existing call site was bounded; the checkout claim lock is bounded (≤120 s) and its timeout error names the lock file and holder. | Reliability | Medium | Open |
| NFR-003 | Code quality | New and changed code passes ruff, ruff format and mypy with zero new suppressions; every touched function stays at complexity ≤ 15. | Maintainability | High | Open |
| NFR-004 | No latency regression | A single uncontended `move-task`, `add-history` or `tracer-append` adds no more than one lock acquire to its current work; only the rollback path adds git calls (at most three, to read the committed log). | Performance | Medium | Open |

### Constraints

| ID | Title | Constraint | Category | Priority | Status |
|----|-------|------------|----------|----------|--------|
| C-005 | Every claim path | `implement`, `agent action implement` and `orchestrator-api start-implementation` all take the checkout claim lock for single_branch repository-root lanes. | Technical | High | Open |
| C-001 | Reuse the existing lock | Mission-file mutation reuses `feature_status_lock` (keyed on the Mission directory name); no parallel per-file lock mechanism is added. | Technical | High | Open |
| C-002 | No commit-scope gate | The `git add -A` / `git stash` prohibition is owned by the upgrade-migration-commit-scope mission (#5443); this Mission does not implement it. | Technical | High | Open |
| C-003 | Stay out of in-flight PRs' files | Keep changes to files touched by PR #5876 (review-exit guard) and #5873 (upgrade commit scope) to the minimal lock call-site changes. | Technical | Medium | Open |
| C-004 | No blocking shared-checkout refusal for review | Review in a shared checkout is warned about, not refused; a blocking refusal is #3129's product decision. | Business | Medium | Open |

### Key Entities

- **Mission write lock**: the per-mission status lock file under the git common dir, keyed on the Mission directory name.
- **Rollback point**: the pre-emit event-log size and `status.json` bytes, captured while the Mission write lock is held.
- **Checkout claim lock**: one lock per write checkout, held across the occupancy check and the claim write.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The #5819 interleaving leaves the other agent's committed rows on disk and in HEAD in 20/20 runs (was 0/3 on rc5). — [build] · no-op passable: no
- **SC-002**: Overlapping tracer-append and add-history pairs keep both entries in 20/20 deterministic runs. — [build] · no-op passable: no
- **SC-003**: Two overlapping single_branch claims result in exactly one `in_progress` WP in 20/20 runs. — [build] · no-op passable: no
- **SC-004**: The architectural gate finds every truncate or unlink of a Mission's status log in `src/specify_cli` inside the Mission write primitive and nowhere else, and fails on a planted one elsewhere. — [build] · no-op passable: no

## Assumptions

- `run.events.jsonl` (runtime bridge) is not a Mission file and is out of scope.
