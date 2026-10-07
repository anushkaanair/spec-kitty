---
work_package_id: WP03
title: One implementer-of-record authority for consolidation
dependencies: []
requirement_refs:
- FR-008
- NFR-003
planning_base_branch: issue-5446-review-exit-guard
merge_target_branch: issue-5446-review-exit-guard
branch_strategy: Planning artifacts for this mission were generated on issue-5446-review-exit-guard. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into issue-5446-review-exit-guard unless the human explicitly redirects the landing branch.
subtasks:
- T008
- T009
history: []
agent_profile: implementer-ivan
authoritative_surface: src/specify_cli/consolidation/preflight.py
create_intent: []
execution_mode: code_change
owned_files:
- src/specify_cli/consolidation/preflight.py
- src/specify_cli/status/review_roles.py
- src/specify_cli/status/__init__.py
- tests/consolidation/test_preflight_seam.py
- tests/consolidation/test_hollow_review_warnings.py
- tests/unit/status/test_review_roles.py
role: implementer
tags: []
task_type: implement
tracker_refs: []
---
# WP03 — One implementer-of-record authority (#5340)

## Goal
`consolidation/preflight._latest_actor_for_transition(feature_dir, wp_id, "in_progress")` counts a reviewer's `in_review -> in_progress` rework verdict as the implementer, so after reject → rework → approve it can read implementer == reviewer and warn falsely. Make `_independent_reviewer_confirmed` use `status.latest_implementer_actor` / `is_latest_implementer` (facade import only, SR-2).

## Subtasks
- **T008** Red-first (own commit): honest loop I implements, R reviews and rejects with a rework verdict (`in_review -> in_progress`, review_ref), I reworks and resubmits, R approves, force_count >= 2 undiscounted → `_collect_hollow_review_warnings` returns `{}`. Twin: I approves its own work → still warns.
- **T009** IMPORTANT (analysis H3): `is_latest_implementer` compares per tool only; today's preflight compares full actor strings. Keep the full-identity comparison: add a pure sibling in `review_roles` that returns the qualifying implementer EVENT (or its full actor identity), have `latest_implementer_actor` use it, and compare that full identity with the approver's like today. Add a same-tool-different-profile twin test (no new false warning). Then: read events tolerantly (existing raw-dict fixtures lack `at`/`execution_mode`; keep them working — either parse into `StatusEvent` with a tolerant path or adapt the projection input), compute the implementer via `latest_implementer_actor`, compare with `is_latest_implementer`. Keep the approver lookup. In `review_roles.py`, document that this is the single implementer-of-record authority and that the reducer's `implementer_of_record` snapshot slot is claim provenance (the planned→claimed claimant), not an implementer authority.

## Validation
- `pytest tests/consolidation/test_preflight_seam.py tests/consolidation/test_hollow_review_warnings.py tests/unit/status/test_review_roles.py tests/architectural/test_status_module_boundary.py -q`
