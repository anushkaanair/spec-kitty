---
work_package_id: "WP07"
subtasks:
  - "T032"
  - "T033"
  - "T034"
  - "T035"
  - "T036"
title: "Thin command and phase sequence"
task_type: "implement"
phase: "Phase 3 - Thin command"
execution_mode: "code_change"
owned_files:
  - "src/specify_cli/cli/commands/implement.py"
  - "src/specify_cli/cli/commands/implement_phases.py"
  - "src/specify_cli/cli/commands/implement_recover.py"
  - "pyproject.toml"
  - "tests/specify_cli/cli/commands/test_implement_phases.py"
  - "tests/specify_cli/cli/commands/test_implement_placement_routing.py"
  - "tests/specify_cli/cli/commands/test_implement_json_safe_output.py"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
  - "tests/specify_cli/test_operational_context_wiring.py"
  - "tests/agent/test_implement_programmatic_call.py"
  - "tests/agent/cli/commands/test_implement_preflight.py"
  - "tests/architectural/test_trio_seam_only.py"
  - "tests/architectural/test_exemption_registry_ratchet.py"
  - "tests/architectural/test_no_write_side_rederivation.py"
  - "tests/contract/test_terminology_guards.py"
  - "tests/contract/test_feature_alias_scope.py"
authoritative_surface: "src/specify_cli/cli/commands/"
create_intent:
  - "src/specify_cli/cli/commands/implement_phases.py"
  - "src/specify_cli/cli/commands/implement_recover.py"
  - "tests/specify_cli/cli/commands/test_implement_phases.py"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
requirement_refs: ["FR-001", "FR-002", "FR-014", "NFR-001", "NFR-002", "SC-001"]
dependencies: ["WP06"]
agent_profile: "python-pedro"
role: "implementer"
agent: "claude"
model: "sonnet"
history:
  - at: "2026-10-04T20:10:00Z"
    actor: "system"
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP07 – Thin command and phase sequence

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

- **`implement.py` becomes thin (FR-001, SC-001: at most 800 lines by `wc -l`).** It keeps:
  - the Typer `implement` command, with signature, option defaults and decorators byte-identical
    (FR-014);
  - `_json_safe_output` and its `_json_wrapper_*` helpers;
  - `detect_feature_context` (it imports `cli.selector_resolution`);
  - presentation: `_report_workspace_created`, `_print_workspace_ready_banner`,
    `_build_implement_json_payload`, `_BANNER_*`;
  - the tracker steps;
  - the call into the phase sequence.
- **`implement_phases.py` holds the ordered phase functions (FR-002).** Each is a named function
  that consumes and produces the immutable phase values from data-model.md (`ImplementContext`,
  `ClaimPreflight`, `WorkspaceSelection`, `AllocationResult`):
  `detect_context` → `claim_preflight` (target branch, protected check, status surface, lanes dir,
  dependency gate) → `commit_planning_artifacts` → `run_bulk_edit_gate` + `build_operational_context`
  → `select_workspace` → `allocate` → `record_claim` (status start) → `commit_claim`.
  - Bodies move **verbatim** from today's `implement()` blocks.
  - `_detect_wp_context` and `_run_bulk_edit_gate_and_inference` move here.
- **`implement_recover.py` holds `--recover`.** Move `_run_recover_mode` and the `_recover_*`
  helpers verbatim; the output is unchanged.
- **Tracker step boundaries and per-step exception handling are byte-identical**:
  - detect: catch the fixed tuple → exit 1;
  - validate: catch `Exception` → tracker error + exit 1;
  - create: catch `Exit` → render + raise; catch `Exception` → the `workspace_created`-aware
    message, plus `next_step` for the three allocator errors;
  - outer claim-commit try: propagate three types, soften the rest.

  The tracker and its exception handling stay in `implement()`, or in a CLI-layer helper in
  `implement.py`. The phase functions raise; they do not render.
- `implement()` complexity drops below 15 (NFR-001).
- `mypy --strict`: remove `implement.py`'s quarantine entry (`pyproject.toml` ~L2675, an
  `ignore_errors` override) if the thin module is strict-clean. Otherwise keep it unchanged and list
  the remaining errors in the activity log. The two known ones are `_json_wrapper_handle_typer_exit`
  (~L175) and the untyped decorator on `implement` (~L1976); fix them if typing-only.

## Context & Constraints

- **Source-text pins to re-point (never loosen):**
  - `tests/specify_cli/cli/commands/test_implement_placement_routing.py:~97,125`: the except-order
    pin on `inspect.getsource(implement)`. If the outer claim-commit try stays in `implement()`, it
    keeps working; if it moves into a helper, re-point the pin to that helper.
  - The same file, ~L307: a forbidden-ternary scan over the module text. Widen it to the implement
    family (all `implement*.py`), so the moved code stays scanned.
  - `tests/specify_cli/test_operational_context_wiring.py:~254`: requires
    `build_operational_context_for_claim` and `require_active_role` in `implement`'s source.
    Re-point it to the phase function that now calls them.
- **Programmatic call.** `agent/workflow.py:~83,1620` imports `implement` and calls it with kwargs.
  Do not touch workflow.py. `tests/agent/test_implement_programmatic_call.py` and the WP01
  characterization must stay green.
- **Console singleton.** Every print uses `specify_cli.cli.console.console`; never cache
  `console.file`. `--json` error text = the last 20 captured lines, so print order matters.
- The lazy imports inside `implement()` (charter preflight, `surface_resolver`, `runtime_bridge`,
  `is_planning_lane`) move with their blocks. Keep them lazy.
- Gate lists: add `implement_phases.py` and `implement_recover.py` to `_TRIO_FILES`,
  `CHURN_SURFACE_MODULES`, `_WRITE_DIR_CONSUMER_MODULES` and the terminology/alias scans wherever
  they carry moved code. Prove each with a plant.

## Subtasks & Detailed Guidance

### Subtask T032 – `implement_phases.py` (verbatim move of the phase blocks)
- Create the frozen phase-value types first, in one small commit.
- Then the move commit: each `implement()` block between tracker calls becomes a phase function,
  with its body byte-identical apart from returning the value it used to bind locally.

### Subtask T033 – `implement_recover.py`
Verbatim move of the recover family. `implement()` calls `implement_recover.run_recover_mode(...)`
after the `--mission` guard, which still exits 2 first.

### Subtask T034 – Thin `implement()`
Rebuild `implement()` as: guard → recover → tracker steps calling the phase functions inside the
same try/except shapes → claim-commit outer try → present. Run ruff C901 and confirm < 15.

### Subtask T035 – Phase-order test and pin re-pointing
- `tests/specify_cli/cli/commands/test_implement_phases.py`:
  - on a healthy fixture, spy each phase function (patched at `implement_phases.<fn>`) and assert
    the call order;
  - unit-test each phase function's value plumbing where it is cheap.
- Re-point the three source pins above.

### Subtask T036 – Quarantine, gates, size
Handle the mypy quarantine entry, widen the gate lists with proofs, check `wc -l` (implement.py
≤ 800, every new sibling ≤ 800), and record the counter.

## Definition of Done

- [ ] `wc -l src/specify_cli/cli/commands/implement.py` ≤ 800; no new module > 800.
- [ ] `implement()` C901 < 15; the Typer signature, defaults and decorators unchanged (FR-014 test green).
- [ ] Characterization suite unedited and green; phase-order test green.
- [ ] Source pins re-pointed, not loosened; gate lists widened with plant proofs.
- [ ] Quarantine decision recorded.

## Review Guidance

- Compare `implement()` before and after for the exception shapes.
- Run `--json` success and error manually on a fixture.
- Run `spec-kitty agent action implement` once on a scratch mission if feasible.

## Branch Strategy

- **Strategy**: lanes topology. Execution worktrees are allocated per computed lane from `lanes.json`.
  This mission's WPs form one dependency chain, so they run sequentially in one lane.
- **Planning base branch**: `issue-5635-implement-degod`
- **Merge target branch**: `issue-5635-implement-degod`. `spec-kitty consolidate` lands the lanes
  there, locally only. The branch then reaches `main` through a PR that the operator merges.
- Prepare the workspace only with `spec-kitty agent action implement WP07 --agent claude --mission implement-degod-01M44488`
  (or `spec-kitty implement WP07 --mission implement-degod-01M44488`), and work in the path it prints.

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

