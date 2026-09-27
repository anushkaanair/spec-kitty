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
