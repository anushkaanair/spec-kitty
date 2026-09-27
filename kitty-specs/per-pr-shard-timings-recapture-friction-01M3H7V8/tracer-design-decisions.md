# Tracer: design decisions and drift

## Branch-naming drift (charter vs. sk-skill doctrine) — MUST record per dispatch

The charter's Collaboration Strategy section mandates `issue-<n>-<slug>` branches:

> "Issue branch first. Completed mission work is opened from an `issue-<n>-<slug>` branch as a
> pull request targeting `main`, with compact history."

The `sk` skill's own doctrine text (the hermes `sk-design`/`sk-implement` skill family this
mission's orchestrator invokes) separately documents a `<type>/<slug>-<issue>` branch-naming
convention for mission branches.

**These two are in direct tension for this mission's branch name.** Per the operator dispatch's
own instruction, and per the charter's own resolution rule ("If the charter and this file [or any
other doctrine text] ever disagree, the charter wins — flag the drift instead of picking
silently"), **the charter wins**: this mission's branch is
`issue-5189-per-pr-shard-timings-recapture-friction` (charter's `issue-<n>-<slug>` shape), not a
`<type>/<slug>-<issue>` shape the sk-skill doctrine text would otherwise suggest. This drift is
deliberate and is recorded here rather than silently resolved.

## Mission-slug auto-suffix (mid8) vs. dispatch's plain-slug path guidance

See `tracer-tooling-friction.md` item 1: the scaffold produced
`kitty-specs/per-pr-shard-timings-recapture-friction-01M3H7V8/` rather than the plain
`kitty-specs/per-pr-shard-timings-recapture-friction/` the dispatch's own path references assumed.
This is the documented Mission Identity Model (083+) behavior (`mission_slug` carries the `mid8`
disambiguator; `mission_id`/`mid8` are the real identity, `mission_number` is display-only and
null pre-merge) — not a drift from doctrine, just a mismatch between the dispatch's illustrative
path and the tool's actual, documented output shape. No override was applied; all tracer/spec
files were written to the actual scaffolded directory.

## Spec section shape: `## Clarifications / Operator Decisions` matched to existing precedent

The dispatch required a `## Clarifications / Operator Decisions` section carrying the operator's
decisions verbatim. Rather than inventing a new format, this spec follows the
`## Clarifications` + `CL-00N` decision-record pattern already established in
`kitty-specs/up-mission-type-seam-01KZY1JB/spec.md` (canonical-sources / no-improvise discipline,
charter Standing Order #6) — each decision gets an ID, the operator's own words, and (where the
dispatch supplied one) the rationale tying it back to the charter tension it resolves.

## Charter-tension section placed as its own top-level section, not folded into FR prose

The dispatch's "CHARTER TENSION the spec MUST address explicitly" block asked for five specific
properties (relocated-not-dropped; charter stays out of the allowlist; other ratchet tests
untouched; visible warning; silent-success modes for the scheduled job). Rather than scattering
these across FR rows, they are collected into one `## Charter Tension — Standing Order #5` section
that cross-references the FRs proving each property, so a reviewer checking Standing Order #5
compliance has one place to look, with traceability back to the falsifiable requirement.

## No new naming decided for the workflow file or the secret

Deliberately left to plan phase — see `tracer-approach.md`'s "Design choices deliberately left
open" section. Naming these here, without the plan phase's fuller pass over existing
`.github/workflows/*.yml` naming conventions and secret-naming conventions across the repo, risked
picking a name that collides with or drifts from an existing convention this spec-authoring pass
did not have reason to fully survey.

## Operator ruling (2026-09-27): the recapture-PR marker is a single fixed head branch, not a plan-time three-way choice

The original spec left "how a recapture PR from this workflow is identified" as a plan-time choice
among three equally-legitimate alternatives (a label, a branch-name prefix, or a bot
commit-author identity — see the pre-ruling Key Entities text), and had FR-007's duplicate-PR
check separately required to stay "consistent with, and never contradicted by" FR-010's
bot-identity/PR-body convention, without pinning which of the three FR-007 itself would use. A
post-spec adversarial review raised two findings against this shape:

- **SPEC-FRESH3-001** (severity 4): the three-way marker choice is deferred past spec into plan,
  but FR-010 already tries to constrain an unchosen marker with a "consistent with, never
  contradicting" clause — a requirement that cannot be verified until the plan makes the choice
  FR-007 needs, and that leaves room for the plan to pick two markers that are not actually
  reconcilable.
- **SPEC-FRESH3-002** (severity 3): the spec's own reconciliation claim was mechanistically false
  — it asserted "FR-010's mechanism can only ever produce a bot-commit-author identity/PR-body,"
  which forecloses two of the three markers the same spec had just called "equally legitimate,"
  contradicting itself.

The operator ruled (`reviews/spec.ruling.md`, 2026-09-27) that this REPLACES the acceptance bar
for both findings, with a fixed mechanism rather than a plan-time choice:

1. The scheduled recapture job always pushes to **one constant, reused head branch** that the spec
   itself now names (e.g. `ci/recapture-charter-shard-timings`), not a freshly-generated
   per-run branch. GitHub permits only one open PR per head branch into a given base, so a
   duplicate recapture PR is structurally impossible by construction — no marker-matching logic
   is needed to prevent it.
2. FR-007's detection mechanism is exactly "an open PR exists with head = that branch and base =
   `main`." When one exists, the job **force-updates that branch** with the fresh capture
   (never skips, never opens a second PR); when none exists, it opens one. An unrelated PR that
   also touches `.github/ci-shard-timings.json` (the #5175/#5177 pattern) is never matched,
   because its head branch differs.
3. The label / branch-name-prefix / bot-commit-author three-way choice is removed from FR-007
   and Key Entities entirely — there is no longer a plan-time marker decision to make.
4. FR-010 no longer carries any identity-matching or "consistent with, never contradicting"
   relationship to FR-007. It stands alone: the PR body and commit message must plainly state,
   in fixed text, that the change is an automated recapture by the scheduled workflow —
   falsifiable by inspection, with no cross-requirement coupling to police.
5. SPEC-FRESH3-002's false mechanism claim was deleted outright, not reworded — the ruling was
   explicit that the correct fix is removing the false claim, not patching its wording, since the
   claim it made had no valid restatement under the old three-way framing.

Why this is the more resolvable shape: the original design tried to keep two independently
plan-chosen conventions (a duplicate-detection marker and a bot-identity signal) mutually
consistent by written constraint alone, which is exactly the kind of cross-cutting invariant that
drifts silently when the plan or a later change touches only one side. Pinning the marker to a
GitHub-enforced structural property (one open PR per head branch) removes the invariant instead of
asking two future authors to keep honoring it. `spec.md`'s FR-007, FR-010, Key Entities, User
Story 2 Acceptance Scenario 3, and the C-003/C-006 constraints were swept for consistency with this
ruling as part of the same fix; `tracer-approach.md` is left untouched as a frozen historical
record of the original (superseded) three-way framing.

## Operator ruling 2 (2026-09-27): "force-update the open PR" replaced with "skip if open"

Ruling 1 (above) fixed the duplicate-detection marker but kept its point 2 as "when an open PR
exists, force-update its branch." That force-update clause immediately spawned three more
requirements to keep it non-vacuous — FR-011 (lease-guarded force push), FR-012 (an explicit
review-state outcome after the force-update), and an Edge Case entry about what happens to inline
review-comment threads across repeated force-update cycles — plus User Story 2's Acceptance
Scenarios 6 and 7, which exercised FR-011's tip-mismatch abort and FR-012's approval-dismissal/
notice outcome respectively. A second post-spec adversarial review (`spec-fresh-5.yaml`) raised
three findings against this shape, all ruled on together in `reviews/spec.ruling.md`'s "Spec HALT
ruling 2":

- **SPEC-FRESH5-001** (severity 4): FR-012's option (a) — "the repository requires 'dismiss stale
  reviews on push' for this branch/PR path" — is infeasible on this repository in any scope: this
  repo carries no branch protection, so the GitHub API returns 404 rather than offering that
  setting. A requirement whose primary option cannot exist on the target repo is not a real
  requirement.
- **SPEC-FRESH5-002** (severity 2): the Charter Tension section's FR range for "silent-success
  failure modes for the scheduled job" had drifted to include FR-011/FR-012 without those IDs'
  content being re-verified against the actual surviving FR set — a stale cross-reference.
- **SPEC-FRESH5-003** (severity 3): the stale-review-thread Edge Case was plan-deferred with no
  falsifiable acceptance bar ("the plan phase must state the accepted behavior explicitly —
  e.g. ... or ..." is a menu, not a requirement), making it unfalsifiable as written.

The operator ruled that this root cause — ruling 1's "force-update" clause itself — is what should
be withdrawn, not merely its unfalsifiable downstream requirements. **Ruling 1 point 2 is amended;
points 1, 3, 4, 5 stand.** The replacement mechanism, applied throughout `spec.md`:

1. The fixed head branch (ruling 1 point 1) is unchanged.
2. If an open PR with head = that branch and base = `main` exists, the job does **not** push,
   force-push, comment, or open anything. It writes one line to the job summary naming the open
   PR's number and exits successfully. The job never force-pushes, in any case.
3. When no such PR is open, the job pushes the fresh capture and opens the PR. If the fixed branch
   exists with no open PR (e.g. a previously closed PR), the plan decides how that stale branch is
   replaced — that is not a force-update of a PR under review, since no PR is open at that point.
4. **Deleted outright** (no replacement text, no "withdrawn" stub row — this spec has no prior
   precedent for a withdrawn-but-retained FR/SC row, so the fallback convention applies: remove
   the row, leave the ID gap, do not reuse the ID): FR-011, FR-012, SC-007, the stale-review-thread
   Edge Case bullet, and User Story 2's Acceptance Scenarios 6 and 7 (renumbered 1–5, no gap).
   FR-001 through FR-010 keep their original numbers unchanged; FR-011/FR-012 are retired IDs, not
   available for reuse. (Surveyed precedent before choosing: `doc-quality-hardening-2245-01KW9AKV/
   spec.md` removes withdrawn FR rows outright with a prose note ("their table rows are removed;
   the numbers are retired, not reused") while keeping a stub row for a withdrawn *constraint*;
   `doctrine-silence-guards-01KYFV7Q/spec.md` instead keeps a strikethrough **WITHDRAWN** stub row
   for a withdrawn FR. Neither is *this* spec's own established convention — this spec had never
   withdrawn anything before this ruling — so per the dispatch's fallback instruction the simpler,
   no-stub removal was used, applied identically to both the FR rows and SC-007 for consistency.)
5. **The accepted cost is now stated in prose**, in the Key Entities "recapture head branch" entry
   and again in Charter Tension item 5: an unmerged recapture PR's capture can go stale relative to
   `main` while it sits open; tolerable because the per-PR `test_charter_is_not_allowlisted_and_
   agrees` check is now a warning only (FR-001), never a merge blocker, and closing a stale PR lets
   the next scheduled run open a fresh one against current `main`.

Every remaining cross-reference was swept: FR-007's table row and its Key Entities description,
User Story 2 Acceptance Scenario 3, C-003 ("opens or force-updates a PR" → "opens a PR, or ...
skips entirely"), C-006's race description (recast as "both observe 'no PR is open' and both
attempt to open one" instead of "corrupt a concurrent force-update push"), the "scheduled recapture
workflow" Key Entities bullet, and Charter Tension item 5's FR range and prose (dropped FR-011/
FR-012, restated as skip-if-open + the accepted staleness cost). Charter Tension item 1's FR range
(`FR-005–FR-009`) already excluded FR-011/FR-012 and needed no change. Ordinary-English uses of
"forces"/"forced" (the issue title, User Story 1's prose, FR-001's rationale) describe the ~18-
minute local recapture burden, not the FR-007 mechanism, and were left untouched.

## Fresh-sweep fix (2026-09-27): FR-007's "always push" framing corrected

A post-spec fresh-sweep review (`reviews/spec-fresh-6.yaml`, SPEC-FRESH6-001) found that the sweep
above was itself incomplete: FR-007's own "As a maintainer, I want..." want-clause still asserted,
unconditionally, that the job "always push[es] its capture to one constant, fixed head branch" —
directly contradicting the same table cell's skip-if-open sentence two sentences later ("When such
a PR exists, the job does not push, force-push, comment, or open anything"). This was leftover
phrasing from ruling 1's original "always pushes, then optionally force-updates" framing that
ruling 2's "skip if open" edit did not fully catch. A softer echo of the same "always pushes to"
phrasing also survived in User Story 2's Acceptance Scenario 3. Both are corrected: FR-007's
want-clause now reads "...push its capture to one constant, fixed head branch (...) whenever no PR
from that branch is currently open, and to detect..."; AC3 now reads "...the single fixed branch
this workflow is permanently pinned to (used whenever it does push; see Key Entities)...". The
fixed/constant branch identity itself (ruling 1 point 1) and the skip-if-open mechanism (ruling 2)
are unchanged — this is a wording-only fix to stop the FR from contradicting itself, not a design
change. The Key Entities "scheduled recapture workflow" and "recapture head branch" bullets were
checked and already correctly condition the push ("pushes ... when no PR ... is currently open, or
... skips entirely ... when one is already open"); no change was needed there.

## Fresh-sweep fix (2026-09-27): stale-branch-replacement mechanism explicitly deferred to plan; force-push guarantee scoped to the skip-if-open path

A third fresh-sweep review (`reviews/spec-fresh-8.yaml`, SPEC-FRESH8-004) found a genuinely new
ambiguity introduced by rulings 1/2's reused-fixed-branch design, not present before it (the
pre-ruling spec never reused a branch, so this case did not exist). The Key Entities "recapture
head branch" bullet stated "the job never force-pushes, in any case" as an unconditional
guarantee, but the same paragraph's stale-branch-replacement carve-out — triggered when the fixed
branch still exists with no open PR (e.g. a previously closed PR) and a new run finds drift —
only ruled out force-updating a PR *under review*; it never said whether the replacement
mechanism itself may be a force-push. Ruling 2 eliminated force-push specifically because it is
unsafe against a PR under active review, and no PR is under review in the stale-branch case, so
the "in any case" wording and the carve-out's careful "of a PR under review" qualifier were in
real tension. Fixed by (1) scoping "the job never force-pushes, in any case" explicitly to the
skip-if-open path ("while a PR from this branch is open, the job never force-pushes, in any
case"), and (2) explicitly deferring the stale-branch replacement mechanism to the plan phase,
mirroring the FR-004/Charter-Tension-point-4 pattern rather than the FR-011/FR-012 route this
spec already rejected once (ruling 2): the plan may choose any git mechanism (delete-and-recreate
the ref, force-push, or another approach), bound by one fixed, falsifiable observable
requirement — the stale branch's prior content is fully replaced by the fresh capture. No FR/SC
text changed; the fix is confined to the Key Entities "recapture head branch" bullet's two
sentences the finding cited.
