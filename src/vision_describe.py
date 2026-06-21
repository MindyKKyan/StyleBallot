"""Structured trilingual image description — GPT-4o vision + fallback."""

from __future__ import annotations

import base64
import io
import json

from PIL import Image

from .config import OPENAI_API_KEY
from .caption import caption_image

LOCALE = {
    "en": "English",
    "zh-Hans": "Simplified Chinese",
    "zh-Hant": "Traditional Chinese",
}

SECTIONS = {
    "en": ("Subject", "Composition", "Color & Mood", "Aesthetic Register"),
    "zh-Hans": ("主体", "构图", "色调与情绪", "美学调性"),
    "zh-Hant": ("主體", "構圖", "色調與情緒", "美學調性"),
}


def _img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def _openai_vision_describe(img: Image.Image, lang: str) -> str | None:
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        locale = LOCALE.get(lang, LOCALE["en"])
        client = OpenAI(api_key=OPENAI_API_KEY)
        b64 = _img_to_b64(img)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a visual analyst. Describe the image in {locale} using exactly four labeled "
                        "sections (1-2 sentences each): Subject, Composition, Color & Mood, Aesthetic Register. "
                        "Return JSON: {\"sections\": {\"subject\": \"...\", \"composition\": \"...\", "
                        "\"color_mood\": \"...\", \"aesthetic\": \"...\"}, \"prompt\": \"single paragraph "
                        "generation prompt combining all four aspects\"}"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this style anchor image in detail."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=500,
            temperature=0.4,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        return _format_sections(data, lang)
    except Exception:
        return None


def _openai_translate(text: str, lang: str) -> str | None:
    if not OPENAI_API_KEY or lang == "en":
        return None
    try:
        from openai import OpenAI

        locale = LOCALE.get(lang, lang)
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Expand this image caption into a detailed 4-part description in {locale}. "
                        "Format: Subject: ...; Composition: ...; Color & Mood: ...; Aesthetic Register: ..."
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=400,
            temperature=0.4,
        )
        return (resp.choices[0].message.content or "").strip() or None
    except Exception:
        return None


def _format_sections(data: dict, lang: str) -> str:
    prompt = (data.get("prompt") or "").strip()
    if prompt:
        sections = data.get("sections") or {}
        if sections and lang != "en":
            labels = SECTIONS.get(lang, SECTIONS["en"])
            keys = ("subject", "composition", "color_mood", "aesthetic")
            parts = []
            for label, key in zip(labels, keys):
                val = sections.get(key, "").strip()
                if val:
                    parts.append(f"{label}：{val}" if lang.startswith("zh") else f"{label}: {val}")
            if parts:
                return "；".join(parts) if lang.startswith("zh") else "; ".join(parts)
        return prompt

    sections = data.get("sections") or {}
    labels = SECTIONS.get(lang, SECTIONS["en"])
    keys = ("subject", "composition", "color_mood", "aesthetic")
    parts = []
    for label, key in zip(labels, keys):
        val = sections.get(key, "").strip()
        if val:
            parts.append(f"{label}：{val}" if lang.startswith("zh") else f"{label}: {val}")
    return "；".join(parts) if lang.startswith("zh") else "; ".join(parts)


def _fallback_describe(img: Image.Image, lang: str) -> str:
    draft = caption_image(img)
    labels = SECTIONS.get(lang, SECTIONS["en"])

    if lang != "en":
        translated = _openai_translate(draft, lang)
        if translated:
            return translated
        notice = {
            "zh-Hans": "（基础识别为英文，设置 OPENAI_API_KEY 可获取中文详细描述）",
            "zh-Hant": "（基礎識別為英文，設定 OPENAI_API_KEY 可取得中文詳細描述）",
        }
        suffix = notice.get(lang, "")
        return (
            f"{labels[0]}: {draft}. "
            f"{labels[1]}: centered framing. "
            f"{labels[2]}: inferred from anchor palette. "
            f"{labels[3]}: style reference image. {suffix}"
        )

    return (
        f"{labels[0]}: {draft}. "
        f"{labels[1]}: balanced layout with clear focal point. "
        f"{labels[2]}: color mood derived from anchor palette. "
        f"{labels[3]}: use as stylistic reference for generation."
    )


def describe_anchor(img: Image.Image, lang: str = "en") -> tuple[str, str]:
    """Return (description_text, source_label)."""
    if img is None:
        return "", "idle"
    for fn, label in [(_openai_vision_describe, "GPT-4o mini vision")]:
        result = fn(img, lang)
        if result:
            return result, label
    return _fallback_describe(img, lang), "mini-caption + template"
