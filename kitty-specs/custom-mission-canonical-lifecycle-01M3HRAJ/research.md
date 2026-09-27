# Research: Canonical lifecycle for custom mission types

**Mission**: `custom-mission-canonical-lifecycle-01M3HRAJ`  
**Audience**: Spec Kitty runtime, charter, mission-runtime, and CLI maintainers  
**Research cut**: repository `5e29a0b4e7b9203b0c6760d68af84e60679feae8`, 2026-09-27  
**Question**: How can a charter-activated custom mission type use the same identity,
dossier, work-package, review, acceptance, merge, and retrospective lifecycle as a
built-in mission without creating another mission-type authority or fabricating
software-dev artifacts?

## Executive finding

The lifecycle is not absent; it is split across authorities that the current custom
loader does not join. `create_mission_core` already mints canonical identity and mission
metadata, the charter resolver already returns `ResolvedMissionType`, expected-artifact
manifests already describe dossier roles, the runtime already freezes custom step
templates, status events already own WP state, and merge already supports planning-only
and direct-on-target shapes. The current `mission run` path bypasses those seams: it
validates a reusable `mission.yaml`, registers synthesized step contracts only in the
process singleton, starts a run, and writes only three type keys into a permissively
loaded `meta.json`. That is why the command can return success with `mission_id: null`.

The appropriate design is therefore a lifecycle bridge through the existing charter and
mission-runtime authorities, not a second custom runtime. A custom type must resolve to
one immutable, validated lifecycle contract before any state is written. Both `agent
mission create` and `mission run` consume that resolved contract. The contract composes
existing step, artifact, and topology authorities and declares only lifecycle policy that
cannot currently be derived: whether work packages are required, forbidden, or optional;
whether delivery is executable or planning-only; and which lifecycle gates apply. Invalid
combinations fail before a dossier or run is created.

## Evidence map

| Ref | Current evidence | Consequence |
|---|---|---|
| E-01 | Issue #4983 reproduces `agent mission create --mission-type architecture` rejecting an activated custom key on both the stable and then-current `main` lines. | Creation does not yet consume the same custom-type authority as runtime discovery. |
| E-02 | `src/specify_cli/core/mission_creation.py::_create_mission_core_impl` already mints ULID identity, `mid8`, canonical directory name, `meta.json`, status stream, task directory, topology, and scaffold commit after resolving an activated type. | Reuse this funnel; do not duplicate its writes in `mission_loader`. |
| E-03 | `src/specify_cli/mission_loader/command.py::run_custom_mission` calls `_ensure_feature_metadata`, which writes type keys with `validate=False`; `_read_mission_id` explicitly returns `None` when identity is absent. | This is the bypass that must be removed from successful new-run behavior. |
| E-04 | `src/charter/activation/mission_type_profiles.py::ResolvedMissionType` is the charter result carrying action sequence plus lazy template, governance, expected-artifact, and step-contract projections. | Extend or compose this result; no parallel resolver or registry. |
| E-05 | `src/runtime/next/_internal_runtime/engine.py` writes `mission_template_frozen.yaml`; `runtime_bridge_composition.py::_resolve_runtime_contract_for_step` can re-synthesize a contract from that frozen file in a later process. | Cross-process step determinism already has a durable source; the process singleton is only an overlay. |
| E-06 | `packs/built-in/missions/*/expected-artifacts.yaml` and `charter.activation.manifest_loader` are the canonical artifact-role/completeness source. `ManifestRegistry` is only a delegate. | Lifecycle contract should reference the resolved expected-artifact manifest, not add another artifact list. |
| E-07 | `src/specify_cli/acceptance/gates_core.py` currently requires `lanes.json`; its planning-artifact-only path deliberately skips the acceptance matrix. Issue #4906 separately demonstrates software-dev artifact assumptions in acceptance. | Custom acceptance must be type- and lifecycle-aware while preserving #4906's independent built-in scope. |
| E-08 | `src/specify_cli/cli/commands/merge.py` already has a guarded `--skip-lanes` direct-on-target route, while `lanes.compute.is_planning_artifact_only` and merge execution already model planning-only lanes. | Reuse these completion mechanics; lifecycle metadata chooses the honest shape, never a fabricated WP. |
| E-09 | `runtime_bridge.py::_dn_decision_materialize` buffers and rolls back runtime state for strict retrospective refusal, but the issue's custom marker path can still return blocked while a later query reports `done`. | Terminal custom-step completion needs one atomic reduce/commit boundary, independent of retrospective policy mode. |
| E-10 | Architecture-pack D03→D06 handoff requires `mission_identity`, `dossier_materialization`, `work_packages`, `review`, `accept`, `merge`, and `retrospective`, and forbids fabricated host state. | The black-box acceptance fixture must prove these capabilities in a clean consumer before D06 claims compatibility. |

## Decisions

### D-01 — One resolution authority

All creation and run-start entry points resolve the requested type through charter
`resolve_mission_type_context`, yielding `ResolvedMissionType`. Runtime discovery may
remain responsible for loading the executable DAG, but it may not decide whether a type
exists, is activated, or is eligible for lifecycle creation independently. A discovered
`mission.yaml` whose key has no activated charter type is not a formal mission type and
must fail with a structured diagnostic.

This deliberately builds on #3831's org-aware resolution rather than reviving the legacy
`specify_cli.mission.Mission` object as authority. The known wider retirement in #2652
remains independent; this mission needs only the canonical activated-type result at the
formal lifecycle boundary.

### D-02 — One lifecycle contract, assembled from existing authorities

The resolved lifecycle contract is an immutable value owned below the CLI layer. It
contains canonical type identity and explicit lifecycle policy, while referencing these
existing projections rather than copying them:

- ordered steps and profile/contract bindings from the resolved/frozen mission template;
- artifact roles and blocking requirements from the resolved expected-artifact manifest;
- target/topology and mission identity from canonical mission metadata;
- review and transition behavior from step-contract bindings and status events;
- merge behavior from the lane manifest and the declared delivery mode.

The only new authored policy is the combination the system cannot infer safely:

- delivery mode: executable or planning-only;
- work-package policy: required, optional, or forbidden;
- gate applicability: required, optional, or not-applicable for implement, independent
  review, acceptance, merge, and retrospective.

The plan phase must choose the smallest schema home that keeps this under the charter
offering model. A new CLI-local YAML format or a second type registry is rejected.

### D-03 — Canonical materialization precedes run creation

For a new handle, `mission run` first materializes a canonical mission through the same
transactional core used by `agent mission create`, then starts the frozen runtime. For an
existing handle, it verifies the immutable mission type and lifecycle-contract identity
before attaching. It never rewrites a different mission's type (the corruption separately
tracked in #4965), never starts with null identity, and never uses `validate=False` as a
substitute for creation.

Creation failure is atomic: no run-index entry, partial dossier, orphan coordination
branch, or success envelope survives.

### D-04 — Artifact and dossier truth is manifest-driven

The expected-artifact manifest is already the canonical declaration of artifact key,
class, path pattern, step ownership, blocking status, and optional status. A custom
mission's formal lifecycle requires a resolvable manifest. Creation records its selected
type/provenance; dossier indexing and action guards resolve the same manifest through the
charter facade. A missing or malformed manifest fails before claiming a formal mission.

This mission does not redefine the artifact set for documentation or research and does
not claim to close #4906. If shared acceptance seams must be generalized to avoid a custom
special case, built-in behavior is covered for regression but the separate issue retains
its own acceptance claim until independently proven.

### D-05 — WP state follows declared policy

An executable, WP-required mission uses the existing tasks/finalize/status/lane machinery.
A planning-only mission may still use planning WPs and the existing planning-only lane
manifest. A no-WP mission creates an explicit canonical empty-WP lifecycle record and lane
shape (or another existing empty manifest representation selected in plan), and its
implement/review commands return a stable not-applicable result rather than "mission not
found" or "no tasks". No path may create dummy `tasks.md`, `WP01`, status events, or
lanes solely to pacify a software-dev gate.

### D-06 — Every mutating command consumes the resolved lifecycle contract

`implement`, `review`, `accept`, and `merge` resolve the same mission identity, selected
type, lifecycle policy, artifact manifest, and status/lane projection. Commands refuse
when an operator invokes a gate declared not-applicable or when required prior gates lack
evidence. Optional means explicitly skippable with durable reason/provenance, not silently
ignored. A custom type cannot fall back to software-dev's artifacts, action names, or WP
expectations.

### D-07 — Terminal advancement is atomic

The final custom step, retrospective outcome, runtime snapshot, emitted completion event,
and user-visible `done` state form one logical transition. If composition, artifact
validation, retrospective capture, or persistence blocks, the step remains resumable and
the reduced state is not terminal. A subsequent query must report the same blocked/current
state, never `done`. Replaying the successful terminal call is idempotent.

### D-08 — One black-box lifecycle proof is the release contract

The primary acceptance test uses the installed CLI in a clean temporary consumer and
separate processes for every command:

```text
install/activate custom type
  -> create canonical mission
  -> run planning steps
  -> finalize declared WPs
  -> implement
  -> independent review
  -> accept
  -> planning-only or executable merge
  -> retrospective
  -> query terminal state
```

It asserts the canonical ULID/directory/meta tuple, dossier/artifact projection, status
event provenance, lane manifest, acceptance evidence, target-branch baseline commit, frozen
step/profile resolution, and atomic terminal state. A paired no-WP arm proves explicit
accept/merge behavior without fake files. Negative controls cover unactivated type,
malformed lifecycle policy, missing manifest, cross-type attach, missing required gate,
and terminal-step failure.

## Rejected alternatives

1. **Teach only `mission run` to write more files.** Rejected because it duplicates
   `create_mission_core` and preserves two identity writers.
2. **Treat a custom type as software-dev with renamed steps.** Rejected because it
   fabricates tasks/artifacts and violates the architecture pack's host-neutral contract.
3. **Make every custom mission use WPs.** Rejected because no-WP and planning-only
   missions are explicit product requirements; fake WPs are false audit evidence.
4. **Infer lifecycle mode from filenames.** Rejected because absence is ambiguous and
   changes as artifacts appear; lifecycle policy must be frozen at creation.
5. **Persist synthesized contracts into the global doctrine repository at run time.**
   Rejected because runtime execution must not mutate authored doctrine and the frozen
   template already supplies deterministic recreation.
6. **Add custom-only branches to each CLI command.** Rejected because each branch would
   become another policy authority and drift from built-ins.

## Risks and open plan questions

- The exact schema home and field vocabulary for lifecycle policy must be checked against
  current `MissionType` projection and pack overlays; adding a separate artifact may be
  justified only if it remains a charter-owned, uniquely resolved component of
  `ResolvedMissionType`.
- `mission run` does not currently collect all human-facing fields accepted by `agent
  mission create`. The plan must define deterministic defaults or require pre-creation,
  while still satisfying the issue's requirement that run-start never succeeds with null
  identity.
- The no-WP lane representation must compose with accept and merge without weakening the
  existing fail-closed missing-`lanes.json` fix (#4891).
- #4965's existing-type overwrite defect is on the same entry path. This mission must not
  regress it; whether the minimal fix is folded or remains a prerequisite must be decided
  from the implementation dependency graph.
- #4906 overlaps the type-aware acceptance seam. This mission may generalize a shared
  primitive but must not over-claim that separate bug without its complete fixture.
- The architecture pack expects outcome-level review/acceptance semantics. The host bridge
  must preserve its producer-owned predicates and only provide lifecycle plumbing.

## Research exit criteria

Research is sufficient for specification when the spec preserves: single charter
authority; canonical materialization before runtime; explicit WP/no-WP and delivery modes;
manifest-owned artifacts; contract-driven command applicability; cross-process frozen
steps; atomic terminus; and the D06 clean-consumer evidence boundary. No unresolved
product choice changes those required outcomes.
