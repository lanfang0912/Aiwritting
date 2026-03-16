"""
內容生產管線 — 步驟 3-6

步驟 3：改寫（風格、字數、格式）
步驟 4：分析 → 潤飾改寫（兩次對話）
步驟 5：希塔療癒視角分析 → 融入信念／下載／顯化元素（兩次對話）
步驟 6：加入來源標註
"""
import anthropic

from config import (
    ANTHROPIC_API_KEY,
    USER_IDENTITY,
    CTA_LEAD_MAGNET,
    STEP3_REWRITE_PROMPT,
    STEP4_ANALYSIS_PROMPT,
    STEP4_REWRITE_PROMPT,
    STEP5_THETA_ANALYSIS_PROMPT,
    STEP5_THETA_REWRITE_PROMPT,
    STEP6_SOURCE_PROMPT,
    build_cta_instruction,
)

MODEL = "claude-haiku-4-5"


def _call(messages: list[dict], label: str = "") -> str:
    """單次 Claude API 串流呼叫，回傳純文字結果。"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    if label:
        print(f"  ▷ {label}...")
    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        messages=messages,
    ) as stream:
        final = stream.get_final_message()
    for block in final.content:
        if block.type == "text":
            return block.text.strip()
    return ""


def _two_turn(
    article: str,
    first_prompt: str,
    second_prompt: str,
    label_first: str = "",
    label_second: str = "",
) -> str:
    """兩輪對話：分析 → 改寫。"""
    messages: list[dict] = [
        {"role": "user", "content": f"{first_prompt}\n\n{article}"}
    ]
    analysis = _call(messages, label=label_first)

    messages.append({"role": "assistant", "content": analysis})
    messages.append({"role": "user", "content": second_prompt})
    result = _call(messages, label=label_second)
    return result


def step3_rewrite(initial_draft: str) -> str:
    """步驟 3：改寫初稿為正式臉書貼文格式。"""
    prompt = STEP3_REWRITE_PROMPT.format(
        draft=initial_draft,
        cta_instruction=build_cta_instruction(CTA_LEAD_MAGNET),
    )
    return _call(
        [{"role": "user", "content": prompt}],
        label="步驟 3｜改寫",
    )


def step4_polish(article: str) -> str:
    """步驟 4：社群寫作教練分析 → 潤飾改寫。"""
    return _two_turn(
        article=article,
        first_prompt=STEP4_ANALYSIS_PROMPT,
        second_prompt=STEP4_REWRITE_PROMPT,
        label_first="步驟 4-1｜風格分析",
        label_second="步驟 4-2｜潤飾改寫",
    )


def step5_theta(article: str) -> str:
    """步驟 5：希塔療癒導師視角 → 融入信念／下載／顯化元素。"""
    analysis_prompt = STEP5_THETA_ANALYSIS_PROMPT.format(identity=USER_IDENTITY)
    return _two_turn(
        article=article,
        first_prompt=analysis_prompt,
        second_prompt=STEP5_THETA_REWRITE_PROMPT,
        label_first="步驟 5-1｜希塔視角分析",
        label_second="步驟 5-2｜融入信念與下載",
    )


def step6_source(article: str, video: dict) -> str:
    """步驟 6：加入影片來源標註。"""
    prompt = STEP6_SOURCE_PROMPT.format(
        video_title=video["title"],
        channel=video["channel"],
        url=video["url"],
    )
    messages = [
        {"role": "user", "content": f"{prompt}\n\n{article}"}
    ]
    return _call(messages, label="步驟 6｜加入來源")


def run_pipeline(initial_draft: str, video: dict) -> str:
    """執行完整內容生產管線（步驟 3-6）。"""
    article = step3_rewrite(initial_draft)
    article = step4_polish(article)
    article = step5_theta(article)
    article = step6_source(article, video)
    return article
