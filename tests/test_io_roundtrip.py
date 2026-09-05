"""
Tests for single-pass JSON and CSV I/O roundtrip fidelity.
"""

import os
import pytest
from engine.io_manager import IOManager


def test_json_load_and_sheet_generation():
    io_mgr = IOManager()
    data = io_mgr.load_dataset()
    assert data["schema_version"] == "1.0"
    assert len(data["records"]) >= 2
    
    # Generate ready sheets
    drg_sheet = io_mgr.generate_pharmapolyscope_ready_sheet("DRG-0001")
    assert drg_sheet["entity_id"] == "DRG-0001"
    assert any(f["label"].startswith("Molecular Weight") for f in drg_sheet["fields"])
    
    pol_sheet = io_mgr.generate_pharmapolyscope_ready_sheet("POL-0001")
    assert pol_sheet["entity_id"] == "POL-0001"
    assert any(f["label"].startswith("Glass Transition") for f in pol_sheet["fields"])


def test_csv_sync_and_structure():
    io_mgr = IOManager()
    data = io_mgr.load_dataset()
    io_mgr.export_csv_from_json(data)
    
    assert os.path.exists(io_mgr.csv_path)
    with open(io_mgr.csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    assert len(lines) >= 3  # Header + 2 rows
    assert lines[0].startswith("entity_id,entity_type,name")
    assert "DRG-0001" in lines[1]
    assert "POL-0001" in lines[2]
