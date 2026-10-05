#!/usr/bin/env bash
# Render README.md to the branded PDF with the canonical internal generator
# (packs/internal/assets/spec-kitty-branded-pdf.py). Needs pandoc and a Python
# with WeasyPrint (PYTHON=...), and the spec-kitty-design repo for fonts and logo
# (DESIGN_REPO=...). Run from this report folder.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
DESIGN_REPO="${DESIGN_REPO:-$REPO_ROOT/../spec-kitty-design}"
# Strip the YAML front matter: the generator reads GitHub-flavoured Markdown.
awk 'BEGIN{f=0} NR==1&&/^---$/{f=1;next} f&&/^---$/{f=0;next} !f' README.md > .pdf-source.md
trap 'rm -f .pdf-source.md' EXIT
"$PYTHON" "$REPO_ROOT/packs/internal/assets/spec-kitty-branded-pdf.py" \
  --input .pdf-source.md \
  --output ci-debrief-2026-10-05.pdf \
  --title "WTF happened<br>with the CI" \
  --subtitle "Shard-timing capture and how CI runtime changed, September to October 2026" \
  --lede "Per-PR CI is twice as fast as it was a week ago. The nightly has been red since 15 September, and the last release candidate shipped under a waiver. What happened, what is fixed, and what is still open." \
  --eyebrow "Spec Kitty · Executive debrief" \
  --footer-center "CI DEBRIEF · 2026-10-05" \
  --meta "AS OF=2026-10-05" \
  --meta "SCOPE=spec-kitty/spec-kitty" \
  --meta "FOR=QA lead · CEO · CTO" \
  --design-repo "$DESIGN_REPO"
