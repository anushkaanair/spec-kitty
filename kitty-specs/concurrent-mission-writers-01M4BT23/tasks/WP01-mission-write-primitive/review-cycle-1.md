---
affected_files: []
cycle_number: 1
mission_slug: concurrent-mission-writers-01M4BT23
reproduction_command:
reviewed_at: '2026-10-07T19:42:56Z'
reviewer_agent: claude-reviewer
wp_id: WP01
---

# WP01 review feedback (cycle 1), reviewer-renata / claude-reviewer

Overall the primitive is sound: one fd is measured and ftruncated, so the file is never extended. The tail parser accepts a leading blank line. Ids are compared as a multiset. The HEAD probe resolves the file's own checkout, which is pinned for the coord worktree by `test_transaction_rollback_refuses_rows_already_committed_and_says_so`, and a git error fails closed. On refusal, files stay byte-identical. The transaction rollback re-enters the same lock file: I checked at runtime and saw one key at depth 2. `coord_status_lock` keeps its lock file. The gate edits are exact and do not weaken it. The tests are deterministic, all targeted suites are green, and `make test-fast` is green. One blocking regression remains.

**Issue 1 (blocking, regression on the failure path): `BookkeepingTransaction._rollback` is no longer tolerant of an OSError in the log half.**
- Where: `src/specify_cli/coordination/transaction.py:1304-1315`, the unguarded `rollback_events_log(...)` call.
- Before: the truncate ran inside `try/except OSError` and logged. The docstring at `:1288-1296` still promises that "every step is guarded so a failing restore on one path still attempts the others". The comment at `:1210-1212` promises that `_rollback` "logs but does not raise so the caller sees the original commit failure".
- Now: an `OSError` from `open("r+b")` (other than FileNotFoundError), `os.ftruncate` or `os.fsync` inside `mission_write.py` (`_rollback_events_locked` / `_cut_tail`) propagates out of `_rollback`. As a result:
  - (a) the caller gets a raw `OSError` instead of `BookkeepingCommitFailed`;
  - (b) the `status.json` restore and `restore_generated_artifact_snapshots` (steps 2 and 3) are skipped.
- Reproduced: monkeypatch `mission_write._cut_tail` to raise `OSError(5, "EIO")` and `transaction.safe_commit` to fail, then run `append_event` + `commit` in a txn. The result is `OSError [Errno 5] EIO` escaping instead of `BookkeepingCommitFailed`.
- `status_transition._restore_coord_status_artifacts` (`status_transition.py:417`) already guards this case, so the two shells now disagree.
- Fix:
  - Wrap the `rollback_events_log` call in `try/except OSError`.
  - Log it at ERROR, as the old code did.
  - Set `self._rollback_refusal` to a message naming the failure, so that `_refusal_suffix` surfaces it. For example: `"STATUS_ROLLBACK_REFUSED: could not cut <log>: <exc>; ... Inspect with: git diff HEAD -- <log>"`, or another clearly labelled text.
  - Treat the log half as not rolled back, so `status.json` is left alone.
  - Still run step 3.
- Add a test in `tests/status/test_mission_write.py` next to the two transaction tests. It should inject the OSError through `mw._cut_tail` and assert three things: `BookkeepingCommitFailed` is raised and carries the text, the original commit failure is preserved as the cause, and the artifact restore still ran (or at least that the exception type is right).

**Issue 2 (non-blocking, coverage gap named in the WP Risks): no owned-checkout test for `capture_rollback_point`'s held-lock check.**
- The WP asks for owned, coord and flat tests. Flat is covered (explicit and implicit `repo_root`) and coord is covered (`test_capture_in_a_coord_worktree_agrees_with_the_lock_taken_by_the_caller`). There is no case where the lock is taken on an `OwnedCheckout.owned_root`, as `BookkeepingTransaction.acquire` does (`transaction.py:561`), and the capture is made for a Mission dir in that checkout.
- Add one, so that WP02/WP03 callers on owned checkouts cannot hit the `RuntimeError` unexpectedly.

**Issue 3 (non-blocking, suggestion): the non-git probe depends on locale.**
- Where: `src/specify_cli/status/mission_write.py:240` matches `b"not a git repository"` in git's stderr.
- Under a translated git locale, a Mission dir outside any repository refuses `HEAD_UNREADABLE` instead of cutting. That is safe because it fails closed, but it is spurious.
- Consider classifying by exit status plus `kernel.git_topology` (or pass `LC_ALL=C` through `run_git`'s `env`), or document it as an accepted limitation.

Not findings (judged acceptable):
- The test monkeypatch moved from `status_surface_guard.run_git` to `kernel.git.listing.run_git` (`tests/coordination/test_status_surface_guard.py`). This follows directly from the lifted helper, and that test file covers the module this WP touched, so the edit outside `owned_files` is justified.
- `write_checkout_claim_lock` and `locked_rewrite_text` have no production caller yet. The plan defers them to WP02/WP03/WP04.
- A torn tail refuses rather than being cut, as plan D1 specifies.
