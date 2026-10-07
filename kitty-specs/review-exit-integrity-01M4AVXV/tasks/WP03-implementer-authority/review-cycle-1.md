---
affected_files: []
cycle_number: 1
mission_slug: review-exit-integrity-01M4AVXV
reproduction_command:
reviewed_at: '2026-10-07T11:21:26Z'
reviewer_agent: opus-reviewer
wp_id: WP03
---

# WP03 review feedback (cycle 1) — opus-reviewer

Verdict: **changes requested** (one blocking finding). Red-first, the #5340 loop
fix, the H3 string twin, lint/format/C901/mypy and the blast-radius suite
(3832 passed, 9 skipped, 6 xfailed) are all good.

## Issue 1 (BLOCKING): asymmetric actor projection makes dict-actor self-approval fail open

`src/specify_cli/consolidation/preflight.py:604` projects the implementer through
`actor_identity_str` (a dict resolved-binding actor becomes its bare `tool`), but
the approver at `preflight.py:620` still comes from `_latest_actor_for_transition`,
which stores `str(actor).strip()` (`preflight.py:552`), i.e. the dict's Python
`repr`. The two sides of `implementer != reviewer` (`preflight.py:621-623`) no
longer use the same projection.

Dict actors are common in real logs: across `kitty-specs/*/status.events.jsonl`,
590 `approved` and 450 `in_progress` events carry a dict actor.

Reproduced with a plain claim -> in_progress -> for_review -> in_review -> approved
log, the same dict actor `{"model": null, "profile": null, "role": "implementer", "tool": "claude"}` on every step:

| case | parent 347b2dbc | HEAD 9cfa87b2 |
|---|---|---|
| same dict actor implements and approves (self-approval) | `_independent_reviewer_confirmed` = False (warns) | **True (warning suppressed)** |
| dict impl, string `"claude"` approver | True | False |

The first row is a fail-open regression: a self-approved WP with a forced
transition loses its hollow-review warning. That breaks this WP's own acceptance
condition that self-approval must still warn, and spec NFR-003.

**Required change:**
- Project the approver and the implementer through ONE identity projection.
  Either give `_latest_actor_for_transition` (approver side) the same projection,
  or add a shared full-identity helper used on both sides.
- Keep H3 for dicts too. `actor_identity_str` collapses a dict to its `tool`,
  so two dicts with the same tool and a different `profile`/`role` would compare
  equal and newly warn. A full-identity projection for dict actors (for example
  `tool:model:profile:role`, in the same shape as the compact string form) keeps
  that pair distinct.
- Add regression tests to `tests/consolidation/test_hollow_review_warnings.py`:
  1. The same dict actor implements and approves: still warns.
  2. Same-tool dicts with a different profile/role: no new warning.
  3. Optionally, a dict implementer with an equivalent compact-string approver.
     Document whichever outcome you choose.

## Non-blocking observations

- `_tolerant_status_events` (`preflight.py:556`) maps raw dict fields to `StatusEvent`
  by hand, in parallel with `StatusEvent.from_dict`. It is not a second authority:
  the store has no lenient reader, and `read_events_raw` raises `StoreError` on bad
  JSON. It follows the raw-scan precedent already in this module. Its failure
  direction: a skipped line (missing `from_lane`, unknown lane) can only drop an
  implementer event, which yields `None` (warn) or an earlier implementer. Not
  worse than the old JSON-skip behaviour. Consider a one-line note in the
  docstring that a skipped line errs toward warning.
- Ordering changed from max `(at, event_id)` (old) to append order (new). This
  matches the review_roles projection used by the ownership guard. Acceptable;
  it could be named in the trace.
- `latest_implementer_actor` keeps its semantics exactly; its callers (move-task
  ownership guard, `_admits_implementer_of_record`) see no behaviour change.
  The `review_roles.py` docstring on `implementer_of_record` being claim provenance
  is accurate.
- Generic actors (`unknown`, `implement-command`) are now skipped on the implementer
  side, which errs toward warning. Good.
