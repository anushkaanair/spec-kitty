# Data model: Canonical custom-mission lifecycle

**Status**: research model; field names remain subject to plan-time schema placement.  
**Authority rule**: every relationship below points to an existing authority. The model
does not authorize duplicate copies in CLI modules.

## 1. Resolved mission type

An immutable charter result identifying one activated mission type.

| Attribute | Meaning | Authority |
|---|---|---|
| `mission_type` | Canonical ASCII key | `ResolvedMissionType` |
| `provenance` | Winning pack/project layer | charter resolver |
| `action_sequence` | Ordered public lifecycle actions | mission-step projection |
| `template_set` | Planning template mapping | mission-step projection |
| `expected_artifacts` | Artifact completeness contract | manifest loader |
| `step_contracts` | Ordered authored step-contract identifiers | step-contract repository |
| `lifecycle` | Explicit execution/WP/gate policy | new charter-owned slot or composed charter artifact |

Invariant: one activated type yields one result. No caller is permitted to re-resolve a
different type from directory presence or default to software-dev after this result exists.

## 2. Mission lifecycle policy

The minimal policy that cannot safely be inferred from existing artifacts.

| Attribute | Candidate values | Rule |
|---|---|---|
| `delivery_mode` | `executable`, `planning_only` | Planning-only delivery may merge artifacts but executes no implementation payload. |
| `work_package_policy` | `required`, `optional`, `forbidden` | Forbidden is the explicit no-WP lifecycle; absence is not enough. |
| `implement_gate` | `required`, `optional`, `not_applicable` | Must agree with delivery and WP policy. |
| `review_gate` | `required`, `optional`, `not_applicable` | Required review must carry independent reviewer evidence. |
| `accept_gate` | `required`, `optional` | Formal missions always have an explicit terminal acceptance policy. |
| `merge_gate` | `required`, `optional`, `not_applicable` | The selected merge path must agree with topology and delivery mode. |
| `retrospective_gate` | `required`, `optional` | Completion is atomic with its declared retrospective outcome. |

Candidate invariants for plan validation:

- `delivery_mode=executable` plus `work_package_policy=forbidden` may be valid only when
  executable steps own their own durable state; otherwise reject.
- `work_package_policy=forbidden` requires implement/review to be `not_applicable` unless
  the contract declares a non-WP review surface.
- a required gate must have a canonical evidence source;
- `not_applicable` is a declared state with a structured command response, not absence;
- invalid combinations fail before mission identity or run state is written.

## 3. Canonical mission instance

| Attribute | Meaning |
|---|---|
| `mission_id` | Immutable ULID identity |
| `mid8` | First eight identity characters, derived once |
| `mission_slug` | Canonical `<human-slug>-<mid8>` directory name |
| `mission_type` | Exact resolved type key |
| `lifecycle_fingerprint` | Digest or stable identity of the frozen resolved lifecycle policy |
| `target_branch` | Canonical branch-integration target |
| `topology` | `single_branch`, `lanes`, `coord`, or `lanes_with_coord` |
| `created_at` | UTC creation time |

The mission instance owns identity only. It references its resolved type/lifecycle; it does
not copy artifact lists or step definitions into `meta.json` unless a frozen fingerprint or
provenance reference is needed for drift detection.

## 4. Frozen runtime definition

The existing `mission_template_frozen.yaml` plus snapshot metadata are the durable source
for step order and cross-process step/profile/contract recreation.

| Attribute | Meaning |
|---|---|
| `template_hash` | SHA-256 of frozen template bytes |
| `mission_key` | Must equal canonical instance type |
| `steps` | Frozen DAG including dependencies, profile bindings, inputs, and contract refs |
| `completed_steps` | Durable completed-step identities |
| `issued_step_id` | Current resumable step, if any |
| `blocked_reason` | Structured current blockage, if any |

Invariant: type mismatch between instance, run index, snapshot, and frozen template refuses
before mutation. A process-local synthesized-contract registry may overlay lookups but is
never durable authority.

## 5. Expected artifact manifest and dossier

The existing manifest is the authored contract; the dossier is its indexed projection.

```text
ResolvedMissionType.expected_artifacts
              |
              v
ExpectedArtifactManifest ----> ArtifactRef[] ----> MissionDossierSnapshot
 (key/class/path/blocking)       (hash/presence)    (completeness/parity)
```

Required and optional artifacts retain their declared class and step. A lifecycle gate
queries this projection for its own action; it does not ask for hard-coded filenames.

## 6. Work-package lifecycle projection

For `required` or selected `optional` WP policy:

- authored task prompts define WPs and dependencies;
- `status.events.jsonl` is the event authority;
- `lanes.json` is the merge/topology projection;
- review records carry independent verdict provenance;
- the acceptance matrix is required when declared by the lifecycle contract.

For `forbidden` WP policy:

- the mission has an explicit empty-WP lifecycle projection;
- implement/review commands return `not_applicable` with type and policy provenance;
- acceptance evaluates declared artifacts/gates rather than task files;
- merge uses the declared planning/no-WP completion path;
- no synthetic WP, checkbox, or lane transition is emitted.

## 7. Gate evidence

Each applicable lifecycle gate produces or consumes a durable evidence record:

| Gate | Minimum evidence |
|---|---|
| Implement | declared WP/status transition or declared non-WP execution outcome |
| Review | reviewer identity distinct from implementer when required; verdict and reviewed revision |
| Accept | artifact completeness, declared acceptance criteria, negative invariants, and prior-gate status |
| Merge | accepted mission, target branch, topology/lane or no-WP policy, resulting baseline commit |
| Retrospective | completed/skipped/failed outcome consistent with policy and terminal reduction |

## 8. Terminal transition

The terminus is a transaction over:

1. final issued-step completion;
2. composition/step guard result;
3. retrospective outcome;
4. `state.json` reduction;
5. `run.events.jsonl` append;
6. externally emitted completion moment.

If any required part refuses or fails, none of 4–6 may describe the mission as done. A
retry from the same pre-terminal state is deterministic and does not duplicate success
events.

## 9. Relationships

```text
Activated charter type
  -> ResolvedMissionType
      -> MissionLifecyclePolicy
      -> ExpectedArtifactManifest
      -> MissionStep/Contract projections
  -> CanonicalMissionInstance
      -> FrozenRuntimeDefinition
      -> WorkPackageLifecycleProjection (required/optional only)
      -> MissionDossier
      -> GateEvidence
      -> TerminalTransition
```

Cardinality rules:

- one mission instance has exactly one immutable mission ID and selected type;
- one live runtime index entry belongs to at most one mission ID;
- one instance has exactly one frozen runtime definition per run;
- zero or more WPs are allowed only as declared by policy;
- every required gate has at least one durable evidence record;
- a terminal mission has one successful atomic terminus outcome.
