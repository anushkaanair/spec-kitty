# Decision Moment `01M4BT8BGBX7C51ZGA6T12J3AT`

- **Mission:** `concurrent-mission-writers-01M4BT23`
- **Origin flow:** `specify`
- **Slot key:** `specify.design.rollback`
- **Input key:** `rollback_semantics`
- **Status:** `resolved`
- **Created:** `2026-10-07T18:33:18.091489+00:00`
- **Resolved:** `2026-10-07T18:33:21.394069+00:00`
- **Opened by:** `cli`
- **Other answer:** `false`

## Question

What may a failed status commit's rollback remove from status.events.jsonl?

## Options

_(none)_

## Final answer

Only rows it appended itself in the same lock hold, never a row already committed at HEAD, never when the log shrank or the tail does not parse; on refusal it leaves the log intact and says so loudly. Start from PR #4072's status/rollback.py design (operator ruling on #5819, 2026-10-07).

## Rationale

_(none)_

## Change log

- `2026-10-07T18:33:18.091489+00:00` — opened
- `2026-10-07T18:33:21.394069+00:00` — resolved (final_answer="Only rows it appended itself in the same lock hold, never a row already committed at HEAD, never when the log shrank or the tail does not parse; on refusal it leaves the log intact and says so loudly. Start from PR #4072's status/rollback.py design (operator ruling on #5819, 2026-10-07).")
