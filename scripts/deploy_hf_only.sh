#!/usr/bin/env bash
# Upload StyleBallot to HF Space (bundles aesthetic_core). Requires: hf auth login
set -euo pipefail
BALLOT="$(cd "$(dirname "$0")/.." && pwd)"
PANEL="$(cd "$BALLOT/../AestheticDissectionPanel" && pwd)"
SPACE_ID="Mindykkyan/Style_Ballot"
STAGE="$(mktemp -d)"

cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "output" \
  --exclude "weights" \
  --exclude "aesthetic_core" \
  --exclude "scripts" \
  "$BALLOT/" "$STAGE/"

rsync -a "$PANEL/aesthetic_core/" "$STAGE/aesthetic_core/"

hf auth whoami || { echo "Run: hf auth login"; exit 1; }

hf upload "$SPACE_ID" "$STAGE" . \
  --repo-type space \
  --exclude ".git/**" \
  --commit-message "feat: StyleBallot style alignment canvas"

hf spaces variables add "$SPACE_ID" -e GRADIO_SSR_MODE=false 2>/dev/null || true

echo "✅ https://huggingface.co/spaces/${SPACE_ID}"
echo "   If hub shows Starting: Settings → pick Hardware → Save → Restart Space."
echo "   GRADIO_SSR_MODE=false set."
