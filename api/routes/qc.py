"""
QC battery dashboard and inspection REST endpoints.
"""

from fastapi import APIRouter
from engine.qc import QualityControlEngine
from engine.io_manager import IOManager

router = APIRouter(prefix="/api/qc", tags=["qc"])

io_mgr = IOManager()
qc_engine = QualityControlEngine()


@router.get("/summary")
def get_qc_summary():
    """
    Returns dashboard overview metrics, complete/incomplete counts, QC flags, and borderline records.
    """
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    
    drugs = [r for r in records if r.get("entity_type") == "drug"]
    polymers = [r for r in records if r.get("entity_type") == "polymer"]
    
    approved_count = 0
    approved_flags_count = 0
    rejected_count = 0
    
    all_warnings = []
    
    for r in records:
        qc = r.get("qc", {})
        status = qc.get("status", "APPROVED")
        if status == "APPROVED":
            approved_count += 1
        elif "flags" in status.lower():
            approved_flags_count += 1
        else:
            rejected_count += 1
            
        for w in qc.get("warnings", []):
            all_warnings.append({"entity_id": r.get("entity_id"), "name": r.get("name"), "warning": w})
            
    return {
        "generator_version": dataset.get("generator_version", "input-generator/1.0"),
        "schema_version": dataset.get("schema_version", "1.0"),
        "total_records": len(records),
        "total_drugs": len(drugs),
        "total_polymers": len(polymers),
        "approved_records": approved_count,
        "approved_with_flags": approved_flags_count,
        "rejected_records": rejected_count,
        "qc_warnings": all_warnings,
        "active_methods": [
            {"id": "TG-RATIO-01", "name": "Tg = 0.70*Tm (drugs, +/- 21 K)"},
            {"id": "DENS-FEDORS-01", "name": "Fedors group molar volume & density"},
            {"id": "HSP-HVK-01", "name": "Hoftyzer-van Krevelen HSP (primary)"},
            {"id": "R0-SCREEN-01", "name": "R0 = 7.5 MPa^0.5 (band 7.0-8.0, assumed)"},
            {"id": "DESC-RDKIT-01", "name": "RDKit MolWt/LogP/TPSA/HBD/HBA"},
            {"id": "LIT-ACQ-01", "name": "Deterministic Tm literature hierarchy"},
            {"id": "LIT-ACQ-02", "name": "Polymer grade literature & vendor acquisition"}
        ]
    }


@router.post("/run_all")
def run_all_qc():
    """Re-evaluates QC checks across all stored records and updates dataset."""
    dataset = io_mgr.load_dataset()
    records = dataset.get("records", [])
    
    for r in records:
        if r.get("entity_type") == "drug":
            r["qc"] = qc_engine.run_drug_qc(r)
        else:
            r["qc"] = qc_engine.run_polymer_qc(r)
            
    dataset["records"] = records
    io_mgr.save_dataset(dataset)
    return {"success": True, "records_validated": len(records), "dataset": dataset}
