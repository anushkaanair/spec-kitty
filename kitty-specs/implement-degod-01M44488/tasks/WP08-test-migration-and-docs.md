---
work_package_id: "WP08"
subtasks:
  - "T037"
  - "T038"
  - "T039"
  - "T040"
title: "Test migration, docs and closing measurements"
task_type: "implement"
phase: "Phase 4 - Tests and docs"
execution_mode: "code_change"
owned_files:
  - "tests/agent/test_implement_command.py"
  - "tests/integration/test_status_emit_on_alloc_failure.py"
  - "tests/cli/test_implement_bulk_edit_planning.py"
  - "tests/specify_cli/cli/commands/test_implement_vcs_lock_claim.py"
  - "tests/specify_cli/cli/commands/test_implement_runtime_frontmatter_claim.py"
  - "tests/specify_cli/test_specify_topology_flag.py"
  - "tests/specify_cli/lanes/test_lane_base_honoring.py"
  - "tests/cli/commands/test_implement_base_flag.py"
  - "tests/specify_cli/cli/commands/test_implement_*.py"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
  - "docs/architecture/wp-runtime-state-eviction.md"
  - "docs/development/reference/read-side-seam-classification.md"
  - "docs/architecture/04_implementation_mapping/README.md"
  - "docs/**/git-operations-matrix.md"
  - "docs/changelog/CHANGELOG.md"
authoritative_surface: "tests/agent/"
create_intent:
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
requirement_refs: ["FR-011", "FR-016", "SC-002", "SC-005", "NFR-003", "NFR-004", "NFR-006"]
dependencies: ["WP07"]
agent_profile: "python-pedro"
role: "implementer"
agent: "claude"
model: "sonnet"
history:
  - at: "2026-10-04T20:10:00Z"
    actor: "system"
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP08 – Test migration, docs and closing measurements

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

- **SC-002**: `tools/count_patch_sites.py` reports **≤ 45** family patch sites (baseline 119).
  - Get there by *rewriting* coupling: tests call seam decisions directly, use real fixtures, or
    patch the seam module that owns the name.
  - Re-pointing a patch to an `implement_*` sibling does not count as a reduction.
- **FR-011**: the orchestration tests that string-patch 5–9 collaborators (`TestImplementCommand`,
  `test_implement_bulk_edit_planning`, `test_status_emit_on_alloc_failure`, and the shared helpers
  in `test_implement_vcs_lock_claim` / `test_implement_runtime_frontmatter_claim`) move onto
  phase-function or seam tests. One CLI smoke per behaviour family is kept (test-remediation §5,
  "E2E smokes to keep").
- **SC-005**: a table in the activity log maps each phase (context, claim preflight + dependency
  gate, planning commit, bulk-edit + operational context, workspace/lane selection, allocate,
  record claim, present) to at least one seam or phase unit test that patches nothing in the
  implement family.
- **NFR-003**: the regression subset (quickstart.md §2, plus every new seam and phase test file)
  runs in ≤ 30 s with `-n auto --dist loadfile`. Record the time.
- **FR-016 docs**:
  - re-point `docs/architecture/wp-runtime-state-eviction.md` (~L37, L80);
  - re-point `docs/development/reference/read-side-seam-classification.md` (~L603–606);
  - re-point the shipped git-operations-matrix `Source File` cells that name moved code
    (`test_git_matrix_paths_resolve.py` must stay green);
  - update `docs/architecture/04_implementation_mapping/README.md` (~L216) to list the new sibling
    modules;
  - update each touched page's `updated:` frontmatter date.
- **CHANGELOG**: add an `[Unreleased]` entry to `docs/changelog/CHANGELOG.md` (the root file is a
  symlink).
  - Bold impact-first lead naming #5635 and #5232. It is a maintainer-facing refactor, and operator
    behaviour is unchanged.
  - Say that #5232's meta-derived placement fallback is replaced by the seam-owned typed placement,
    and that #5673 is now a one-function change.
  - Follow the file's existing style.

## Context & Constraints

- **Never edit an assertion to make a migration pass.** If a test's assertion cannot be satisfied
  through the seams, the seam is wrong. Stop and report.
- **Add the seam or phase test before deleting the e2e/orchestration test it replaces.** Each
  retired test names its replacement in the activity log.
- **Keep these smokes** (test-remediation §5):
  - lane allocation: `tests/lanes/test_lane_allocation_integrity_e2e.py`;
  - coord partition: `tests/integration/test_wp_integrity_p0_repro.py`,
    `test_wp_integrity_cross_partition_scan.py`;
  - crash recovery: `test_wp_integrity_crash_recovery.py`;
  - single_branch refusals: the CLI cases in `test_single_branch_implement_refusals.py`;
  - base ref: the integration class in `tests/cli/commands/test_implement_base_flag.py`;
  - planning-lane ancestry: `test_issue_2993…`;
  - protected-target coord commit: `tests/git/test_guard_capability_regression.py`;
  - JSON and programmatic call: `test_implement_programmatic_call.py`,
    `test_implement_json_safe_output.py`.
- Docs: run `scripts/docs/check_docs_freshness.py --ci` (errors=0) and
  `pytest tests/architectural/test_no_legacy_terminology.py`. If you add a docs page, regenerate
  the docs retrieval index (`scripts/docs/docs_index.py --write`).

## Subtasks & Detailed Guidance

### Subtask T037 – Migrate `tests/agent/test_implement_command.py` (54 string targets)
- `TestDetectFeatureContext` / `TestFindWpFile`: if WP02 has not already absorbed them, move them
  into the seam tests.
- `TestImplementCommand` (7 tests). For each, identify the behaviour it owns (JSON payload shape;
  dependency gate before allocation; protected-target coord commit allowed; execution_mode
  threading; planning-lane allowance). Prove that behaviour through a phase-function test with
  real values, or a real-git fixture. Then delete the MagicMock-graph version.
- Keep `test_implement_json_error_output_is_clean` (it is the lanes.json guard).

### Subtask T038 – Migrate the remaining class-A/B files
- `test_status_emit_on_alloc_failure.py` (F-50: no blocked emission on allocation failure): drive
  `allocate` failure through the dispatch map and assert the event log has no `blocked` event,
  using real `status.events.jsonl` reads.
- `test_implement_bulk_edit_planning.py`: assert on the bulk-edit phase function's verdict and
  console output, without 6 patches.
- `test_implement_vcs_lock_claim.py` / `test_implement_runtime_frontmatter_claim.py`: the shared
  5-string-patch helper becomes a real fixture plus the dispatch map for the allocator only.
- `test_specify_topology_flag.py` (2): re-point or rewrite.
- `test_lane_base_honoring.py` (remaining patches) and `test_implement_base_flag.py`: same approach.
- Re-measure with the counter after each file.

### Subtask T039 – Docs and CHANGELOG
As listed in the objectives. Keep each doc's Divio type, and update `updated:` dates.

### Subtask T040 – Closing measurements
Record in the activity log:
- the counter, before WP08 and after;
- the SC-005 table;
- the NFR-003 timing;
- the full targeted run:
  - `make test-fast`;
  - the regression subset;
  - the owning dirs `tests/lanes/`, `tests/specify_cli/workspace/`,
    `tests/specify_cli/coordination/`, `tests/status/` and `tests/specify_cli/core/`, run as
    targeted dirs, not as an architectural sweep;
  - the gate files (quickstart.md §3);
  - `tests/e2e/test_cli_smoke.py::test_full_workflow_sequence`.

## Definition of Done

- [ ] Counter ≤ 45 (string + object), with console and private-import numbers reported.
- [ ] SC-005 table complete; NFR-003 met.
- [ ] Docs re-pointed; CHANGELOG entry; the docs freshness check and the terminology guard green.
- [ ] No assertion edited; every retirement names its replacement.

## Review Guidance

- Sample three migrated tests and confirm the replacement asserts the same behaviour, not a weaker one.
- Re-run the counter yourself.

## Branch Strategy

- **Strategy**: lanes topology. Execution worktrees are allocated per computed lane from `lanes.json`.
  This mission's WPs form one dependency chain, so they run sequentially in one lane.
- **Planning base branch**: `issue-5635-implement-degod`
- **Merge target branch**: `issue-5635-implement-degod`. `spec-kitty consolidate` lands the lanes
  there, locally only. The branch then reaches `main` through a PR that the operator merges.
- Prepare the workspace only with `spec-kitty agent action implement WP08 --agent claude --mission implement-degod-01M44488`
  (or `spec-kitty implement WP08 --mission implement-degod-01M44488`), and work in the path it prints.

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

