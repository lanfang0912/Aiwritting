"""Fetch CC subtitles from YouTube videos."""
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from config import PREFERRED_LANGUAGES

MAX_TRANSCRIPT_CHARS = 8000


def fetch_transcript(video_id: str) -> tuple[str, str]:
    """
    Fetch the best available transcript for a video.

    Returns:
        (transcript_text, language_code) — both empty strings if unavailable.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None
        for lang in PREFERRED_LANGUAGES:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except NoTranscriptFound:
                continue

        if transcript is None:
            try:
                transcript = transcript_list.find_manually_created_transcript(
                    PREFERRED_LANGUAGES + ["zh-TW", "zh-CN", "zh"]
                )
            except NoTranscriptFound:
                pass

        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(
                    PREFERRED_LANGUAGES + ["zh-TW", "zh-CN", "zh"]
                )
            except NoTranscriptFound:
                pass

        if transcript is None:
            return "", ""

        entries = transcript.fetch()
        lang_code = transcript.language_code
        full_text = " ".join(entry["text"] for entry in entries)
        return full_text[:MAX_TRANSCRIPT_CHARS], lang_code

    except (TranscriptsDisabled, NoTranscriptFound):
        return "", ""
    except Exception as e:
        print(f"  [WARN] Could not fetch transcript for {video_id}: {e}")
        return "", ""
