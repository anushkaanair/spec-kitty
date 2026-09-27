# Activated custom lifecycle probe

**Source revision**: `5e29a0b4e7b9203b0c6760d68af84e60679feae8`

**CLI**: wheel/editable environment built from that checkout, reporting
`spec-kitty-cli version 4.0.0rc5`

**Environment**: disposable local git repository on branch `main`; commands were separate
processes. Paths below use `<consumer>` deliberately so this public artifact contains no
developer-home path.

## Fixture controls

The fixture declared all of the formal-type inputs missing from issue #4983's original
reproduction:

1. `.kittify/config.yaml` activated `docs-audit` and registered a local organization pack.
2. `<org-pack>/mission_types/docs-audit.yaml` declared the type.
3. `.kittify/overrides/mission-steps/docs-audit/specify/step.yaml` projected a non-empty
   action sequence and mapped artifact key `spec` to `spec-template.md`.
4. `<org-pack>/missions/docs-audit/templates/spec-template.md` supplied that template.
5. `.kittify/missions/docs-audit/mission.yaml` supplied reusable runtime steps `specify`
   and `retrospective`.

Minimal file contents for reproduction:

```yaml
# .kittify/config.yaml
charter_packs:
  org:
    packs:
      - name: acme-doctrine
        local_path: org-packs/acme-doctrine
mission_type_activations:
  - docs-audit
```

```yaml
# org-packs/acme-doctrine/mission_types/docs-audit.yaml
schema_version: 1
id: docs-audit
display_name: "Docs Audit Kitty"
action_sequence:
  - specify
```

```yaml
# .kittify/overrides/mission-steps/docs-audit/specify/step.yaml
id: specify
display_name: "Specification"
step_type: agent
prompt_template: prompt.md
agent_profile: null
guidance: null
delegates_to: []
depends_on: []
sequence_index: 0
in_action_sequence: true
template:
  artifact_key: spec
  template_file: spec-template.md
```

```markdown
<!-- .kittify/overrides/mission-steps/docs-audit/specify/prompt.md -->
# Specify

Author the declared audit specification.
```

```markdown
<!-- org-packs/acme-doctrine/missions/docs-audit/templates/spec-template.md -->
# Custom audit specification

## Scope
```

```yaml
# .kittify/missions/docs-audit/mission.yaml
mission:
  key: docs-audit
  name: Docs Audit
  version: "1.0.0"
steps:
  - id: specify
    title: Specification
    agent_profile: architect-alphonso
  - id: retrospective
    title: Retrospective
    agent_profile: retrospective-facilitator
```

The controls were introduced incrementally. Canonical create produced these deterministic
configuration outcomes before the positive arm:

```text
activated descriptor without actions -> empty action sequence refusal
actions without a spec mapping        -> no configured template mapping refusal
mapping without a resolvable template -> unresolved spec-template.md refusal
complete activated fixture            -> success
```

## Commands

```bash
git init -b main
git config user.name "Spec Kitty Probe"
git config user.email "probe@example.invalid"
git add .
git commit -m "test: activated custom lifecycle fixture"

spec-kitty agent mission create architecture-probe \
  --mission-type docs-audit \
  --topology single_branch \
  --branch-strategy already-confirmed \
  --target-branch main \
  --friendly-name "Docs audit" \
  --purpose-tldr probe \
  --purpose-context probe \
  --json

spec-kitty mission run docs-audit \
  --mission architecture-probe-01M3HSM7 \
  --json

spec-kitty next --agent codex \
  --mission architecture-probe-01M3HSM7 \
  --result success \
  --json

# Run repeatedly from fresh processes through the final custom step, then query.
spec-kitty next --mission architecture-probe-01M3HSM7 --json

spec-kitty implement WP01 --mission architecture-probe-01M3HSM7 --json
spec-kitty accept --mission architecture-probe-01M3HSM7
spec-kitty merge --mission architecture-probe-01M3HSM7 --target main --yes
```

## Sanitized observations

- Canonical create returned mission ID `01M3HSM7R7CGABA9NS3P09SYTA`, derived `mid8`
  `01M3HSM7`, type `docs-audit`, a canonical mission directory, `meta.json`,
  `status.events.jsonl`, and a task scaffold.
- `mission run` returned the same mission ID, froze `mission_template_frozen.yaml`, and
  created the runtime event/snapshot files.
- Fresh `next` processes issued `specify` and then `retrospective` from the custom frozen
  definition, proving the normal steps do not require the original process registry.
- Completing `retrospective` returned blocked because no `docs-audit/retrospective` step
  contract resolved; a fresh query nevertheless reported `mission_state: done`.
- `implement WP01` failed because no WP was declared.
- Acceptance requested `plan.md`, `tasks.md`, and `lanes.json`, demonstrating
  software-dev-shaped assumptions on this custom type.
- Merge refused because `lanes.json` did not exist.

## Interpretation

The activated positive disproves the broad claim that canonical creation or identity
attachment is absent for fully configured custom types. The remaining red arms establish
the bounded work: prevent null-identity `mission run`, define/freeze lifecycle policy,
route WP/no-WP review/accept/merge by that policy, complete every declared step contract
across processes, and keep terminal state non-done when final composition blocks.
