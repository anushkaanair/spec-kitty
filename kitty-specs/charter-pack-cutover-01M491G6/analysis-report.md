---
schema_version: 1
artifact_type: spec-kitty.analysis-report
command: /spec-kitty.analyze
mission_slug: charter-pack-cutover-01M491G6
mission_id: 01M491G6102N7NRMAW3219Z2F9
generated_at: '2026-10-06T19:48:15.653794+00:00'
analyzer_agent: unknown
input_artifacts:
  spec.md:
    path: kitty-specs/charter-pack-cutover-01M491G6/spec.md
    sha256: dbe4e34a99472e03fe23e332aaf2445a77c8f2fe2f1c30e5209e710d078edcd4
  plan.md:
    path: kitty-specs/charter-pack-cutover-01M491G6/plan.md
    sha256: 10495adc85ae3d7608ad549592a2399c69751fc9566464eca1fce997cd4ed6a2
  tasks.md:
    path: kitty-specs/charter-pack-cutover-01M491G6/tasks.md
    sha256: 4ed09fd18fa44d48534dbb368e7f789c8a50d82657c88f6179e9597bb19f0a59
  charter:
    path: .kittify/charter/charter.yaml
    sha256: 39e75cd05429257095cd1d6111fa75460e0430e5f147d3a97d8c921916bd76af
verdict: ready
issue_counts:
  medium: 4
  high: 0
  low: 7
  critical: 0
  info: 0
findings:
- id: I1
  severity: medium
  category: inconsistency
  summary: Spec edge case tells pre-upgrade lane worktrees to rebase after the root upgrade; plan, contracts/cli.md, quickstart and WP24 say merge the target and never rebase.
- id: C1
  severity: medium
  category: coverage
  summary: FR-016 path-allowlist entries WP03 assigns to WP25 (about 9 pack-relative literal sites) have no WP25 subtask that repoints them, yet WP25 must close the allowlist empty.
- id: A1
  severity: medium
  category: ambiguity
  summary: WP17 leaves to the implementer whether an org-charter.yaml declaring schema_version 1 still validates; this is a consumer-visible compatibility rule that no spec, contract or decision fixes.
- id: D1
  severity: medium
  category: charter
  summary: The charter requires __all__ in every src/charter module, but WP07 (offering/packs/presets.py) and WP08 (activation/preset_application.py) give no __all__ guidance, and no gate enforces it.
- id: I2
  severity: low
  category: inconsistency
  summary: Plan Technical Context and spec OD-10 say about 19 work packages; tasks.md has 25.
- id: I3
  severity: low
  category: inconsistency
  summary: 'Plan IC-08 (package split) is sequenced after IC-03 and IC-06, but tasks puts WP04/WP05 before WP06 and WP13 (deliberately: the move carries the default_pack import).'
- id: I4
  severity: low
  category: inconsistency
  summary: WP05 says FR-005 deletes charter.activation.default_pack later in WP13; WP09 deletes it, and WP13 only verifies.
- id: U1
  severity: low
  category: underspecification
  summary: Per WP12, a reportable [] makes detect() true, but resets run only on the first application; after an operator follows the report and restores a deliberate [], detect() stays true forever.
- id: U2
  severity: low
  category: underspecification
  summary: The FR-018 closed token list leaves out some renamed spellings (CLI --kind doctrine-skill, state surface project_doctrine_graph, DefaultCharterPackMissingError, LegacyDoctrineRootWarning); they are guarded only by per-WP tests.
- id: C2
  severity: low
  category: coverage
  summary: WP01 acceptance test test_fr011_exempt_invocations covers only upgrade/init/--version/--help; the merge-driver and hook exemptions in FR-011 are tested only in WP14 unit tests.
- id: I5
  severity: low
  category: inconsistency
  summary: occurrence_map.yaml exceptions and moves leave out the FR-018 tombstone files (skills/retired.py, offering/packs/retired_fields.py), the tests/doctrine -> tests/charter_offering move and the kernel/doctrine_root.py replacement.
---

## Specification Analysis Report

Mission `charter-pack-cutover-01M491G6` (#3732). Artifacts analysed: spec.md, plan.md, tasks.md, data-model.md, contracts/ (cli, errors, upgrade-migration, activation-preset schema), occurrence_map.yaml, research.md, tasks/WP01–WP25 prompts and frontmatter, and the project charter. Three squad rounds already ran: post-spec, post-tasks, and the post-tasks fold. Findings that the fold resolved were checked against the artifacts and are not reported again. Spot checks that confirmed fold resolutions:

- NFR-001 is amended with the per-fixture relation.
- `anti_patterns` is in the preset schema.
- contracts/cli.md gained the flag rules, the `--json` shapes and the error format.
- contracts/upgrade-migration.md gained the re-selection rule and the `migration_reports` keys.
- WP frontmatter dependencies match the fold table.
- No `rc7` mention remains.
- T115 (public-packs sidecar PR) exists.
- The `test_fr010_retired_identifiers_absent` scans are assigned to WP19–WP22.
- The unmarked regression guards are listed in WP01.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | MEDIUM | spec.md:126 vs plan.md:108, contracts/cli.md:68-71, quickstart.md:12, tasks/WP24:180 | The spec edge case "Lane worktrees created before the upgrade" names the remedy as "upgrade the worktree, or rebase the lane after the root upgrade". Every downstream artifact says to merge the upgraded target into the lane and never rebase, because a rebase loses the approval stamp (`APPROVAL_STAMP_NOT_ON_LANE`). | Change the spec edge case to the contract wording ("upgrade the repository root and merge the target into the lane; do not rebase"). The implementers follow the contract, so this is spec hygiene, not a blocker. |
| C1 | Coverage | MEDIUM | tasks/WP03:193; tasks/WP25 T113 | WP03 seeds `charter_pack_path_allowlist.yaml` with pack-relative literal sites outside the old package and names WP25 as their owner "unless a WP touching the file removes them first". The sites are `drg_activation.py:163`, `_drg_helpers.py:177`, `org_pack_loader.py:536`, `org_pack_discovery.py:158,269`, `mission_step_contracts/executor.py:583` and `_doctrine_collect.py:94,141,173`. WP25 T113 only checks that the allowlist is empty and its owned file is the vocabulary gate. No subtask enumerates or repoints these sites, so NFR-002's "FR-016 allowlist empty" can turn red at closeout with the work unassigned. | Add a WP25 step, or a step in WP19/WP20/WP21 (which touch these files), that repoints each listed site to `kernel.charter_pack_paths` and deletes its allowlist row. Alternatively, re-key each entry's owner to the rename WP that edits that file. |
| A1 | Ambiguity | MEDIUM | tasks/WP17:251; spec OD-1; contracts/errors.md | OD-1 says to bump the org-charter `schema_version`. WP17 leaves to the implementer whether a `schema_version: 1` file without `doctrine_pack_id` still validates ("recommended: yes … record"). That choice decides whether every third-party org pack breaks on the cutover, and WP24's runbook and changelog depend on it. | Fix the rule in contracts/errors.md or data-model.md before WP17 starts: v1 files validate and only the `doctrine_pack_id` field is rejected, which is the WP17 recommendation. Then add a WP01/WP17 test for it. |
| D1 | Charter alignment | MEDIUM | charter.md "`__all__` Declaration Convention (binding per C-007)"; tasks/WP07, tasks/WP08 | The charter says every module under `src/charter/` and `src/kernel/` MUST declare `__all__`. WP02, WP04–WP06, WP09, WP14 and WP17 cover it for their modules. WP07 (`charter/offering/packs/presets.py`) and WP08 (`charter/activation/preset_application.py`) do not mention it, and no architectural gate checks that `__all__` is present. | Add an "every new `src/charter` module declares `__all__`" line to WP07 and WP08, and a review checklist item. This is an omission, not a conflict: no artifact contradicts the rule. |
| I2 | Inconsistency | LOW | plan.md:26; spec.md OD-10 | Both say "~19 work packages"; tasks.md has 25. | Update the plan figure, or leave it as historical. |
| I3 | Inconsistency | LOW | plan.md IC-08 vs tasks.md dependency graph | IC-08 is sequenced after IC-03 and IC-06, but WP04/WP05 run before WP06 and WP13. The tasks order is deliberate: WP05 carries the `default_pack` import, which is legal inside `charter`. | Optionally align the plan IC-08 line with the tasks order. |
| I4 | Inconsistency | LOW | tasks/WP05:164 vs WP06:116, WP09:155-163 | WP05 says WP13 deletes `default_pack`. WP09 deletes it and WP13 only verifies. | Correct the attribution in WP05 if the prompt is edited again. |
| U1 | Underspecification | LOW | contracts/upgrade-migration.md:12,23; tasks/WP12:168-169 | `detect()` counts a reportable `[]` as actionable, but resets are first-application-only. A deliberate `[]` restored after the cutover (as the reset warning tells operators to do) leaves `detect()` true permanently. Runner selection is unaffected (recorded as applied, and the structural predicate is false), but dry-run and doctor output could report a pending migration. | Count `[]` and snapshot resets in `detect()` only while the first-application marker is unset. Add the restored-`[]` case to the NFR-004 tests. |
| U2 | Underspecification | LOW | spec.md FR-018 closed lists; contracts/cli.md:22 | Renamed consumer-visible spellings missing from the closed token list: `--kind doctrine-skill`, `project_doctrine_graph`, `DefaultCharterPackMissingError`, `LegacyDoctrineRootWarning`, `LegacyTrackerOwnershipKeyWarning`. Only per-WP acceptance tests guard them. | Accept as is, since the list is closed by spec and other tests cover these. Or add them in a later spec revision before WP25. |
| C2 | Coverage | LOW | tasks/WP01:329; tasks/WP14:170-177 | The acceptance-level exempt test lists only `upgrade`, `init`, `--version` and `--help`. The merge-driver and hook exemptions that FR-011 and US2-5 name are tested only in WP14's own unit tests. | Optionally extend the WP01 regression guard with a `merge-driver-*` invocation and the hook entry points. |
| I5 | Inconsistency | LOW | occurrence_map.yaml exceptions/moves | The map leaves out the FR-018 tombstone files, the `tests/doctrine/` → `tests/charter_offering/` move (WP23) and the `kernel/doctrine_root.py` → `kernel/charter_pack_paths.py` replacement. The category rules cover them implicitly. | Add do_not_change entries for the tombstones and the two moves so the map matches spec FR-018 and the WP23 plan. |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 activate-a-preset | Yes | WP08 (T041–T045), WP01 T004 | OD-6 diff, flag rules and JSON per contract |
| FR-002 built-in-presets-as-pack-data | Yes | WP07 (T037, T040) | After FR-015 (WP06) |
| FR-003 init-equals-default-preset | Yes | WP09 (T046–T049) | Positive control present |
| FR-004 presets-from-any-pack | Yes | WP07 T036, WP08 T043 | |
| FR-005 retire-preset-registry | Yes | WP06 T033, WP09 T048, WP13 T066–T069 | After snapshots and rc35 neutralised (WP10) |
| FR-006 charter-homes | Yes | WP15 (T075–T079) | |
| FR-007 remove-doctrine-group | Yes | WP16 (T080–T082) | After FR-006 |
| FR-008 skill-families | Yes | WP18 (T088–T091), WP12 T063 | 13 retired names |
| FR-009 three-names | Yes | WP17 (T083–T087) | |
| FR-010 rename-retired-tier | Yes | WP04, WP05, WP17, WP19–WP23 | |
| FR-011 remove-read-side-shims | Yes | WP14 (T070–T074) | After FR-012 |
| FR-012 one-upgrade-migration | Yes | WP10, WP11, WP12 | Run-first plus structural re-selection |
| FR-013 glossary-and-citations | Yes | WP24 T107 | |
| FR-014 reachability-pins | Yes | WP25 T112 | |
| FR-015 promotion-from-effective-set | Yes | WP06 (T030–T034) | |
| FR-016 project-pack-root | Yes | WP02, WP03 | Allowlist drain gap, see C1 |
| FR-017 messaging | Yes | WP24 T108, T109 | |
| FR-018 vocabulary-gate | Yes | WP25 T111 | After FR-008 |
| FR-019 preset-format | Yes | WP07 T035, T038, T039 | |
| NFR-001 effective-set-preserved | Yes | WP01 T002–T003, WP12 T065 | Golden "before" sets frozen at base |
| NFR-002 gates-close-empty | Yes | WP05 T028, WP16, WP25 T113 | See C1 |
| NFR-003 cli-latency | Yes | WP08 T045 | `timing` marker, success precondition |
| NFR-004 upgrade-idempotence | Yes | WP11 T060, WP12 T065 | See U1 |
| SC-001..SC-005 | Yes | WP08, WP12, WP25, WP15, WP24 | |

Constraints C-001..C-008 are reflected in the WP ordering and prompts. The C-008 edges were verified against the dependency graph: FR-015→FR-002, FR-016→FR-011/012, FR-012→FR-005/011, FR-006→FR-007 and FR-008→FR-018 all hold.

**Charter Alignment Issues:**

- D1 (MEDIUM): the guidance that new `src/charter` modules declare `__all__` is missing from WP07 and WP08.
- No artifact conflicts with a charter MUST. The following are all present:
  - ATDD-first (C-006: WP01 strict-xfail suite, red-first commits).
  - Mission tracer files (`traces/`).
  - Non-vacuous gates with floors and planted self-tests (FR-016, FR-018).
  - Burn-down with empty allowlists (NFR-002).
  - User customisation preservation: customised lists kept, edited skill copies kept, hash-matched removal only, user path values never rewritten.
  - Pack tiers (C-003).
  - The per-WP test policy (`NO_FULL_HEAVY_SUITES_IN_MISSION`).

**Unmapped Tasks:** none. Every T001–T115 maps to a requirement through its WP's `requirement_refs`. T115 maps to OD-2 and FR-017.

**Metrics:**

- Total Requirements: 23 (19 FR + 4 NFR); plus 8 constraints and 5 success criteria
- Total Tasks: 115 subtasks in 25 work packages
- Coverage %: 100% (23/23 requirements have at least one task)
- Ambiguity Count: 1 (A1)
- Duplication Count: 0
- Critical Issues Count: 0 (high: 0)

**Issue-matrix heads-up (non-gating):** the artifacts cite #3732, #4400, #5323, #5826, #4573, #5825 and #5409 as addressed or bound issues. #5823, #5824, #5828 and #5830 are cited as out of scope or follow-up. #5457, #4836 and others are context-only. Bare references to issues this mission addresses will need issue-matrix rows before their owning WPs are approved; follow-up and context citations need none.

### Next Actions

- No CRITICAL or HIGH findings. Implementation (WP01) can start.
- Recommended before the affected WPs start:
  - A1 before WP17: fix the org-charter `schema_version: 1` acceptance rule in contracts/errors.md or data-model.md.
  - C1 before WP19–WP21 or WP25: give the WP25-owned FR-016 allowlist sites an explicit repointing step.
  - I1 at any time: correct the spec edge case to "merge, do not rebase".
  - D1 before WP07/WP08: add the `__all__` line to those prompts.
- The LOW items are optional hygiene. They can be folded into the next artifact edit, or left as is.
