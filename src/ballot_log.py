"""Optional vote log for research data collection."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import LOG_DIR

CSV_PATH = LOG_DIR / "ballot_log.csv"
CSV_FIELDS = [
    "timestamp",
    "round",
    "refined",
    "prompt",
    "user_choice",
    "ai_best",
    "agreement",
    "user_semantic",
    "user_aesthetic",
    "user_color_mood",
    "ai_semantic",
    "ai_aesthetic",
    "ai_color_mood",
    "diagnosis_source",
    "profile_json",
    "scores_json",
]


def _ensure_header() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()


def persist_vote(
    prompt: str,
    user_idx: int,
    ai_best_idx: int,
    scores: list[dict],
    diagnosis_source: str,
    round_num: int = 1,
    refined: bool = False,
    profile: dict | None = None,
) -> Path:
    _ensure_header()
    user = scores[user_idx]
    ai = scores[ai_best_idx]
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "round": round_num,
        "refined": refined,
        "prompt": prompt,
        "user_choice": user.get("label", str(user_idx)),
        "ai_best": ai.get("label", str(ai_best_idx)),
        "agreement": user_idx == ai_best_idx,
        "user_semantic": user["semantic"],
        "user_aesthetic": user["aesthetic"],
        "user_color_mood": user["color_mood"],
        "ai_semantic": ai["semantic"],
        "ai_aesthetic": ai["aesthetic"],
        "ai_color_mood": ai["color_mood"],
        "diagnosis_source": diagnosis_source,
        "profile_json": json.dumps(profile or {}, ensure_ascii=False),
        "scores_json": json.dumps(scores, ensure_ascii=False),
    }
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow(row)
    return CSV_PATH
