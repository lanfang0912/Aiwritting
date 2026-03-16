"""YouTube video finder using yt-dlp (no API key required)."""
import json
import random
import subprocess
from datetime import datetime, timedelta, timezone

from config import SEARCH_QUERIES, MIN_VIEW_COUNT, MAX_AGE_DAYS, VIDEOS_PER_RUN


def _search_one_query(query: str, max_results: int = 20) -> list[dict]:
    """Search YouTube with yt-dlp and return raw info list."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                f"ytsearch{max_results}:{query}",
                "--dump-json",
                "--skip-download",
                "--no-playlist",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    videos = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        try:
            videos.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return videos


def _is_recent(video: dict) -> bool:
    """Return True if the video was published within MAX_AGE_DAYS."""
    upload_date = video.get("upload_date", "")  # YYYYMMDD
    if not upload_date or len(upload_date) != 8:
        return True  # unknown date, keep it
    try:
        pub = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
        return pub >= cutoff
    except ValueError:
        return True


def find_videos() -> list[dict]:
    """
    Search multiple queries via yt-dlp and return up to VIDEOS_PER_RUN
    unique videos with view count >= MIN_VIEW_COUNT published within MAX_AGE_DAYS.
    """
    queries = SEARCH_QUERIES.copy()
    random.shuffle(queries)

    seen_ids: set[str] = set()
    candidates: list[dict] = []

    for query in queries:
        if len(candidates) >= VIDEOS_PER_RUN * 3:
            break

        print(f"  搜尋：{query}")
        raw = _search_one_query(query)

        for v in raw:
            vid_id = v.get("id") or v.get("webpage_url_basename")
            if not vid_id or vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)

            view_count = v.get("view_count") or 0
            if view_count < MIN_VIEW_COUNT:
                continue
            if not _is_recent(v):
                continue

            candidates.append(v)

    random.shuffle(candidates)
    selected = candidates[:VIDEOS_PER_RUN]
    return [_format_video(v) for v in selected]


def _format_video(v: dict) -> dict:
    """Normalise yt-dlp output to the shape the rest of the code expects."""
    vid_id = v.get("id") or v.get("webpage_url_basename", "")
    upload_date = v.get("upload_date", "")
    if len(upload_date) == 8:
        published_at = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}T00:00:00Z"
    else:
        published_at = ""
    return {
        "id": vid_id,
        "title": v.get("title", ""),
        "channel": v.get("uploader") or v.get("channel", ""),
        "published_at": published_at,
        "view_count": v.get("view_count") or 0,
        "url": f"https://www.youtube.com/watch?v={vid_id}",
    }
