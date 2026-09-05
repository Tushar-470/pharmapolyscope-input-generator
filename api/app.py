"""
Main FastAPI application for Pharmapolyscope Physicochemical Input Generator.
Serves REST APIs and the static scientific user interface.
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routes import drugs, polymers, qc, export, audit

app = FastAPI(
    title="Pharmapolyscope Physicochemical Input Generator",
    version="1.0.0",
    description="Independent upstream physicochemical input generation application for Pharmapolyscope"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(drugs.router)
app.include_router(polymers.router)
app.include_router(qc.router)
app.include_router(export.router)
app.include_router(audit.router)

# Mount static UI directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ui_dir = os.path.join(base_dir, "ui")

if os.path.exists(ui_dir):
    app.mount("/static", StaticFiles(directory=ui_dir), name="static")

@app.get("/")
def serve_ui():
    """Serves the main application UI."""
    index_path = os.path.join(ui_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "running", "docs_url": "/docs"}
