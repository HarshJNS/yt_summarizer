# TubeAI Summarizer

TubeAI Summarizer is a full-stack web application that turns YouTube videos into structured AI notes. Paste a YouTube URL, fetch the available transcript, and generate a clean dashboard with an overview, key insights, action points, study notes, business analysis, productivity takeaways, chapters, a mind map, and transcript-aware AI chat.

Repository: [https://github.com/HarshJNS/yt_summarizer](https://github.com/HarshJNS/yt_summarizer)

## Overview

Long videos often contain useful information, but finding the important parts can take time. TubeAI Summarizer solves that by combining YouTube transcript extraction with Gemini-powered analysis. The application first loads timestamped transcript blocks so the user can inspect the source content quickly, then sends the transcript to an AI model for structured summarization.

The frontend is intentionally lightweight: a single responsive HTML file powered by Tailwind CDN and vanilla JavaScript. The backend is a FastAPI service that handles YouTube URL parsing, transcript retrieval, text cleanup, chunking, Gemini calls, and video chat responses.

## Key Features

- YouTube URL support for `watch?v=`, `youtu.be`, `embed`, `shorts`, and raw video IDs.
- Transcript extraction using `youtube-transcript-api`.
- Preferred transcript selection with support for manual captions, generated captions, and translation to English when available.
- Transcript cleanup that removes common filler words and normalizes spacing.
- Timestamped transcript blocks for quick scanning.
- AI-generated overview summary.
- Key insights, action points, and quick notes.
- Study, productivity, business, and ELI5 analysis modes.
- Chapter generation from transcript blocks.
- Mind map view generated from summary sections.
- AI chat endpoint that answers questions from the current video context.
- Copy summary, copy transcript, and download report tools.
- Gemini quota fallback that keeps the app usable when a model quota is reached.
- Deployment-friendly frontend API configuration through a query parameter.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML, Tailwind CSS CDN, Vanilla JavaScript |
| Backend | Python, FastAPI, Uvicorn |
| AI | Google Gemini API through `google-generativeai` |
| Transcript Source | `youtube-transcript-api` |
| Configuration | `python-dotenv` |
| Deployment Targets | Railway or Render for backend, Netlify or Vercel for frontend |

## Project Structure

```text
yt_summarizer/
  backend/
    main.py              FastAPI app, routes, CORS, YouTube URL parsing
    summarizer.py        Gemini model selection, summary generation, AI chat
    transcript.py        Transcript retrieval, language selection, cleanup
    chunker.py           Transcript chunking for large videos
    requirements.txt     Python dependencies
    .env                 Local secrets, ignored by Git
  frontend/
    index.html           Main responsive dashboard and app logic
    components/
      VideoPreviewCard.jsx
  .gitignore
  README.md
```

## How It Works

1. The user enters a YouTube URL in the frontend.
2. The frontend extracts the video ID for immediate validation.
3. The backend receives the URL and validates the YouTube video ID.
4. `youtube-transcript-api` fetches transcript snippets.
5. Transcript snippets are cleaned and grouped into readable timestamped blocks.
6. The cleaned transcript is chunked if needed.
7. Gemini generates a structured JSON response for the summary dashboard.
8. The frontend renders the transcript, summary, chapters, mind map, and tool panels.
9. The AI chat panel sends a question plus video context to the backend `/chat` endpoint.

## Backend API

### `GET /`

Health check endpoint.

Example response:

```json
{
  "status": "online",
  "message": "TubeAI Summarizer API is running. Send a POST request to /summarize to get started."
}
```

### `POST /transcript`

Fetches timestamped transcript data for a video.

Request:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

Response includes:

- `language`
- `language_code`
- `is_generated`
- `segments`
- `blocks`
- `raw_transcript`
- `video_id`
- `video_url`

### `POST /summarize`

Generates the structured AI summary.

Request:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "raw_transcript": "Optional transcript text already loaded by the frontend"
}
```

Response includes:

- `summary`
- `key_insights`
- `takeaways`
- `notes`
- `eli5`
- `study_mode`
- `productivity_mode`
- `business_mode`
- `raw_transcript`
- `video_id`
- `video_url`

### `POST /chat`

Answers a question using the current video transcript and summary context.

Request:

```json
{
  "question": "What are the main takeaways?",
  "context": "Summary, transcript, notes, and insights for the current video"
}
```

Response:

```json
{
  "answer": "Concise answer based on the video context."
}
```

## Local Setup

### Prerequisites

- Python 3.8 or later
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- A modern browser

### 1. Clone the Repository

```bash
git clone https://github.com/HarshJNS/yt_summarizer.git
cd yt_summarizer
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

Create `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Do not commit this file. It is already ignored by `.gitignore`.

### 5. Run the Backend

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend will run at:

```text
http://127.0.0.1:8000
```

### 6. Run the Frontend

Open a second terminal from the project root:

```bash
cd frontend
python3 -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080
```

## Frontend API Configuration

For local development, the frontend defaults to:

```text
http://localhost:8000
```

For deployment, open the frontend once with the backend URL in the `api` query parameter:

```text
https://your-frontend-domain.netlify.app/?api=https://your-backend-domain.up.railway.app
```

The frontend stores this backend URL in `localStorage` under:

```text
tubeai_api_base_url
```

## Deployment

### Backend Deployment

Recommended platforms:

- Railway
- Render
- Fly.io

General steps:

1. Create a new backend service from this GitHub repository.
2. Set the service root to `backend` if the platform asks for it.
3. Install dependencies from `backend/requirements.txt`.
4. Add the environment variable:

```env
GEMINI_API_KEY=your_production_gemini_api_key
```

5. Use this start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

If the platform does not provide `$PORT`, use the port recommended by that platform.

### Frontend Deployment

Recommended platforms:

- Netlify
- Vercel
- GitHub Pages

Because the frontend is static, deploy the `frontend/` directory. After deployment, connect it to the backend:

```text
https://your-frontend-domain.netlify.app/?api=https://your-backend-domain
```

## Security Notes

- Never commit `backend/.env`.
- Store `GEMINI_API_KEY` only in local environment files or deployment platform environment variables.
- If an API key is exposed publicly, rotate it immediately in Google AI Studio.
- CORS is currently configured with `allow_origins=["*"]` for easier demos and deployment testing. For production, restrict it to your frontend domain.
- The Gemini Python package used here, `google-generativeai`, currently works but may show a deprecation warning. A future production update should migrate to the newer Google GenAI SDK.

## Error Handling

The backend returns clear errors for common cases:

- Empty URL
- Invalid YouTube URL
- Disabled transcripts
- Missing transcripts
- Private, deleted, or unavailable videos
- Empty transcript after cleanup
- AI provider quota limits
- Invalid or missing Gemini API key

When Gemini quota is reached during summarization, the backend can return a deterministic local fallback summary so users still get a usable result.

## Known Limitations

- The app depends on YouTube captions being available.
- Some videos may not expose transcripts through the transcript API.
- Very long videos are truncated before sending to Gemini to control request size.
- The frontend is static and stores the configured backend URL in browser local storage.
- AI chat quality depends on the transcript and summary context provided to the `/chat` endpoint.

## Future Improvements

- Migrate from `google-generativeai` to the latest Google GenAI SDK.
- Add persistent user accounts and saved summaries.
- Add export formats such as PDF, Markdown, and Notion-ready blocks.
- Add transcript search and clickable timestamps.
- Add a production CORS allowlist.
- Add automated tests for URL parsing, transcript chunking, and API responses.
- Add CI/CD workflows for linting and deployment.

## Author

Built by [HarshJNS](https://github.com/HarshJNS).

