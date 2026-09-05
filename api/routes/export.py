"""
Export and Import API routes for JSON, CSV, and Pharmapolyscope-ready manual entry sheets.
"""

import os
import json
from fastapi import APIRouter, HTTPException, Response
from engine.io_manager import IOManager

router = APIRouter(prefix="/api/export", tags=["export"])

io_mgr = IOManager()


@router.get("/pharmapolyscope_ready/{entity_id}")
def get_pharmapolyscope_ready_sheet(entity_id: str):
    """
    Returns the clean, dedicated summary sheet of values and units
    for manual transcription into Pharmapolyscope.
    """
    try:
        sheet = io_mgr.generate_pharmapolyscope_ready_sheet(entity_id)
        return sheet
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/csv")
def download_csv():
    """Streams the current input_dataset.csv file."""
    if not os.path.exists(io_mgr.csv_path):
        data = io_mgr.load_dataset()
        io_mgr.export_csv_from_json(data)
        
    with open(io_mgr.csv_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=input_dataset.csv"}
    )


@router.get("/json")
def download_json():
    """Streams the current input_dataset.json file."""
    data = io_mgr.load_dataset()
    content = json.dumps(data, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=input_dataset.json"}
    )
