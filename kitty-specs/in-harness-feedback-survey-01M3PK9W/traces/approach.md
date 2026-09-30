# Approach — in-harness-feedback-survey-01M3PK9W

Initial approach (from spec + plan): a new `specify_cli.feedback` bounded context with thin adapters. Agents are reached through the same renderer seam that carries the startup upgrade check (agent-check → native ask → agent-submit). Humans in a terminal get an inline form gated by `is_interactive()`. Delivery is a detached single-attempt sender. The upstream build ships dormant (no default endpoint); downstream distributions supply one via `DistributionProfile`.

- 2026-09-30 — Command surface slimmed at operator request: a single `spec-kitty feedback` command with `--status` / `--prompts`, and no subcommand group.
- 2026-09-30 — All mission artifacts must stay vendor-neutral (operator direction): no company identity in spec, plan, code, docs, or defaults.
