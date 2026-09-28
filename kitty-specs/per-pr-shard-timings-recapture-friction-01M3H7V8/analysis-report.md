---
schema_version: 1
artifact_type: spec-kitty.analysis-report
command: /spec-kitty.analyze
mission_slug: per-pr-shard-timings-recapture-friction-01M3H7V8
mission_id: 01M3H7V865DG4BNBKP2ETZSZ1A
generated_at: '2026-09-28T01:09:09.638957+00:00'
analyzer_agent: claude-sonnet-5-design-amendment
input_artifacts:
  spec.md:
    path: kitty-specs/per-pr-shard-timings-recapture-friction-01M3H7V8/spec.md
    sha256: 87190c606d80ed63ee4c94f911a552c49aa72d44e6e3f35b387ac47559662457
  plan.md:
    path: kitty-specs/per-pr-shard-timings-recapture-friction-01M3H7V8/plan.md
    sha256: cb1c5c0c4adb980e85fc3250622415afdb8c1ca94650e3b4bfe1f77bedec7cb8
  tasks.md:
    path: kitty-specs/per-pr-shard-timings-recapture-friction-01M3H7V8/tasks.md
    sha256: 570f8d48d4197d46afc12c085ae87797de6282348ebd6e1957d0f47c5eb23084
  charter:
    path: .kittify/charter/charter.yaml
    sha256: a2b2f62cf1c0fa8987b67f6759d18bcc18b2fb47a8d3ad2783f8fac68b192c77
verdict: ready
issue_counts:
  low: 0
  high: 0
  medium: 2
  critical: 0
  info: 0
findings:
- id: I1
  severity: medium
  category: inconsistency
  summary: WP02 frontmatter requirement_refs omits NFR-003, though tasks.md's WP02 header, WP02's own Objectives prose, and tasks.md's FR/NFR/Constraint traceability table all attribute NFR-003 to WP02.
- id: I2
  severity: medium
  category: inconsistency
  summary: tasks.md's traceability table credits WP03 (via T019) with partial ownership of NFR-001, but neither tasks.md's WP03 header line nor WP03.md's frontmatter requirement_refs lists NFR-001.
---

## Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | MEDIUM | `tasks/WP02-recapture-decision-script.md:5-16` (frontmatter `requirement_refs`) vs. `tasks.md:252-253` (WP02 header `**Requirements**:` line) vs. `tasks/WP02-recapture-decision-script.md:87-89` (Objectives prose) vs. `tasks.md:137` (traceability table row) | WP02's own YAML frontmatter `requirement_refs` list is `[FR-005..FR-010, C-001, C-003, C-004, C-005, C-006]` — it omits `NFR-003`. Yet tasks.md's WP02 header line ends "...C-006; NFR-003", WP02's own Objectives paragraph states "...and **NFR-003** (no credential leakage)", and tasks.md's FR/NFR/Constraint traceability table has a dedicated row "`NFR-003 (no credential leakage) \| WP02 \| T012, T013 \|`...". Three independent sources agree WP02 owns NFR-003; only the machine-readable frontmatter field disagrees. | Add `NFR-003` to WP02's frontmatter `requirement_refs` list so automated requirement-coverage/traceability tooling (e.g. `map-requirements`, coverage reports) sees the same ownership the prose and table already assert. No code-behavior change needed — T012/T013 already implement the no-credential-leakage behavior. |
| I2 | Inconsistency | MEDIUM | `tasks.md:135` (traceability table row) vs. `tasks.md:296-300` (WP03 header `**Requirements**:` line) vs. `tasks/WP03-scheduled-workflow-wiring.md:6-10` (frontmatter `requirement_refs`) | tasks.md's traceability table states "`NFR-001 (gate protects shard balance, not correctness) \| WP01, WP03 \| T002 (code shape, read-and-confirm), T019 (PR-body statement)`" — crediting WP03's T019 with a share of NFR-001. WP03's own body (T019 step 3, Review Guidance) does in fact discuss and require the NFR-001 shard-balance-only PR-body statement. But WP03's tasks.md header line ("**Requirements**: NFR-002, C-003, C-005, C-006 (workflow-file half); IC-04 (docs note)") and WP03.md's frontmatter `requirement_refs` (`[NFR-002, C-003, C-005, C-006]`) both omit NFR-001 — internally consistent with each other, but both disagree with the traceability table's explicit dual-WP attribution. | Either add `NFR-001` to WP03's header line and frontmatter `requirement_refs` (to reflect the traceability table's claim that WP03's T019 partially discharges it), or narrow the traceability table's row to list WP01 only and describe T019's NFR-001 mention as incidental PR-body content rather than requirement ownership. Either fix is a documentation-only change; T019's actual content is unaffected. |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | WP01 T002, T003, T005 | Verified against merged `#5240` code; production-function signatures and fixture shapes match the actual checkout. |
| FR-002 | Yes | WP01 T002, T008 | Unconditional `assert "charter" not in _MISMATCH_ALLOWLIST` confirmed present in checkout. |
| FR-003 | Yes | WP01 T004, T008 | Cross-module gate demotion confirmed in checkout (`_report_drift` called from both gate functions). |
| FR-004 | Yes | WP01 T002, T003, T003b, T004, T004b, T005, T006 | All three dispositions (disagree/agree/infra-break) covered for both gates; T003b/T004b restore the agreeing-case fixture a prior fresh-sweep found missing. |
| FR-005 | Yes | WP02 T012, T014 (fixture 5) | Truthy check ordering (before open-PR check and capture) explicitly specified in T013. |
| FR-006 | Yes | WP02 T010, T014 (fixtures 3, 6) | `has_drift` is a pure length-only comparator, matches spec's anti-noise requirement. |
| FR-007 | Yes | WP02 T011, T013, T014 (fixtures 1, 2), T015 (fixture 7) | Fixed-branch matching + TOCTOU re-check both specified; T011's superseded `--json number,headRefName` correction is self-documented (TASKS-FRESH2-001). |
| FR-008 | Yes | WP02 T009, T014 (fixture 4), T015 (fixtures 8, 9, 10) | `run_capture_or_die` catches `(Exception, SystemExit)`, re-raises `KeyboardInterrupt`; ordinary-failure-continues fixture present. |
| FR-009 | Yes | WP02 T009, T013 | `MODULE = "charter"` hardcoded constant, no `--module` flag exposed. |
| FR-010 | Yes | WP02 T013 | Fixed bot identity/commit message/PR body template, verbatim. |
| NFR-001 | Yes (attribution gap — see I2) | WP01 T002; WP03 T019 (per table only) | Table credits WP03; WP03 header/frontmatter do not. |
| NFR-002 | Yes | WP03 T016, T019, T020 | 30-min recapture budget + 10-min strict-mode budget, both with measured-evidence rationale. |
| NFR-003 | Yes (frontmatter gap — see I1) | WP02 T012, T013 | Header/prose/table agree; frontmatter `requirement_refs` omits it. |
| C-001 – C-006 | Yes | WP01/WP02/WP03 (see traceability table) | All six constraints mapped; frontmatter lists match tasks.md headers for every WP except the NFR-003 gap on WP02. |

**Charter Alignment Issues:** None found. Standing Order #5 (architectural gate discipline), Standing Order #2 (campsite cleaning), DIRECTIVE_044/045/050, and the Pre-existing Failure Reporting Rule were checked against spec.md/plan.md/tasks.md's specific citations — all citations resolve to real charter sections with matching content. `.github/workflows/protect-main.yml` was independently read and does perform the post-hoc "flags direct pushes to main" behavior spec.md's CL-001 describes (post-hoc commit inspection, not GitHub branch-protection blocking) — no overstatement found.

**Unmapped Tasks:** None found. Every subtask (T001–T020, including T003b/T004b) maps to at least one requirement, ruling point, or the FR/NFR/Constraint traceability table.

**Metrics:**

- Total Requirements (FR+NFR+C): 19 (10 FR, 3 NFR, 6 C)
- Total Tasks (subtasks): 22 (T001–T020 plus T003b, T004b)
- Coverage % (requirements with >=1 task): 100%
- Ambiguity Count: 0
- Duplication Count: 0
- Critical Issues Count: 0

## Verification notes (fresh, from scratch this run)

- Re-verified all four `pytest.raises(...)` call sites in WP01 (T005 x2, T006 x2): every one uses `pytest.raises(pytest.fail.Exception, ...)`, never bare `pytest.raises(Exception)`. Confirmed `pytest.fail()` raises `_pytest.outcomes.Failed` (subclass of `BaseException`, not `Exception`), so this is the only exception class that would actually catch it — no defect found here (the prior round's fix holds).
- Read the live `tests/architectural/test_module_length_agreement.py` on the current checkout and confirmed: `ShardTimingsDriftWarning`, `_strict_mode()`, `_report_drift()`, `_STRICT_ENV_VAR`, `_TIMINGS_PATH`, `_REGISTRY_PATH`, `_registry_modules()`, `_committed_length()` all exist exactly as WP01's T002/T003/T003b/T004/T004b/T005/T006 describe, and the production gate functions' actual parameter signatures/order match every illustrative fixture's positional-argument shape in WP01.
- Checked all three WP files' frontmatter `subtasks:` lists against their own body's `### Subtask T...` headers: all three are 1:1 (WP01: 10/10, WP02: 7/7, WP03: 5/5). No orphaned or missing subtask IDs.
- Grepped for `_charter_disposition` / `pytest.xfail` / "charter-only demotion" across spec.md, plan.md, tasks.md, and all three WP files: every live occurrence is explicitly framed as a dead/superseded design in amendment/history prose ("do not build", "originally specified", Activity Log entries) — no live reference asserts the old design is current.
- Confirmed `lanes.json`'s `write_scope` per lane matches each WP's `owned_files` frontmatter exactly, and `depends_on_lanes`/`parallel_group` match the WP `dependencies` fields (WP03 depends on WP02).
- Confirmed `docs/development/reference/known-friction-points.md` currently does contain the #5189/#5190 bullet WP03's T018 branches on — the "bullet IS present" path applies on this checkout.
- Confirmed SC-007's absence from spec.md's Success Criteria list is intentional and documented (`reviews/spec.ruling.md`: "SC-007 are deleted — they have no subject under this [ruling]"), not a numbering gap.
- All cross-referenced files (`reviews/amendment.ruling.md`, `reviews/spec.ruling.md`, `reviews/plan.ruling.md`, `reviews/tasks.ruling.md`, `tracer-approach.md`, `tracer-design-decisions.md`, `lanes.json`) exist and were spot-checked for the specific claims spec.md/plan.md/tasks.md make about them.

## Next Actions

- Both findings are MEDIUM (documentation/traceability-metadata drift, not a functional or charter defect) — this analysis's verdict is **ready**. Implementation is not blocked.
- Recommended (non-blocking) follow-up before/at implementation start: add `NFR-003` to WP02's frontmatter `requirement_refs` (I1), and reconcile WP03's NFR-001 attribution one way or the other (I2) — both are single-line frontmatter/table edits, not new work.
- No spec/plan/tasks rework is required to proceed to `/spec-kitty.implement`.

## Offer to Remediate

Should these two findings be addressed before moving on to implementation? I can suggest concrete remediation edits (a one-line frontmatter addition to WP02, and either a one-line frontmatter addition to WP03 or a one-line traceability-table edit) for either or both findings you want resolved — no edits have been applied automatically.
