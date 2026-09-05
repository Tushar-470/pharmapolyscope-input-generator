"""
Tests for Quality Control (QC) battery.
"""

import pytest
from engine.qc import QualityControlEngine


def test_qc_unit_error_detection():
    qc = QualityControlEngine()
    # Drug with Tm entered in Celsius instead of Kelvin
    drug_rec = {
        "entity_id": "DRG-TEST",
        "name": "Test Drug",
        "canonical_smiles": "CC(=O)O",
        "tm_K": {"value": 76.0},  # 76 C entered
        "tg_K": {"value": 53.2},
        "density_g_cm3": {"value": 1.2},
        "delta_D": 17.0,
        "delta_P": 5.0,
        "delta_H": 8.0,
        "R0": 7.5,
        "logP": 1.0,
        "TPSA": 30.0,
        "HBD": 1,
        "HBA": 2,
        "BCS_class": "I",
        "provenance": {
            "tm_K": "LITERATURE", "tg_K": "CALCULATED", "density_g_cm3": "CALCULATED",
            "delta_D": "CALCULATED", "delta_P": "CALCULATED", "delta_H": "CALCULATED",
            "R0": "ASSUMED", "mw": "COMPUTED-DESCRIPTOR", "logP": "COMPUTED-DESCRIPTOR",
            "TPSA": "COMPUTED-DESCRIPTOR", "HBD": "COMPUTED-DESCRIPTOR", "HBA": "COMPUTED-DESCRIPTOR",
            "BCS_class": "LITERATURE"
        }
    }
    res = qc.run_drug_qc(drug_rec)
    assert res["status"] == "REJECTED"
    assert any("Celsius" in e for e in res["errors"])


def test_qc_polymer_calculated_tg_rejection():
    qc = QualityControlEngine()
    # Polymer Tg erroneously marked CALCULATED
    poly_rec = {
        "entity_id": "POL-TEST",
        "name": "Test Polymer",
        "grade": "Test Grade",
        "repeat_unit_smiles": "*CC*",
        "tg_K": 400.0,
        "density_g_cm3": 0.4,
        "delta_D": 18.0,
        "delta_P": 5.0,
        "delta_H": 5.0,
        "R0": 7.5,
        "provenance": {
            "tg_K": "CALCULATED",  # Forbidden for polymers
            "delta_D": "CALCULATED", "delta_P": "CALCULATED", "delta_H": "CALCULATED",
            "R0": "ASSUMED", "mn": "MANUFACTURER-SPEC", "bulk_density": "MANUFACTURER-SPEC",
            "repeat_unit_smiles": "LITERATURE (curated record)"
        }
    }
    res = qc.run_polymer_qc(poly_rec)
    assert res["status"] == "REJECTED"
    assert any("CALCULATED" in e for e in res["errors"])
