"""
Test Suite for High-Precision Scientific QC Diagnostics 2.0.
Validates case-specific rule triggers, quantitative deltas, chemical motif tagging, and remediation paths.
"""

import pytest
from engine.qc import QualityControlEngine
from engine.polymer_pipeline import PolymerPipelineEngine
from api.routes.drugs import calculate_drug_properties, DrugCalculateRequest


def test_qc_clean_pass_paracetamol():
    """Validates that a canonical, unflagged drug receives APPROVED with a clean pass diagnostic."""
    qc = QualityControlEngine()
    req = DrugCalculateRequest(
        name="Paracetamol",
        smiles="CC(=O)NC1=CC=C(C=C1)O",
        tm_value_k=442.15,
        bcs_class="I",
        pubchem_cid=1983
    )
    res = calculate_drug_properties(req)
    rec = res["calculated_record"]
    qc_res = res["qc"]

    assert qc_res["status"] == "APPROVED"
    assert len(qc_res["errors"]) == 0
    # Clean pass diagnostics
    assert all(d["severity"] != "ERROR" for d in qc_res["diagnostics"])


def test_qc_hsp_displacement_diagnostic():
    """Validates QC-FLAG-HSP-DISP-01 trigger and structured diagnostic fields."""
    qc = QualityControlEngine()
    test_rec = {
        "name": "Displacement Test Drug",
        "canonical_smiles": "CC(=O)NC1=CC=CC=C1",
        "tm_K": {"tm_K": 380.0, "provenance": "LITERATURE"},
        "tg_K": {"tg_K": 266.0, "provenance": "CALCULATED"},
        "density_g_cm3": {"density_g_cm3": 1.15, "provenance": "CALCULATED"},
        "hsp_mpa_half": {
            "delta_D": 18.0, "delta_P": 8.0, "delta_H": 10.0,
            "displacement": 3.25
        },
        "delta_D": 18.0, "delta_P": 8.0, "delta_H": 10.0,
        "R0": 7.5,
        "mw": 135.16,
        "logP": 1.16,
        "TPSA": 29.1,
        "HBD": 1,
        "HBA": 1,
        "BCS_class": "I",
        "provenance": {
            "tm_K": "LITERATURE", "tg_K": "CALCULATED", "density_g_cm3": "CALCULATED",
            "delta_D": "CALCULATED", "delta_P": "CALCULATED", "delta_H": "CALCULATED",
            "R0": "ASSUMED", "mw": "COMPUTED-DESCRIPTOR", "logP": "COMPUTED-DESCRIPTOR",
            "TPSA": "COMPUTED-DESCRIPTOR", "HBD": "COMPUTED-DESCRIPTOR", "HBA": "COMPUTED-DESCRIPTOR",
            "BCS_class": "LITERATURE"
        }
    }
    qc_res = qc.run_drug_qc(test_rec)
    assert qc_res["status"] == "APPROVED with flags"
    codes = [d["code"] for d in qc_res["diagnostics"]]
    assert "QC-FLAG-HSP-DISP-01" in codes
    
    diag = next(d for d in qc_res["diagnostics"] if d["code"] == "QC-FLAG-HSP-DISP-01")
    assert "3.25" in diag["observed_value"]
    assert diag["severity"] == "WARNING"
    assert "Monte Carlo" in diag["remediation_guidance"]


def test_qc_heavy_halogen_density_diagnostic():
    """Validates QC-FLAG-DENS-HALOGEN detection for iodinated molecule (CID 87971)."""
    req = DrugCalculateRequest(
        name="N-(3-iodophenyl)acetamide",
        smiles="CC(=O)NC1=CC(=CC=C1)I",
        tm_value_k=350.0,
        bcs_class="II",
        pubchem_cid=87971
    )
    res = calculate_drug_properties(req)
    qc_res = res["qc"]
    
    codes = [d["code"] for d in qc_res["diagnostics"]]
    assert "QC-FLAG-DENS-HALOGEN" in codes
    diag = next(d for d in qc_res["diagnostics"] if d["code"] == "QC-FLAG-DENS-HALOGEN")
    assert diag["severity"] == "INFO"
    assert "halogen" in diag["molecular_motif"].lower()


def test_qc_lipinski_and_tpsa_ritonavir():
    """Validates high MW and high TPSA diagnostics for Ritonavir."""
    req = DrugCalculateRequest(
        name="Ritonavir",
        smiles="CC(C)C1=NC(=CS1)CN(C)C(=O)NC(C(C)C)C(=O)NC(CC2=CC=CC=C2)C(CC(CC3=CC=CC=C3)NC(=O)OCC4=CN=CS4)O",
        tm_value_k=395.15,
        bcs_class="IV",
        pubchem_cid=392622
    )
    res = calculate_drug_properties(req)
    qc_res = res["qc"]
    
    codes = [d["code"] for d in qc_res["diagnostics"]]
    assert "QC-FLAG-MW-RO5-01" in codes
    assert "QC-FLAG-TPSA-HIGH-01" in codes


def test_qc_salt_counterion_diagnostic():
    """Validates QC-FLAG-ION-SALT on multi-fragment salt SMILES."""
    qc = QualityControlEngine()
    test_rec = {
        "name": "Naproxen Sodium",
        "canonical_smiles": "CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)[O-].[Na+]",
        "tm_K": {"tm_K": 528.0, "provenance": "LITERATURE"},
        "tg_K": {"tg_K": 369.6, "provenance": "CALCULATED"},
        "density_g_cm3": {"density_g_cm3": 1.28, "provenance": "CALCULATED"},
        "hsp_mpa_half": {"delta_D": 18.0, "delta_P": 4.0, "delta_H": 8.0, "displacement": 1.0},
        "delta_D": 18.0, "delta_P": 4.0, "delta_H": 8.0,
        "R0": 7.5,
        "mw": 252.24,
        "logP": 3.0,
        "TPSA": 40.1,
        "HBD": 0,
        "HBA": 3,
        "BCS_class": "II",
        "provenance": {
            "tm_K": "LITERATURE", "tg_K": "CALCULATED", "density_g_cm3": "CALCULATED",
            "delta_D": "CALCULATED", "delta_P": "CALCULATED", "delta_H": "CALCULATED",
            "R0": "ASSUMED", "mw": "COMPUTED-DESCRIPTOR", "logP": "COMPUTED-DESCRIPTOR",
            "TPSA": "COMPUTED-DESCRIPTOR", "HBD": "COMPUTED-DESCRIPTOR", "HBA": "COMPUTED-DESCRIPTOR",
            "BCS_class": "LITERATURE"
        }
    }
    qc_res = qc.run_drug_qc(test_rec)
    codes = [d["code"] for d in qc_res["diagnostics"]]
    assert "QC-FLAG-ION-SALT" in codes


def test_polymer_qc_pvp_k30_lactam_displacement():
    """Validates that Povidone K30 triggers QC-FLAG-POLY-HSP-DISP with lactam ring motif."""
    poly_engine = PolymerPipelineEngine()
    qc = QualityControlEngine()
    
    rec = poly_engine.calculate_polymer_record("povidone", "K30")
    qc_res = qc.run_polymer_qc(rec)
    
    assert qc_res["status"] == "APPROVED with flags"
    codes = [d["code"] for d in qc_res["diagnostics"]]
    assert "QC-FLAG-POLY-HSP-DISP" in codes
    
    diag = next(d for d in qc_res["diagnostics"] if d["code"] == "QC-FLAG-POLY-HSP-DISP")
    assert "lactam" in diag["molecular_motif"].lower()
    assert float(diag["observed_value"].split()[0]) > 2.0


def test_qc_inorganic_rejection():
    """Validates that non-organic/inorganic inputs (NaCl) are rejected with QC-ERR-INORGANIC-SUBSTANCE."""
    qc = QualityControlEngine()
    test_rec = {
        "name": "Sodium Chloride",
        "canonical_smiles": "[Na+].[Cl-]",
        "tm_K": 1074.0,
        "tg_K": 751.8,
        "density_g_cm3": 2.16,
        "delta_D": 15.0, "delta_P": 5.0, "delta_H": 5.0,
        "provenance": {"tm_K": "LITERATURE", "tg_K": "CALCULATED", "density_g_cm3": "CALCULATED", "delta_D": "CALCULATED", "delta_P": "CALCULATED", "delta_H": "CALCULATED", "R0": "ASSUMED", "mw": "COMPUTED-DESCRIPTOR", "logP": "COMPUTED-DESCRIPTOR", "TPSA": "COMPUTED-DESCRIPTOR", "HBD": "COMPUTED-DESCRIPTOR", "HBA": "COMPUTED-DESCRIPTOR", "BCS_class": "LITERATURE"}
    }
    qc_res = qc.run_drug_qc(test_rec)
    assert qc_res["status"] == "REJECTED"
    codes = [d["code"] for d in qc_res["diagnostics"]]
    assert "QC-ERR-INORGANIC-SUBSTANCE" in codes


def test_qc_solvent_detection():
    """Validates low MW solvent/reagent detection (Acetone, MW=58.0 g/mol)."""
    qc = QualityControlEngine()
    test_rec = {
        "name": "Acetone",
        "canonical_smiles": "CC(=O)C",
        "tm_K": 178.4,
        "tg_K": 124.9,
        "density_g_cm3": 0.784,
        "delta_D": 15.5, "delta_P": 10.4, "delta_H": 7.0,
        "provenance": {"tm_K": "LITERATURE", "tg_K": "CALCULATED", "density_g_cm3": "CALCULATED", "delta_D": "CALCULATED", "delta_P": "CALCULATED", "delta_H": "CALCULATED", "R0": "ASSUMED", "mw": "COMPUTED-DESCRIPTOR", "logP": "COMPUTED-DESCRIPTOR", "TPSA": "COMPUTED-DESCRIPTOR", "HBD": "COMPUTED-DESCRIPTOR", "HBA": "COMPUTED-DESCRIPTOR", "BCS_class": "LITERATURE"}
    }
    qc_res = qc.run_drug_qc(test_rec)
    codes = [d["code"] for d in qc_res["diagnostics"]]
    assert "QC-FLAG-SOLVENT-FRAGMENT" in codes


def test_qc_polymer_in_drug_pipeline_detection():
    """Validates that entering a polymer in Pipeline A triggers QC-FLAG-POLYMER-IN-DRUG-INPUT."""
    qc = QualityControlEngine()
    test_rec = {
        "name": "PVP K30",
        "canonical_smiles": "C1CCN(C1=O)C=C",
        "tm_K": 350.0,
        "tg_K": 245.0,
        "density_g_cm3": 1.20,
        "delta_D": 20.44, "delta_P": 13.67, "delta_H": 6.86,
        "provenance": {"tm_K": "LITERATURE", "tg_K": "CALCULATED", "density_g_cm3": "CALCULATED", "delta_D": "CALCULATED", "delta_P": "CALCULATED", "delta_H": "CALCULATED", "R0": "ASSUMED", "mw": "COMPUTED-DESCRIPTOR", "logP": "COMPUTED-DESCRIPTOR", "TPSA": "COMPUTED-DESCRIPTOR", "HBD": "COMPUTED-DESCRIPTOR", "HBA": "COMPUTED-DESCRIPTOR", "BCS_class": "LITERATURE"}
    }
    qc_res = qc.run_drug_qc(test_rec)
    codes = [d["code"] for d in qc_res["diagnostics"]]
    assert "QC-FLAG-POLYMER-IN-DRUG-INPUT" in codes
