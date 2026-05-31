import re
from typing import Optional
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import local modules
from transcript import fetch_and_clean_transcript, fetch_transcript_segments
from chunker import chunk_transcript
from summarizer import summarize_transcript, answer_video_question

app = FastAPI(
    title="TubeAI Summarizer API",
    description="FastAPI Backend for extracting transcripts and summarizing YouTube videos using Advanced AI.",
    version="1.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummarizeRequest(BaseModel):
    url: str
    raw_transcript: Optional[str] = None

class ChatRequest(BaseModel):
    question: str
    context: str

def extract_video_id(url: str) -> str:
    """
    Extracts the 11-character YouTube video ID from various styles of YouTube URLs.
    Supports watch?v=, youtu.be/, embed/, shorts/, and direct video ID inputs.
    """
    url = url.strip()
    
    # Check if the input itself is directly a valid 11-char video ID
    if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
        
    # Standard formats matching YouTube URLs
    pattern = r'(?:https?://)?(?:www\.)?(?:m\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|shorts/|v/|e/)?([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
        
    # Fallback to search for v= parameter anywhere in the query string
    param_match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    if param_match:
        return param_match.group(1)
        
    raise ValueError(
        "Invalid YouTube URL. Please make sure you copy the link directly from your browser "
        "or share menu (e.g., https://www.youtube.com/watch?v=... or https://youtu.be/...)"
    )

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "TubeAI Summarizer API is running. Send a POST request to /summarize to get started."
    }

@app.post("/transcript")
def get_transcript(request: SummarizeRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="The YouTube URL field cannot be empty.")

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        transcript_result = fetch_transcript_segments(video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcript retrieval error: {str(e)}")

    transcript_result["video_id"] = video_id
    transcript_result["video_url"] = f"https://www.youtube.com/watch?v={video_id}"
    return transcript_result

@app.post("/summarize")
def summarize_video(request: SummarizeRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="The YouTube URL field cannot be empty.")
        
    # Step 1: Extract Video ID
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Step 2: Reuse a previously fetched transcript when the frontend has one.
    if request.raw_transcript and request.raw_transcript.strip():
        cleaned_transcript = request.raw_transcript.strip()
    else:
        try:
            cleaned_transcript = fetch_and_clean_transcript(video_id)
        except ValueError as e:
            # Expected errors like transcripts disabled, video unavailable, etc.
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcript retrieval error: {str(e)}")
        
    # Step 3: Chunk transcript (if it exceeds 8000 characters)
    try:
        chunks = chunk_transcript(cleaned_transcript, max_chars=8000)
        if not chunks:
            raise HTTPException(status_code=400, detail="The video transcript is empty.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to chunk transcript: {str(e)}")
        
    # Step 4: Call AI engine to summarize
    try:
        summary_result = summarize_transcript(chunks)
    except ValueError as e:
        # Mostly configuration errors (e.g. API key missing) or bad JSON parses
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Summarizer error: {str(e)}")
        
    # Add raw transcript and video metadata to the response
    summary_result["raw_transcript"] = cleaned_transcript
    summary_result["video_id"] = video_id
    summary_result["video_url"] = f"https://www.youtube.com/watch?v={video_id}"
    
    return summary_result

@app.post("/chat")
def chat_with_video(request: ChatRequest):
    question = request.question.strip()
    context = request.context.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not context:
        raise HTTPException(status_code=400, detail="Video context is not available yet.")

    try:
        return {"answer": answer_video_question(question, context)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Chat error: {str(e)}")
