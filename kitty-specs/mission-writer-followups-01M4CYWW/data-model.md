# Data Model: mission-writer-followups-01M4CYWW

This Mission adds no persisted schema. It adds one key function, two locked helpers, one injected runtime fact and two error codes. Everything it writes is already persisted under an existing shape.

## Mission lock key (D1)

| Input | Rule | Key |
|-------|------|-----|
| `meta.json` records `coordination_branch` **and** `mid8` | coordination-routed | `coord_mission_dir_name(mission_slug, mid8)` |
| anything else (flat, primary-only, legacy primary dir without mid8, unreadable `meta.json`) | primary | `feature_dir.name` |

- `mission_lock_key(feature_dir: Path) -> str` is pure and git-free: it reads only `feature_dir/meta.json`. An unreadable or missing `meta.json` falls back to `feature_dir.name`. That fallback is exactly the pre-change key, so no writer moves to a new lock file without evidence.
- Invariant (NFR-002): for every Mission, `mission_lock_key(primary_dir) == mission_lock_key(coord_dir) == BookkeepingTransaction._mission_specs_dir_name`.
- The key is computed before the lock is entered and passed down; it is never resolved while holding the lock.

## Locked helpers (D2)

| Helper | Lock | Read | Write | Returns |
|--------|------|------|-------|---------|
| `mission_metadata.locked_update_meta(feature_dir, mutate, *, repo_root=None, timeout=BOUNDED)` | `mission_write_lock(feature_dir)` | `meta.json` re-read under the lock | atomic write of `mutate(meta)` | the written dict |
| `frontmatter.locked_update_frontmatter(wp_path, mutate, *, feature_dir, repo_root=None)` | `mission_write_lock(feature_dir)` | WP frontmatter + body re-read under the lock | atomic write, body preserved byte-for-byte | the written frontmatter |

`mutate` is a pure function from the read value to the new value. It is only called; it is never stored, returned or assigned (gate Rule 2). It returning the input unchanged means "no write".

**Finalize restore (compare-and-swap).** For each file, finalize records the bytes it wrote. A restore writes the pre-finalize bytes back only while the file's current bytes equal the recorded ones, and reports any other file as `kept (changed by another writer)`.

## Runtime terminal gate (D4)

- The hook is `before_run_completed: Callable[[RunState], None] | None`. It is passed to `commit_advance` (it exists today) and to `next_step` (new).
- If the hook raises `MissionCompletionBlocked(reason, guard_failures)`, nothing is appended to `run.events.jsonl` or `state.json`.
- The bridge maps that exception to a decision with `kind="blocked"`, `reason` naming the retrospective gate, and `guard_failures` copied from the exception.

## Analysis-currency fact (D7)

- Type: `AnalysisCurrency = Callable[[], AnalysisVerdict]`. It is injected into `DecideNextContext.analysis_currency` and defaults to `None`, meaning not evaluated.
- `AnalysisVerdict` has two fields: `status: Literal["current", "missing", "stale"]` and `stale_inputs: tuple[str, ...]`.

| Verdict | Decision on the `analyze` step |
|---------|-------------------------------|
| `current` | advance to `implement` |
| `missing` | re-issue `analyze`, `error_code="ANALYSIS_REPORT_MISSING"` |
| `stale` | re-issue `analyze`, `error_code="ANALYSIS_REPORT_STALE"`, `guard_failures` = one entry per stale input |

## Software-dev runtime step order (D7)

`discovery → specify → plan → tasks → analyze → implement → review → accept`

A run frozen before this Mission keeps its recorded order. The analyze step is absent there, and the implement-time `analysis_report_required` refusal is the backstop.
