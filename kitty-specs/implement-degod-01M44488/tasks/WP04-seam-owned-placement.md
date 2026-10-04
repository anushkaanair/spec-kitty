---
work_package_id: "WP04"
subtasks:
  - "T017"
  - "T018"
  - "T019"
  - "T020"
  - "T021"
title: "#5232 seam-owned planning placement (B2*)"
task_type: "implement"
phase: "Phase 2 - #5232"
execution_mode: "code_change"
owned_files:
  - "src/specify_cli/coordination/planning_commit.py"
  - "src/specify_cli/cli/commands/implement_planning_commit.py"
  - "src/specify_cli/cli/commands/implement_cores.py"
  - "src/specify_cli/cli/commands/implement.py"
  - "tests/specify_cli/cli/commands/test_implement_placement_reachability.py"
  - "tests/specify_cli/cli/commands/test_implement_*.py"
  - "tests/specify_cli/cli/commands/test_coordination_remedy_5113.py"
  - "tests/specify_cli/cli/commands/test_precondition_ref_unification.py"
  - "tests/specify_cli/coordination/test_flat_legacy_none_seam_success_arms.py"
  - "tests/specify_cli/coordination/test_planning_commit.py"
  - "tests/lanes/test_issue_2993_lane_planning_ancestry.py"
  - "tests/specify_cli/lanes/test_lane_base_honoring.py"
  - "tests/agent/test_implement_command.py"
  - "tests/architectural/test_wp_integrity_partition_call_shape.py"
  - "tests/architectural/test_no_write_side_rederivation.py"
authoritative_surface: "src/specify_cli/coordination/"
create_intent:
  - "tests/specify_cli/cli/commands/test_implement_placement_reachability.py"
  - "src/specify_cli/coordination/planning_commit.py"
  - "src/specify_cli/cli/commands/implement_planning_commit.py"
  - "tests/specify_cli/coordination/test_planning_commit.py"
requirement_refs: ["FR-008", "FR-015", "FR-018", "SC-004", "C-007"]
dependencies: ["WP03"]
agent_profile: "python-pedro"
role: "implementer"
agent: "claude"
model: "sonnet"
history:
  - at: "2026-10-04T20:10:00Z"
    actor: "system"
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP04 – #5232 seam-owned planning placement (B2*)

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

Close #5232 under the issue's second acceptable shape: *"a documented, tested degrade path is
kept, owned by the placement seam and not by `implement.py`"*. Change **no** reachable outcome.
The design is fixed by `research.md` **R-1 (B2\*)** and `contracts/seam-decisions.md` §Placement.
Read both before you start.

- **New typed placement.** `PlanningPlacement` + `resolve_planning_placement(repo_root, *,
  mission_slug, wp_id)` in `coordination/planning_commit.py`:
  1. Call `resolve_action_context(repo_root, action="implement", feature=mission_slug, wp_id=wp_id)`
     first. Any non-`ActionContextError` propagates unchanged; this is today's pre-commit gate, and
     `MissingLanesError` / `CorruptLanesError` must still stop implement before any commit.
  2. On success: `resolved=True`, `ref=context.artifact_placement.placement_ref`, and
     `coordination_ref` = what `_placement_coord_filter` returns today for that ref.
  3. On `ActionContextError`: `resolved=False`, `ref=None`. `coordination_ref` comes from the
     placement seam (`placement_seam(repo_root, mission_slug).write_target(MissionArtifactKind.DECISION_LOG).ref`).
     It is set **only** when the stored topology routes through coordination **and** the mission
     declares a coordination branch; otherwise it is `None`.
     - Use the seam and topology helpers for both conditions. Do not hand-read `meta.json` here:
       `resolve_topology`, `routes_through_coordination`, and the topology SSOT helper that tells
       whether a coordination branch is declared.
     - If no such helper exists, the identifier cascade's `coord_branch` *may* be used **as a
       declared-ness predicate only, never as the ref value**. Record which you used.
  4. If the seam itself raises while computing `coordination_ref`, raise
     `PlacementResolutionRequired` with the single remedy text (FR-018).
- **Adapter rewire.** `_ensure_planning_artifacts_committed_git` and
  `_commit_planning_artifacts_transaction` take a required `placement: PlanningPlacement`.
  - The coord filter becomes `placement.coordination_ref`.
  - The arms are keyed on `placement.resolved` / `placement.coordination_ref`:
    - resolved → today's resolved partition arm;
    - unresolved + no coord ref → today's arm (a), the single transaction;
    - unresolved + coord ref + protected planning branch → today's arm (b) raise;
    - unresolved + coord ref + unprotected → today's arm (c) partition, destination
      `placement.coordination_ref`.
  - The `placement_ref: CommitTarget | None = None` parameter and the
    `_resolve_bookkeeping_transaction_identifiers(...)[0]` placement read are deleted.
  - The identifier tuple stays for identity: mission_id, mid8, effective ids, and the `is_legacy`
    console line.
- **Docstrings and comments** stop citing C-004. Console text is unchanged.
- **FR-018.** One definition of the `PlacementResolutionRequired` remedy text (today duplicated at
  implement.py ~L1238, now in the adapter, and `implement_cores._resolve_claim_commit_target`).
  `_resolve_placement_ref`'s `None` contract is retired; it is deleted or becomes a thin call into
  `resolve_planning_placement`. `_resolve_claim_commit_target` is reused if it fits, otherwise
  deleted along with its tests' rewritten equivalents.
- **SC-004.** `grep` shows no placement or destination read of `coordination_branch` from meta in
  the implement flow; record the command and output.

## C-007 escalation rule (binding)

If any FR-015 row's outcome differs between the base commit and your change, **stop**:
- outcome here means exit code, console text, number of planning transactions, destination refs,
  or `git status`;
- push nothing further for this WP;
- record the diverging row in the activity log and report to the orchestrator.

This is an operator decision and is never yours to make.

## Subtasks & Detailed Guidance

### Subtask T017 – Red-first reachability tests (FR-015)

Create `tests/specify_cli/cli/commands/test_implement_placement_reachability.py` (`git_repo`,
`integration`). Build the fixtures with the real CLI the way the R-1 research did: `agent mission
create`, write and commit tasks/WP files, `agent mission finalize-tasks`, then make the tree dirty
with an edited `spec.md` (PRIMARY) and an untracked `traces/approach.md` (COORD-residue).

Run the real `implement` through `CliRunner` with `--auto-commit` and record exit code, console,
planning commits (per ref: files, count) and `git status`.

Rows (each is one test, with its expected outcome = today's outcome):
1. Healthy: flat (no topology), `single_branch`, `single_branch` with a minted mission branch,
   `lanes`, `coord`, `lanes_with_coord`. Expect the resolved partition arm, with refs per topology.
2. Duplicate WP prompt (`WP01-demo.md` + `WP01-zcopy.md`, so `WORK_PACKAGE_UNRESOLVED`):
   - flat expects arm (a), one transaction, then a later refusal;
   - coord expects arm (c), the partition, then a later refusal.
3. `lanes.json` missing or corrupt: exit 1, the `MissingLanesError` / `CorruptLanesError` text,
   **zero** planning commits.
4. Coordination branch declared but never created: the context resolves, and the commit is refused
   with `DESTINATION_REF_NOT_FOUND`.
5. Merged mission with the coordination branch torn down, re-run:
   - clean tree expects exit 0, as today;
   - dirty tree expects today's commit-then-`CoordinationBranchDeleted`.

   Characterize what happens today; do not assume.
6. Arm (b), exotic: a coord mission with a protected target, `--no-auto-commit`, a COORD-residue
   file committed on primary, and a duplicate WP. Expect `PlacementResolutionRequired`, 0 commits.

Plus unit tests of `resolve_planning_placement` (they import the new API, so they are red until
T018 lands): resolved on healthy; unresolved with a coord ref on duplicate-WP coord; unresolved with
no coord ref on duplicate-WP flat; `PlacementResolutionRequired` when the seam raises.

**Commit T017 alone first.** The behavioural rows must be **green on the base** (they pin today);
the unit tests of the new API are red. Record both counts. That commit is the red-first evidence.

### Subtask T018 – Implement `PlanningPlacement` / `resolve_planning_placement`

Follow the contract exactly. Keep it pure apart from the seam and context calls, and give it unit
tests (T017).

### Subtask T019 – Rewire the adapter arms

- Replace the `placement_ref` parameter and every `placement_ref is None` branch with the typed
  placement.
- Keep the arm bodies byte-identical: same `_run_planning_artifact_commit` calls, same
  `commit_to_primary_target` / `enforce_partition` values, same console lines.
- The validate block in `implement.py` calls `resolve_planning_placement(...)` where it called
  `_resolve_placement_ref(...)`.
- Re-run the FR-015 rows: all green, **identical** to the T017 run.

### Subtask T020 – FR-018 remedy dedupe and dead helper

- One module-level remedy builder, `placement_resolution_remedy(mission_slug) -> str`, in the
  seam. Both raise sites use it, and the text is byte-identical. Add a test asserting the text.
- Delete or redirect `_resolve_placement_ref`. Reuse or delete `_resolve_claim_commit_target`, and
  re-point `test_no_write_side_rederivation.py` (~L519 names it) accordingly.

### Subtask T021 – Rewrite the tests that pinned or forced the `None` path

- `tests/specify_cli/cli/commands/test_coordination_remedy_5113.py` (~L238–243): asserts
  `_resolve_placement_ref` returns `None`. Rewrite it to assert `resolve_planning_placement`
  returns `resolved=False` with the seam coord ref for that fixture.
  - The research showed its `None` comes from `WORK_PACKAGE_UNRESOLVED` (no WP in the fixture),
    not from the unmaterialized worktree. Say so in the test docstring.
- `tests/agent/test_implement_command.py:~710` and `tests/specify_cli/lanes/test_lane_base_honoring.py:~260`:
  they patch `_resolve_placement_ref → None`. Patch `resolve_planning_placement` to return the
  unresolved placement instead, or supply a real one.
- `tests/specify_cli/coordination/test_flat_legacy_none_seam_success_arms.py` (INV-7): re-key it.
  "An unresolved placement with no coordination ref on a flat mission reaches the flat success arm
  and commits once to the planning branch." Keep its intent; do not delete it.
- `tests/lanes/test_issue_2993_lane_planning_ancestry.py` (the `legacy-fallback` param),
  `test_implement_writeside.py` (`placement_ref=None` call sites) and
  `test_precondition_ref_unification.py` (L237, L302): pass the typed placement instead.
- `test_implement_bookkeeping_identifiers.py::test_consumer_contract_five_tuple_positions_match_fixture`
  (C-006): the `[0]` placement consumer is gone. The tuple stays (identity), so update the
  docstring or contract note, not the arity.
- `tests/architectural/test_wp_integrity_partition_call_shape.py`: the arm count is unchanged
  under B2\* (all arms survive), so the floor stays at 3. Verify, and do not touch it unless it
  reds.

## Definition of Done

- [ ] T017 committed alone first: behavioural rows green on base, new-API unit tests red; counts logged.
- [ ] All FR-015 rows identical before and after; any difference means escalation.
- [ ] No `placement_ref=None` overload; no meta-derived placement read; the remedy defined once; no C-004 wording in docstrings or comments.
- [ ] Characterization suite unedited and green; INV-7 re-keyed and green.
- [ ] `mypy --strict`, ruff and C901 clean.

## Risks & Mitigations

- **The `DECISION_LOG` choice**: the research showed it equals the context placement in every
  lifecycle phase where both resolve, while `STATUS_STATE` diverges under PUBLISHED.
- **Topology/declared-branch predicate**: if no seam helper exists, use the identifier cascade only
  as a boolean, and note it.

## Review Guidance

- Re-run the FR-015 suite on the base commit (checkout of T017's parent plus the T017 test file)
  and on the head. The rows must be identical.
- Read the arms diff: bodies unchanged, only the keys changed.

## Branch Strategy

- **Strategy**: lanes topology. Execution worktrees are allocated per computed lane from `lanes.json`.
  This mission's WPs form one dependency chain, so they run sequentially in one lane.
- **Planning base branch**: `issue-5635-implement-degod`
- **Merge target branch**: `issue-5635-implement-degod`. `spec-kitty consolidate` lands the lanes
  there, locally only. The branch then reaches `main` through a PR that the operator merges.
- Prepare the workspace only with `spec-kitty agent action implement WP04 --agent claude --mission implement-degod-01M44488`
  (or `spec-kitty implement WP04 --mission implement-degod-01M44488`), and work in the path it prints.

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

