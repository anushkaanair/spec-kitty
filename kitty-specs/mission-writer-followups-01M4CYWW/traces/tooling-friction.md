# Tracer: tooling-friction

One entry per finding: `YYYY-MM-DD · actor · <text>`.

---

2026-10-08 · claude · Seed: (1) mission create still commits 'Add scaffold for feature <slug>' (mission_creation_commit.py:95) - in scope as FR-012. (2) branch-context/create report target_branch = the topic branch itself when started off a stacked PR branch; fine for single_branch but the PR base question (stack on PR 5890 vs main) is not represented anywhere in the Mission contract. (3) The YAML glossary pack header says regenerate via scratchpad/migrate_glossary_pack.py, which is not in the repo. (4) generate_contextive_glossaries.py check is red at HEAD (orchestration.yml stale since #5780) and no CI job runs it.
