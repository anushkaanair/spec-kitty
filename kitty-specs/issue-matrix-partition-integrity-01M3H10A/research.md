# Research: Issue-Matrix Partition Read Integrity & Merge Verdict-Terminality

**Phase 0** — all decisions grounded in live-code findings from the pre-spec analysis squad
(root-cause, architecture-alignment, foldable-issues lenses) and the operator's recorded
architecture decisions. No open `NEEDS CLARIFICATION` markers.

## D1 — Reuse the placement seam; do not add a second resolver

- **Decision**: Adopt the existing `PlacementSeam.read_dir` / `resolve_artifact_surface` /
  `coord_read_dir_for` (`src/mission_runtime/resolution.py`) at the two straggler consumers,
  mirroring the healthy pattern in `src/specify_cli/status/doctor.py::check_issue_matrix`
  (discovery from PRIMARY `feature_dir`, verdicts from the COORD dir).
- **Rationale**: Charter single-canonical-authority; `test_read_surface_placement_guard.py`
  declares `read_dir` the one blessed read entry point (~40+ call sites). A second helper would
  breach DIRECTIVE_044 and re-institutionalize the parallel-surface split the bug represents.
- **Alternatives considered**: a bespoke per-gate resolver (rejected — second authority); a
  narrow #5171-only wiring fix (rejected by operator — leaves #4943 live and divergent).

## D2 — Coordination-branch-ref read is a NEW primitive (the deep fix)

- **Decision**: Add a read authority in `src/mission_runtime/resolution.py` that resolves
  ISSUE_MATRIX content from the coordination **branch ref** (`git show <ref>:<path>`) when the
  worktree is unmaterialized-but-retained.
- **Rationale**: `coord_read_dir_for` fail-softs to `None` when the coord worktree is gone
  (post-consolidation) — `resolve_artifact_surface` stamps PRIMARY for EMPTY/UNMATERIALIZED and
  absorbs DELETED — so even the "already partition-aware" review CLI reproduces #5171's residue read
  post-merge. No existing primitive reads blob content off a ref (grep of `mission_runtime` found
  only branch-*name*/topology resolution). This is `[build]`, not adoption.
- **Alternatives considered**: require `--retain-worktrees` so the worktree survives (rejected —
  changes user workflow, doesn't close the class); materialize a throwaway worktree at read time
  (rejected — slow, side-effecting, violates the <2s bar).

## D3 — Merge mirrors move-task's terminal-verdict rule

- **Decision**: Merge applies the `in-mission`/`unknown` -> `done` rejection that
  `tasks_move_task.py::_issue_matrix_approval_blocker` already implements: `block` refuses before
  the target advances (naming rows); `warn` advances/records `done` but prints the same list.
- **Rationale**: #4943 leg 2 — merge records `done` directly via
  `merge/done_bookkeeping.py::_mark_wp_merged_done`, bypassing the only enforcement point. Reuse the
  existing rule (single authority), do not re-define verdict semantics.
- **Alternatives considered**: route merge's done-recording through `move-task` (rejected — large
  behavioral coupling, out of scope); block on `warn` too (rejected — contradicts existing
  `merge_gates.mode` conventions).

## D4 — Deterministic deleted-vs-unmaterialized boundary; fail closed

- **Decision**: Distinguish states by `git rev-parse --verify refs/heads/<coordination_branch>`:
  ref present + no worktree ⇒ read from ref (D2); ref absent ⇒ deleted, fail closed; ref present but
  content probe errors ⇒ fail closed on a distinct path; empty authored set with live references ⇒
  fail closed (never "nothing to enforce").
- **Rationale**: Avoids conflating "deleted" with a transient probe error (both refuse, but for
  different, separately-tested reasons). Fail-open is the worse failure mode (vacuous PASS), so every
  ambiguity resolves to refusal (NFR-002).
- **Alternatives considered**: catch-all exception → "deleted" (rejected — hides probe errors and
  produces a misleading diagnostic).

## D5 — Non-vacuous regression guard

- **Decision**: A `tests/architectural/` guard asserts no mission-review doctrine step or review/merge
  gate consumer reconstructs a topology-dependent `issue-matrix` path by hand; it carries a
  self-mutation check (inject a raw read → guard trips).
- **Rationale**: DIRECTIVE_043 close-defect-class-by-construction; NFR-001 count = 0. Prevents the
  improvised-path regression re-entering doctrine or code.

## Adversarial evidence (post-spec squad dispositions)

Per `contracts/adversarial-evidence-contract.md`, no contested finding silently dropped:

| Finding | Disposition |
|---------|-------------|
| Testability M1 — merge fixture not partition-discriminating | **changed** — US2 seeded with divergent primary/coord + inverted mirror |
| Testability M2 — FR-007 refusal legs not decomposed / unpaired | **changed** — US4 scenarios 4/5 add empty-set + probe-error, each same-fixture paired |
| Testability M3 — deep read/terminality witnessed only via review | **changed** — US4 scenario 2 + US3 bound to coord post-consolidation exercise the merge path |
| Testability M4 — FR-002 witnessed only by absence guard | **changed** — FR-002 gains a positive control (rendered doctrine references the resolver) |
| Testability m5 — corrected-behavior FRs mislabeled `[ratchet]` | **changed** — relabelled `[build]` (FR-001/003/004, SC-001/002) |
| Testability m6 — NFR-003 threshold unmeasurable | **changed** — pinned fixture (10 issues / 25 rows) |
| Scope M1 — "not a new-primitive" over-broad | **changed** — Assumptions scoped; FR-005 called out as new |
| Scope M2 — deleted-vs-unmaterialized signal unnamed | **changed** — `git rev-parse --verify` named (D4) |
| Scope M3 — warn-vs-block semantics ambiguous | **changed** — US3 scenario 2 states warn still records done |
| Scope m1 — "husk" not in Key Entities | **changed** — added to Coordination partition entity |

## Supply-chain security (advisory)

No new third-party dependencies are added. The branch-ref read uses `git` via subprocess, the same
mechanism already used across the merge/lanes code; no new registry, lifecycle scripts, or package
pins are introduced. No supply-chain surface to review for this mission.
