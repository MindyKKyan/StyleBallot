"""Preference profile summary after 1–2 voting rounds."""

from __future__ import annotations

import html

from .refine import compute_dimension_weights

DIM_NAMES = {
    "en": {"semantic": "semantic content", "aesthetic": "aesthetic register", "color_mood": "color mood"},
    "zh-Hans": {"semantic": "内容主题", "aesthetic": "美学调性", "color_mood": "色调情绪"},
    "zh-Hant": {"semantic": "內容主題", "aesthetic": "美學調性", "color_mood": "色調情緒"},
}

TITLE = {
    "en": "Your preference profile",
    "zh-Hans": "你的偏好画像",
    "zh-Hant": "你的偏好畫像",
}


def _top_dim(weights: dict[str, float]) -> str:
    return max(weights, key=weights.get)


def build_profile_text(votes: list[dict], lang: str = "en") -> str:
    """Plain-text one-paragraph preference summary."""
    if not votes:
        empty = {
            "en": "Vote on a candidate to build your preference profile.",
            "zh-Hans": "请先投票，以生成你的偏好画像。",
            "zh-Hant": "請先投票，以生成你的偏好畫像。",
        }
        return empty.get(lang, empty["en"])

    names = DIM_NAMES.get(lang, DIM_NAMES["en"])
    weights = compute_dimension_weights(votes)
    top = _top_dim(weights)
    ai_agree = sum(1 for v in votes if v.get("agreement"))
    total = len(votes)

    if lang == "zh-Hans":
        return (
            f"基于 {total} 轮投票，你最常选择的是 **{names[top]}** 维度更高的候选"
            f"（权重约 {weights[top]:.0%}）。"
            f"与 AI 一致 {ai_agree}/{total} 次。"
        )
    if lang == "zh-Hant":
        return (
            f"基於 {total} 輪投票，你最常選擇的是 **{names[top]}** 維度更高的候選"
            f"（權重約 {weights[top]:.0%}）。"
            f"與 AI 一致 {ai_agree}/{total} 次。"
        )
    return (
        f"Across {total} round(s), you most often favored candidates strong in **{names[top]}** "
        f"(~{weights[top]:.0%} weight). You agreed with the AI {ai_agree}/{total} time(s)."
    )


def build_profile_html(votes: list[dict], lang: str = "en") -> str:
    text = build_profile_text(votes, lang)
    weights = compute_dimension_weights(votes)
    bars = ""
    names = DIM_NAMES.get(lang, DIM_NAMES["en"])
    for dim in ("semantic", "aesthetic", "color_mood"):
        v = weights[dim]
        bars += f"""
        <div class="profile-bar-row">
          <span>{html.escape(names[dim])}</span>
          <div class="profile-bar-track"><div class="profile-bar-fill" style="width:{v*100:.0f}%"></div></div>
          <span>{int(v*100)}%</span>
        </div>
        """
    return f"""
    <section class="profile-card">
      <h3>{html.escape(TITLE.get(lang, TITLE["en"]))}</h3>
      <p>{html.escape(text).replace("**", "")}</p>
      <div class="profile-bars">{bars}</div>
    </section>
    """
