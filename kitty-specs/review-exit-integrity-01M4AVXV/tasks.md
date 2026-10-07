# Tasks: A WP leaves review or approval only through a recorded verdict or an operator force with a note

Mission: `review-exit-integrity-01M4AVXV` (topology `single_branch`, target `issue-5446-review-exit-guard`).

## Work Package WP01: Review-exit guard and operator force with a note

**Dependencies**: None

Requirement refs: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-002, NFR-003, C-003, C-004

- [ ] T001 Red-first `p0_repro(issue=5446)` reproduction through `agent action implement` (in_review takeover, approved takeover, for_review takeover by a non-owner)
- [ ] T002 Replace `allow_rework`/`rework_reason` in `start_implementation_status` with the lane rules and `operator_force_note`
- [ ] T003 `agent action implement --force --note` (validation before any status write) threaded to the lifecycle
- [ ] T004 Invert `tests/status/test_work_package_lifecycle.py` forced-rework test; add positive controls; keep #5377 tests green

## Work Package WP02: Approval works after a forced review exit

**Dependencies**: None

Requirement refs: FR-006, FR-007, NFR-003, C-001

- [ ] T005 Red-first test: forced in_review exit, new review cycle, approve through move-task
- [ ] T006 `ReviewResultLookup.cleared_without_verdict`; verdict facts treat a cleared slot as no verdict on record
- [ ] T007 Honest refusal text for a malformed slot (no synthetic file to repair)

## Work Package WP03: One implementer-of-record authority for consolidation

**Dependencies**: None

Requirement refs: FR-008, NFR-003

- [ ] T008 Red-first test: honest reject -> rework -> approve loop raises no hollow-review warning; non-vacuity twin
- [ ] T009 `_independent_reviewer_confirmed` reads the implementer via `latest_implementer_actor` (facade import); document the reducer slot as claim provenance in `review_roles`

## Work Package WP04: Forced approvals do not restamp the approval bound

**Dependencies**: None

Requirement refs: FR-009, NFR-003, C-005

- [ ] T010 Red-first tests in `test_approved_bound.py`: forced self-approval after a late commit refuses; never-reviewed forced approval reports a missing stamp; arbiter override still counts
- [ ] T011 `_newest_approval` skips forced non-arbiter approvals; forced-approval warning at move-task / status emit

## Work Package WP05: Review-cycle artifacts are never overwritten

**Dependencies**: None

Requirement refs: FR-010, NFR-003

- [ ] T012 Red-first `@pytest.mark.regression` reproduction for #5194 (cycle 1 on one surface, second rejection allocates on the other)
- [ ] T013 Allocate the next cycle across every read surface; exclusive create on write
