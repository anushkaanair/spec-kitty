# Mission Specification: A WP leaves review or approval only through a recorded verdict or an operator force with a note

**Mission Branch**: `issue-5446-review-exit-guard`
**Created**: 2026-10-07
**Status**: Draft
**Input**: Orchestrator brief for #5446 (P0), with #5340, #5721 (forced-approval part) and #5194 folded in.

## Intent Summary (confirmed from the brief and the issues)

- **Primary actor:** an agent running `spec-kitty agent action implement <WP> --agent <name>` in a multi-agent Mission; secondarily the reviewer who holds or granted the review, and the operator who may override.
- **Trigger:** the implement command is run for a work package (WP) that is `for_review`, `in_review` or `approved`, for example by an orchestrator that re-dispatches the wrong WP.
- **Desired outcome:** the command refuses, the same way it already refuses a second agent on an `in_progress` WP, unless the caller is the WP's own implementer withdrawing an unclaimed submission, or an operator passes `--force` with a `--note`. No status event ever carries a review reason that no reviewer gave.
- **Invariant:** a WP leaves `for_review`, `in_review` or `approved` only through a recorded verdict, its own implementer's withdrawal of an unclaimed submission, or an operator force that carries the operator's note.
- **Domain terms:** Mission, work package (WP), implementer of record, review cycle, review verdict, approval stamp (`lane_head`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Another agent cannot take a WP out of review or approval (Priority: P1)

A second agent runs `agent action implement` on a WP that is under review or already approved. Today it exits 0, force-moves the WP to `in_progress`, and records "Re-implementing after review feedback". After the change it is refused with a message that names who holds the WP and the route that does what the caller wanted.

**Why this priority**: it is the P0 in #5446: false success, a fabricated record, a reviewer silently displaced and an approval silently discarded.

**Independent Test**: the issue's reproducer, driven through the real `agent action implement` entry point.

**Acceptance Scenarios**:

1. **Given** WP02 is `in_review` and claimed by reviewer `rev`, **When** `agentB` runs `agent action implement WP02 --agent agentB`, **Then** it exits non-zero with a claim conflict naming `rev`, no status event is written, and `rev` can still approve WP02.
2. **Given** WP03 is `approved` by `rev`, **When** `agentB` runs `agent action implement WP03 --agent agentB`, **Then** it exits non-zero, no status event is written, and the message names the route `agent tasks move-task WP03 --to planned --review-feedback-file <file>` for sending an approved WP back.
3. **Given** WP04 is `for_review` (submitted by `agentA`, no reviewer has claimed it), **When** `agentB` runs implement on it, **Then** it is refused naming `agentA`; **When** `agentA` runs it, **Then** WP04 moves to `in_progress` with a reason that says the implementer withdrew the submission, never a review-feedback reason.
4. **Given** the WP's implementer of record runs implement on its own WP while it is `in_review`, **Then** it is refused naming the reviewer (the implementer waits for the verdict).

### User Story 2 - An operator can still override, on the record (Priority: P1)

An operator needs to pull a WP back out of review or approval (stuck reviewer, wrong approval).

**Independent Test**: `agent action implement WP02 --agent ops --force --note "reviewer left"` on an `in_review` WP.

**Acceptance Scenarios**:

1. **Given** WP02 is `in_review`, **When** the operator runs implement with `--force --note "<text>"`, **Then** WP02 moves to `in_progress`, the event is forced and its reason carries the note.
2. **Given** `--force` without `--note` (or with a blank note), **Then** the command refuses before writing anything and says `--note` is required.
3. **Given** `--note` without `--force`, **Then** the command refuses and says `--note` only applies with `--force`.

### User Story 3 - A WP that was forced out of review can still be approved (Priority: P1)

After any forced exit from `in_review` with no verdict (an operator force, or history written by the bug before this fix), the reduced state carries an empty review-result slot. Today every later approval of that WP is refused with "review-cycle-damaged-event-record.md has no parseable review verdict", naming a file that does not exist.

**Independent Test**: build that history, run a new `for_review -> in_review` cycle, approve through `move-task --to approved`.

**Acceptance Scenarios**:

1. **Given** WP02 was forced from `in_review` to `in_progress` with no verdict, then resubmitted and claimed again for review, **When** the reviewer approves it with a normal review, **Then** the approval succeeds.
2. **Given** the review-result slot really is unreadable for the current review cycle, **When** approval is refused, **Then** the message names the WP, says why, and names a route that works today; it never names a file that does not exist as the thing to repair.

### User Story 4 - One answer to "who implemented this WP" (Priority: P2)

The ownership guards, the implement guard of this Mission and the consolidation hollow-review check all ask who implemented the WP. They answer from one projection (#5340).

**Acceptance Scenarios**:

1. **Given** an honest loop implement (I) -> review (R) -> reject with a rework verdict -> rework (I) -> approve (R) with two or more forced moves on record, **When** `consolidate` checks for hollow reviews, **Then** it does not warn that the reviewer approved their own work.
2. **Given** I approves its own work, **Then** the warning still prints (non-vacuity twin).

### User Story 5 - A forced move into `approved` does not restamp the approval bound (Priority: P2)

A forced move into `approved` (`approved -> approved --force`, `canceled -> approved --force`, `in_progress -> approved --force`) is not a review. `consolidate`'s approval-stamp bound uses the newest review approval (unforced, an arbiter override, or an approved-reviewed attestation), so a commit made after the real approval is still refused (#5721, forced-approval residual).

**Acceptance Scenarios**:

1. **Given** WP01 approved by review, then a late commit on its lane, then `move-task WP01 --to approved --force`, **When** `consolidate` runs, **Then** it refuses with `LANE_MOVED_AFTER_APPROVAL`.
2. **Given** a WP never reviewed but forced into `approved`, **Then** consolidate refuses with `APPROVAL_STAMP_MISSING` (attestation remains the recorded route).
3. **Given** an arbiter override (forced `planned -> approved` right after a rejection), **Then** its stamp still counts.
4. **When** a forced, non-arbiter approval is recorded through `move-task` or `agent status emit`, **Then** a one-line warning on stderr says it is not a review approval for the bound.

### User Story 6 - Every review cycle keeps its own artifact (Priority: P2)

A second rejection never overwrites `review-cycle-1.md` (#5194).

**Acceptance Scenarios**:

1. **Given** a WP rejected once (cycle 1 on disk), resubmitted and rejected again, **Then** `review-cycle-2.md` is written and `review-cycle-1.md` is byte-identical to before, whichever status surface the cycle count and the write use.

### Edge Cases

- Generic placeholder actors (`user`, `unknown`, `implement-command`) never count as an implementer of record; a WP whose only implementer is generic is refused for `for_review` withdrawal unless forced.
- The #5377 path stays green: after a reviewer's rework verdict (`in_review -> in_progress` with a review reference) the implementer of record resumes without `--force`.
- An `in_progress` WP behaves exactly as today (no-op resume or claim conflict).
- A WP in `done` or `canceled` is still rejected as not startable, also with `--force` (leaving a terminal lane is `move-task --force`'s job).
- `--force` applies only to a WP in `for_review`, `in_review` or `approved`; on any other lane the command refuses it before writing anything, so an override is never recorded where none was needed.
- Actor identity is compared per tool, the same rule the existing `claimed`/`in_progress` claim guard uses: another session of the same tool counts as the same implementer.
- An operator force records the `--agent` value as the actor, so the operator names the agent that will implement (usually the original implementer) and that agent becomes the implementer of record.
- The new rules apply only to `agent action implement`. `spec-kitty implement` and `orchestrator-api start-implementation` keep refusing every review lane exactly as today.
- A forced move into `approved` that carries an approved review result (for example a reviewer forcing past an unrelated gate, or the self-review fallback) is still a review approval for the bound; only a forced approval with no review evidence is skipped.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Title | User Story | Priority | Status | Delivery | No-op passable? |
|----|-------|------------|----------|--------|----------|-----------------|
| FR-001 | Refuse an in_review takeover | As a reviewer, I want `agent action implement` on a WP I hold `in_review` to be refused with a claim conflict naming me, so that my review is not silently discarded. | High | Open | [build] | no — the #5446 reproducer exits 0 today |
| FR-002 | Refuse an approved takeover | As a reviewer, I want `agent action implement` on an `approved` WP to be refused and name the `move-task --to planned --review-feedback-file` route, so that an approval is only undone by a recorded verdict. | High | Open | [build] | no — exits 0 today |
| FR-003 | Only the implementer of record withdraws a for_review WP | As an implementer, I want only the WP's implementer of record to pull an unclaimed `for_review` submission back to `in_progress`, so that another agent cannot take it over. | High | Open | [build] | no — any agent succeeds today; paired with the implementer positive control on the same fixture |
| FR-004 | No fabricated rework reason | As an auditor, I want no status event written by `agent action implement` to carry a review-feedback reason unless a reviewer gave one, so that the status log is truthful. | High | Open | [build] | no — default reason is written today |
| FR-005 | Operator force with a required note | As an operator, I want `agent action implement --force --note <text>` to move a WP out of `for_review`, `in_review` or `approved`, recording a forced event whose reason is my note, and `--force` without a note to be refused, so that every override is on the record. | High | Open | [build] | no — flags do not exist today |
| FR-006 | Approval works after a forced review exit | As a reviewer, I want to approve a WP that was once forced out of `in_review` with no verdict once a new review cycle has begun, so that the WP is not deadlocked. | High | Open | [build] | no — refused today |
| FR-007 | Honest refusal when the verdict slot is unreadable | As a reviewer, I want a refusal on an unreadable review-result slot to name a route that works, not a file that does not exist. | Medium | Open | [build] | no — names a synthetic file today |
| FR-008 | One implementer-of-record projection | As a maintainer, I want the move-task ownership guard, the implement guard and the consolidation hollow-review check to use the single `status` projection of the implementer of record, so that they cannot disagree (#5340). | Medium | Open | [build] | no — consolidation counts a reviewer's rework verdict as the implementer today |
| FR-009 | Forced approvals do not restamp the bound | As a maintainer, I want `consolidate`'s approval-stamp bound to ignore forced moves into `approved` that are not arbiter overrides, and the approval command to warn when one is recorded, so that a late commit cannot land through a restamp (#5721). | Medium | Open | [build] | no — a forced self-approval restamps today |
| FR-010 | A review cycle artifact is never overwritten | As a reviewer, I want each rejection to write its own `review-cycle-N.md` and never replace an earlier one, so that review history survives (#5194). | Medium | Open | [build] | no — pinned by a red-first reproduction |

### Non-Functional Requirements

| ID | Title | Requirement | Category | Priority | Status |
|----|-------|-------------|----------|----------|--------|
| NFR-001 | Refusals write nothing | A refused implement call appends 0 status events and leaves `status.events.jsonl` and `status.json` byte-identical. | Reliability | High | Open |
| NFR-002 | No regression on the rework loop | The #5377 resume-after-rejection tests and the rework guard ratchets pass unchanged (0 edits to their assertions). | Reliability | High | Open |
| NFR-003 | Code quality | New and changed functions have cyclomatic complexity <= 15; ruff, ruff format and mypy report 0 issues on changed files; 0 new suppressions. | Maintainability | High | Open |

### Constraints

| ID | Title | Constraint | Category | Priority | Status |
|----|-------|------------|----------|----------|--------|
| C-001 | Do not edit spec-kitty-events | The reducer behaviour that writes an empty review-result slot on a forced `in_review` exit stays as is; the CLI side handles it and the reducer change is a recorded follow-up. | Technical | High | Open |
| C-002 | Out of scope | #5819, #5468, #5804, #5467, #5820, #5796, #5099 (concurrency), #4941 are not touched. | Business | High | Open |
| C-003 | No global force semantics change | `wp_state` force semantics stay as they are; the guard lives in the implement lifecycle and the bound reader, not in the state machine. | Technical | High | Open |
| C-004 | Red-first | A `@pytest.mark.p0_repro(issue=5446)` reproduction lands before the fix and is flipped to a passing regression after it (ADR `2026-07-17-1`). | Technical | High | Open |
| C-005 | Unforced `in_progress -> approved` edge stays | Removing or guarding that edge is a state-machine and orchestrator-API contract change; it stays a recorded residual of #5721. | Technical | Medium | Open |

### Key Entities

- **Implementer of record**: the actor of the latest move into `claimed` or `in_progress` that is not a reviewer's verdict or claim exit and not a generic placeholder actor (`status/review_roles.py`).
- **Review approval**: an unforced move into `approved` (or unforced `in_review -> done`), an arbiter override, or an approved-reviewed attestation.

## Success Criteria *(mandatory)*

- **SC-001**: The #5446 reproducer (both arms) exits 0 with "product refused every takeover" on the branch.
- **SC-002**: A WP forced out of `in_review` is approved after one new review cycle with no repair step.
- **SC-003**: Zero false hollow-review warnings on the honest reject -> rework -> approve fixture.
