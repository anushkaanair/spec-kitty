# Grounding: runtime_bridge cleanup (#2560 / #2561 / #2562)

Op: `01M48EGX6W10155GCSDWJCZAT1` (designer-dagmar, design). Base: `main` @ `7297d8c0`.
Baseline: 2738 passed / 4 skipped over the 160-file runtime_bridge test surface
(every test file that references `runtime_bridge` + `tests/runtime`, `tests/next`,
`tests/specify_cli/next`).

## Current state (live tree, not the issue bodies)

- `src/runtime/next/runtime_bridge.py`: 4082 LOC. The issues' line numbers are stale.
- 37 docstrings say "Thin compat delegate". 36 are pure forwards to the 6 seams:
  identity 3, retrospective 9, io 13, composition 8, engine 1, cores 2.
  `_check_cli_guards` carries that label but is real composition logic, so it stays.
- The frozen guard `tests/runtime/test_bridge_compat_surface.py` was already deleted by
  #3285, so nothing still pins the delegates. The sub-issue #2633 says the same.
- The seams call back into the delegates through 40+ deferred
  `from runtime.next import runtime_bridge as _rb; _rb.<name>` lookups (io 14,
  composition 6, retrospective 3, engine 2, identity 2). Their only purpose is
  to make tests that patch `runtime_bridge.<name>` take effect.
- Production callers **outside `src/runtime/next/`** use `runtime_bridge.get_or_start_run`
  and `runtime_bridge.build_operational_context_for_claim`: `next_cmd.py`
  (module-attribute access), `implement_phases.py`, `workflow_executor.py`,
  `mission_loader/command.py` and `orchestrator_api/decision_verbs.py`. The two names are
  in `__all__`, and `test_no_dead_symbols` pins 4 façade names. Unless the mission
  scope crosses into `specify_cli`, these two must stay as public re-exports.
- `provide_decision_answer` in `_internal_runtime/engine.py` still carries
  `# noqa: C901`. The 2026-10-04 refresh asks for it to be cleared in this slice.

## #2561 prototype result (scratch patch, not committed)

`prototype-2561-delegate-deletion.patch`: 48 files, +508 / −1524.

- Deleted the 36 delegates and pointed callers in `runtime_bridge` at `<seam>.<name>`.
- Removed every `_rb` back-edge to a delegated name. The calls became plain
  intra-module calls or `<other_seam>.<name>`. `io → identity` is now a top-level
  import; `io → composition` stays deferred because of the cycle.
- `get_or_start_run` / `build_operational_context_for_claim` are kept as plain
  re-exports (same function objects).
- Repointed about 50 test files: string targets, `setattr`/`patch.object` targets,
  attribute reads and imports. Tests that pinned the compat mechanism itself were
  deleted or rewritten as patch-point tests.
- Seam docstrings were rewritten to describe ownership instead of the compat mechanism.
- Status: down to a few remaining test files to fix. A full re-run of the 160-file
  surface was not done yet.

### Hazards found (these belong in the spec as acceptance criteria)

1. **Deleting a delegate fails loudly; repointing an internal call can pass silently.**
   Patching a deleted name raises `AttributeError`. But a test that patches the kept
   façade `runtime_bridge.get_or_start_run` stops intercepting the calls
   `runtime_bridge` makes internally. 9 tests in `test_bridge_decide_next`,
   `test_runtime_bridge_blocked_paths`, `test_query_mode_unit`,
   `test_runtime_bridge_unit` and `test_next_command_integration` needed manual
   repointing. Each patch's call path has to be reviewed, not just grepped.
2. **Some delegates are adapters, not pure forwards.** `_load_feature_runs(repo_root)`
   is `load_feature_runs(_feature_runs_path(repo_root))`, and a naive rename caused a
   real regression that a patch-free test caught. `_parse_requirement_refs_from_tasks_md`
   injects `grammar=`. `_build_run_ref` threads `run_ref_cls`. Characterise every
   one of these before deleting it.
3. `test_reassess_under_lock` fails when the working tree is dirty
   ("Baseline source is dirty"). That is environmental, not this change.
4. mypy over `src/runtime/next/` reports 21 errors on `main` too; the prototype adds none.

## #2560: dependency analysis for the query/answer seam

AST closure of `query_current_state` + its builders + `_query_*` + `answer_decision_via_runtime`:
it depends on symbols `runtime_bridge` owns that the decide path also uses:
`_materialize_decision`/`_prompt_exists`, `_merged_mission_short_circuit`,
`_finalized_task_board_override_step` (+ `_count_wp_endings`, `_has_claimable_planned_wp`),
`_wp_task_surface_error`, `_wrap_with_decision_git_log` (+ coordination helpers,
`DecisionGitLogUnavailable`), `_is_read_path_error`, and the exceptions.
The `_map_*` mapper family and the WP-board family are **shared with the decide
path** (`_dn_decision_materialize`, `_dn_finalized_board_override`,
`_dn_dependency_gate`, `_resolve_planned_wp_workspace`, and engine
`advance_run_state_after_composition`).

To avoid the cycle, the query seam cannot simply be "query + answer". Candidate shape:
- a lower **decision-mapping** seam: materialise, the WP-board family, the WP-iteration
  builder, the `_map_*` mappers, the merged/finalized short-circuits;
- a **query** seam on top: `query_current_state`, its builders, `answer_decision_via_runtime`;
- `_wrap_with_decision_git_log` and its helpers move to the identity/coordination seam,
  or the query seam keeps one deferred import (to decide in plan).
- The engine adapter's `_rb._map_runtime_decision` back-edge would then point at the
  mapping seam, so the engine ↔ bridge cycle goes away.

False-green risk for the move: names that **both** the remaining `runtime_bridge`
code and the moved code use (`get_mission_type`, `_state_to_action`,
`_compute_wp_progress`, `runtime_provide_decision_answer`, …). A test that patches
`runtime_bridge.<name>` to steer the query/answer path stops intercepting without
failing. Remedy: drop now-unused imports so stale patches fail loudly, then review
each shared name's patches by hand.

## #2562 design-spike finding

The engine now has `plan_advance` / `_commit_advance` / `commit_advance` / `apply_result`.
The adapter's `plan_composition_advance` + `advance_run_state_after_composition` differ
from `next_step`'s success branch in three ways:

- **Planning:** the adapter runs `apply_result` + `plan_next` only. It skips
  `_evaluate_audit_significance` (no `SignificanceEvaluated` event) and
  `_record_step_raci`. A composition-backed advance therefore records no RACI
  binding and no audit significance. That is a behaviour difference, not just
  duplicated code.
- **Terminal:** the adapter runs the retrospective gate (blocking capture → emit
  `MissionRunCompleted` → non-blocking capture). The engine emits directly.
- **Emitter seeding:** the adapter seeds the emitter from the snapshot.

Safe, behaviour-preserving dedup: extract per-event emit primitives from
`engine._commit_advance` (step auto-completed, step issued, decision-input requested
with its dedupe, run completed) and have both paths call them. The payload
construction is byte-for-byte duplicated today.
**Not** behaviour-preserving: routing the composition path through `plan_advance`
would add significance and RACI. That needs an owner decision on whether the gap is
a bug.
