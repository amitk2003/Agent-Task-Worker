"""
Main FastAPI Application Entrypoint.

Starts the server, configures CORS middleware, loads routers,
and provides a health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="Autonomous AI Task Worker API",
    description="Autonomous Agent runtime demonstrating goal decomposition, tool execution, failure recovery, and verification.",
    version="1.0.0",
)

# Configure CORS for local development with React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agent-task-worker.onrender.com","http://localhost:5173"],  # Allows Vite dev server on any port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

storage_path = Path(__file__).parent / "storage"
storage_path.mkdir(exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "model": settings.groq_model,
        "groq_api_key_configured": bool(settings.groq_api_key),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
