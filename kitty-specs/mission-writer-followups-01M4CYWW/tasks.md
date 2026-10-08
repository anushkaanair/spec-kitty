# Work Packages: Every Mission-file writer takes the lock, and the runtime never cuts a log it cannot prove is its own

**Inputs**: Design documents from `/kitty-specs/mission-writer-followups-01M4CYWW/`
**Prerequisites**: plan.md (including "Amendments after the post-plan squad", which are binding), spec.md, research.md, data-model.md

**Tests**: Required. Every bug fix is red-first: a deterministic reproduction is committed and shown failing on the pre-fix code before the fix lands (ADR 2026-07-17-1).

**Topology**: single_branch. WPs run sequentially in the repository root checkout.

## Subtask Format: `[Txxx] [P?] Description`

Subtasks are reference rows; record completion with `spec-kitty agent tasks mark-status <Txxx> --status done`.

---

## Work Package WP01: One canonical Mission lock key for every lock caller (Priority: P1)

**Goal**: `mission_lock_key(feature_dir)` is the one key every per-Mission lock caller uses (`mission_write_lock`, `hold_mission_write_lock`, every direct `feature_status_lock` caller, `BookkeepingTransaction`, `coord_status_lock`, `_holds_mission_lock`/`capture_rollback_point`), so a legacy bare-directory coordination Mission (`060-test` primary with a `060-test-<mid8>` coordination surface) locks one file from every door, in one order.
**Independent Test**: `tests/status/test_mission_lock_key.py`: key equality across primary, coordination and flat Missions plus the bare-directory coordination fixture; the mid8 cascade; the empty-mid8 typed error; key stability inside a hold; a cross-thread lock-order test (lifecycle path vs implement claim path) that does not deadlock; the subprocess-count check.
**Prompt**: `/tasks/WP01-canonical-lock-key.md`
**Requirement Refs**: FR-005, C-002, NFR-002, NFR-003, C-006

### Included Subtasks

T001 Red-first: the bare-directory coordination fixture shows the transaction and `mission_write_lock`/emit resolving different lock files, and `capture_rollback_point` raising under a held primary lock after a naive rekey (plan A1, A2) (WP01)
T002 `mission_lock_key(feature_dir)` in `status/mission_write.py`, using the transaction's mid8 cascade through one shared helper (with `branch_naming`/`resolve_transaction_mid8`); a typed error for a coordination-routed Mission with no resolvable mid8; the key read from the canonical primary `meta.json` via the read-path resolver (A3, A4) (WP01)
T003 Thread-local held-key reuse: nested entries for the same Mission reuse the held key; a test with `flatten_coordination_metadata`-style meta mutation inside a hold (A4) (WP01)
T004 Route every per-Mission lock caller through the key: `mission_write_lock`, `hold_mission_write_lock`, `_holds_mission_lock`/`capture_rollback_point`, `mission_write_lock_dir`, `BookkeepingTransaction._mission_specs_dir_name`, `coord_status_lock` and every direct `feature_status_lock(root, X.name)` caller listed in A1 (emit, work_package_lifecycle, lifecycle_events, migrate_lifecycle_envelope, move-task, mark-status, agent status, decisions emit, finalize status surface, retrospective lifecycle events, review cycle, the migrations) (WP01)
T005 Disposition the two Rule 1 whole-file rewrites in files this WP owns: `migration/rebuild_state.py` (`os.replace` onto the events log) and `status/migrate_lifecycle_envelope.py` run their rewrite under the Mission lock (plan A7). Cross-thread lock-order test on the bare-directory coordination fixture (lifecycle path vs implement claim path); NFR-003 subprocess delta with a warmed `git_common_dir` cache (A12) (WP01)

### Dependencies

- None.

### Risks & Mitigations

- This WP changes which file a writer locks on legacy Missions; it never adds a second mechanism (C-002). Keep `feature_status_lock`'s signature; callers pass `mission_lock_key(...)`. Re-derive the caller list with `grep -rn "feature_status_lock(\|mission_write_lock(\|hold_mission_write_lock(" src`.

---

## Work Package WP02: Locked meta.json helper, setters and accept restamps (Priority: P1)

**Goal**: Every `mission_metadata` read-modify-write and accept's direct restamp writes run through `locked_update_meta(feature_dir, mutate, ...)`: the lock is taken, `meta.json` is re-read under it, `mutate` is applied, and the result is written atomically. The acceptance verdict guard locks through `mission_write_lock`. The three dead setters are removed.
**Independent Test**: `tests/specify_cli/test_locked_meta_writers.py`: for each setter family a deterministic two-thread overlap keeps both writes (US1); nested use under `ensure_vcs_locked`; the bounded wait fails with `STATUS_LOCK_HELD` (NFR-002); the uncontended path adds one lock acquisition and no subprocess.
**Prompt**: `/tasks/WP02-locked-meta-helper.md`
**Requirement Refs**: FR-001, FR-005, FR-020, NFR-001, NFR-002

### Included Subtasks

T006 Red-first: two overlapping `meta.json` writers (for example `record_acceptance` vs `set_target_branch`, `set_origin_ticket` vs `record_discard`) lose a write today (US1) (WP02)
T007 `locked_update_meta(feature_dir, mutate, *, repo_root=None, timeout=BOUNDED)` in `mission_metadata.py`; every setter (`record_acceptance`, `record_discard`, `flatten_coordination_metadata`, `clear_merge_metadata`, `set_target_branch`, `set_origin_ticket`, `set_documentation_state`, `set_vcs_lock`) uses it; `restore_meta_text` gets a compare-and-swap variant for WP04 (A8) (WP02)
T008 Remove `set_change_mode`, `clear_coordination_metadata` and `set_purpose_summary` with their `dead_symbol_allowlist.yaml` entries and tests (WP02)
T009 acceptance: the planning-only `record_acceptance` call and the direct restamp writes go through the helper; `locked_acceptance_verdict_guard` locks through `mission_write_lock` keyed via WP01 (FR-005) (WP02)
T010 Callers: `core/mission_creation_meta.py`, `tracker/origin.py`, `cli/commands/mission_type.py` (discard, flatten, reopen), `_coordination_doctor.py`, `lanes/implement_support.py` (`set_vcs_lock` under `ensure_vcs_locked`, unbounded wait unchanged) (WP02)

### Dependencies

- Depends on WP01.

### Risks & Mitigations

- `mutate` is a pure function that is only called, never stored, returned or assigned (gate Rule 2). Watch for nesting: `ensure_vcs_locked` already holds the same per-thread re-entrant lock. A subprocess cannot re-enter its parent's hold; document that edge case if one exists. Edit `dead_symbol_allowlist.yaml` wherever it lives (`grep -rn set_change_mode tests`).

---

## Work Package WP03: Remaining meta.json writers take the lock (Priority: P1)

**Goal**: Every other read-modify-write of `meta.json` runs through `locked_update_meta`, so gate Rule 4 (WP08) passes on the real tree with no allowlist. This covers the documentation-state writers, consolidation teardown, baseline and mission-number bake, and the migrations and upgrades.
**Independent Test**: `tests/specify_cli/test_remaining_meta_writers.py`: one overlap test per writer family (documentation state, consolidation, migrations) and a parametrized check that each writer calls the locked helper.
**Prompt**: `/tasks/WP03-remaining-meta-writers.md`
**Requirement Refs**: FR-020, NFR-002

### Included Subtasks

T011 Red-first per family: a documentation-state writer, a consolidation writer and a migration writer each lose a concurrent locked write today (C-006 part by part) (WP03)
T012 `doc_analysis/doc_state.py` (`set_audit_metadata`, `set_generators_configured`, `set_iteration_mode`, `set_divio_types_selected`, `write_documentation_state`, `ensure_documentation_state`) and their `mission_setup_plan.py` callers (WP03)
T013 Consolidation: `phase_teardown` (flatten caller and `_clear_landed_single_branch_mission_branch`), `baseline.record_baseline_merge_commit`/`_stamp_pr_merge_provenance`, `mission_number/bake.py` (the scratch-checkout write locks the scratch Mission's key) (WP03)
T014 Migrations and upgrades: `migration/mission_state.py`, `runtime_state_cutover.py`, `upgrade/feature_meta.py`, raw meta writes in `backfill_mission_type.py`, `backfill_identity.py` (including the `open(meta_path, "w")`+`json.dump` form), `backfill_topology.py`, `m_0_13_8_target_branch.py` (WP03)

### Dependencies

- Depends on WP02.

### Risks & Mitigations

- Migrations get no exemption (plan D5); they write through the helper. The merge driver (`consolidation/drivers.py`) is out of scope: it writes the temporary path git hands it, and WP08 excludes it structurally. Re-derive line numbers (lens A10).

---

## Work Package WP04: Frontmatter, finalize and matrix writers take the lock (Priority: P1)

**Goal**: map-requirements, the finalize flush, the finalize write-scope restore, the issue-matrix scaffold, the matrix helpers and the remaining frontmatter writers read and write inside one Mission-lock hold. `locked_update_frontmatter(wp_path, mutate, *, feature_dir, ...)` is the helper. The finalize restore is a compare-and-swap on every branch.
**Independent Test**: `tests/specify_cli/test_locked_frontmatter_writers.py` (US2): map-requirements overlap; finalize vs a concurrent map-requirements ref and a concurrent body note; the compare-and-swap restore for rewrite, unlink and `restore_meta_text`. `tests/specify_cli/test_matrix_writer_locks.py` (US3): the scaffold vs a recorded verdict; the two-worktree matrix writers on the bare-directory coordination fixture.
**Prompt**: `/tasks/WP04-frontmatter-and-matrix.md`
**Requirement Refs**: FR-002, FR-003, FR-004, FR-005, FR-020, NFR-001

### Included Subtasks

T015 Red-first: map-requirements overlap (FR-002); finalize erasing a concurrent frontmatter field and body note (FR-003, A9); the scaffold overwriting a verdict (FR-004); matrix helpers on the bare-directory coordination fixture, identifying key vs root as the cause (FR-005, A9) (WP04)
T016 `locked_update_frontmatter` in `frontmatter.py`, preserving the body byte for byte; map-requirements uses it (re-read refs under the lock) (WP04)
T017 Finalize flush applies its field delta to the freshly read frontmatter and body under the lock; the write-scope restore (rewrite and unlink branches) and `restore_meta_text` become compare-and-swap inside the lock and report kept files (A8); `mission_finalize_branch_contract.py` meta writes use `locked_update_meta` (WP04)
T018 `scaffold_issue_matrix` exists-check and write in one hold; `acceptance/matrix.py` and `issue_verdict.py` lock through `mission_write_lock` keyed via WP01 (WP04)
T019 Other frontmatter writers: `task_metadata_validation.py` (`validate-tasks` repair), `lanes/implement_support.py` `update_fields`, the frontmatter migrations (`backfill_ownership`, `strip_frontmatter`, `m_2_0_6_consistency_sweep`); the lane mirror in `emit.py` stays as it is (runtime-locked; WP08 recognizes it) (WP04)

### Dependencies

- Depends on WP02.

### Risks & Mitigations

- `review/prompt_metadata.write_frontmatter` is out of scope (C-007): it writes a per-invocation temporary file. Finalize keeps a long in-memory window, so apply deltas rather than writing back the model.

---

## Work Package WP05: Runtime terminal gate runs before completion; speculative rollback removed (Priority: P1)

**Goal**: On every legacy `next` path, including the stale-plan and no-plan fallbacks, the retrospective gate runs as the engine's abort-only `before_run_completed` hook before anything is appended to `run.events.jsonl` or `state.json`. A refusal reads as a typed retrospective-gate refusal. The speculative capture, the rollback and `_BufferingRuntimeEmitter` are deleted.
**Independent Test**: `tests/runtime/test_terminal_gate_before_completion.py` (US5): a refused terminal step leaves both files byte-identical to what other writers left, on `commit_advance`, the stale-plan fallback and the no-plan fallback; a concurrent append from another writer survives a refusal; the refusal decision shape on the legacy and composition paths; a terminal re-poll does not re-run the gate or the non-blocking capture.
**Prompt**: `/tasks/WP05-runtime-terminal-gate.md`
**Requirement Refs**: FR-009, FR-010, FR-011, NFR-001

### Included Subtasks

T020 Red-first: a foreign append made between the speculative capture and the rollback is cut today; the stale-plan fallback appends completion before the gate (FR-009, FR-011) (WP05)
T021 `engine.next_step` takes `before_run_completed: Callable[[], None] | None`; `_dn_advance_engine` passes the retrospective hook to both `commit_advance` and `next_step` (WP05)
T022 One bridge-level adapter wraps every hook failure (`MissionCompletionBlocked(decision)`, the policy error, a capture exception) in one typed refusal on the legacy and composition paths, caught before the generic engine-error and `_advance_failed_decision` handlers (B6) (WP05)
T023 Delete `_dn_capture_pre_speculative_state`, `_dn_rollback_buffered_run_state`, `_BufferingRuntimeEmitter` and their tests; update the five test files R4 names (FR-010) (WP05)
T024 Pin the re-poll behaviour: the gate and the non-blocking learning capture fire only on the transition into terminal (B7) (WP05)

### Dependencies

- None.

### Risks & Mitigations

- `src/runtime` must not gain a `specify_cli` import (C-001). Keep `engine._append_event` append-only. Run `tests/runtime tests/next` plus `tests/architectural/test_layer_rules.py`.

---

## Work Package WP06: next reads the pack templates; the pack Mission config matches what runs (Priority: P1)

**Goal**: The runtime resolves built-in runtime templates from `packs/built-in/missions` through `charter.activation.mission_type_profile_repository.builtin_missions_root()` with the same tier order. The four `src` `mission-runtime.yaml` copies are deleted, and the runtime→specify_cli ledger drops from 23 to 22. Every pack Mission config matches what the CLI runs today (FR-023, operator ruling): software-dev and plan runtime templates take the src content, documentation and research runtime bytes stay unchanged, and every pack `mission.yaml` becomes byte-equal to its src copy. In-flight runs keep working.
**Independent Test**: `tests/runtime/test_pack_runtime_template_parity.py`: for each type, the resolved template plans the same step sequence and dispatch route per step as the baseline recorded from today's resolver (NFR-006, SC-009); a persisted run whose recorded src path is gone still advances and answers query mode (B1). `tests/specify_cli/missions/test_pack_mission_config_parity.py`: pack `mission.yaml` byte-equal to src for all four types.
**Prompt**: `/tasks/WP06-canonical-runtime-templates.md`
**Requirement Refs**: FR-017, FR-018, FR-023, NFR-006, C-001, C-004, C-008

### Included Subtasks

T025 Red-first: record today's resolved template per type, then show that the pack software-dev/plan templates diverge (agent-profile routing widening, plan does not load), that a pack `mission.yaml` differs from src, and that query mode on a run with a vanished recorded path raises `QueryModeValidationError` (WP06)
T026 Built-in tier via `builtin_missions_root()`, `PackRootNotFound` failing closed with a named error and a test; `mission_loader/command.py` switches to the same accessor; both bare `import specify_cli` edges removed; the ledger entry removed, cap 23→22, and the `_baselines.yaml` justification updated (B8) (WP06)
T027 Reconcile the pack runtime templates per B2: software-dev and plan take the src content; documentation and research are byte-unchanged; delete the four src `mission-runtime.yaml` copies and the deprecation banner; move the tests that hard-code the src path to the pack path (B8) (WP06)
T028 `mission.yaml` parity (FR-023): pack copies made byte-equal to src (drop `task_types`, documentation `deliverables: docs/output/`), wording fixes applied to both; first confirm no pack-copy reader consumes the dropped keys and stop for an owner decision if one does; regenerate the charter-bundle goldens the compiler embeds; `spec-kitty doctrine regenerate-graph` (WP06)
T029 Query mode loads `run_dir/mission_template_frozen.yaml`; the live path is used only for drift (B1); confirm the planner drift-skip keeps an in-flight software-dev run on its frozen order (FR-017) (WP06)

### Dependencies

- Depends on WP05, WP02.

### Risks & Mitigations

- Only `mission-runtime.yaml` moves (C-008); `templates/` and the Python modules stay. After the change, run `pip install -e .` or `uv sync --frozen` before `tests/doctrine/test_doctrine_regenerate_graph_roundtrip.py` (C13). Owned test paths that do not exist under these exact names: find the real ones (`grep -rln "specify_cli/missions/.*/mission-runtime.yaml" tests`) and record them in the Activity Log.

---

## Work Package WP07: next issues a guarded analyze step between tasks and implement (Priority: P1)

**Goal**: The software-dev runtime order becomes `discovery → specify → plan → tasks → analyze → implement → review → accept`. `analyze` completes only while the analysis report is current. Otherwise it is re-issued with `error_code` `ANALYSIS_REPORT_MISSING`, `ANALYSIS_REPORT_STALE` or `ANALYSIS_CURRENCY_UNAVAILABLE`, and `guard_failures` naming each stale input. The finalized-board override and query mode apply the same check before they hand out implement.
**Independent Test**: `tests/runtime/test_analyze_step.py` (US7): missing, stale and current reports on the analyze step; the finalized-board override with hand-run specify/plan/tasks in both decide and query modes (B3); the orchestrator-api `decide_next` path; a missing callable failing closed; error-code precedence; `_state_to_action("analyze")` and `_build_prompt_or_error` resolving; `_with_guard_failure_paths` rendering stale inputs; an in-flight frozen run keeping its order.
**Prompt**: `/tasks/WP07-analyze-step.md`
**Requirement Refs**: FR-016, FR-017, C-001, C-004

### Included Subtasks

T030 Red-first: today `next` after tasks returns implement while `agent action implement` refuses on the missing analysis report; the finalized-board override skips analyze (B3) (WP07)
T031 Add the analyze step to the pack software-dev runtime template (analyze stays `in_action_sequence: false`, C6) (WP07)
T032 Inject the analysis-currency callable inside the shared `next_cmd.decide_next` wrapper and route `orchestrator_api/decision_verbs.py` through it (B4); the bridge computes the verdict into `status_facts` only for `analyze` or the board override, so the cores module stays pure (B5) (WP07)
T033 `analyze` guard in `_evaluate_software_dev_guards`, error codes in `decision.py`, the precedence rule (a prompt-resolution failure wins), and the board override in decide and query modes (B3, B5) (WP07)

### Dependencies

- Depends on WP06.

### Risks & Mitigations

- The runtime gets the callable injected; it imports nothing new from `specify_cli` (C-001). The callable wraps `analysis_report.check_analysis_report_current`.

---

## Work Package WP08: Mission write discipline gate: Rules 1–4 close the writer class (Priority: P1)

**Goal**: The gate closes the writer class by construction with an empty allowlist. Rule 1 also catches whole-file rewrites and replaces of status and run logs, and scans `src/runtime`. Rule 2 treats every non-call reference to the callable parameter as an escape. Rule 3 accepts only `mission_lock_key(...)` for keys and only `mission_write_lock_dir(...)` or a parameter for paths. New Rule 4 keeps `meta.json`, `tasks/WP*.md` and `tasks.md` writes inside a lock region or a registered locked helper.
**Independent Test**: `tests/architectural/test_mission_write_discipline.py`: for every new or extended rule, a synthetic offender, a near-miss negative and a self-mutation proof of a real module (NFR-004); the rule passes on the real tree.
**Prompt**: `/tasks/WP08-gate-rules.md`
**Requirement Refs**: FR-006, FR-007, FR-008, FR-019, NFR-004, NFR-005

### Included Subtasks

T034 Rule 1 (FR-008, A7): track target names assigned from the log/meta/state filenames through assignments and `/` joins; sinks are truncate, `write_text`, `write_bytes`, `open` in w/x/a/r+ modes, `os.replace`/`shutil.move` onto a target, and `atomic_write`; scan `src/runtime` with the run-log and run-state names; fix the consolidation bookkeeping projection (rewrite under the status lock), the lane auto-rebase create-if-missing (exclusive create), and confirm the WP01 dispositions of `rebuild_state.py` and `migrate_lifecycle_envelope.py` pass the rule; the merge driver is excluded by a stated structural rule (WP08)
T035 Rule 2 (FR-006, A11): any non-call-func reference to the parameter, including passing it as an argument or keyword or capturing it in a nested def or lambda, is an escape; an unresolvable callee fails closed (WP08)
T036 Rule 3 (FR-007, A6): keys only as `mission_lock_key(...)`; paths as `mission_write_lock_dir(...)` or a function parameter; a bare `.name` is refused (WP08)
T037 Rule 4 (FR-019, A5): regions are lexical lock `with`, `ExitStack.enter_context(<lock cm>)`, `__enter__`..`__exit__`, a `with` on a name assigned from a lock cm, and `locked_acceptance_verdict_guard`; a sink in function F is accepted when F is a registered locked helper or every same-module call site of F is in a region; unresolvable cross-module callers fail closed; no name-based exemptions; the merge driver exclusion applies (WP08)

### Dependencies

- Depends on WP03, WP04, WP07.

### Risks & Mitigations

- Fix real-tree hits in the owning code, not by allowlisting. If a hit sits in a file another WP owned, fix it here and note it in the Activity Log.

---

## Work Package WP09: Built-in software-dev prompts, steps and contracts describe what the CLI does (Priority: P1)

**Goal**: Every shipped software-dev step prompt, `step.yaml`, step contract, `expected-artifacts.yaml`, README and governance profile describes what the CLI actually does. The tasks and tasks-finalize prompts name `/spec-kitty.analyze` as required before implement, with its staleness rule. The scripted prompt walk (SC-008) finds 0 refused instructions and 0 non-existent references. The provenance ratchet counts go down.
**Independent Test**: `tests/doctrine/test_software_dev_prompt_walk.py` (SC-008, C12): command paths and each `--option` resolve against Click; rendered step-contract bootstrap commands parse; every "next advances to X" claim matches the runtime order; consumer paths resolve against a `spec-kitty init` fixture with an explicit placeholder list; covers the CLI-driven implement, review, accept and tasks-finalize prompts.
**Prompt**: `/tasks/WP09-pack-software-dev-cleanup.md`
**Requirement Refs**: FR-015, FR-022, C-003

### Included Subtasks

T038 Red-first: the prompt walk gate fails on today's files (refused `charter context --profile/--tool`, missing `--mission`, false "next advances" claims, nonexistent paths) (WP09)
T039 Step contracts: drop `--profile`/`--tool` bootstrap inputs in every built-in contract (C1, the one Locality exception); fix the C2 items; update `test_shipped_contracts.py` (WP09)
T040 Tasks family prompts (tasks, tasks-outline, tasks-packages, tasks-finalize, `tasks/guidelines.md`): analyze required with its staleness rule (FR-015), dedupe, false "next advances" claims, the template reference (C6), the dependency command, the provenance tokens, "feature" wording, `/ad-hoc-profile-load` (WP09)
T041 Other prompts (analyze, accept, implement, review, plan, specify): the R7 items plus C3 (`--mission` boilerplate), C4, C5, C10 (recovery recipe outside the checkout) (WP09)
T042 Pack files: `software-dev/README.md`, `missions/README.md`, `expected-artifacts.yaml` (retired tasks_* ids, analysis report on implement), `governance-profile.yaml`, the `step.yaml` chain (tasks-finalize depends on tasks-packages, analyze depends on tasks) (WP09)
T043 Ratchet baseline lowered by hand per entry (diff only goes down, C8); pinning tests and snapshots updated (C7); `spec-kitty doctrine regenerate-graph`; reinstall, then the roundtrip test (WP09)

### Dependencies

- Depends on WP07.

### Risks & Mitigations

- Run the specific gates: `tests/architectural/test_builtin_pack_provenance_ratchet.py`, `tests/doctrine/test_builtin_cli_command_references.py`, `tests/doctrine/test_doctrine_regenerate_graph_roundtrip.py` and the pinning tests listed in R7/C7. Owned paths that do not exist under these names: find the real ones and record them in the Activity Log.

---

## Work Package WP10: Operator-facing text and generated commits say mission (Priority: P1)

**Goal**: The five planning commit builders and the operator-facing CLI errors say "mission". The finalize drift check accepts both the new and the legacy subjects. An AST scan keeps "for feature" out of operator text. commitlint covers every planning subject for both words.
**Independent Test**: `tests/specify_cli/test_no_for_feature_operator_text.py` (FR-014, C9): scans every non-docstring string constant under `src/specify_cli` for "for feature" or a leading "Feature:"; a synthetic offender per construction form (f-string, concatenation, variable).
**Prompt**: `/tasks/WP10-mission-wording.md`
**Requirement Refs**: FR-012, FR-013, FR-014

### Included Subtasks

T044 Red-first: the FR-014 scan fails on today's tree; the drift check on a legacy-subject Mission (WP10)
T045 Commit builders: finalize planning pin, `mission_setup_plan` (spec/plan setup, gap analysis, generator config), `core/mission_creation_commit`; the drift check accepts the old and new subjects (FR-013) (WP10)
T046 CLI errors from R8 and C9; `FEATURE_CONTEXT_UNRESOLVED` stays (machine contract) and is filed as a follow-up (WP10)
T047 commitlint: the planning-subject rule covers the scaffold, gap-analysis, generator-config and origin-ticket-binding subjects for both words; update tests and goldens that assert the old text (R8, C7) (WP10)

### Dependencies

- Depends on WP03, WP04.

### Risks & Mitigations

- Golden and fixture files that assert the old subjects (R8, C7 wording pins) change in this WP. Find them with `grep -rn "for feature" tests`.

---

## Work Package WP11: The glossary defines topic branch, Mission and Mission Run consistently (Priority: P1)

**Goal**: topic branch is added, Mission and Mission Run are rewritten, and feature branch becomes an alias of topic branch. All of this is consistent across `docs/context`, the YAML seed, the built-in glossary pack and the regenerated contextive glossaries. The R9 and C11 inconsistencies are fixed.
**Independent Test**: The glossary parity gates (`test_glossary_pack_parity.py`, `test_glossary_authority_parity.py`, `tests/glossary/test_seed_validation.py`) and `tests/architectural/test_no_legacy_terminology.py`; the regenerate-graph roundtrip.
**Prompt**: `/tasks/WP11-glossary.md`
**Requirement Refs**: FR-021

### Included Subtasks

T048 Entries: topic branch (new), Mission, Mission Run, feature branch → alias of topic branch, across the four surfaces (WP11)
T049 Fix the R9 and C11 inconsistencies (WP11)
T050 Regenerate the contextive glossaries (`scripts/generate_contextive_glossaries.py`) and the graph (`spec-kitty doctrine regenerate-graph`); the `test_no_legacy_terminology` baseline only shrinks (WP11)

### Dependencies

- Depends on WP09.

### Risks & Mitigations

- If a `docs/context` file named here does not exist, find the real one. This WP has no code-behaviour change, so red-first does not apply beyond the parity gates.

---

## Work Package WP12: CHANGELOG and architecture docs (Priority: P1)

**Goal**: `[Unreleased]` CHANGELOG entries describe the user-visible changes: the lock key, the locked writers, the runtime gate, the analyze step, the pack templates and config parity, the prompt cleanup and the wording. The "Mission write lock and rollback" section in `docs/architecture/status-model.md` describes the canonical key, the locked helpers and Rule 4.
**Independent Test**: `tests/docs/test_changelog_style.py`, `tests/docs/test_docs_index_freshness.py`, `tests/architectural/test_no_legacy_terminology.py`.
**Prompt**: `/tasks/WP12-changelog-and-docs.md`
**Requirement Refs**: C-005, C-007

### Included Subtasks

T051 CHANGELOG `[Unreleased]` entries in the repository's changelog style (WP12)
T052 status-model.md: canonical lock key, locked helpers, Rule 4; refresh the docs retrieval index if it is required (WP12)

### Dependencies

- Depends on WP01, WP02, WP03, WP04, WP05, WP06, WP07, WP08, WP09, WP10, WP11.

### Risks & Mitigations

- Describe behaviour, not WP ids or requirement ids.

---
