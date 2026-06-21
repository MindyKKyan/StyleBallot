"""Alignment dashboard HTML — bars, palette strips, aesthetic badges."""

from __future__ import annotations

import html

DIM_LABELS = {
    "en": {
        "semantic": "Semantic",
        "aesthetic": "Aesthetic",
        "color_mood": "Color Mood",
        "title": "Alignment details",
        "anchor_palette": "Anchor palette",
        "ai_pick": "AI pick",
    },
    "zh-Hans": {
        "semantic": "语义",
        "aesthetic": "美学调性",
        "color_mood": "色调情绪",
        "title": "对齐详情",
        "anchor_palette": "锚点色板",
        "ai_pick": "AI 推荐",
    },
    "zh-Hant": {
        "semantic": "語意",
        "aesthetic": "美學調性",
        "color_mood": "色調情緒",
        "title": "對齊詳情",
        "anchor_palette": "錨點色板",
        "ai_pick": "AI 推薦",
    },
}

COLORS = {"A": "#007aff", "B": "#ff9500", "C": "#af52de", "D": "#34c759", "E": "#ff3b30"}
AESTHETIC_BADGE = {
    "up": ("↑ Fine-art", "↑ 更艺术", "↑ 更藝術"),
    "down": ("↓ Commercial", "↓ 更商业", "↓ 更商業"),
    "neutral": ("≈ Neutral", "≈ 中性", "≈ 中性"),
}


def _labels(lang: str) -> dict:
    return DIM_LABELS.get(lang, DIM_LABELS["en"])


def _pct(v: float) -> str:
    return f"{int(round(v * 100))}%"


def _bar_row(label: str, value: float, color: str, ai_badge: str = "") -> str:
    badge = f'<span class="ai-badge">{html.escape(ai_badge)}</span>' if ai_badge else ""
    return f"""
    <div class="align-bar-row">
      <div class="align-bar-head">
        <span class="align-bar-label">{html.escape(label)}{badge}</span>
        <span class="align-bar-pct">{_pct(value)}</span>
      </div>
      <div class="align-bar-track"><div class="align-bar-fill" style="width:{value*100:.1f}%;background:{color}"></div></div>
    </div>
    """


def _palette_strip(title: str, swatches: list[str]) -> str:
    chips = "".join(
        f'<span class="palette-chip" style="background:{html.escape(c)}" title="{html.escape(c)}"></span>'
        for c in (swatches or ["#888"])
    )
    return f'<div class="palette-block"><span class="palette-title">{html.escape(title)}</span><div class="palette-chips">{chips}</div></div>'


def _aesthetic_badge(direction: str, lang: str) -> str:
    idx = 0 if lang == "en" else 1 if lang == "zh-Hans" else 2
    text = AESTHETIC_BADGE.get(direction, AESTHETIC_BADGE["neutral"])[idx]
    css = direction if direction in ("up", "down", "neutral") else "neutral"
    return f'<span class="aesthetic-badge {css}">{html.escape(text)}</span>'


def build_alignment_dashboard(
    scores: list[dict],
    ai_best_idx: int,
    anchor_palette: list[str],
    lang: str = "en",
) -> str:
    """HTML dashboard: dimension bars + palette comparison + aesthetic badges."""
    if not scores:
        return '<div class="align-dashboard empty"><p>—</p></div>'

    L = _labels(lang)
    ai_label = scores[ai_best_idx].get("label", "?")

    bars_html = ""
    for dim in ("semantic", "aesthetic", "color_mood"):
        bars_html += f'<div class="dim-group"><p class="dim-group-title">{html.escape(L[dim])}</p>'
        for row in scores:
            label = row.get("label", "?")
            color = COLORS.get(label, "#007aff")
            badge = L["ai_pick"] if row.get("label") == ai_label else ""
            bars_html += _bar_row(f"Candidate {label}", row[dim], color, badge if dim == "semantic" else "")
        bars_html += "</div>"

    anchor_strip = _palette_strip(L["anchor_palette"], anchor_palette)
    candidate_strips = ""
    for row in scores:
        label = row.get("label", "?")
        swatches = row.get("palette_candidate") or []
        candidate_strips += _palette_strip(f"{label}", swatches)

    aesthetic_row = "".join(
        _aesthetic_badge(row.get("aesthetic_direction", "neutral"), lang)
        + f' <span class="aesthetic-label">{html.escape(row.get("label", "?"))}</span>'
        for row in scores
    )

    return f"""
    <section class="align-dashboard">
      <h3 class="align-dashboard-title">{html.escape(L["title"])}</h3>
      <div class="align-bars">{bars_html}</div>
      <div class="palette-row">{anchor_strip}{candidate_strips}</div>
      <div class="aesthetic-row"><span class="aesthetic-row-label">Aesthetic delta:</span>{aesthetic_row}</div>
    </section>
    """
