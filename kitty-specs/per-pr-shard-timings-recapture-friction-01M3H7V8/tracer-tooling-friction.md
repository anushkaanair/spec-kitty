# Tracer: spec-kitty tooling friction

Seeded at spec-authoring time per the mission-tracer-files procedure (charter Standing Order #3).

## Friction observed

1. **`spec-kitty agent mission create` auto-suffixed the slug with the mission's `mid8`.**
   Dispatched with `mission_slug=per-pr-shard-timings-recapture-friction`, the scaffold created
   `kitty-specs/per-pr-shard-timings-recapture-friction-01M3H7V8/` (mission_slug field in
   `meta.json` became `per-pr-shard-timings-recapture-friction-01M3H7V8`), not the plain
   `kitty-specs/per-pr-shard-timings-recapture-friction/` a naive read of the dispatch instructions
   would expect. This is expected, documented behavior under the Mission Identity Model (083+)
   described in this checkout's `CLAUDE.md` (`mission_slug` is a human handle, disambiguated by
   `mid8`; `mission_id`/`mid8` are the real identity) — not a defect — but it is worth recording
   because the dispatch's own path guidance (`kitty-specs/per-pr-shard-timings-recapture-friction/`)
   did not anticipate the suffix. No workaround needed; this tracer file, `tracer-approach.md`,
   and `tracer-design-decisions.md` were written to the actual scaffolded path.
2. **No other scaffold friction.** `uv sync --frozen --all-extras`, the venv resolution check
   (`specify_cli.__file__` resolved into this checkout's own `src/`, not `~/.local/`), and
   `spec-kitty agent mission create ... --start-branch ... --json` all completed cleanly on the
   first attempt, with the branch (`issue-5189-per-pr-shard-timings-recapture-friction`) checked
   out and the scaffold commit reachable at `git log --oneline -1` immediately after.
3. **The auto-generated scaffold commit message is non-conventional** ("Add scaffold for feature
   per-pr-shard-timings-recapture-friction-01M3H7V8") — this matches ledger entry SK-64's known
   tooling defect (dispatch flagged this in advance); left as-is, not amended, per instruction.

No spec-kitty CLI bug blocked spec authoring itself.
