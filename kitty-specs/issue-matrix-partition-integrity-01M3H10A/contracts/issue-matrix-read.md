# Contract: Coordination-aware issue-matrix read

Behavioral contract (not HTTP) for the read authority that every issue-matrix consumer routes
through. Backed by ATDD tests; each MUST-clause names its witnessing scenario.

## Inputs

- `repo_root`, `mission_slug`
- `kind = MissionArtifactKind.ISSUE_MATRIX`
- topology (from `meta.json`), coordination branch name (when applicable)

## Guarantees

1. **Discovery/verdict partition split** — reference discovery reads the PRIMARY partition; matrix
   verdicts read the matrix's owning partition. On coord topology the two are different directories.
   *(FR-001, FR-003, FR-004; witnessed: US1.1/1.3, US2.1/2.2/2.3/2.4)*
2. **Branch-flat unchanged** — on single_branch/lanes the matrix resolves to PRIMARY; behavior is
   byte-for-byte identical to today. *(US1.3, US2.4 parity)*
3. **Post-consolidation branch-ref read** — when the coordination branch ref resolves
   (`git rev-parse --verify`) but its worktree is absent, matrix content is read from the branch ref
   (`git show <ref>:<path>`). *(FR-005; witnessed: US4.1, US4.2)*
4. **Fail closed** — the read REFUSES (raises / returns a typed refusal), never falling back to
   PRIMARY residue or passing vacuously, when:
   - the coordination ref is absent (deleted) — *US4.3*;
   - the content probe errors — *US4.5 negative*;
   - the authored set is empty while gating references exist — *US4.4 negative*.
   *(FR-007, NFR-002)*
5. **Positive controls** — for each refusal clause a same-fixture positive assertion proves the read
   returns the verdict when present (non-empty set → resolves; probe ok → reads `fixed`). *(US4.4/4.5)*
6. **Performance** — resolution completes within the CLI <2s bar on the NFR-003 fixture (10 issues /
   25 rows); the branch-ref read adds no measurable overhead vs the worktree read. *(NFR-003)*

## Non-goals

- No second resolver authority; extends the existing seam in `src/mission_runtime/resolution.py`.
- No change to verdict semantics or the canonical verdict vocabulary.
