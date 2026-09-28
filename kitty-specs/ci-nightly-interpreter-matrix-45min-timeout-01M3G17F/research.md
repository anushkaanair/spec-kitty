# Research: Nightly interpreter-matrix leg completes within its time cap

This is reference material for the plan phase — evidence and measurement
mechanics that support `spec.md`'s FR/NFR/AC contract. Nothing here is itself
a binding requirement; where a number or observation needs to become
binding, `spec.md` states it as an FR/NFR/AC and cites this file.

## 1. The two prior dispatch runs (issue #4951's evidence)

Both were manual `workflow_dispatch`es of `ci-nightly.yml` against branch
`issue-4866-interpreter-matrix-3-13` (mission #4866), run to verify that
mission's environment-pinning fix (`uv run --frozen --python 3.13
--all-extras`, FR-001) on a real GitHub-hosted runner. Both are quoted from
the issue body verbatim below; this orchestrator did not re-fetch these
specific run logs (the issue itself notes the raw pytest log is unretrievable
for both — `BlobNotFound`, Azure blob eviction before flush — so there is
nothing further to fetch).

| | Run 1 (serial) | Run 2 (`-n auto`) |
|---|---|---|
| Run ID | `35778042008` | `35788021368` |
| Commit | `694fda140` | `3b2517d5e` |
| Config | serial `pytest`, no `-n auto` | `-n auto` added |
| Sync step | succeeded in ~2s | succeeded in ~2s |
| `pytest` step start | 20:06:24Z | 21:40:41Z |
| `pytest` step outcome | never completed | never completed |
| Job conclusion | `cancelled` | `cancelled` |
| Force-killed | 21:01:01Z (~54m37s into the step) | 22:35:21Z (~54m40s into the step) |
| Check-run annotation | "The job has exceeded the maximum execution time of 45m0s" | same |
| Raw pytest log | unretrievable (`BlobNotFound`) | unretrievable (`BlobNotFound`) |
| "Upload interpreter-matrix reports" step | never started | never started |

**What this proves**: the #4866 environment-pinning fix works on a real
GitHub-hosted runner — sync succeeded in ~2 seconds both times, so the
interpreter is genuinely 3.13 with `--all-extras`, not silently re-synced to
the pinned 3.11 default (the pre-#4866 defect).

**What this does not prove**: that the leg can produce a verdict on this
runner class at all — in neither configuration has it ever done so.

**What cannot be quoted**: no retrievable pytest log for either run, so no
per-test timing, no collection count, and no partial-progress indicator is
available from these two runs themselves.

**Reasonable inference, not a log quote**: ~54 minutes of pytest running
without exiting is more consistent with collection succeeding and the suite
being mid-execution than with a collection-time import failure — the
pre-#4866 defect died within ~1 minute with 13 `ModuleNotFoundError`s
(test-only deps `pytestarch`, `respx`, `pytest_benchmark` missing because the
silently-resynced environment used default extras). This is an inference
about shape, not a measured fact; the plan phase's fresh capture (Section 3
below) is what replaces inference with a real number.

**`-n auto` gave no measurable gain on this runner**: both runs died
mid-suite at the cap, so there is no wall-clock completion time for either
configuration to compare. Any claim that `-n auto` helps or doesn't help on
this runner class is unsupported by these two runs and must come from the
fresh capture instead.

## 2. Local-scale numbers (context only, not a runner-sized estimate)

On the mission author's local 24-core workstation, the same `fast or unit`
selector completed in:

- ~5036s (~84 min), serial, 3.11 baseline
- ~475.87s (~8 min), with `-n auto`, 3.13, ~34,835 tests collected

These numbers are **offered as context only** — GitHub-hosted runners
(`ubuntu-24.04` standard, 2 vCPU) are far smaller than a 24-core workstation,
so neither figure is a usable estimate of GitHub-runner wall-clock. The
issue itself is explicit that this is "plausible context, not a measured
explanation" — the runner's actual CPU/IO ceiling under this test population
was never profiled. The plan phase's shard-sizing capture must not
extrapolate a shard count or budget from these local numbers; it must use a
fresh, real capture on the actual runner class (`ubuntu-24.04`).

## 3. SK-247 and why Option B (reuse `module-tests.yml` sharding) is rejected

Ledger entry SK-247 (status open at the time this spec was written, verified
first-hand in mission `ci-nightly-wallclock-budget-01M34HNZ`) documents:

- `.github/ci-module-registry.yml` claims `shard_count` is chosen by greedy
  LPT bin-packing of *measured* per-test durations.
- This claim is **false for 20 of the registry's 21 modules**.
- The producer, `scripts/ci/capture_shard_timings.py`, pairs durations to
  node ids **positionally** — the committed `.github/ci-shard-timings.json`
  drops node ids for compactness to keep the file smaller, so there is no
  join key.
- When the committed duration-list length no longer matches the live
  collected node-id count (which it doesn't, for 20/21 modules — measured
  mismatches up to ~4x, e.g. `cli`: committed 2704 vs. collected 682), the
  consumer silently falls back to **uniform/count-based weighting for the
  whole module**.
- No gate catches this: the skew guard
  (`tests/architectural/test_module_shard_registry.py::test_inter_shard_skew_within_twenty_percent`)
  re-reads the same committed (wrong-length) list, so it cannot detect its
  own staleness.

This orchestrator additionally verified (2026-09-27, direct read of
`scripts/ci/capture_shard_timings.py`'s module docstring and constants) that
the capture tool is tightly coupled to the registry's own consumer shape: it
reads `.github/ci-module-registry.yml` (`REGISTRY_PATH`), writes
`.github/ci-shard-timings.json` (`TIMINGS_PATH`), and selects tests over the
registry's own `test_dirs` for a named module. It is not a drop-in tool for a
nightly-only, registry-independent shard split — using it for the
interpreter leg would mean either (a) adding the interpreter leg as a fake
"module" row in a registry this mission is constrained not to touch (C-002),
or (b) forking/adapting the tool, which reopens the same positional-pairing
hazard unless the fork is careful never to let a committed duration list
silently outlive the node-id set it was measured against.

**Rejection rationale (for `spec.md`'s Clarifications section, restated
here in full)**: Option B — splitting the interpreter leg using
`module-tests.yml`'s existing sharding infrastructure — is rejected because
it would inherit SK-247's documented-broken balancing mechanism wholesale.
The operator's Q1 decision (nightly-only shards, sized from fresh timings,
inside `ci-nightly.yml` itself) avoids this by construction: a fresh capture
scoped to exactly this leg's own test population, consumed once, immediately,
by the same change that produces it — never committed as a long-lived
duration list that can silently drift out of sync with a later collection
run the way `ci-shard-timings.json` did for `charter` and 19 other modules.

## 4. Precedent: mission `ci-nightly-wallclock-budget-01M34HNZ` (#4865/#4864, PR #4948)

This sibling mission split the nightly `performance-and-e2e` job (issue
#4865: a shared 60-minute cap truncated the stress suite and blended three
suites' verdicts into one) into three independent jobs — `performance`
(35 min), `e2e` (40 min), `stress` (10 min) — each:

- with its own `timeout-minutes`, sized from a real measured run (not copied
  unchanged from the old shared cap);
- keeping the existing `set +e` + `if: always()` + terminal fail-loud +
  exit-0-or-5-passes convention;
- running under `fail-fast: false` (implicit for independent jobs — no
  shared matrix to cancel);
- each with its own `scripts/ci/nightly_escalation.py --suite-key` call
  (`performance`, `e2e`, `stress` — already distinct keys, since they were
  already separate suites before the split, not new shards of one suite);
- requiring `nightly-summary`'s `needs:` list to grow from one name
  (`performance-and-e2e`) to three;
- requiring `tests/architectural/test_performance_marker_guard.py`'s three
  hardcoded-job-name tests to be updated to the new job names (that mission's
  FR-010 — the exact same guard file, same category of maintenance, this
  mission's FR-009/FR-010 repeat for the interpreter leg's shards instead of
  the perf/e2e/stress split);
- validated by manual `workflow_dispatch` evidence before merge (that
  mission's FR-009/NFR-006), since none of the real acceptance criteria
  (no truncation, per-suite verdict, correct budget) are provable by a unit
  test alone.

This mission (`ci-nightly-interpreter-matrix-45min-timeout-01M3G17F`) follows
the same shape for the interpreter leg, with two differences the sibling
mission did not face: (1) the interpreter leg is currently ONE suite being
split into multiple shards of the SAME suite (not three previously-separate
suites gaining independent jobs), so shard identity and `--suite-key`
uniqueness must be freshly designed rather than inherited from pre-existing
distinct suite names; and (2) the interpreter leg's shard-sizing data has no
prior measured baseline at all (the two dispatch runs in Section 1 never
completed), whereas the sibling mission had a real 65-minute combined-job
measurement to re-partition from.

## 5. Precedent: mission `interpreter-matrix-3-13-env-and-divergence-01M34HVD` (#4866, PR #4952)

This mission fixed the root cause that made the interpreter leg's own
`pytest` step silently re-sync to the wrong interpreter (3.11) with default
extras, via a nested `uv run --frozen` call inside the leg discarding the
outer `uv sync --python 3.13 --all-extras`. The fix: pin `--python`/
`--all-extras` on the run step itself, plus `--no-sync` at two nested `uv
run` call sites (a third and fourth site are tracked separately as follow-up
#4922 — explicitly unrelated to this mission's timeout mechanism). It also
added the per-interpreter dedicated venv (`UV_PROJECT_ENVIRONMENT:
.venv-py${{ matrix.python-version }}`, WP04) as defense-in-depth so a nested
`uv run` at worst re-syncs the leg's own dedicated venv, never a
differently-pinned concurrent process's environment.

This mission's shard split must preserve both halves of that fix
independently in every shard (FR-008): each shard job needs its own
`uv sync --frozen --all-extras --python "3.13"` step and its own
`UV_PROJECT_ENVIRONMENT: .venv-py3.13`, not a shared sync step whose result
is reused across shards (which would reopen a cross-shard version of the
exact hazard #4866 fixed if any two shards ran concurrently against a shared
environment path).

## 6. How the up-to-3 measurement dispatches (Q2) should be used

Operator decision Q2 authorizes, starting at the plan/implementation phase
(not during spec authoring — see `spec.md` Constraint C-003), up to 3 manual
`workflow_dispatch` runs of `ci-nightly.yml` on this mission's branch:

1. **Baseline / timing-capture run**: dispatch with the interpreter leg
   still shaped however the plan's chosen measurement mechanism needs it
   (e.g. a temporary per-module/per-directory timing capture step, or a
   `pytest --collect-only -q` + a real timed sub-run per candidate shard
   boundary). This run's job is to produce REAL per-shard-candidate wall-clock
   and collection-count numbers on `ubuntu-24.04` — not to be the final
   shape. Its data feeds the shard count N and each shard's
   `timeout-minutes` (FR-002, NFR-001).
2. **Validation run**: dispatch the shaped, shard-split `interpreter-matrix`
   replacement and confirm every shard reaches a real `success`/`failure`
   conclusion within its budget (SC-001, SC-002), that the coverage-
   completeness check passes (SC-003), and that each shard's escalation
   suite-key is distinct and independently functional (SC-005). This run's
   URL and every shard's conclusion must be recorded in the PR body or a
   mission tracer file (NFR-005) as the durable evidence FR-014 requires.
3. **Spare**: reserved for a re-run if the validation run surfaces a fixable
   issue (a mis-sized budget, a coverage gap, a flaky escalation call) that a
   second attempt can confirm resolved without needing to go back to the
   operator. If more than 3 total dispatches are needed, that returns to the
   operator per Q2's own limit — this is a plan/implement-phase decision
   point, not something to pre-resolve in this spec.

Each of these three runs is real GitHub Actions minutes spent against the
mission's own branch — accepted cost, analogous to NFR-004's "recapture is
accepted cost" precedent in the sibling wallclock-budget mission.

## 7. `tests/architectural/_gate_coverage.py`'s existing coverage-oracle
   substrate (a reuse candidate for FR-004/NFR-002/FR-016/FR-017)

Verified first-hand (2026-09-27, direct read of
`tests/architectural/_gate_coverage.py`): `ci-nightly.yml` is a member of the
module-level `WORKFLOW_FILES` tuple, so this file's parser
(`parse_workflow`) already statically parses every pytest invocation in
`ci-nightly.yml` — including the current single-job `interpreter-matrix`
step — into `Gate` objects feeding a repo-wide orphan/duplicate coverage
oracle consumed by `tests/architectural/test_ci_collection_completeness.py`.

The same file separately ships a `BaselineTarget` dataclass and a
`collect_real_union_for_target` function whose docstring states the design
goal verbatim: a target matched by `(workflow, job)` alone "transparently
covers however many shard legs the job has TODAY ... or GROWS to under [a
later mission] (a matrix): `collect_real_union_for_target` unions every
matching leg's real selection, so a shard split alone (same total coverage,
more legs) cannot false-red GC-2b." This is real, tested infrastructure
purpose-built for exactly the falsification target FR-004/NFR-002 need (a
real `pytest --collect-only` node-id union across a job's shard legs,
compared against a full/frozen baseline) — a near-turnkey reuse candidate,
narrower in one sense (a per-job baseline, not a from-scratch "full 3.13
selection vs. shard union" comparison) but directly relevant either as the
implementation or as load-bearing precedent for FR-004.

**Caveat verified in the same read, so the plan phase does not overstate
this**: `BASELINE_TARGETS` — the tuple of `BaselineTarget` entries this
mechanism actually evaluates — is currently `()` (empty); an adjacent
comment records that "the former slow-tests authoring baseline was retired
... no restored workflow currently owns an E3 selection baseline." So no
job, including `interpreter-matrix`, is presently baselined through this
mechanism — it is available, tested substrate the plan phase can extend (add
an `interpreter-matrix` `BaselineTarget` entry) or explicitly reject with a
documented rationale, not an already-active gate this mission would
otherwise silently duplicate or contradict.

**Further verified (2026-09-27), a second gap beyond the empty tuple**: no
test file anywhere in `tests/` imports or calls `collect_real_union_for_target`,
`gates_for_target`, or `BaselineTarget` (repo-wide grep, zero hits outside
`_gate_coverage.py` itself), and no Makefile target or
`.github/workflows/*.yml` invokes the `--emit-census`/`--verify-census`/
`--freeze-baselines` CLI entry points that would exercise them either. The
module's own top-of-file docstring names `test_ci_collection_completeness.py`
as this class of mechanism's "companion end-to-end oracle" consumer, but that
file's own docstring states plainly that the collection-completeness oracle
(among the other SC-013/NFR-005 tests that depended on the same deleted
workflow files) "were retired with it" (planning#57), and lists only unrelated
pure-unit checks
(`baseline_reaches`, `job_runs_under`, `split_top_level`, `normalize_condition`)
as what remains. So this mechanism is unconsumed, not merely unconfigured:
reusing it for FR-004/FR-016/FR-017 is not "add a `BaselineTarget` entry to an
already-wired check" but "add the entry AND author a brand-new consuming
test/oracle from scratch," and FR-017/SC-010's reuse-vs-rejection decision
must be costed against that larger lift.

**Relevance to FR-016, not only FR-004/NFR-002**: `gates_for_target` — the
function `collect_real_union_for_target` calls to resolve a
`BaselineTarget`'s matching legs — already raises loudly, naming the stale
target's slug/workflow/job, when a target's `(workflow, job)` pairing no
longer resolves to any parsed `Gate` (verified first-hand,
`tests/architectural/_gate_coverage.py`, function `gates_for_target`): "a
stale `BASELINE_TARGETS` entry must be fixed, not ignored." That is the same
class of hazard — a job renamed or deleted from the workflow file — that
FR-016's shard-identity roster exists to catch at the per-shard level (a
shard deleted from the job list entirely, distinct from a present-but-empty
shard, per User Story 2 AC3). FR-017's reuse-vs-rejection evaluation
therefore must weigh this mechanism against BOTH FR-004/NFR-002's node-id
union check AND FR-016's roster diff (spec.md SC-010), rather than
evaluating reuse for the node-id check alone while the roster mechanism gets
designed in isolation from the same canonical substrate.

**Shape gap this reuse candidate does NOT close for FR-016**: `BaselineTarget`
itself (verified first-hand, same file, the dataclass definition) carries
exactly three fields — `slug`, `workflow`, `job` — and no independently-
declared selector or test-paths field of its own. `gates_for_target` matches
a target's legs purely by `g.workflow == target.workflow and g.job ==
target.job` against the `Gate` list `parse_workflow` produces by parsing the
CURRENT `ci-nightly.yml` live — the "selector" in play is whatever that live
parse currently reads out of the same workflow file being validated, never a
value stored independently of it. So `gates_for_target`'s raise-on-zero-gates
behavior only catches the identity half of FR-016's own definition ("shard
name -> its assigned test paths/selector") — a shard's job key deleted from
`jobs:` entirely. It cannot catch a shard whose job key still exists but
whose selector was silently reassigned or corrupted to the wrong subset of
tests, because it never compares a gate's selector against any independently
recorded intended assignment. Reusing `gates_for_target` therefore does not
by itself satisfy FR-016: the plan phase must still separately declare/store
each shard's intended test-paths/selector to cover that second half, rather
than treating this mechanism's raise behavior as a complete substitute for
the roster.

**Risk this raises for FR-001's shard split**: because `_gate_coverage.py`'s
parser already treats `interpreter-matrix`'s current single
`pytest -m "fast or unit"` invocation as one `Gate`, whichever exact
invocation shape each new shard uses in the workflow YAML must remain one of
the shapes `parse_workflow` recognizes — this same file's own comments
document a "runner-prefix pattern mis-parsed" failure mode for other
workflows (`ci-router.yml`/`packs.yml` gates silently dropped because
`--frozen`'s optional argument swallowed the `pytest` command word) as a
concrete precedent for how a plausible-looking invocation shape can silently
break this parser. FR-017 requires the plan phase to (a) make an explicit
reuse-vs-rejection decision against this mechanism before designing FR-004's
implementation, mirroring the SK-247/`capture_shard_timings.py` rejection
write-up in Section 3 above, and (b) confirm each new shard's `pytest`
invocation stays parseable by `_gate_coverage.py`, so the split does not
silently break or mis-model the pre-existing repo-wide coverage oracle that
`spec.md`'s C-005 full `tests/architectural/` run will exercise.
