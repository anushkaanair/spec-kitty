# Implementation Plan: Issue-Matrix Partition Read Integrity & Merge Verdict-Terminality

**Branch**: `claude/spec-kitty-ci-failures-r0xui3` | **Date**: 2026-09-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `kitty-specs/issue-matrix-partition-integrity-01M3H10A/spec.md`

## Summary

Every issue-matrix consumer must resolve the artifact's owning partition before reading it,
and merge must enforce the terminal-verdict rule. The placement seam
(`src/mission_runtime/resolution.py` — `PlacementSeam.read_dir`, `resolve_artifact_surface`,
`coord_read_dir_for`) is the canonical resolver and is already correctly adopted by
`src/specify_cli/status/doctor.py::check_issue_matrix` (discovery from PRIMARY, verdicts from
COORD). This mission (a) adopts that same two-partition split at the two straggler consumers —
the mission-review issue-matrix gate and the merge issue-matrix completeness gate; (b) adds a
NEW coordination-branch-ref read primitive so authored verdicts remain readable after the coord
worktree is consolidated away (branch retained); and (c) makes merge apply the
`in-mission -> done` terminal-verdict rule that today lives only in `move-task`. Approach and
call sites were confirmed against live code by the pre-spec analysis squad.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: typer + rich (CLI), ruamel.yaml (frontmatter), `git` via subprocess (branch-ref reads: `git rev-parse --verify`, `git show <ref>:<path>` / `cat-file`), the placement seam in `src/mission_runtime/`, `spec_kitty_events` / `spec_kitty_tracker` (public imports only)
**Storage**: git — coordination branch refs, `status.events.jsonl`, and `issue-matrix.json`/`.md` on the primary and coordination partitions; no database
**Testing**: pytest (fast/unit + integration + architectural). ATDD red-first through the real production entry points (mission-review gate, merge gate, rendered doctrine); every refusal/absence assertion paired with a same-fixture positive control; coord-vs-flat topology fixtures; compound fixes proven half-by-half
**Target Platform**: cross-platform CLI (Linux, macOS, Windows 10+)
**Project Type**: single project (this repository)
**Performance Goals**: mission-review and merge gate evaluation < 2s on the NFR-003 fixture (10 gating issues / 25 matrix rows); branch-ref read adds no measurable overhead vs the worktree read on the same fixture
**Constraints**: single canonical authority (reuse the seam; the new branch-ref primitive lives in `src/mission_runtime/`, never in the CLI adapter); respect the enforced import chain `kernel <- charter <- {glossary, runtime, mission_runtime} <- specify_cli` (no new outbound edges); fail-closed on ambiguity/probe error; terminology canon (Mission, canonical verdict vocabulary); complexity ceiling 15 (extract helpers)
**Scale/Scope**: bounded bug-fix touching ~6 source modules + one doctrine SKILL (+ regenerated agent copies) + a new architectural guard + targeted tests

## Charter Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **Single canonical authority (PASS)**: No second partition-resolution authority is introduced.
  FR-001–FR-004 adopt the existing `PlacementSeam`/`coord_read_dir_for`; the new branch-ref read
  (FR-005) is added *inside* the seam's owning module (`src/mission_runtime/resolution.py`) as a
  layered primitive, not a parallel resolver in `specify_cli`.
- **Architectural alignment / layer rules (PASS)**: Consumers in `specify_cli` already import the
  seam from `mission_runtime` (a permitted edge). No new outbound module edges; the
  `landscape`/`LayerRule` fixtures stay satisfied. Verified by `tests/architectural/test_layer_rules.py`.
- **ATDD-first (PASS, enforced in tasks)**: Each WP ships a failing-first test committed before the
  fix; reviewer verifies RED on base / GREEN on final. C-003 in the spec binds this.
- **Terminology canon (PASS)**: New prose/doctrine uses "Mission" and the canonical verdict set.
  Run `pytest tests/architectural/test_no_legacy_terminology.py` before pushing doctrine/prose.
- **Boy-Scout vs locality (PASS)**: Scope is bounded to the issue-matrix kind and its named
  consumers; opportunistic cleanup limited to the touched functions (e.g. keeping `merge_gates.py`
  functions ≤ complexity 15 when the signature changes force a touch).
- **Test policy (PASS)**: Blast radius targeted (see Project Structure → Tests); no whole-repo run.

No charter violations requiring Complexity Tracking.

## Project Structure

### Documentation (this mission)

```
kitty-specs/issue-matrix-partition-integrity-01M3H10A/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (behavioral contracts, not HTTP)
├── traces/              # tooling-friction / approach / design-decisions tracers
└── tasks.md             # Phase 2 output (/spec-kitty.tasks — NOT created here)
```

### Source Code (repository root)

```
src/mission_runtime/
├── resolution.py         # PlacementSeam.read_dir, resolve_artifact_surface, coord_read_dir_for
│                         #   + NEW: coordination-branch-ref read authority (FR-005/FR-007)
└── artifacts.py          # ISSUE_MATRIX kind classification (reference only; unchanged)

src/specify_cli/
├── status/doctor.py                      # check_issue_matrix — REFERENCE two-partition split pattern
├── cli/commands/review/__init__.py       # _evaluate_issue_matrix — separate discovery/matrix reads (FR-001)
├── cli/commands/review/_issue_matrix.py  # validate_issue_matrix / matrix load (FR-001 read side)
├── policy/merge_gates.py                 # _evaluate_issue_matrix_completeness_gate (FR-003/FR-004/FR-006)
├── merge/executor.py                     # threads repo_root/mission_slug into evaluate_merge_gates (FR-003)
├── merge/done_bookkeeping.py             # _mark_wp_merged_done / _record_merged_wps_done_for_merge (FR-006)
├── tasks/issue_reference_discovery.py    # gating_issue_numbers — PRIMARY discovery (reference)
├── tasks/issue_matrix_migration.py       # load_issue_matrix / issue_matrix_artifact_present (read side)
└── cli/commands/agent/tasks_move_task.py # _issue_matrix_approval_blocker — REFERENCE terminal-verdict rule (FR-006)

src/charter/offering/skills/spec-kitty-mission-review/SKILL.md   # Gate-4 doctrine: resolver-backed read (FR-002)
# regenerated agent copies (.claude/, .agents/skills/, ...) via `spec-kitty upgrade` — never hand-edited

tests/
├── architectural/        # NEW guard: no raw issue-matrix path reads in review/merge consumers (FR-008); layer rules
├── policy/               # merge_gates coord-vs-flat fixtures (FR-003/FR-004/FR-006)
├── specify_cli/cli/commands/review/  # mission-review gate partition + doctrine-render tests (FR-001/FR-002)
├── mission_runtime/ (or tests/unit/) # branch-ref read authority unit + fail-closed tests (FR-005/FR-007)
└── integration/          # post-consolidation e2e: coord worktree torn down, branch retained (FR-005/FR-006)
```

**Structure Decision**: Single-project layout. The new primitive lands in `src/mission_runtime/`
(seam owner); all consumer edits are in `src/specify_cli/`; the doctrine fix is in
`src/charter/offering/skills/` with agent copies regenerated by `spec-kitty upgrade`.

## Implementation Concern Map

> Concerns are NOT work packages. `/spec-kitty.tasks` translates these into WPs.

### IC-01 — Coordination-branch-ref read authority (the deep primitive)

- **Purpose**: Resolve issue-matrix (ISSUE_MATRIX) content from the coordination branch ref when
  the coordination worktree is unmaterialized but the branch is retained (post-consolidation), so
  authored verdicts stay readable; fail closed on a deleted ref, a probe error, or an empty
  authored set while gating references exist.
- **Relevant requirements**: FR-005, FR-007, NFR-002, NFR-003.
- **Affected surfaces**: `src/mission_runtime/resolution.py` (new read authority layered on
  `resolve_artifact_surface`/`read_dir`); git probes (`git rev-parse --verify`, `git show <ref>:<path>`).
- **Sequencing/depends-on**: none (foundational; IC-02 and IC-03 consume it).
- **Risks**: distinguishing deleted (ref absent) from unmaterialized (ref present) deterministically;
  keeping the read fail-closed without swallowing probe errors; git-probe latency (NFR-003).

### IC-02 — Mission-review issue-matrix gate partition split (#5171)

- **Purpose**: Make the mission-review Gate 4 read gating references from PRIMARY and authored
  verdicts from COORD (via IC-01), and replace the doctrine's raw `cat` with a resolver-backed read.
- **Relevant requirements**: FR-001, FR-002, FR-008.
- **Affected surfaces**: `src/specify_cli/cli/commands/review/__init__.py` (`_evaluate_issue_matrix` —
  separate the two partition reads instead of one `feature_dir`), `review/_issue_matrix.py` (matrix
  load), `src/charter/offering/skills/spec-kitty-mission-review/SKILL.md` (Gate-4 step), regenerated
  agent copies.
- **Sequencing/depends-on**: IC-01 (for the post-consolidation read).
- **Risks**: the current partial fix (`coord_read_dir_for(...) or feature_dir`) conflates the two
  reads — must fully separate discovery vs matrix; doctrine change must be a positive read, not a
  deletion (FR-002 positive control).

### IC-03 — Merge issue-matrix completeness gate partition split (#4943 leg 1)

- **Purpose**: Give `_evaluate_issue_matrix_completeness_gate` `repo_root`/`mission_slug`, discover
  references from the PRIMARY spec dir (via the seam, as risk/dependency gates already do per #3439),
  and read verdicts from COORD (via IC-01), so coord missions are enforced identically to lanes.
- **Relevant requirements**: FR-003, FR-004.
- **Affected surfaces**: `src/specify_cli/policy/merge_gates.py`, `src/specify_cli/merge/executor.py`
  (caller threads the args, already available on `evaluate_merge_gates`).
- **Sequencing/depends-on**: IC-01.
- **Risks**: fail-open is the worse mode — a missing row must FAIL, never vacuously PASS; keep the
  function ≤ complexity 15 when the signature grows (extract a helper).

### IC-04 — Merge terminal-verdict enforcement (#4943 leg 2)

- **Purpose**: Make merge apply the same `in-mission`/`unknown` -> `done` rejection `move-task`
  applies: refuse in `block` mode (naming rows) before the target advances; warn with the same list
  in `warn` mode (which still advances/records done).
- **Relevant requirements**: FR-006.
- **Affected surfaces**: `src/specify_cli/policy/merge_gates.py` (verdict check), the merge
  done-recording path `src/specify_cli/merge/done_bookkeeping.py`; mirrors
  `tasks_move_task.py::_issue_matrix_approval_blocker` (reference rule, not re-invented).
- **Sequencing/depends-on**: IC-01, IC-03 (shares the coord verdict read).
- **Risks**: warn vs block semantics must match existing `merge_gates.mode` conventions; must read
  verdicts from the correct partition (else re-introduces the bug it fixes).

### IC-05 — Regression guard + test-remediation

- **Purpose**: A non-vacuous architectural guard that trips if any review/merge consumer reconstructs
  a topology-dependent `issue-matrix` path by hand; re-judge and correct any existing test that pins
  the husk/residue read.
- **Relevant requirements**: FR-008, NFR-001, C-005.
- **Affected surfaces**: `tests/architectural/` (new guard with a self-mutation check),
  `tests/policy/`, `tests/specify_cli/cli/commands/review/` (re-judge buggy-behavior pins).
- **Sequencing/depends-on**: IC-02, IC-03, IC-04 (guards their result).
- **Risks**: guard must be non-vacuous (injecting a raw read must trip it); do not green-wash a test
  that asserts the old wrong-partition behavior — correct it.
