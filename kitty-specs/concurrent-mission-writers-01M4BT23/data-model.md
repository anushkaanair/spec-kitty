# Data Model: Mission write primitive

## Mission write lock
- **Identity**: lock file `<git-common-dir>/spec-kitty-locks/<mission-dir-name>.status.lock` (same file as `feature_status_lock`).
- **Invariant**: every mutation of a Mission file in scope (status log, status snapshot, WP file activity log, tracer file) happens while the calling thread holds it. Re-entrant per thread.

## RollbackPoint
| Field | Type | Meaning |
|---|---|---|
| `events_path` | Path | the Mission's `status.events.jsonl` on the write surface |
| `status_path` | Path | the Mission's `status.json` |
| `pre_event_size` | int | log size at capture |
| `pre_status_bytes` | bytes \| None | snapshot bytes at capture (`None` = absent) |
| `events_existed` | bool | whether the log existed at capture (rollback may unlink only then-absent logs) |

- **Invariant**: captured only while the Mission write lock is held (capture refuses otherwise).

## RollbackOutcome
| Field | Type | Meaning |
|---|---|---|
| `rolled_back` | bool | the tail was cut (or nothing needed cutting) and the snapshot restored |
| `refusal` | RollbackRefusal \| None | `LOG_VANISHED`, `LOG_SHRANK`, `TAIL_UNPARSEABLE`, `TAIL_NOT_OWNED`, `TAIL_ALREADY_COMMITTED`, `HEAD_UNREADABLE`; printed with code `STATUS_ROLLBACK_REFUSED` |

- **State rule**: a refused rollback leaves both files byte-identical.

## Checkout claim lock
- **Identity**: `<git-common-dir>/spec-kitty-locks/__checkout-<sha1(normcase(resolved checkout))[:16]>__.status.lock`.
- **Order**: always taken before any Mission write lock.

## SharedWorkspaceWriter (advisory)
| Field | Type |
|---|---|
| `mission_slug` | str |
| `wp_id` | str |
| `lane` | `in_progress` \| `in_review` |
| `actor` | str \| None |
