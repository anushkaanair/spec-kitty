# Design Decisions

> Capture the rationale that would otherwise evaporate.

**Prompting questions**
- What decision was made?
- What alternatives were considered?
- What was the rationale — why this option over the others?

---

## Entries

<!-- YYYY-MM-DD — Decision: [what]. Alternatives: [what else]. Rationale: [why this one]. -->

## Seed (2026-09-27)
- Operator decisions (recorded as resolved Decision Moments): (1) fold #5171 review-gate + #4943 merge-gate partition legs into one mission; (2) deep fix — read the coordination branch ref when the worktree is unmaterialized; (3) fold #4943's verdict-terminality leg here too.
- Single canonical authority (C-001): no second partition resolver; any shared helper lands in the runtime seam module, not the CLI adapter.
- Topology choice: mission minted as `lanes` (branch-flat) deliberately, to avoid dogfooding the coord issue-matrix bug it repairs.
