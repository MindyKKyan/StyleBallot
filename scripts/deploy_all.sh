#!/usr/bin/env bash
# Deploy StyleBallot to GitHub + Hugging Face Space.
#   export GITHUB_PAT="ghp_xxxx"   # optional if git credentials work
#   hf auth login                  # required for HF
#   bash scripts/deploy_all.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$DIR/deploy_github.sh"
bash "$DIR/deploy_hf_only.sh"
