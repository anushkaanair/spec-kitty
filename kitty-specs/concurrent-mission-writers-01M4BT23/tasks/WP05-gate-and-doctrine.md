---
work_package_id: WP05
title: Architectural gate and one-writer doctrine
dependencies:
- WP02
- WP03
- WP04
requirement_refs:
- FR-010
- FR-011
planning_base_branch: issue-5819-concurrent-mission-writers
merge_target_branch: issue-5819-concurrent-mission-writers
branch_strategy: Planning artifacts for this mission were generated on issue-5819-concurrent-mission-writers. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5819-concurrent-mission-writers unless the human explicitly redirects the landing branch.
subtasks:
- T021
- T022
- T023
- T024
phase: Phase 3
history:
- at: '2026-10-07T19:00:00Z'
  actor: system
  action: Prompt generated via /spec-kitty.tasks
agent_profile: python-pedro
authoritative_surface: tests/architectural/
create_intent:
- tests/architectural/test_mission_write_discipline.py
execution_mode: code_change
model: claude-sonnet
owned_files:
- tests/architectural/test_mission_write_discipline.py
- packs/built-in/missions/mission-steps/software-dev/implement/prompt.md
- packs/built-in/missions/mission-steps/software-dev/review/prompt.md
- packs/built-in/pack-manifest.yaml
- tests/prompts/test_prompt_fragment_rendering.py
- tests/specify_cli/next/test_wp_prompt_governance_contract.py
- tests/doctrine/fixtures/content-manifest.json
- tests/architectural/_builtin_pack_provenance_baseline.yaml
role: implementer
tags: []
task_type: implement
tracker_refs: []
---

# Work Package Prompt: WP05 – Architectural gate and one-writer doctrine

## ⚡ Do This First: Load Agent Profile

Use the `/ad-hoc-profile-load` skill (or `spk-doctrine-profile-load`) to load the agent profile in the frontmatter, and behave according to its guidance before parsing the rest of this prompt.

- **Profile**: `python-pedro`
- **Role**: `implementer`
- **Agent/tool**: `claude`

---

## ⚠️ IMPORTANT: Review Feedback

Check `spec-kitty agent tasks status --mission concurrent-mission-writers-01M4BT23` and the Activity Log below for a `review_ref`; address every feedback item before marking the WP done.

---

## Context & Constraints (all WPs)

- Binding: `.kittify/charter/charter.md`, `CLAUDE.md`, `kitty-specs/concurrent-mission-writers-01M4BT23/plan.md` — **the "Amendments after the post-plan squad" section overrides D1–D6**. Also `spec.md`, `research.md`, `data-model.md`.
- Terminology: **Mission**, never "feature", in all new prose/identifiers (existing identifiers like `feature_dir` stay).
- Red-first (ADR 2026-07-17-1): write the reproduction test first, run it against the unchanged code and record the RED output (test id + assertion line) in the tracer via `spec-kitty agent tracer-append --mission concurrent-mission-writers-01M4BT23 --category approach --actor <you> --entry "..."`, then fix. Concurrency tests are deterministic: inject `threading.Event`/`Barrier` hooks at seams (monkeypatch), never `sleep` as synchronization; give each wait a timeout so a regression fails instead of hanging. Real git repos via existing fixtures where git matters. Mark tests `pytest.mark.unit` or `pytest.mark.git_repo` per neighbours; only real multi-process tests get `stress`.
- Code quality: ruff, `ruff format --check --force-exclude <files>`, mypy on changed files — zero new findings, no new `# noqa` / `# type: ignore`; cyclomatic complexity ≤ 15; repeated literals (≥3) become constants.
- Coordinate: PR #5876 edits `workflow.py`, `workflow_executor.py`, `status/__init__.py`, `status/store.py`, `status/emit.py`, `tasks_move_task_executor.py`. Keep hunks minimal and away from its regions. Never implement a `git add -A`/`git stash` commit-scope gate (#5443 owns it).
- Commit with explicit paths (`git add <paths>`; never `git add -A`, never `git stash`). Commit message: `fix(<area>): ... (#<issue>)` with the attribution trailer the orchestrator gives you.
- Tests to run: your new tests, the test files of every module you touch, the owning subsystem directory fast tier, plus `make test-fast`; never `make test-full` or a bare `tests/architectural/` sweep (only named gate files). Record exact commands and pass/fail counts in the Activity Log.

## Branch Strategy

- **Strategy**: single_branch (direct_repo), sequential WPs in the repository root checkout
- **Planning base branch**: issue-5819-concurrent-mission-writers
- **Merge target branch**: issue-5819-concurrent-mission-writers

## Objectives & Success Criteria

Close the defect class by construction (charter Standing Order #5) and state the one-writer rule in shipped doctrine (amendments A11, A12, A14). After this WP:

- `tests/architectural/test_mission_write_discipline.py` passes on the real tree with EMPTY allowlists and fails on every synthetic offender and on the self-mutated real module.
- The software-dev implement and review mission-step prompts state the one-writer-per-checkout rule (implementers and reviewers, single_branch included), without any `git add -A`/`git stash` wording (#5443 owns that).

## Subtasks & Detailed Guidance

Model the scanner on `tests/architectural/test_acceptance_matrix_write_seam.py` (call-shape resolution incl. aliases, census floor, stale-entry test) and `test_lock_primitive_ban.py` (accepted over-fire documentation). Scan `src/specify_cli/**/*.py`; the docstring states that `src/runtime` (run.events.jsonl) and `src/kernel` (lock files) are out of scope by design.

### T021 – Rule 1: truncate / unlink of the status log only in the primitive

- Flag: `<expr>.truncate(...)`; `os.truncate`, `os.ftruncate`, `posix.*` and their `import os as _os` / `from os import ftruncate as t` aliases; `getattr(<x>, "truncate")`; `operator.methodcaller("truncate", ...)`; `.unlink(` on an expression whose text names the event log (`events_path`, `_events_path`, `EVENTS_FILENAME`, `"status.events.jsonl"`).
- Allowed only in `src/specify_cli/status/mission_write.py`. Floor: exactly the primitive's sites (positive control: the scanner finds them). Accepted over-fire: rich `Text.truncate` (none in scope today) — documented.
- Non-vacuity: a list of synthetic source snippets (each form above) fed to the scanner must each be flagged.

### T022 – Rule 2: read/sink pairs in one locked region

- Registered pairs (extendable dict with rationale): add-history `(locate_work_package | the primitive read, append_activity_log)`; tracer `(_read_current_coord_content, _append_entry)`.
- A call is in a **locked region** when it is (a) inside the body of `with mission_write_lock(...)` / `feature_status_lock(...)` / `coord_status_lock(...)` without crossing a nested `FunctionDef`/`Lambda`, or (b) inside a function/lambda passed as `transform` to `locked_rewrite_text`, or (c) inside a function/lambda passed as an argument to a call that is itself in region (a). A named function is resolved to its `def` in the same module and must have no other references. Every sink call must be in a locked region and, where the pair's read is a call in the same module, the read must be in the same region (or the sink is inside a `locked_rewrite_text` transform, whose read is the primitive's). Non-call references to a sink (e.g. `functools.partial(append_activity_log, ...)`) fail as unclassifiable.
- Floor: exactly the two current sink sites, both locked.
- Self-mutation: parse the real `cli/commands/agent/tasks.py` and `retrospective/tracer_writer.py`, strip the lock (`With` → its body / replace `locked_rewrite_text(path, f, ...)` with `f(None)`), assert the gate fires.

### T023 – Rule 3: no slug-keyed status lock

- Flag any `feature_status_lock(<root>, <key>)` call whose key expression is a Name/Attribute whose identifier contains `slug` (e.g. `mission_slug`, `st.mission_slug`). Empty allowlist after WP04. Synthetic positive control.

### T024 – One-writer doctrine sentence

- `packs/built-in/missions/mission-steps/software-dev/implement/prompt.md` (~:42 "only one WP may be in progress at a time" for single_branch): extend with the rule — one writer per checkout: concurrent implementers and reviewers each work in their own checkout (lane worktree, or a harness-isolated worktree); on single_branch the repository-root checkout has one writer at a time, and `implement` refuses a second claim (`WRITE_CHECKOUT_OCCUPIED`) while `agent action review` warns when another actor works there.
- `.../review/prompt.md` (~:18): the reviewer-side sentence (do not edit files in a checkout another actor is implementing in; the warning names them).
- These prompts are SOURCE templates; never edit generated agent copies. Check `tests/` for prompt content/size snapshot tests (`grep -rl "mission-steps/software-dev/implement/prompt.md" tests | head`) and update them. Run the terminology guard: `.venv/bin/python -m pytest tests/architectural/test_no_legacy_terminology.py -q`. If any pack-manifest hash covers these files, run `spec-kitty doctrine regenerate-graph` and commit the regenerated manifest.

## Test Strategy

```bash
.venv/bin/python -m pytest tests/architectural/test_mission_write_discipline.py tests/architectural/test_status_events_writes_gate.py tests/architectural/test_no_legacy_terminology.py -q
.venv/bin/python -m pytest <prompt content tests found above> -q
make test-fast
```

## Definition of Done

- Gate green on the tree with empty allowlists; every synthetic/self-mutation case red.
- Prompts updated; prompt tests and terminology guard green.

## Review Guidance

- Try to dodge the gate (alias, getattr, lambda defined in a `with` but called later) — each must be caught or explicitly documented.

## Activity Log
