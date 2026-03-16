"""
創作者覺醒日 AI 超級內容生產線

流程：
  步驟 1-2  YouTube 搜尋 + 抓字幕 + Claude 初稿
  步驟 3    改寫（風格、字數、格式）
  步驟 4    社群寫作教練分析 → 潤飾改寫
  步驟 5    希塔療癒導師視角 → 融入信念／下載／顯化
  步驟 6    加入影片來源標註
  ────────────────────────────────
  步驟 7    ★ 人工精修（貼入 Google 文件）

執行：
    python main.py
"""
import sys
from datetime import date
from pathlib import Path

from config import YOUTUBE_API_KEY, ANTHROPIC_API_KEY, VIDEOS_PER_RUN, USER_IDENTITY
from youtube_finder import find_videos
from transcript_fetcher import fetch_transcript
from report_generator import generate_facebook_post
from pipeline import run_pipeline


DIVIDER = "=" * 70
THIN = "─" * 70


def check_env() -> None:
    missing = []
    if not YOUTUBE_API_KEY:
        missing.append("YOUTUBE_API_KEY")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if missing:
        print(f"[ERROR] 缺少環境變數：{', '.join(missing)}")
        print("        請複製 .env.example 為 .env 並填入 API Keys。")
        sys.exit(1)


def run() -> None:
    check_env()

    today = date.today().isoformat()

    print(f"\n{DIVIDER}")
    print(f"  創作者覺醒日 AI 內容生產線 — {today}")
    print(DIVIDER)
    print(f"  主題：關係療癒 ／ 心靈成長 ／ 豐盛顯化")
    print(f"  身份：{USER_IDENTITY}")
    print(f"  目標：{VIDEOS_PER_RUN} 支外文 CC 字幕影片（觀看數 > 10 萬，一年內）")
    print(DIVIDER + "\n")

    print("▶ 搜尋 YouTube 影片中...")
    try:
        videos = find_videos()
    except Exception as e:
        print(f"[ERROR] YouTube 搜尋失敗：{e}")
        sys.exit(1)

    if not videos:
        print("[WARN] 未找到符合條件的影片，請稍後再試。")
        sys.exit(0)

    print(f"  找到 {len(videos)} 支符合條件的影片\n")

    success_count = 0

    for idx, video in enumerate(videos, start=1):
        print(f"\n{DIVIDER}")
        print(f"  ▍ 影片 {idx}/{len(videos)}")
        print(f"  標題：{video['title']}")
        print(f"  頻道：{video['channel']}")
        print(f"  網址：{video['url']}")
        print(f"  觀看數：{video['view_count']:,}　發布：{video['published_at'][:10]}")
        print(DIVIDER)

        print("  ▷ 步驟 2｜抓取 CC 字幕...")
        transcript, lang = fetch_transcript(video["id"])

        if not transcript:
            print("  [SKIP] 找不到可用的 CC 字幕，跳過此影片。\n")
            continue

        print(f"         字幕語言：{lang}　字幕長度：{len(transcript):,} 字元")

        try:
            print("  ▷ 步驟 2｜Claude 生成初稿...")
            initial_draft = generate_facebook_post(video, transcript)

            print(f"\n{THIN}")
            print("  ▍ 進入內容生產管線（步驟 3-6）")
            print(THIN)
            final_draft = run_pipeline(initial_draft, video)

        except Exception as e:
            print(f"  [ERROR] 處理失敗：{e}\n")
            continue

        draft_path = Path(f"draft_{today}_{idx:02d}.txt")
        draft_path.write_text(final_draft, encoding="utf-8")

        print(f"\n{THIN}")
        print(f"  ✓ 草稿已儲存：{draft_path.resolve()}")
        print(f"  → 下一步：貼入 Google 文件進行人工精修（步驟 7）")
        print(THIN)

        preview = final_draft[:300].replace("\n", " ")
        print(f"\n  預覽：{preview}……\n")

        success_count += 1

    print(f"\n{DIVIDER}")
    print(f"  完成！成功產出 {success_count}/{len(videos)} 篇草稿")
    if success_count > 0:
        print(f"  草稿檔案：draft_{today}_01.txt ～ draft_{today}_{success_count:02d}.txt")
        print(f"  下一步：將草稿貼入 Google 文件，進行步驟 7 人工精修")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    run()
