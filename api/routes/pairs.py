"""
Drug-Polymer Pair Screening and Sensitivity REST endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from engine.pair_metrics import evaluate_drug_polymer_pair
from engine.sensitivity import SensitivityEngine
from engine.io_manager import IOManager

router = APIRouter(prefix="/api/pairs", tags=["pairs"])

io_mgr = IOManager()
sens_engine = SensitivityEngine()


class PairScreenRequest(BaseModel):
    drug_id: str
    polymer_id: str
    r0_assigned: float = 7.5


class ResamplingRequest(BaseModel):
    drug_id: str
    polymer_id: str
    r0_assigned: float = 7.5
    n_samples: int = 10000


@router.get("/matrix")
def get_screening_matrix():
    """
    Computes pair miscibility metrics across ALL saved drugs and polymers in the dataset.
    """
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    
    drugs = [r for r in records if r.get("entity_type") == "drug"]
    polymers = [r for r in records if r.get("entity_type") == "polymer"]
    
    matrix = []
    borderline_pairs = []
    
    for d in drugs:
        d_row = {"drug_id": d["entity_id"], "drug_name": d["name"], "pairs": []}
        for p in polymers:
            pair_res = evaluate_drug_polymer_pair(d, p)
            d_row["pairs"].append(pair_res)
            if pair_res["borderline_flag"]:
                borderline_pairs.append({
                    "pair": [d["entity_id"], p["entity_id"]],
                    "drug_name": d["name"],
                    "polymer_name": p.get("abbreviation") or p["name"],
                    "Ra": pair_res["hansen_distance_Ra"],
                    "RED_7_5": pair_res["RED_at_7_5"],
                    "greenhalgh_delta_t": pair_res["greenhalgh_delta_t_tabulated"],
                    "notes": pair_res["qc_notes"]
                })
        matrix.append(d_row)
        
    return {
        "drug_count": len(drugs),
        "polymer_count": len(polymers),
        "total_pairs": len(drugs) * len(polymers),
        "matrix": matrix,
        "borderline_pairs": borderline_pairs
    }


@router.post("/screen_pair")
def screen_pair(req: PairScreenRequest):
    """Screens a single specific drug-polymer pair."""
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    
    matching_drug = [r for r in records if r.get("entity_id") == req.drug_id]
    matching_poly = [r for r in records if r.get("entity_id") == req.polymer_id]
    
    if not matching_drug:
        raise HTTPException(status_code=404, detail=f"Drug '{req.drug_id}' not found")
    if not matching_poly:
        raise HTTPException(status_code=404, detail=f"Polymer '{req.polymer_id}' not found")
        
    res = evaluate_drug_polymer_pair(matching_drug[0], matching_poly[0], req.r0_assigned)
    return res


@router.post("/resampling_sensitivity")
def resampling_sensitivity(req: ResamplingRequest):
    """Executes Monte Carlo HSP resampling sensitivity test on a drug-polymer pair."""
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    
    matching_drug = [r for r in records if r.get("entity_id") == req.drug_id]
    matching_poly = [r for r in records if r.get("entity_id") == req.polymer_id]
    
    if not matching_drug:
        raise HTTPException(status_code=404, detail=f"Drug '{req.drug_id}' not found")
    if not matching_poly:
        raise HTTPException(status_code=404, detail=f"Polymer '{req.polymer_id}' not found")
        
    d_hsp = matching_drug[0].get("hsp_mpa_half", {})
    p_hsp = matching_poly[0].get("hsp_mpa_half", {})
    
    res = sens_engine.analyze_hsp_resampling(d_hsp, p_hsp, req.r0_assigned, req.n_samples)
    return res
