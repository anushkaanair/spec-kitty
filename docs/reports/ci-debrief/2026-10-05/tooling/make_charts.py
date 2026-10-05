#!/usr/bin/env python3
"""Render the debrief's charts from ``../raw/`` (the collector output) to SVG.

Charts only draw collected facts; nothing here computes a new number except
the plotting positions. Palette: the brand's deep yellow leads (series 1), with
blue and orange as series 2 and 3. Checked with the dataviz palette validator
(light mode). The deep yellow sits below 3:1 contrast on white, so every series
is also direct-labelled and the underlying table is in the appendix.
Status colours (green = passed, red = failed) are reserved for pass/fail cells.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.dates as mdates  # noqa: E402  (backend must be chosen first)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
OUT = ROOT / "charts"

INK, INK_SOFT, MUTED, GRID, BASE = "#231D12", "#5A5342", "#8A8578", "#E8E2D0", "#C3BCA8"
S1, S2, S3 = "#C99A0E", "#2A78D6", "#EB6834"
GOOD, BAD, SKIP = "#0CA30C", "#D03B3B", "#E8E2D0"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "text.color": INK,
        "axes.labelcolor": INK_SOFT,
        "axes.edgecolor": BASE,
        "axes.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "svg.fonttype": "none",
    }
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (RAW / name).open() as fh:
        return list(csv.DictReader(fh))


def num(v: str) -> float | None:
    return float(v) if v not in ("", "None", None) else None


def day(v: str) -> dt.date:
    return dt.date.fromisoformat(v[:10])


def save(fig: Figure, name: str) -> None:
    fig.savefig(OUT / name, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def _daily() -> list[dict[str, str]]:
    return read_csv("per_pr_ci_daily_code.csv")


def per_pr_runtime(name: str = "per-pr-wall-clock.svg", size: tuple[float, float] = (6.3, 2.5)) -> None:
    rows = _daily()
    days = [day(r["date"]) for r in rows]
    med = [float(r["median_min"]) for r in rows]
    p90 = [float(r["p90_min"]) for r in rows]
    fig, ax = plt.subplots(figsize=size)
    ax.plot(days, p90, color=S2, lw=2, marker="o", ms=3.5, label="p90")
    ax.plot(days, med, color=S1, lw=2, marker="o", ms=3.5, label="median")
    landing = dt.date(2026, 10, 1)
    ax.axvline(landing, color=BASE, lw=1, ls=(0, (3, 2)))
    ax.annotate(
        "ci-runtime-stabilisation\nlands (#5510)",
        (landing, max(p90) * 1.02),
        xytext=(-4, 0),
        textcoords="offset points",
        ha="right",
        va="top",
        fontsize=7,
        color=INK_SOFT,
    )
    for series, label in ((p90, "p90"), (med, "median")):
        ax.annotate(f"{label} {series[-1]:.0f}", (days[-1], series[-1]), xytext=(6, 0), textcoords="offset points", va="center", color=INK_SOFT, fontsize=7.5)
    ax.set_ylim(0, max(p90) * 1.12)
    ax.set_ylabel("minutes, push to final gate")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_xticks(days[::2])
    ax.tick_params(axis="x", labelsize=7)
    ax.legend(frameon=False, loc="lower left", ncol=2)
    save(fig, name)


def per_pr_shards() -> None:
    rows = _daily()
    days = [day(r["date"]) for r in rows]
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.0))
    ax = axes[0]
    ax.bar(days, [num(r["median_longest_shard_min"]) for r in rows], width=0.75, color=S1)
    ax.set_title("Slowest test shard per PR, median (min)", fontsize=8, color=INK, loc="left")
    ax = axes[1]
    ax.bar(days, [num(r["median_shard_runner_min"]) for r in rows], width=0.75, color=S2)
    ax.set_title("Runner-minutes in test shards per PR, median", fontsize=8, color=INK, loc="left")
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.set_xticks(days[::4])
        ax.tick_params(axis="x", labelsize=6.5)
    save(fig, "per-pr-shards.svg")


def nightly_heatmap() -> None:
    cells = read_csv("nightly_jobs.csv")
    runs = read_csv("nightly_runs.csv")
    order = [r["run_id"] for r in sorted(runs, key=lambda r: r["created_at"])]
    labels = {r["run_id"]: r["date"][5:] + ("*" if r["event"] != "schedule" else "") for r in runs}

    families = [
        ("Performance", "Performance suite (with e2e/stress until 23 Sep)"),
        ("Heavy e2e", "Heavy e2e suite"),
        ("Stress", "Stress suite"),
        ("Interpreter matrix", "Python 3.13 interpreter matrix (any shard)"),
        ("Integration + next", "Integration + next suite"),
        ("Integration marker", "Integration marker slice"),
        ("specify_cli out-of-matrix", "specify_cli out-of-matrix trees"),
        ("Architectural battery", "Architectural battery backstop"),
        ("module-tests (", "Full module matrix (any shard)"),
        ("Open-P0", "Open-P0 reproductions"),
        ("Test-universe", "Test-universe reuse check"),
    ]

    def family(name: str) -> str | None:
        for prefix, label in families:
            if name.startswith(prefix):
                return label
        return None

    status: dict[tuple[str, str], str] = {}
    rank = {"failure": 3, "timed_out": 3, "cancelled": 2, "success": 1, "skipped": 0}
    for c in cells:
        fam = family(c["job"])
        if fam is None:
            continue
        key = (fam, c["run_id"])
        prev = status.get(key)
        if prev is None or rank.get(c["conclusion"], 0) > rank.get(prev, 0):
            status[key] = c["conclusion"]
    fams = [label for _, label in families]
    fig, ax = plt.subplots(figsize=(6.6, 0.22 * len(fams) + 0.9))
    for yi, f in enumerate(fams):
        for xi, rid in enumerate(order):
            st = status.get((f, rid))
            if st is None:
                continue
            color = BAD if st in ("failure", "timed_out") else GOOD if st == "success" else SKIP
            ax.add_patch(plt.Rectangle((xi + 0.06, yi + 0.08), 0.88, 0.84, color=color, lw=0))
    ax.set_xlim(0, len(order))
    ax.set_ylim(len(fams), 0)
    ax.set_yticks([i + 0.5 for i in range(len(fams))], fams, fontsize=8)
    ax.set_xticks([i + 0.5 for i in range(len(order))], [labels[r] for r in order], rotation=90, fontsize=6)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(
        "Nightly jobs by run (red: failed or timed out, green: passed, grey: skipped or cancelled; *: manual run)", fontsize=7.5, color=INK_SOFT, loc="left"
    )
    save(fig, "nightly-heatmap.svg")


def nightly_duration() -> None:
    runs = sorted(read_csv("nightly_runs.csv"), key=lambda r: r["created_at"])
    xs = list(range(len(runs)))
    fig, ax = plt.subplots(figsize=(6.3, 1.9))
    colors = [GOOD if r["conclusion"] == "success" else BAD if r["conclusion"] == "failure" else SKIP for r in runs]
    ax.bar(xs, [num(r["duration_min"]) or 0 for r in runs], color=colors, width=0.8)
    ax.set_xticks(xs[::3], [runs[i]["date"][5:] for i in xs[::3]], fontsize=6.5)
    ax.set_ylabel("run minutes")
    ax.set_title("Nightly run duration, coloured by verdict (green passed, red failed, grey other)", fontsize=7.5, color=INK_SOFT, loc="left")
    save(fig, "nightly-duration.svg")


def timeline() -> None:
    # timeline.json carries only the editorial label; each date is looked up in
    # the collector output (a commit SHA in ci_config_commits.csv, or a PR/issue
    # merge/close date in named_issues.json), so no date is typed by hand.
    commits = {r["sha"]: r["date"] for r in read_csv("ci_config_commits.csv")}
    issues = json.loads((RAW / "named_issues.json").read_text())
    events = []
    for e in json.loads((ROOT / "tooling" / "timeline.json").read_text()):
        if "sha" in e:
            date = commits[e["sha"][:9]]
        else:
            rec = issues[str(e["issue"])]
            date = (rec.get("merged_at") or rec.get("closed_at") or rec["created_at"])[:10]
        events.append({"date": date, "label": e["label"]})
    events.sort(key=lambda e: e["date"])
    fig, ax = plt.subplots(figsize=(6.3, 0.27 * len(events) + 0.3))
    n = len(events)
    ax.vlines(0, -0.4, n - 0.6, color=BASE, lw=1.2)
    for i, e in enumerate(events):
        d = day(e["date"])
        ax.plot(0, i, "o", color=S1, ms=6, mec="white", mew=1.2)
        ax.text(-0.04, i, f"{d:%d %b}", ha="right", va="center", fontsize=7.5, color=INK_SOFT)
        ax.text(0.04, i, e["label"].replace("\n", " "), ha="left", va="center", fontsize=8, color=INK)
    ax.set_xlim(-0.5, 2.6)
    ax.set_ylim(n - 0.4, -0.6)
    ax.axis("off")
    save(fig, "ci-timeline.svg")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    per_pr_runtime()
    per_pr_runtime("summary-wall-clock.svg", (6.3, 1.7))
    per_pr_shards()
    nightly_heatmap()
    nightly_duration()
    timeline()


if __name__ == "__main__":
    main()
