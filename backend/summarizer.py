import os
import json
import re
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MAX_MODEL_TRANSCRIPT_CHARS = 120000
QUOTA_ERROR_MARKERS = (
    "429",
    "quota",
    "rate limit",
    "resource_exhausted",
    "GenerateRequestsPerDayPerProjectPerModel",
)

# Exact structured prompt template as requested
STRUCTURED_PROMPT_TEMPLATE = """
You are an expert content summarizer. Analyze this YouTube video transcript and respond ONLY in valid JSON with this exact structure:
{{
  "summary": "2-3 paragraph overview of the entire video",
  "key_insights": ["insight 1", "insight 2", "insight 3", "insight 4", "insight 5"],
  "takeaways": ["actionable step 1", "actionable step 2", "actionable step 3"],
  "notes": ["bullet note 1", "bullet note 2", "bullet note 3", "bullet note 4"],
  "eli5": "A simple plain-English explanation as if explaining to a complete beginner with no jargon",
  "study_mode": "Deep educational breakdown focusing on concepts, definitions, and learning outcomes",
  "productivity_mode": "Focus on time-saving tips, workflow improvements, and efficiency gains mentioned",
  "business_mode": "Extract business strategy, market insights, revenue opportunities, and professional applications"
}}
Transcript: {transcript}
"""

def is_quota_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return any(marker.lower() in error_text for marker in QUOTA_ERROR_MARKERS)

def split_sentences(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]

def build_local_summary(transcript: str, reason: str = "") -> dict:
    """
    Deterministic fallback when the Gemini quota is exhausted.
    It is not as smart as the model, but it keeps the app useful and avoids a hard failure.
    """
    sentences = split_sentences(transcript)
    preview_sentences = sentences[:8] if sentences else [transcript[:700]]
    summary = " ".join(preview_sentences).strip()
    if len(summary) > 1400:
        summary = summary[:1400].rsplit(" ", 1)[0] + "..."

    keywords = []
    for word in re.findall(r'\b[a-zA-Z][a-zA-Z-]{4,}\b', transcript.lower()):
        if word in {"about", "there", "their", "which", "would", "could", "should", "because", "while", "where", "these", "those", "video"}:
            continue
        if word not in keywords:
            keywords.append(word)
        if len(keywords) == 8:
            break

    fallback_note = "AI quota was reached, so this overview was generated locally from the transcript."
    if reason:
        fallback_note = f"{fallback_note} Gemini detail: {reason[:180]}"

    return {
        "summary": summary or "Transcript loaded, but there was not enough text to build a local summary.",
        "key_insights": [
            "The transcript was fetched successfully and is available with timestamped blocks.",
            "The AI provider quota was reached before a full model-generated summary could be created.",
            "Use the transcript timeline for the complete source text while the quota resets.",
            f"Likely focus terms: {', '.join(keywords[:5])}" if keywords else "The transcript did not expose enough repeated terms for keyword extraction.",
            "Try again after the Gemini retry window or switch to a paid/higher-limit API key for full AI output.",
        ],
        "takeaways": [
            "Read the timestamped transcript blocks for the full video content.",
            "Retry summarization after the Gemini quota resets.",
            "Use a higher-limit model/API key before publishing to real users.",
        ],
        "notes": [
            fallback_note,
            "This fallback does not call Gemini and therefore returns quickly.",
            "For production, keep this as a backup so users never hit a dead end.",
        ],
        "eli5": "The app found the video text, but the AI service said the free limit was used up. So the app made a simple local summary instead of failing.",
        "study_mode": "Study the timestamped transcript blocks first. The local fallback highlights the opening content and likely keywords, but a full AI explanation requires available Gemini quota.",
        "productivity_mode": "The transcript is already loaded, so you can still scan the video quickly. Retry AI analysis later for deeper notes.",
        "business_mode": "For public launch, quota limits need a production plan, fallback provider, or paid API key so users do not see provider errors.",
        "fallback": True,
    }

def clean_and_parse_json(text: str) -> dict:
    """
    Cleans up the text from potential markdown code fences and parses it as JSON.
    """
    cleaned = text.strip()
    
    # Remove markdown code fences if present (e.g. ```json ... ```)
    if cleaned.startswith("```"):
        # Remove the leading ```json or ```
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        # Remove trailing ```
        cleaned = re.sub(r"\s*```$", "", cleaned)
        
    cleaned = cleaned.strip()
    return json.loads(cleaned)

def get_preferred_model():
    """
    Select a Flash model that is fast and likely to work within free-tier/demo quotas.
    """
    try:
        available_models = [m.name for m in genai.list_models()]
    except Exception:
        available_models = []

    model_name = "gemini-2.5-flash-lite"
    preferences = [
        "models/gemini-2.5-flash-lite",
        "models/gemini-flash-lite-latest",
        "models/gemini-2.0-flash-lite",
        "models/gemini-2.0-flash",
        "models/gemini-2.5-flash",
        "models/gemini-1.5-flash",
        "models/gemini-flash-latest",
        "models/gemini-3.5-flash",
    ]

    for pref in preferences:
        if pref in available_models:
            model_name = pref.split("/")[-1]
            break

    return genai.GenerativeModel(model_name)

def summarize_transcript(chunks: list[str]) -> dict:
    """
    Generates a structured summary of the video transcript using Gemini 1.5 Flash.
    
    If the transcript has multiple chunks, it summarizes each chunk first,
    then compiles and generates the final structured summary.
    """
    # Force reload environment variables to ensure any key updates are active
    load_dotenv(override=True)
    
    transcript_content = "\n\n".join(chunks).strip()
    if len(transcript_content) > MAX_MODEL_TRANSCRIPT_CHARS:
        transcript_content = transcript_content[:MAX_MODEL_TRANSCRIPT_CHARS].rsplit(" ", 1)[0]

    # Verify API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        return build_local_summary(transcript_content, "GEMINI_API_KEY is missing.")
        
    # Configure Gemini SDK
    genai.configure(api_key=api_key)
    
    try:
        model = get_preferred_model()
    except Exception as e:
        if is_quota_error(e):
            return build_local_summary(transcript_content, str(e))
        raise RuntimeError(f"Failed to initialize AI Model: {str(e)}")
        
    # Format the final structured prompt
    final_prompt = STRUCTURED_PROMPT_TEMPLATE.format(transcript=transcript_content)
    
    # Request JSON output using Gemini generation_config
    try:
        response = model.generate_content(
            final_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        response_text = response.text
        if not response_text:
            raise ValueError("The AI service returned an empty response.")
    except Exception as e:
        if is_quota_error(e):
            return build_local_summary(transcript_content, str(e))
        raise RuntimeError(f"Error calling AI service for final summary: {str(e)}")
        
    # Parse the response to verify it is valid JSON
    try:
        summary_json = clean_and_parse_json(response_text)
        
        # Verify required keys exist
        required_keys = [
            "summary", "key_insights", "takeaways", "notes", 
            "eli5", "study_mode", "productivity_mode", "business_mode"
        ]
        
        missing_keys = [key for key in required_keys if key not in summary_json]
        if missing_keys:
            # Add missing keys with default values/messages so the frontend doesn't crash
            for key in missing_keys:
                if key in ["key_insights", "takeaways", "notes"]:
                    summary_json[key] = ["No details provided by AI for this section."]
                else:
                    summary_json[key] = "Not specified in video transcript."
                    
        return summary_json
    except Exception as e:
        raise ValueError(
            f"Failed to parse API response as valid JSON: {str(e)}. "
            f"Raw response: {response_text[:300]}..."
        )

def answer_video_question(question: str, context: str) -> str:
    """
    Answer a user question from the current video context.
    """
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError("GEMINI_API_KEY is missing.")

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    genai.configure(api_key=api_key)
    model = get_preferred_model()
    prompt = f"""
Answer the user's question using only the video transcript and summary context below.
If the answer is not present in the context, say that the video does not clearly mention it.
Keep the answer concise and useful.

Question: {question}

Video context:
{context[:90000]}
"""

    try:
        response = model.generate_content(prompt)
        if not response.text:
            raise ValueError("The AI service returned an empty response.")
        return response.text.strip()
    except Exception as e:
        if is_quota_error(e):
            raise ValueError("Gemini quota was reached. Try again later or use the local summary tools.")
        raise RuntimeError(f"Error calling AI chat service: {str(e)}")
