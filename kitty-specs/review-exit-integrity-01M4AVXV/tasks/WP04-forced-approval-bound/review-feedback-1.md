# WP04 review — cycle 1 (opus-reviewer): CHANGES REQUESTED

## Blocking

**Issue 1 — the discriminator does not hold in a normally configured repository; a bare forced re-approval still restamps the lane (#5721 not closed).**

`src/specify_cli/consolidation/approved_bound.py:254` (`_carries_review_evidence`) counts a forced move as a review when `evidence.review.reviewer != "unknown"`. The reviewer recorded on a bare `move-task <WP> --to approved --force` is not `unknown` in practice: `_mt_approval_facts` (`src/specify_cli/cli/commands/agent/tasks_move_task.py:1234`) fills it with `st.reviewer or _detect_reviewer_name()`, and `_detect_reviewer_name` (`tasks_move_task.py:1783`) returns `git config user.name`. It is `unknown` only when git has no user name, which is the isolated-HOME test environment the trace in `traces/design-decisions.md` was checked in, not an operator's checkout.

Reproduced end to end through the real CLI (terminus `build_coord_mission_mixed_lane_canceled`, late commit on the lane after WP01's approval, then `move-task WP01 --to approved --force --note restamp`, then `consolidate --attest-canceled-superseded WP02 ...`):

| repo `git config user.name` | event `evidence.review` | warning | consolidate |
|---|---|---|---|
| unset | reviewer `unknown`, `auto-approval:WP01:20261007` | printed | exit 1, `LANE_MOVED_AFTER_APPROVAL` |
| `Real Operator` | reviewer `Real Operator`, `auto-approval:WP01:20261007` | **not printed** | **exit 0, late file landed on `main`** |

The real status logs in this repository show the same shape (forced approvals with `auto-approval:` references and reviewers such as `Stijn Dejongh`). So for every operator with a git identity the fix is a no-op, and the warning never fires.

Required change: build the predicate on something the operator actually has to assert, not on the auto-detected reviewer. For example (implementer's choice, keep it one predicate used by every reader):
- treat a forced move into `approved` from a lane other than `in_review` as a review only when it carries an approved `review_result`, or a non-synthetic reference (`--approval-ref`), or is an arbiter override; or
- have the move-task shell record whether the reviewer was named explicitly (`--reviewer`) versus auto-detected, and read that.
Then fix `--self-review-fallback`: the forced approval event it writes carries the same auto-detected reviewer and a synthetic reference unless `--approval-ref` is given; its real evidence is the companion `emit_reviewer_self_approval` record (`tasks_move_task_executor.py:606`). Decide whether it counts and read that evidence, not the git name.

**Issue 2 — the tests encode the false premise.** `tests/consolidation/test_approved_bound.py:173` (`_BARE_EVIDENCE`, reviewer `unknown`) and `_SELF_REVIEW_FALLBACK` (reviewer `operator`, reference `PR#42`) are not what the production path writes with a git identity. Required: add a regression where the bare forced move's evidence carries an auto-detected reviewer name (e.g. `reviewer="Real Operator"`, `auto-approval:` reference) for approved->approved, canceled->approved and in_progress->approved, plus one real-CLI test (terminus `run_terminus`, repo with `user.name` set, which the terminus fixture already sets) that a forced re-approval after a late commit still refuses with `LANE_MOVED_AFTER_APPROVAL` and prints the warning. Model `--self-review-fallback` on what it really records.

**Issue 3 — docs overclaim.** `AGENTS.md` (Consolidation, #5668 paragraph) and `docs/adr/4.x/2026-10-04-5-approval-stamp-bounds-the-approved-claim.md` (Follow-up 2026-10-07, "What a bare forced move writes") state the bare forced move writes reviewer `unknown`, and that `--self-review-fallback` "records the reviewer ... the operator named". Both are true only without a git identity. Correct them to match the fixed rule, and keep the named-reviewer residual wording accurate.

## Non-blocking

- `approved_bound.py:282`: `events[:index]` is sliced for every forced move into `approved` of the WP, even when the evidence check alone decides. Cost is O(forced approvals × log length), acceptable; consider passing the index and slicing only in the arbiter branch.
- Red-first verified: `abb2d0bc` fails (`forced-approved-to-approved-is-no-stamp`: `'s2' == 's1'`), passes at HEAD. Attestation, arbiter (strictly-earlier log, lazy import), `in_review` forced hop with `review_result`, and the warning's never-fail fold (45da1dbf) look right. ruff, format (`--force-exclude`), C901 clean; mypy only the pre-existing `no-any-return` at `approved_bound.py:407`.
