"""
Phylax Server - Main FastAPI Application

Purpose:
- Expose traces via HTTP
- Support replay and comparison
- Provide OpenAI-compatible endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from server.routes import traces, replay, chat

# Create FastAPI app
app = FastAPI(
    title="Phylax",
    description="Developer-first local LLM tracing, replay & debugging system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(traces.router, prefix="/v1", tags=["traces"])
app.include_router(replay.router, prefix="/v1", tags=["replay"])
app.include_router(chat.router, prefix="/v1", tags=["chat"])

# Mount static files for UI
ui_path = Path(__file__).parent.parent / "ui"
if ui_path.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_path), html=True), name="ui")

# Mount assets folder for logo/favicon
assets_path = Path(__file__).parent.parent / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Phylax",
        "version": "1.0.0",
        "description": "Developer-first local LLM tracing, replay & debugging system",
        "docs": "/docs",
        "ui": "/ui",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
