"""Round-2 refine — prompt bias and dimension inference."""

from __future__ import annotations

REFINE_SEEDS = (789, 1011)

DIM_SUFFIX = {
    "semantic": "emphasis on subject and scene content, clear semantic alignment",
    "aesthetic": "fine-art aesthetic register, gallery-polished look",
    "color_mood": "emphasis on color mood and palette harmony",
}

DIM_SUFFIX_ZH = {
    "semantic": "强调主体与场景内容",
    "aesthetic": "强调高级艺术感",
    "color_mood": "强调色调与色板统一",
}


def infer_priority_dim(user_idx: int, scores: list[dict]) -> str:
    """Which dimension the user's pick scores highest on."""
    user = scores[user_idx]
    return max(("semantic", "aesthetic", "color_mood"), key=lambda k: user[k])


def infer_gap_dim(user_idx: int, ai_idx: int, scores: list[dict]) -> str:
    """Dimension where user and AI disagree most."""
    user = scores[user_idx]
    ai = scores[ai_idx]
    user_best = infer_priority_dim(user_idx, scores)
    ai_best = max(("semantic", "aesthetic", "color_mood"), key=lambda k: ai[k])
    if user_best != ai_best:
        return user_best
    gaps = {d: abs(user[d] - ai[d]) for d in ("semantic", "aesthetic", "color_mood")}
    return max(gaps, key=gaps.get)


def build_refine_prompt(base_prompt: str, user_idx: int, ai_idx: int, scores: list[dict]) -> str:
    """Append English bias suffix for SD 1.5 Round 2."""
    dim = infer_gap_dim(user_idx, ai_idx, scores)
    suffix = DIM_SUFFIX.get(dim, DIM_SUFFIX["semantic"])
    base = (base_prompt or "").strip()
    if not base:
        return suffix
    return f"{base}, {suffix}"


def compute_dimension_weights(votes: list[dict]) -> dict[str, float]:
    """Aggregate dimension emphasis from vote records."""
    totals = {"semantic": 0.0, "aesthetic": 0.0, "color_mood": 0.0}
    if not votes:
        return {k: round(1 / 3, 3) for k in totals}
    for v in votes:
        scores = v.get("scores") or []
        idx = v.get("user_idx", 0)
        if idx < len(scores):
            row = scores[idx]
            for d in totals:
                totals[d] += row.get(d, 0)
    s = sum(totals.values()) or 1.0
    return {k: round(v / s, 3) for k, v in totals.items()}
