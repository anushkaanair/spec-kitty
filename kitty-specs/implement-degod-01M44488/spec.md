# Mission Specification: Implement command degod (tidy-first)

**Mission Branch**: `issue-5635-implement-degod`
**Created**: 2026-10-04
**Status**: Draft
**Input**: Operator brief (semi-automatic): deliver #5635 and #5232 as one tidy-first,
behaviour-preserving decomposition of the implement command. Remove the meta-derived
coordination fallback, move the tests onto the seams, and deliver as one PR on
spec-kitty/spec-kitty (milestone "4.0.0 release scope").

## Intent Summary (confirmed)

- **Primary actors:**
  - Spec Kitty maintainers who land the remaining milestone-11 fixes in the implement area,
    such as #5673, #5676 and #5669.
  - Operators and agents who run `spec-kitty implement WP##`, directly or through
    `spec-kitty agent action implement`.
- **Trigger:** the implement command file is a hotspot.
  - 2,304 lines; 53 commits in 90 days, 18 of them fixes.
  - 112 test patch sites reach into its internals.
  - Every fix in this area is costly to make and hard to pin with a test.
- **Desired outcome:** a thin command layer that only parses arguments and presents output,
  over an ordered sequence of implement phases.
  - Each phase's decisions live in the existing domain seams (workspace context, lanes,
    coordination, status, dependency graph), where a test can pin them without patching the
    command module.
  - The tests follow the code onto those seams.
- **Rule that must always hold:** an operator sees exactly the same behaviour before and after.
  - Same refusals, error codes, exit codes and console/JSON output, and the same commits and
    state files.
  - The one exception is #5232: the legacy meta-derived coordination fallback is replaced by a
    seam-owned placement resolution (see FR-008).
- **Discovery mode:** brief intake.
  - The operator's brief is comprehensive and asks for autonomous execution, stopping only on
    charter conflicts, real behaviour-change decisions, or a gate that cannot be kept green
    honestly.
  - The one design decision with behaviour impact (#5232 shape) is recorded as Decision Moment
    `01M4455PBFDASHQ7R9DN5ZQRMW`.
  - Grounding evidence is in [`research/code-grounding.md`](research/code-grounding.md) and
    [`research/test-remediation.md`](research/test-remediation.md). Every requirement below
    traces to a decision (D1–D10) in `code-grounding.md` §2.

## Domain Language

| Term | Meaning here | Do not confuse with |
|---|---|---|
| **implement phase** | One ordered step of `spec-kitty implement`: context, claim preflight and dependency gate, planning-artifact commit, bulk-edit gate and operational context, workspace/lane selection, allocate, record claim, present. | "Auto-rebase". It is **not** on this path (it lives in lane lifecycle sync and consolidation) and is out of scope. |
| **seam** | An existing package module that owns a domain decision: `workspace/context.py`, `lanes/implement_support.py`, `coordination/`, the status facade, `core/dependency_graph.py`. | A new package. None is introduced. |
| **legacy meta-derived fallback** (#5232) | The implement-local branch that derives the coordination branch from `meta.json` when the context placement ref fails to resolve. The implement code calls it the "C-004 strangler". | ADR `2026-06-24-1`'s C-004 ("the coordination-worktree mechanism stays"), and this spec's own constraint IDs. |
| **placement ref** | The single commit target that planning artifacts and status events resolve to (C-PLACE-1). | A branch name read directly from `meta.json`. |
| **patch site** | A test `patch`/`monkeypatch` that replaces a name in a module's namespace. | Patches of shared objects (`console.print`). |
| **routing** | Not used unqualified. Here it only ever means *placement* (which branch a planning artifact commits to). | Dispatch, model or event routing. |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A maintainer pins a fix in one phase without patching the command module (Priority: P1)

A maintainer picks up a milestone-11 bug in the implement area. #5673 is the example: the claim
commit sweeps the operator's uncommitted `.kittify/config.yaml`. They find the decision in its
seam module, change it there, and pin it with a seam unit test that needs neither the CLI nor a
dozen patches on the command module.

**Why this priority**: this is the reason for the mission. Later fixes in this area become
cheap to make and to pin.

**Independent Test**: for each phase, at least one seam unit test calls the phase's decision
directly with plain inputs and asserts its verdict or typed error, with no patch on the
implement command module.

**Acceptance Scenarios**:

1. **Given** the claim-commit path bundle, **When** a test calls the seam function with a
   feature dir, a WP file and a topology flag, **Then** it gets the exact list of paths the claim
   commit would stage, without running git or the CLI.
2. **Given** a reduced status snapshot in which a dependency is `planned`, **When** a test calls
   the dependency-gate decision, **Then** it raises the same `dependencies_not_satisfied: …`
   error the command raises today, with no git repository involved.
3. **Given** a list of dirty planning paths, **When** a test calls the planning-commit partition
   decision, **Then** it gets the same PRIMARY and coordination-residue groups the command commits
   today.

---

### User Story 2 - An operator sees no change when running implement (Priority: P1)

An operator runs `spec-kitty implement WP##` (or `agent action implement`) on any topology:
flat, `lanes`, coordination, `single_branch`. They get the same workspace, the same commits,
the same refusals, codes, exit codes and console/JSON output as before the decomposition.

**Why this priority**: a tidy-first refactor that changes behaviour is a regression.

**Independent Test**: a characterization suite lands before any code moves. It covers every
refusal family and the side-effect order, and stays green, unedited, through every later
work package.

**Acceptance Scenarios**:

1. **Given** a WP whose dependency is not yet approved, **When** the operator runs implement,
   **Then** the command exits 1 with the same `dependencies_not_satisfied` text. No worktree, VCS
   lock or status event is created.
2. **Given** a WP that has not been finalized, **When** the operator runs implement, **Then** the
   command exits 1 with "WP <id> is not finalized; run `spec-kitty agent mission finalize-tasks`".
3. **Given** a `single_branch` mission whose write checkout is on the wrong branch, occupied or
   dirty, **When** the operator runs implement, **Then** the same `WRITE_CHECKOUT_*` refusal is
   shown, and `meta.json` carries no `vcs` lock afterwards.
4. **Given** the workspace was created but starting the WP status fails, **When** the operator runs
   implement, **Then** the same "Workspace was created but starting the WP status failed" message
   is shown with exit 1.
5. **Given** `--json`, **When** implement succeeds or fails, **Then** stdout carries the same
   machine-readable payload shape as before.
6. **Given** `agent action implement` calls the command programmatically, **When** it omits
   optional keyword arguments, **Then** the call behaves as before (no `OptionInfo` leakage).

---

### User Story 3 - Planning-artifact placement always comes from the canonical seam (Priority: P2)

An operator claims a WP on a coordination-topology mission whose action context cannot be
resolved (for example an empty coordination branch or a topology mismatch). Today implement
silently falls back to a coordination branch read from `meta.json`, which can split planning
artifacts between the primary branch and the coordination branch. After this mission the
placement always comes from the placement seam. If the seam itself cannot resolve, the claim
fails closed with an actionable remedy (`spec-kitty doctor coordination --mission <slug> --fix`).

**Why this priority**: it closes #5232, a recorded split-brain risk, as one slice of the
refactor.

**Independent Test**: on real-git fixtures for each topology, the seam-resolved placement equals
today's context placement wherever the latter resolves. A mission whose placement cannot be
resolved is refused with `PlacementResolutionRequired` and the doctor remedy, and nothing is
committed.

**Acceptance Scenarios**:

1. **Given** a flat mission, **When** the operator claims a WP with dirty planning artifacts,
   **Then** they are committed to the planning branch exactly as today.
2. **Given** a coordination mission with dirty PRIMARY and coordination-residue artifacts,
   **When** the operator claims a WP, **Then** each group lands on the same branch as today.
3. **Given** a mission whose placement the seam cannot resolve, **When** the operator claims a WP,
   **Then** the claim exits 1 at the validate step with the doctor remedy, and no planning-artifact
   commit lands.

---

### Edge Cases

- **Exit codes before recover.** `--recover` without `--mission` still exits 2, and the
  `--mission` guard runs before recover mode.
- **Commit before late refusals.** The planning-artifact commit still runs before the bulk-edit,
  operational-context and checkout-identity refusals. This existing order is preserved and
  recorded as a follow-up, not changed.
- **Claim-commit exceptions.** The claim commit still re-raises `SafeCommitPathPolicyError`,
  `SafeCommitHeadMismatch` and `PlacementResolutionRequired`, and still downgrades any other
  failure to a warning with exit 0.
- **`--base` on a repository-root planning lane.** It stays a warned no-op. An unresolvable
  `--base` still prints the single canonical error and exits 1.
- **Coordination worktree not materialized.** The coordination branch exists but its worktree
  does not (fresh clone or CI). Behaviour is unchanged wherever today's flow already refuses
  earlier. Elsewhere the write-shaped seam composes the coordination ref instead of refusing.
- **Patch target moves.** A test patch whose target moved to a seam must fail loudly (attribute
  error or liveness gate), never pass silently.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Title | User Story | Priority | Status | Delivery | No-op passable? |
|----|-------|------------|----------|--------|----------|-----------------|
| FR-001 | Thin command layer | As a maintainer, I want the implement command module to hold only argument parsing, the JSON-safe output wrapper and presentation, so that orchestration and decisions can be read and tested elsewhere. The module contains no planning-commit, dependency-gate, lane-selection or claim-commit decision code. | High | Open | [build] | no — today all four live in the module |
| FR-002 | Ordered implement phases | As a maintainer, I want the implement flow expressed as named, ordered phase steps (context → claim preflight and dependency gate → planning-artifact commit → bulk-edit gate and operational context → workspace and lane selection → allocate → record claim → present), with today's side-effect order kept. | High | Open | [build] | no — paired with FR-009's phase-order characterization test |
| FR-003 | Dependency gate in the dependency-graph seam | As a maintainer, I want the claim-precondition decision (unseeded-WP rejection plus dependency readiness) to be a pure function in the dependency-graph seam. It takes a reduced status snapshot and raises the same exception types and messages as today. | High | Open | [build] | no — a seam unit test calls it without git |
| FR-004 | Planning-commit decisions in the coordination seam | As a maintainer, I want the planning-artifact commit decisions to live in the coordination seam beside the bookkeeping transaction and to return typed results or typed errors. That covers the PRIMARY/coordination-residue partition, the partition guard, the `meta.json` demotion predicate, the bookkeeping identifiers and the candidate-file enumeration. The command renders the identical text. | High | Open | [build] | no — seam unit tests call them directly |
| FR-005 | Lane selection in the lanes seam | As a maintainer, I want these to live in the lanes implement-support seam with typed errors: lane lookup from `lanes.json`, origin-preferred `--base` resolution, the repository-root write-checkout refusal, and the VCS lock preparation. | High | Open | [build] | no — seam unit tests call them directly |
| FR-006 | Workspace context reads in the workspace seam | As a maintainer, I want the WP-prompt-file lookup, the `lanes.json` directory and the target-branch reads used by implement to resolve through the workspace-context seam. | Medium | Open | [build] | no — seam unit tests call them directly |
| FR-007 | Claim recording through the status seam | As a maintainer, I want the claim policy metadata built through the status facade, and the claim-commit path bundle to be a pure, directly testable function. That makes the #5673 fix a one-line change. The propagate/soften exception contract of the claim commit stays exactly as today. | High | Open | [build] | no — table test over the exception contract plus a seam test of the bundle |
| FR-008 | Seam-owned planning placement (#5232) | As an operator, I want implement-claim to resolve planning-artifact placement through the placement seam in every case. If the seam cannot resolve, the claim fails closed with `PlacementResolutionRequired` and the doctor remedy, instead of falling back to a coordination branch read from `meta.json`. The optional placement parameter, the meta-derived arm and the legacy-fallback wording are removed. | High | Open | [build] | no — a fixture whose placement cannot resolve must refuse, and a flat/coordination fixture must still commit (same-fixture positive control) |
| FR-009 | Behaviour characterization first | As an operator, I want a characterization suite to land before any code moves and to stay green, with no assertion edited, through every later step. It pins every refusal family (text or code, exit code, no mutation), the side-effect order, the genesis rejection, the #4888 message, the claim-commit exception table, `--json` payloads, and the write-shaped versus read-shaped placement equality. | High | Open | [ratchet] | yes — the positive control is a planted break per family, proven red before the suite is accepted |
| FR-010 | Patch-liveness coverage | As a maintainer, I want the existing patch-target liveness gate widened to the implement command family before anything moves, so a patch left on a name that no longer dispatches through that module fails instead of passing silently. | High | Open | [build] | no — a planted dead patch must turn the gate red |
| FR-011 | Tests follow the code | As a maintainer, I want tests that string-patch implement internals moved onto the seams. Each test either calls the seam decision directly or patches the seam module that owns the name. I want the patch-site count into the implement namespace reported before and after, and at least one end-to-end smoke test kept per behaviour family. | High | Open | [build] | no — measured count must drop (SC-002) |
| FR-012 | Gates follow the code | As a maintainer, I want every architectural census or scan list that names the implement module to gain the module(s) the code moved to, every path or source-text pin re-pointed, and no gate loosened or newly added for size. | High | Open | [ratchet] | yes — positive control: each widened scan reports a non-zero contribution from the new module |
| FR-013 | Vacuous tests repaired | As a maintainer, I want the tests the grounding found vacuous fixed or retired. Each retirement names its covering guard, proven by a planted break. | Medium | Open | [build] | no — the planted break must turn the covering guard red |
| FR-014 | Programmatic call contract | As an agent, I want `agent action implement` to keep calling the implement command with an unchanged signature and decorators, so programmatic callers see no difference. | High | Open | [ratchet] | yes — positive control: the existing programmatic-call tests fail when an optional keyword default is changed |

### Non-Functional Requirements

| ID | Title | Requirement | Category | Priority | Status |
|----|-------|-------------|----------|----------|--------|
| NFR-001 | Complexity ceiling | Every function added or touched has cyclomatic complexity ≤ 15 (ruff C901); `implement()` drops below 15. | Maintainability | High | Open |
| NFR-002 | Strict typing | Every new or receiving module passes `mypy --strict` with 0 errors in the touched code. No module is added to the mypy quarantine, and the pre-existing quarantine of the implement module is not widened. | Maintainability | High | Open |
| NFR-003 | Fast feedback | The implement-direct regression subset (the command recorded in `research/test-remediation.md` §6, extended with the new seam tests) completes in ≤ 30 s with `-n auto --dist loadfile`. Baseline: 18.3 s. | Performance | Medium | Open |
| NFR-004 | Lint and format clean | `ruff check` and `ruff format --check --force-exclude` report 0 issues on every changed file, and no new `noqa` or `type: ignore` is added without an inline rationale. | Maintainability | High | Open |
| NFR-005 | Reviewable slices | Each work package's diff is reviewable on its own: one phase extraction or one test-migration batch, with code moves in commits separate from caller adjustments. | Process | Medium | Open |

### Constraints

| ID | Title | Constraint | Category | Priority | Status |
|----|-------|------------|----------|----------|--------|
| C-001 | Behaviour preserved | No change to refusal texts, error codes, exit codes, console or JSON output, commits or state files, except the FR-008 placement change. | Technical | High | Open |
| C-002 | Move, then adjust | Code is moved verbatim first and callers are adjusted second. Logic is never edited inside a move. | Process | High | Open |
| C-003 | No new size or ratchet gates | Operator ruling: refactoring is engineering discipline, not a gate. Existing gates are widened or re-pointed, never loosened. | Process | High | Open |
| C-004 | Existing seams only | Decisions move into existing packages. No new top-level package, and no module is converted into a package. Lower packages (`lanes`, `workspace`, `coordination`, `status`, `core`) never import the CLI layer. They return typed results or raise typed errors, and only the CLI prints. | Technical | High | Open |
| C-005 | Scope boundary | Out of scope: the #5673 and #5676 fixes, #5669, #3931, the move-task seam modules, `core/mission_creation.py` (sibling mission #5634), auto-rebase, and a shared implement application service. | Business | High | Open |
| C-006 | Recognized raise sites stay | The `WRITE_CHECKOUT_*`, `MissingLanesError`, `DESTROYED_LANE` and `LANE_WORK_TIP_UNKNOWN` raise sites already live in the lanes package and are not moved or reworded. | Technical | Medium | Open |
| C-007 | Escalation | A characterization test proving the write-shaped placement diverges from today's placement in a reachable case stops the mission for an operator decision. | Process | High | Open |
| C-008 | Traceability | Every commit carries `Co-Authored-By: Stijn Dejongh <stijn.dejongh@sddevelopment.be>`. No AI model identifier appears in commits or the PR. The operator merges. | Process | High | Open |

### Key Entities

- **Implement phase**: one ordered step of the implement flow. It consumes the previous phase's
  result and either produces its own result or raises a typed refusal.
- **Seam decision**: a pure function in an existing seam module that returns a verdict or raises a
  typed error. Its effect adapter performs the I/O; the command renders the outcome.
- **Placement ref**: the single commit target for planning artifacts and status events, resolved
  by the placement seam.
- **Patch site**: one test replacement of a module-namespace name. It is counted to measure how
  tightly tests couple to internals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The implement command module shrinks from 2,304 lines to at most 800, and contains
  only argument parsing, the output wrapper, presentation and the phase sequence. — [build] · no-op passable: no
- **SC-002**: Test patch sites into the implement command namespace drop from 112 (94 string + 18
  object) by at least 60%, to at most 45, measured with the recorded commands. — [build] · no-op passable: no
- **SC-003**: The characterization suite (FR-009) is green on the base commit and on the final
  commit, with zero assertions edited in between. — [ratchet] · no-op passable: yes — positive control: planted breaks per refusal family
- **SC-004**: No code path in the implement flow derives a coordination branch from `meta.json`,
  and #5232 is closed by the PR. — [build] · no-op passable: no
- **SC-005**: Every implement phase has at least one seam unit test that exercises its decision
  without the CLI and without patching the implement command module. — [build] · no-op passable: no

## Assumptions

- Under the write-shaped placement seam, a flat mission resolves to its target branch and a
  coordination mission to its coordination ref, matching `mission_record_analysis` (#5113). The
  FR-009 equality test verifies this before FR-008 lands (see C-007).
- The pre-existing red `test_commit_recipes.py::test_no_unallowed_git_commit_recipe_strings_in_src`
  (#5699, nightly P0) is unrelated and stays red. It is not chased here.
- Follow-ups are filed rather than folded:
  - the planning-artifact commit lands before late validation;
  - the misleading "not finalized" refusal for an unmaterialized coordination worktree;
  - a shared implement application service (needs an ADR).
