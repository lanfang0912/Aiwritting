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
    "status": "idle",   # idle | running | done | error
    "started_at": None,
    "finished_at": None,
    "message": "",
    "drafts": [],
}
_lock = threading.Lock()


def _run_pipeline():
    """在背景執行主程式。"""
    import sys
    from io import StringIO

    with _lock:
        _state["status"] = "running"
        _state["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _state["finished_at"] = None
        _state["message"] = "執行中…"
        _state["drafts"] = []

    try:
        from main import run as main_run
        main_run()

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


@app.route("/run", methods=["POST", "OPTIONS"])
def run_pipeline():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    with _lock:
        if _state["status"] == "running":
            return jsonify({"error": "已在執行中，請稍後"}), 409

    t = threading.Thread(target=_run_pipeline, daemon=True)
    t.start()
    return jsonify({"ok": True, "message": "已開始執行"})


@app.route("/status", methods=["GET"])
def get_status():
    with _lock:
        return jsonify(dict(_state))


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
