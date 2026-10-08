# WP04 review — cycle 1 — CHANGES REQUESTED

Reviewer: claude-reviewer (reviewer-renata). Diff: c58359978..HEAD (fix 92d8ced26, census 090a286a5).

The production changes are correct:
- add-history now reads in `locked_rewrite_text`. The BOM strip plus the utf-8 read/write is byte-equivalent to the old utf-8-sig read and utf-8 write: the BOM is dropped on write as before, and newlines are handled the same way.
- The tracer key `_mission_lock_dir` uses the read-only, topology-aware `candidate_feature_dir_for_mission`. On the real coord fixture it resolves to the coordination worktree's directory (`coord-topo-fixture-01KW2E7A`), which is the name `coord_status_lock` takes. When the handle does not resolve, the lock falls back to the handle: tracers for that handle still serialize with each other, and the write-seam probe refuses the write. That is acceptable.
- The re-keys and the owned-checkout lock are fine, and the four slug-to-dir-name test edits keep their intent.
- The gate census (090a286a5) is correct.

## Blocking

1. **The #5820 test does not pin the lock** (`tests/specify_cli/cli/commands/agent/test_concurrent_appenders.py:133-155`).
   - **What the test does:** it pauses writer A after `locate_work_package`, which runs *before* the locked region. That proves only that A re-reads the file fresh before writing, not that the read-modify-write is locked.
   - **Mutation check:** I replaced the `locked_rewrite_text(...)` call with an unlocked fresh read-transform-write: `wp.path.write_text(_append(wp.path.read_text(encoding="utf-8")), encoding="utf-8")`. The test still passed (1 passed). By contrast, removing the tracer `with` makes both tracer tests fail, as they should.
   - **What T017 asked for:** pause A *after its read of record, before its write*, so that B blocks on the lock after the fix.
   - **Fix:** pause inside the transform, for example by wrapping `tasks_module.append_activity_log`, which runs only inside `_append`. Then drive B with the `B_PROGRESS_SECONDS` pattern the tracer test already uses: after the fix B never reaches its read while A is paused. Keep the assertion that both notes survive.
   - **Required result:** the test fails on the base, fails against the unlocked-fresh-read mutant above, and passes on the fix. Record that in the tracer.

## Non-blocking

2. `status/lifecycle_events.py:302-303`: the touched lines carry two `no-any-return` mypy errors (`feature_status_lock` returns Any). They exist on the base too, so they are not new. Fix them if cheap (campsite rule), or note them.
3. `tests/status/conftest.py:178`: the mypy error there is pre-existing. The file is unchanged in this range.
4. `test_status_lock_keys.py::test_tracer_lock_dir_is_the_mission_directory_name_and_reenters_coord_lock` uses a non-coord fixture. I verified the coord resolution by hand (see above); a one-line assertion on `_build_coord_topology` (`_mission_lock_dir(repo, slug) == ctx.coord_feature_dir.name`-equivalent) would pin it.

## Anti-pattern checklist
| # | Check | Result |
|---|---|---|
| 1 | Dead code | PASS |
| 2 | Synthetic fixture | FAIL (item 1: the test passes without the lock) |
| 3 | Silent empty return | PASS |
| 4 | FR coverage | FAIL for the #5820 lock (item 1) |
| 5 | Frozen surface | PASS |
| 6 | Locked decision | PASS |
| 7 | Shared-file ownership | PASS |
| 8 | Production fragility | PASS (the `FileNotFoundError` in `_append` is a fail-loud vanished-file case) |

## Tests run by reviewer
| Suite | Result |
|---|---|
| `test_concurrent_appenders.py` + `test_status_lock_keys.py`, 5 runs | 10/10 each time |
| `tests/specify_cli/retrospective tests/status tests/retrospective` (-n auto --dist loadfile) | 2031 passed, 14 skipped |
| `tests/specify_cli/cli/commands/agent -k "history or tracer or move_task or mark_status"` | 565 passed, 4 skipped |
| `test_status_events_writes_gate.py` + `test_status_module_boundary.py` | 36 passed |
| ruff, `ruff format --check --force-exclude` | clean |
| mypy | only the pre-existing errors in items 2 and 3 |
