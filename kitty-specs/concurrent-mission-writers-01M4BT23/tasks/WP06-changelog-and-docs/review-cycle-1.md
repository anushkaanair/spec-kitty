---
affected_files: []
cycle_number: 1
mission_slug: concurrent-mission-writers-01M4BT23
reproduction_command:
reviewed_at: '2026-10-08T01:00:10Z'
reviewer_agent: claude-reviewer
wp_id: WP06
---

# WP06 review — cycle 1 — CHANGES REQUESTED

Reviewer: claude-reviewer (reviewer-renata). Commit ba482a4e3.

These claims match the shipped code:
- the lock path `<git common dir>/spec-kitty-locks/<dir>.status.lock` (`core/checkout_file_lock.LOCK_DIRECTORY`);
- the directory-name key and the coord directory key;
- the primitive's API names;
- the six refusal reasons (`RollbackRefusal`);
- "never extends";
- that only the primitive truncates or unlinks the log;
- the lock order and its `RuntimeError` (`locking.py:370`);
- `shared_workspace_writers` being advisory;
- that orchestrator-api start-implementation is covered and is refused `WRITE_CHECKOUT_OCCUPIED` (`_fail(cmd, exc.error_code, ...)`, `WriteCheckoutOccupiedError.error_code`);
- the three gate rules.

The terminology is correct ("Mission"; `feature_dir` appears only as a parameter name), and the style, terminology and docs-freshness tests pass. Two statements about refusal reporting are not accurate for every path. They are the operator-facing part of this change, so please fix them.

## Blocking

1. **A committed claim does not print `STATUS_ROLLBACK_REFUSED`.**
   - `CHANGELOG.md` (first bullet) says: "If it cannot prove that, it leaves `status.events.jsonl` unchanged, exits non-zero and prints `STATUS_ROLLBACK_REFUSED` …; run `git diff HEAD -- …`, keep or revert the listed rows yourself". `status-model.md` says: "A refusal … prints `STATUS_ROLLBACK_REFUSED` with the reason".
   - The shipped behaviour differs for `TAIL_ALREADY_COMMITTED` on the `agent action implement` / `review` paths (`workflow_executor._report_refused_rollback`, `_handle_commit_failure`, the typer.Exit and lane-sync arms). Those paths print `<WP> claim was committed; the follow-up <operation> commit failed: <error>`, record the receipt as `committed`, exit 1, and print no `STATUS_ROLLBACK_REFUSED`. That is plan A4 and spec US3 scenario 2.
   - Telling an operator to "revert the listed rows" for a claim that is committed is wrong guidance.
   - **Fix:** state the committed case separately in both places, e.g. "When the rows are already committed (always the case on a coordination Mission), the command says the claim was committed and that only the follow-up commit failed, and exits non-zero; nothing is cut and there is nothing to revert. Otherwise …".

2. **The remedy path is hard-coded.**
   - `RollbackOutcome.message()` prints `STATUS_ROLLBACK_REFUSED: <reason>; <log> left unchanged. Inspect with: git diff HEAD -- <log>` with the absolute log path. On a coord Mission that path is the coordination worktree's log, not `kitty-specs/<mission>/status.events.jsonl` in the main checkout.
   - **Fix:** say "run the `git diff HEAD -- <log>` command the message prints".

## Non-blocking

3. **Where the refusal shows up depends on the path.** `BookkeepingTransaction` appends it to the commit error (`_refusal_suffix`), and `agent action` prints it. The coord fallback arm (`coordination/status_transition.py:548`, `_restore_coord_status_artifacts`) only logs it through `logger.warning`, and the original commit error propagates. "Prints" is therefore slightly strong for that arm; "reports" would be accurate.
4. **The bounded wait is only the default.** `mission_write_lock`'s timeout is bounded by default, but the `agent action implement` / `review` windows and `implement`'s claim hold pass `timeout=-1` (unbounded, plan A1). Consider "bounded wait by default; claim windows wait without a limit".

## Tests run by reviewer
| Suite | Result |
|---|---|
| `tests/docs/test_changelog_style.py`, `tests/architectural/test_no_legacy_terminology.py`, `tests/docs/test_docs_index_freshness.py` | 331 passed |
