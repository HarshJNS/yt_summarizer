import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

PREFERRED_LANGUAGES = ("en", "en-US", "en-GB", "hi")
TRANSCRIPT_BLOCK_SECONDS = 30
TRANSCRIPT_BLOCK_MAX_CHARS = 900


def _select_best_transcript(transcript_list):
    """
    Pick the most useful transcript available for summarization.
    Preference order: English manual, English generated, translated English,
    then any manual/generated transcript YouTube exposes.
    """
    try:
        return transcript_list.find_manually_created_transcript(PREFERRED_LANGUAGES)
    except NoTranscriptFound:
        pass

    try:
        return transcript_list.find_generated_transcript(PREFERRED_LANGUAGES)
    except NoTranscriptFound:
        pass

    for transcript in transcript_list:
        if transcript.is_translatable:
            return transcript.translate("en")

    for transcript in transcript_list:
        return transcript

    raise ValueError("No transcript was found for this video.")


def _clean_transcript_text(raw_text: str) -> str:
    raw_text = re.sub(r'\s+', ' ', raw_text)

    fillers = [
        r'\bum\b',
        r'\buh\b',
        r'\byou\s+know\b',
        r'\blike\b',
        r'\bbasically\b',
        r'\bliterally\b'
    ]

    cleaned_text = raw_text
    for filler in fillers:
        cleaned_text = re.sub(filler, '', cleaned_text, flags=re.IGNORECASE)

    return re.sub(r'\s+', ' ', cleaned_text).strip()


def _group_transcript_segments(segments: list[dict]) -> list[dict]:
    """
    Merge tiny caption snippets into readable time-period blocks.
    This produces NoteGPT-style transcript chunks instead of one line per second.
    """
    blocks = []
    current = None

    for segment in segments:
        segment_start = segment["start"]
        segment_end = segment["start"] + segment["duration"]
        segment_text = segment["text"]

        should_start_new_block = (
            current is None
            or segment_start - current["start"] >= TRANSCRIPT_BLOCK_SECONDS
            or len(current["text"]) + len(segment_text) + 1 > TRANSCRIPT_BLOCK_MAX_CHARS
        )

        if should_start_new_block:
            if current:
                current["text"] = _clean_transcript_text(current["text"])
                blocks.append(current)

            current = {
                "index": len(blocks),
                "start": segment_start,
                "end": segment_end,
                "duration": round(segment_end - segment_start, 2),
                "text": segment_text,
            }
            continue

        current["end"] = segment_end
        current["duration"] = round(current["end"] - current["start"], 2)
        current["text"] = f'{current["text"]} {segment_text}'

    if current:
        current["text"] = _clean_transcript_text(current["text"])
        blocks.append(current)

    return blocks


def fetch_transcript_segments(video_id: str) -> dict:
    """
    Fetch timestamped transcript segments quickly for the frontend timeline.
    This does not call the AI model, so it should return much faster than /summarize.
    """
    try:
        api = YouTubeTranscriptApi()
        transcript = _select_best_transcript(api.list(video_id))
        transcript_data = transcript.fetch(preserve_formatting=False)

        segments = []
        raw_parts = []

        for index, snippet in enumerate(transcript_data):
            text = re.sub(r'\s+', ' ', snippet.text).strip()
            if not text:
                continue

            raw_parts.append(text)
            segments.append({
                "index": index,
                "start": round(float(snippet.start), 2),
                "duration": round(float(snippet.duration), 2),
                "text": text,
            })

        cleaned_text = _clean_transcript_text(" ".join(raw_parts))
        if not cleaned_text:
            raise ValueError("The transcript was successfully retrieved but is empty after cleaning.")

        return {
            "language": getattr(transcript, "language", "Unknown"),
            "language_code": getattr(transcript, "language_code", ""),
            "is_generated": getattr(transcript, "is_generated", False),
            "segments": segments,
            "blocks": _group_transcript_segments(segments),
            "raw_transcript": cleaned_text,
        }

    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled or not available for this video.")
    except NoTranscriptFound:
        raise ValueError("No transcript was found for this video.")
    except VideoUnavailable:
        raise ValueError("This video is unavailable (it may be private, deleted, or geoblocked).")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Could not retrieve transcript: {str(e)}")


def fetch_and_clean_transcript(video_id: str) -> str:
    """
    Fetches the transcript for a YouTube video by ID and cleans it.
    
    Removes standard filler words: "um", "uh", "you know", "like", "basically", "literally".
    Handles common transcript fetching exceptions.
    """
    try:
        cleaned_text = fetch_transcript_segments(video_id)["raw_transcript"]
        
        if not cleaned_text:
            raise ValueError("The transcript was successfully retrieved but is empty after cleaning.")
            
        return cleaned_text

    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled or not available for this video.")
    except NoTranscriptFound:
        raise ValueError("No transcript was found for this video.")
    except VideoUnavailable:
        raise ValueError("This video is unavailable (it may be private, deleted, or geoblocked).")
    except Exception as e:
        # Raise generic errors with detail
        raise ValueError(f"Could not retrieve transcript: {str(e)}")
