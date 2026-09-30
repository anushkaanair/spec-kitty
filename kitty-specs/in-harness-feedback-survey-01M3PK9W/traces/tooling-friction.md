# Tooling Friction — in-harness-feedback-survey-01M3PK9W

Tooling this mission touches: the command renderer/installer seams (`prepend_agent_upgrade_check` call sites), CLI-driven command shims, `DistributionProfile`, kernel locking/atomic primitives, and the `spec-kitty` specify/plan/decision CLI.

- 2026-09-29 — Specify: the Decision Moment protocol requires `decision open --mission` before each interview question, but no mission exists until `mission create`; the pre-create discovery questions had to be backfilled as decisions after creation.
- 2026-09-29 — Specify: `spec.md` is scaffolded empty; the canonical `spec-template.md` had to be located by hand under `packs/built-in/missions/software-dev/templates/`.
- 2026-09-30 — Plan: `spec-kitty next --mission … --json` reported `mission_state: not_started` / `preview_step: discovery` even though the spec was committed through `/spec-kitty.specify`; the runtime loop does not reflect slash-command-driven phase progress.
- 2026-09-30 — Plan: `spec-kitty charter context --include tactic:<id> --json` returned an empty payload; the tactic YAML had to be read directly.
