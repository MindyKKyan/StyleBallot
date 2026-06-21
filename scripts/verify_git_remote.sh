#!/usr/bin/env bash
# Fail fast if StyleBallot is not using the StyleBallot GitHub remote.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "❌ No .git in $ROOT — run from StyleBallot/ after git init, or use deploy_github.sh"
  exit 1
fi

TOP="$(git rev-parse --show-toplevel)"
if [[ "$TOP" != "$ROOT" ]]; then
  echo "❌ Git root is $TOP (expected $ROOT)"
  echo "   cd StyleBallot before git push, or use: bash scripts/deploy_github.sh"
  exit 1
fi

URL="$(git remote get-url origin 2>/dev/null || true)"
if [[ "$URL" != *"MindyKKyan/StyleBallot"* ]]; then
  echo "❌ origin points to: ${URL:-<unset>}"
  echo "   Expected MindyKKyan/StyleBallot — fix with:"
  echo "   git remote set-url origin https://github.com/MindyKKyan/StyleBallot.git"
  exit 1
fi

echo "✅ Git OK: $TOP → $URL"
