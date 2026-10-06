# Mission Specification: Charter offering, activation presets and the doctrine-to-charter cutover

**Mission Branch**: `issue-3732-charter-pack-rename`
**Created**: 2026-10-06
**Status**: Draft
**Input**: Issue #3732 (rename doctrine packs to charter packs), bound by ADR `docs/adr/4.x/2026-10-06-1-charter-offering-active-charter-and-activation-presets.md` (owner ruling, 2026-10-06); absorbs #4400, #5323, #5826, the legacy-key half of #4573 and the pack-path half of #5825. Requirement set confirmed by the owner in brief-intake mode on 2026-10-06.

## Bulk edit declaration

This mission renames the retired **doctrine pack** vocabulary to the **charter** vocabulary across the codebase, CLI, configuration, skills and documentation. Per-category rules (code symbols, import paths, filesystem paths, serialized keys, CLI commands, user-facing strings, tests and fixtures, logs and telemetry) are captured in `occurrence_map.yaml`, produced during plan from the classification ledger posted on #3732. Unlike a default bulk edit, CLI commands and serialized keys **are** renamed: the owner ruled a full cutover with no compatibility layer, and the upgrade migration (FR-012) is the consumer-protection mechanism.

## Domain Language

| Canonical term | Meaning | Replaces / do not use |
|---|---|---|
| **Charter offering** | Everything offered to a project: the Charter Packs it can draw from. | "doctrine" as the name of the offer-side tier |
| **Charter Pack** | A distributable bundle of interconnected charter components (artifacts and their DRG edges) with a set of activation presets; an org pack may also enforce activations. | "doctrine pack" |
| **Activation preset** | A named set of activations a Charter Pack ships, applied to a project by activating it. | "Pack Default Charter", "default charter pack", the old meaning of "charter pack" |
| **Active charter** | What a project has activated: its per-kind activation keys and mission-type activations. | the third meaning of "charter pack" (the project's activation state) |
| **Charter Bundle** | Unchanged: the materialised `.kittify/charter/` tree. | — |

"Active" / "inactive" still describe a single artefact's state; **active charter** names the project's activated set as a whole. "Doctrine" stays only where it means the governance content itself, in historical records, in `DIRECTIVE_039`, and in the `doctrine-daphne` profile name.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Apply a curated starting point from a pack (Priority: P1)

An operator setting up governance for a project wants a small, legible baseline instead of every built-in artifact. They run `spec-kitty charter activate --preset minimal` (the built-in pack is the default pack) and the project's active charter becomes the curated baseline. An operator whose organisation publishes its own Charter Pack runs `spec-kitty charter activate --pack <org-pack> --preset <name>` the same way.

**Why this priority**: presets are the user-facing heart of the new model, and the old path (`charter pack apply`) is removed by this mission.

**Independent Test**: in a fresh project, apply `--preset minimal`, then `--preset default`, then an org pack's preset; read the active charter back after each.

**Acceptance Scenarios**:

1. **Given** a fresh project, **When** the operator runs `spec-kitty charter activate --preset minimal`, **Then** the active charter equals the built-in pack's `minimal` preset and `spec-kitty charter list` shows it.
2. **Given** a project with the `minimal` preset active, **When** the operator runs `spec-kitty charter activate --preset default`, **Then** every built-in artifact is effective, including artifacts added to the built-in pack after the preset was written.
3. **Given** an org pack that ships a preset, **When** the operator activates it with `--pack <org-pack> --preset <name>`, **Then** the active charter matches that preset.
4. **Given** any project, **When** the operator runs `spec-kitty charter activate --preset does-not-exist`, **Then** the command fails, names the pack and lists its presets, and changes nothing.

---

### User Story 2 - Upgrade an existing project without losing anything (Priority: P1)

An operator upgrades a project created under the old vocabulary: config uses the legacy `doctrine.org.packs` key, charter governance uses `governance.doctrine.*`, project artifacts live in `.kittify/doctrine/`, and the per-kind activation keys may hold the stale `default.yaml` lists. They run `spec-kitty upgrade` once and keep working.

**Why this priority**: the cutover removes every read-side fallback, so the migration is the only thing standing between existing users and a broken project.

**Independent Test**: build a fixture project in the legacy shape, run the upgrade, and compare the effective artifact set before and after.

**Acceptance Scenarios**:

1. **Given** a legacy project, **When** `spec-kitty upgrade` runs, **Then** the config keys use the canonical names, project artifacts live in `.kittify/charter-packs/`, and the effective artifact set is unchanged.
2. **Given** a project whose activation lists equal the stale `default.yaml` contents, **When** the upgrade runs, **Then** those keys become absent and the newer built-in artifacts are effective again.
3. **Given** a project with a customised activation list, **When** the upgrade runs, **Then** that list is left exactly as it was.
4. **Given** an already-upgraded project, **When** the upgrade runs again, **Then** nothing changes.
5. **Given** a legacy project that has not been upgraded, **When** any charter command runs, **Then** it fails with an error naming `spec-kitty upgrade`.

---

### User Story 3 - One command surface for pack authors (Priority: P2)

A pack author validates and assembles their Charter Pack with `spec-kitty charter pack validate` and `spec-kitty charter pack assemble`, and checks the project's active charter with `spec-kitty charter check`. No step uses the `spec-kitty doctrine` group, which no longer exists.

**Why this priority**: today pack authors must use the deprecated group and see its banner on every call.

**Independent Test**: run every former `spec-kitty doctrine` workflow through its `charter` replacement; run each old spelling and see it fail as unknown.

**Acceptance Scenarios**:

1. **Given** a pack directory, **When** the author runs `spec-kitty charter pack validate <dir>`, **Then** it validates exactly as `doctrine pack validate` did.
2. **Given** any former `spec-kitty doctrine <command>`, **When** it is run, **Then** it fails as an unknown command.
3. **Given** a project, **When** the operator runs `spec-kitty charter pack list`, **Then** it shows each available pack and the presets it ships.

---

### User Story 4 - Agents read one vocabulary (Priority: P2)

An agent working in a consumer project loads skills and reads docs. Every skill name, command, config key and path it meets uses the charter vocabulary; none contradicts another.

**Why this priority**: mixed names are the problem the owner named; agents and harnesses then contradict themselves.

**Independent Test**: list the installed skills and scan shipped guidance for the retired names.

**Acceptance Scenarios**:

1. **Given** a freshly upgraded project, **When** the agent lists skills, **Then** it sees `spk-charter-*` and `spk-practice-*` and no `spk-doctrine-*` or legacy `spec-kitty-*` charter skills.
2. **Given** the shipped skills, packs and living docs, **When** they are scanned for the retired names, **Then** none remain outside the documented historical records.

---

### User Story 5 - Promotion keeps what was effective (Priority: P1)

The charter interview, the org-charter union and the unify-activation upgrade step each materialise an absent activation key. They write exactly what was effective at that moment, never a narrower list.

**Why this priority**: once the `default` preset lists nothing, these callers would otherwise seed from an empty set (#4400).

**Independent Test**: for each caller, start from an absent key with org packs present and compare the effective set before and after.

**Acceptance Scenarios**:

1. **Given** an absent activation key and a declared org pack, **When** each caller promotes the key, **Then** every artifact effective before is still effective after.

---

### Edge Cases

- A project that has both `.kittify/doctrine/` and `.kittify/charter-packs/`: the migration merges without overwriting and reports any id present in both.
- A project with the canonical and legacy config keys both present: the canonical value wins; the legacy key is removed and reported.
- A preset that names an artifact the pack does not ship: activation fails and names the missing id; nothing is written.
- An org pack fetched from the public-packs repository without a `presets/` directory: the pack works; it simply offers no presets.
- A project whose activation list is the stale `default.yaml` list plus one customisation: it is not the stale list, so it is left untouched and reported for the operator to review.
- A saved script that calls `spec-kitty doctrine fetch`: it fails as an unknown command (no alias, by ruling); the changelog Before/After names the replacement.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Title | User Story | Priority | Status | Delivery | No-op passable? |
|----|-------|------------|----------|--------|----------|-----------------|
| FR-001 | Activate a preset | As an operator, I want `spec-kitty charter activate --pack <pack> --preset <preset>` (with `--pack` defaulting to `built-in`) to apply a pack's activation preset so that I can start from a curated baseline. | High | Open | [build] | no |
| FR-002 | Built-in presets as pack data | As an operator, I want the built-in pack to ship `default` and `minimal` presets as pack data, where `default` lists no artifact ids (every built-in artifact is effective, plus the built-in mission types), so that the default can never drift from what ships. | High | Open | [build] | no |
| FR-003 | Init equals the default preset | As an operator, I want skipping charter activation during `spec-kitty init` to leave the project exactly as `--preset default` would, reading the mission types from the built-in pack's `default` preset, so that both paths agree. | High | Open | [ratchet] | yes — paired with FR-002's preset-content check on the same fixture |
| FR-004 | Presets from any pack | As a pack author, I want presets discovered from any pack (built-in, org, fetched from the public-packs repository) and listed by `spec-kitty charter pack list` so that my pack can ship its own starting points. | High | Open | [build] | no |
| FR-005 | Retire the preset registry | As a maintainer, I want the hard-coded preset registry, the `src/charter/activation/packs/` files, `charter pack apply` and the `accompanies_doctrine_pack` descriptor field removed so that presets have one home. | Medium | Open | [build] | no |
| FR-006 | Charter homes for pack commands | As a pack author, I want `charter pack validate/assemble/list/path`, `charter check` (from `consistency-check`), and `charter` homes for `regenerate-graph` and `asset`, so that no workflow needs the deprecated group. | High | Open | [build] | no |
| FR-007 | Remove the doctrine command group | As an operator, I want `spec-kitty doctrine` removed so that only one command surface exists; old spellings fail as unknown commands. | High | Open | [build] | no |
| FR-008 | Skill families | As an agent, I want the charter-governance skills named `spk-charter-{governance,glossary,profile-load,spdd-reasons}` and the practice skills `spk-practice-{bulk-edit,semantic-compression,show-me}`, with the older `spec-kitty-*` charter skills folded in and deleted and generated agent copies regenerated, so that each skill has one name. `doctrine-daphne` is unchanged. | High | Open | [build] | no |
| FR-009 | Three meanings, three names | As a maintainer, I want the code to separate Charter Pack, activation preset and active charter, renaming `CharterPackManager`, `CharterPackConfigError` and the error code `CHARTER_PACK_CONFIG_INVALID` accordingly, so that one word means one thing. | Medium | Open | [build] | no |
| FR-010 | Rename retired-tier wording | As an agent or contributor, I want retired-tier "doctrine" wording in living code, packs and docs renamed per the occurrence map, including the `src/specify_cli/doctrine/` module, so that no living surface uses the retired name. | High | Open | [build] | no |
| FR-011 | Remove read-side shims | As a maintainer, I want the `doctrine.org.packs`, `governance.doctrine.*` and `.kittify/doctrine/` read fallbacks removed, with an error naming `spec-kitty upgrade` for an unmigrated project, so that there is one supported shape. | High | Open | [build] | no |
| FR-012 | One upgrade migration | As an operator, I want one idempotent upgrade migration to rewrite legacy config keys (including this repository's own `doctrine.org.packs`), move `.kittify/doctrine/` to `.kittify/charter-packs/` and reset activation lists that equal the stale `default.yaml` to absent, so that my project keeps working after the cutover. | High | Open | [build] | no |
| FR-013 | Glossary and citations | As a reader, I want the glossary to define charter offering, Charter Pack, activation preset and active charter, and the citations of the missing ADR 2026-08-22-2 repointed, so that the terms have one canonical definition. | Medium | Open | [build] | no |
| FR-014 | Reachability pins | As a maintainer, I want the stale `test_reachability.py` pins re-asserted against the new default preset or deleted, so that no unasserted pin remains (#5323 item 2). | Low | Open | [build] | no |
| FR-015 | Promotion seeds from the effective set | As an operator, I want the interview, org-charter union and unify-activation promotion of an absent key to seed from the effective set (the #4399 seam), not from `default.yaml`, landing no later than FR-002, so that promotion never drops what was effective (#4400). | High | Open | [build] | no |
| FR-016 | Pack-path constants | As a maintainer, I want the project pack directory and the pack-relative paths (`drg/fragment.yaml`, `org-charter.yaml`, the presets directory) defined once and used everywhere this mission touches, so that the `.kittify/charter-packs/` move has one home (path half of #5825). | Medium | Open | [build] | no |

### Non-Functional Requirements

| ID | Title | Requirement | Category | Priority | Status |
|----|-------|-------------|----------|----------|--------|
| NFR-001 | Effective set preserved | For every legacy fixture project (at least: legacy keys only, legacy directory only, stale default lists, customised lists, mixed canonical and legacy), the effective artifact set after upgrade equals the set before, except that stale default lists regain the newer built-in artifacts; 0 artifacts lost. | Reliability | High | Open |
| NFR-002 | Gates stay empty | Every vocabulary and boundary gate touched by this mission closes with an empty allowlist, and a gate forbids the retired names on living surfaces with 0 exemptions beyond the documented historical roots. | Maintainability | High | Open |
| NFR-003 | CLI latency | `spec-kitty charter activate --preset <name>` and `spec-kitty charter pack list` complete in under 2 seconds on a project with the built-in pack plus two org packs. | Performance | Medium | Open |
| NFR-004 | Migration idempotence | Running the upgrade migration a second time changes 0 files. | Reliability | High | Open |

### Constraints

| ID | Title | Constraint | Category | Priority | Status |
|----|-------|------------|----------|----------|--------|
| C-001 | No compatibility layer | No alias commands, alias skills, redirect stubs or read-side fallbacks; a one-time upgrade migration is allowed (owner ruling, ADR 2026-10-06-1 §7). | Business | High | Open |
| C-002 | Historical records immutable | `kitty-specs/` of other missions, released changelog sections, ADRs, dated reports and the archive keep their wording. | Business | High | Open |
| C-003 | Pack tiers | `packs/built-in` ships to consumers and `packs/internal` does not; nothing maintainer-only moves into `packs/built-in`. | Technical | High | Open |
| C-004 | Names kept | The `doctrine-daphne` profile id and name, and `DIRECTIVE_039`, are unchanged. | Business | Medium | Open |
| C-005 | Out of scope | The Walk-B half of #4573, the built-in/builtin tier spelling (#5825), #5823 and #5824 are not part of this mission. | Business | Medium | Open |

### Key Entities

- **Charter Pack**: a pack directory with artifacts, DRG edges, a descriptor, optional enforced activations (org packs) and a set of activation presets.
- **Activation preset**: a named, pack-local set of activations; may leave a kind unrestricted (absent) or list ids; may list mission types.
- **Active charter**: the project's per-kind activation keys and mission-type activations.
- **Legacy project state**: legacy config keys, the `.kittify/doctrine/` directory and stale default activation lists, all rewritten once by the upgrade migration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can switch a project between the `minimal` and `default` presets with one command each, and the active charter matches the preset exactly in 100% of fixture runs — [build] · no-op passable: no
- **SC-002**: After upgrading each legacy fixture project, 0 previously effective artifacts are lost, and stale-default fixtures regain all built-in artifacts shipped at the time of the upgrade — [build] · no-op passable: no
- **SC-003**: 0 occurrences of the retired names remain on living surfaces outside the documented historical roots, measured by the mission's vocabulary gate — [build] · no-op passable: no
- **SC-004**: Every workflow that used `spec-kitty doctrine` before the mission has a working `spec-kitty charter` equivalent, verified one by one — [build] · no-op passable: no

## Assumptions

- The built-in pack stays bundled with the CLI; other packs, including those from the public-packs sidecar repository, arrive through `spec-kitty charter fetch`.
- `spec-kitty upgrade` is the only supported path from a pre-cutover project; the changelog carries the Before/After table for every renamed command and skill.
- The occurrence map is derived from the 2026-10-06 classification ledger (measured at `b327f5bb`) and re-derived at the mission's base before implementation.
