from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Hacker Cyber Deception Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"

if (dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(dist / "assets")), name="assets")


@app.get("/{full_path:path}")
def serve_hacker_app(full_path: str):
    if full_path:
        f = dist / full_path
        if f.is_file():
            return FileResponse(f)
    return FileResponse(dist / "index.hacker.html")


if __name__ == "__main__":
    print("[HACKER DASHBOARD] Starting Hacker Adversary Dashboard on http://localhost:3001")
    uvicorn.run(app, host="0.0.0.0", port=3001, log_level="info")
