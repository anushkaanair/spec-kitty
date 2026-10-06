# CLI contract: charter-pack-cutover-01M491G6

Every "Before" spelling is removed (C-001, OD-3): it exits 2 through Typer's unknown-command path. No hidden alias, no hint.

## Command map

| Before | After | Notes |
|---|---|---|
| `spec-kitty charter pack apply <name> [--force] [--compile] [--json]` | `spec-kitty charter activate [--pack <pack>] --preset <preset> [--force] [--compile\|--no-compile] [--resynthesize] [--json]` | `--pack` defaults to `built-in`. `--preset` is mutually exclusive with positional `KIND ARTIFACT_ID` (exit 2). |
| `spec-kitty charter pack list` (presets only) | `spec-kitty charter pack list [--json]` | One row per pack (built-in, each org pack, `project`) with its presets. |
| `spec-kitty charter pack path <preset>` | `spec-kitty charter pack path <pack> [--preset <preset>]` | Prints the pack root, or the preset file with `--preset`. |
| `spec-kitty charter pack consistency-check` | `spec-kitty charter consistency-check` | Checks the active charter; flags unchanged. |
| `spec-kitty doctrine pack validate <dir>` | `spec-kitty charter pack validate <dir>` | Also validates `presets/` and rejects retired descriptor/activation fields. |
| `spec-kitty doctrine pack assemble …` | `spec-kitty charter pack assemble …` | Same flags. |
| `spec-kitty doctrine regenerate-graph [--check]` | `spec-kitty charter pack regenerate-graph [--check]` | Manifest `generated_by` follows. |
| `spec-kitty doctrine asset list` / `asset path <id>` | `spec-kitty charter pack asset list` / `asset path <id>` | |
| `spec-kitty doctrine fetch` / `new` / `validate` / `org init` / `org validate` | `spec-kitty charter fetch` / `new` / `validate` / `org init` / `org validate` | Already shared handlers; handlers move out of `doctrine.py`. `charter org validate` also validates presets. |
| `spec-kitty doctrine mission-type list` | `spec-kitty charter mission-type list --include-inactive` | |
| `spec-kitty doctrine` (group) | — | Removed. |
| `spec-kitty doctor doctrine [--json]` | `spec-kitty doctor charter-packs [--json]` | JSON keys unchanged. |
| `spec-kitty tracker … --doctrine-mode <m>` | `--ownership-mode <m>` | JSON output key `doctrine_mode` removed (`ownership_mode` only). |

## `charter activate --preset` outcomes

| Situation | Exit | Output | Writes |
|---|---|---|---|
| Applied | 0 | governed keys written/removed; `--json`: `{"pack","preset","written":{…},"removed":[…],"target_file"}` | one atomic write |
| Unknown pack | 1 | names the pack; lists available packs | nothing |
| Unknown preset | 1 | names the pack; lists its presets | nothing |
| Unresolvable id in preset | 1 | names preset file and id | nothing |
| Governed key would change, no `--force` | 1 | per-key diff | nothing |
| `--preset` with positional `KIND ARTIFACT_ID` | 2 | usage error | nothing |

## Unmigrated project (FR-011)

Any command except `upgrade`, `init`, `--version`, `--help`, run in a project (or current checkout) whose state matches the legacy predicate, exits 1 with code `LEGACY_CHARTER_STATE` and:

```
This project uses the retired doctrine layout (<first finding>).
Run `spec-kitty upgrade` to migrate it. In a lane worktree, upgrade the
repository root and merge the target into this lane (do not rebase).
See docs/migrations/charter-pack-cutover.md.
```
