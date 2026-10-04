---
work_package_id: "WP03"
subtasks:
  - "T011"
  - "T012"
  - "T013"
  - "T014"
  - "T015"
  - "T016"
title: "Planning-artifact commit split"
task_type: "implement"
phase: "Phase 1 - Seam extraction"
execution_mode: "code_change"
owned_files:
  - "src/specify_cli/cli/commands/implement.py"
  - "src/specify_cli/cli/commands/implement_planning_commit.py"
  - "src/specify_cli/coordination/planning_commit.py"
  - "tests/specify_cli/coordination/test_planning_commit.py"
  - "tests/specify_cli/cli/commands/test_implement_*.py"
  - "tests/specify_cli/cli/commands/test_precondition_ref_unification.py"
  - "tests/specify_cli/cli/commands/test_meta_bypass_diagnosability.py"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
  - "tests/specify_cli/coordination/test_flat_legacy_none_seam_success_arms.py"
  - "tests/specify_cli/coordination/test_partition_authority_characterization.py"
  - "tests/lanes/test_issue_2993_lane_planning_ancestry.py"
  - "tests/integration/test_wp_integrity_*.py"
  - "tests/architectural/test_wp_integrity_partition_call_shape.py"
  - "tests/architectural/test_exemption_registry_ratchet.py"
  - "tests/architectural/test_trio_seam_only.py"
  - "tests/architectural/test_no_write_side_rederivation.py"
  - "tests/specify_cli/test_mid8_contract_sensitive_routing.py"
  - "tests/specify_cli/test_meta_fail_closed_full_census_contract.py"
  - "tests/specify_cli/status/test_cutover_byte_stability.py"
  - "tests/contract/test_terminology_guards.py"
  - "tests/contract/test_feature_alias_scope.py"
authoritative_surface: "src/specify_cli/coordination/"
create_intent:
  - "src/specify_cli/cli/commands/implement_planning_commit.py"
  - "src/specify_cli/coordination/planning_commit.py"
  - "tests/specify_cli/coordination/test_planning_commit.py"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
requirement_refs: ["FR-004", "FR-012", "NFR-005"]
dependencies: ["WP02"]
agent_profile: "python-pedro"
role: "implementer"
agent: "claude"
model: "sonnet"
history:
  - at: "2026-10-04T20:10:00Z"
    actor: "system"
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP03 – Planning-artifact commit split

## ⚡ Do This First: Load Agent Profile

Load the agent profile named in the frontmatter through the canonical path, and work according to
its guidance before you read the rest of this prompt:

```bash
spec-kitty agent profile show python-pedro
spec-kitty charter context --action implement --json
```

- **Profile**: `python-pedro`
- **Role**: `implementer`
- **Agent/tool**: `claude`

State, in your first activity-log entry, which directives and tactics of the profile you applied.

---

## ⚠️ IMPORTANT: Review Feedback

Before you start, read the `review_ref` in the event log (`spec-kitty agent tasks status --mission implement-degod-01M44488`)
and the Activity Log below. Treat any review feedback as your TODO list.

---

## Markdown Formatting

Wrap HTML/XML tags in backticks. Use language identifiers in code blocks.

---

## Binding rules for this mission (read once, apply throughout)

- **Behaviour preserved (C-001).** Refusal texts, error codes, exit codes, console and `--json`
  output (including print order), commits and state files stay byte-identical.
- **Move, then adjust (C-002 / NFR-005).**
  - Commit 1 of each extraction is a verbatim move: `git diff --color-moved=zebra` must show only
    moved blocks plus the minimal import lines.
  - Commit 2 adjusts callers and imports, deletes the moved names' re-exports from `implement.py`
    (research R-3: keep a re-export only where *production* imports it from there), and applies
    typing-only fixes.
  - Never edit logic inside the move commit.
- **Existing packages only (C-004).** Lower packages (`lanes`, `workspace`, `coordination`,
  `status`, `core`) never import `specify_cli.cli`, `typer` or the console. They return typed
  results or raise typed errors; only the command package prints.
- **Gates follow the code (FR-012).**
  - Every census or scan list that names `implement.py` gains the module the code moved to; pins
    are re-pointed and never loosened.
  - Prove each widened scan by planting a violation in the new module, running the gate red, then
    removing the plant (never committed).
  - Record the commands and the red output in your activity log.
  - Checklist: research/code-grounding.md §1.5 and research/test-remediation.md §5 ("Gate/census edits").
- **Tests (charter SO 4, brief).**
  - Never edit an assertion to make a move pass.
  - Re-point imports and patches to the module that now *looks the name up*.
  - Add seam unit tests before trimming any end-to-end test, and keep at least one smoke test per
    behaviour family.
  - The characterization suite (`test_implement_characterization.py`) must stay green **unedited**.
    Only its dispatch-map fixture may change, when a collaborator's dispatch site moves.
- **Quality (NFR-001/002/004).**
  - Complexity ≤ 15.
  - `mypy --strict` clean on new and receiving modules; nothing added to the mypy quarantine.
  - `ruff check` + `ruff format --check --force-exclude` clean on changed files.
  - No new `noqa` or `type: ignore` without an inline rationale.
- **Commits.** Every commit message ends with
  `Co-Authored-By: Stijn Dejongh <stijn.dejongh@sddevelopment.be>`. No AI model identifier anywhere
  (C-008).
- **Tracer files.** Append dated 1–3 sentence entries for friction, approach changes or design
  decisions to `kitty-specs/implement-degod-01M44488/traces/` (via the orchestrator, if your
  worktree cannot write the mission dir).
- **No heavy suites.** Never run `make test-full` or a whole `tests/architectural/` sweep. Run the
  targeted files and the specific gate files (quickstart.md §2–§3).


## Objectives & Success Criteria

Move the planning-artifact commit block (implement.py ~L400–1292 plus `_planning_commit_branch`
~L1906; about 890 LOC, 39% of the file) out of `implement.py`. Behaviour must not change.
- **Pure decisions → `src/specify_cli/coordination/planning_commit.py`** (new sibling in the existing
  `coordination` package; no `cli`, `typer` or console import):
  - `_partition_files_for_commit`;
  - `_guard_planning_commit_partition`;
  - `_read_json_at_ref`, `_meta_json_demotion_refusal`, `_meta_json_repo_relative_path`, the
    `_DEMOTION_*` messages and `_META_JSON_FILENAME`;
  - the bookkeeping identifier cascade: `_load_primary_anchored_mission_meta`,
    `_load_fallback_mission_meta`, `_extract_mission_identifiers_from_meta`,
    `_compute_effective_bookkeeping_ids`, `_BookkeepingTransactionIdentifiers`,
    `_resolve_bookkeeping_transaction_identifiers`;
  - `_feature_dir_file_paths` and `_planning_artifact_source_dir`.
- **Adapter → `src/specify_cli/cli/commands/implement_planning_commit.py`**:
  - `_ensure_planning_artifacts_committed_git`, `_commit_planning_artifacts_transaction`,
    `_run_planning_artifact_commit`;
  - `_print_uncommitted_planning_artifacts`, `_print_planning_artifact_commit_instructions`,
    `_print_structural_planning_refusal`;
  - `_refuse_if_meta_json_demotion`, `_refuse_on_unreadable_planning_status`;
  - `_planning_commit_branch` and the `_RED_ERROR_PREFIX` it needs.
- Public names in the seam drop the leading underscore **only in the adjust commit**
  (contracts/seam-decisions.md lists the target names). The C-006 five-tuple keeps its arity and
  order.
- `implement.py` calls the adapter. Every test that imported these names from `implement` imports
  from the new home.
- The characterization suite stays green unedited. The coord-partition smokes and
  `tests/e2e/test_cli_smoke.py::test_full_workflow_sequence` (#3371 lesson) stay green.

## Context & Constraints

- `coordination/` must not import `specify_cli.cli`. This is guarded by
  `tests/specify_cli/coordination/test_commit_router_layering.py`; find it with
  `grep -rn "commit_router_layering" tests`, and run it.
- `_guard_planning_commit_partition` raises `coordination.commit_router.PrimaryKindReachedCoordStagingError`.
  Keep that type and the message texts.
- `_meta_json_demotion_refusal` returns `str | None`. Keep that verdict shape; the adapter prints
  `\n{_RED_ERROR_PREFIX}{refusal}` and exits 1, as today.
- `_load_primary_anchored_mission_meta` and the identity helpers lazily import `core.paths` and
  `lanes.branch_naming`. Keep the lazy imports, which the cold-import boundary relies on.
- The placement/`None` logic (`placement_ref`, `_placement_coord_filter`, `_resolve_placement_ref`)
  moves **unchanged**. WP04 owns changing it. Do not touch the C-004 arms here.
- `implement_cores.py` stays as it is. Its re-export shim block in `implement.py` (~L69–91) loses
  every name `implement.py` no longer uses itself (research R-3). Tests that imported those names
  via `implement` re-point to `implement_cores`.

## Subtasks & Detailed Guidance

### Subtask T011 – Create `coordination/planning_commit.py` (verbatim move commit)

- Move the pure decisions listed above, byte-for-byte, with their docstrings and comments.
- Add only the imports they need.
- `implement.py` (or, after T012, the adapter) imports them back so the tree still imports.

### Subtask T012 – Create `cli/commands/implement_planning_commit.py` (verbatim move commit)

- Move the adapter functions listed above byte-for-byte.
- `implement.py` keeps one call site, in `implement()`'s validate block:
  `implement_planning_commit._ensure_planning_artifacts_committed_git(...)` plus
  `_planning_commit_branch(...)`.
- These two commits may be one move commit if that keeps `--color-moved` clean. Never mix the move
  with the adjust.

### Subtask T013 – Adjust commit

- Rename the seam's public functions to the contract names. Update the adapter and tests.
- Delete the moved names (and the now-unused `implement_cores` shim names) from `implement.py`.
- Type everything to `mypy --strict` on both new modules.
- Run `ruff check`, `ruff format --check --force-exclude` and C901 ≤ 15 on both.

### Subtask T014 – Re-point test imports and patches

- About 8 files import `_ensure_planning_artifacts_committed_git` from implement, and several more
  import the private planning helpers. Use `grep -rln` over `tests` for each moved name.
- Re-point every import to the new home. Re-point string and object patches to the module that
  looks the name up:
  - a patch on `_ensure_planning_artifacts_committed_git` used by `implement()` becomes a patch on
    `implement_planning_commit._ensure_planning_artifacts_committed_git`, **if `implement.py` calls
    it as an attribute of that module**;
  - otherwise it stays on the name `implement.py` binds. Choose one call style and keep the
    liveness gate green.
- Prefer the attribute-call style (`implement_planning_commit.<fn>(...)`). That way one patch on
  the sibling module intercepts. If you choose it, record the decision in the activity log.
- Update the dispatch map.
- Never edit an assertion.

### Subtask T015 – Gates follow the code (with planted-violation proofs)

- `tests/architectural/test_wp_integrity_partition_call_shape.py`: `_IMPLEMENT` (~L47) re-points to
  `implement_planning_commit.py`. Keep the floor of at least 3 `_run_planning_artifact_commit` calls
  (~L157); there are still 5 here.
- `tests/architectural/test_exemption_registry_ratchet.py` `CHURN_SURFACE_MODULES` (~L79): add both
  new modules.
- `tests/architectural/test_trio_seam_only.py` `_TRIO_FILES` (~L104): add both new modules.
  `_CORE_FILES` (~L119) gains `coordination/planning_commit.py` **only if** it is I/O-free. It is
  not (git subprocess, file reads), so leave it out and record why.
- `tests/architectural/test_no_write_side_rederivation.py` `_WRITE_DIR_CONSUMER_MODULES` (~L126,
  not the frozen `_PRE_` tuple): add both.
- `test_mid8_contract_sensitive_routing.py:59`, `test_meta_fail_closed_full_census_contract.py:86`,
  `test_cutover_byte_stability.py:63`, `tests/contract/test_terminology_guards.py:53` and
  `tests/contract/test_feature_alias_scope.py:60`: add the new module(s) carrying the moved code.
- `test_safe_commit_import_boundary.py`, `test_git_matrix_paths_resolve.py` (it checks the shipped
  git-operations-matrix `Source File` cells) and
  `tool_artifact_enrolment/registry/_is_self_write_only_diff.md`: re-point any path that named
  `implement.py` for moved code.
- For **each** widened list, plant a violation in the new module, run the gate red, then remove the
  plant. Log it.

### Subtask T016 – Seam unit tests and end-to-end smoke

- `tests/specify_cli/coordination/test_planning_commit.py` (fast unit, no git where possible):
  - partition (PRIMARY vs residue, `meta.json` defaults to PRIMARY);
  - partition guard (both directions raise; self-bookkeeping exempt);
  - demotion predicate (no baseline allows; HEAD has the branch and working drops it refuses with
    the exact text; corrupt HEAD or working copy refuses with the corrupt text). This one needs a
    tiny git repo;
  - identifier cascade (primary meta first, fallback second, `legacy-<slug>` id);
  - candidate enumeration (`.worktrees/` guard raises `SafeCommitPathPolicyError`).
- Run `uv run --frozen pytest -p no:randomly tests/e2e/test_cli_smoke.py::test_full_workflow_sequence`.

## Definition of Done

- [ ] Move commit(s) pure; adjust commit separate.
- [ ] `coordination/planning_commit.py` imports nothing from `specify_cli.cli`; the layering test is green.
- [ ] `implement.py` lost about 890 LOC; the new modules are each ≤ 800 LOC.
- [ ] All re-pointed tests, gates and smokes green; the characterization suite unedited.
- [ ] Counter before and after recorded; `mypy --strict` clean on both new modules.

## Risks & Mitigations

- **Silent dead patches.** The liveness gate (WP01) must stay green. If it reports a dead patch,
  re-point it; never allow-list it.
- **The C-006 tuple**: `test_implement_bookkeeping_identifiers.py` pins it. Keep it green.

## Review Guidance

- `--color-moved` on the move commit.
- Confirm no `cli` import in `coordination/`.
- Check each widened gate's planted-violation log.
- Run the e2e smoke.

## Branch Strategy

- **Strategy**: lanes topology. Execution worktrees are allocated per computed lane from `lanes.json`.
  This mission's WPs form one dependency chain, so they run sequentially in one lane.
- **Planning base branch**: `issue-5635-implement-degod`
- **Merge target branch**: `issue-5635-implement-degod`. `spec-kitty consolidate` lands the lanes
  there, locally only. The branch then reaches `main` through a PR that the operator merges.
- Prepare the workspace only with `spec-kitty agent action implement WP03 --agent claude --mission implement-degod-01M44488`
  (or `spec-kitty implement WP03 --mission implement-degod-01M44488`), and work in the path it prints.

## Validation (run and record in the activity log: command + pass/fail counts)

1. `make test-fast`
2. The implement-direct regression subset (quickstart.md §2), plus every new or touched test file.
3. The owning subsystem directories of every source module you touched (CLAUDE.md blast radius),
   targeted files only.
4. The specific gate files you widened or re-pointed (quickstart.md §3).
5. `uv run --frozen ruff check <changed files>`, `uv run --frozen ruff format --check --force-exclude <changed files>`,
   `uv run --frozen mypy --strict <new/receiving src modules>`, and the C901 check.
6. The counter: `uv run --frozen python kitty-specs/implement-degod-01M44488/tools/count_patch_sites.py`
   (before/after numbers in the activity log).
7. Classify every red against the base commit (CLAUDE.md baseline-red gotcha).
   `test_commit_recipes.py::test_no_unallowed_git_commit_recipe_strings_in_src` is a known
   pre-existing red (#5699); do not chase it.

## Activity Log

- 2026-10-04T20:10:00Z – system – Prompt created via /spec-kitty.tasks.

