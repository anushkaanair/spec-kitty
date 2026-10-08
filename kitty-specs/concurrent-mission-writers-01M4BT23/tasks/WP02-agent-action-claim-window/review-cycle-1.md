---
affected_files: []
cycle_number: 1
mission_slug: concurrent-mission-writers-01M4BT23
reproduction_command:
reviewed_at: '2026-10-07T21:12:02Z'
reviewer_agent: claude-reviewer
wp_id: WP02
---

# WP02 review — cycle 1 — CHANGES REQUESTED

Reviewer: claude-reviewer (reviewer-renata). Diff: f93d9fdd9..HEAD (fix 7f903c09f).

The production change is sound: the wrapper/body split keyed on `_canonical_status_feature_dir` (wf_feature_dir), capture inside the hold, verified rollback in place of the blind truncate, A4 committed-claim wording, checkout lock via ExitStack (entered only for single_branch repo-root, before the Mission lock, closed in `finally`), and the advisory scan. ruff/format/mypy clean, C901 clean, tests green and stable (5/5). The rejection is about test coverage the WP explicitly asked for and that is feasible.

## Blocking

1. **#5819 HEAD half is not pinned (deviation a rejected)** — `tests/status/test_concurrent_mission_writers.py:228-280`.
   The test is named "never erases a *committed* foreign row" but writer B's rows are never committed (on this coord-less lanes fixture `move-task` leaves status rows uncommitted, even with `--auto-commit`), and the "next writer" is another non-committing `move-task`. The issue's core harm — the next status writer commits the loss into HEAD — is therefore not asserted. A committing fixture is feasible; I prototyped it and it is GREEN on HEAD in both modes:
   - in `_writer_b`, after the move-task, `git add kitty-specs/<m>/status.events.jsonl kitty-specs/<m>/status.json && git commit` (B's rows now committed, as in the issue);
   - make the failure injection switchable (`fail_when=lambda: armed[0]`; note `_installed`'s monkeypatches outlive the `with` block), disarm after A's failure;
   - use a committing next writer: `agent action implement WP03 --agent carol` (legacy safe_commit arm commits `status.events.jsonl`), then assert from `git show HEAD:kitty-specs/<m>/status.events.jsonl` that WP02 is `canceled` and the `descoped` note is present (plus WP03 `in_progress`).
   Keep the on-disk assertions; add the HEAD assertions; record RED/GREEN in the tracer.

2. **No CLI-level test of the #5099 warning wiring (deviation d rejected)** — `workflow.py:1640` (implement) and `workflow.py:2297` (review).
   All tests in `tests/lanes/test_shared_workspace_warning.py` call `shared_workspace_writers` / `warn_shared_workspace_writers` directly; deleting either wiring line leaves the suite green (anti-pattern #2 for FR-009). T012 asked for an implement-arm and a review-arm test. Add one CLI-level test per arm through `_invoke("agent","action",...)`, e.g. on the flat lanes fixture with `_add_wp03` (WP02+WP03 share lane-b): alice implements WP02, then bob `agent action implement WP03` → output contains `Warning: <m>/WP02 is in_progress by alice`; review arm: WP02 moved to `for_review`, WP03 `in_progress` by alice, bob `agent action review WP02` → warning names WP03/alice. Also assert the same-actor negative at CLI level for one arm.

3. **A15 coord review test missing** — T009: "add a coord review test (failing follow-up commit → only the review's own uncommitted rows are cut / committed rows are reported as committed)". There is no test driving `review_claim_transition` on a coord Mission (grep finds none). Add one using `_build_two_lane_coord_mission`: WP in `for_review`, `_commit_via_coordination_transaction` commits then raises (as in the #5804 test), assert the output says the claim was committed, no "rolled back", coord log parses, the `in_review` row is in coord HEAD.

## Non-blocking (fix if cheap, else note in the Activity Log)

4. `workflow_executor.py:284-288` (`except typer.Exit` arm): on `TAIL_ALREADY_COMMITTED` it prints "claim was committed" but records no receipt; T010 asked for a `committed` receipt in this arm too.
5. `workflow_executor.py:309-316` (lane-sync arm): `_mark_receipt_refused` runs before the rollback, so if the outcome is `TAIL_ALREADY_COMMITTED` the output says "committed" while the receipt says refused. After a real `_revert_coordination_commit` the tail is no longer at HEAD, so this branch only fires when the revert silently did nothing — the test at `test_concurrent_mission_writers.py:452` pins that unrealistic shape. Either make receipt and message agree or drop the branch's "committed" wording there.
6. Deviation (c) accepted: neither command has a JSON mode; note it in the Activity Log (done in commit message).
7. Deviation (b) accepted: NUL-free rollback is pinned by WP01's unit tests; the e2e checks parseability.
8. Deviation (e) accepted: the 7 call-site edits and the JSON-row fixtures in `test_workflow_review_lane_gate.py` keep the original intent (call order, refused receipt, byte restore).
9. PR #5876 coordination: its hunk adds `operator_force_note` right after `resolved_binding` in `implement_claim_transition`'s signature (base line 962), exactly where the wrapper inserts — a textual conflict is certain; resolution is mechanical (thread the param through wrapper and body). Mention in the PR body. All other regions are clear (review() 2299 vs 2326/2344; implement() 1555 vs 1551 is 4 lines apart — check on rebase).

## Anti-pattern checklist
1 Dead code PASS · 2 Synthetic fixture FAIL (warning wiring, item 2) · 3 Silent empty return PASS (`warn_shared_workspace_writers` returns [] on OSError/ValueError/RuntimeError with debug log: documented advisory degrade) · 4 FR coverage FAIL for FR-009 CLI path (item 2); FR-003/FR-004 partial (items 1, 3) · 5 Frozen surface PASS · 6 Locked decision PASS · 7 Shared-file ownership PASS (out-of-map gate edit noted) · 8 Production fragility PASS.

## Tests run by reviewer
- new tests + gate files (`test_concurrent_mission_writers.py test_shared_workspace_warning.py test_status_events_writes_gate.py test_status_module_boundary.py`): 54 passed
- `test_concurrent_mission_writers.py` ×5: 12/12 each
- `tests/specify_cli/cli/commands/agent` + `tests/agent/test_workflow_review_lane_gate.py tests/integration/test_implement_review_flow.py tests/lanes/test_checkout_occupancy.py` (-n auto --dist loadfile): 2635 passed, 5 skipped, 2 xfailed
- ruff check / ruff format --check --force-exclude / mypy on changed files: clean
