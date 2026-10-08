# WP05 review — cycle 1 — CHANGES REQUESTED

Reviewer: claude-reviewer (reviewer-renata). Diff: 273e487ba.

The gate is RED on the real tree, so this WP cannot be approved. `test_rule3_no_slug_keyed_status_lock` fails:

```
src/specify_cli/migration/backfill_runtime_state.py:1682: slug-keyed feature_status_lock
src/specify_cli/review/cycle.py:1115: slug-keyed feature_status_lock
src/specify_cli/review/cycle.py:1160: slug-keyed feature_status_lock
src/specify_cli/review/cycle.py:1201: slug-keyed feature_status_lock
```

Orchestrator decision: these are the same defect class as amendment A8 and are **in scope**. They must be **fixed, not allowlisted**. Both allowlists stay empty.

## Blocking

1. **`review/cycle.py:1115, 1160, 1201` lock the Mission slug, not the Mission directory.**
   - **What is wrong:** the three `feature_status_lock(main_repo_root, mission_slug, timeout=...)` takes do not converge with the lock that `status.emit` and the other re-keyed writers take for the same Mission.
   - **What to do:**
     - (a) Promote WP04's read-only "Mission directory from handle" resolution (`retrospective/tracer_writer._mission_lock_dir`, built on `candidate_feature_dir_for_mission`) to ONE canonical helper. Put it in `status/mission_write.py`, or wherever the layering allows: check `tests/architectural/test_layer_rules.py` and `test_status_module_boundary.py` (SR-2: callers import from the `specify_cli.status` facade).
     - (b) Reuse that helper in `tracer_writer` (delete the private copy) and in the three `review/cycle.py` sites.
   - **Decide and verify the key:** it should be the status write surface's directory name, coord-aware, equal to what `status.emit` and `coord_status_lock` lock for the same Mission (on coord, the coordination worktree's Mission directory name). Verify it against the actual call paths. Note:
     - `move-task` rejections create review cycles while `_mt_execute` holds the Mission-directory lock. After the re-key, cycle's take re-enters that same file on the same thread, which is fine.
     - The cycle docstring says resolving the lock path consults Git and the helper must not run inside another status-lock scope. Resolve the directory BEFORE the `with` and keep `_in_queue_status_lock_timeout`.
     - Check the `owned=` arm: the lock root is still `main_repo_root`. Make sure that matches what the owned status writers take after WP04.
   - **Test:** add a key-convergence test for review cycle in the style of `tests/status/test_status_lock_keys.py`: spy on `feature_status_lock_path`, assert the review-cycle lock path equals the `status.emit` lock path, on a Mission whose directory name differs from its slug and on a real coord fixture.

2. **`migration/backfill_runtime_state.py:1682` is flagged only because of a variable name.**
   - `slug = feature_dir.name` is already the directory name, so the key is correct; the identifier just contains `slug`.
   - Fix by keying on `feature_dir.name` directly in the `feature_status_lock(...)` call (keep `slug` for the result fields if needed). No allowlist, and do not widen the gate to dataflow.

After both: rule 3 is green with an empty allowlist, and the WP01–WP04 tests still pass.

## Gate review (no change required unless noted)

- **Non-vacuity:** good. Every rule has synthetic offenders. The real tree is scanned (300+ files floor). Rule 1's floor is exact (`Counter` of the primitive's two sites), and so is rule 2's (exactly one call site per registered sink). Self-mutations of the real `tasks.py` and `tracer_writer.py` fire.
- **Declared hole:** a callable passed into a call inside the `with`, stored, and run after the lock is released is accepted. It is documented in the module docstring and fits the real seam (`write_artifact(stage=...)` runs the stage synchronously). Acceptable.
- **Residual (low, optional):**
  - Rule 3 sees only Name/Attribute keys. `meta["mission_slug"]` and similar subscripts would pass.
  - Rule 1 does not catch truncation by `open(events_path, "w")` / `write_text("")`.
  - Mention both in the docstring's out-of-scope list.
- **Run time:** about 26 s wall time for the file (18 s of tests). It carries `pytest.mark.architectural`, like its neighbours. Acceptable.
- **Prompts:** both are source templates, not generated copies. The wording states one writer per checkout for implementers and reviewers, including single_branch, and contains no `git add -A` / `stash` wording.
  - Optional nit: the implement prompt says "`agent action review` warns"; since WP02, `agent action implement` warns too, so name both.
- **Prompt pinning:** no change needed. `test_builtin_pack_provenance_ratchet.py` (the new sentences add no repo paths), the stale-path sweep, the terminology guard and the runtime/skill render tests are green, and `spec-kitty doctrine regenerate-graph --check` reports the graph is fresh.

## Anti-pattern checklist
| # | Check | Result |
|---|---|---|
| 1 | Dead code | PASS |
| 2 | Synthetic fixture | PASS |
| 3 | Silent empty return | PASS |
| 4 | FR coverage | FAIL (the gate is red) |
| 5 | Frozen surface | PASS |
| 6 | Locked decision | PASS |
| 7 | Shared-file ownership | PASS |
| 8 | Production fragility | N/A |

## Tests run by reviewer
| Suite | Result |
|---|---|
| `tests/architectural/test_mission_write_discipline.py` | 1 failed (rule 3), 49 passed |
| Prompt-pinning set (stale-path sweep, provenance ratchet, terminology, runtime agent commands, crlf skill render, charter autotrack, analyze surface agreement, regression 1615) | 220 passed, 1 skipped, 1 xfailed; provenance ratchet tests 54 passed |
| `spec-kitty doctrine regenerate-graph --check` | fresh |
