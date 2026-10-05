#!/usr/bin/env python3
"""Deterministic fact collector for the 2026-10-05 CI executive debrief.

Every count, duration and date quoted in ``../README.md`` (and the PDF built
from it) comes from the files this script writes under ``../raw/``. The
narrative interprets those facts; it never adds a number of its own.

Sources (both read-only):

* the GitHub REST API, repository-scoped only (``gh api repos/<repo>/...``),
  paginated; GraphQL and ``search/issues`` are not used;
* the local git history of the checkout this script runs in.

Run from the repository root:

    python docs/reports/ci-debrief/2026-10-05/tooling/collect_ci_debrief.py \
        --cache-dir /tmp/ci-debrief-cache

The cache directory holds raw API responses so a re-run is cheap and
reproducible; it is not committed. ``--as-of`` pins the upper bound of every
time window so a re-run on another day reproduces the same facts.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

REPO = "spec-kitty/spec-kitty"
WINDOW_START = dt.date(2026, 8, 1)

# Workflows whose runs are listed. Keyed by a short label.
WORKFLOWS = {
    "router": "ci-router.yml",
    "modules": "ci-modules.yml",
    "aggregate": "ci-aggregate.yml",
    "quality": "ci-quality.yml",
    "legacy_ci": "ci.yml",
    "nightly": "ci-nightly.yml",
    "recapture": "ci-shard-recapture.yml",
    "release": "release.yml",
}

# Runs and PRs the brief names explicitly; each is fetched so the report can
# quote it from data rather than from the request text.
NAMED_RUNS = [37266895377, 37225822329, 36965118691, 36968309023, 36968955805]
NAMED_ISSUES = [
    3881,
    3993,
    3995,
    4334,
    4347,
    5034,
    5189,
    5240,
    5271,
    5419,
    5510,
    5559,
    5611,
    5614,
    5617,
    5624,
    5652,
    5688,
    5708,
    5730,
]

# Files whose first-added commit marks a CI-topology milestone.
MILESTONE_PATHS = [
    ".github/workflows/ci.yml",
    ".github/workflows/ci-router.yml",
    ".github/workflows/ci-modules.yml",
    ".github/workflows/ci-aggregate.yml",
    ".github/workflows/module-tests.yml",
    ".github/workflows/ci-nightly.yml",
    ".github/workflows/sonar.yml",
    ".github/workflows/packs.yml",
    ".github/workflows/ci-shard-recapture.yml",
    ".github/workflows/ci-charter-shard-recapture.yml",
    ".github/ci-shard-timings.json",
    ".github/ci-module-registry.yml",
    "scripts/ci/gate_selection.py",
    "scripts/ci/nightly_escalation.py",
    "scripts/ci/release_nightly_gate.py",
    "scripts/ci/recapture_shard_timings.py",
    "scripts/ci/capture_shard_timings.py",
]


# --------------------------------------------------------------------------- io


class Api:
    """Thin, cached wrapper around ``gh api`` (repository-scoped paths only)."""

    def __init__(self, cache_dir: Path, refresh: bool) -> None:
        self.cache_dir = cache_dir
        self.refresh = refresh
        cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, path: str) -> Any:
        if not path.startswith(f"repos/{REPO}"):
            raise ValueError(f"refusing non-repository-scoped path: {path}")
        # Cache-file naming only, not charter content hashing.
        key = hashlib.sha256(path.encode()).hexdigest()[:24]  # noqa: TID251
        cached = self.cache_dir / f"{key}.json"
        if cached.exists() and not self.refresh:
            return json.loads(cached.read_text())
        proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            # Fail closed: a missing fact is recorded as missing, never guessed.
            result: Any = {"__error__": proc.stderr.strip() or proc.stdout.strip()}
        else:
            result = json.loads(proc.stdout)
        cached.write_text(json.dumps(result))
        return result


def parse_ts(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def minutes(start: str | None, end: str | None) -> float | None:
    a, b = parse_ts(start), parse_ts(end)
    if a is None or b is None:
        return None
    return round((b - a).total_seconds() / 60.0, 2)


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (deterministic, no interpolation)."""
    ordered = sorted(values)
    rank = max(1, -(-len(ordered) * pct // 100))  # ceil
    return ordered[int(rank) - 1]


def iso_week(ts: str) -> str:
    d = parse_ts(ts)
    assert d is not None
    monday = (d - dt.timedelta(days=d.weekday())).date()
    return monday.isoformat()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------------------------------- collectors

RUN_FIELDS = (
    "id",
    "name",
    "event",
    "head_sha",
    "head_branch",
    "run_attempt",
    "created_at",
    "run_started_at",
    "updated_at",
    "status",
    "conclusion",
    "display_title",
)


def slim_run(run: dict[str, Any]) -> dict[str, Any]:
    out = {k: run.get(k) for k in RUN_FIELDS}
    out["pull_requests"] = [p["number"] for p in run.get("pull_requests") or []]
    return out


def list_runs(api: Api, workflow: str, start: dt.date, end: dt.date) -> list[dict[str, Any]]:
    """All runs of a workflow created in [start, end], day by day.

    The runs endpoint returns at most 1,000 results per query, so the window is
    split into single days (no day comes near that cap)."""

    def one_day(day: dt.date) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        page = 1
        while True:
            data = api.get(f"repos/{REPO}/actions/workflows/{workflow}/runs?per_page=100&page={page}&created={day.isoformat()}")
            batch = data.get("workflow_runs", []) if isinstance(data, dict) else []
            found.extend(slim_run(run) for run in batch)
            if len(batch) < 100:
                return found
            page += 1

    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    runs: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for batch in pool.map(one_day, days):
            for run in batch:
                runs[run["id"]] = run
    return sorted(runs.values(), key=lambda r: r["created_at"])


def run_jobs(api: Api, run_id: int, attempt: int | None = None) -> list[dict[str, Any]]:
    base = f"repos/{REPO}/actions/runs/{run_id}/attempts/{attempt}/jobs" if attempt else f"repos/{REPO}/actions/runs/{run_id}/jobs"
    jobs: list[dict[str, Any]] = []
    page = 1
    while True:
        data = api.get(f"{base}?per_page=100&page={page}")
        batch = data.get("jobs", []) if isinstance(data, dict) else []
        for job in batch:
            jobs.append(
                {
                    "id": job["id"],
                    "name": job["name"],
                    "status": job["status"],
                    "conclusion": job["conclusion"],
                    "started_at": job["started_at"],
                    "completed_at": job["completed_at"],
                    "steps": [
                        {
                            "name": s["name"],
                            "conclusion": s["conclusion"],
                            "started_at": s.get("started_at"),
                            "completed_at": s.get("completed_at"),
                        }
                        for s in job.get("steps") or []
                    ],
                }
            )
        if len(batch) < 100:
            break
        page += 1
    return jobs


def job_minutes(job: dict[str, Any]) -> float:
    m = minutes(job["started_at"], job["completed_at"])
    return m if m is not None and m > 0 else 0.0


# ------------------------------------------------------------ per-PR CI chain


def per_pr_chains(api: Api, runs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """One row per first-attempt pull_request CI Modules run.

    Chain = CI Router run + CI Modules run for the same head SHA (both on the
    pull_request event) + the CI Aggregate run whose title names that CI Modules
    run as its source ("CI Aggregate source <id> attempt 1").

    wall-clock = max(router finish, aggregate-gate job completed)
                 - min(router created, modules created)
    i.e. from the moment GitHub queued PR CI to the moment the terminal gate
    answered. Re-run attempts (run_attempt > 1) are excluded because their
    timestamps span the human delay before the re-run.
    """
    router_by_sha: dict[str, dict[str, Any]] = {}
    for r in runs["router"]:
        if r["event"] == "pull_request" and r["run_attempt"] == 1:
            router_by_sha.setdefault(r["head_sha"], r)
    agg_by_source: dict[str, dict[str, Any]] = {}
    for r in runs["aggregate"]:
        title = r.get("display_title") or ""
        if title.startswith("CI Aggregate source ") and title.endswith(" attempt 1"):
            agg_by_source[title.split()[3]] = r

    modules = [r for r in runs["modules"] if r["event"] == "pull_request" and r["run_attempt"] == 1 and r["status"] == "completed"]

    def build(mod: dict[str, Any]) -> dict[str, Any] | None:
        router = router_by_sha.get(mod["head_sha"])
        agg = agg_by_source.get(str(mod["id"]))
        mjobs = run_jobs(api, mod["id"], 1)
        shard_jobs = [j for j in mjobs if j["name"].startswith("module-tests (")]
        executed = [j for j in shard_jobs if j["conclusion"] not in ("skipped", None)]
        modules_in_matrix = sorted({j["name"].split("(", 1)[1].split(" shard", 1)[0] for j in shard_jobs})
        gate = None
        agg_runner_min = 0.0
        if agg:
            ajobs = run_jobs(api, agg["id"], 1)
            agg_runner_min = sum(job_minutes(j) for j in ajobs)
            gates = [j for j in ajobs if j["name"] == "CI Aggregate gate"]
            gate = gates[0] if gates else None
        starts = [mod["created_at"]] + ([router["created_at"]] if router else [])
        ends = []
        if gate and gate["completed_at"]:
            ends.append(gate["completed_at"])
        if router and router["status"] == "completed":
            ends.append(router["updated_at"])
        wall = minutes(min(starts), max(ends)) if gate and gate["completed_at"] else None
        return {
            "modules_run_id": mod["id"],
            "head_sha": mod["head_sha"],
            "pr": mod["pull_requests"][0] if mod["pull_requests"] else None,
            "created_at": min(starts),
            "week": iso_week(min(starts)),
            "router_run_id": router["id"] if router else None,
            "router_conclusion": router["conclusion"] if router else None,
            "aggregate_run_id": agg["id"] if agg else None,
            "aggregate_gate_conclusion": gate["conclusion"] if gate else None,
            "modules_conclusion": mod["conclusion"],
            "wall_clock_min": wall,
            "modules_run_min": minutes(mod["created_at"], mod["updated_at"]),
            "shard_jobs_in_matrix": len(shard_jobs),
            "shard_jobs_executed": len(executed),
            "modules_in_matrix": len(modules_in_matrix),
            "longest_shard_min": max((job_minutes(j) for j in executed), default=0.0),
            "shard_runner_min": round(sum(job_minutes(j) for j in executed), 2),
            "modules_runner_min": round(sum(job_minutes(j) for j in mjobs), 2),
            "aggregate_runner_min": round(agg_runner_min, 2),
        }

    with ThreadPoolExecutor(max_workers=12) as pool:
        rows = [r for r in pool.map(build, modules) if r]
    return sorted(rows, key=lambda r: r["created_at"])


def weekly_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_week: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_week[r["week"]].append(r)
    out = []
    for week in sorted(by_week):
        group = by_week[week]
        green = [r["wall_clock_min"] for r in group if r["aggregate_gate_conclusion"] == "success" and r["wall_clock_min"]]
        allw = [r["wall_clock_min"] for r in group if r["wall_clock_min"]]
        shards = [r["shard_jobs_executed"] for r in group]
        longest = [r["longest_shard_min"] for r in group if r["shard_jobs_executed"]]
        runner = [r["shard_runner_min"] for r in group if r["shard_jobs_executed"]]
        out.append(
            {
                "week_start": week,
                "pr_ci_runs": len(group),
                "runs_with_gate_verdict": len(allw),
                "green_runs": len(green),
                "green_median_min": round(statistics.median(green), 1) if green else None,
                "green_p90_min": round(percentile(green, 90), 1) if green else None,
                "all_median_min": round(statistics.median(allw), 1) if allw else None,
                "all_p90_min": round(percentile(allw, 90), 1) if allw else None,
                "median_shards_executed": statistics.median(shards) if shards else None,
                "max_shards_executed": max(shards) if shards else None,
                "median_longest_shard_min": round(statistics.median(longest), 1) if longest else None,
                "median_shard_runner_min": round(statistics.median(runner), 1) if runner else None,
            }
        )
    return out


def rolling_daily(rows: list[dict[str, Any]], as_of: dt.date, window_days: int = 7, min_runs: int = 20) -> list[dict[str, Any]]:
    """Per UTC day, the trailing ``window_days`` median/p90 of green wall-clock.

    Days whose window holds fewer than ``min_runs`` green chains are omitted, and
    the as-of day itself is excluded because it is incomplete.
    """
    green = [(day_of(r["created_at"]), r) for r in rows if r["aggregate_gate_conclusion"] == "success" and r["wall_clock_min"]]
    if not green:
        return []
    out = []
    d = min(g[0] for g in green)
    while d < as_of:
        lo = d - dt.timedelta(days=window_days - 1)
        win = [r for gd, r in green if lo <= gd <= d]
        if len(win) >= min_runs:
            wall = [r["wall_clock_min"] for r in win]
            out.append(
                {
                    "date": d.isoformat(),
                    "window_green_runs": len(win),
                    "median_min": round(statistics.median(wall), 1),
                    "p90_min": round(percentile(wall, 90), 1),
                    "median_shards_executed": statistics.median(r["shard_jobs_executed"] for r in win),
                    "median_longest_shard_min": round(statistics.median(r["longest_shard_min"] for r in win), 1),
                    "median_shard_runner_min": round(statistics.median(r["shard_runner_min"] for r in win), 1),
                }
            )
        d += dt.timedelta(days=1)
    return out


def _stats(win: list[dict[str, Any]]) -> dict[str, Any]:
    wall = [r["wall_clock_min"] for r in win]
    return {
        "green_runs": len(win),
        "median_min": round(statistics.median(wall), 1),
        "p90_min": round(percentile(wall, 90), 1),
        "median_shards_executed": statistics.median(r["shard_jobs_executed"] for r in win),
        "median_longest_shard_min": round(statistics.median(r["longest_shard_min"] for r in win), 1),
        "median_shard_runner_min": round(statistics.median(r["shard_runner_min"] for r in win), 1),
    }


def _green_code(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Green first-attempt chains that executed at least one module-test shard.

    PRs routed off the test matrix (docs/prose-only) finish in minutes and would
    otherwise make the median depend on the day's mix of PR types."""
    return [r for r in rows if r["aggregate_gate_conclusion"] == "success" and r["wall_clock_min"] and r["shard_jobs_executed"] > 0]


def daily_code_prs(rows: list[dict[str, Any]], as_of: dt.date, min_runs: int = 10) -> list[dict[str, Any]]:
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in _green_code(rows):
        by_day[r["created_at"][:10]].append(r)
    return [{"date": d} | _stats(v) for d, v in sorted(by_day.items()) if d < as_of.isoformat() and len(v) >= min_runs]


PERIODS = [
    # (label, first day, last day) -- inclusive UTC days, chosen around the
    # landing of mission ci-runtime-stabilisation (#5510) on 2026-10-01.
    ("2026-09-16..2026-09-30", "2026-09-16", "2026-09-30"),
    ("2026-10-02..2026-10-04", "2026-10-02", "2026-10-04"),
]


def period_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for label, lo, hi in PERIODS:
        code = [r for r in _green_code(rows) if lo <= r["created_at"][:10] <= hi]
        allg = [r for r in rows if r["aggregate_gate_conclusion"] == "success" and r["wall_clock_min"] and lo <= r["created_at"][:10] <= hi]
        out.append({"period": label, "population": "green, ran >=1 shard"} | _stats(code))
        out.append({"period": label, "population": "all green"} | _stats(allg))
    return out


def day_of(ts: str) -> dt.date:
    return dt.date.fromisoformat(ts[:10])


def legacy_weekly(runs: list[dict[str, Any]], label: str) -> list[dict[str, Any]]:
    """Weekly run-duration summary for a single-workflow CI (pre-modular)."""
    by_week: dict[str, list[float]] = defaultdict(list)
    counts: Counter[str] = Counter()
    for r in runs:
        if r["event"] != "pull_request" or r["run_attempt"] != 1 or r["status"] != "completed":
            continue
        counts[iso_week(r["created_at"])] += 1
        if r["conclusion"] == "success":
            m = minutes(r["created_at"], r["updated_at"])
            if m is not None:
                by_week[iso_week(r["created_at"])].append(m)
    return [
        {
            "workflow": label,
            "week_start": w,
            "pr_runs": counts[w],
            "green_runs": len(by_week[w]),
            "green_median_min": round(statistics.median(by_week[w]), 1) if by_week[w] else None,
            "green_p90_min": round(percentile(by_week[w], 90), 1) if by_week[w] else None,
        }
        for w in sorted(counts)
    ]


# ------------------------------------------------------------------- nightly


def nightly(api: Api, runs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    summary, cells = [], []
    for r in runs:
        jobs = run_jobs(api, r["id"])
        red = sorted(j["name"] for j in jobs if j["conclusion"] in ("failure", "timed_out", "cancelled"))
        summary.append(
            {
                "run_id": r["id"],
                "event": r["event"],
                "created_at": r["created_at"],
                "date": r["created_at"][:10],
                "conclusion": r["conclusion"],
                "duration_min": minutes(r["run_started_at"] or r["created_at"], r["updated_at"]),
                "jobs_total": len(jobs),
                "jobs_red": len(red),
                "red_jobs": "; ".join(red),
                "runner_min": round(sum(job_minutes(j) for j in jobs), 1),
            }
        )
        for j in jobs:
            cells.append(
                {
                    "run_id": r["id"],
                    "date": r["created_at"][:10],
                    "event": r["event"],
                    "job": j["name"],
                    "conclusion": j["conclusion"],
                    "minutes": job_minutes(j),
                }
            )
    return summary, cells


# ------------------------------------------------------------- named objects


def named_runs(api: Api) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for run_id in NAMED_RUNS:
        run = api.get(f"repos/{REPO}/actions/runs/{run_id}")
        if "__error__" in run:
            out[str(run_id)] = run
            continue
        out[str(run_id)] = {
            "run": slim_run(run) | {"path": run.get("path"), "head_branch": run.get("head_branch")},
            "jobs": run_jobs(api, run_id),
        }
    return out


def failed_job_log_tails(api: Api, named: dict[str, Any], run_ids: list[int]) -> dict[str, Any]:
    """Last lines of each failed job's log for the named runs (plain-text endpoint)."""
    out: dict[str, Any] = {}
    for rid in run_ids:
        for job in named.get(str(rid), {}).get("jobs", []):
            if job["conclusion"] != "failure":
                continue
            cached = api.cache_dir / f"log-{job['id']}.txt"
            if not cached.exists() or api.refresh:
                proc = subprocess.run(
                    ["gh", "api", f"repos/{REPO}/actions/jobs/{job['id']}/logs"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                # The logs endpoint redirects to a signed blob URL. On failure the
                # error text carries that signed URL, so record a fixed marker
                # instead of the message (never write a credential-bearing URL).
                cached.write_text(proc.stdout if proc.returncode == 0 else "__error__ log download failed (redirect target not reachable)")
            lines = [ln.split(" ", 1)[-1] for ln in cached.read_text().splitlines() if ln.strip()]
            out[f"{rid}/{job['name']}"] = lines[-25:]
    return out


def named_issues(api: Api) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for n in NAMED_ISSUES:
        issue = api.get(f"repos/{REPO}/issues/{n}")
        if "__error__" in issue:
            out[str(n)] = issue
            continue
        rec = {
            "number": n,
            "title": issue["title"],
            "kind": "pr" if "pull_request" in issue else "issue",
            "state": issue["state"],
            "state_reason": issue.get("state_reason"),
            "created_at": issue["created_at"],
            "closed_at": issue.get("closed_at"),
            "author": (issue.get("user") or {}).get("login"),
            "assignees": sorted(a["login"] for a in issue.get("assignees") or []),
            "milestone": (issue.get("milestone") or {}).get("title"),
            "labels": sorted(lbl["name"] for lbl in issue.get("labels") or []),
            # Opening text, kept so a claim quoted from an issue or PR body is
            # traceable to collected data.
            "body_excerpt": (issue.get("body") or "")[:4000],
        }
        if rec["kind"] == "pr":
            pr = api.get(f"repos/{REPO}/pulls/{n}")
            rec.update(
                {
                    "merged_at": pr.get("merged_at"),
                    "draft": pr.get("draft"),
                    "head_ref": (pr.get("head") or {}).get("ref"),
                    "head_sha": (pr.get("head") or {}).get("sha"),
                    "base_ref": (pr.get("base") or {}).get("ref"),
                    "changed_files": pr.get("changed_files"),
                }
            )
            sha = rec["head_sha"]
            if sha:
                prs_runs = api.get(f"repos/{REPO}/actions/runs?head_sha={sha}&per_page=100")
                rec["ci_runs_on_head"] = [
                    {
                        "name": r["name"],
                        "event": r["event"],
                        "conclusion": r["conclusion"],
                        "created_at": r["created_at"],
                        "actor": (r.get("actor") or {}).get("login"),
                        "triggering_actor": (r.get("triggering_actor") or {}).get("login"),
                    }
                    for r in prs_runs.get("workflow_runs", [])
                ]
        out[str(n)] = rec
    return out


def merged_prs_by_day(api: Api, since: dt.date, until: dt.date) -> list[dict[str, Any]]:
    """Merged PRs into main per UTC day, from the paginated pulls list."""
    counts: Counter[str] = Counter()
    page = 1
    while True:
        data = api.get(f"repos/{REPO}/pulls?state=closed&base=main&sort=updated&direction=desc&per_page=100&page={page}")
        if not isinstance(data, list) or not data:
            break
        stop = False
        for pr in data:
            if pr.get("merged_at"):
                day = pr["merged_at"][:10]
                if since.isoformat() <= day <= until.isoformat():
                    counts[day] += 1
            if pr["updated_at"][:10] < since.isoformat():
                stop = True
        if stop or len(data) < 100:
            break
        page += 1
    return [{"date": d, "merged_prs": counts[d]} for d in sorted(counts)]


# ----------------------------------------------------------------------- git


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def git_milestones() -> list[dict[str, Any]]:
    rows = []
    for path in MILESTONE_PATHS:
        added = git("log", "--diff-filter=A", "--format=%H|%ad|%s", "--date=short", "--", path).strip()
        deleted = git("log", "--diff-filter=D", "--format=%H|%ad|%s", "--date=short", "-1", "--", path).strip()
        touches = git("log", "--format=%H", "--", path).split()
        first = added.splitlines()[-1].split("|", 2) if added else None
        last_del = deleted.split("|", 2) if deleted else None
        rows.append(
            {
                "path": path,
                "added_sha": first[0][:9] if first else None,
                "added_date": first[1] if first else None,
                "added_subject": first[2] if first else None,
                "deleted_date": last_del[1] if last_del else None,
                "deleted_subject": last_del[2] if last_del else None,
                "commits_touching": len(touches),
                "exists_at_head": Path(path).exists(),
            }
        )
    return rows


def ci_config_commits(since: dt.date) -> list[dict[str, Any]]:
    """Every commit on main touching CI configuration since ``since``."""
    log = git(
        "log",
        f"--since={since.isoformat()}",
        "--format=%H|%ad|%s",
        "--date=short",
        "--",
        ".github/workflows",
        ".github/ci-module-registry.yml",
        ".github/ci-shard-timings.json",
        "scripts/ci",
    )
    rows = []
    for line in log.splitlines():
        sha, date, subject = line.split("|", 2)
        rows.append({"date": date, "sha": sha[:9], "week": iso_week(date + "T00:00:00Z"), "subject": subject})
    return sorted(rows, key=lambda r: (r["date"], r["sha"]))


def git_history_floor() -> dict[str, Any]:
    oldest = git("log", "--reverse", "--format=%H|%ad", "--date=short").splitlines()[0]
    shallow = git("rev-parse", "--is-shallow-repository").strip()
    return {"oldest_commit_in_checkout": oldest, "shallow": shallow == "true", "head": git("rev-parse", "HEAD").strip()}


def shard_timings_snapshot() -> dict[str, Any]:
    data = json.loads(Path(".github/ci-shard-timings.json").read_text())
    prov = data.get("module_capture_provenance", {})
    durations = data.get("module_duration_seconds", {})
    counts = data.get("module_test_count", {})
    modules = []
    for name in sorted(durations):
        p = prov.get(name, {})
        modules.append(
            {
                "module": name,
                "recorded_seconds": durations.get(name),
                "recorded_tests": counts.get(name),
                "captured_at": p.get("captured_at"),
                "producer": p.get("producer"),
            }
        )
    return {
        "schema_version": data.get("schema_version"),
        "modules_recorded": len(durations),
        "sum_recorded_seconds": round(sum(durations.values()), 1),
        "modules": modules,
    }


# ----------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent.parent / "raw")
    parser.add_argument("--as-of", default="2026-10-05")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    api = Api(args.cache_dir, args.refresh)
    as_of = dt.date.fromisoformat(args.as_of)
    out = args.out_dir

    runs = {label: list_runs(api, wf, WINDOW_START, as_of) for label, wf in WORKFLOWS.items()}
    run_counts = {
        label: {
            "total": len(rs),
            "first_created": rs[0]["created_at"] if rs else None,
            "last_created": rs[-1]["created_at"] if rs else None,
            "by_event": dict(Counter(r["event"] for r in rs)),
        }
        for label, rs in runs.items()
    }
    write_json(out / "workflow_run_counts.json", run_counts)

    chains = per_pr_chains(api, runs)
    write_csv(out / "per_pr_ci_runs.csv", chains)
    write_csv(out / "per_pr_ci_weekly.csv", weekly_summary(chains))
    write_csv(out / "per_pr_ci_rolling7d.csv", rolling_daily(chains, as_of))
    write_csv(out / "per_pr_ci_daily_code.csv", daily_code_prs(chains, as_of))
    write_csv(out / "per_pr_ci_periods.csv", period_summary(chains))
    legacy = legacy_weekly(runs["quality"], "ci-quality.yml") + legacy_weekly(runs["legacy_ci"], "ci.yml")
    write_csv(out / "legacy_ci_weekly.csv", legacy)

    nsum, ncells = nightly(api, runs["nightly"])
    write_csv(out / "nightly_runs.csv", nsum)
    write_csv(out / "nightly_jobs.csv", ncells)

    named = named_runs(api)
    write_json(out / "named_runs.json", named)
    write_json(out / "failed_job_log_tails.json", failed_job_log_tails(api, named, [36965118691, 37266895377]))
    write_json(out / "named_issues.json", named_issues(api))
    write_csv(out / "merged_prs_by_day.csv", merged_prs_by_day(api, as_of - dt.timedelta(days=14), as_of))
    write_csv(out / "release_runs.csv", [{k: r[k] for k in ("id", "event", "head_branch", "created_at", "conclusion", "display_title")} for r in runs["release"]])
    write_csv(out / "git_milestones.csv", git_milestones())
    write_csv(out / "ci_config_commits.csv", ci_config_commits(WINDOW_START))
    write_json(out / "shard_timings_snapshot.json", shard_timings_snapshot())

    green = [r["wall_clock_min"] for r in chains if r["aggregate_gate_conclusion"] == "success" and r["wall_clock_min"]]
    write_json(
        out / "meta.json",
        {
            "repo": REPO,
            "window_start": WINDOW_START.isoformat(),
            "as_of": as_of.isoformat(),
            "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "git": git_history_floor(),
            "per_pr_chain_rows": len(chains),
            "per_pr_green_rows": len(green),
            "per_pr_green_median_min": round(statistics.median(green), 1) if green else None,
            "per_pr_green_p90_min": round(percentile(green, 90), 1) if green else None,
            "nightly_runs": len(nsum),
            "nightly_red_runs": sum(1 for r in nsum if r["conclusion"] == "failure"),
            "billing": api.get(f"repos/{REPO}/actions/runs/{NAMED_RUNS[0]}/timing"),
        },
    )
    print(f"wrote facts to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
