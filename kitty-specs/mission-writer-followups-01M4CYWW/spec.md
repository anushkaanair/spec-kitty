# Mission Specification: Every Mission-file writer takes the lock, and the runtime never cuts a log it cannot prove is its own

**Mission Branch**: `issue-5883-mission-writer-followups`
**Created**: 2026-10-08
**Status**: Draft
**Input**: Operator brief (2026-10-08): follow-ups to PR #5890 (Mission `concurrent-mission-writers-01M4BT23`), issues #5883, #5884 and #5885, starting from that PR's branch. A research squad (alignment and brownfield lenses) confirmed all three are still real on that branch and on `main`.

## Purpose

PR #5890 gave Mission files one write lock and one verified rollback, and an architectural gate that keeps unlocked read-modify-writes and blind truncates out. Its scout left three things open. First, more Mission-file writers still read a file and write it back without the lock (`meta.json` setters, work-package frontmatter writers in `map-requirements` and `finalize-tasks`, the issue-matrix scaffold), and the gate documents three shapes it does not catch. Second, the runtime rolls its own run log (`run.events.jsonl`) and `state.json` back with the same unverified truncate the status log used to have, and two `spec-kitty next` processes on one Mission can reach it. Third, running that Mission through the CLI surfaced planning friction: generated commits say "feature" where the domain object is a Mission, and `implement` refuses on an analyze step that neither the tasks prompts nor `spec-kitty next` ever offers. This Mission closes all three so parallel agents never lose a write and the planning flow names every step it will enforce.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Two writers to one `meta.json` both land (Priority: P1)

Agent A runs `spec-kitty implement WP01`, which records the Mission's VCS lock in `meta.json` under the Mission lock. At the same moment agent B binds a tracker ticket to the Mission (or `finalize-tasks` records the target branch, or `accept` restamps acceptance fields, or a Mission is reopened or discarded).

**Why this priority**: the unlocked setter reads `meta.json`, the locked write lands, then the unlocked write puts the stale copy back. One of the two fields silently disappears and both commands exit 0 (#5883).

**Independent Test**: pause writer B after it read `meta.json`, let writer A finish, resume B; both fields are present afterwards.

**Acceptance Scenarios**:

1. **Given** writer B has read `meta.json` and is paused, **When** writer A writes another field under the Mission lock and B resumes, **Then** `meta.json` contains both A's and B's fields.
2. **Given** a setter is called from a command that already holds the Mission lock on the same thread, **When** it runs, **Then** it does not deadlock and still writes.

### User Story 2 - Concurrent work-package frontmatter writers keep each other's changes (Priority: P1)

Two agents map requirement refs onto the same work package (`agent tasks map-requirements`, union mode), or one agent runs `finalize-tasks` while another adds a history note to a work package.

**Why this priority**: each reads the frontmatter, holds it in memory for a while (finalize runs all its ownership checks in between) and writes the whole file back, erasing the other writer's change (#5883).

**Independent Test**: pause the first writer after its read, let the second finish, resume; both changes are present.

**Acceptance Scenarios**:

1. **Given** two `map-requirements` runs add different refs to one work package, **When** they overlap, **Then** both refs are in the frontmatter.
2. **Given** `finalize-tasks` has read the work-package frontmatter and is paused, **When** `add-history` adds a note and finalize resumes, **Then** the note survives finalize's write.

### User Story 3 - The issue-matrix scaffold never overwrites a recorded verdict (Priority: P2)

`finalize-tasks` scaffolds the issue matrix while another agent records an issue verdict that creates the matrix.

**Why this priority**: the scaffold checks that the file is missing and then writes the whole map; a verdict recorded in between is overwritten. Rare, but silent (#5883).

**Independent Test**: pause the scaffold after its existence check, record a verdict, resume; the verdict row is still present.

**Acceptance Scenarios**:

1. **Given** the scaffold saw no matrix and is paused, **When** a verdict creates the matrix and the scaffold resumes, **Then** the matrix still holds the verdict row.

### User Story 4 - The gate catches the three shapes it used to document (Priority: P2)

A contributor adds a writer that (a) passes a callable into the Mission-lock block that is stored and run after the lock is released, (b) keys the Mission lock on a subscript such as `meta["mission_slug"]`, or (c) truncates a status or run log through `open(..., "w")`, `write_text` or `write_bytes`.

**Why this priority**: the gate is how the defect class stays closed; each documented hole is a way back in (#5883).

**Independent Test**: one synthetic offender per shape goes red; the real source tree stays green with an empty allowlist.

**Acceptance Scenarios**:

1. **Given** a synthetic module with each offending shape, **When** the gate scans it, **Then** each shape is reported with its rule.
2. **Given** the real source tree, **When** the gate scans it, **Then** it passes with no allowlist entries beyond the primitive itself, and every real site the extended rules newly see is fixed or routed through the primitive.

### User Story 5 - A refused terminal step leaves the run log and state exactly as other writers left them (Priority: P1)

The retrospective policy blocks completion, a `spec-kitty next` call reaches the terminal step, and the retrospective gate refuses. Meanwhile another `spec-kitty next` on the same Mission appends to the same run directory, or the run log shrank.

**Why this priority**: today the runtime has already written the completion, then cuts `run.events.jsonl` back to a size measured earlier and overwrites `state.json`. A shrunk log is padded with NUL bytes, another writer's rows are cut, and another writer's state is overwritten (#5884).

**Independent Test**: drive a refused terminal step while mutating the run directory inside the gate; afterwards the log has no NUL bytes, the foreign row is present, and the foreign state is intact.

**Acceptance Scenarios**:

1. **Given** the gate refuses completion, **When** the call returns, **Then** no completion row was ever appended and `state.json` is not rewritten by the rollback, so nothing needs to be cut.
2. **Given** another writer appended a row or replaced `state.json` while the gate ran, **When** the gate refuses, **Then** that row and that state are still there.
3. **Given** the run log shrank while the gate ran, **When** the gate refuses, **Then** the log contains no NUL bytes.
4. **Given** the engine's cached plan is missing or stale, **When** the terminal step is reached, **Then** the gate still runs before completion is written (it is never skipped by the fallback path).
5. **Given** the gate passes, **When** the call returns, **Then** the run completes exactly as before.

### User Story 6 - Planning commits say "mission" (Priority: P3)

An operator runs specify, plan, finalize-tasks or a documentation-mission planning step and reads the generated commit subjects.

**Why this priority**: the Terminology Canon forbids "feature" for a Mission in operator-facing text (#5885).

**Independent Test**: run each command (or its message builder) and read the subject; a source scan fails if any planning commit builder says "for feature".

**Acceptance Scenarios**:

1. **Given** any of the five planning commit builders, **When** it builds a subject, **Then** the subject reads "… for mission `<slug>`".
2. **Given** a Mission finalized before this change (its commit says "Add tasks for feature `<slug>`"), **When** finalize-tasks runs again, **Then** the drift check still treats that commit as finalize bookkeeping and raises no false drift warning.

### User Story 7 - The planning flow names the analyze step before implement (Priority: P2)

An operator finishes `/spec-kitty.tasks` on a software-dev Mission and asks what comes next, either by reading the prompt's handoff or by running `spec-kitty next`.

**Why this priority**: today the prompts and `next` point straight at implement, and implement then refuses with `analysis_report_required`; an edit to a planning artifact later makes the report stale and implement refuses again (#5885).

**Independent Test**: read the tasks and tasks-finalize handoff sections; run `next` on a Mission whose tasks are finalized with no analysis report, then with a stale one, then with a current one.

**Acceptance Scenarios**:

1. **Given** the software-dev tasks and tasks-finalize prompts, **When** an agent reads their report and next-step sections, **Then** both name `/spec-kitty.analyze` as the required step before implement and say that editing the spec, plan, tasks or charter afterwards makes the report stale.
2. **Given** a software-dev Mission with finalized tasks and no analysis report, **When** the operator runs `spec-kitty next`, **Then** it offers the analyze step, not implement.
3. **Given** the analysis report is stale, **When** the operator runs `spec-kitty next`, **Then** it offers the analyze step again and says why.
4. **Given** the analysis report is current, **When** the operator runs `spec-kitty next`, **Then** it offers implement as before.

### Edge Cases

- A setter runs inside a command that already holds the Mission lock on the same thread: the lock is re-entrant per thread and the key must be the same Mission directory name, so it neither deadlocks nor takes a second, different lock.
- A setter is reached from a subprocess or git hook while the parent holds the lock: it waits up to the bounded timeout and fails with the existing `STATUS_LOCK_HELD` diagnostic rather than hanging.
- The run directory or `run.events.jsonl` vanishes while the gate runs: nothing is created or padded.
- A run that is already terminal is polled again: the retrospective gate is not re-run (accepted consequence; the gate runs once, when the step completes).
- A Mission with a legacy "Add tasks for feature" finalize commit: drift check accepts both subjects.
- A non-software-dev Mission type: the analyze step and its `next` guard do not apply.

## Domain Language *(optional)*

| Canonical term | Meaning | Avoid |
|----------------|---------|-------|
| Mission lock | The per-Mission lock door `mission_write_lock`, keyed on the canonical Mission directory name | "status lock" for non-status writers, slug-keyed locks |
| Mission file | Any file under a Mission's directory (`meta.json`, work-package files, matrices, status log) | — |
| Run log | `run.events.jsonl` in a runtime run directory; not a Mission file | "event log" (that is the status log) |
| Analysis report | The recorded `/spec-kitty.analyze` result that implement checks for currency | — |

## Requirements *(mandatory)*

### Functional Requirements

| ID | Title | User Story | Priority | Status | Delivery | No-op passable? |
|----|-------|------------|----------|--------|----------|-----------------|
| FR-001 | `meta.json` setters write under the Mission lock | As an agent, I want every `meta.json` read-modify-write (the setters `set_target_branch`, `set_origin_ticket`, `record_discard`, `set_documentation_state`, `record_acceptance`, `clear_merge_metadata`, `clear_coordination_metadata`, `flatten_coordination_metadata`, `set_change_mode`, and accept's direct restamp writes) to read and write inside one Mission-lock hold, so that a concurrent locked write is never erased. | High | Open | [build] | no — overlap test fails against today's unlocked setter |
| FR-002 | `map-requirements` frontmatter writes under the Mission lock | As an agent, I want `agent tasks map-requirements` to read the existing refs and write the work-package frontmatter inside one Mission-lock hold, so that two overlapping runs keep both refs. | High | Open | [build] | no — overlap test fails today |
| FR-003 | `finalize-tasks` frontmatter flush does not erase concurrent writes | As an agent, I want `finalize-tasks` to re-read and write each work package's frontmatter under the Mission lock, so that a history note or ref added while finalize ran survives. | High | Open | [build] | no — overlap test fails today |
| FR-004 | Issue-matrix scaffold checks and writes under the Mission lock | As an agent, I want the issue-matrix scaffold's existence check and write inside one Mission-lock hold, so that a verdict recorded in between is never overwritten. | Medium | Open | [build] | no — overlap test fails today |
| FR-005 | Acceptance-matrix and issue-verdict helpers use the Mission lock door | As a maintainer, I want the two existing locked re-read helpers to take the lock through `mission_write_lock` instead of a raw status lock, so that there is one lock door for Mission-file writers. Behaviour is unchanged. | Medium | Open | [ratchet] | yes — paired with FR-008's gate rule that flags a raw status-lock call outside the status pipeline |
| FR-006 | Gate Rule 2 refuses a callable run after the lock is released | As a maintainer, I want the read/sink rule to accept a callable passed into a lock block only when its parameter is only ever called (never stored, returned or assigned), so that deferred execution after release is caught. | Medium | Open | [build] | no — synthetic offender goes red |
| FR-007 | Gate Rule 3 accepts only known Mission-directory-name keys | As a maintainer, I want the lock-key rule to accept only key expressions known to be a Mission directory name (and to check `mission_write_lock`'s first argument too), so that a subscript or call key such as `meta["mission_slug"]` is caught. | Medium | Open | [build] | no — synthetic offender goes red |
| FR-008 | Gate Rule 1 catches whole-file rewrites of status and run logs | As a maintainer, I want the truncate rule to also flag `open(..., "w")`, `write_text` and `write_bytes` whose target names a status or run log, and to scan `src/runtime` with the run-log names, so that a blind rewrite cannot come back under another name. Every real site it newly sees is fixed or routed through an owning primitive; the allowlist stays empty. | High | Open | [build] | no — synthetic offender and today's runtime truncate go red |
| FR-009 | Runtime terminal gate runs before completion is written | As an operator, I want the retrospective gate on the legacy `next` path to run as the engine's abort-only completion hook, so that a refused completion appends nothing to the run log and rewrites no state. | High | Open | [build] | no — NUL-pad, foreign-row and foreign-state repros fail today |
| FR-010 | Runtime speculative rollback is removed | As a maintainer, I want the speculative capture and rollback of the run log and `state.json` removed, so that no runtime code truncates a run log or restores state it cannot prove is its own. | High | Open | [build] | no — FR-008's runtime scan goes red while it exists |
| FR-011 | The stale-plan fallback never skips the gate | As an operator, I want the path that runs when no plan is cached or the plan is stale to plan again (or carry the same hook), so that the gate runs before completion on every path. | High | Open | [build] | no — stale-plan repro shows completion written without the gate today |
| FR-012 | Planning commit subjects say "mission" | As an operator, I want the five planning commit builders (tasks finalize, spec/plan setup, gap analysis, generator config, Mission creation) to say "for mission `<slug>`". | Low | Open | [build] | no — subject assertion fails today |
| FR-013 | Finalize drift check accepts the legacy subject | As an operator, I want the finalize drift check to accept both "Add tasks for mission" and the legacy "Add tasks for feature" subject, so that Missions finalized earlier raise no false drift warning. | Low | Open | [build] | no — paired: a legacy-subject fixture and a foreign-subject fixture on the same history |
| FR-014 | Source scan keeps "for feature" out of commit builders | As a maintainer, I want a test that fails if any commit-subject builder under `src/specify_cli` says "for feature {", so that the wording cannot regress. | Low | Open | [build] | no — fails on today's five sites |
| FR-015 | Tasks prompts name the analyze step and its staleness rule | As an operator, I want the software-dev tasks and tasks-finalize prompts' report and next-step sections to name `/spec-kitty.analyze` as required before implement, and to say editing spec, plan, tasks or charter afterwards makes the report stale. | Medium | Open | [build] | no — section-scoped content test fails today |
| FR-016 | `spec-kitty next` offers analyze before implement on software-dev | As an operator, I want `next` on a software-dev Mission with finalized tasks to offer the analyze step while the analysis report is missing or stale, and implement only once it is current, so that `next` never hands out a step implement will refuse. | Medium | Open | [build] | no — `next` offers implement today with no report |

### Non-Functional Requirements

| ID | Title | Requirement | Category | Priority | Status |
|----|-------|-------------|----------|----------|--------|
| NFR-001 | Overlap tests are deterministic | Every new concurrency test uses injected pause points, not sleeps, and passes 5 of 5 repeated runs with no flake. | Reliability | High | Open |
| NFR-002 | Lock waits are bounded | No newly locked writer waits for the Mission lock longer than the existing bounded default (30 s) before failing with `STATUS_LOCK_HELD`; none is changed to unbounded. | Reliability | High | Open |
| NFR-003 | No added latency on the uncontended path | An uncontended `meta.json` setter or frontmatter write takes under 50 ms more than today on a typical Mission. | Performance | Medium | Open |
| NFR-004 | Gate stays empty-allowlist | The mission-write discipline gate ends the Mission with zero allowlist entries beyond the primitive's own sites, and each extended rule has a synthetic offender and a self-mutation proof. | Maintainability | High | Open |
| NFR-005 | New code quality | New and changed code passes `ruff check`, `ruff format --check` and `mypy` with zero new issues and no new suppressions; every touched function stays at complexity 15 or below. | Maintainability | High | Open |

### Constraints

| ID | Title | Constraint | Category | Priority | Status |
|----|-------|------------|----------|----------|--------|
| C-001 | Layer rules hold | `src/runtime` must not import `specify_cli`; the runtime fix uses only runtime and kernel code (`kernel <- charter <- runtime <- specify_cli`). | Technical | High | Open |
| C-002 | One lock door | Mission-file writers outside the status pipeline lock through `mission_write_lock` keyed via `mission_write_lock_dir`; no second lock mechanism is introduced. | Technical | High | Open |
| C-003 | Edit sources, not copies | Prompt changes go to `packs/built-in/missions/mission-steps/software-dev/...`; generated agent copies are not edited. New prompt text carries no work-package ids, issue numbers, requirement ids, `src/specify_cli` or `kitty-specs/` paths (provenance ratchet). | Technical | High | Open |
| C-004 | Deprecated runtime template untouched | The analyze step is added to the live software-dev dispatch (mission definition and step contracts), not to the deprecated `mission-runtime.yaml`. | Technical | High | Open |
| C-005 | Stacked on PR #5890 | The work starts from and builds on the PR #5890 branch; it may not change that PR's behaviour except where a requirement here says so. | Business | High | Open |
| C-006 | Red-first | Each FR with "no" in No-op passable gets a reproduction that is shown failing against the pre-fix code before the fix lands (ADR 2026-07-17-1). | Technical | High | Open |
| C-007 | Out of scope | `review/prompt_metadata.write_frontmatter` (a per-invocation temporary file, not a Mission file), git `index.lock` collisions (#5515/#5443), and serialising two concurrent runtime commits (#5854) are out of scope. | Business | Medium | Open |

### Key Entities

- **Mission lock**: the per-Mission, per-thread re-entrant lock, keyed on the canonical Mission directory name; held for every read-modify-write of a Mission file.
- **Run directory**: the runtime's per-Mission run state (`state.json`, `run.events.jsonl`); shared by every `spec-kitty next` on that Mission in one repository.
- **Analysis report**: the recorded analyze result, current only while the hashed planning inputs (spec, plan, tasks, charter and related material) are unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In every overlap scenario of User Stories 1–3, both writers' changes are present afterwards in 5 of 5 runs (0 of 5 before the fix). — [build] · no-op passable: no
- **SC-002**: A refused terminal step leaves 0 NUL bytes in the run log, 0 foreign rows removed and 0 foreign state overwrites across the three repro scenarios. — [build] · no-op passable: no
- **SC-003**: The mission-write discipline gate reports each of the 3 new offender shapes, and 0 offenders and 0 allowlist entries on the real tree. — [build] · no-op passable: no
- **SC-004**: 0 planning commit builders produce a "for feature" subject. — [build] · no-op passable: no
- **SC-005**: On a software-dev Mission with finalized tasks, `next` offers implement 0 times while the analysis report is missing or stale, and offers it once the report is current. — [build] · no-op passable: no

## Assumptions

- Two `spec-kitty next` processes on one Mission are an expected case (#5389 already handles a start race), so the run directory has more than one writer in practice.
- The bulk-edit guardrail does not apply: the "for feature" change touches five enumerated commit builders, each listed in FR-012 and kept closed by FR-014's scan; it is not a codebase-wide rename.
- The analyze step's prompt (`software-dev/analyze`) already exists; the Mission wires it into the live dispatch and does not rewrite it.
- The exact shape of the `next` analyze step (a new action in the software-dev sequence, or a guard that routes tasks-complete Missions to analyze) is a plan-phase decision within FR-016 and C-004.

## Dependencies

- PR #5890 (`issue-5819-concurrent-mission-writers`) supplies `mission_write_lock`, `mission_write_lock_dir`, `locked_rewrite_text` and the gate this Mission extends.
- Related, not owned: #5854 (unserialised runtime commits), #5515 / #5443 (git index collisions).
