"""Alignment radar chart — anchor baseline + candidate overlays."""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

AXIS_LABELS = {
    "en": ("Semantic", "Aesthetic", "Color Mood"),
    "zh-Hans": ("语义", "美学调性", "色调情绪"),
    "zh-Hant": ("語意", "美學調性", "色調情緒"),
}

CANDIDATE_COLORS = ["#007aff", "#ff9500", "#af52de"]
ANCHOR_COLOR = "#86868b"


def _setup_font(lang: str) -> None:
    fonts = ["PingFang SC", "Arial Unicode MS", "Heiti SC", "DejaVu Sans"]
    plt.rcParams["font.sans-serif"] = fonts
    plt.rcParams["axes.unicode_minus"] = False


def build_radar_chart(scores: list[dict], lang: str = "en") -> Image.Image:
    """Render triangular radar: dashed anchor baseline + solid candidate lines."""
    _setup_font(lang)
    labels = AXIS_LABELS.get(lang, AXIS_LABELS["en"])
    keys = ("semantic", "aesthetic", "color_mood")
    n = len(keys)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    anchor_vals = [1.0] * n + [1.0]

    fig, ax = plt.subplots(figsize=(5.2, 5.2), subplot_kw={"polar": True})
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fafafa")

    ax.plot(angles, anchor_vals, color=ANCHOR_COLOR, linewidth=1.8, linestyle="--", label="Anchor")
    ax.fill(angles, anchor_vals, color=ANCHOR_COLOR, alpha=0.06)

    for idx, row in enumerate(scores):
        vals = [row[k] for k in keys] + [row[keys[0]]]
        color = CANDIDATE_COLORS[idx % len(CANDIDATE_COLORS)]
        label = row.get("label", chr(65 + idx))
        ax.plot(angles, vals, color=color, linewidth=2.2, label=f"Candidate {label}")
        ax.fill(angles, vals, color=color, alpha=0.12)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0.25", "0.50", "0.75", "1.00"], fontsize=8, color="#86868b")
    ax.grid(color="#e8e8ed", linewidth=0.8)
    ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.12), fontsize=9, frameon=False)
    ax.spines["polar"].set_color("#e8e8ed")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=144, bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")
