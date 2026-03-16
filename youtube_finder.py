"""YouTube video finder using YouTube Data API v3."""
import random
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from config import YOUTUBE_API_KEY, SEARCH_QUERIES, MIN_VIEW_COUNT, MAX_AGE_DAYS, VIDEOS_PER_RUN


def get_youtube_client():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def get_published_after() -> str:
    """Return ISO 8601 date string for one year ago."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")


def search_videos(youtube, query: str, max_results: int = 20) -> list[dict]:
    """Search YouTube for videos matching query with CC captions."""
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        videoCaption="closedCaption",
        order="viewCount",
        publishedAfter=get_published_after(),
        maxResults=max_results,
        relevanceLanguage="en",
    )
    response = request.execute()
    return response.get("items", [])


def get_video_details(youtube, video_ids: list[str]) -> list[dict]:
    """Fetch view count and duration details for a list of video IDs."""
    request = youtube.videos().list(
        part="statistics,contentDetails,snippet",
        id=",".join(video_ids),
    )
    response = request.execute()
    return response.get("items", [])


def filter_by_views(videos: list[dict], min_views: int = MIN_VIEW_COUNT) -> list[dict]:
    """Keep only videos exceeding the minimum view count."""
    return [
        v for v in videos
        if int(v["statistics"].get("viewCount", 0)) >= min_views
    ]


def find_videos() -> list[dict]:
    """
    Main entry point: search multiple queries and return up to VIDEOS_PER_RUN
    unique videos with CC captions and view count >= MIN_VIEW_COUNT.
    """
    youtube = get_youtube_client()
    seen_ids: set[str] = set()
    candidates: list[dict] = []

    queries = SEARCH_QUERIES.copy()
    random.shuffle(queries)

    for query in queries:
        if len(candidates) >= VIDEOS_PER_RUN * 5:
            break

        search_results = search_videos(youtube, query)
        video_ids = [
            item["id"]["videoId"]
            for item in search_results
            if item["id"]["videoId"] not in seen_ids
        ]
        seen_ids.update(video_ids)

        if not video_ids:
            continue

        details = get_video_details(youtube, video_ids)
        qualified = filter_by_views(details)
        candidates.extend(qualified)

    unique: dict[str, dict] = {}
    for v in candidates:
        unique[v["id"]] = v

    selected = list(unique.values())
    random.shuffle(selected)
    selected = selected[:VIDEOS_PER_RUN]

    return [_format_video(v) for v in selected]


def _format_video(video: dict) -> dict:
    """Extract the fields we need into a clean dict."""
    snippet = video["snippet"]
    stats = video["statistics"]
    vid_id = video["id"]
    return {
        "id": vid_id,
        "title": snippet["title"],
        "channel": snippet["channelTitle"],
        "published_at": snippet["publishedAt"],
        "view_count": int(stats.get("viewCount", 0)),
        "url": f"https://www.youtube.com/watch?v={vid_id}",
    }
