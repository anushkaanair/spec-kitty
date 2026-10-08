# Tracer: approach

One entry per finding: `YYYY-MM-DD · actor · <text>`.

---

2026-10-08 · claude · Seed: extend the PR 5890 Mission write primitive rather than add a second door. Route every meta.json/frontmatter/matrix read-modify-write through mission_write_lock (key resolved before entering the lock), close the gate by construction (Rule 4 + Rule 1/2/3 extensions, empty allowlist, synthetic offender + near-miss + self-mutation per rule). Runtime: delete the speculative rollback, run the retrospective gate as commit_advance's abort-only before_run_completed hook. Planning: canonicalize runtime templates on packs/built-in/missions, insert an analyze DAG step with a currency guard injected from specify_cli, drift-safe for in-flight runs. Red-first deterministic cross-thread interleavings per writer family.
