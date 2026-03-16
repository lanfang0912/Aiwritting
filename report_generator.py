"""Generate initial draft from video transcript using Claude API."""
import anthropic

from config import ANTHROPIC_API_KEY, FACEBOOK_POST_PROMPT


def generate_facebook_post(video: dict, transcript: str) -> str:
    """
    Call Claude to generate an initial draft based on the video transcript.

    Args:
        video: dict with keys title, channel, url
        transcript: CC subtitle text

    Returns:
        Generated draft text, or empty string on failure.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = FACEBOOK_POST_PROMPT.format(
        title=video["title"],
        channel=video["channel"],
        url=video["url"],
        transcript=transcript,
    )

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        final = stream.get_final_message()

    for block in final.content:
        if block.type == "text":
            return block.text.strip()

    return ""
