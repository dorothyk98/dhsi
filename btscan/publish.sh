#!/bin/bash
# Scan, export, and publish to GitHub Pages every N minutes (default 15).
# Usage: ./publish.sh [minutes]   — Ctrl+C to stop.
cd "$(dirname "$0")"
INTERVAL_MIN="${1:-15}"
while true; do
  python3 app.py --export || echo "scan failed; retrying next cycle"
  if ! git diff --quiet -- scan.json; then
    git commit -m "data: auto-publish scan" -- scan.json
  fi
  # Push even when nothing was just committed, so an earlier failed push retries.
  git push || echo "push failed; retrying next cycle"
  echo "Next publish in ${INTERVAL_MIN} min - Ctrl+C to stop."
  sleep $((INTERVAL_MIN * 60))
done
