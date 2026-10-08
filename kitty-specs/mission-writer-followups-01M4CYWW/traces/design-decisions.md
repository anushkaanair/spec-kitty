# Tracer: design-decisions

One entry per finding: `YYYY-MM-DD · actor · <text>`.

---

2026-10-08 · claude · Seed (operator rulings, all recorded as Decision Moments): #5884 remove rollback (not kernel verified truncate); 'for feature' -> 'mission' at all 5 commit builders + the CLI error strings, legacy finalize subject still accepted; analyze = new DAG step (not tasks-guard) AND canonicalize runtime templates on packs (src/specify_cli/missions copy is what next reads today, packs copy wrongly says DEPRECATED); Rule 4 + fix every meta.json/frontmatter writer; glossary full fix (topic branch added, Mission/Mission Run rewritten, feature branch demoted to alias).

2026-10-08 · python-pedro · WP01: _mission_specs_dir_name keeps its trailing-dash path-composition grammar (pinned by test_coord_dir_seam); the transaction LOCK site moved to legacy_resolution._transaction_lock_key -> branch_naming.mission_lock_dir_name (bare slug when no mid8). mission_lock_key reads the canonical primary meta via new public _read_path_resolver.literal_primary_meta (raw kitty-specs joins are gated). A coordination dir is named by the key itself, so no stem-pairing is needed. Held keys are a thread-local map registered by mission_write_lock.
