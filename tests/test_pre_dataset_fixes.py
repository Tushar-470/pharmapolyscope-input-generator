"""
Regression tests for Pre-Dataset UI and Data Integrity Fixes.
Validates duplicate detection, object-valued field rendering, status counts, and ready sheet formatting.
"""

import pytest
from api.routes.polymers import save_polymer, PolymerSaveRequest
from api.routes.drugs import save_drug, DrugSaveRequest
from api.routes.qc import get_qc_summary
from engine.io_manager import IOManager
from engine.qc import QualityControlEngine


def test_polymer_duplicate_detection():
    """Validates that submitting an existing polymer carrier/grade triggers duplicate detection."""
    io_mgr = IOManager()
    data = io_mgr.load_dataset()
    has_pol = any(r.get("entity_type") == "polymer" for r in data.get("records", []))
    if not has_pol:
        pytest.skip("No polymers in database; skipping duplicate detection until polymers are added.")
        
    req = PolymerSaveRequest(
        carrier_name="povidone",
        grade_name="K30",
        custom_bulk_density=0.40,
        force_distinct=False
    )
    result = save_polymer(req)
    assert result["duplicate_detected"] is True
    assert "DUPLICATE RECORD DETECTED" in result["message"]
    assert result["existing_record"]["entity_id"] == "POL-0001"


def test_drug_duplicate_detection():
    """Validates that submitting an existing drug SMILES triggers duplicate detection."""
    req = DrugSaveRequest(
        name="ibuprofen",
        canonical_smiles="CC(C)Cc1ccc(C(C)C(=O)O)cc1",
        tm_K=349.15,
        tg_K=244.4,
        density_g_cm3=1.055,
        delta_D=17.85,
        delta_P=2.22,
        delta_H=7.15,
        logP=3.07,
        TPSA=37.3,
        HBD=1,
        HBA=2,
        force_distinct=False
    )
    result = save_drug(req)
    assert result["duplicate_detected"] is True
    assert "DUPLICATE RECORD DETECTED" in result["message"]
    assert result["existing_record"]["entity_id"] == "DRG-0001"


def test_dashboard_status_counts():
    """Validates dashboard summary counting logic."""
    data = get_qc_summary()
    assert data["total_records"] >= 2
    assert data["total_drugs"] >= 1
    assert data["total_polymers"] >= 0
    assert data["approved_records"] >= 1
    assert data["rejected_records"] == 0



def test_polymer_manual_entry_sheet_rendering():
    """Validates that polymer manual-entry sheet renders verified notes or numerical values."""
    io_mgr = IOManager()
    data = io_mgr.load_dataset()
    has_pol = any(r.get("entity_id") == "POL-0001" for r in data.get("records", []))
    if not has_pol:
        pytest.skip("POL-0001 not in database; skipping until polymers are added.")
        
    sheet = io_mgr.generate_pharmapolyscope_ready_sheet("POL-0001")
    assert sheet["entity_id"] == "POL-0001"
    
    fields_map = {f["label"]: f for f in sheet["fields"]}
    
    # Check Mn
    assert "Number-Average Molar Mass (Mn)" in fields_map
    mn_field = fields_map["Number-Average Molar Mass (Mn)"]
    assert mn_field["value"] == "VALUE REQUIRES VERIFIED GRADE-SPECIFIC INPUT"
    assert mn_field["provenance"] == "MANUFACTURER-SPEC"
    
    # Check Density
    assert "Bulk Density" in fields_map
    dens_field = fields_map["Bulk Density"]
    assert dens_field["value"] == "VALUE REQUIRES VERIFIED GRADE-SPECIFIC INPUT"
    assert dens_field["provenance"] == "MANUFACTURER-SPEC"
    
    # Check Tg
    assert "Glass Transition Temperature (Tg)" in fields_map
    tg_field = fields_map["Glass Transition Temperature (Tg)"]
    assert tg_field["value"] == 426.8
    assert "LITERATURE" in tg_field["provenance"]
    assert "CALCULATED" not in tg_field["provenance"]


def test_drug_manual_entry_sheet_rendering():
    """Validates that drug manual-entry sheet renders all exact values."""
    io_mgr = IOManager()
    sheet = io_mgr.generate_pharmapolyscope_ready_sheet("DRG-0001")
    assert sheet["entity_id"] == "DRG-0001"
    
    fields_map = {f["label"]: f for f in sheet["fields"]}
    assert fields_map["Molecular Weight (MW)"]["value"] == 206.28
    assert fields_map["Melting Temperature (Tm)"]["value"] == 349.15
    assert fields_map["Glass Transition Temperature (Tg)"]["value"] == 244.4
    assert fields_map["Glass Transition Temperature (Tg)"]["provenance"] == "CALCULATED (0.70*Tm +/- 21 K)"
    assert fields_map["Crystalline Density"]["value"] == 1.055
    assert fields_map["Hansen Dispersion (δD)"]["value"] == 17.85
    assert fields_map["Hansen Polar (δP)"]["value"] == 2.22
    assert fields_map["Hansen Hydrogen-Bonding (δH)"]["value"] == 7.15
    assert fields_map["Interaction Radius (R0)"]["value"] == 7.5
