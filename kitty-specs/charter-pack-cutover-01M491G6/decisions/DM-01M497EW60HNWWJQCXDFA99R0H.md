# Decision Moment `01M497EW60HNWWJQCXDFA99R0H`

- **Mission:** `charter-pack-cutover-01M491G6`
- **Origin flow:** `plan`
- **Slot key:** `plan.migration.normalizer-empty-lists`
- **Input key:** `normalizer_empty_lists`
- **Status:** `open`
- **Created:** `2026-10-06T18:26:19.968527+00:00`
- **Opened by:** `cli`
- **Other answer:** `false`

## Question

Projects where the 3.2.6 normalize-activation-absence migration wrote [] (nothing activated) for kinds that were absent (all active): should the cutover migration reset those [] keys to absent?

## Options

- Reset only [] keys for kinds the project never listed and report each
- Keep every [] and report it
- Other

## Final answer

_(none)_

## Rationale

_(none)_

## Change log

- `2026-10-06T18:26:19.968527+00:00` — opened
