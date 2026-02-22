"""
YouTube transcript extraction.
Returns (title, transcript_text, duration_seconds).
"""

import re
from typing import Tuple, Optional

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from pytubefix import YouTube


def _extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError(f"Cannot extract video ID from URL: {url}")


async def fetch_transcript(url: str) -> Tuple[str, str, Optional[int]]:
    """
    Returns:
        title           – video title (best-effort)
        transcript_text – full transcript as plain text
        duration        – seconds (best-effort)
    """
    video_id = _extract_video_id(url)

    # --- transcript ---
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "en-US", "en-GB"]
        )
    except (TranscriptsDisabled, NoTranscriptFound):
        # fallback: try auto-generated in any language
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript_list = transcripts.find_generated_transcript(
            [t.language_code for t in transcripts]
        ).fetch()

    transcript_text = " ".join(
        item["text"].strip() for item in transcript_list if item.get("text")
    )

    # --- metadata via pytube (best-effort) ---
    title = "YouTube Video"
    duration = None
    try:
        yt = YouTube(url)
        title = yt.title or title
        duration = yt.length
    except Exception:
        pass

    return title, transcript_text, duration
