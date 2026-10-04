# Research: Implement command degod (tidy-first)

Phase 0 output. The pre-spec grounding lives in [`research/code-grounding.md`](research/code-grounding.md)
(decisions D1–D10) and [`research/test-remediation.md`](research/test-remediation.md). This file adds
the plan-time decisions and records the disposition of every squad finding (adversarial-squad
findings-disposition contract: accepted, changed, or deferred with rationale; none dropped).

## Decisions

### R-1 — #5232 placement: which seam query, which surviving arm

R1_PLACEHOLDER

### R-2 — Where the phase sequence lives

- **Decision**: `cli/commands/implement_phases.py`, a sibling inside the command package.
- **Rationale**: the phase sequence drives the `StepTracker` and the per-step exception rendering,
  which are CLI concerns. Putting it in a lower package would import the CLI upward (C-004).
  `runtime.next` must not import the CLI layer either.
- **Alternatives considered**: a new `specify_cli/implement/` application service shared with
  `agent action implement` and `orchestrator_api` (rejected for this mission: it is a new package and
  needs an ADR; filed as a follow-up). Keeping the sequence inside `implement.py` (rejected: SC-001,
  FR-001).

### R-3 — Re-export policy for moved names

- **Decision**: a moved name loses its re-export from `implement.py` in the same WP, unless
  production code imports it from there. Today that is only `implement` itself
  (`cli/commands/__init__.py`, `agent/workflow.py`). Tests are re-pointed.
- **Rationale**: a re-export keeps a stale `patch("…implement.X")` silently non-intercepting
  (test-remediation §2c). Deleting the re-export turns it into an `AttributeError`, and the widened
  liveness gate catches the rest.
- **Alternatives considered**: identity re-exports (#5650/#5679 precedent). Rejected: in this file
  they would mask about 100 patch sites, and `test_no_dead_symbols` counts a re-export as a caller.
  The existing `implement_cores` shim block is reduced in the same way as its names stop being used
  from `implement`.

### R-4 — Claim-policy-metadata dedupe home

- **Decision**: one `claim_policy_metadata(shell_pid, agent)` exported by the status facade next to
  `build_claim_policy_metadata`, importing `core.process_liveness` lazily. `implement` and
  `agent/workflow_executor.py` both call it.
- **Rationale**: the two bodies are semantically identical today (workflow_executor.py:92–117 and
  implement.py:1812–1830). The status facade is importable from both callers without a layer break.
- **Alternatives considered**: `core/process_liveness.py` (rejected: it would import status upward
  in the core-to-status direction for a status-owned key layout). Keeping both copies (rejected: the
  single-authority principle; the copies are documented duplicates).

### R-5 — Characterization without patching the implement namespace

- **Decision**: the FR-009 suite runs `implement` through `typer.testing.CliRunner` and calls the
  command function directly on real-git fixtures, built with the helpers the existing integration
  tests use (`tests/specify_cli/cli/commands/test_single_branch_implement_refusals.py`,
  `tests/integration/test_wp_integrity_*`). Failure injection patches only the *external* owner
  module of a collaborator (for example `specify_cli.status.work_package_lifecycle`), never
  `specify_cli.cli.commands.implement*`.
- **Rationale**: FR-009 / SC-003 require zero assertion edits across the moves, so the suite cannot
  depend on names that move.

### R-6 — Census-scan widening proof

- **Decision**: each widened scan list (FR-012) is proven by temporarily planting a violation in the
  new module and running that gate red, then removing the plant. The plant is never committed; the
  command and the red output are recorded in the WP review notes.

## Squad finding dispositions

### Pre-spec grounding squad (4 lenses)

All findings are dispositioned in `research/code-grounding.md` §2 (D1–D10) and §1.6 (related issues).
Disposition summary:
- **Accepted:** auto-rebase dropped, liveness gate first, scan widening, source-pin re-pointing,
  mypy strictness on moved code, out-of-matrix local runs, #5673 shaping, #5676 out of scope.
- **Deferred with follow-up issues:**
  - the planning commit runs before late validation;
  - the misleading "not finalized" message for an unmaterialized coordination worktree;
  - a shared implement application service.

### Post-specify squad

| Finding (lens) | Disposition |
|---|---|
| FR-009 frozen suite vs FR-008 change (renata, HIGH) | **Changed**: FR-015 added. Placement outcomes are pinned red-first outside FR-009's frozen set. |
| US3-3 refusal phase (renata, HIGH) | **Changed**: the scenario names the planning-commit phase inside the `validate` tracker step. |
| SC-004 forbids identity reads (renata + alphonso, HIGH) | **Changed**: SC-004 is scoped to commit destinations and placement refs. The identity tuple, mid8, the legacy console line and the demotion guard are kept. |
| SC-002 gameable or unmeasurable (renata + alphonso, HIGH/MED) | **Changed**: family-wide count with a committed counter script. Console couplings and private imports are reported. |
| `mission_record_analysis` kind is PRIMARY (alphonso, HIGH) | **Changed**: the assumption is corrected, and the kind choice moved to R-1 / FR-015. |
| C-007 domain too narrow, no lifecycle axis (alphonso, HIGH) | **Changed**: C-007 covers any reachable outcome change. FR-015 covers topology × lifecycle phase. |
| FR-001 vs SC-001 phase-sequence home (both, MED) | **Changed**: FR-001 names the sibling adapters; SC-001 states `wc -l` and a per-sibling cap. |
| FR-002 no-op passable (renata, MED) | **Changed**: own check, a phase-call-order test. |
| C-002 vs mypy fixes and re-export deletion (renata, MED) | **Changed**: the adjust commit may carry typing-only fixes and re-export deletion. |
| NFR-002 quarantine and pre-existing errors (renata, MED) | **Changed**: quarantine entry rule stated; `dependency_graph.py` errors fixed in passing. |
| FR-010 baseline (renata, MED) | **Changed**: the unresolvable baseline is not raised, and dead patches are fixed. |
| FR-012 positive control and checklist (renata, MED) | **Changed**: planted-violation control, checklist cited, floor re-calibration sanctioned with proof. |
| FR-013 not enumerated (renata, MED) | **Changed**: the four tests are named. |
| Missing docs, changelog, tracker, dead helper, out-of-matrix runs (renata, MED) | **Changed**: FR-016, FR-017, FR-018 and NFR-006 added. Format-exclude rule added to NFR-004. |
| FR-009 must not patch the implement namespace (renata, MED) | **Changed**: stated in FR-009, and R-5 here. |
| NFR-005 not measurable (renata, LOW) | **Changed**: move commits shown with `--color-moved`, listed in the PR. |
| FR-007 mixes ratchet and build (renata, LOW) | **Changed**: the exception table moved into FR-009; FR-007 is build-only. |
| FR-014 decorators (renata, LOW) | **Changed**: decorators and option defaults named. |
| C-008 vs tool attribution trailer (renata, LOW) | **Changed**: C-008 states that the operator rule overrides the default trailer. |
| Legacy console line removal (alphonso, MED) | **Changed**: only docstrings and comments lose the C-004 wording; the console line is kept. |
| "Collapses to two arms (flat: single)" contradicts code (alphonso, MED) | **Changed**: the surviving arm structure is decided by R-1, not assumed. |
| Partition-call floor would drop (alphonso, MED) | **Changed**: FR-012 sanctions re-calibration with rationale and planted break. |
| FR-007 upward import of the status-artifact collector (alphonso, MED) | **Changed**: the bundle stays in the command package (`implement_claim.py`). The metadata half is a dedupe (R-4). |
| D4 re-export rule missing (alphonso, MED) | **Changed**: FR-011 states the rule (R-3). |
| FR-003 single-authority tension with `dependency_verdict` (alphonso, LOW) | **Deferred**: pinned, not deduplicated, in this mission. Dedupe recorded as part of the shared-service follow-up. |
| FR-004 only pure decisions move (alphonso, LOW) | **Accepted**: the contract lists exactly which functions move and which stay in the adapter. |
| FR-006 `__all__` and allow-list (alphonso, LOW) | **Accepted**: FR-006 and the contract name both. |
| Recover mode, console singleton, #3371 e2e (alphonso, LOW) | **Accepted**: spec edge cases added. |
