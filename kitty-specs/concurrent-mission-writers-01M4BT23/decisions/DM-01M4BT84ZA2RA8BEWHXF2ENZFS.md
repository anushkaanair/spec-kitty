# Decision Moment `01M4BT84ZA2RA8BEWHXF2ENZFS`

- **Mission:** `concurrent-mission-writers-01M4BT23`
- **Origin flow:** `specify`
- **Slot key:** `specify.design.lock_model`
- **Input key:** `lock_model`
- **Status:** `resolved`
- **Created:** `2026-10-07T18:33:11.402352+00:00`
- **Resolved:** `2026-10-07T18:33:14.660229+00:00`
- **Opened by:** `cli`
- **Other answer:** `false`

## Question

Which lock guards Mission-file mutation: a new mechanism or the existing per-mission status lock?

## Options

_(none)_

## Final answer

Reuse the existing per-mission feature_status_lock (keyed on the Mission directory name under the git common dir) as the one Mission write lock; add one checkout-wide claim lock only for the single_branch occupancy check, modelled on the verdict-save queue. No parallel per-file locks. Operator brief + #5819/#5804 triage (lock-held, tail-verified rollback as one fix).

## Rationale

_(none)_

## Change log

- `2026-10-07T18:33:11.402352+00:00` — opened
- `2026-10-07T18:33:14.660229+00:00` — resolved (final_answer="Reuse the existing per-mission feature_status_lock (keyed on the Mission directory name under the git common dir) as the one Mission write lock; add one checkout-wide claim lock only for the single_branch occupancy check, modelled on the verdict-save queue. No parallel per-file locks. Operator brief + #5819/#5804 triage (lock-held, tail-verified rollback as one fix).")
