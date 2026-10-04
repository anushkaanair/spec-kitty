# Approach — implement-degod-01M44488

Running log of how the approach evolves (1-3 sentences per dated entry). Seeded at planning.

Initial approach (spec + research/code-grounding.md §2):
- Tidy-first and behaviour-preserving, following the 2026-10-04 degod precedents
  (#5650/#5664/#5679/#5695).
- Characterization pins and patch-liveness coverage land first. Code then moves verbatim into the
  existing seams, and callers are adjusted afterwards.
- #5232 is a separate slice, delivered through the write-shaped placement seam.
- Tests migrate onto the seams last, with the patch-site count measured before and after.

- 2026-10-04 — The grounding squad showed that "auto-rebase" is not on the implement path. The phase
  list was corrected to *context → claim preflight + dependency gate → planning-artifact commit →
  bulk-edit + operational context → workspace/lane selection → allocate → record claim → present*.
- 2026-10-04 — The post-spec squad corrected a wrong precedent: `mission_record_analysis` queries a
  PRIMARY kind. That triggered an empirical reachability study before planning #5232 instead of
  trusting the precedent. The study found the fallback reachable only via a duplicate WP prompt or a
  torn-down coordination branch.
- 2026-10-04 — The post-spec squad corrected a wrong precedent: `mission_record_analysis` queries a
  PRIMARY kind. That triggered an empirical reachability study before planning #5232 instead of
  trusting the precedent. The study found the fallback reachable only via a duplicate WP prompt or a
  torn-down coordination branch.
