"""Nutrition Planner -- FastAPI app.

Serves the JSON API under /api and the compiled Vite frontend at /.
"""
import os

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_logger, log_startup_config
from routers import chat, health, phases, profile

logger = get_logger(__name__)

log_startup_config()

app = FastAPI(title="Nutrition Planner", docs_url="/api/docs")

# --- API routes (must be registered before the static mount) ----------------
app.include_router(health.router, prefix="/api")
app.include_router(phases.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(profile.router, prefix="/api")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log the stack only -- never request headers or tokens.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# --- static frontend ---------------------------------------------------------
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC_DIR):
    _INDEX = os.path.join(_STATIC_DIR, "index.html")

    # SPA deep-link fallback: any non-/api path that StaticFiles 404s falls back
    # to index.html so client-side routes survive refresh/bookmark.
    @app.exception_handler(404)
    async def spa_fallback(request: Request, exc):
        if request.url.path.startswith("/api"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return FileResponse(_INDEX)

    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
else:  # frontend not built yet (e.g. backend-only local run / tests)
    logger.warning("static/ not found at %s -- frontend not mounted", _STATIC_DIR)

    @app.get("/")
    def _no_frontend():
        return {"detail": "frontend not built; run scripts/build.sh"}
