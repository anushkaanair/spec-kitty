---
work_package_id: "WP09"
subtasks:
  - "T041"
  - "T042"
title: "Issue matrix and follow-ups"
task_type: "plan"
phase: "Phase 5 - Tracker hygiene"
execution_mode: "planning_artifact"
owned_files:
  - "kitty-specs/implement-degod-01M44488/issue-matrix.md"
authoritative_surface: "kitty-specs/implement-degod-01M44488/"
create_intent:
  - "kitty-specs/implement-degod-01M44488/issue-matrix.md"
requirement_refs: ["FR-017"]
dependencies: ["WP08"]
agent_profile: "planner-priti"
role: "planner"
agent: "claude"
model: "sonnet"
history:
  - at: "2026-10-04T20:10:00Z"
    actor: "system"
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP09 – Issue matrix and follow-ups

## ⚡ Do This First: Load Agent Profile

Load the agent profile named in the frontmatter through the canonical path, and work according to
its guidance before you read the rest of this prompt:

```bash
spec-kitty agent profile show planner-priti
spec-kitty charter context --action plan --json
```

- **Profile**: `planner-priti`
- **Role**: `planner`
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

- `kitty-specs/implement-degod-01M44488/issue-matrix.md` has one row per addressed issue, using the
  repository's canonical issue-matrix format. Find it from an existing mission:
  `ls kitty-specs/*/issue-matrix.md | head`; also read `spec-kitty charter context --action review`
  for the verdict vocabulary. Rows:
  - #5635: delivered; closed by the PR.
  - #5232: delivered (B2\*, seam-owned typed placement); closed by the PR.
  - #5673: shaped, not fixed (`implement_claim.claim_commit_paths`); stays open.
  - #5676: out of scope (`core/mission_creation.py`, sibling mission #5634).
  - #5669 and #3931: out of scope.
- Follow-up issues are filed by the orchestrator through the GitHub tooling, and their numbers are
  recorded in the matrix and in the PR body:
  1. The planning-artifact commit lands before late validation (`resolve_workspace_for_wp`, lane
     lookup), so a validate failure leaves a landed commit.
  2. An unmaterialized coordination worktree surfaces as a misleading "WP not finalized" refusal.
  3. A shared implement application service for `implement`, `agent action implement` and
     `orchestrator_api` (needs an ADR; includes deduping the dependency-gate glue with
     `status/dependency_verdict.py`).
  4. The #5232 single-path end state (B1): an operator decision, because it changes four reachable
     outcomes (research.md R-1).

## Subtasks & Detailed Guidance

### Subtask T041 – Write the issue matrix
Follow the canonical format exactly. Each row carries an issue number, a verdict and evidence (a
WP id or a research.md section).

### Subtask T042 – Follow-ups
Draft each follow-up's title and body (why / for whom / intended effect / evidence with
file:line), and hand them to the orchestrator to file. Each body ends with the Claude Code
attribution footer. Record the returned numbers in the matrix.

## Definition of Done

- [ ] Matrix rows for all six issues with verdicts.
- [ ] Four follow-ups filed and their numbers recorded.

## Branch Strategy

- **Strategy**: lanes topology. Execution worktrees are allocated per computed lane from `lanes.json`.
  This mission's WPs form one dependency chain, so they run sequentially in one lane.
- **Planning base branch**: `issue-5635-implement-degod`
- **Merge target branch**: `issue-5635-implement-degod`. `spec-kitty consolidate` lands the lanes
  there, locally only. The branch then reaches `main` through a PR that the operator merges.
- Prepare the workspace only with `spec-kitty agent action implement WP09 --agent claude --mission implement-degod-01M44488`
  (or `spec-kitty implement WP09 --mission implement-degod-01M44488`), and work in the path it prints.

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

