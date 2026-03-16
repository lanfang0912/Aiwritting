"""Configuration for YouTube Video Finder."""
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Search settings
VIDEOS_PER_RUN = 3
MIN_VIEW_COUNT = 100_000
MAX_AGE_DAYS = 365

# Search queries — 三大主題：關係、心靈療癒、豐盛顯化
SEARCH_QUERIES = [
    # 伴侶 / 親子關係
    "couples therapy interview relationship advice",
    "parenting expert interview child development",
    "marriage counseling relationship podcast interview",
    "parent child relationship psychology interview",
    "couple conflict resolution expert talk",
    "attachment parenting expert interview",
    # 心靈成長 / 療癒
    "spiritual healing interview self discovery",
    "inner child healing therapy interview",
    "trauma healing expert talk interview",
    "mindfulness meditation expert podcast interview",
    "theta healing belief work interview",
    "energy healing transformation story interview",
    # 豐盛顯化
    "manifestation abundance mindset interview",
    "law of attraction success story interview",
    "abundance mindset coach interview",
    "manifesting wealth consciousness interview",
]

# Preferred languages (non-Chinese, targeting foreign content)
PREFERRED_LANGUAGES = ["en", "ja", "ko", "es", "fr", "de"]

# ── 使用者設定 ──────────────────────────────────────────────────────────────
USER_IDENTITY = "希塔療癒導師"

# ── 步驟 1-2：初稿 ──────────────────────────────────────────────────────────
FACEBOOK_POST_PROMPT = """根據以下影片的字幕內容，請完成以下任務：

(1) 根據來源資訊，把內容寫成一篇通俗易懂的臉書貼文，口語化、節奏快、煽情、幽默、但不說教。
(2) 不要杜撰，根據事實，用「第三者」的視角說故事。開頭要有爆點，引言不要太長，趕快進入重點，結尾要總結本文重點，並且有金句，讓人讀得津津有味！
(3) 不要有表情符號、分隔線、#主題標籤

影片標題：{title}
影片頻道：{channel}
影片連結：{url}

字幕內容（節錄）：
{transcript}

請直接輸出臉書貼文內容，不需要額外說明。"""

# ── 步驟 3：改寫 ────────────────────────────────────────────────────────────
STEP3_REWRITE_PROMPT = """以下是一篇根據 YouTube 影片字幕整理的初稿，請根據以下要求改寫：

(1) 任務：請把這篇文章改寫成一篇臉書貼文，盡量保留原文資訊豐富度與細節，包含研究出處、關鍵數據、名人案例、真實對白，不要過度刪減，也不要憑空捏造，文章至少1200~1500字以上。
(2) 風格：口語化，煽情、但不說教。情緒表達豐富（驚訝、敬畏、懸念、恐懼、焦慮、憤怒、好笑、感動）。資訊密度高、長短句交錯。
(3) 注意：不要過度想要說服他人、不要把讀者當白癡。
(4) 限制：不要使用以下詞彙與句型「不是ＯＯ而是ＯＯ、其實很ＯＯ、從來不是、溫柔提醒、這不是偶然、很穩、停住、撐住、冷掉、安靜、殘酷、刺耳、很直接、不太舒服、走得很深、背脊發涼、陰陽怪氣、其實很單純、再普通不過的、留下一句話、而是願意說一句、回頭看、總結來說、旨在、帶走、硬核、結構」
(5) 更正：去除分隔線、表情符號與主題標籤及其內容。
(6) 標註：如果資料來源提到名字時，包含中譯名與英文原名，請在第一次出現時，在中譯名後加註英文原名。如果來源提到名字時，沒有包含中英對照的姓名則不用標註。
(7) 文章標題格式：

【主標】

—— 副標

內文標題在文字前置入：▋

(8) 文末 CTA：在文章最後加上一段邀請留言與分享的文字。語氣自然、不強迫，像是朋友說話。引導讀者留言分享自身經驗或想法，並鼓勵轉發給有需要的人。不要用命令句，不要用「記得」「趕快」「立刻」等催促語。

初稿如下：
{draft}

請直接輸出改寫後的文章，不需要額外說明。"""

# ── 步驟 4-1：分析 ──────────────────────────────────────────────────────────
STEP4_ANALYSIS_PROMPT = """你是一位資深社群寫作教練，請分析這篇文章的風格與優缺點，以及可優化的地方，並根據建議提出文句範例。"""

# ── 步驟 4-2：根據分析改寫 ──────────────────────────────────────────────────
STEP4_REWRITE_PROMPT = """按照你提供的方向調整，原文盡量不大幅改動，只調整必要調整的地方。可以針對字句、段落、排版小幅度修改、更動與刪減，但不要從頭到尾每一字每一句都全部改寫。用字遣詞可精簡，但要維持高資訊密度。不要與我互動與對話，直接給我文章。"""

# ── 步驟 5-1：希塔療癒視角分析 ─────────────────────────────────────────────
STEP5_THETA_ANALYSIS_PROMPT = """我是一名{identity}。

請分析這篇文章與希塔療癒（Theta Healing）的關聯，根據文章主題，判斷是否適合加入以下元素，並提供修改建議與文句範例：

1. 信念：點出人們對此主題常見的 1-3 個底層限制性信念
   格式：「很多人對 XX 的底層信念是……」

2. 下載：給讀者 1-3 個希塔療癒肯定語
   格式：「我知道如何……是安全的」

3. 豐盛顯化：若文章主題與豐盛、顯化相關，自然帶入對應視角

注意：
- 如果文章主題與以上元素關聯性低，可以選擇不加或只加部分，不要硬塞。
- 提供文句範例時，請勿使用「不是ＯＯ而是ＯＯ」句型。"""

# ── 步驟 5-2：融入希塔元素 ──────────────────────────────────────────────────
STEP5_THETA_REWRITE_PROMPT = """幫我將以上建議自然融入文章，原文內容盡量不變，只調整必要調整的地方，不要從頭到尾改寫，不要與我互動與對話，直接把完成的文章給我。"""

# ── 步驟 6：加入來源標註 ────────────────────────────────────────────────────
STEP6_SOURCE_PROMPT = """請在文章中適合的段落（選擇自然的位置，不要放在開頭或結尾太突兀），加入以下這段來源說明：

「YT 推播「{video_title}」影片給我，覺得很有意思，整理重點做為學習紀錄，也分享給你」

頻道：{channel}
連結：{url}

不要與我互動與對話，直接把加入來源後的完整文章給我。"""
