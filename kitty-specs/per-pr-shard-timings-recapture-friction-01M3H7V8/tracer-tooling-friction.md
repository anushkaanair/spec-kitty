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

4. **Plan phase: transient `spec-kitty safe-commit` failure, `global_assets`-related, succeeded on
   retry.** Reported by a subagent during the plan-authoring phase (not verified first-hand by the
   tasks-phase agent writing this entry): the first `spec-kitty safe-commit` attempt at plan-commit
   time failed with an error whose message referenced `global_assets`; the exact error text was not
   preserved by the reporting subagent. A bare retry of the same `safe-commit` invocation succeeded
   immediately, with no other change to the tree between attempts. A search of this checkout
   (`grep -rn "global_assets"` across tracked and untracked files under this mission's workspace, and
   `src/specify_cli/`) found no matching error string or log capturing the original failure — only
   unrelated, pre-existing `global_assets`/`assess_global_assets` identifiers in other missions'
   planning artifacts (`kitty-specs/ci-suite-stability-test-isolation-01M22MM5/`,
   `kitty-specs/startup-assess-cold-concurrency-01M3EQ9S/`) and in
   `src/specify_cli/runtime/asset_preparation.py` / `src/specify_cli/runtime/agent_skills.py` /
   `src/specify_cli/skills/installer.py` / `src/specify_cli/upgrade/assessment.py` — none of which is
   evidence of *this* mission's transient failure. Recorded here per instruction as **reported by a
   subagent**, not reproduced or verified first-hand; no workaround was needed since the retry
   succeeded. If this recurs, capture the full stderr/JSON output before retrying so a future entry
   (or a ledger entry) can carry the actual error text.

5. **Tasks phase: dispatch assumed a `tasks-outline -> tasks-packages -> finalize-tasks` flow; the
   checkout's actual active sequence is a single `tasks` authoring step + `finalize-tasks`.
   Verified first-hand by the tasks-phase agent.** The dispatch's own tooling-surface note asked
   this to be checked and recorded rather than treated as a blocker, and it is confirmed exactly as
   the dispatch suspected:
   - `packs/built-in/missions/mission-steps/software-dev/tasks/step.yaml` carries
     `sequence_index: 2` and `in_action_sequence: true` — this is the one active task-authoring step
     for the `software-dev` mission type on this checkout.
   - `packs/built-in/missions/mission-steps/software-dev/tasks-outline/step.yaml` and
     `.../tasks-packages/step.yaml` both carry `sequence_index: null` and
     `in_action_sequence: false` — neither is part of the active sequence.
   - `.venv/bin/spec-kitty tasks-outline --help` and `.venv/bin/spec-kitty tasks-packages --help`
     both fail with `Error: No such command 'tasks-outline'.` / `'tasks-packages'.` (exit code 2) —
     neither is registered as a top-level CLI command on this checkout at all, confirming the
     step-sequence finding operationally, not just via the YAML flag.
   - `.venv/bin/spec-kitty tasks --help` IS registered, but as a **different** action than the
     `software-dev/tasks` mission-step prompt: its own `--help` text is "Finalize tasks metadata
     after task generation" (exit 0) — i.e. this top-level `tasks` CLI command is a finalize-tasks
     equivalent, not the task-authoring step. `packs/built-in/missions/mission-steps/software-dev/
     tasks-finalize/step.yaml` (`in_action_sequence: false` there too, since `finalize-tasks`/`tasks`
     is invoked directly rather than through the mission-step sequence) confirms this shape.

   **Net effect on this mission's tasks-phase workflow**: this agent authored `tasks.md` and
   `kitty-specs/<mission>/tasks/WP##-*.md` directly by hand, following the `tasks` step's own
   `prompt.md`/`guidelines.md` (the canonical, currently-active task-authoring procedure), then ran
   `spec-kitty agent mission finalize-tasks --mission <handle> --json` (documented as "then commit
   to target branch") as the finalize entry point — never `tasks-outline`, `tasks-packages`, or the
   bare top-level `spec-kitty tasks` command. No workaround was needed; the dispatch's own
   fallback instruction (prefer `agent mission finalize-tasks`) was followed exactly.

6. **WP01 implementation start: `spec-kitty agent action implement WP01 ... --mission
   per-pr-shard-timings-recapture-friction-01M3H7V8` failed 4 of 6 attempts with the known
   `global_assets` race (ledger SK-243), before succeeding.** Every failure carried the same shape
   -- `Error: slash_commands: Global asset input changed: <home>/.<agent-dir>/workflows[/<file>.md];
   re-run the command; if it persists, run \`spec-kitty doctor --help\`` -- but the specific path
   named a *different* agent's workflow directory each time (`.kilocode/workflows`,
   `.agent/workflows`, `.agent/workflows/spec-kitty.analyze.md` twice more), consistent with other
   missions concurrently running on this same machine mutating the global per-agent asset inventory
   mid-scan (this checkout's ledger SK-243 shape: a shared-host race, not a bug in this mission's
   own WP01 tasks). A widened retry batch (beyond the nominal 3, run because the failure kept
   naming a different transient path each time rather than repeating) succeeded on its second
   attempt within that batch: claimed WP01, resolved the lane worktree at
   `.worktrees/per-pr-shard-timings-recapture-friction-01M3H7V8-lane-a`, and printed the WP prompt
   path. No absolute home path is reproduced above (the operator's home directory is written as
   `<home>` per instruction); the workaround was the documented one -- re-run, no CLI or state
   change needed.
