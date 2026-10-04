---
work_package_id: "WP01"
subtasks:
  - "T001"
  - "T002"
  - "T003"
  - "T004"
  - "T005"
title: "Safety net before any move"
task_type: "implement"
phase: "Phase 0 - Safety net"
execution_mode: "code_change"
owned_files:
  - "tests/specify_cli/cli/commands/test_implement_characterization.py"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
  - "tests/specify_cli/cli/commands/agent/test_tasks_patch_targets_live.py"
  - "tests/specify_cli/regression/test_issue_1615_1616_1617_1618.py"
  - "tests/agent/test_implement_command.py"
  - "tests/specify_cli/cli/commands/test_implement.py"
authoritative_surface: "tests/specify_cli/cli/commands/"
create_intent:
  - "tests/specify_cli/cli/commands/test_implement_characterization.py"
  - "tests/specify_cli/cli/commands/_implement_dispatch.py"
requirement_refs: ["FR-009", "FR-010", "FR-013", "FR-014", "SC-003"]
dependencies: []
agent_profile: "python-pedro"
role: "implementer"
agent: "claude"
model: "sonnet"
history:
  - at: "2026-10-04T20:10:00Z"
    actor: "system"
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP01 – Safety net before any move

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

Freeze today's `spec-kitty implement` behaviour through **public entry points only**, make stale
test patches into the implement family fail loudly, and repair the tests the grounding found
vacuous. No source file under `src/` changes in this WP.

Done when:
- **FR-009 suite.** `tests/specify_cli/cli/commands/test_implement_characterization.py` exists and
  is green on the base commit.
  - It drives only the CLI (`CliRunner` over the `implement` Typer command), the `implement`
    command function, and `agent action implement`.
  - No assertion names an implement-family internal.
  - A planted break per refusal family turns it red; record each plant and its red output in the
    activity log.
- **FR-010 liveness gate.** `tests/specify_cli/cli/commands/agent/test_tasks_patch_targets_live.py`
  also covers the implement family: every `src/specify_cli/cli/commands/implement*.py` module,
  derived from the filesystem, so the siblings later WPs add join automatically.
  - `UNRESOLVABLE_BASELINE` is not raised.
  - Dead implement patches it finds are fixed, not allow-listed.
  - A planted dead patch turns the gate red.
- **FR-013 vacuous tests.** The four named tests are repaired or retired, each with its
  planted-break proof.
- **FR-014.** The programmatic-call contract is pinned. `agent action implement` calls `implement`
  with the optional kwargs omitted, and the signature, option defaults and decorators are
  asserted.

## Context & Constraints

- Read first:
  - `kitty-specs/implement-degod-01M44488/spec.md` (FR-009, FR-010, FR-013, FR-014);
  - `research.md` R-3 and R-5;
  - `research/test-remediation.md` §3–§5;
  - `research/code-grounding.md` §1.3 (behaviour that must survive).
- Live code under test: `src/specify_cli/cli/commands/implement.py` (`implement()` at about L1977,
  `_json_safe_output` at about L188).
- Fixture helpers to reuse, not re-invent:
  - `tests/specify_cli/cli/commands/test_single_branch_implement_refusals.py`
    (real-git single_branch missions, WRITE_CHECKOUT_* refusals, the meta.json-has-no-`vcs`
    no-mutation check);
  - `tests/integration/test_wp_integrity_p0_repro.py` (coord topology);
  - `tests/agent/test_implement_command.py` `create_meta_json`;
  - `tests/specify_cli/cli/commands/test_implement_json_safe_output.py`.
- Side-effect order to pin (code-grounding §1.3, plan.md Engineering Alignment):
  1. `--mission` guard (exit 2), which runs before `--recover`;
  2. the charter preflight;
  3. target branch and protected status-commit check;
  4. the status surface and the dependency gate;
  5. the planning-artifact commit (which can commit);
  6. the bulk-edit gate;
  7. the operational context;
  8. `resolve_workspace_for_wp(write_intent=True)`;
  9. the lane lookup;
  10. the write-checkout refusals;
  11. the VCS lock;
  12. `create_lane_workspace`;
  13. `start_implementation_status`;
  14. the claim commit.

## Subtasks & Detailed Guidance

### Subtask T001 – Widen the patch-liveness gate to the implement family

- **Purpose**: today `test_tasks_patch_targets_live.py` covers only `agent/tasks_*.py` + `tasks`.
  About 120 patch sites target `specify_cli.cli.commands.implement[_cores].*`. After a move they
  would silently stop intercepting.
- **Steps**:
  1. Read the gate end to end (module docstring rules, `_function_locals`,
     `_name_loads_outside_own_def`, the ALLOWLIST and `UNRESOLVABLE_BASELINE`).
  2. Generalize it to two **families** in the same file: the existing tasks family, unchanged,
     and an implement family. The implement family is `src/specify_cli/cli/commands/implement*.py`
     whose stem is `implement` or starts with `implement_`, derived by glob so WP03/05/06/07's new
     siblings join automatically.
  3. Liveness rule for the implement family: the same seam-module rule as tasks (a module-level
     name is live if the module reads it as a plain `Name` load outside its own def, or a call-time
     `from <pkg>.M import name` exists anywhere under `src/`).
  4. Parametrize the test ids by family so failures name the family.
  5. Run it. Any implement patch reported dead today is a **real dead patch**. Fix the test by
     re-pointing it to where the name is looked up, and record each fix in the activity log.
  6. Do not add allowlist entries for implement. Do not raise `UNRESOLVABLE_BASELINE`.
     - If an unresolvable implement target appears, resolve the test's target so the scanner can
       read it.
     - If that is impossible, stop and record why; the orchestrator decides.
  7. Positive control: plant `monkeypatch.setattr("specify_cli.cli.commands.implement.no_such_dispatch", ...)`
     in a scratch test, run red, and remove it.
- **Files**: `tests/specify_cli/cli/commands/agent/test_tasks_patch_targets_live.py`.
- **Notes**: keep the tasks-family behaviour byte-identical. Its existing assertions must not change.

### Subtask T002 – Characterization part 1: refusal families with no mutation

- **Purpose**: pin every refusal family's observable outcome before any raise site moves.
- **Steps**: create `tests/specify_cli/cli/commands/test_implement_characterization.py`, marked
  `git_repo` + `integration`. Build each case from a real-git fixture and invoke through `CliRunner`.
  For each case assert:
  1. the exit code;
  2. the refusal text (the substring today's tests use, plus the full message where the message is
     a contract; decide per refusal and note it);
  3. **no mutation**: no new `.worktrees/` entry, no `vcs` key added to `meta.json`, no new line in
     `status.events.jsonl`, and HEAD unchanged where the refusal precedes the planning commit.

  Cases:
  - `--mission` omitted → exit 2, `--mission <slug> is required` (also with `--recover`).
  - WP not finalized (genesis) → exit 1, contains `is not finalized; run \`spec-kitty agent mission finalize-tasks\``.
    No test pins this today.
  - Dependency not approved → exit 1, contains `dependencies_not_satisfied:` and the full
    `… all dependencies must be approved or done before implementation can start` text.
  - Protected status-commit target with auto-commit → exit 1, `Refusing to start implementation status on protected branch`.
  - `lanes.json` missing → exit 1, `lanes.json is required`.
  - `--base <nonexistent>` → exit 1, the canonical `Base ref '…' does not resolve. Try 'git fetch' or 'git branch -a' to see available refs.`
  - single_branch WRITE_CHECKOUT_WRONG_BRANCH, WRITE_CHECKOUT_OCCUPIED and WRITE_CHECKOUT_DIRTY
    (reuse the existing fixtures) → exit 1 with today's text, and no `vcs` in `meta.json`.
  - meta.json coordination demotion (#4979) → exit 1, the `silently demotes` refusal.
- **Notes**: a single parametrized test with a case table is fine, but keep each case's fixture
  explicit and readable. Positive controls: for each family, plant a break in the *source* (for
  example comment out the raise), run red, revert, and log it.

### Subtask T003 – Characterization part 2: order, #4888, exception table, JSON, programmatic call

- **Purpose**: pin the parts of the contract that a reordering or re-wiring would break.
- **Dispatch-map fixture**: create `tests/specify_cli/cli/commands/_implement_dispatch.py`.
  - It holds a single mapping from a *logical collaborator* to its current dotted dispatch target,
    for example `"start_status": "specify_cli.cli.commands.implement.start_implementation_status"`.
  - It also holds a helper `patch_collaborator(monkeypatch, logical_name, replacement)`.
  - Assertions never reference implement internals. Later WPs update only this map when a
    dispatch site moves. Document this in the module docstring.
  - The liveness gate (T001) must see these targets. Check that it scans the map's string
    literals; they are plain `"specify_cli.cli.commands.implement.X"` strings, so the string scan
    covers them.
- **Cases**:
  - **Side-effect order**: wrap the collaborators in recording spies (through the dispatch map) on a
    healthy lanes fixture. Assert the recorded sequence: target branch → dependency gate → planning
    commit → bulk-edit gate → operational context → workspace resolve → VCS lock → allocate →
    status start → claim commit.
  - **#4888**: make `start_status` raise `RuntimeError("boom")` after allocation. Assert exit 1 and
    the text `Workspace was created but starting the WP status failed: boom.` +
    `The WP status transition may have already landed on the lane branch.` Then repeat with an
    exception carrying `commit_sha="abc"` and assert the `(sha=abc)` variant.
  - **Allocation failure before workspace exists**: `allocate` raises → exit 1,
    `Workspace allocation failed:`.
  - **Claim-commit exception table**:
    - `SafeCommitPathPolicyError`, `SafeCommitHeadMismatch` and `PlacementResolutionRequired`
      raised by the claim commit propagate (non-zero exit; the exception type is visible).
    - A generic `RuntimeError` is softened: exit 0 and `Warning: Could not update WP status:`
      (outer handler), or `Could not auto-commit lane change:` (inner handler). Pin the one today's
      code produces for each injection point.
  - **`--json`**:
    - success payload keys and values on a healthy lanes fixture;
    - error payload `{"status":"error","error":…,"wp_id":…}` on a refusal;
    - stdout is exactly one JSON document in both cases.
  - **Programmatic call (FR-014)**:
    - Call `implement(...)` the way `agent/workflow.py:~1620` does, with keyword arguments and the
      optional ones omitted. Assert it behaves like the CLI call, with no
      `'OptionInfo' object has no attribute` error.
    - Also assert `inspect.signature(implement)` parameter names and defaults, and that the
      function is wrapped (decorators present, `functools.wraps` preserved:
      `implement.__wrapped__` exists).

### Subtask T004 – Repair the vacuous tests (FR-013)

Each repair needs a planted break that proves its covering guard is live. Plant, run red, revert,
and log every one.
- `tests/specify_cli/regression/test_issue_1615_1616_1617_1618.py::test_resolve_mission_read_path_used_in_implement`
  passes only because of a *comment* (implement.py ~L2066).
  - Replace the oracle with a behavioural one: on a coord-topology fixture whose WP is seeded only
    on the coord status surface, the implement dependency gate reads that surface (the claim is
    not refused as "not finalized").
  - If a behavioural test is too heavy for this file, assert instead that the dependency-gate read
    calls `resolve_status_surface_with_anchor`, via a spy in the dispatch map.
  - Planted break: make the gate read the primary surface → red.
- `tests/agent/test_implement_command.py::test_implement_requires_lanes_json` (~L163) is vacuous: it
  exits on "Could not determine current branch".
  - Retire it. The covering guard is `test_implement_json_error_output_is_clean` (~L246, asserts
    `lanes.json is required`), plus the new T002 case.
  - Planted break: make `require_lanes_json` return silently → both go red.
- `tests/specify_cli/cli/commands/test_implement.py` `callable(implement)` (~L375) and
  `hasattr(implement, "safe_commit")` (~L363).
  - Retire both. The covering guard is any class-B test that imports and calls `implement`, plus
    T003's programmatic-call case.
  - Planted break: rename `implement` → import error.

### Subtask T005 – Evidence and baseline

- Record in the activity log:
  - the counter output (`tools/count_patch_sites.py`, expected 119 on the base commit, minus any
    retired patch);
  - every planted break (file, change, failing test id);
  - the run counts for the new suite and the gate.
- Run the regression subset (quickstart.md §2) and record its counts.

## Definition of Done

- [ ] Characterization suite green on the base commit; each family proven non-vacuous by a planted break.
- [ ] Liveness gate covers the implement family by glob; planted dead patch proven red; no baseline raise; no implement allowlist entries.
- [ ] The four FR-013 tests repaired or retired with planted-break proofs.
- [ ] No `src/` file changed.
- [ ] Validation commands run and recorded.

## Risks & Mitigations

- **Fixture cost.** Real-git fixtures are slow. Reuse module-scoped builders where safe, and keep
  the suite under ~20 s.
- **Accidental internal coupling.** Review every `monkeypatch`: it must go through the dispatch map,
  or target a non-implement module the command does not re-import into its namespace.

## Review Guidance

- Verify that no assertion names an implement internal and that every injection uses the dispatch map.
- Re-run two planted breaks yourself.
- Confirm that the liveness widening did not change the tasks-family results.

## Branch Strategy

- **Strategy**: lanes topology. Execution worktrees are allocated per computed lane from `lanes.json`.
  This mission's WPs form one dependency chain, so they run sequentially in one lane.
- **Planning base branch**: `issue-5635-implement-degod`
- **Merge target branch**: `issue-5635-implement-degod`. `spec-kitty consolidate` lands the lanes
  there, locally only. The branch then reaches `main` through a PR that the operator merges.
- Prepare the workspace only with `spec-kitty agent action implement WP01 --agent claude --mission implement-degod-01M44488`
  (or `spec-kitty implement WP01 --mission implement-degod-01M44488`), and work in the path it prints.

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

