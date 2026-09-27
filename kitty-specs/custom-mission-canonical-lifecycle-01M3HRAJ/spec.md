# Mission Specification: Canonical lifecycle for custom mission types

**Mission Branch**: `issue-4983-custom-mission-canonical-lifecycle`  
**Created**: 2026-09-27  
**Status**: Draft  
**Input**: GitHub issue #4983 and the architecture-pack D03→D06 runtime-integration contract

## Summary

Project and organization packs can define reusable custom mission steps, but those types
cannot yet participate in Spec Kitty's formal mission lifecycle. Creation rejects the
custom type, while `mission run` can start an identity-less runtime with only minimal
metadata. Work-package state, independent review, acceptance, merge, dossier completeness,
and retrospective completion then either assume software-dev or cannot find the mission.

This mission makes an activated custom type a first-class formal Mission. It reuses the
charter's `ResolvedMissionType` as the single type authority, materializes canonical
identity and dossier state before runtime start, freezes one resolved lifecycle contract,
and routes every applicable command through that contract. The contract explicitly models
executable, planning-only, WP-driven, and no-WP behavior so the runtime never fabricates
software-dev files or weakens a gate merely because a mission is custom.

The architecture pack is the first downstream consumer: D06 may claim compatibility only
after a clean consumer completes the full declared lifecycle and paired negative fixtures
fail closed.

## Scope

In scope:

- activated custom-type creation and run attachment through the canonical identity funnel;
- an immutable resolved lifecycle policy composed with existing step-contract and
  expected-artifact authorities;
- explicit WP-required, WP-optional, and no-WP behavior;
- contract-aware implement, review, accept, merge, and retrospective routing;
- cross-process resolution of frozen steps, profiles, and contracts;
- atomic terminal completion;
- installed-CLI clean-consumer acceptance evidence for the architecture-pack dependency.

Out of scope:

- retiring every legacy mission loader or packaged mission copy tracked by #2652;
- redefining the architecture pack's outcome semantics, evidence rules, or authority model;
- claiming #4906's documentation/research acceptance defect closed without its own full
  regression proof;
- silently repairing or retyping existing missions;
- introducing a new mission-type resolver, status store, lane model, dossier schema, or
  artifact vocabulary;
- hosted transport, certification, standards conformance, legal compliance, or production
  readiness claims.

## User Scenarios & Testing

### User Story 1 — Create a custom type as a canonical Mission (Priority: P1)

As a pack operator, I want `agent mission create --mission-type <custom>` to resolve an
activated custom type and create the same canonical identity and dossier structure as any
built-in type, so every later command addresses one real Mission instead of an ad-hoc run.

**Why this priority**: Identity and type selection are upstream of all other lifecycle
behavior. A run without them cannot produce trustworthy review or acceptance evidence.

**Independent Test**: In a clean initialized consumer, activate a custom type, create it
through the public CLI, and assert the returned non-null ULID, derived `mid8`, canonical
directory, validated metadata, status stream, topology record, and resolvable dossier.

**Acceptance Scenarios**:

1. **Given** a valid activated custom type, **When** the operator creates a Mission with
   that type, **Then** creation resolves the type through `ResolvedMissionType` and returns
   a non-null canonical identity.
2. **Given** the custom definition is discoverable but not charter-activated, **When** the
   operator creates it, **Then** creation fails before writing mission or runtime state and
   names the activation remedy.
3. **Given** a malformed or incomplete lifecycle contract, **When** creation is attempted,
   **Then** validation fails atomically before a directory, branch, run, or success envelope
   is produced.
4. **Given** an existing Mission of another type, **When** a custom run is requested through
   any equivalent handle, **Then** the immutable type mismatch is refused without changing
   metadata or run state.

---

### User Story 2 — Run custom planning steps reproducibly across processes (Priority: P1)

As an operator or external orchestrator, I want every custom step and profile binding to
resolve after the original `mission run` process exits, so separate `next` invocations are
deterministic and never depend on a process-local registry.

**Why this priority**: Real CLI use is one process per command. In-memory success is not a
usable workflow contract.

**Independent Test**: Create and start a custom Mission, invoke every planning step from a
fresh CLI process, and prove each step uses the frozen definition and declared profile or
contract binding even after the authored live definition changes.

**Acceptance Scenarios**:

1. **Given** a created custom Mission, **When** `mission run` starts it, **Then** the selected
   step definition and lifecycle policy are frozen with verifiable provenance before the
   first step is issued.
2. **Given** the starting process has exited, **When** a new process advances the Mission,
   **Then** its active step, profile, and step contract resolve from durable frozen state.
3. **Given** the live pack definition changes after run start, **When** the Mission advances,
   **Then** the runtime either continues from the frozen contract or reports governed drift;
   it never silently changes the in-flight workflow.
4. **Given** a final step whose composition or required gate fails, **When** advancement is
   attempted, **Then** the durable state remains resumable at that step.

---

### User Story 3 — Execute and independently review declared work packages (Priority: P1)

As a custom mission author, I want the lifecycle contract to declare whether WPs are
required, optional, or forbidden, so executable missions use canonical status/review
machinery and no-WP missions do not need invented tasks.

**Why this priority**: WP policy is the main behavioral difference between software
delivery, planning-only work, and outcome-oriented architecture work.

**Independent Test**: Drive one WP-required fixture through finalize, implement, reject,
rework, and independent approval; drive a paired no-WP fixture through its declared path
and prove it creates no fake task or status evidence.

**Acceptance Scenarios**:

1. **Given** a WP-required custom Mission with finalized packages, **When** implement and
   review run, **Then** claims, transitions, review cycles, dependencies, and approvals are
   recorded by the existing canonical event/status authorities.
2. **Given** independent review is required, **When** the reviewer is the implementer of
   record, **Then** approval is refused with an actionable diagnostic.
3. **Given** review rejects a WP, **When** the implementer corrects it and resubmits,
   **Then** prior review evidence remains append-only and a new cycle can be approved.
4. **Given** a no-WP custom Mission, **When** implement or WP review is invoked, **Then** the
   command returns an explicit `not_applicable` outcome with lifecycle-policy provenance
   and performs no mutation.
5. **Given** a planning-only Mission that declares planning WPs, **When** packages finalize,
   **Then** the canonical lane manifest identifies them honestly as planning artifacts.

---

### User Story 4 — Accept against the custom contract, not software-dev assumptions (Priority: P1)

As an accountable operator, I want acceptance to evaluate the selected custom type's
declared artifacts, applicable gates, and evidence so a valid architecture Mission can be
accepted without a placeholder `tasks.md`, while missing required evidence still blocks.

**Why this priority**: Acceptance is the trust boundary. A custom type is not first-class
if it passes only by fabricating another type's files or by skipping checks.

**Independent Test**: Populate exactly the artifacts and evidence declared by a custom
fixture, accept successfully, then independently remove each required class and prove its
specific gate fails; adding unrelated software-dev files must not change either verdict.

**Acceptance Scenarios**:

1. **Given** all custom required artifacts and gates pass, **When** acceptance runs, **Then**
   it records a successful verdict naming the selected type, lifecycle policy, artifact
   manifest, evidence revisions, and evaluated/non-applicable gates.
2. **Given** a required custom artifact is missing, **When** acceptance runs, **Then** it
   fails with that artifact key/path and does not request a software-dev-only artifact.
3. **Given** a no-WP Mission with no task files by contract, **When** acceptance runs,
   **Then** WP checks are recorded as not applicable and do not block.
4. **Given** a required review or other prior gate lacks evidence, **When** acceptance runs,
   **Then** it fails closed even if every declared file exists.
5. **Given** an optional gate was skipped, **When** acceptance runs, **Then** the skip is
   accepted only when durable actor/reason provenance exists.

---

### User Story 5 — Merge or close through the declared delivery mode (Priority: P1)

As a Mission operator, I want merge to use the contract's executable, planning-only, or
no-WP path and produce a final target-branch baseline, so completion reflects real work
without weakening merge-readiness or lane safety.

**Why this priority**: A formally accepted Mission that cannot reach an auditable target
baseline is still lifecycle-incomplete.

**Independent Test**: Merge a WP-backed custom fixture through real lanes and a no-WP or
planning-only fixture through its declared path, then verify the target commit, baseline
record, terminal statuses, and absence of unrelated source changes.

**Acceptance Scenarios**:

1. **Given** an accepted executable WP-backed Mission, **When** merge runs, **Then** the
   existing dependency-ordered lane merge and integrity checks apply unchanged.
2. **Given** an accepted planning-only Mission, **When** merge runs, **Then** only declared
   planning artifacts and bookkeeping reach the target, using the existing planning-only
   safety invariants.
3. **Given** an accepted no-WP Mission, **When** its declared completion path runs, **Then**
   merge/close records an explicit no-WP topology and baseline without synthetic lanes.
4. **Given** a Mission is not accepted or its declared merge evidence is incomplete,
   **When** merge runs, **Then** it refuses before advancing the target branch.
5. **Given** a caller supplies a flag contradicting the frozen lifecycle policy, **When**
   merge runs, **Then** it refuses rather than treating the flag as a gate bypass.

---

### User Story 6 — Complete retrospective and terminal state atomically (Priority: P1)

As an auditor, I want the final step, retrospective outcome, completion event, and reduced
Mission state to agree, so a blocked command can never be followed by a query that says the
Mission is done.

**Why this priority**: Contradictory terminal evidence invalidates the audit trail and can
cause downstream automation to publish unfinished work.

**Independent Test**: Force each final-step failure arm, query from a new process, and prove
the Mission remains non-terminal; then repair and retry, proving one terminal event and one
stable done state.

**Acceptance Scenarios**:

1. **Given** final-step composition fails, **When** advancement returns blocked, **Then** a
   subsequent query reports the same resumable current step, not `done`.
2. **Given** a required retrospective fails or cannot persist, **When** the terminal call
   runs, **Then** no terminal state or externally visible completion event is committed.
3. **Given** all terminal obligations succeed, **When** completion commits, **Then** runtime
   state, events, retrospective record, status projection, and query all report terminal.
4. **Given** a successful terminal call is replayed, **When** the operator queries or retries,
   **Then** it remains idempotent and emits no duplicate completion evidence.

### Edge Cases

- The same custom key exists at project and organization tiers; normal resolver precedence
  chooses one and records the winning provenance.
- A discovered custom definition is not activated, or activation names a type whose
  lifecycle/step/artifact components cannot all resolve.
- A custom type uses Unicode display text while all storage identifiers remain ASCII.
- `mission run` receives a slug, `mid8`, numeric prefix, or full ULID resolving to an
  existing Mission of the same or a different type.
- Creation succeeds but run freezing fails; the command must report the created Mission
  honestly and must not claim a live run, or must roll back the entire combined operation
  according to the selected transaction boundary.
- A manifest is missing, malformed, shadowed, or changes after Mission creation.
- A lifecycle policy declares impossible combinations, such as required WP review with WPs
  forbidden and no non-WP review surface.
- A no-WP Mission has a stray `tasks.md` or `lanes.json`; stray files must not silently
  change its frozen policy.
- A WP-required Mission has zero finalized WPs; this is an error, not implicit no-WP mode.
- An optional gate is skipped without actor/reason provenance.
- Target branch moves between acceptance and merge.
- The terminal state write, event append, or retrospective write fails after another part
  has succeeded; recovery must be deterministic and must not expose split terminal state.

## Requirements

### Functional Requirements

| ID | Title | User Story | Priority | Status | Delivery | No-op passable? |
|---|---|---|---|---|---|---|
| FR-001 | Canonical custom-type resolution | As an operator, I want every formal custom Mission entry point to resolve the requested activated type through the charter `ResolvedMissionType` authority so that discovery and lifecycle identity cannot disagree. | High | Open | [build] | no |
| FR-002 | Activated custom creation | As an operator, I want `agent mission create --mission-type <custom>` to accept a valid activated custom type so that it is a peer of built-ins at creation. | High | Open | [build] | no |
| FR-003 | Canonical identity materialization | As an auditor, I want successful create/run-start to have a non-null ULID, derived `mid8`, canonical directory, validated metadata, target, topology, and status stream before a run starts. | High | Open | [build] | no |
| FR-004 | Atomic creation refusal | As an operator, I want unresolved, unactivated, malformed, or lifecycle-incompatible types to fail before mission/run side effects so that failed creation leaves no false evidence. | High | Open | [ratchet] | yes — same fixture has a valid activated positive control |
| FR-005 | Immutable type attachment | As an operator, I want run attachment to verify that instance, run index, frozen template, and requested type agree so that an existing Mission can never be silently retyped. | High | Open | [ratchet] | yes — paired same-type attachment succeeds |
| FR-006 | Resolved lifecycle policy | As a pack author, I want one charter-owned lifecycle policy to declare delivery mode, WP policy, and gate applicability so that commands do not infer behavior from filenames or type names. | High | Open | [build] | no |
| FR-007 | Policy combination validation | As a pack author, I want invalid lifecycle-policy combinations rejected with field-specific diagnostics so impossible workflows cannot be activated. | High | Open | [build] | no |
| FR-008 | Manifest-owned artifacts | As a pack author, I want artifact role, path, step, required/optional, and blocking semantics to come from the resolved expected-artifact manifest so no second artifact list drifts. | High | Open | [ratchet] | yes — positive and missing-artifact arms share the manifest |
| FR-009 | Frozen lifecycle provenance | As an auditor, I want the selected type, lifecycle policy, artifact manifest, and step definition frozen or fingerprinted at run start so later commands can prove what governed the Mission. | High | Open | [build] | no |
| FR-010 | Durable cross-process step resolution | As an orchestrator, I want fresh CLI processes to resolve every active custom step, profile binding, and contract from durable frozen state so process-local registry state is never required. | High | Open | [ratchet] | yes — same-process control plus separate-process regression |
| FR-011 | Governed definition drift | As an operator, I want changes to the live custom definition after run start handled according to one explicit frozen/drift policy so in-flight behavior never changes silently. | High | Open | [build] | no |
| FR-012 | WP-required materialization | As a custom executable-mission author, I want required WPs finalized into canonical task, dependency, status-event, and lane projections so existing implement/review machinery can consume them. | High | Open | [build] | no |
| FR-013 | Explicit no-WP lifecycle | As a no-WP mission author, I want an explicit canonical no-WP state so accept/merge/close can proceed without fabricated tasks, WPs, checkboxes, or lane transitions. | High | Open | [build] | no |
| FR-014 | Optional WP selection | As a mission author, I want optional WP policy resolved to a frozen present-or-absent choice before execution so later commands cannot switch modes opportunistically. | Medium | Open | [build] | no |
| FR-015 | Contract-aware implement | As an operator, I want implement to execute only when the lifecycle policy declares it applicable and to return structured `not_applicable` otherwise. | High | Open | [build] | no |
| FR-016 | Independent review evidence | As an accountable operator, I want required custom review to enforce implementer/reviewer separation and append-only verdict cycles so approval is independently attributable. | High | Open | [build] | no |
| FR-017 | Gate applicability provenance | As an auditor, I want each required, optional, skipped, and not-applicable gate recorded with its governing policy and actor/reason evidence where applicable. | High | Open | [build] | no |
| FR-018 | Contract-aware acceptance | As an accountable operator, I want acceptance to evaluate the frozen custom lifecycle, manifest, WP policy, applicable gates, and evidence instead of hard-coded software-dev files. | High | Open | [build] | no |
| FR-019 | Acceptance fail-closed controls | As an auditor, I want missing required artifacts, review evidence, acceptance criteria, or negative-invariant evidence to block while unrelated software-dev files cannot alter the verdict. | High | Open | [ratchet] | yes — each negative uses the same accepted positive fixture |
| FR-020 | Acceptance evidence record | As an auditor, I want the acceptance result to name the mission identity, type, lifecycle fingerprint, evaluated artifacts/gates, evidence revisions, and verdict. | High | Open | [build] | no |
| FR-021 | Executable lane merge | As an operator, I want an accepted WP-backed custom Mission to use the existing dependency-ordered merge and integrity gates unchanged. | High | Open | [ratchet] | yes — built-in lane merge is the behavior control |
| FR-022 | Planning-only completion | As an operator, I want an accepted planning-only custom Mission to use the existing planning-artifact merge semantics and produce a target baseline without source-delivery assumptions. | High | Open | [build] | no |
| FR-023 | No-WP completion | As an operator, I want an accepted no-WP custom Mission to merge or close through an explicit policy-selected route without synthesizing a lane manifest that claims work never performed. | High | Open | [build] | no |
| FR-024 | Merge precondition integrity | As an operator, I want every custom merge route to refuse before target mutation when acceptance, target freshness, policy, topology, or declared evidence is invalid. | High | Open | [ratchet] | yes — accepted fresh control advances the same target fixture |
| FR-025 | Baseline and terminal WP state | As an auditor, I want successful completion to record the resulting target baseline and terminal status for every declared WP or the explicit no-WP outcome. | High | Open | [build] | no |
| FR-026 | Atomic custom terminus | As an auditor, I want final-step success, required retrospective, runtime reduction, durable events, and externally emitted completion to commit as one logical transition. | High | Open | [ratchet] | yes — paired successful and forced-failure terminal arms |
| FR-027 | Blocked-state query consistency | As an operator, I want a query after any blocked terminal attempt to report the same resumable non-terminal step so blocked and done can never coexist. | High | Open | [ratchet] | yes — same run succeeds after repair |
| FR-028 | Terminal idempotency | As an auditor, I want replay after successful completion to preserve one terminal outcome and avoid duplicate completion or retrospective evidence. | High | Open | [ratchet] | yes — first successful terminal call is the control |
| FR-029 | Full clean-consumer lifecycle proof | As the architecture-pack D06 integrator, I want an installed-CLI fixture to run create → planning → finalize → implement → independent review → accept → merge → retrospective in separate processes and verify all promised artifacts/state. | High | Open | [build] | no |
| FR-030 | Paired no-WP and negative proof | As the architecture-pack D06 integrator, I want a no-WP fixture plus unactivated, malformed, cross-type, missing-evidence, and terminal-failure controls so compatibility cannot be claimed from one happy path. | High | Open | [build] | no |
| FR-031 | Stable structured diagnostics | As an external orchestrator, I want every refusal and not-applicable outcome to carry a stable error/status code, mission identity when available, governing type/policy, and actionable remediation. | Medium | Open | [build] | no |
| FR-032 | Existing built-in behavior preservation | As a Spec Kitty user, I want built-in software-dev creation and lifecycle behavior unchanged except where shared correctness is explicitly covered, so custom support does not regress the primary workflow. | High | Open | [ratchet] | yes — byte/behavior controls use existing built-in fixtures |

### Non-Functional Requirements

| ID | Title | Requirement | Category | Priority | Status |
|---|---|---|---|---|---|
| NFR-001 | Resolver latency | Added lifecycle resolution contributes no more than 100 ms p95 to a warm local create or query across at least 100 repetitions. | Performance | High | Open |
| NFR-002 | Command latency | No lifecycle command adds an unbounded wait, retry, network dependency, or background daemon; ordinary local metadata-only operations remain under 2 seconds on the repository test fixture. | Performance | High | Open |
| NFR-003 | Failure atomicity | Every tested create/run-start/terminal failure leaves either the complete pre-operation state or the complete post-operation state; zero tested arms expose partial identity or terminal evidence. | Reliability | High | Open |
| NFR-004 | Determinism | Repeating resolution and clean-consumer runs against identical inputs yields byte-identical policy fingerprints and equivalent ordered lifecycle evidence, excluding declared timestamps/ULIDs/commit identities. | Reliability | High | Open |
| NFR-005 | Cross-process fidelity | One hundred percent of the clean-consumer commands run in fresh processes; no test may seed the in-memory custom-contract registry as hidden setup. | Reliability | High | Open |
| NFR-006 | Security and path safety | Authored paths and identifiers remain validated against traversal, absolute-path, symlink-swap, and non-ASCII storage-identifier hazards; negative fixtures perform no out-of-root write. | Security | High | Open |
| NFR-007 | Backward compatibility | Targeted regression suites for mission creation, loader, runtime-next, status, review, acceptance, merge, dossier, and retrospective pass with no existing public JSON key removed or reinterpreted silently. | Compatibility | High | Open |
| NFR-008 | Architectural non-vacuity | Each new architectural gate has a concrete production caller, a positive control, a negative self-mutation/control, and a shrink-only census where an allowlist is unavoidable. | Maintainability | High | Open |
| NFR-009 | Test quality | New behavior is driven red-first through public CLI or existing production entry points and new/changed code meets the repository's 90% diff-coverage gate. | Testability | High | Open |
| NFR-010 | Offline operation | The complete lifecycle proof passes with network disabled after local package installation and fixture setup; no hosted service is required. | Operability | High | Open |
| NFR-011 | Public-safe evidence | Generated diagnostics, logs, tests, and mission artifacts contain no credentials, customer data, developer-home paths, or private repository material. | Security | High | Open |
| NFR-012 | Installed-package fidelity | The clean-consumer proof runs against the built wheel/sdist or equivalent isolated installed CLI, not imports from the developer checkout. | Compatibility | High | Open |

### Constraints

| ID | Title | Constraint | Category | Priority | Status |
|---|---|---|---|---|---|
| C-001 | Single type authority | Charter `ResolvedMissionType` is the sole formal custom-type selection authority; no parallel resolver, allowlist, or type registry may be introduced. | Architecture | High | Open |
| C-002 | Existing artifact authority | Artifact roles and required/optional semantics remain owned by the expected-artifact manifest and its charter loader. | Architecture | High | Open |
| C-003 | Existing runtime authority | Step order, dependencies, inputs, profiles, and contract refs remain owned by the resolved/frozen mission template and step-contract system. | Architecture | High | Open |
| C-004 | Existing state authority | WP lifecycle state remains event-sourced; `lanes.json`, dashboards, and acceptance summaries are projections, not competing state stores. | Architecture | High | Open |
| C-005 | No fabricated evidence | No command may create a software-dev artifact, dummy WP, fake lane, review verdict, acceptance row, or retrospective outcome solely to satisfy a gate. | Integrity | High | Open |
| C-006 | No guard weakening | Safe-commit, protected-branch, target-freshness, lane-integrity, independent-review, acceptance, and retrospective guards may be made contract-aware but not bypassed. | Integrity | High | Open |
| C-007 | Pack-tier boundary | Consumer lifecycle doctrine belongs in built-in/pack offering surfaces; Spec Kitty maintainer-only procedures remain internal and are not force-shipped. | Architecture | High | Open |
| C-008 | Layer direction | `kernel <- charter <- {glossary, runtime, mission_runtime} <- specify_cli` remains valid; lower layers must not import CLI command modules. | Architecture | High | Open |
| C-009 | Issue boundaries | #2652, #4906, and #4965 retain separate closure unless their complete acceptance contracts are explicitly executed and independently reviewed in this mission. | Scope | Medium | Open |
| C-010 | Architecture semantics ownership | The architecture pack owns its outcome, evidence, authority, tailoring, and restart semantics; core provides lifecycle capabilities without reinterpreting them. | Scope | High | Open |
| C-011 | No in-scope release number | This mission defines behavior and evidence, not a product release/version number or publication date. | Release | Medium | Open |
| C-012 | Operator merge authority | Agents may prepare and review core work but must not push or merge; the human operator owns publication and merge. | Workflow | High | Open |

### Key Entities

- **Resolved Mission Type**: the charter-selected custom type with provenance and lazy
  projections for steps, templates, artifacts, governance, and lifecycle policy.
- **Mission Lifecycle Policy**: immutable declaration of delivery mode, WP policy, and
  gate applicability.
- **Canonical Mission Instance**: ULID-addressed mission metadata, topology, target, and
  lifecycle fingerprint.
- **Frozen Runtime Definition**: durable step DAG and bindings used across CLI processes.
- **Expected Artifact Manifest**: authoritative artifact-role and completeness contract.
- **Mission Dossier**: indexed, hashed projection of the instance's artifacts.
- **Work-Package Lifecycle**: event-sourced WP/dependency/review state, when applicable.
- **Gate Evidence**: durable proof for implement, review, accept, merge, and retrospective.
- **Terminal Transition**: atomic final-step/retrospective/state/event completion boundary.

## Dependencies and coordination

- #3831 supplies the charter-aware custom type resolution foundation; this mission extends
  it rather than replacing it.
- #4906 is an adjacent acceptance-type bug and remains independently tracked.
- #4965 is an adjacent type-overwrite bug on `mission run`; this mission's immutable attach
  invariant must compose with it without false closure.
- Architecture pack D06 remains blocked until this mission lands and the pack's clean
  consumer independently proves the supported core revision.
- Core work is based on exact commit `5e29a0b4e7b9203b0c6760d68af84e60679feae8`; later base changes require refreshed review.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A valid activated custom type completes canonical create with non-null ULID,
  derived `mid8`, validated metadata, dossier projection, status stream, and frozen
  lifecycle provenance; the unactivated control writes none of them. — [build] · no-op
  passable: no
- **SC-002**: Every step in the positive custom fixture resolves from a fresh CLI process,
  and changing the live authored definition does not silently alter the in-flight run. —
  [build] · no-op passable: no
- **SC-003**: A WP-required custom fixture completes implement → rejection → rework →
  independent approval with append-only status/review evidence. — [build] · no-op
  passable: no
- **SC-004**: A no-WP fixture reaches acceptance and completion with zero synthetic
  `tasks.md`, `WP*.md`, or WP transition events, while invoking implement reports explicit
  not-applicable. — [build] · no-op passable: no
- **SC-005**: Acceptance passes with exactly the custom contract's required evidence and
  fails when each required artifact/gate is independently removed; unrelated
  software-dev artifacts change no verdict. — [ratchet] · no-op passable: yes
- **SC-006**: Executable and planning/no-WP merge arms each produce the correct target
  baseline and refuse before target mutation when not accepted or stale. — [build] · no-op
  passable: no
- **SC-007**: Every forced terminal failure returns blocked and remains non-terminal on a
  fresh query; the repaired retry produces exactly one terminal completion outcome. —
  [ratchet] · no-op passable: yes
- **SC-008**: The installed, offline clean-consumer matrix passes all positive and negative
  arms in fresh processes and proves every D03→D06 required capability. — [build] · no-op
  passable: no
- **SC-009**: Targeted existing suites for all touched owner modules pass, new/changed code
  satisfies the repository's 90% diff-coverage requirement, and every implicated named
  architectural gate passes. — [ratchet] · no-op passable: yes
- **SC-010**: Resolver performance stays within 100 ms p95 warm overhead and ordinary local
  metadata-only commands remain under 2 seconds on the declared fixture. — [ratchet] ·
  no-op passable: yes
