# TubeAI Summarizer 📺🤖

An AI-powered web application that takes any YouTube video URL, extracts its transcript, cleanses it of filler words, chunks the text, and feeds it into the Gemini AI API to return structured summaries, study guides, productivity steps, business details, and raw transcripts in a premium, dark-themed ChatGPT/Notion style dashboard.

---

## Folder Structure

```text
youtube-summarizer/
  backend/
    main.py         ← FastAPI server, CORS configuration, URL parsing
    summarizer.py   ← Gemini API interface, chunk joining, JSON response schema
    transcript.py   ← youtube-transcript-api wrapper, filler word removal, error handling
    chunker.py      ← Paragraph-aware text partitioner (limits blocks to 8k chars)
    requirements.txt← Server dependencies
    .env            ← API configuration file (contains GEMINI_API_KEY)
  frontend/
    index.html      ← Single-file responsive HTML, Tailwind CSS, & JavaScript dashboard
  README.md         ← Project documentation
```

---

## Local Setup & Installation

Follow these steps to run the application locally on your machine.

### Prerequisites
- **Python 3.8+** installed on your system.
- A web browser.
- A **Gemini API Key** (Get one at [Google AI Studio](https://aistudio.google.com/app/apikey)).

### Step 1: Clone or Open the Project
Ensure you are in the project root directory (`yt_summarizer`):
```bash
cd yt_summarizer
```

### Step 2: Set Up Environment Variables
1. Navigate to the `backend/` folder.
2. Open the `.env` file.
3. Fill in your API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```

### Step 3: Install Backend Dependencies
It is recommended to use a virtual environment, but you can also install the dependencies directly:
```bash
# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r backend/requirements.txt
```

---

## Running the Application

### 1. Run the Backend Server
Start the FastAPI server using Uvicorn. Run this command from the `backend/` directory:
```bash
cd backend
uvicorn main:app --reload --port 8000
```
This will start the API server at `http://localhost:8000`. Leave this terminal tab running.

### 2. Open the Frontend
Since the frontend is a single `index.html` file, you do not need to build it or run an `npm` server. Simply open it directly:
- On macOS, run:
  ```bash
  open frontend/index.html
  ```
- Or just find the `frontend/index.html` file in your system finder/explorer and double-click it to open it in Google Chrome, Safari, Firefox, or Edge.

---

## Features & Modes

- **Video Player Integration**: View the embedded video side-by-side with your transcripts and notes.
- **Micro-Insight Cards**: Dedicated sections extract key insights (with lightbulb indicators), actionable takeaways (numbered items), and quick bullets.
- **Flexible Analysis Modes**:
  - **🎓 Study Mode**: Educational breakdowns, terminology definitions, and core concepts.
  - **⚡ Productivity Mode**: Time-saving workflow improvements, hacks, and efficiency summaries.
  - **💼 Business Mode**: Monetization strategies, business plans, and market insights.
  - **✨ ELI5 Mode**: "Explain Like I'm 5" - zero-jargon simplicity.
- **Text Export Utilities**:
  - **Copy Summary**: Copies a formatted report (with icons and bold headers) ready to paste into Slack, Notion, or Discord.
  - **Download Summary**: Downloads a `.txt` file containing the summaries of all active modules for offline reference.

---

## Deployment Instructions

### Backend (FastAPI) Deployment (e.g. Railway)
1. Sign up/log in on [Railway.app](https://railway.app/).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your repository.
4. Under variables, add:
   - `GEMINI_API_KEY`: `your_actual_api_key`
5. Railway will automatically detect the Python environment, install `requirements.txt`, and deploy the server.
6. Note down the deployment domain (e.g., `https://your-api.up.railway.app`).

### Frontend Deployment (e.g. Netlify)
1. Log in to [Netlify](https://www.netlify.com/).
2. Drag and drop the `frontend/` folder into the Netlify deployment UI.
3. Open the deployed frontend once with your backend URL in the `api` query parameter:
   ```text
   https://your-frontend.netlify.app/?api=https://your-api.up.railway.app
   ```
   The frontend stores this backend URL in browser local storage for future visits.
4. Netlify will deploy your static page in seconds.

---

## Troubleshooting Common Errors

### 1. `CORS Blocked (Silent Fail)`
- **Problem**: The frontend is open, but hitting "Summarize" returns immediately or console logs a CORS error.
- **Fix**: The FastAPI server automatically has `CORSMiddleware` configured with `allow_origins=["*"]`. Ensure that the backend is running on `http://localhost:8000` and that the port matches exactly. If you changed the backend port, update the `fetch()` domain in the `<script>` tag inside `frontend/index.html`.

### 2. `Transcripts are disabled or not available for this video`
- **Problem**: The error card displays saying transcripts are disabled.
- **Reason**: The video either has transcripts explicitly turned off by the creator, is auto-generated by YouTube but has not finished processing, or uses an unsupported language.
- **Fix**: Try a popular video, or one where you can click the `[CC]` button on YouTube to confirm subtitles are active.

### 3. `API key is not set`
- **Problem**: The API returns a 400 error indicating the API key is empty.
- **Fix**: Double check that your `backend/.env` file contains your API key correctly configured. The server will dynamically load the changes on the next request.
