---
work_package_id: "WP01"
title: "Acceptance suite and golden \"before\" sets"
subtasks: ["T001", "T002", "T003", "T004", "T005", "T006", "T007", "T008", "T009", "T010"]
dependencies: []
requirement_refs: ["C-006", "NFR-001", "FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "FR-006", "FR-007", "FR-008", "FR-009", "FR-010", "FR-011", "FR-012", "FR-013", "FR-014", "FR-015", "FR-016", "FR-017", "FR-018", "FR-019", "SC-001", "SC-002", "SC-003", "SC-004", "SC-005"]
task_type: "implement"
phase: "Phase 0 - Acceptance first"
execution_mode: "code_change"
owned_files:
  - "tests/acceptance/charter_pack_cutover/**"
  - "tests/fixtures/charter_pack_cutover/**"
authoritative_surface: "tests/acceptance/charter_pack_cutover/"
create_intent:
  - "tests/acceptance/charter_pack_cutover/__init__.py"
  - "tests/acceptance/charter_pack_cutover/conftest.py"
  - "tests/acceptance/charter_pack_cutover/_support.py"
  - "tests/acceptance/charter_pack_cutover/_effective_set.py"
  - "tests/acceptance/charter_pack_cutover/_requirements.py"
  - "tests/acceptance/charter_pack_cutover/legacy_fixtures.py"
  - "tests/acceptance/charter_pack_cutover/generate_golden_before.py"
  - "tests/acceptance/charter_pack_cutover/test_golden_before.py"
  - "tests/acceptance/charter_pack_cutover/test_presets.py"
  - "tests/acceptance/charter_pack_cutover/test_upgrade_migration.py"
  - "tests/acceptance/charter_pack_cutover/test_cli_surface.py"
  - "tests/acceptance/charter_pack_cutover/test_promotion.py"
  - "tests/acceptance/charter_pack_cutover/test_rename_skills_glossary.py"
  - "tests/acceptance/charter_pack_cutover/test_package_split.py"
  - "tests/acceptance/charter_pack_cutover/test_project_pack_root.py"
  - "tests/acceptance/charter_pack_cutover/test_gates_latency_messaging.py"
  - "tests/acceptance/charter_pack_cutover/test_traceability.py"
  - "tests/fixtures/charter_pack_cutover/default_yaml_snapshots.yaml"
  - "tests/fixtures/charter_pack_cutover/golden_before/_meta.json"
  - "tests/fixtures/charter_pack_cutover/cli_before.json"
agent_profile: "reviewer-renata"
role: "implementer"
agent: "claude"
history:
  - at: "2026-10-06T19:30:00Z"
    actor: "system"
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP01 – Acceptance suite and golden "before" sets

## ⚡ Do This First: Load Agent Profile

Use the `/ad-hoc-profile-load` skill to load the agent profile specified in the frontmatter, and behave according to its guidance before parsing the rest of this prompt.

- **Profile**: `reviewer-renata` (tactic `acceptance-criteria-non-vacuity`)
- **Role**: `implementer`
- **Agent/tool**: `claude`

If the profile cannot be loaded, run `spec-kitty agent profile list` and pick the best match for `task_type: implement` on `tests/acceptance/charter_pack_cutover/`.

---

## ⚠️ IMPORTANT: Review Feedback

- **Has review feedback?** Check `review_ref` in the event log (`spec-kitty agent tasks status`) or the Activity Log below.
- Address every feedback item before you finish; log each fix in the Activity Log.

## Review Feedback

*[If this WP was returned from review, the reviewer feedback reference appears in the Activity Log below or in the status event log.]*

---

## Markdown Formatting

Wrap HTML/XML tags in backticks. Use language identifiers on code blocks.

## Objectives & Success Criteria

This WP is the mission's contract (C-006, owner ruling 2026-10-06). Every later WP takes its done-condition from these tests and may not redefine them.

1. Every FR (FR-001..FR-019), every NFR (NFR-001..NFR-004), every SC (SC-001..SC-005) and every user-story acceptance scenario (US1-1..US5-2) is covered by at least one test in `tests/acceptance/charter_pack_cutover/`.
2. Each test that targets unbuilt behaviour is a **strict xfail** created by `pending_until("WPnn")`, naming the WP that turns it green. Tests whose behaviour already exists at base (for example `charter fetch`) carry no marker and pass.
3. Every assertion has a **positive control on the same fixture**, so no test passes vacuously (fakes listed in `research/postspec-squad-testability.md` §B).
4. NFR-001's golden "before" sets and SC-004's recorded `spec-kitty doctrine …` outputs are generated **now, at the mission base**, with the pre-cutover code, and frozen with their generator and the base SHA.
5. The traceability test passes: every spec id is covered; every `pending_until` names a real WP (WP02..WP25).
6. `pytest tests/acceptance/charter_pack_cutover -q` collects and ends with only `xfailed` / `passed` (no `failed`, no `xpassed`, no collection error).

## Context & Constraints

- Read first: `.kittify/charter/charter.md`; mission `spec.md` (FR table, FR-012 inventory, FR-018 closed lists, Edge Cases, OD-1..OD-10), `plan.md`, `research.md`, `research/postspec-squad-testability.md` (§B test shapes, §C NFR-001 measurement), `research/default-yaml-snapshots.md`, `research/runtime-seams.md` (§3 detection seam, §4 doctrine leaves, §6 error codes), `contracts/*.md`, `data-model.md`.
- **No production code changes in this WP.** Only the two owned trees.
- **Lazy imports inside test bodies.** A test may not import a post-cutover module at module level (for example `charter.activation.effective_set`, `kernel.charter_pack_paths`). A collection-time `ImportError` would error the whole module instead of one strict xfail. Import with `importlib.import_module(...)` inside the test.
- **Drive behaviour through the CLI** (`from specify_cli import app` + `typer.testing.CliRunner`, `contextlib.chdir(project)`), not through internal functions, unless the requirement is structural (module absent, gate exists). Use the opt-in `charter_cwd_isolation` fixture (`tests/_support/charter_cwd.py`) for `charter generate/synthesize/resynthesize`.
- Markers: only markers already registered in `pytest.ini` (`integration`, `git_repo`, `corpus`, `timing`, `windows_ci`). Do not add markers (that would touch `pytest.ini`, outside this WP). Tests that read `packs/built-in/**` or `kitty-specs/**` carry `corpus` (guarded by `tests/architectural/test_ci_corpus_trigger_completeness.py`).
- CI routing note: `tests/acceptance` sits in the rootless deferred bucket of `.github/ci-module-registry.yml:833` and runs in the nightly interpreter shard 5 (`tests/architectural/_interpreter_shard_roster.py:315`), not in a per-PR module lane. Do not change CI routing here; record this in the Activity Log so the reviewer and WP25 see it. Every later WP runs the suite locally.
- Code style: ruff, `ruff format`, mypy clean; complexity ≤ 15; no new `# noqa` / `# type: ignore` except one justified `# noqa: TID251 - file-integrity digest` if you hash the generator file.

## Branch Strategy

- **Strategy**: Planning artifacts were generated on `issue-3732-charter-pack-rename`; completed changes merge back into `issue-3732-charter-pack-rename`.
- **Planning base branch**: `issue-3732-charter-pack-rename`
- **Merge target branch**: `issue-3732-charter-pack-rename`
- Lane: from `lanes.json` (filled by `spec-kitty agent mission finalize-tasks`).

## Flip map (the contract every later WP reads)

Each WP's first commit deletes exactly its own `pending_until("WPnn")` markers (red), and its last commit turns them green. Test function names below are binding; parametrised rows carry their own marker through `pytest.param(..., marks=pending_until(...))`.

| File | Test (covers) | Pending WP |
|---|---|---|
| test_project_pack_root.py | `test_fr016_kernel_module_is_single_authority` (FR-016) · `test_fr016_layer_roots_project_is_pack_root` (FR-016) · `test_fr016_migrated_fixture_project_artifact_is_listed` (FR-016) | WP02 |
| test_project_pack_root.py | `test_fr016_synthesize_writes_new_root_only` · `test_fr016_path_authority_gate_detects_planted_literal` · `test_fr016_state_contract_and_gitignore_use_new_root` | WP03 |
| test_package_split.py | `test_fr010_pack_tooling_lives_in_charter_offering_packs` · `test_fr010_charter_packs_facade_exports` | WP04 |
| test_package_split.py | `test_fr010_specify_cli_doctrine_package_deleted` · `test_fr010_org_charter_and_adapters_at_ruled_homes` · rows of `test_nfr002_gates_close_empty` for census + boundary exemptions | WP05 |
| test_promotion.py | all FR-015 / US5 tests; `test_fr005_merge_defaults_removed` | WP06 |
| test_presets.py | `test_fr002_builtin_presets_are_pack_data` · all `test_fr019_*` | WP07 |
| test_presets.py / test_gates_latency_messaging.py | all `test_fr001_*`, `test_fr004_*`, `test_fr002_deleting_preset_file_fails_activation`, `test_nfr003_preset_and_pack_list_latency`; FR-006 row `pack path` | WP08 |
| test_presets.py | `test_fr003_*` | WP09 |
| test_upgrade_migration.py | `test_fr012_rc35_and_normalizer_recorded_skipped` | WP10 |
| test_upgrade_migration.py | `test_fr012_cutover_runs_first`, `test_fr012_legacy_keys_rewritten[*]`, `test_fr012_doctrine_pack_id_renamed`, `test_fr012_project_root_moved`, `test_fr012_collision_refuses_and_moves_nothing`, `test_fr012_path_references_rewritten`, `test_fr012_user_path_values_untouched`, `test_fr012_windows_locked_file_refuses` | WP11 |
| test_upgrade_migration.py | stale/kept/minimal/`[]`/skills/dry-run FR-012 tests, all `test_nfr001_*`, `test_nfr004_*`, `test_us2_6_*`, `test_us2_7_*` | WP12 |
| test_cli_surface.py | all `test_fr005_*` except `merge_defaults`; `test_us3_4_accompanies_field_rejected`; FR-007 row `charter pack apply` | WP13 |
| test_cli_surface.py | all `test_fr011_*`; NFR-002 row "cr02 compat test deleted" | WP14 |
| test_cli_surface.py | FR-006 rows not yet built (`pack validate/assemble/regenerate-graph/asset`, `consistency-check`, `doctor charter-packs`), `test_fr006_in_repo_callers_use_charter_spellings`; FR-007 rows `doctor doctrine`, `charter pack consistency-check` | WP15 |
| test_cli_surface.py | remaining `test_fr007_old_spelling_exits_2` rows (the `doctrine` group); NFR-002 row "guidance gate is a removed-command gate" | WP16 |
| test_rename_skills_glossary.py | all `test_fr009_*`, `test_fr010_charter_pack_id_in_project_state`, `test_us3_4_doctrine_pack_id_rejected_in_org_charter` | WP17 |
| test_rename_skills_glossary.py | all `test_fr008_*` (incl. US4-1) | WP18 |
| test_package_split.py | `test_fr010_no_src_module_named_for_retired_tier` | WP21 |
| test_package_split.py | `test_fr010_tests_doctrine_directory_renamed` | WP23 |
| test_rename_skills_glossary.py / test_gates_latency_messaging.py | `test_fr013_*`, `test_fr017_*` (SC-005) | WP24 |
| test_rename_skills_glossary.py / test_gates_latency_messaging.py | `test_fr014_*`, `test_fr018_*` (SC-003), remaining `test_nfr002_gates_close_empty` rows, `test_traceability_no_pending_markers_remain` | WP25 |

If, while writing a test, you find its behaviour cannot be owned by the WP above (for example the WP's subtasks do not build it), keep the closest WP from tasks.md and record the mismatch in the Activity Log for the orchestrator. Do not invent a new WP.

## Subtasks & Detailed Guidance

### Subtask T001 – Acceptance suite scaffold and `pending_until(wp)`

- **Purpose**: one package with the shared helpers, so every test file reads the same way and the traceability test can parse markers.
- **Steps**:
  1. Create `tests/acceptance/charter_pack_cutover/__init__.py` (empty docstring module). `tests/acceptance/` has no `__init__.py`; with pytest's default `prepend` import mode the package is imported as `charter_pack_cutover`. Use **relative imports only** (`from ._support import …`) so the same modules also import as `tests.acceptance.charter_pack_cutover` under `python -m` (T003). Verify with `uv run --frozen python -c "import tests.acceptance.charter_pack_cutover"`.
  2. `_support.py`:
     - The set of valid WP ids is **not** hard-coded here: T010 parses it from `kitty-specs/charter-pack-cutover-01M491G6/tasks.md` (`^## Work Package (WP\d\d):`). `_support.py` only validates the shape (`^WP\d\d$`) and rejects `WP01`.
     - `pending_until(wp: str, reason: str) -> pytest.MarkDecorator` returns `pytest.mark.xfail(strict=True, raises=(AssertionError, ImportError), reason=f"pending {wp}: {reason}")`. `raises` makes a test that fails for an unrelated reason (a `TypeError` in the harness, a broken fixture) **fail**, not xfail. The first argument must be a string literal at every call site (T010 checks this with `ast`).
     - `covers(*ids: str)` decorator: validates each id against `^(FR|NFR|SC)-\d{3}$|^US\d-\d$|^C-\d{3}$`, stores `fn.__covers__ = ids`, returns `fn`. Works on functions and on classes.
     - `run_cli(args: list[str], cwd: Path, *, input: str | None = None) -> click.testing.Result`: `CliRunner()` (stderr separated if the installed click supports it), `contextlib.chdir(cwd)`, `app` from `specify_cli`, `catch_exceptions=True`; returns the result. Assertions on `exit_code` always print `result.output` in the message.
     - `read_json_output(result) -> object`: strips ANSI with `tests/_support/ansi.py` helpers and parses the first JSON document on stdout; fails with the raw output in the message.
     - `active_charter(project: Path) -> dict[str, object]`: reads the resolved activation store (`config.yaml`, or the `charter.yaml` named by the `charter:` pointer) with `ruamel.yaml` safe loader and returns the governed keys only (`activated_*`, `activated_kinds`, `mission_type_activations`). Independent of production readers on purpose.
     - `tree_digest(project: Path) -> str`: deterministic digest over `.kittify/`, `.gitignore` and the agent directories (`.claude`, `.agents`, and any dir in `AGENT_DIRS`), path + bytes, sorted (NFR-004). Use `charter.hasher.hash_content` if it accepts bytes; otherwise `hashlib.sha256` with `# noqa: TID251 - file-integrity digest`.
  3. `conftest.py`: fixtures `legacy_project(request, tmp_path)` (indirect parametrisation by fixture name from T002), `migrated_project(tmp_path)` (canonical layout: `charter_packs.org.packs`, `.kittify/charter-packs/`), `two_org_packs(tmp_path)`, `copied_builtin_pack(tmp_path, monkeypatch)` (copy `packs/built-in` and point `SPEC_KITTY_PACKS_ROOT` at it; see `kernel.paths.get_built_in_pack_root`). Every fixture builds under `tmp_path`, never in the repository.
- **Files**: `__init__.py`, `_support.py`, `conftest.py`.
- **Parallel?**: no; T002–T010 build on it.
- **Notes**: `pytest.ini` has no global `xfail_strict`; strictness comes only from the helper. Do not use `pytest.mark.skip` anywhere in the suite (a skip is invisible to the flip discipline).
- **Validation**: a throwaway local check that `pending_until("WP02", "x")` on `assert False` reports `xfailed`, on `assert True` reports `failed` (XPASS strict), and on `raise TypeError` reports `failed`. Do not commit that check; T010 pins the same properties.

### Subtask T002 – Legacy fixture-project builders (NFR-001 list)

- **Purpose**: one deterministic builder per legacy shape, shared by the generator (T003) and the tests (T005).
- **Steps**:
  1. Copy `kitty-specs/charter-pack-cutover-01M491G6/research/default-yaml-snapshots.yaml` verbatim to `tests/fixtures/charter_pack_cutover/default_yaml_snapshots.yaml`. The tests own their copy, independent of the migration's embedded data (WP12 T061), so a wrong migration table cannot make its own test pass.
  2. `legacy_fixtures.py`: `BUILDERS: dict[str, Callable[[Path], Path]]` and `NFR001_FIXTURES: tuple[str, ...]` (the subset golden-compared). Each builder writes `.kittify/config.yaml`, `metadata.yaml` (via `ProjectMetadata(...).save()` and `MigrationRunner._stamp_schema_version(kittify, MAX_SUPPORTED_SCHEMA)`, as `tests/specify_cli/upgrade/test_upgrade_provisions_mission_type_activations.py:120-140` does), any pack directories, then `git init -b main` + commit. Stamp version `4.0.0rc5` unless the shape needs older.
  3. Builders (names are binding; the spec's NFR-001 list first):
     - `legacy_keys_only` (`doctrine.org.packs[]` with one local org pack; `governance.doctrine.*` in `config.yaml`)
     - `single_pack_legacy_form` (`doctrine.org.{local_path,subdir,source_type}`)
     - `organisation_packs` (flat `organisation_packs[]`)
     - `legacy_directory_only` (`.kittify/doctrine/{directive,tactic,procedure,overlays}/…` + `graph.yaml`; canonical keys)
     - `stale_<doc>_<form>`: one per distinct released `default.yaml` document form in the snapshot file (D1..D5 × `original`/`rtk`/`rc5`/`rtk+rc5`, deduplicated); write every key of that form into `config.yaml`
     - `stale_in_pointed_charter_yaml` (D5 lists in `.kittify/charter/charter.yaml` behind the `charter:` pointer)
     - `near_miss_stale` (D5 tactics minus one id)
     - `customised_lists` (D5 directives plus one id; `DIRECTIVE_NNN` spelling for one entry)
     - `minimal_equal` (released M2 lists **with** `activated_kinds: [directives, tactics]`)
     - `governance_doctrine_in_charter_yaml`
     - `two_org_packs` (canonical keys; pack 2 holds an artifact whose `id:` differs from its file stem, #4399)
     - `mixed_stale_and_custom` (stale tactics, custom directives)
     - `pre_rc35` (version `3.2.0rc30`, no activation keys, no `mission_type_activations`)
     - `synthesized_with_provenance` (`.kittify/doctrine/` artifacts + `.kittify/charter/synthesis-manifest.yaml` + `.kittify/charter/provenance/*`). Produce the real shape once at base (T003 runs the base synthesizer on a scratch project) and freeze it under `tests/fixtures/charter_pack_cutover/static/synthesized/`; the builder copies that tree.
     - `project_pack_skills` (`.kittify/doctrine/skills/<ns>-<id>/…`, `charter_packs.project.skill_namespace`, `.kittify/skills-manifest.json` with a `source_ref` under the old root)
     - `normalizer_empty_lists` (`activated_glossary_packs: []` and one more per-artifact `[]`)
  4. FR-012-only builders (not golden-compared): `doctrine_pack_id_activations`, `tracker_doctrine_key`, `answers_doctrine_key`, `standalone_governance_yaml`, `both_roots_collision`, `both_roots_disjoint`, `user_path_value_with_doctrine` (`local_path: packs/doctrine-foo`), `installed_removed_skills` (`.claude/skills/` and `.agents/skills/`: one manifested `spk-doctrine-charter`, one unmanifested copy byte-equal to the shipped file, one edited copy), `lane_in_approved` (a coord-topology mission with a lane worktree whose WP is `approved`; reuse `tests/integration/coord_topology_fixture.py` helpers).
- **Files**: `legacy_fixtures.py`, `tests/fixtures/charter_pack_cutover/default_yaml_snapshots.yaml`, `tests/fixtures/charter_pack_cutover/static/**`.
- **Parallel?**: yes with T004–T009 once T001 exists.
- **Notes**: builders must not import post-cutover modules. Keep each builder ≤ 15 complexity (one small writer helper per file kind).
- **Validation**: a parametrised smoke test in `test_golden_before.py` builds every fixture and asserts the legacy shape it claims exists (positive control for the builders themselves).

### Subtask T003 – Golden "before" generator, frozen JSON and base SHA

- **Purpose**: NFR-001 compares the effective set after upgrade with what the project had **before**. After the cutover no code can read the legacy shapes, so "before" is measured now and frozen (`research/postspec-squad-testability.md` §C).
- **Steps**:
  1. `_effective_set.py`: `effective_set(repo_root: Path) -> dict[str, list[str]]` per §C: `build_activation_aware_doctrine_service(repo_root)` from `charter.activation.doctrine_service_builder` (`:266`); for each artifact kind attribute take the mapping's keys; read `service.directives` explicitly (the `pack_manager._effective_ids_for_kind` helper, `pack_manager.py:455`, skips directives); add `mission_types` = `PackContext.from_config(repo_root).activated_mission_types`; add `skills` = `establish_in_force_skill_ids(repo_root)` (`charter/activation/skill_preparation.py:272`). Sort every list. This helper is used after the cutover too; the rename WPs (WP19/WP20) update its imports mechanically.
  2. `generate_golden_before.py`, runnable as `uv run --frozen python -m tests.acceptance.charter_pack_cutover.generate_golden_before`:
     - **Refuse after cutover**: exit 2 with "refusing: pre-cutover code required (…)" unless `importlib.util.find_spec("kernel.doctrine_root")` is found, `src/charter/activation/packs/default.yaml` exists, and `importlib.util.find_spec("specify_cli.doctrine")` is found.
     - Record `_meta.json`: `base_sha` (`git rev-parse HEAD`), `package_version`, `python`, `generated_at` (`kernel.clock.now_utc`), `generator_digest` (digest of the generator file's bytes), `fixtures` (sorted names).
     - For each `NFR001_FIXTURES` name: build into a temp dir, compute `effective_set`, run `spec-kitty charter list --json` through `run_cli` and store its activated rows (normalised, paths stripped); write `golden_before/<name>.json` with `{"fixture", "base_sha", "effective", "charter_list"}`.
     - Write `cli_before.json` for SC-004: on one doctrine-command fixture (a project plus a local pack dir), run each old leaf and record `exit_code`, normalised stdout and the `key_lines` extracted by the per-leaf patterns declared in `test_cli_surface.py::DOCTRINE_LEAVES` (import that table; keep it data only). Leaves: `doctrine fetch`, `doctrine regenerate-graph --check`, `doctrine new`, `doctrine validate`, `doctrine pack validate <dir>`, `doctrine pack assemble …`, `doctrine org init`, `doctrine org validate`, `doctrine mission-type list`, `doctrine asset list`, `doctrine asset path <id>`, `charter pack consistency-check`, and `doctor doctrine --json` (record the JSON key set).
     - Freeze the synthesized-project tree for T002 (`static/synthesized/`) the same way.
  3. Run it once, now, on the WP01 lane (pre-cutover code). Commit generator, data and `_meta.json` together in one commit whose message names the base SHA.
  4. `test_golden_before.py` (no xfail; passes at base and must keep passing):
     - every `NFR001_FIXTURES` name has a golden file; every golden file's `base_sha` equals `_meta.json`'s; `generator_digest` equals the digest of the current generator file (editing the generator after freezing goes red);
     - `base_sha` is 40 hex; when `git cat-file -e <sha>` succeeds, `git merge-base --is-ancestor <sha> HEAD` holds;
     - the refusal: factor the check into `is_pre_cutover_tree() -> tuple[bool, str]`. Test 1 monkeypatches it to `(False, "kernel.doctrine_root missing")`, calls `main(out_dir=tmp_path)` and asserts exit 2 and an empty `tmp_path`. Test 2 (control, valid before and after the cutover) asserts `is_pre_cutover_tree()[0] == (Path("src/kernel/doctrine_root.py").exists() and Path("src/charter/activation/packs/default.yaml").exists())`. No `skip`/`skipif` (T001).
- **Files**: `_effective_set.py`, `generate_golden_before.py`, `test_golden_before.py`, `tests/fixtures/charter_pack_cutover/golden_before/*.json`, `cli_before.json`, `static/**`.
- **Parallel?**: no; it needs T002 and the `DOCTRINE_LEAVES` table from T006.
- **Notes**: never recompute golden data in a test. If a fixture cannot be read by the base code (record the traceback), drop it from `NFR001_FIXTURES`, keep its builder, and record the reason in the Activity Log.
- **Validation**: rerunning the generator on the same base reproduces byte-identical JSON (except `generated_at`); check once locally.

### Subtask T004 – Preset acceptance tests (FR-001..FR-004, FR-019, US1, SC-001)

- **Purpose**: presets are pack data applied with replace semantics; prove the reader honours the data, not a hard-coded list (testability §B FR-001/FR-002/FR-003/FR-004 rows).
- **Steps** (`test_presets.py`; all CLI-driven unless noted):
  - `test_fr001_activate_minimal_preset_writes_governed_keys` (FR-001, US1-1): fresh migrated project; `charter activate --preset minimal`; assert `active_charter()` equals the preset file's governed keys and `charter list --json` agrees. Positive control: before the command the keys differ.
  - `test_fr001_default_preset_removes_every_governed_key` (FR-001, US1-2, SC-001): apply `minimal`, then `--preset default --force`; assert every `activated_<kind>` (except `activated_skills`, `activated_glossary_packs`) and `activated_kinds` are **absent** (never compare id lists); `mission_type_activations` equals the preset's. Drift: with `copied_builtin_pack`, add a synthetic tactic after writing the preset and assert it is effective (`effective_set`).
  - `test_fr001_fixture_preset_listing_one_id_writes_that_id` (positive control for the reader): a copied pack whose `default` lists one directive writes exactly that id.
  - `test_fr001_org_pack_preset_unioned_with_required` (US1-3): `two_org_packs`, org preset lists a built-in and an org id; `--pack <org> --preset <name>`; result = preset ∪ org `required_<kind>`.
  - `test_fr001_unknown_preset_names_pack_and_lists_presets` (US1-4): exit 1, output names the pack and its presets, `tree_digest` unchanged.
  - `test_fr001_customised_list_refused_without_force` (US1-5, OD-6): exit 1, per-key diff printed, nothing written; with `--force` it applies (control).
  - `test_fr001_preset_with_positional_kind_exits_2`.
  - `test_fr002_builtin_presets_are_pack_data` (FR-002, `corpus`): `packs/built-in/presets/{default,minimal}.yaml` exist; `default` has no `activated_*`, no `activated_kinds`, lists the built-in mission types; `minimal` has no `activated_kinds` (or one consistent with its own keys).
  - `test_fr002_deleting_preset_file_fails_activation` (half-by-half): delete `minimal.yaml` in a copied pack; activation fails naming it.
  - `test_fr003_init_without_activation_equals_default_preset` (FR-003, US1/SC-001): `spec-kitty init` in a tmp dir skipping activation; `active_charter()` equals what `--preset default` writes on a second fresh project.
  - `test_fr003_copied_pack_default_preset_drives_init` (positive control; a [ratchet] that is no-op passable): copied pack whose `default` preset lists only `software-dev`; `init` writes `[software-dev]`.
  - `test_fr004_pack_list_shows_packs_presets_and_project` (FR-004, US3-3): built-in, org-with-presets, org-without-presets (negative control: listed with none), a fetched pack in the cache, and the `project` row with none; use `--json`.
  - `test_fr019_validate_names_malformed_file_and_unresolved_id` (FR-019): `charter pack validate <dir>` on a pack with `presets/bad.yaml` (unknown key) and `presets/ghost.yaml` (unknown id): non-zero, each named; the same pack with a valid preset exits 0 (control).
  - `test_fr019_org_validate_validates_presets`, `test_fr019_org_init_scaffolds_example_preset`, `test_fr019_manifest_hashes_presets_not_an_artifact_kind` (preset listed in `pack-manifest.yaml` constituents; `ArtifactKind` has no preset member).
- **Files**: `test_presets.py`.
- **Parallel?**: yes.
- **Notes**: markers per the flip map. Use the contract outcomes table in `contracts/cli.md` for exit codes.
- **Validation**:
  - [ ] Every FR-001/FR-004 test reads the result back with `charter list --json` **and** `active_charter()`.
  - [ ] No test compares the `default` preset to an id list.
  - [ ] Each refusal test asserts `tree_digest` unchanged.
  - [ ] Locally removing one marker shows a red `AssertionError`/`ImportError`, not a harness error.

### Subtask T005 – Upgrade acceptance tests (FR-012, NFR-001, NFR-004, US2, SC-002)

- **Purpose**: the migration is the only consumer protection; test each inventory row and the whole-upgrade guarantees through `spec-kitty upgrade`.
- **Steps** (`test_upgrade_migration.py`, `integration` + `git_repo`):
  - `test_fr012_cutover_runs_first`: `spec-kitty upgrade --dry-run --json` on `legacy_keys_only`; the first planned migration id is `charter_pack_cutover`.
  - `test_fr012_rc35_and_normalizer_recorded_skipped` (WP10): on `pre_rc35`, after upgrade, `metadata.yaml` records `3.2.0rc35_default_charter_pack` and the normalizer as skipped.
  - `test_fr012_legacy_keys_rewritten[...]`: one param per key row (org packs, single-pack → explicit name ≠ `default`, `organisation_packs`, `governance.doctrine` in each of the three files, tracker `doctrine` → `ownership`, answers `doctrine:`); assert canonical key present, legacy key absent, value preserved. Edge: canonical and legacy both present → canonical wins and the summary names the removed key.
  - `test_fr012_doctrine_pack_id_renamed` (OD-1), `test_fr012_project_root_moved` (US2-1: `.kittify/charter-packs/` holds every file, `.kittify/doctrine/` absent, uncommitted edits carried over), `test_fr012_collision_refuses_and_moves_nothing` (lists colliding paths; `tree_digest` unchanged; `both_roots_disjoint` moves everything — control), `test_fr012_path_references_rewritten` (manifest, provenance, skills-manifest `source_ref`, `.gitignore`), `test_fr012_user_path_values_untouched`.
  - `test_fr012_windows_locked_file_refuses` (`windows_ci`): a held handle under `.kittify/doctrine/` refuses naming the path.
  - `test_fr012_stale_list_reset[stale_*]` (US2-2): each key equal to a snapshot becomes absent; the summary names it.
  - `test_fr012_near_miss_and_customised_kept_and_reported` (US2-3), `test_fr012_minimal_kind_gate_removed_lists_reported`, `test_fr012_normalizer_empty_lists_reset_and_reported` (summary names file and key to restore), `test_fr012_installed_removed_skills` (manifested and hash-equal copies removed, edited copy kept and reported), `test_fr012_dry_run_parity` (same report lines, `tree_digest` unchanged).
  - `test_nfr001_effective_set_preserved[NFR001_FIXTURES]` (NFR-001, SC-002): after upgrade, `after ⊇ before` for every kind; non-stale fixtures `after == before`; stale fixtures `after == before ∪ builtin_inventory()` where the inventory is read from the upgrading CLI's built-in pack at test time; `charter list --json` agrees.
  - `test_nfr004_second_upgrade_changes_zero_bytes[NFR001_FIXTURES]` (US2-4): first upgrade changes `tree_digest` (positive control), the second does not, and the migration's `detect()` is false (import lazily).
  - `test_us2_6_pre_rc35_upgrade_has_zero_errors` (effective set equals the `default` preset's), `test_us2_7_lane_in_approved_consolidates_after_root_upgrade` (upgrade the root, merge target into the lane, `spec-kitty consolidate` exits 0, no `LANE_MOVED_AFTER_APPROVAL`).
- **Files**: `test_upgrade_migration.py`.
- **Parallel?**: yes.
- **Notes**: run upgrade with the flags the existing harness uses (`--yes`/`--no-worktrees` as appropriate; check `spec-kitty upgrade --help`). Each test asserts on the migration result lines through the CLI output, not on private functions.
- **Validation**:
  - [ ] Every NFR-001 fixture appears in both `test_nfr001_*` and `test_nfr004_*` parametrisations.
  - [ ] NFR-004 asserts the first run changed something (non-vacuity) before asserting the second changed nothing.
  - [ ] The built-in inventory used for stale fixtures is read at test time from the CLI's pack, never frozen.
  - [ ] Each FR-012 inventory row of `spec.md` maps to at least one test id (comment table at the top of the file).

### Subtask T006 – CLI-surface acceptance tests (FR-005..FR-007, FR-011, US3, SC-004)

- **Purpose**: every removed spelling hits Typer's unknown-command path; every replacement does the same job (testability §B FR-005/FR-007, FR-006 rows).
- **Steps** (`test_cli_surface.py`):
  - `DOCTRINE_LEAVES`: a data table (old argv, new argv, per-leaf `key_patterns`, pending WP or `None`). Rows from `research/runtime-seams.md` §4. Rows already built at base (`charter fetch/new/validate/org init/org validate`, `charter mission-type list --include-inactive`) carry no marker.
  - `test_fr006_charter_home_matches_recorded_output[row]` (FR-006, SC-004, US3-1): run the new argv on the same fixture as `cli_before.json`; assert the recorded exit code and that every recorded key line appears. `doctor charter-packs --json`: same JSON key set as the recorded `doctor doctrine --json`.
  - `test_fr006_in_repo_callers_use_charter_spellings` (`corpus`): `.github/workflows/packs.yml`, `Makefile`, `packs/built-in/pack-manifest.yaml` `generated_by`, `AGENTS.md`, `packs/internal/**` carry no `spec-kitty doctrine` / `doctor doctrine`; each names the new spelling (positive control).
  - `test_fr007_old_spelling_exits_2[row]` (FR-007, US3-2, OD-3): every old argv (each `doctrine` leaf, the bare group, `doctor doctrine`, `charter pack apply`, `charter pack consistency-check`) exits 2 with "No such command"; the new argv on the same fixture exits 0 (control).
  - `test_fr005_registry_modules_not_importable`: `specify_cli.charter_pack_registry`, `charter.activation.packs`, `charter.activation.default_pack` raise `ModuleNotFoundError`; no `src/**/*.py` defines or imports `BUILTIN_PACKS` (AST scan; control: the scan finds a planted definition in a tmp file).
  - `test_fr005_no_default_yaml_reader_outside_migration_data`: AST/text scan of `src/` for `default.yaml` / `default_pack` readers; only the cutover migration's frozen data module may mention released snapshots.
  - `test_us3_4_accompanies_field_rejected`: `charter pack validate` on a pack whose `pack.yaml` has `accompanies_doctrine_pack` → `RETIRED_PACK_FIELD`, names the field (control: same pack without it → 0).
  - `test_fr011_legacy_project_fails_naming_upgrade[cmd]` (FR-011, US2-5): `legacy_keys_only`; one param per top-level group plus the hot paths (`charter list`, `status`, `doctor charter-packs`, `agent tasks status`, `next`, `implement WP01`; derive the group list from `specify_cli.app.registered_groups`/`registered_commands` so a new group is covered automatically) → exit 1 (the binding value in `contracts/cli.md` "Unmigrated project"; `research/runtime-seams.md` §3 proposed 4, and the contract wins), `LEGACY_CHARTER_STATE`, text names `spec-kitty upgrade` and `docs/migrations/charter-pack-cutover.md`. Control: same fixture after `spec-kitty upgrade` → the error is gone.
  - `test_fr011_exempt_invocations` (`upgrade`, `init`, `--version`, `--help`), `test_fr011_stale_worktree_checkout_detected` (legacy layout in the current checkout only), `test_fr011_shims_removed` (no `LegacyDoctrineRootWarning`, `LegacyTrackerOwnershipKeyWarning`, `apply_legacy_governance_selection_key_compat` anywhere in `src`; `--doctrine-mode` exits 2; JSON has no `doctrine_mode`), `test_fr011_load_governance_config_fails_closed`.
- **Files**: `test_cli_surface.py`.
- **Parallel?**: yes, but T003 imports `DOCTRINE_LEAVES`; land the table first.
- **Validation**:
  - [ ] Every row of the `contracts/cli.md` command map has an old-spelling row and a new-spelling row.
  - [ ] Old-spelling tests assert exit 2 **and** the unknown-command text (a hidden alias would exit 0).
  - [ ] The FR-011 control (post-upgrade run) is on the same fixture copy.

### Subtask T007 – Promotion acceptance tests (FR-015, US5)

- **Purpose**: #4400; an absent key promoted by any of the four callers keeps everything that was effective (testability §B FR-015 row).
- **Steps** (`test_promotion.py`):
  - Fixture: `two_org_packs` with an id≠stem artifact in pack 2, every activation key absent.
  - `test_fr015_promotion_preserves_effective_set[caller]` (US5-1), callers through their CLI entry points: `charter interview` (non-interactive answers file), the org-charter union path (`charter generate` with an org pack declaring `required_<kind>`), `spec-kitty upgrade` driving `m_unify_charter_activation` (fixture stamped below 3.2.6rc1 with `answers.yaml` selections), and `charter resynthesize` (resynthesis preflight). Assert `effective_set` after ⊇ before, including the pack-2 artifact and directives.
  - `test_fr015_unresolvable_set_leaves_key_absent_and_reports` (US5-2): break the org pack (dangling `local_path`); the key stays absent and the output names it; control: the healthy fixture promotes.
  - `test_fr015_effective_set_seam_is_public`: `importlib.import_module("charter.activation.effective_set")` exposes one public function; the four callers import it (AST scan of the four modules).
  - `test_c007_interview_does_not_import_a_migration_module` (AST of `cli/commands/charter/interview.py`).
  - `test_fr005_merge_defaults_removed`: `pack_manager.merge_defaults` and `_load_default_pack` absent.
- **Files**: `test_promotion.py`. **Parallel?**: yes.
- **Validation**:
  - [ ] The test asserts the fixture really has two org packs and an id≠stem artifact before acting.
  - [ ] One param per caller, so reverting one caller turns exactly one row red.

### Subtask T008 – Rename, skills, glossary and package-split tests (FR-008..FR-010, FR-013, FR-014, US4)

- **Steps** (`test_rename_skills_glossary.py`, `test_package_split.py`):
  - FR-008: `test_fr008_skill_families_present` (`src/charter/offering/skills/spk-charter-{governance,glossary,profile-load,spdd-reasons}`, `spk-practice-{bulk-edit,semantic-compression,show-me}` exist; the seven `spk-doctrine-*` and five folded names absent; `doctrine-daphne` untouched), `test_fr008_removed_names_are_retired` (`RETIRED_CANONICAL_SKILL_NAMES` ⊇ all twelve), `test_fr008_upgrade_installs_new_and_removes_old` (US4-1: `installed_removed_skills` plus a user-global root under the isolated HOME; after `spec-kitty upgrade` and one more CLI run, new names present, old names absent in both roots, manifests have no orphan entry).
  - FR-009: `test_fr009_three_names_no_alias` (`ActiveCharterManager`, `ActiveCharterConfigError` importable from `charter.activation.pack_manager` / `pack_context`; AST scan: no `src` module binds `CharterPackManager` / `CharterPackConfigError`; `CHARTER_PACK_CONFIG_INVALID` absent from `src/`), `test_fr009_json_error_code` (`agent mission create --json` on a broken activation config returns `ACTIVE_CHARTER_CONFIG_INVALID`), `test_fr009_tool_surface_kind` (`ToolSurfaceKind.CHARTER_SKILL.value == "charter_skill"`, no `DOCTRINE_SKILL`).
  - FR-010 (`test_package_split.py`): `test_fr010_pack_tooling_lives_in_charter_offering_packs` (`charter.offering.packs.{pack_descriptor,pack_lineage,pack_manifest,builtin_manifest,pack_validator,pack_assembler,extends}` import), `test_fr010_charter_packs_facade_exports` (`charter.packs` re-exports by identity), `test_fr010_specify_cli_doctrine_package_deleted` (`ModuleNotFoundError`; `src/specify_cli/doctrine` absent), `test_fr010_org_charter_and_adapters_at_ruled_homes` (`charter.activation.org_charter`, `charter.activation.org_charter_loader`, `specify_cli.charter_packs.{sources,snapshot,template_render}`), `test_fr010_no_src_module_named_for_retired_tier` (no `src/**` path segment containing `doctrine` except the kept migration ids listed in the occurrence map), `test_fr010_tests_doctrine_directory_renamed`, `test_fr010_charter_pack_id_in_project_state` (after upgrade of `doctrine_pack_id_activations`, `charter.yaml` uses `charter_pack_id`).
  - `test_us3_4_doctrine_pack_id_rejected_in_org_charter` (`charter org validate` names the field and `charter_pack_id`).
  - FR-013: `test_fr013_glossary_defines_terms` (`docs/context/charter.md` has entries for charter offering, Charter Pack, activation preset, active charter, project layer, Charter Bundle; resolve each through `glossary.resolution.resolve_term` if it can read that doc, else parse anchors), `test_fr013_no_living_citation_of_missing_adr` (no `2026-08-22-2` outside historical roots; control: the new citation target exists).
  - FR-014: `test_fr014_reachability_pins_reasserted_or_recorded`: locate the file by glob `tests/**/drg/test_reachability.py` (WP23 moves the directory); assert no pin references `default.yaml` / `default_pack` / `charter_pack_registry`, and every deleted pin is listed with a reason in the module docstring section `Deleted pins (FR-014)`.
- **Parallel?**: yes.
- **Validation**:
  - [ ] Each structural test (module absent) has a control (a module that must exist does import).
  - [ ] AST scans exclude `tests/` and historical roots, and each has a planted-positive check on a tmp file.

### Subtask T009 – Gate, latency and messaging tests (FR-016..FR-018, NFR-002, NFR-003, SC-003, SC-005)

- **Steps** (`test_project_pack_root.py`, `test_gates_latency_messaging.py`):
  - FR-016 / WP02: `test_fr016_kernel_module_is_single_authority` (`kernel.charter_pack_paths` exposes `PROJECT_PACK_DIRNAME == "charter-packs"`, `project_pack_root(repo) == repo/".kittify"/"charter-packs"`; `kernel.doctrine_root` raises `ModuleNotFoundError`), `test_fr016_layer_roots_project_is_pack_root` (`charter.activation.layer_roots.resolve_layer_roots(migrated)["project"]` is the pack root), `test_fr016_migrated_fixture_project_artifact_is_listed` (a project directive only under `.kittify/charter-packs/` appears in `charter list --all --json` with layer `project`; control: removed file → not listed).
  - FR-016 / WP03: `test_fr016_synthesize_writes_new_root_only` (`charter synthesize` on `migrated_project` with interview answers: artifact under `.kittify/charter-packs/`, no `.kittify/doctrine/` created; control: artifact readable via `charter list --json`), `test_fr016_path_authority_gate_detects_planted_literal` (import `tests/architectural/test_charter_pack_path_authority.py`'s scan function by path, plant `Path(".kittify") / "doctrine"` in a tmp module: one finding; clean module: zero), `test_fr016_state_contract_and_gitignore_use_new_root`.
  - `test_nfr002_gates_close_empty[row]`: rows (census `EXEMPT_MANAGEMENT_SURFACE` empty [WP05]; boundary `_EXEMPT_SUBPACKAGE` gone [WP05]; `test_lifted_cli_doctrine_charter_cr02_compat.py` deleted [WP14]; `test_no_deprecated_doctrine_command_in_guidance.py` is a removed-command gate [WP16]; FR-016 allowlist empty, FR-018 allowlist only C-004 names, `test_no_dead_doctrine_paths` and kind-vocabulary allowlists empty [WP25]). Read each by importing the gate module by path.
  - `test_nfr003_preset_and_pack_list_latency` (`timing`): fixture = built-in + two org packs; in-process median of 5 runs each of `charter activate --preset minimal --force`, `charter pack list`, `charter list`; each ≤ 1.5 × `charter list`.
  - `test_fr018_vocabulary_gate_zero_findings_over_floor` (SC-003, US4-2) and `test_fr018_planted_token_detected` (each closed-list token planted in a tmp living-surface file is found).
  - `test_fr017_changelog_before_after_lists_every_removed_name` (SC-005: the `Unreleased` section names every row of `contracts/cli.md` and `contracts/errors.md`, the twelve skill names, config keys, `.kittify/doctrine/`, `accompanies_doctrine_pack`), `test_fr017_runbook_and_historical_banners` (`docs/migrations/charter-pack-cutover.md` exists and names `spec-kitty upgrade`; the two superseded runbooks carry a historical banner).
- **Parallel?**: yes.
- **Validation**:
  - [ ] Gate tests load gate modules by file path (`importlib.util.spec_from_file_location`) inside the test, so a missing gate is an `ImportError` xfail, not a collection error.
  - [ ] The timing test carries `timing` and is therefore outside `make test-fast`.
  - [ ] The changelog check parses only the `Unreleased` section (released sections are historical, C-002).

### Subtask T010 – Traceability test

- **Purpose**: the suite is complete and every marker is meaningful.
- **Steps** (`test_traceability.py`, `corpus`):
  1. `_requirements.py`: `REQUIRED_IDS` closed tuple: FR-001..FR-019, NFR-001..NFR-004, SC-001..SC-005, US1-1..US1-5, US2-1..US2-7, US3-1..US3-4, US4-1..US4-2, US5-1..US5-2.
  2. `test_required_ids_match_spec`: parse `kitty-specs/charter-pack-cutover-01M491G6/spec.md` (table first cells `FR-\d{3}`, `NFR-\d{3}`, `SC-\d{3}` bullets, numbered acceptance scenarios per story) and assert equality with `REQUIRED_IDS`.
  3. `test_every_required_id_is_covered`: AST-scan every `test_*.py` in the package for `covers(...)` decorators with string-literal args; union ⊇ `REQUIRED_IDS`; report missing ids.
  4. `test_every_pending_marker_names_a_real_wp`: AST-scan for `pending_until(...)` calls; first arg must be a string literal matching a `## Work Package WPnn:` heading in this mission's `tasks.md`, never `WP01`; a reason string is present.
  5. `test_traceability_no_pending_markers_remain`: zero `pending_until(` calls remain. Itself marked `pending_until("WP25", "closeout removes the last markers")`.
  6. Self-tests of the helpers: a strict-xfail property check (`pytester` if available in this repo's plugins, else run the helper on a nested function and inspect the returned mark's `kwargs`: `strict is True`, `raises` set).
- **Parallel?**: no; last.
- **Validation**:
  - [ ] A `pending_until("WP99", "x")` planted in a tmp copy of a test file (inside the test, never in the tree) turns the WP check red.
  - [ ] Dropping one `covers("FR-019")` in a tmp copy makes the coverage check name `FR-019`.

## Test Strategy

```bash
make test-fast
uv run --frozen pytest tests/acceptance/charter_pack_cutover -q -rxX
uv run --frozen pytest tests/architectural/test_ci_corpus_trigger_completeness.py tests/architectural/test_marker_registry_single_source.py tests/architectural/test_ci_collection_completeness.py -q
uv run --frozen ruff check tests/acceptance/charter_pack_cutover
uv run --frozen ruff format --check --force-exclude tests/acceptance/charter_pack_cutover
uv run --frozen mypy tests/acceptance/charter_pack_cutover
uv run --frozen pytest tests/architectural/test_no_legacy_terminology.py -q
```

Expected: the acceptance run shows only `passed` and `xfailed`. Record counts in the Activity Log.

## Commit discipline

Conventional subjects referencing #3732, for example `test(acceptance): scaffold charter-pack cutover suite and pending_until (#3732)`, `test(acceptance): freeze golden before-sets at <sha> (#3732)`. Commit per subtask. Never push to `main`.

## Risks & Mitigations

- **Vacuous pass**: positive control per test; strict xfail with `raises`; traceability.
- **Golden data from post-cutover code**: generator refusal + digest pin + base SHA.
- **Collection errors masking the contract**: lazy imports only.
- **Suite not in per-PR CI**: recorded; every WP runs it locally (Test Strategy of each WP).

## Definition of Done

- [ ] All ten subtasks done; flip map honoured; names binding.
- [ ] Golden data generated at base and committed with `_meta.json`, generator and base SHA.
- [ ] Acceptance run: 0 failed, 0 xpassed, 0 errors; traceability green.
- [ ] ruff, format, mypy clean on the owned trees; no production file changed.

## Review Guidance

- Verify every test has a positive control on the same fixture and drives the CLI where behaviour is user-facing.
- Run the suite: only `passed`/`xfailed`. Spot-check three xfails by deleting their marker locally: they must fail with an `AssertionError`/`ImportError` that names the missing behaviour.
- Check `generate_golden_before.py` refuses when `kernel.doctrine_root` is absent, and `_meta.json.base_sha` is the lane base.
- Confirm no test imports a post-cutover module at module level.

## Activity Log

- 2026-10-06T19:30:00Z – system – Prompt created.
