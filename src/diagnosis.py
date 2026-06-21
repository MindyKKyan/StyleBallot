"""Human–AI preference gap diagnosis with LLM / template fallback."""

from __future__ import annotations

import json
import urllib.request

from .config import HF_TOKEN, OPENAI_API_KEY

DIM_NAMES = {
    "en": {
        "semantic": "semantic content",
        "aesthetic": "aesthetic register",
        "color_mood": "color mood",
    },
    "zh-Hans": {
        "semantic": "内容主题",
        "aesthetic": "美学调性",
        "color_mood": "色调情绪",
    },
    "zh-Hant": {
        "semantic": "內容主題",
        "aesthetic": "美學調性",
        "color_mood": "色調情緒",
    },
}

AGREE_MSG = {
    "en": "AI agrees with you — the image you picked is also the highest overall alignment match.",
    "zh-Hans": "AI 与你所见略同 — 你选中的图片也是综合对齐分数最高的一张。",
    "zh-Hant": "AI 與你所見略同 — 你選中的圖片也是綜合對齊分數最高的一張。",
}


def _dim_names(lang: str) -> dict:
    return DIM_NAMES.get(lang, DIM_NAMES["en"])


def _best_dim(scores: list[dict], key: str) -> int:
    return max(range(len(scores)), key=lambda i: scores[i][key])


def _template_diagnosis(
    user_idx: int,
    ai_idx: int,
    scores: list[dict],
    lang: str,
) -> str:
    names = _dim_names(lang)
    user = scores[user_idx]
    ai = scores[ai_idx]
    user_label = user.get("label", chr(65 + user_idx))
    ai_label = ai.get("label", chr(65 + ai_idx))

    user_best_dim = max(("semantic", "aesthetic", "color_mood"), key=lambda k: user[k])
    ai_best_dim = max(("semantic", "aesthetic", "color_mood"), key=lambda k: ai[k])

    if lang.startswith("zh"):
        parts = []
        for dim in ("semantic", "aesthetic", "color_mood"):
            if ai[dim] > user[dim] + 0.05:
                parts.append(f"图 {ai_label} 在{names[dim]}上更接近锚点（{ai[dim]:.2f} vs {user[dim]:.2f}）")
        reason = ""
        if user_best_dim != ai_best_dim:
            reason = f"你可能更看重 **{names[user_best_dim]}** 而非 **{names[ai_best_dim]}**。"
        elif user[user_best_dim] >= ai[user_best_dim]:
            reason = f"你在 **{names[user_best_dim]}** 维度上给了更高权重。"
        gap = "；".join(parts[:2]) if parts else f"图 {ai_label} 的综合对齐分更高（{ai['ai_overall']:.2f} vs {user['ai_overall']:.2f}）。"
        return f"你选择了图 {user_label} 而非图 {ai_label}。{gap}{reason}"

    parts = []
    for dim in ("semantic", "aesthetic", "color_mood"):
        if ai[dim] > user[dim] + 0.05:
            parts.append(
                f"Image {ai_label} is closer on {names[dim]} ({ai[dim]:.2f} vs {user[dim]:.2f})"
            )
    reason = ""
    if user_best_dim != ai_best_dim:
        reason = f"You may weight **{names[user_best_dim]}** over **{names[ai_best_dim]}**."
    gap = "; ".join(parts[:2]) if parts else (
        f"Image {ai_label} scores higher overall ({ai['ai_overall']:.2f} vs {user['ai_overall']:.2f})."
    )
    return f"You picked image {user_label} instead of {ai_label}. {gap} {reason}".strip()


def _openai_diagnosis(
    user_idx: int,
    ai_idx: int,
    scores: list[dict],
    lang: str,
) -> str | None:
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        locale = "Traditional Chinese" if lang == "zh-Hant" else "Simplified Chinese" if lang == "zh-Hans" else "English"
        payload = {
            "user_choice": scores[user_idx],
            "ai_choice": scores[ai_idx],
            "all_scores": scores,
        }
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Write ONE concise sentence in {locale} explaining why a user picked a different "
                        "candidate than the AI's top alignment pick. Mention which dimension (semantic, "
                        "aesthetic register, color mood) the user likely prioritized. No bullet points."
                    ),
                },
                {"role": "user", "content": json.dumps(payload)},
            ],
            max_tokens=180,
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or None
    except Exception:
        return None


def _hf_diagnosis(
    user_idx: int,
    ai_idx: int,
    scores: list[dict],
    lang: str,
) -> str | None:
    if not HF_TOKEN:
        return None
    try:
        user = scores[user_idx]
        ai = scores[ai_idx]
        prompt = (
            f"User picked candidate {user.get('label')} over AI pick {ai.get('label')}. "
            f"Scores: {json.dumps(scores)}. "
            "One sentence explaining the preference gap in Chinese or English:"
        )
        body = json.dumps({"inputs": prompt, "parameters": {"max_new_tokens": 120}}).encode()
        req = urllib.request.Request(
            "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
            data=body,
            headers={"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.loads(resp.read().decode())
        text = out[0]["generated_text"] if isinstance(out, list) else out.get("generated_text", "")
        line = text.strip().split("\n")[0][:400]
        return line or None
    except Exception:
        return None


def diagnose_vote(
    user_idx: int | None,
    ai_best_idx: int,
    scores: list[dict],
    lang: str = "en",
) -> tuple[str, str]:
    """Return (message, source_label)."""
    if user_idx is None:
        empty = {
            "en": "Select the candidate that best matches the anchor style.",
            "zh-Hans": "请选择最像锚点风格的一张候选图。",
            "zh-Hant": "請選擇最像錨點風格的一張候選圖。",
        }
        return empty.get(lang, empty["en"]), "idle"

    if user_idx == ai_best_idx:
        return AGREE_MSG.get(lang, AGREE_MSG["en"]), "agreement"

    for fn, label in [
        (_openai_diagnosis, "GPT-4o mini"),
        (_hf_diagnosis, "HF Inference"),
    ]:
        result = fn(user_idx, ai_best_idx, scores, lang)
        if result:
            return result, label

    return _template_diagnosis(user_idx, ai_best_idx, scores, lang), "rule-based template"
