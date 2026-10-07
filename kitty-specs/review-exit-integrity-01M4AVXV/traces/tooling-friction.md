# Tooling friction

Tooling touched: `spec-kitty agent action implement`, `agent tasks move-task`, `consolidate` approval-stamp bound, review-cycle artifact writer.

- 2026-10-07: No `.codegraph/` index in this repo; brownfield mapping done with three Explore scouts instead.
- 2026-10-07: `h.implement` in `_rework_loop_harness.py` takes no extra argv, so the force arms swap `h.CliRunner` for a thin argv-appending wrapper instead of editing the (unowned) harness. `tests/status/test_work_package_lifecycle.py` already defines a `_start`; the new helper is `_start_wp` to avoid shadowing.
- 2026-10-07: `move-task --to for_review --note` committed the transition but left its trailing annotation event (agent/note delta) uncommitted in status.events.jsonl/status.json on a single_branch mission; committed by hand.
- 2026-10-07 (close): Per-WP sweeps never covered tests/agent; two fixtures broken by WP01 surfaced only in WP05's sweep. Blast-radius lists should include every test dir that drives the changed CLI entry point (grep the command name), not only the mirrored module dir.
- 2026-10-07 (close): Subagents reached for `git stash` by reflex in a shared single_branch checkout despite instructions; harmless here, but a stash mid-run by one agent would corrupt another's run.
