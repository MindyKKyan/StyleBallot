"""Style alignment scores for radar chart and AI ranking."""

from __future__ import annotations

import src  # noqa: F401 — bootstrap aesthetic_core path

from PIL import Image

from aesthetic_core.alignment import (
    anchor_embedding,
    clip_cosine_sim,
    delta_aesthetic,
    palette_distance,
)

WEIGHTS = {"semantic": 0.4, "aesthetic": 0.3, "color_mood": 0.3}


def aesthetic_closeness(anchor: Image.Image, img: Image.Image) -> float:
    delta = delta_aesthetic(anchor, img)["delta"]
    return round(max(0.0, 1.0 - min(abs(delta) / 3.0, 1.0)), 4)


def score_candidate(
    anchor_emb,
    primary_anchor: Image.Image,
    candidate: Image.Image,
    label: str,
    anchor_palette: list[str] | None = None,
) -> dict:
    semantic = clip_cosine_sim(anchor_emb, candidate)
    aesthetic = aesthetic_closeness(primary_anchor, candidate)
    palette_info = palette_distance(primary_anchor, candidate)
    color_mood = palette_info["closeness"]
    aesthetic_detail = delta_aesthetic(primary_anchor, candidate)
    ai_overall = round(
        WEIGHTS["semantic"] * semantic
        + WEIGHTS["aesthetic"] * aesthetic
        + WEIGHTS["color_mood"] * color_mood,
        4,
    )
    return {
        "label": label,
        "semantic": semantic,
        "aesthetic": aesthetic,
        "color_mood": color_mood,
        "ai_overall": ai_overall,
        "aesthetic_delta": aesthetic_detail["delta"],
        "aesthetic_direction": aesthetic_detail["direction"],
        "aesthetic_hint": aesthetic_detail["hint"],
        "palette_mood": palette_info.get("mood", ""),
        "palette_anchor": anchor_palette or palette_info.get("anchor_palette", []),
        "palette_candidate": palette_info.get("generated_palette", []),
    }


def score_candidates(
    anchor: Image.Image,
    candidates: list[Image.Image],
    labels: list[str] | None = None,
) -> dict:
    """Score candidates vs single anchor."""
    primary = anchor.convert("RGB")
    emb = anchor_embedding([primary])
    anchor_palette = palette_distance(primary, primary)["anchor_palette"]
    lbls = labels or [chr(65 + i) for i in range(len(candidates))]
    scores = [
        score_candidate(emb, primary, c.convert("RGB"), lbls[i], anchor_palette)
        for i, c in enumerate(candidates)
    ]
    ai_best_idx = max(range(len(scores)), key=lambda i: scores[i]["ai_overall"])
    return {
        "scores": scores,
        "ai_best_idx": ai_best_idx,
        "ai_best_label": lbls[ai_best_idx],
        "weights": WEIGHTS,
        "anchor_palette": anchor_palette,
    }


def score_triplet(anchors: list[Image.Image], candidates: list[Image.Image]) -> dict:
    """Legacy wrapper — uses first anchor only."""
    if not anchors:
        raise ValueError("At least one anchor image is required.")
    return score_candidates(anchors[0], candidates, ["A", "B", "C"][: len(candidates)])
