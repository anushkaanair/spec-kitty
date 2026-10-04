---
work_package_id: "WP02"
subtasks:
  - "T006"
  - "T007"
  - "T008"
  - "T009"
  - "T010"
title: "Context and dependency gate into their seams"
task_type: "implement"
phase: "Phase 1 - Seam extraction"
execution_mode: "code_change"
owned_files:
  - "src/specify_cli/cli/commands/implement.py"
  - "src/specify_cli/workspace/context.py"
  - "src/specify_cli/core/dependency_graph.py"
  - "tests/specify_cli/core/test_claim_preconditions.py"
  - "tests/specify_cli/workspace/test_context_implement_reads.py"
  - "tests/specify_cli/core/test_dependency_graph_canceled.py"
  - "tests/specify_cli/acceptance/test_trio_read_seam_migration.py"
  - "tests/specify_cli/regression/test_issue_1615_1616_1617_1618.py"
  - "tests/architectural/dead_symbol_allowlist.yaml"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
authoritative_surface: "src/specify_cli/core/"
create_intent:
  - "tests/specify_cli/core/test_claim_preconditions.py"
  - "tests/specify_cli/workspace/test_context_implement_reads.py"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
requirement_refs: ["FR-003", "FR-006", "FR-012", "NFR-002"]
dependencies: ["WP01"]
agent_profile: "python-pedro"
role: "implementer"
agent: "claude"
model: "sonnet"
history:
  - at: "2026-10-04T20:10:00Z"
    actor: "system"
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP02 – Context and dependency gate into their seams

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

- **FR-006.** Move the context reads that implement owns today into
  `src/specify_cli/workspace/context.py`:
  - `find_wp_file` (implement.py ~L243);
  - `_resolve_lanes_dir` (~L377), which becomes the public `resolve_lanes_dir`;
  - `resolve_feature_target_branch` (~L279), which becomes `resolve_mission_target_branch`. The
    terminology canon forbids a new `feature` name; keep the old name nowhere.
- **FR-003.** Move the claim-precondition decision from `_ensure_wp_claim_preconditions` (~L1503)
  into `src/specify_cli/core/dependency_graph.py` as a pure
  `ensure_wp_claim_preconditions(wp_id, declared_deps, work_packages)`.
  - It takes the reduced snapshot's `work_packages` mapping.
  - It raises exactly today's `WorkPackageStartRejected` / `ValueError` with today's texts.
  - The event read and reduce (`read_events` + `reduce`) stay in the implement caller.
- Seam unit tests exercise both seams without the CLI and without patching implement (SC-005, for
  the context and dependency-gate phases).
- The characterization suite stays green **unedited** (the dispatch map may change).

## Context & Constraints

- Contract: `kitty-specs/implement-degod-01M44488/contracts/seam-decisions.md` (sections
  `core/dependency_graph.py`, `workspace/context.py`).
- `core/dependency_graph.py` already imports the `specify_cli.status` facade at module scope (~L15–18).
  `tests/architectural/test_cold_import_status_boundary.py` requires `task_utils.support` and
  `core.owned_mission` not to load status/workspace on cold import. Verify that your import changes
  keep it green.
- `tests/architectural/test_owned_checkout_single_authority.py` pins `resolve_workspace_for_wp` in
  `workspace/context.py`. Adding functions there is fine.
- **Lane-map derivation (pin, do not dedupe).** Today the lane map is
  `{wp: state.get("lane", Lane.GENESIS)}`. `status/dependency_verdict.wp_lanes_from_snapshot` uses
  `str(state.get("lane") or GENESIS.value)`. Keep implement's form byte-for-byte, and add a unit test
  pinning the present-but-falsy case.
- `find_wp_file` is in `implement.__all__` and has a `category_b_grandfathered_legacy` row in
  `tests/architectural/dead_symbol_allowlist.yaml` (~L652–657). Re-key that row to the new module,
  or delete it if the moved symbol now has a src caller. Then run `test_no_dead_symbols.py`.
- **Production importers.** Find every production caller of the moved names
  (`grep -rn "find_wp_file\|resolve_feature_target_branch\|_resolve_lanes_dir" src`) and re-point
  each one. Production importers of `implement.find_wp_file`, if any, switch to the new home.

## Subtasks & Detailed Guidance

### Subtask T006 – Move the context reads (verbatim move commit)

- Cut `find_wp_file`, `_resolve_lanes_dir` and `resolve_feature_target_branch` (with their
  docstrings and `_WP_ID_RE`) out of `implement.py` and paste them into `workspace/context.py`
  **unchanged, names included**. The renames to `resolve_lanes_dir` and
  `resolve_mission_target_branch` happen in the T008 adjust commit (change-function-declaration).
- Add the minimal imports.
- `implement.py` imports them from the new home in the same commit, so the tree imports cleanly;
  the commit is allowed to be transiently test-red only on patch targets.
- `git diff --color-moved=zebra HEAD~1` must show moved blocks plus import lines only.

### Subtask T007 – Move the claim-precondition decision (verbatim, then reshape)

- **Move commit**: move `_ensure_wp_claim_preconditions` into `dependency_graph.py` unchanged.
- **Adjust commit**:
  - Split the event I/O out: the implement caller keeps
    `snapshot = reduce(read_events(status_feature_dir))` and passes `snapshot.work_packages`.
  - The seam function `ensure_wp_claim_preconditions(wp_id, declared_deps, work_packages)` keeps the
    genesis check, the lane map, `dependency_readiness_for_wp(..., provenance=work_packages)` and
    the `ValueError` text byte-identical.
  - Keep `WorkPackageStartRejected` from the status facade.
- Fix the two pre-existing `mypy --strict` errors in `dependency_graph.py` (~L90, ~L123, both
  `no-any-return`) with typing-only changes (boy-scout rule, NFR-002).

### Subtask T008 – Adjust commit: callers, re-exports, `__all__`, allow-list, typing

- Delete the moved names from `implement.py`, including their re-exports (research R-3). Keep a
  re-export only if **production** code imports the name from `implement`.
- `implement.__all__` drops `find_wp_file`. Add `find_wp_file` (and the other new public names) to
  `workspace/context.py`'s `__all__` if that module declares one.
- Update the dispatch map (`tests/specify_cli/cli/commands/_implement_dispatch.py`) if any entry
  pointed at a moved name.
- Apply the renames (`_resolve_lanes_dir` → `resolve_lanes_dir`, `resolve_feature_target_branch` →
  `resolve_mission_target_branch`) and update every caller.
- Fix strict typing on the moved functions (for example `resolve_feature_target_branch`'s
  no-any-return, implement.py ~L288).

### Subtask T009 – Seam unit tests

- `tests/specify_cli/core/test_claim_preconditions.py` (fast, unit, no git). Cases:
  - genesis WP raises `WorkPackageStartRejected` with the exact text;
  - an unmet dependency raises `ValueError` with the exact `dependencies_not_satisfied:` text;
  - all dependencies approved or done passes;
  - an operator-canceled dependency counts as satisfied, while a synthetic-canceled one blocks
    (move these from `test_dependency_graph_canceled.py::TestImplementClaimGateThreadsProvenance`
    if they test the same decision);
  - the present-but-falsy lane pin.
- `tests/specify_cli/workspace/test_context_implement_reads.py`:
  - `find_wp_file` (valid, invalid id, missing dir, multiple matches → first sorted);
  - `resolve_lanes_dir` returns the PRIMARY dir on a coord fixture (absorb
    `tests/cli/commands/test_resolve_lanes_dir.py` cases if they test the same thing);
  - `resolve_mission_target_branch` on a meta fixture.

### Subtask T010 – Re-point tests and gates, prove the scans

- `test_dependency_graph_canceled.py` imports `_ensure_wp_claim_preconditions` from implement:
  re-point it to the seam.
- `test_trio_read_seam_migration.py`'s `find_wp_file` case: re-point it.
- `test_issue_1615…` (fixed in WP01): make sure it still holds.
- Run the gate files: `test_cold_import_status_boundary`, `test_status_module_boundary`,
  `test_owned_checkout_single_authority`, `test_trio_seam_only`, `test_no_write_side_rederivation`,
  `test_no_dead_symbols`, `test_layer_rules`, and the liveness gate.
  - If a gate scans a fixed file list that included `implement.py` and the moved code is in scope
    for it (for example `_TRIO_FILES` for the read-seam `placement_seam(...).read_dir(...)` calls),
    add `workspace/context.py`.
  - If it is already covered by another rule, record why no widening is needed.
- Run the planted-violation proofs.

## Definition of Done

- [ ] The two move commits are pure moves; the adjust commit is separate.
- [ ] Seam tests green; the characterization suite unedited and green.
- [ ] `mypy --strict` clean on `workspace/context.py` and `core/dependency_graph.py` (the 2 pre-existing errors fixed).
- [ ] Gates green; widened scans proven by planted violations.
- [ ] Counter before and after recorded.

## Risks & Mitigations

- **Import cycle**: `mission_runtime` imports `workspace.context` lazily (resolution.py ~L3096).
  Keep `placement_seam` usage in `workspace/context.py` cycle-free, and verify by importing the
  module cold.

## Review Guidance

- `git diff --color-moved=zebra` on the move commits.
- Exact-text equality of both precondition errors.
- No new status import that breaks the cold-import gate.

## Branch Strategy

- **Strategy**: lanes topology. Execution worktrees are allocated per computed lane from `lanes.json`.
  This mission's WPs form one dependency chain, so they run sequentially in one lane.
- **Planning base branch**: `issue-5635-implement-degod`
- **Merge target branch**: `issue-5635-implement-degod`. `spec-kitty consolidate` lands the lanes
  there, locally only. The branch then reaches `main` through a PR that the operator merges.
- Prepare the workspace only with `spec-kitty agent action implement WP02 --agent claude --mission implement-degod-01M44488`
  (or `spec-kitty implement WP02 --mission implement-degod-01M44488`), and work in the path it prints.

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

