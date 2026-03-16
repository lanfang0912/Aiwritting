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
from flask import Flask, jsonify, request
from flask_cors import CORS
...
CORS(app)

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

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


@app.route("/run", methods=["POST"])
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
def health():
    return jsonify({"ok": True, "service": "Aiwritting"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
