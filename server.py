"""
輕量 HTTP 伺服器 — 讓 admin 後台可以點按執行 AI 內容生產線

端點：
  POST /run        觸發執行（需 Authorization: Bearer <RUN_TOKEN>）
  GET  /status     查詢目前狀態
  GET  /results    取得最新草稿列表
"""
import os
import threading
import time
from datetime import date
from pathlib import Path
from flask import Flask, jsonify, request, make_response, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        res = make_response('', 204)
        res.headers['Access-Control-Allow-Origin'] = '*'
        res.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return res

RUN_TOKEN = os.getenv("RUN_TOKEN", "")
PORT = int(os.getenv("PORT", 8080))

# 全域狀態
_state = {
    "status": "idle",   # idle | searching | searched | running | done | error
    "started_at": None,
    "finished_at": None,
    "message": "",
    "drafts": [],
    "candidates": [],   # [{id, title, channel, url, view_count, published_at}]
}
_lock = threading.Lock()


def _summarize_videos(videos: list) -> list:
    """用 Claude Haiku 為每支影片生成中文摘要。"""
    import anthropic
    from config import ANTHROPIC_API_KEY
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    result = []
    for v in videos:
        try:
            prompt = f"以下是一支 YouTube 影片的標題與頻道，請用繁體中文寫 1-2 句話說明這支影片大概在講什麼主題，語氣簡潔。\n\n標題：{v['title']}\n頻道：{v['channel']}\n\n直接輸出摘要，不需要其他說明。"
            resp = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )
            summary = resp.content[0].text.strip()
        except Exception:
            summary = ""
        result.append({**v, "summary": summary})
    return result


def _do_search():
    """在背景搜尋影片候選清單。"""
    with _lock:
        _state["status"] = "searching"
        _state["message"] = "搜尋影片中…"
        _state["candidates"] = []

    try:
        from youtube_finder import find_videos
        videos = find_videos()

        with _lock:
            _state["message"] = "生成中文摘要中…"

        videos = _summarize_videos(videos)

        with _lock:
            _state["status"] = "searched"
            _state["message"] = f"找到 {len(videos)} 支影片，請選擇要生成的題目"
            _state["candidates"] = videos
    except Exception as e:
        with _lock:
            _state["status"] = "error"
            _state["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            _state["message"] = f"搜尋失敗：{e}"


def _run_pipeline(video_ids: list):
    """在背景執行主程式，處理指定的影片 ID 清單。"""
    with _lock:
        _state["status"] = "running"
        _state["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _state["finished_at"] = None
        _state["message"] = "執行中…"
        _state["drafts"] = []

    try:
        from main import run_selected
        candidates = _state.get("candidates", [])
        selected = [v for v in candidates if v["id"] in video_ids] if video_ids else candidates
        run_selected(selected)

        today = date.today().isoformat()
        drafts = sorted(Path(".").glob(f"draft_{today}_*.txt"), key=lambda p: p.name)
        draft_list = [p.name for p in drafts]

        with _lock:
            _state["status"] = "done"
            _state["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            _state["message"] = f"完成，共產出 {len(draft_list)} 篇草稿"
            _state["drafts"] = draft_list

    except Exception as e:
        with _lock:
            _state["status"] = "error"
            _state["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            _state["message"] = f"執行失敗：{e}"


def _check_auth():
    if not RUN_TOKEN:
        return True
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {RUN_TOKEN}"


@app.route("/search", methods=["POST", "OPTIONS"])
def search_videos():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    with _lock:
        if _state["status"] in ("searching", "running"):
            return jsonify({"error": "已在執行中，請稍後"}), 409
    t = threading.Thread(target=_do_search, daemon=True)
    t.start()
    return jsonify({"ok": True, "message": "搜尋中…"})


@app.route("/run", methods=["POST", "OPTIONS"])
def run_pipeline():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    with _lock:
        if _state["status"] == "running":
            return jsonify({"error": "已在執行中，請稍後"}), 409

    data = request.get_json(silent=True) or {}
    video_ids = data.get("video_ids", [])

    t = threading.Thread(target=_run_pipeline, args=(video_ids,), daemon=True)
    t.start()
    return jsonify({"ok": True, "message": "已開始執行"})


@app.route("/status", methods=["GET"])
def get_status():
    with _lock:
        return jsonify(dict(_state))


@app.route("/save-gdocs/<filename>", methods=["POST", "OPTIONS"])
def save_gdocs(filename):
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    p = Path(filename)
    if not p.exists() or not p.name.startswith("draft_"):
        return jsonify({"error": "Not found"}), 404
    try:
        from gdocs import save_to_gdocs
        content = p.read_text(encoding="utf-8")
        title = p.stem  # e.g. draft_2026-03-16_01
        url = save_to_gdocs(title, content)
        return jsonify({"ok": True, "url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/results/<filename>", methods=["GET"])
def get_result(filename):
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    p = Path(filename)
    if not p.exists() or not p.name.startswith("draft_"):
        return jsonify({"error": "Not found"}), 404
    return p.read_text(encoding="utf-8"), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "Aiwritting"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
