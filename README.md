---
title: StyleBallot
emoji: 🗳️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "5.50.0"
app_file: app.py
python_version: "3.11"
pinned: false
license: apache-2.0
startup_duration_timeout: 1h
preload_from_hub:
  - runwayml/stable-diffusion-v1-5
  - openai/clip-vit-large-patch14
  - cnmoro/mini-image-captioning
---

# StyleBallot — Style Alignment Canvas (UX V2)

**Turn fuzzy aesthetic intuition into auditable, votable dimensions.**

Upload **one** style anchor (with preview) → **trilingual detailed description** → 3 SD 1.5 variants → alignment dashboard → vote. Optionally **refine once** (keep your pick + 2 new images, **5 images max per session**).

**Live demo:** [Open app directly](https://mindykkyan-style-ballot.hf.space) · [HF Space page](https://huggingface.co/spaces/Mindykkyan/Style_Ballot)

> Logs may show `Running on http://0.0.0.0:7860` on HF — that is normal (container bind address); traffic is served at `*.hf.space`.

## UX V2 highlights

1. **Single anchor preview** — `gr.Image` upload with visible thumbnail
2. **Structured description** — Subject / Composition / Color & Mood / Aesthetic Register in **English · 简体中文 · 繁體中文** (GPT-4o mini vision when `OPENAI_API_KEY` set; template fallback otherwise)
3. **Alignment dashboard** — radar + dimension bars + palette strips + aesthetic delta badges
4. **Optional Round 2 refine** — after voting, keep your pick and generate 2 more variants; finish with a **preference profile**
5. **Cost cap** — max **5 SD images** per session (3 + 2), no endless loops

## Workflow

```
Upload anchor → Describe → Round 1 (3 candidates) → Vote
  → [Optional] Refine (+2 images) → Vote again
  → Preference profile
```

## Run locally

```bash
cd DeliberativeVisualCo-Creation
source .venv/bin/activate
pip install -r AestheticDissectionPanel/requirements.txt
pip install -r StyleBallot/requirements.txt
export PYTORCH_ENABLE_MPS_FALLBACK=1
export OPENAI_API_KEY=sk-...   # optional: rich trilingual descriptions
cd StyleBallot && python app.py
# → http://127.0.0.1:7860
```

## Deploy

### Hugging Face Space

```bash
hf auth login
cd StyleBallot
bash scripts/deploy_hf_only.sh
```

Then in [Space Settings](https://huggingface.co/spaces/Mindykkyan/Style_Ballot/settings):
- **Hardware → CPU basic** (save once so `hardware.current` is assigned — if stuck on Starting with `current: null`, pick hardware again and **Restart this Space**)
- **Hardware → ZeroGPU** when you need SD 1.5 generation (upgrade from CPU)
- **Secrets** (optional): `OPENAI_API_KEY`

Live (direct): https://mindykkyan-style-ballot.hf.space

**Build vs Starting vs Running**
- **Build logs** (`Build Queued`, `pip install torch`, `Pushing image`) = Docker image is being built. This can take **15–30+ minutes** on first deploy (torch + CUDA wheels ~2 GB). Settings may show CPU **loading** during this — wait for build to finish.
- **Runtime startup** is separate: Gradio binds `0.0.0.0:7860` in ~1 s. Models are **lazy-loaded** on first user action (caption / align / generate), not at process start — so startup is **not** blocked by SD/CLIP download.
- **`preload_from_hub`** (in this README frontmatter) bakes model weights into the image at **build** time so the first click is faster; it does not fix a stuck hub badge.

**Troubleshooting HF "Starting" badge**
- If logs show `Running on http://0.0.0.0:7860` but the hub page says Starting, open the **direct URL** above (app is usually live).
- In Settings, confirm hardware is selected and saved, then **Restart this Space** or **Factory rebuild**.
- Compare with a working Space: runtime should show `hardware.current` assigned (not `null`) and `stage: RUNNING`.
- HF **persistent storage** for Spaces is deprecated; use `preload_from_hub` or accept first-request download into ephemeral `~/.cache/huggingface`.

### GitHub

`StyleBallot/` is its own git repo (`origin` → `MindyKKyan/StyleBallot`). **Always `cd StyleBallot` first** — if you run `git` from your home folder, it may push to the wrong repo (e.g. Riverchain-Infos1).

Verify remote before pushing:

```bash
cd StyleBallot
bash scripts/verify_git_remote.sh
```

**Recommended** (bundles `aesthetic_core` for a self-contained repo):

```bash
cd StyleBallot
bash scripts/deploy_github.sh
```

Optional PAT if git credentials are not configured:

```bash
export GITHUB_PAT="ghp_xxxx"
bash scripts/deploy_github.sh
```

Repo: https://github.com/MindyKKyan/StyleBallot

### Both at once

```bash
export GITHUB_PAT="ghp_xxxx"
hf auth login
bash scripts/deploy_all.sh
```

`deploy_*` scripts bundle `AestheticDissectionPanel/aesthetic_core/` so GitHub/HF repos are self-contained.

---

© 2026 — HCI research demonstration prototype.
