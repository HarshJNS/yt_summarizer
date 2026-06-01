from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.responses import FileResponse

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app as backend_app

app = FastAPI(title="TubeAI Summarizer Vercel App")
app.mount("/api", backend_app)


@app.get("/")
def serve_frontend():
    return FileResponse(ROOT_DIR / "public" / "index.html")
