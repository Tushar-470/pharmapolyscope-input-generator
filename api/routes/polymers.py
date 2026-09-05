"""
Polymer pipeline REST endpoints.
Handles grade identification, curated repeat units, composition weighting, and CRUD.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from engine.polymer_pipeline import PolymerPipelineEngine
from engine.qc import QualityControlEngine
from engine.audit import AuditTrailEngine
from engine.sensitivity import SensitivityEngine
from engine.io_manager import IOManager
from engine.structure import query_pubchem_by_name_or_cid, generate_structure_svg

router = APIRouter(prefix="/api/polymers", tags=["polymers"])

poly_engine = PolymerPipelineEngine()
qc_engine = QualityControlEngine()
audit_engine = AuditTrailEngine()
io_mgr = IOManager()


class PolymerCalculateRequest(BaseModel):
    name: str
    repeat_unit_smiles: str
    tg_value_k: Optional[float] = None
    tg_value_c: Optional[float] = None
    density_g_cm3: Optional[float] = 0.40
    grade_name: Optional[str] = None
    seed: Optional[int] = 42


class PolymerSaveRequest(BaseModel):
    name: Optional[str] = None
    grade_name: Optional[str] = "Standard"
    repeat_unit_smiles: Optional[str] = None
    carrier_name: Optional[str] = None
    polymer_id: Optional[str] = None
    tg_value_k: Optional[float] = None
    tg_value_c: Optional[float] = None
    custom_bulk_density: Optional[float] = 0.40
    custom_mn: Optional[str] = None
    user_action_reason: Optional[str] = None
    force_distinct: Optional[bool] = False


@router.get("")
def list_polymers():
    """Lists all polymer records in the data store."""
    dataset = io_mgr.load_dataset()
    polymers = [r for r in dataset.get("records", []) if r.get("entity_type") == "polymer"]
    return {"polymers": polymers, "count": len(polymers)}


@router.get("/search_pubchem")
@router.post("/search_pubchem")
def search_polymer_pubchem(query: str = Query(..., description="Polymer name, monomer, or CID")):
    """Searches PubChem for polymer/monomer chemical identity and properties."""
    data, err = query_pubchem_by_name_or_cid(query)
    if err and not data:
        return {"found": False, "message": err}
    
    svg = None
    if data and data.get("canonical_smiles"):
        svg = generate_structure_svg(data["canonical_smiles"])
        
    return {"found": True, "data": data, "svg": svg}


@router.get("/curated_carriers")
def list_curated_carriers():
    """Returns curated library of pharmaceutical polymer carriers and grades."""
    return {"carriers": poly_engine.list_available_carriers()}


@router.get("/grade_info")
def get_grade_info(carrier: str, grade: str):
    """Retrieves detailed curated specs for a specific carrier and grade."""
    info = poly_engine.get_carrier_grade(carrier, grade)
    if not info:
        raise HTTPException(status_code=404, detail=f"Carrier '{carrier}' grade '{grade}' not found")
    return info


@router.post("/calculate")
def calculate_polymer(req: PolymerCalculateRequest):
    """Calculates properties and 10k Monte Carlo UQ for any custom or preset polymer."""
    tg_k = req.tg_value_k
    if tg_k is None and req.tg_value_c is not None:
        tg_k = round(req.tg_value_c + 273.15, 2)
        
    record = poly_engine.calculate_custom_polymer_record(
        name=req.name,
        repeat_unit_smiles=req.repeat_unit_smiles,
        tg_K=tg_k,
        density_g_cm3=req.density_g_cm3 or 0.40,
        grade_name=req.grade_name
    )
    
    sens_engine = SensitivityEngine(seed=req.seed or 42)
    dual_rep = sens_engine.generate_dual_representation(record)
    uncertainty_table = sens_engine.compute_full_uncertainty_table(record)
    
    return {
        "calculated_record": record,
        "dual_representation": dual_rep,
        "uncertainty_table": uncertainty_table,
        "seed": req.seed or 42
    }


@router.post("/preview_grade")
def preview_polymer_grade(carrier: str, grade: str, bulk_density: Optional[float] = None, mn: Optional[str] = None, seed: Optional[int] = 42):
    """Generates a live preview record for a selected polymer grade."""
    try:
        record = poly_engine.calculate_polymer_record(carrier, grade, custom_bulk_density=bulk_density, custom_mn=mn)
        sens_engine = SensitivityEngine(seed=seed or 42)
        uncertainty_table = sens_engine.compute_full_uncertainty_table(record)
        dual_rep = sens_engine.generate_dual_representation(record)
        
        return {"preview_record": record, "dual_representation": dual_rep, "uncertainty_table": uncertainty_table}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/save")
def save_polymer(req: PolymerSaveRequest):
    """Saves or updates a polymer record in the dataset."""
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    
    poly_name = req.name or req.carrier_name or "Custom Polymer"
    grade_name = req.grade_name or "Standard"
    carrier_lookup = req.carrier_name or req.name or ""
    
    # Check for duplicate record if creating new record
    if not req.polymer_id and not req.force_distinct:
        for r in records:
            if r.get("entity_type") == "polymer":
                r_grade = r.get("grade", {})
                r_carrier = r_grade.get("carrier") if isinstance(r_grade, dict) else None
                r_grade_name = r_grade.get("grade") if isinstance(r_grade, dict) else None
                r_name = r.get("name", "").lower()
                
                is_carrier_match = (r_carrier and carrier_lookup and r_carrier.lower() == carrier_lookup.lower()) or (carrier_lookup and carrier_lookup.lower() in r_name)
                is_grade_match = (r_grade_name and r_grade_name.lower() == grade_name.lower()) or (r.get("abbreviation", "").lower() == grade_name.lower())
                
                if is_carrier_match and is_grade_match:
                    return {
                        "duplicate_detected": True,
                        "message": f"DUPLICATE RECORD DETECTED: An existing record for {r.get('name')} ({r.get('abbreviation') or grade_name}) already exists as {r.get('entity_id')}.",
                        "existing_record": r,
                        "options": [
                            "Open existing record",
                            "Create intentionally distinct version",
                            "Cancel"
                        ]
                    }
    
    if not req.polymer_id:
        existing_poly_ids = [int(r["entity_id"].split("-")[1]) for r in records if r.get("entity_type") == "polymer" and "-" in r.get("entity_id", "")]
        next_num = max(existing_poly_ids, default=0) + 1
        poly_id = f"POL-{next_num:04d}"
    else:
        poly_id = req.polymer_id
        
    try:
        if req.carrier_name and poly_engine.get_carrier_grade(req.carrier_name, grade_name):
            record = poly_engine.calculate_polymer_record(
                req.carrier_name,
                grade_name,
                entity_id=poly_id,
                custom_bulk_density=req.custom_bulk_density,
                custom_mn=req.custom_mn
            )
        else:
            tg_k = req.tg_value_k
            if tg_k is None and req.tg_value_c is not None:
                tg_k = round(req.tg_value_c + 273.15, 2)
            record = poly_engine.calculate_custom_polymer_record(
                name=poly_name,
                repeat_unit_smiles=req.repeat_unit_smiles or "*CC(*)*",
                tg_K=tg_k,
                density_g_cm3=req.custom_bulk_density,
                entity_id=poly_id,
                grade_name=grade_name
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    existing_idx = None
    for i, r in enumerate(records):
        if r.get("entity_id") == poly_id:
            existing_idx = i
            break
            
    action = "RECORD_UPDATED" if existing_idx is not None else "RECORD_CREATED"
    if existing_idx is not None:
        records[existing_idx] = record
    else:
        records.append(record)
        
    dataset["records"] = records
    io_mgr.save_dataset(dataset)
    
    audit_engine.log_event(
        entity_id=poly_id,
        entity_name=f"{poly_name} ({grade_name})",
        action=action,
        reason=req.user_action_reason or "User polymer record save"
    )
    
    return {"success": True, "duplicate_detected": False, "entity_id": poly_id, "record": record}


@router.delete("/{entity_id}")
def delete_polymer(entity_id: str):
    """Deletes a polymer record from the dataset."""
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    initial_len = len(records)
    records = [r for r in records if r.get("entity_id") != entity_id]
    if len(records) == initial_len:
        raise HTTPException(status_code=404, detail=f"Polymer '{entity_id}' not found")
        
    dataset["records"] = records
    io_mgr.save_dataset(dataset)
    audit_engine.log_event(
        entity_id=entity_id,
        entity_name=entity_id,
        action="RECORD_DELETED",
        reason="User deleted polymer record"
    )
    return {"success": True, "message": f"Polymer {entity_id} deleted"}
