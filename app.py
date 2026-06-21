"""
StyleBallot UX V2 — single anchor, trilingual describe, alignment dashboard, optional refine round.
"""

from __future__ import annotations

import src  # noqa: F401

import html
import json
from pathlib import Path

import gradio as gr
from PIL import Image

from src.align_viz import build_alignment_dashboard
from src.ballot_log import CSV_PATH, persist_vote
from src.config import BASE_DIR, DEVICE, LOG_DIR, SHARE_LOCAL
from src.diagnosis import diagnose_vote
from src.generate import generate_pair, generate_variants
from src.metrics import score_candidates
from src.preference_profile import build_profile_html
from src.radar import build_radar_chart
from src.refine import build_refine_prompt, compute_dimension_weights
from src.vision_describe import describe_anchor

CSS_PATH = Path(__file__).parent / "css" / "custom.css"
CUSTOM_CSS = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""

LANGS = {
    "en": {
        "eyebrow": "HCI · Style Alignment · Preference Gap",
        "title": "StyleBallot",
        "subtitle": "Upload one style anchor → detailed description → 3 variants → vote. Optionally refine once (max 5 images).",
        "language_label": "Language / 语言",
        "guide_title": "Two steps",
        "guide_body": "Upload a style reference. We describe it in your language, generate candidates, and show where you and the AI disagree.",
        "guide_steps": [
            "Round 1: pick the closest of 3 variants (max 3 SD images).",
            "Round 2 (optional): keep your pick + 2 new variants (2 more images, 5 total max).",
        ],
        "anchor_label": "Style anchor",
        "anchor_hint": "Drop or click · one image · PNG / JPG",
        "prompt_label": "Description (auto-filled, editable)",
        "prompt_placeholder": "Upload an anchor for a detailed description…",
        "describe_source": "Description source",
        "generate_btn": "Generate & Align",
        "candidates_label": "Candidates",
        "radar_label": "Alignment radar",
        "vote_label": "Which best matches the anchor style?",
        "diagnosis_idle": "Select a candidate to compare with the AI pick.",
        "refine_btn": "Refine from your pick (+2 images)",
        "finish_btn": "Finish — view preference profile",
        "refine_used_note": "Refine used · session cap: 5 images",
        "cost_note": "Session limit: 5 generated images · Round 2 optional once",
        "json_label": "Raw metrics (JSON)",
        "json_waiting": '{\n  "status": "waiting"\n}',
        "no_anchor": "Upload a style anchor image.",
        "pipeline_failed": "Pipeline failed",
        "step_upload": "Upload",
        "step_round1": "Round 1",
        "step_vote": "Vote",
        "step_round2": "Refine",
        "step_profile": "Profile",
        "locked_pick": "Your pick (locked)",
        "round1_choices": ["A", "B", "C"],
        "round2_choices": ["Keep pick", "D", "E"],
    },
    "zh-Hans": {
        "eyebrow": "HCI · 风格对齐 · 偏好分歧",
        "title": "StyleBallot",
        "subtitle": "上传一张风格锚点 → 详细描述 → 3 张候选 → 投票。可选 refine 一轮（最多 5 张图）。",
        "language_label": "语言 / Language",
        "guide_title": "两步流程",
        "guide_body": "上传风格参考图。系统用你的语言描述画面、生成候选，并展示你与 AI 的分歧。",
        "guide_steps": [
            "第 1 轮：从 3 张候选中选出最像锚点的一张（最多 3 张 SD 图）。",
            "第 2 轮（可选）：保留你的选择 + 再生成 2 张（+2 张，全程最多 5 张）。",
        ],
        "anchor_label": "风格锚点",
        "anchor_hint": "拖拽或点击 · 单张图片 · PNG / JPG",
        "prompt_label": "描述（自动生成，可编辑）",
        "prompt_placeholder": "上传锚点后自动生成详细描述…",
        "describe_source": "描述来源",
        "generate_btn": "生成与对齐",
        "candidates_label": "候选图",
        "radar_label": "对齐雷达图",
        "vote_label": "哪一张最像锚点风格？",
        "diagnosis_idle": "请选择一张候选，与 AI 推荐对比。",
        "refine_btn": "以此为基础 refine（+2 张）",
        "finish_btn": "完成 — 查看偏好画像",
        "refine_used_note": "已 refine · 本轮上限 5 张图",
        "cost_note": "单次会话最多生成 5 张 · 第 2 轮可选 1 次",
        "json_label": "原始指标（JSON）",
        "json_waiting": '{\n  "status": "等待"\n}',
        "no_anchor": "请上传一张风格锚点图。",
        "pipeline_failed": "流程失败",
        "step_upload": "上传",
        "step_round1": "第 1 轮",
        "step_vote": "投票",
        "step_round2": "Refine",
        "step_profile": "画像",
        "locked_pick": "你的选择（锁定）",
        "round1_choices": ["A", "B", "C"],
        "round2_choices": ["保留选择", "D", "E"],
    },
    "zh-Hant": {
        "eyebrow": "HCI · 風格對齊 · 偏好分歧",
        "title": "StyleBallot",
        "subtitle": "上傳一張風格錨點 → 詳細描述 → 3 張候選 → 投票。可選 refine 一輪（最多 5 張圖）。",
        "language_label": "語言 / Language",
        "guide_title": "兩步流程",
        "guide_body": "上傳風格參考圖。系統用你的語言描述畫面、生成候選，並展示你與 AI 的分歧。",
        "guide_steps": [
            "第 1 輪：從 3 張候選中選出最像錨點的一張（最多 3 張 SD 圖）。",
            "第 2 輪（可選）：保留你的選擇 + 再生成 2 張（+2 張，全程最多 5 張）。",
        ],
        "anchor_label": "風格錨點",
        "anchor_hint": "拖曳或點擊 · 單張圖片 · PNG / JPG",
        "prompt_label": "描述（自動生成，可編輯）",
        "prompt_placeholder": "上傳錨點後自動生成詳細描述…",
        "describe_source": "描述來源",
        "generate_btn": "生成與對齊",
        "candidates_label": "候選圖",
        "radar_label": "對齊雷達圖",
        "vote_label": "哪一張最像錨點風格？",
        "diagnosis_idle": "請選擇一張候選，與 AI 推薦對比。",
        "refine_btn": "以此為基礎 refine（+2 張）",
        "finish_btn": "完成 — 查看偏好畫像",
        "refine_used_note": "已 refine · 本輪上限 5 張圖",
        "cost_note": "單次會話最多生成 5 張 · 第 2 輪可選 1 次",
        "json_label": "原始指標（JSON）",
        "json_waiting": '{\n  "status": "等待"\n}',
        "no_anchor": "請上傳一張風格錨點圖。",
        "pipeline_failed": "流程失敗",
        "step_upload": "上傳",
        "step_round1": "第 1 輪",
        "step_vote": "投票",
        "step_round2": "Refine",
        "step_profile": "畫像",
        "locked_pick": "你的選擇（鎖定）",
        "round1_choices": ["A", "B", "C"],
        "round2_choices": ["保留選擇", "D", "E"],
    },
}


def _copy(lang: str) -> dict:
    return LANGS.get(lang, LANGS["en"])


def _header_html(lang: str) -> str:
    c = _copy(lang)
    return f"""
    <header class="app-header">
      <p class="eyebrow">{html.escape(c["eyebrow"])}</p>
      <h1>{html.escape(c["title"])}</h1>
      <p class="subtitle">{html.escape(c["subtitle"])}</p>
    </header>
    """


def _guide_html(lang: str) -> str:
    c = _copy(lang)
    steps = "".join(f"<li>{html.escape(s)}</li>" for s in c["guide_steps"])
    return f"""
    <section class="intro-card">
      <div class="intro-head"><h2>{html.escape(c["guide_title"])}</h2></div>
      <p class="intro-body">{html.escape(c["guide_body"])}</p>
      <ul class="intro-list">{steps}</ul>
      <p class="cost-note">{html.escape(c["cost_note"])}</p>
    </section>
    """


def _steps_html(lang: str, active: str) -> str:
    c = _copy(lang)
    keys = ["upload", "round1", "vote", "round2", "profile"]
    labels = [c[f"step_{k}"] for k in keys]
    parts = []
    for key, label in zip(keys, labels):
        cls = "workflow-step active" if key == active else "workflow-step"
        parts.append(f'<span class="{cls}">{html.escape(label)}</span>')
    return f'<nav class="workflow-steps" aria-label="Progress">{" ".join(parts)}</nav>'


def _hint_html(lang: str) -> str:
    return f'<p class="upload-hint">{html.escape(_copy(lang)["anchor_hint"])}</p>'


def _diagnosis_html(message: str, source: str, lang: str) -> str:
    idle = _copy(lang)["diagnosis_idle"]
    if not message or message == idle:
        return f'<div class="diagnosis-box"><p>{html.escape(idle)}</p></div>'
    css = "agree" if source == "agreement" else "gap" if source not in ("idle", "error", "") else ""
    src = f'<p class="diagnosis-source">{html.escape(source)}</p>' if source not in ("idle", "agreement", "error", "") else ""
    return f'<div class="diagnosis-box {css}"><p>{html.escape(message)}</p>{src}</div>'


def _json_html(payload: str) -> str:
    return f'<pre class="json-raw">{html.escape(payload)}</pre>'


def _gallery_items(images: list[Image.Image], labels: list[str], locked_idx: int | None = None) -> list[tuple]:
    out = []
    for i, (img, lab) in enumerate(zip(images, labels)):
        suffix = " ★ locked" if locked_idx is not None and i == locked_idx else ""
        out.append((img, f"{lab}{suffix}"))
    return out


def _empty_session() -> dict:
    return {
        "round": 0,
        "prompt": "",
        "candidates": [],
        "candidate_labels": [],
        "scores": [],
        "ai_best_idx": 0,
        "anchor_palette": [],
        "votes": [],
        "winner_idx": None,
        "winner_image": None,
        "winner_label": "",
        "refine_used": False,
        "images_generated": 0,
        "round1_user_idx": None,
        "round1_ai_idx": None,
    }


def on_anchor_change(anchor_img, lang):
    if anchor_img is None:
        return "", _hint_html(lang), ""
    try:
        text, source = describe_anchor(anchor_img, lang)
    except Exception as exc:
        return "", f'<p class="status-msg error">{html.escape(str(exc))}</p>', ""
    return text, _hint_html(lang), source


def on_lang_change(anchor_img, lang):
    c = _copy(lang)
    chrome = (
        _header_html(lang),
        _guide_html(lang),
        gr.update(label=c["language_label"]),
        gr.update(label=c["anchor_label"]),
        _hint_html(lang),
        gr.update(label=c["prompt_label"], placeholder=c["prompt_placeholder"]),
        gr.update(value=c["generate_btn"]),
        gr.update(label=c["candidates_label"]),
        gr.update(label=c["radar_label"]),
        gr.update(label=c["vote_label"]),
        gr.update(value=c["refine_btn"]),
        gr.update(value=c["finish_btn"]),
        _diagnosis_html(c["diagnosis_idle"], "idle", lang),
        gr.update(label=c["json_label"]),
        _steps_html(lang, "upload"),
    )
    if anchor_img is not None:
        text, source = describe_anchor(anchor_img, lang)
        return (
            *chrome[:5],
            gr.update(label=c["prompt_label"], placeholder=c["prompt_placeholder"], value=text),
            *chrome[6:],
            source,
        )
    return (
        *chrome[:5],
        gr.update(label=c["prompt_label"], placeholder=c["prompt_placeholder"]),
        *chrome[6:],
        "",
    )


def _build_results(anchor, metrics: dict, candidates: list[Image.Image], labels: list[str], lang: str):
    radar = build_radar_chart(metrics["scores"], lang)
    dashboard = build_alignment_dashboard(
        metrics["scores"],
        metrics["ai_best_idx"],
        metrics.get("anchor_palette", []),
        lang,
    )
    gallery = _gallery_items(candidates, labels)
    return radar, dashboard, gallery


def run_round1(anchor_img, prompt, lang, progress=gr.Progress()):
    c = _copy(lang)
    if anchor_img is None:
        raise gr.Error(c["no_anchor"])
    anchor = anchor_img.convert("RGB")
    prompt = (prompt or "").strip()
    if not prompt:
        prompt, _ = describe_anchor(anchor, lang)

    progress(0.1, desc="Generating 3 variants…")
    try:
        candidates, seeds = generate_variants(prompt)
        progress(0.75, desc="Scoring alignment…")
        metrics = score_candidates(anchor, candidates, c["round1_choices"])
        radar, dashboard, gallery = _build_results(anchor, metrics, candidates, c["round1_choices"], lang)
        session = _empty_session()
        session.update({
            "round": 1,
            "prompt": prompt,
            "candidates": candidates,
            "candidate_labels": c["round1_choices"],
            "scores": metrics["scores"],
            "ai_best_idx": metrics["ai_best_idx"],
            "anchor_palette": metrics.get("anchor_palette", []),
            "images_generated": 3,
        })
        detail = {"round": 1, "prompt": prompt, "seeds": seeds, "metrics": metrics}
        return (
            _steps_html(lang, "vote"),
            gallery,
            radar,
            dashboard,
            gr.update(choices=c["round1_choices"], value=None, visible=True),
            _diagnosis_html(c["diagnosis_idle"], "idle", lang),
            _json_html(json.dumps(detail, indent=2, ensure_ascii=False)),
            session,
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            prompt,
        )
    except Exception as exc:
        raise gr.Error(f'{c["pipeline_failed"]}: {exc}') from exc


def on_vote(choice, session, lang):
    c = _copy(lang)
    if not session or not choice or session.get("round", 0) < 1:
        return (
            _diagnosis_html(c["diagnosis_idle"], "idle", lang),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            session,
        )

    labels = session.get("candidate_labels") or []
    if session["round"] == 1:
        label_to_idx = {lab: i for i, lab in enumerate(labels)}
        user_idx = label_to_idx.get(choice)
    else:
        choices = c["round2_choices"]
        idx_map = {choices[i]: i for i in range(min(3, len(choices)))}
        user_idx = idx_map.get(choice)

    if user_idx is None:
        return (
            _diagnosis_html(c["diagnosis_idle"], "idle", lang),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            session,
        )

    scores = session["scores"]
    ai_idx = session["ai_best_idx"]
    message, source = diagnose_vote(user_idx, ai_idx, scores, lang)

    vote_record = {
        "round": session["round"],
        "user_idx": user_idx,
        "user_label": scores[user_idx].get("label"),
        "ai_idx": ai_idx,
        "agreement": user_idx == ai_idx,
        "scores": scores,
        "source": source,
    }
    votes = list(session.get("votes") or [])
    votes = [v for v in votes if v.get("round") != session["round"]]
    votes.append(vote_record)
    session = dict(session)
    session["votes"] = votes

    if session["round"] == 1:
        session["round1_user_idx"] = user_idx
        session["round1_ai_idx"] = ai_idx
        session["winner_idx"] = user_idx
        session["winner_label"] = scores[user_idx].get("label", "?")
        session["winner_image"] = session["candidates"][user_idx]
        try:
            persist_vote(session["prompt"], user_idx, ai_idx, scores, source, round_num=1)
        except Exception:
            pass
        show_refine = not session.get("refine_used")
        return (
            _diagnosis_html(message, source, lang),
            gr.update(visible=show_refine),
            gr.update(visible=True),
            "",
            session,
        )

    profile_html = build_profile_html(votes, lang)
    weights = compute_dimension_weights(votes)
    try:
        persist_vote(
            session["prompt"],
            user_idx,
            ai_idx,
            scores,
            source,
            round_num=2,
            refined=True,
            profile={"weights": weights, "votes": len(votes)},
        )
    except Exception:
        pass
    return (
        _diagnosis_html(message, source, lang),
        gr.update(visible=False),
        gr.update(visible=False),
        profile_html,
        session,
    )


def run_refine(session, lang, progress=gr.Progress()):
    c = _copy(lang)
    if not session or session.get("refine_used") or session.get("winner_image") is None:
        raise gr.Error("Refine not available.")
    anchor_needed = session.get("winner_image")
    user_idx = session.get("round1_user_idx", 0)
    ai_idx = session.get("round1_ai_idx", 0)
    base_prompt = session.get("prompt", "")
    refine_prompt = build_refine_prompt(base_prompt, user_idx, ai_idx, session["scores"])

    progress(0.2, desc="Generating 2 refine variants…")
    new_imgs, seeds = generate_pair(refine_prompt)

    winner = session["winner_image"]
    winner_label = session.get("winner_label", "Pick")
    all_candidates = [winner, new_imgs[0], new_imgs[1]]
    all_labels = [winner_label, "D", "E"]

    anchor = winner  # score new vs winner context — use original anchor from round1 if stored
    # Re-score: use first candidate's anchor from metrics — we need original anchor image
    # Store anchor in session during round1
    anchor_img = session.get("anchor_image")
    if anchor_img is None:
        anchor_img = winner

    metrics_new = score_candidates(anchor_img, [new_imgs[0], new_imgs[1]], ["D", "E"])
    winner_score = session["scores"][session["winner_idx"]]
    combined_scores = [winner_score, metrics_new["scores"][0], metrics_new["scores"][1]]
    ai_best_idx = max(range(3), key=lambda i: combined_scores[i]["ai_overall"])

    session = dict(session)
    session.update({
        "round": 2,
        "refine_used": True,
        "prompt": refine_prompt,
        "candidates": all_candidates,
        "candidate_labels": all_labels,
        "scores": combined_scores,
        "ai_best_idx": ai_best_idx,
        "images_generated": session.get("images_generated", 3) + 2,
    })

    radar = build_radar_chart(combined_scores, lang)
    dashboard = build_alignment_dashboard(
        combined_scores,
        ai_best_idx,
        session.get("anchor_palette", []),
        lang,
    )
    gallery = _gallery_items(all_candidates, all_labels, locked_idx=0)
    detail = {"round": 2, "prompt": refine_prompt, "seeds": seeds, "scores": combined_scores}

    return (
        _steps_html(lang, "round2"),
        gallery,
        radar,
        dashboard,
        gr.update(choices=c["round2_choices"], value=None, visible=True),
        _diagnosis_html(c["diagnosis_idle"], "idle", lang),
        _json_html(json.dumps(detail, indent=2, ensure_ascii=False)),
        session,
        gr.update(visible=False),
        "",
    )


def on_finish(session, lang):
    votes = (session or {}).get("votes") or []
    if not votes and session and session.get("round1_user_idx") is not None:
        votes = [{
            "round": 1,
            "user_idx": session["round1_user_idx"],
            "agreement": session["round1_user_idx"] == session.get("round1_ai_idx"),
            "scores": session.get("scores", []),
        }]
    profile = build_profile_html(votes, lang)
    return _steps_html(lang, "profile"), profile


def run_round1_store_anchor(anchor_img, prompt, lang, progress=gr.Progress()):
    results = run_round1(anchor_img, prompt, lang, progress)
    session = results[7]
    if anchor_img is not None and session:
        session = dict(session)
        session["anchor_image"] = anchor_img.convert("RGB")
    return results[:7] + (session,) + results[8:]


with gr.Blocks(
    title="StyleBallot",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="gray", neutral_hue="gray"),
    css=CUSTOM_CSS,
) as demo:
    default_lang = "en"
    session_state = gr.State(_empty_session())

    with gr.Column(elem_classes=["page-top"]):
        lang_in = gr.Dropdown(
            choices=[("English", "en"), ("中文简体", "zh-Hans"), ("中文繁體", "zh-Hant")],
            value=default_lang,
            label=_copy(default_lang)["language_label"],
            elem_classes=["lang-select"],
            container=False,
        )
        header_out = gr.HTML(_header_html(default_lang))

    guide_out = gr.HTML(_guide_html(default_lang))
    steps_out = gr.HTML(_steps_html(default_lang, "upload"))

    with gr.Row(elem_classes=["main-row"]):
        with gr.Column(scale=4, elem_classes=["left-col"]):
            anchor_in = gr.Image(
                type="pil",
                label=_copy(default_lang)["anchor_label"],
                height=360,
                sources=["upload"],
            )
            hint_out = gr.HTML(_hint_html(default_lang))
            prompt_in = gr.Textbox(
                label=_copy(default_lang)["prompt_label"],
                placeholder=_copy(default_lang)["prompt_placeholder"],
                lines=5,
            )
            describe_src = gr.Textbox(
                label=_copy(default_lang)["describe_source"],
                interactive=False,
                visible=True,
            )
            generate_btn = gr.Button(
                _copy(default_lang)["generate_btn"],
                variant="primary",
                elem_classes=["primary-btn"],
            )

        with gr.Column(scale=7, elem_classes=["right-col"]):
            candidates_out = gr.Gallery(
                label=_copy(default_lang)["candidates_label"],
                columns=3,
                height=300,
                object_fit="contain",
            )
            with gr.Row():
                radar_out = gr.Image(
                    label=_copy(default_lang)["radar_label"],
                    type="pil",
                    interactive=False,
                    scale=1,
                )
            dashboard_out = gr.HTML("")
            vote_in = gr.Radio(
                choices=_copy(default_lang)["round1_choices"],
                label=_copy(default_lang)["vote_label"],
                value=None,
                visible=False,
            )
            diagnosis_out = gr.HTML(_diagnosis_html(_copy(default_lang)["diagnosis_idle"], "idle", default_lang))
            with gr.Row():
                refine_btn = gr.Button(_copy(default_lang)["refine_btn"], visible=False)
                finish_btn = gr.Button(_copy(default_lang)["finish_btn"], visible=False)
            profile_out = gr.HTML("")

    with gr.Accordion(_copy(default_lang)["json_label"], open=False) as json_acc:
        json_out = gr.HTML(_json_html(_copy(default_lang)["json_waiting"]))
        csv_dl = gr.File(
            label="Download ballot CSV",
            value=str(CSV_PATH) if CSV_PATH.exists() else None,
            interactive=False,
        )

    lang_outputs = [
        header_out, guide_out, lang_in, anchor_in, hint_out, prompt_in, generate_btn,
        candidates_out, radar_out, vote_in, refine_btn, finish_btn, diagnosis_out, json_acc,
        steps_out, describe_src,
    ]

    lang_in.change(
        on_lang_change,
        inputs=[anchor_in, lang_in],
        outputs=lang_outputs,
    )

    anchor_in.change(
        on_anchor_change,
        inputs=[anchor_in, lang_in],
        outputs=[prompt_in, hint_out, describe_src],
    )

    gen_outputs = [
        steps_out, candidates_out, radar_out, dashboard_out, vote_in,
        diagnosis_out, json_out, session_state, refine_btn, profile_out, describe_src, prompt_in,
    ]

    generate_btn.click(
        run_round1_store_anchor,
        inputs=[anchor_in, prompt_in, lang_in],
        outputs=gen_outputs,
    )

    vote_outputs = [diagnosis_out, refine_btn, finish_btn, profile_out, session_state]

    vote_in.change(
        on_vote,
        inputs=[vote_in, session_state, lang_in],
        outputs=vote_outputs,
    )

    refine_outputs = [
        steps_out, candidates_out, radar_out, dashboard_out, vote_in,
        diagnosis_out, json_out, session_state, refine_btn, profile_out,
    ]

    refine_btn.click(
        run_refine,
        inputs=[session_state, lang_in],
        outputs=refine_outputs,
    )

    finish_btn.click(
        on_finish,
        inputs=[session_state, lang_in],
        outputs=[steps_out, profile_out],
    )

    demo.queue(default_concurrency_limit=1)


def _gradio_allowed_paths() -> list[str]:
    return sorted({str(BASE_DIR), str(LOG_DIR), "/data/style_ballot_logs", "/data"})


if __name__ == "__main__":
    print(f"\n🗳️  StyleBallot · device = {DEVICE}\n")
    demo.launch(share=SHARE_LOCAL, allowed_paths=_gradio_allowed_paths())
