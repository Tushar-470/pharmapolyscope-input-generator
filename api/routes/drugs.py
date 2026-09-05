"""
Drug pipeline REST endpoints.
Handles structure resolution, live property calculation, Fedors/HVK decomposition, and CRUD.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Any as AnyType
from engine.structure import canonicalize_smiles, get_neutral_parent, query_pubchem_by_name_or_cid, generate_structure_svg
from engine.descriptors import compute_molecular_descriptors
from engine.group_contribution import GroupContributionEngine
from engine.thermophysical import select_melting_point, calculate_drug_tg, calculate_drug_density_and_volume
from engine.hsp import HspEngine
from engine.qc import QualityControlEngine
from engine.audit import AuditTrailEngine
from engine.sensitivity import SensitivityEngine
from engine.io_manager import IOManager

router = APIRouter(prefix="/api/drugs", tags=["drugs"])

io_mgr = IOManager()
gc_engine = GroupContributionEngine()
hsp_engine = HspEngine(gc_engine)
qc_engine = QualityControlEngine()
audit_engine = AuditTrailEngine()


class DrugCalculateRequest(BaseModel):
    name: str
    smiles: str
    tm_value_c: Optional[float] = None
    tm_value_k: Optional[float] = None
    tm_sources: Optional[List[Dict[str, Any]]] = None
    custom_groups: Optional[List[Dict[str, Any]]] = None
    bcs_class: Optional[str] = "II"
    pubchem_cid: Optional[int] = None
    lit_pycnometric_density: Optional[float] = None
    seed: Optional[int] = 42


class DrugSaveRequest(BaseModel):
    drug_id: Optional[str] = None
    name: str
    canonical_smiles: str
    tm_K: float
    tm_form: Optional[str] = "form I (stable at 25 C)"
    tm_citation: Optional[str] = "Literature"
    all_tm_sources: Optional[List[AnyType]] = None
    tg_K: float
    density_g_cm3: float
    delta_D: float
    delta_P: float
    delta_H: float
    R0: float = 7.5
    logP: float
    TPSA: float
    HBD: int
    HBA: int
    BCS_class: str = "II"
    source_citation: Optional[str] = ""
    pubchem_cid: Optional[int] = None
    formula: Optional[str] = None
    iupac_name: Optional[str] = None
    user_action_reason: Optional[str] = "Manual entry / calculation"
    force_distinct: Optional[bool] = False


@router.get("")
def list_drugs():
    """Lists all drug records in the dataset."""
    dataset = io_mgr.load_dataset()
    drugs = [r for r in dataset.get("records", []) if r.get("entity_type") == "drug"]
    return {"drugs": drugs, "count": len(drugs)}


@router.get("/search_pubchem")
@router.post("/search_pubchem")
def search_pubchem(query: str = Query(..., description="Compound name or CID")):
    """Searches PubChem for compound identity and properties."""
    data, err = query_pubchem_by_name_or_cid(query)
    if err and not data:
        return {"found": False, "message": err}
    
    svg = None
    if data and data.get("canonical_smiles"):
        svg = generate_structure_svg(data["canonical_smiles"])
        
    return {"found": True, "data": data, "svg": svg}


@router.get("/render_svg")
def render_smiles_svg(smiles: str = Query(..., description="SMILES string to render")):
    """Renders 2D depiction SVG directly from SMILES."""
    svg = generate_structure_svg(smiles)
    if not svg:
        return {"valid": False, "svg": None}
    return {"valid": True, "svg": svg}


@router.get("/{entity_id}")
def get_drug(entity_id: str):
    """Gets a specific drug record."""
    dataset = io_mgr.load_dataset()
    for r in dataset.get("records", []):
        if r.get("entity_id") == entity_id and r.get("entity_type") == "drug":
            return r
    raise HTTPException(status_code=404, detail=f"Drug with ID '{entity_id}' not found")


@router.post("/calculate")
def calculate_drug_properties(req: DrugCalculateRequest):
    """
    Executes the full frozen Pipeline A on submitted drug data.
    """
    # 1. Structure canonicalization and neutral parent
    canon_smiles, err = canonicalize_smiles(req.smiles)
    if err:
        raise HTTPException(status_code=400, detail=f"Invalid SMILES: {err}")
    parent_smiles, counter_ion, formula = get_neutral_parent(canon_smiles)
    
    # 2. Descriptors (RDKit)
    descriptors, prov_desc = compute_molecular_descriptors(parent_smiles)
    mw = descriptors["mw"]
    
    # 3. Tm selection
    if req.tm_sources:
        tm_info = select_melting_point(req.tm_sources)
        tm_k = tm_info["tm_K"]
    elif req.tm_value_k:
        tm_k = req.tm_value_k
        tm_info = {
            "tm_K": tm_k,
            "form": "stated polymorph",
            "provenance": "LITERATURE",
            "confidence": "medium",
            "uncertainty_K": 3.0,
            "all_sources": [round(tm_k - 273.15, 2)]
        }
    elif req.tm_value_c is not None:
        tm_k = round(req.tm_value_c + 273.15, 2)
        tm_info = {
            "tm_K": tm_k,
            "form": "stated polymorph",
            "provenance": "LITERATURE",
            "confidence": "medium",
            "uncertainty_K": 3.0,
            "all_sources": [req.tm_value_c]
        }
    else:
        tm_k = 350.0
        tm_info = {
            "tm_K": tm_k,
            "form": "unspecified",
            "provenance": "ESTIMATED",
            "confidence": "low",
            "uncertainty_K": 10.0,
            "all_sources": []
        }
        
    # 4. Drug Tg (0.70 * Tm)
    tg_info = calculate_drug_tg(tm_k)
    
    # 5. Group decomposition (Fedors + HVK)
    if req.custom_groups and len(req.custom_groups) > 0:
        groups = req.custom_groups
    else:
        groups = gc_engine.decompose_smiles(parent_smiles)
        
    # Fedors density & Vm
    fedors_res = gc_engine.calculate_fedors(groups, mw)
    density_info = calculate_drug_density_and_volume(mw, fedors_res["molar_volume_cm3_mol"], req.lit_pycnometric_density)
    
    # HVK HSP
    hsp_res = hsp_engine.calculate_hsp_from_groups(groups, mw, fedors_res["molar_volume_cm3_mol"])
    
    # Assemble candidate record
    candidate_record = {
        "entity_type": "drug",
        "name": req.name,
        "canonical_smiles": parent_smiles,
        "mw": mw,
        "tm_K": tm_info,
        "tg_K": tg_info,
        "density_g_cm3": density_info,
        "hsp_mpa_half": hsp_res,
        "delta_D": hsp_res["delta_D"],
        "delta_P": hsp_res["delta_P"],
        "delta_H": hsp_res["delta_H"],
        "R0": { "value": 7.5, "band": [7.0, 8.0] },
        "logP": descriptors["logP"],
        "TPSA": descriptors["TPSA"],
        "HBD": descriptors["HBD"],
        "HBA": descriptors["HBA"],
        "BCS_class": req.bcs_class,
        "provenance": {
            "tm_K": tm_info["provenance"],
            "tg_K": "CALCULATED",
            "density_g_cm3": "CALCULATED",
            "delta_D": "CALCULATED",
            "delta_P": "CALCULATED",
            "delta_H": "CALCULATED",
            "R0": "ASSUMED",
            "mw": "COMPUTED-DESCRIPTOR",
            "logP": "COMPUTED-DESCRIPTOR",
            "TPSA": "COMPUTED-DESCRIPTOR",
            "HBD": "COMPUTED-DESCRIPTOR",
            "HBA": "COMPUTED-DESCRIPTOR",
            "BCS_class": "LITERATURE"
        }
    }
    
    # 6. Quality Control run
    qc_res = qc_engine.run_drug_qc(candidate_record)
    candidate_record["qc"] = qc_res
    
    # 2D structure SVG
    svg = generate_structure_svg(parent_smiles)
    
    # Generate structured dual-value representation and 10k Monte Carlo uncertainty calculation table
    sens_engine = SensitivityEngine(seed=req.seed or 42)
    dual_rep = sens_engine.generate_dual_representation(candidate_record)
    uncertainty_table = sens_engine.compute_full_uncertainty_table(candidate_record)
    
    return {
        "calculated_record": candidate_record,
        "dual_representation": dual_rep,
        "uncertainty_table": uncertainty_table,
        "seed": req.seed or 42,
        "descriptors": descriptors,
        "groups_matched": groups,
        "fedors_breakdown": fedors_res["breakdown"],
        "hvk_breakdown": hsp_res["breakdown"],
        "qc": qc_res,
        "svg": svg
    }


@router.post("/save")
def save_drug(req: DrugSaveRequest):
    """Saves or updates a drug record in the dataset."""
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    
    # Check for duplicate record if creating new record (no drug_id provided and force_distinct is False)
    if not req.drug_id and not req.force_distinct:
        for r in records:
            if r.get("entity_type") == "drug":
                if (r.get("canonical_smiles") and r.get("canonical_smiles") == req.canonical_smiles) or (r.get("name", "").lower() == req.name.lower()):
                    return {
                        "duplicate_detected": True,
                        "message": f"DUPLICATE RECORD DETECTED: An existing record for {r.get('name')} already exists as {r.get('entity_id')}.",
                        "existing_record": r,
                        "options": [
                            "Open existing record",
                            "Create intentionally distinct version",
                            "Cancel"
                        ]
                    }
    
    # Generate new ID if not provided
    if not req.drug_id:
        existing_drug_ids = [int(r["entity_id"].split("-")[1]) for r in records if r.get("entity_type") == "drug" and "-" in r.get("entity_id", "")]
        next_num = max(existing_drug_ids, default=0) + 1
        drug_id = f"DRG-{next_num:04d}"
    else:
        drug_id = req.drug_id
        
    # Build complete record
    record = {
        "entity_id": drug_id,
        "entity_type": "drug",
        "name": req.name,
        "abbreviation": None,
        "canonical_smiles": req.canonical_smiles,
        "repeat_unit_smiles": None,
        "structure": {
            "pubchem_cid": req.pubchem_cid,
            "iupac_name": req.iupac_name,
            "formula": req.formula,
            "neutral_parent": True
        },
        "mn": None,
        "mw": round(compute_molecular_descriptors(req.canonical_smiles)[0]["mw"], 2),
        "tm_K": {
            "value": req.tm_K,
            "form": req.tm_form,
            "convention": "DSC onset, primary source selected by Table 4-1 rule",
            "all_sources": req.all_tm_sources or [req.tm_K - 273.15]
        },
        "tg_K": {
            "value": req.tg_K,
            "method_id": "TG-RATIO-01",
            "equation": "0.70 * Tm",
            "uncertainty_K": 21.0
        },
        "density_g_cm3": {
            "value": req.density_g_cm3,
            "state": "Fedors liquid-state surrogate for crystalline field"
        },
        "hsp_mpa_half": {
            "delta_D": req.delta_D,
            "delta_P": req.delta_P,
            "delta_H": req.delta_H,
            "primary_total": round((req.delta_D**2 + req.delta_P**2 + req.delta_H**2)**0.5, 2),
            "method_id": "HSP-HVK-01"
        },
        "R0": { "value": req.R0, "band": [7.0, 8.0] },
        "logP": {
            "primary": req.logP,
            "primary_algorithm": "RDKit Crippen"
        },
        "TPSA": req.TPSA,
        "HBD": req.HBD,
        "HBA": req.HBA,
        "BCS_class": req.BCS_class,
        "provenance": {
            "tm_K": "LITERATURE",
            "tg_K": "CALCULATED",
            "density_g_cm3": "CALCULATED",
            "delta_D": "CALCULATED",
            "delta_P": "CALCULATED",
            "delta_H": "CALCULATED",
            "R0": "ASSUMED",
            "mw": "COMPUTED-DESCRIPTOR",
            "logP": "COMPUTED-DESCRIPTOR",
            "TPSA": "COMPUTED-DESCRIPTOR",
            "HBD": "COMPUTED-DESCRIPTOR",
            "HBA": "COMPUTED-DESCRIPTOR",
            "BCS_class": "LITERATURE"
        },
        "source": req.source_citation or "Standardized Input Generator pipeline",
        "method": ["TG-RATIO-01", "HSP-HVK-01", "DENS-FEDORS-01", "DESC-RDKIT-01"],
        "algorithm": "Hoftyzer-van Krevelen group tables; Fedors 1974 constants; RDKit Crippen/Ertl/Lipinski",
        "confidence": "medium",
        "uncertainty": {
            "tg_K": "+/- 21 K (1-sigma)",
            "density": "approx. 5 percent vs pycnometry",
            "hsp_components": "approx. 1.5 MPa^0.5"
        },
        "calculation_date": "2026-09-01",
        "software_version": "input-generator/1.0"
    }
    
    # Run QC
    qc_res = qc_engine.run_drug_qc(record)
    record["qc"] = qc_res
    
    # Update or insert in dataset
    existing_idx = None
    for i, r in enumerate(records):
        if r.get("entity_id") == drug_id:
            existing_idx = i
            break
            
    action = "RECORD_UPDATED" if existing_idx is not None else "RECORD_CREATED"
    if existing_idx is not None:
        records[existing_idx] = record
    else:
        records.append(record)
        
    dataset["records"] = records
    io_mgr.save_dataset(dataset)
    
    # Audit log
    audit_engine.log_event(
        entity_id=drug_id,
        entity_name=req.name,
        action=action,
        reason=req.user_action_reason or "User drug record save"
    )
    
    return {"success": True, "duplicate_detected": False, "entity_id": drug_id, "qc": qc_res, "record": record}


@router.delete("/{entity_id}")
def delete_drug(entity_id: str):
    """Deletes a drug record from the dataset."""
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    initial_len = len(records)
    records = [r for r in records if r.get("entity_id") != entity_id]
    if len(records) == initial_len:
        raise HTTPException(status_code=404, detail=f"Drug '{entity_id}' not found")
        
    dataset["records"] = records
    io_mgr.save_dataset(dataset)
    audit_engine.log_event(
        entity_id=entity_id,
        entity_name=entity_id,
        action="RECORD_DELETED",
        reason="User deleted drug record"
    )
    return {"success": True, "message": f"Drug {entity_id} deleted"}
