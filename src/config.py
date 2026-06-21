"""StyleBallot runtime configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import torch

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
PANEL_DIR = REPO_ROOT / "AestheticDissectionPanel"

# Local dev: import aesthetic_core from Panel (append so StyleBallot app.py wins).
if (BASE_DIR / "aesthetic_core").is_dir():
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
elif PANEL_DIR.is_dir() and str(PANEL_DIR) not in sys.path:
    sys.path.append(str(PANEL_DIR))

WEIGHTS_DIR = BASE_DIR / "weights"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

IS_HF_SPACE = os.environ.get("SPACE_ID") is not None or os.environ.get("SYSTEM") == "spaces"
# Back-compat alias — only means "on HF Spaces", NOT "CUDA is available".
IS_ZEROGPU = IS_HF_SPACE

CAPTION_MODEL_ID = "cnmoro/mini-image-captioning"
SD_MODEL_ID = "runwayml/stable-diffusion-v1-5"
NUM_INFERENCE_STEPS = 20
IMAGE_SIZE = 512
NUM_VARIANTS = 3
GUIDANCE_SCALE = 7.5
VARIANT_SEEDS = (42, 123, 456)

SHARE_LOCAL = os.environ.get("DV_SHARE", "0") == "1"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


def resolve_hf_token() -> str:
    for key in ("HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    try:
        from huggingface_hub import get_token

        cached = get_token()
        if cached:
            return cached
    except Exception:
        pass
    return ""


HF_TOKEN = resolve_hf_token()


def resolve_log_dir() -> Path:
    env_dir = os.environ.get("STYLE_BALLOT_LOG_DIR", "").strip()
    if env_dir:
        path = Path(env_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path
    hf_data = Path("/data/style_ballot_logs")
    try:
        hf_data.mkdir(parents=True, exist_ok=True)
        probe = hf_data / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return hf_data
    except OSError:
        pass
    fallback = BASE_DIR / "output"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


LOG_DIR = resolve_log_dir()
