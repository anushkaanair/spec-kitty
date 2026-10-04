# Design decisions — regression-slice-cleanup

- 2026-10-04 — Branch named `issue-5618-regression-slice-cleanup` (charter) instead of the brief's `fix/regression-slice-cleanup`; the charter wins.
- 2026-10-04 — Removing `regression` does not de-route tests (module shards select `not performance and not stress`); it only moves `fast`/`unit` tests into `make test-fast`.
- 2026-10-04 — Operator direction: no planning-branch draft PR while no multi-user runs are ongoing; the early draft #5626 was closed and the PR opens at closeout.
