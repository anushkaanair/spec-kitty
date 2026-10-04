# Tooling friction — implement-degod-01M44488

Running log (1-3 sentences per dated entry). Seeded at planning.

Tooling this mission touches: the `spec-kitty` CLI (installed editable from this checkout), the
mission loop (`agent mission create/setup-plan/finalize-tasks`, `implement`, `move-task`,
`consolidate`), pytest with xdist, ruff, mypy, and the architectural gate files.

- 2026-10-04 — `spec-kitty` was not on PATH in the cloud container. Fixed with an editable install
  into `.venv` plus a symlink into `~/.local/bin`, so `spec-kitty --version` reports `4.0.0rc6` from
  this checkout.
- 2026-10-04 — The shallow clone hid the 90-day churn history. The archaeologist lens had to deepen
  it with `git fetch --shallow-since=2026-06-20` before `git log --since=90.days` was meaningful.
- 2026-10-04 — The specify workflow leaves `spec.md` untracked until it is substantive (#846). The
  session's stop hook flags every untracked file, so the empty scaffold had to be parked outside the
  repo until the spec was written.
