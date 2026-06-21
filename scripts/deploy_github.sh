#!/usr/bin/env bash
# Push StyleBallot (+ bundled aesthetic_core) to GitHub.
# Requires: GITHUB_PAT with `repo` scope, or SSH remote already configured.
#
#   export GITHUB_PAT="ghp_xxxx"
#   bash scripts/deploy_github.sh
set -euo pipefail

BALLOT="$(cd "$(dirname "$0")/.." && pwd)"
PANEL="$(cd "$BALLOT/../AestheticDissectionPanel" && pwd)"
REPO_URL="https://github.com/MindyKKyan/StyleBallot.git"
STAGE="$(mktemp -d)"

cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

echo "==> Staging StyleBallot + aesthetic_core"
rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "output" \
  --exclude "weights" \
  --exclude "aesthetic_core" \
  "$BALLOT/" "$STAGE/"

rsync -a "$PANEL/aesthetic_core/" "$STAGE/aesthetic_core/"

cd "$STAGE"
git init -b main
git add .
git -c user.name="StyleBallot" -c user.email="deploy@local" commit -m "feat: StyleBallot UX V2 — style alignment canvas"

if [[ -n "${GITHUB_PAT:-}" ]]; then
  git push -f "https://MindyKKyan:${GITHUB_PAT}@github.com/MindyKKyan/StyleBallot.git" main:main
else
  git remote add origin "$REPO_URL"
  echo "No GITHUB_PAT set — force-pushing via configured git credentials:"
  git push -f -u origin main
fi

echo "✅ GitHub: https://github.com/MindyKKyan/StyleBallot"
