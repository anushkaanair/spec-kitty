# Tracer: design-decisions

One entry per finding: `YYYY-MM-DD · actor · <text>`.

---

2026-10-07 · claude · Seed: reuse feature_status_lock rather than a new per-file lock (C-001); rollback refuses rather than cuts on any doubt (shrunk log, unparseable tail, row already in HEAD); lock order checkout claim lock -> Mission lock; review in a shared checkout is warned, not refused (#3129 owns refusal).

2026-10-08 · claude · Close: the claim window releases the Mission lock before the lane auto-rebase (pre-PR finding: holding it there made bounded writers time out) and re-takes it for an id-verified rollback; a real git revert already restoring the log counts as a finished rollback. Slug-keyed locks found by the gate in review/cycle.py were fixed via one mission_write_lock_dir, not allowlisted.
