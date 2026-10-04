# Work Packages: Implement command degod (tidy-first)

**Inputs**: Design documents from `kitty-specs/implement-degod-01M44488/`
**Prerequisites**: plan.md, spec.md, research.md (R-1…R-6), data-model.md, contracts/seam-decisions.md, quickstart.md, research/code-grounding.md, research/test-remediation.md

**Tests**: required. The spec makes tests part of the deliverable (FR-009, FR-010, FR-011, FR-013, FR-015, SC-002, SC-005).

**Organization**: subtasks (`Txxx`) roll up into work packages (`WPxx`).
- WP01–WP08 each change `src/specify_cli/cli/commands/implement.py` and run as one
  dependency-ordered chain in a single lane.
- The ownership validator exempts dependency-ordered pairs from the overlap rule.
- WP09 is a planning-artifact package.

## Subtask Format: `[Txxx] [P?] Description`

- **[P]** marks a subtask that can proceed in parallel with the others in its WP.
- Subtasks are **reference rows**. Record completion with
  `spec-kitty agent tasks mark-status <Txxx> --status done`.

## Path Conventions

Single project: `src/specify_cli/…`, `tests/…`.

Binding rules for every code WP (spec C-001..C-004, research R-3):
- **Move, then adjust.** Move code verbatim in its own commit. Adjust callers and imports, delete
  re-exports and fix typing in a second commit.
- **Gates follow the code.** Widen or re-point the gates in the same WP (FR-012).
- **Run the out-of-matrix tests locally.** Record the commands and counts in the WP's activity log
  (NFR-006).

---

## Work Package WP01: Safety net before any move (Priority: P0)

**Goal**: freeze today's implement behaviour through public entry points, make stale test patches loud, and repair the vacuous tests, all before any source moves.
**Independent Test**: the new characterization suite and the widened liveness gate are green on the base commit. Each planted break per refusal family turns the suite red.
**Prompt**: `tasks/WP01-safety-net.md`
**Requirement Refs**: FR-009, FR-010, FR-013, FR-014, SC-003

### Included Subtasks

T001 Widen `test_tasks_patch_targets_live.py` to the implement command family; fix any dead implement patch it surfaces (no baseline raise)
T002 Characterization suite part 1: refusal families + no-mutation (`tests/specify_cli/cli/commands/test_implement_characterization.py`)
T003 Characterization suite part 2: side-effect order, #4888 message, claim-commit exception table, `--json` payloads, programmatic call, via a dispatch-map fixture
T004 [P] Repair the vacuous tests (FR-013) with planted-break proofs
T005 Record planted-break evidence and the counter baseline in the WP activity log

### Implementation Notes

- The tests use only the public entry points and real-git fixtures. Failure injection goes
  through the dispatch map (research R-5).

### Dependencies

- None (starting package).

### Risks & Mitigations

- Characterization that patches internals would break SC-003. Assertions must never name
  implement-family internals.

---

## Work Package WP02: Context and dependency gate into their seams (Priority: P1)

**Goal**: move the WP-file lookup, the lanes-dir read and the target-branch read into `workspace/context.py`, and the claim-precondition decision into `core/dependency_graph.py` as a pure snapshot-in function.
**Independent Test**: new seam unit tests call `ensure_wp_claim_preconditions` and the workspace reads directly, with no CLI and no implement patches. The characterization suite is unchanged and green.
**Prompt**: `tasks/WP02-context-and-dependency-gate.md`
**Requirement Refs**: FR-003, FR-006, FR-012, NFR-002

### Included Subtasks

T006 Move `find_wp_file`, `_resolve_lanes_dir`, `resolve_feature_target_branch` into `workspace/context.py` (verbatim move commit)
T007 Move the claim-precondition decision into `core/dependency_graph.py` as `ensure_wp_claim_preconditions` (snapshot in, pure); event I/O stays in the caller
T008 Adjust commit: callers, re-export deletion, `__all__`, the `dead_symbol_allowlist.yaml` row, typing fixes, and the 2 pre-existing strict errors in `dependency_graph.py`
T009 [P] Seam unit tests: `tests/specify_cli/core/test_claim_preconditions.py`, `tests/specify_cli/workspace/test_context_implement_reads.py`
T010 Re-point the affected tests and gates (`test_dependency_graph_canceled.py`, `test_trio_read_seam_migration.py`, `test_cold_import_status_boundary`, `test_status_module_boundary`); run the planted-violation proofs

### Dependencies

- Depends on WP01.

### Risks & Mitigations

- Cold-import boundary: keep status imports lazy where required.
- The lane-map derivation stays byte-identical; it is not deduplicated.

---

## Work Package WP03: Planning-artifact commit split (Priority: P1)

**Goal**: move the ~890-LOC planning-commit block verbatim out of `implement.py`. Pure decisions go to `coordination/planning_commit.py`; the printing and transaction adapter goes to `cli/commands/implement_planning_commit.py`.
**Independent Test**: the seam tests in `tests/specify_cli/coordination/test_planning_commit.py` pass. The characterization suite, the coord-partition smokes and `tests/e2e/test_cli_smoke.py::test_full_workflow_sequence` stay green.
**Prompt**: `tasks/WP03-planning-commit-split.md`
**Requirement Refs**: FR-004, FR-012, NFR-005

### Included Subtasks

T011 Create `coordination/planning_commit.py` by moving the pure decisions verbatim: partition, partition guard, demotion predicate + `_read_json_at_ref`, bookkeeping identifiers, candidate enumeration, source dir
T012 Create `cli/commands/implement_planning_commit.py` by moving the adapter verbatim: `_ensure_planning_artifacts_committed_git`, `_commit_planning_artifacts_transaction`, `_run_planning_artifact_commit`, print helpers, `_refuse_on_unreadable_planning_status`, `_planning_commit_branch`
T013 Adjust commit: imports, re-export deletion, typing to strict, no `cli` import in `coordination/`
T014 Re-point the test imports and patches (8 files import `_ensure_planning_artifacts_committed_git`, plus the private-helper importers); update the dispatch map
T015 Widen or re-point the gates with planted-violation proofs: `test_wp_integrity_partition_call_shape._IMPLEMENT`, `CHURN_SURFACE_MODULES`, `_TRIO_FILES`, `_WRITE_DIR_CONSUMER_MODULES`, mid8, meta census, cutover byte stability, terminology and alias scans
T016 [P] Seam unit tests `tests/specify_cli/coordination/test_planning_commit.py`; run the e2e smoke (#3371 lesson)

### Dependencies

- Depends on WP02.

### Risks & Mitigations

- Largest diff. Keep the move commit pure so `--color-moved` shows it.
- The C-006 five-tuple must hold.

---

## Work Package WP04: #5232 seam-owned planning placement (B2*) (Priority: P1)

**Goal**: replace the meta-derived placement fallback with the typed `PlanningPlacement` from `coordination/planning_commit.py` (research R-1, B2*). Remove the `None` overload, reduce the remedy text to one definition, and keep every reachable outcome byte-identical.
**Independent Test**: the FR-015 reachability tests, committed red-first, go green. The characterization suite is unchanged and green, and INV-7 is re-keyed and green.
**Prompt**: `tasks/WP04-seam-owned-placement.md`
**Requirement Refs**: FR-008, FR-015, FR-018, SC-004, C-007

### Included Subtasks

T017 Red-first commit: FR-015 reachability tests on real-git fixtures for every reachable R-1 row and the healthy rows per topology (`tests/specify_cli/cli/commands/test_implement_placement_reachability.py`)
T018 Implement `PlanningPlacement` + `resolve_planning_placement` in `coordination/planning_commit.py` (context first, then a seam-owned degrade using `DECISION_LOG`, then fail-closed)
T019 Rewire the adapter arms on the typed placement; delete the `placement_ref=None` overload and the meta placement read (the `[0]` consumer); drop the C-004 wording from docstrings and comments only
T020 FR-018: one `PlacementResolutionRequired` remedy definition; retire `_resolve_placement_ref`'s `None` contract; reuse or delete `_resolve_claim_commit_target`
T021 Rewrite the tests that pin or force the `None` path, re-key INV-7 to the typed placement, and re-calibrate the partition-call floor with a rationale and a planted break

### Dependencies

- Depends on WP03.

### Risks & Mitigations

- Any reachable outcome change means **stop and escalate** (C-007).

---

## Work Package WP05: Lane selection and allocation preflight into the lanes seam (Priority: P1)

**Goal**: move lane lookup, the origin-preferred `--base` resolution, the repository-root write-checkout refusal and the VCS-lock decision into `lanes/implement_support.py` with typed errors. The command keeps the exact printed texts.
**Independent Test**: `tests/lanes/test_implement_support_lane_selection.py` passes. The base-flag, base-ref, single_branch refusal and characterization suites are unchanged and green.
**Prompt**: `tasks/WP05-lane-selection-seam.md`
**Requirement Refs**: FR-005, FR-012, C-006

### Included Subtasks

T022 Move `_rev_parse_ref`, `_is_ancestor`, `_resolve_base_ref`, `_validate_base_ref`, `_git_stdout` (as needed), `_resolve_execution_lane`, `_resolve_active_lanes_manifest` and `_refuse_repo_root_checkout_if_unavailable` into `lanes/implement_support.py` (verbatim move commit)
T023 Adjust commit: typed `BaseRefUnresolved`; the tracker step completion and the planning-lane warning stay printed by the command; typing fixes
T024 VCS-lock decision `ensure_vcs_locked` with typed errors; the command keeps `_ensure_vcs_in_meta`'s output and order
T025 [P] Seam unit tests `tests/lanes/test_implement_support_lane_selection.py`; re-point `test_implement_base_flag.py`, `test_implement_base_ref.py`, `test_resolve_lanes_dir.py`, `test_lane_base_honoring.py`
T026 Gates: `dead_symbol_allowlist.yaml` (`_ensure_vcs_in_meta` row), `_WRITE_DIR_CONSUMER_MODULES` / `CHURN_SURFACE_MODULES` if implicated; planted-violation proofs; dispatch-map update

### Dependencies

- Depends on WP04.

### Risks & Mitigations

- The "refusals before VCS lock" order and the canonical base-ref message are pinned; keep them.

---

## Work Package WP06: Claim recording seam (Priority: P1)

**Goal**: move claim preflight, status start and the claim commit into `cli/commands/implement_claim.py`. Extract the pure `claim_commit_paths` (shapes #5673), and dedupe the claim policy metadata into the status facade.
**Independent Test**: `tests/specify_cli/cli/commands/test_implement_claim.py` covers the path bundle and the propagate/soften table at seam level. The `tests/status/` coverage of the shared helper passes. The characterization suite is unchanged and green.
**Prompt**: `tasks/WP06-claim-recording-seam.md`
**Requirement Refs**: FR-007, FR-012

### Included Subtasks

T027 Move `_protected_branch_status_commit_error`, `_status_commit_destination_branch`, `_raise_if_status_commit_protected`, `_claim_policy_metadata`, `_start_wp_implementation_status`, `_primary_surface_status_paths` and `_commit_wp_claim_status` into `implement_claim.py` (verbatim move commit)
T028 Extract the pure `claim_commit_paths(...)`; `_commit_wp_claim_status` uses it, with the bundle order unchanged
T029 Shared `claim_policy_metadata(shell_pid, agent)` in the status facade; `implement_claim` and `agent/workflow_executor.py` both call it; add in-matrix tests under `tests/status/`
T030 Re-point the WS#3 allow-list entry and its twin guard, the `test_implement_placement_routing.py` except-order source pin, `test_issue_610_head_mismatch_not_swallowed.py`, `test_implement_compact_identity_4665.py`, and the dispatch map
T031 [P] Seam tests `test_implement_claim.py` (bundle, propagate/soften table)

### Dependencies

- Depends on WP05.

### Risks & Mitigations

- The except-order pin freezes the claim-commit `try`; move it whole.
- New `status/` lines need in-matrix coverage (diff-cover).

---

## Work Package WP07: Thin command and phase sequence (Priority: P1)

**Goal**: `implement()` becomes Typer parsing plus a call into `implement_phases.py`'s ordered phase functions. `--recover` moves to `implement_recover.py`. The Typer signature and decorators stay byte-identical, and `implement.py` is at most 800 lines.
**Independent Test**: a phase-order test records the phase-function call order. The programmatic-call, `--json` and characterization suites are unchanged and green. `implement()` complexity is below 15.
**Prompt**: `tasks/WP07-thin-command-and-phases.md`
**Requirement Refs**: FR-001, FR-002, FR-014, NFR-001, NFR-002, SC-001

### Included Subtasks

T032 Create `implement_phases.py`: immutable phase results (data-model.md) and one function per phase, moving the bodies verbatim from `implement()`
T033 Create `implement_recover.py` (verbatim move of `_run_recover_mode` and `_recover_*`)
T034 Thin `implement()`: tracker steps and per-step exception rendering, unchanged; signature and decorators byte-identical
T035 Phase-order test `tests/specify_cli/cli/commands/test_implement_phases.py`; re-point `test_operational_context_wiring.py` and the `test_implement_placement_routing.py` forbidden-ternary scan
T036 The mypy quarantine entry for `implement.py` (remove it if strict-clean, otherwise list the remaining errors); widen the gate lists for the new modules; planted-violation proofs; `wc -l` check

### Dependencies

- Depends on WP06.

### Risks & Mitigations

- Print order is part of the `--json` contract.
- Never cache `console.file`.
- Keep the `OptionInfo` defaults (#5650 class).

---

## Work Package WP08: Test migration, docs and closing measurements (Priority: P2)

**Goal**: migrate the remaining tests that string-patch implement internals onto seams or real fixtures (the biggest is `tests/agent/test_implement_command.py`, with 54 string targets). Re-point the docs, add the CHANGELOG entry, and measure SC-002, SC-005 and NFR-003.
**Independent Test**: the counter reports at most 45 family patch sites. Each phase has a seam unit test. The regression subset runs in at most 30 s.
**Prompt**: `tasks/WP08-test-migration-and-docs.md`
**Requirement Refs**: FR-011, FR-016, SC-002, SC-005, NFR-003, NFR-004, NFR-006

### Included Subtasks

T037 Migrate `tests/agent/test_implement_command.py` (orchestration tests → seam calls, real fixtures or phase-function tests; keep one CLI smoke per family)
T038 Migrate `test_status_emit_on_alloc_failure.py`, `test_implement_bulk_edit_planning.py`, `test_implement_vcs_lock_claim.py`, `test_implement_runtime_frontmatter_claim.py`, `test_specify_topology_flag.py` and the remaining class-A/B files
T039 [P] Docs re-point (`wp-runtime-state-eviction.md`, `read-side-seam-classification.md`, the git-operations-matrix `Source File` cells, `04_implementation_mapping/README.md`) and the CHANGELOG `[Unreleased]` entry
T040 Closing measurements: counter before and after, the SC-005 phase-to-seam-test table, NFR-003 timing, and the full targeted run recorded

### Dependencies

- Depends on WP07.

### Risks & Mitigations

- Never edit an assertion to make a migration pass. Add the seam test before trimming an e2e test.

---

## Work Package WP09: Issue matrix and follow-ups (Priority: P2)

**Goal**: record the issue-matrix rows for every addressed issue, and file the follow-up issues named in the spec Assumptions and research R-1.
**Independent Test**: `issue-matrix.md` carries a row and verdict per issue, and each follow-up has an issue number.
**Prompt**: `tasks/WP09-issue-matrix-and-follow-ups.md`
**Requirement Refs**: FR-017

### Included Subtasks

T041 Write `issue-matrix.md` rows: #5635 and #5232 delivered (close); #5673 shaped (`claim_commit_paths`); #5676, #5669 and #3931 out of scope
T042 File the follow-ups and record their numbers: planning commit before late validation; misleading "not finalized" for an unmaterialized coordination worktree; shared implement application service (ADR); the #5232 single-path end state (B1, operator decision)

### Dependencies

- Depends on WP08.

---

## Dependency & Execution Summary

- **Sequence**: WP01 → WP02 → WP03 → WP04 → WP05 → WP06 → WP07 → WP08 → WP09. This is a linear
  refactor chain over one hot file in one lane.
- **Parallelization**: within a WP only (`[P]` subtasks). Across WPs the shared `implement.py`
  forbids it.
- **MVP scope**: WP01. The safety net alone makes the rest safe to land incrementally.

## Requirements Coverage Summary

| Requirement ID | Covered By Work Package(s) |
|----------------|----------------------------|
| FR-001 | WP07 |
| FR-002 | WP07 |
| FR-003 | WP02 |
| FR-004 | WP03 |
| FR-005 | WP05 |
| FR-006 | WP02 |
| FR-007 | WP06 |
| FR-008 | WP04 |
| FR-009 | WP01 |
| FR-010 | WP01 |
| FR-011 | WP08 |
| FR-012 | WP02, WP03, WP05, WP06, WP07 |
| FR-013 | WP01 |
| FR-014 | WP01, WP07 |
| FR-015 | WP04 |
| FR-016 | WP08 |
| FR-017 | WP09 |
| FR-018 | WP04 |

## Subtask Index (Reference)

| Subtask ID | Summary | Work Package | Priority | Parallel? |
|------------|---------|--------------|----------|-----------|
| T001 | Widen patch-liveness gate | WP01 | P0 | No |
| T002 | Characterization: refusals | WP01 | P0 | No |
| T003 | Characterization: order/exception/json | WP01 | P0 | No |
| T004 | Vacuous test repair | WP01 | P0 | Yes |
| T005 | Planted-break evidence | WP01 | P0 | No |
| T006 | Move context reads → workspace | WP02 | P1 | No |
| T007 | Move claim preconditions → dependency_graph | WP02 | P1 | No |
| T008 | Adjust commit WP02 | WP02 | P1 | No |
| T009 | Seam tests WP02 | WP02 | P1 | Yes |
| T010 | Re-point tests/gates WP02 | WP02 | P1 | No |
| T011 | coordination/planning_commit.py move | WP03 | P1 | No |
| T012 | implement_planning_commit.py move | WP03 | P1 | No |
| T013 | Adjust commit WP03 | WP03 | P1 | No |
| T014 | Re-point test imports WP03 | WP03 | P1 | No |
| T015 | Gates WP03 | WP03 | P1 | No |
| T016 | Seam tests + e2e WP03 | WP03 | P1 | Yes |
| T017 | FR-015 red-first reachability tests | WP04 | P1 | No |
| T018 | PlanningPlacement | WP04 | P1 | No |
| T019 | Rewire arms, delete None overload | WP04 | P1 | No |
| T020 | Remedy dedupe, dead helper | WP04 | P1 | No |
| T021 | Rewrite None-path tests, INV-7 | WP04 | P1 | No |
| T022 | Move lane selection → lanes | WP05 | P1 | No |
| T023 | Adjust commit WP05 | WP05 | P1 | No |
| T024 | VCS-lock decision | WP05 | P1 | No |
| T025 | Seam tests WP05 | WP05 | P1 | Yes |
| T026 | Gates WP05 | WP05 | P1 | No |
| T027 | Move claim recording | WP06 | P1 | No |
| T028 | claim_commit_paths | WP06 | P1 | No |
| T029 | claim_policy_metadata dedupe | WP06 | P1 | No |
| T030 | Re-point pins WP06 | WP06 | P1 | No |
| T031 | Seam tests WP06 | WP06 | P1 | Yes |
| T032 | implement_phases.py | WP07 | P1 | No |
| T033 | implement_recover.py | WP07 | P1 | No |
| T034 | Thin implement() | WP07 | P1 | No |
| T035 | Phase-order test + pins | WP07 | P1 | No |
| T036 | Quarantine, gates, wc -l | WP07 | P1 | No |
| T037 | Migrate test_implement_command.py | WP08 | P2 | No |
| T038 | Migrate remaining class-A/B files | WP08 | P2 | No |
| T039 | Docs + CHANGELOG | WP08 | P2 | Yes |
| T040 | Closing measurements | WP08 | P2 | No |
| T041 | Issue matrix | WP09 | P2 | No |
| T042 | File follow-ups | WP09 | P2 | No |
