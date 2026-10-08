---
schema_version: 1
artifact_type: spec-kitty.analysis-report
command: /spec-kitty.analyze
mission_slug: mission-writer-followups-01M4CYWW
mission_id: 01M4CYWW2JE17MK86TMYDR0FYH
generated_at: '2026-10-08T06:46:01.445607+00:00'
analyzer_agent: unknown
input_artifacts:
  spec.md:
    path: kitty-specs/mission-writer-followups-01M4CYWW/spec.md
    sha256: 966d3db5ae889ea5aaf4c91cb8d643ad350d9d4e7df85411cdc3cc76c89eb531
  plan.md:
    path: kitty-specs/mission-writer-followups-01M4CYWW/plan.md
    sha256: 94e380cffccf538da07390af5ade3f3f586474ecbc38b9d3312093e6cf4264f6
  tasks.md:
    path: kitty-specs/mission-writer-followups-01M4CYWW/tasks.md
    sha256: 742284208aad0d82214386015e0c7f256512be2baf17d6f025b592035b760362
  charter:
    path: .kittify/charter/charter.yaml
    sha256: 39e75cd05429257095cd1d6111fa75460e0430e5f147d3a97d8c921916bd76af
verdict: blocked
issue_counts:
  low: 4
  high: 1
  medium: 7
  critical: 0
  info: 0
findings:
- id: I1
  severity: high
  category: inconsistency
  summary: Binding amendment A7 lists open(...,'a') and os.replace onto a log/state target as Rule 1 sinks, but WP08 T034 declares append-only 'a' opens and the tmp-then-os.replace snapshot publish as structural near-misses.
- id: I2
  severity: medium
  category: inconsistency
  summary: data-model.md lock-key table predates A3/A4 (reads only feature_dir/meta.json, needs recorded mid8, silent fallback) and mislabels its invariant NFR-002.
- id: I3
  severity: medium
  category: inconsistency
  summary: "FR-010's stated red proof (FR-008's runtime scan goes red) is unrealizable: WP05 deletes the rollback before WP08 adds the runtime scan; tasks substitute T020 without updating the spec."
- id: I4
  severity: medium
  category: inconsistency
  summary: spec Assumptions say the analyze prompt is not rewritten, but FR-022 and WP16 T041 rewrite it.
- id: O1
  severity: medium
  category: underspecification
  summary: WP02 T009 rewires locked_acceptance_verdict_guard in acceptance/matrix.py, a file owned by WP04, not WP02.
- id: O2
  severity: medium
  category: underspecification
  summary: "owned_files omit files subtasks must edit: WP02 T008 (dead_symbol_allowlist.yaml, dead-setter tests), WP10 T047/C7 (tests/core/test_mission_creation_probe_order.py, test_mission_creation_fanout_commit_boundary.py, finalize commit-surface tests; test_next_command_integration.py is WP06's), WP01 T004 (coordination/legacy_resolution.py)."
- id: C1
  severity: medium
  category: coverage
  summary: "CLI-level acceptance the spec demands has no explicit subtask: SC-005/US7 via 'spec-kitty next --json'/'--result success', FR-002/FR-003/US1 overlap 'through the CLI', FR-012 finalize-tasks subject via CLI, FR-018 red 'pack fixture edit ignored by next'."
- id: D1
  severity: medium
  category: charter
  summary: Shared WP rules omit the charter Pre-existing Failure Reporting Rule (MUST open a GitHub issue) and the standing order to append mission tracer files during implementation.
- id: L1
  severity: low
  category: coverage
  summary: issue-matrix.json rows are all verdict 'unknown' and no WP subtask owns filling them before approval.
- id: L2
  severity: low
  category: coverage
  summary: 'Cross-cutting refs traced to one WP only: NFR-005 to WP15, C-006 to WP01, C-005 to WP12.'
- id: L3
  severity: low
  category: inconsistency
  summary: "Post-amendment drift: C-001 'keeps its current size' vs ledger 23->22; FR-016 'only on analyze' vs B5 board override; D1 'only a test' vs T004 routing; SC ids out of order."
- id: L4
  severity: low
  category: underspecification
  summary: WP08/WP15 say fix real-tree gate hits in other WPs' files, but WP15 owns only the gate test.
---

## Specification Analysis Report

Mission `mission-writer-followups-01M4CYWW`. Inputs: spec.md (FR-001..FR-023, NFR-001..NFR-006, C-001..C-008, SC-001..SC-009), plan.md (D1-D10 plus binding amendments A1-A12, B1-B8, C1-C13), research.md, data-model.md, tasks.md, 17 WP files, charter.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | plan.md A7; tasks.md T034; WP08 | A7 makes `open(..., "a")` and `os.replace` onto a log/state target sinks; T034 exempts append-only opens (`engine._append_event`, `status/store.py`) and the snapshot publish (`engine._write_snapshot`). Amendments are declared binding over WPs, so the implementer must pick one, and the real-tree empty-allowlist pass depends on it. | Amend A7 to state the append and fresh-snapshot structural exclusions T034 describes (or change T034) before WP08 starts. |
| I2 | Inconsistency | MEDIUM | data-model.md "Mission lock key"; plan A3, A4 | Data model still describes the D1 rule; A3 adds the mid8 cascade and a typed empty-mid8 error, A4 reads the canonical primary meta and reuses the held key. Invariant labelled NFR-002 (that is bounded waits). | Update data-model.md to A3/A4; fix the label. |
| I3 | Inconsistency | MEDIUM | spec FR-010; WP05 T020/T023; WP08 | The named red proof needs Rule 1's runtime scan, which lands after WP05 deletes the rollback. | Restate FR-010's red proof as T020's foreign-append cut, or add a runtime-scan red check in WP05. |
| I4 | Inconsistency | MEDIUM | spec Assumptions; FR-022; WP16 T041 | "Does not rewrite the prompt" conflicts with the analyze prompt rewrite. | Drop or reword the assumption. |
| O1 | Ownership | MEDIUM | WP02 T009; WP04 owned_files | `locked_acceptance_verdict_guard` is at `acceptance/matrix.py:770`, owned by WP04. | Move that change to WP04 T018, or add a handoff. |
| O2 | Ownership | MEDIUM | WP02, WP10, WP01 owned_files | Edited files missing from owned_files (see carrier). | Add them or record explicit handoffs. |
| C1 | Coverage | MEDIUM | SC-005, US1, US6, US7, FR-002/003/012/018 | Independent tests are bridge or helper level; the CLI-entry assertions the spec names are not tasked. | Add one CLI-entry test per item in WP07, WP04, WP10, WP06. |
| D1 | Charter | MEDIUM | WP shared rules; charter Pre-existing Failure Reporting Rule, Standing Order 3 | Omission, not contradiction. | Add both obligations to the shared rules. |
| L1 | Coverage | LOW | issue-matrix.json | All rows `unknown` (non-gating heads-up). | Assign row filling. |
| L2 | Traceability | LOW | requirement_refs | NFR-005, C-006, C-005 single-WP. | Add to code WPs or mark cross-cutting. |
| L3 | Inconsistency | LOW | spec C-001, FR-016, SC list; plan D1 | Wording drift. | Tidy on next spec edit. |
| L4 | Ownership | LOW | WP08/WP15 risks | "Fix it here" vs narrow owned_files. | Permit a recorded handoff. |

**Coverage Summary Table:**

| Requirement | Has Task? | WPs |
|-------------|-----------|-----|
| FR-001 | yes | WP02 |
| FR-002..FR-004 | yes | WP04 |
| FR-005 | yes | WP01, WP02, WP04 |
| FR-006, FR-019 | yes | WP15 |
| FR-007, FR-008 | yes | WP08 (WP13 T054) |
| FR-009..FR-011 | yes | WP05 |
| FR-012..FR-014 | yes | WP10 |
| FR-015 | yes | WP09 |
| FR-016 | yes | WP07 |
| FR-017 | yes | WP06, WP07 |
| FR-018 | yes | WP06 |
| FR-020 | yes | WP02, WP03, WP04, WP06 |
| FR-021 | yes | WP11 |
| FR-022 | yes | WP09, WP16, WP17 |
| FR-023 | yes | WP06, WP14 |
| NFR-001 | yes | WP02, WP04, WP05, WP13 |
| NFR-002 | yes | WP01, WP02, WP03, WP13 |
| NFR-003 | yes | WP01 |
| NFR-004 | yes | WP08, WP15 |
| NFR-005 | thin | WP15 + shared rules |
| NFR-006 | yes | WP06 |
| C-001, C-004 | yes | WP06, WP07 |
| C-002 | yes | WP01, WP13 |
| C-003 | yes | WP09, WP16, WP17 |
| C-005, C-007 | yes | WP12 |
| C-006 | thin | WP01 + shared rules |
| C-008 | yes | WP06 |
| SC-001..SC-009 | by text | see C1 |

The requirement_refs in all 17 WP files match tasks.md exactly. Every owned_files path exists or is in create_intent. Every lock-caller and meta/frontmatter sink file under src is owned by some WP, except `review/prompt_metadata.py`, which C-007 excludes. `"for feature"` operator strings are all in WP10-owned files.

**Charter Alignment Issues:** D1 (an omission). No MUST principle is contradicted.

**Unmapped Tasks:** none.

**Metrics:**

- Total Requirements: 37 (23 FR, 6 NFR, 8 C), plus 9 SC
- Total Tasks: 57 subtasks in 17 WPs
- Coverage: 100%
- Ambiguity Count: 1
- Duplication Count: 0
- Critical Issues Count: 0

## Next Actions

- Resolve I1 (amend A7 or T034) before WP08. It is the only finding that blocks.
- Fix I2, I3, I4, O1, O2, C1 and D1 with small artifact edits. Then re-run `/spec-kitty.analyze`, because any edit to the spec, plan or tasks makes this report stale.
