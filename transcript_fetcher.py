"""Fetch CC subtitles from YouTube videos using yt-dlp."""
import subprocess
import json
import tempfile
import os

from config import PREFERRED_LANGUAGES

MAX_TRANSCRIPT_CHARS = 8000


def fetch_transcript(video_id: str) -> tuple[str, str]:
    """
    Fetch the best available transcript for a video using yt-dlp.

    Returns:
        (transcript_text, language_code) — both empty strings if unavailable.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    lang_preference = ",".join(PREFERRED_LANGUAGES)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--write-auto-sub",
                    "--write-sub",
                    "--sub-langs", lang_preference,
                    "--sub-format", "json3",
                    "--skip-download",
                    "--no-playlist",
                    "-o", os.path.join(tmpdir, "%(id)s"),
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            print(f"  [WARN] yt-dlp timed out for {video_id}")
            return "", ""
        except FileNotFoundError:
            print("  [WARN] yt-dlp not found, please add it to requirements")
            return "", ""

        # Find the downloaded subtitle file
        for fname in os.listdir(tmpdir):
            if fname.endswith(".json3"):
                lang_code = fname.split(".")[-2]  # e.g. en, ja
                fpath = os.path.join(tmpdir, fname)
                try:
                    with open(fpath, encoding="utf-8") as f:
                        data = json.load(f)
                    # json3 format: events list with segs
                    parts = []
                    for event in data.get("events", []):
                        for seg in event.get("segs", []):
                            text = seg.get("utf8", "").strip()
                            if text and text != "\n":
                                parts.append(text)
                    full_text = " ".join(parts)
                    return full_text[:MAX_TRANSCRIPT_CHARS], lang_code
                except Exception as e:
                    print(f"  [WARN] Could not parse subtitle file: {e}")
                    return "", ""

        print(f"  [WARN] No subtitle file found for {video_id}")
        return "", ""
