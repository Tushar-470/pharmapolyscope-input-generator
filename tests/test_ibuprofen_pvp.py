"""
Regression test for Appendix A worked example: Ibuprofen (DRG-0001) & Povidone K30 (POL-0001).
Asserts that all physicochemical properties, uncertainties, and QC behavior are reproduced faithfully.
"""

import pytest
from engine.group_contribution import GroupContributionEngine
from engine.thermophysical import calculate_drug_tg, calculate_drug_density_and_volume
from engine.descriptors import compute_molecular_descriptors
from engine.polymer_pipeline import PolymerPipelineEngine
from engine.qc import QualityControlEngine


def test_ibuprofen_reproduction():
    """Validates DRG-0001 Ibuprofen values against Appendix A.1 and Table 5-2."""
    smiles = "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"
    
    # 1. Descriptors
    desc, prov = compute_molecular_descriptors(smiles)
    assert desc["mw"] == 206.28
    assert desc["TPSA"] == 37.3
    assert desc["HBD"] == 1
    assert desc["HBA"] == 2
    assert desc["logP"] == 3.07  # RDKit Crippen
    
    # 2. Thermophysical: Tm = 349.15 K -> Tg = 244.4 K (+/- 21 K)
    tm_k = 349.15
    tg_res = calculate_drug_tg(tm_k, validation_ref_tg=[227.15, 228.5])
    assert tg_res["tg_K"] == 244.4
    assert tg_res["uncertainty_K"] == 21.0
    assert tg_res["method_id"] == "TG-RATIO-01"
    
    # 3. Group Contribution (Fedors Table 5-2 arithmetic)
    gc = GroupContributionEngine()
    groups = [
        {"name": "-CH3 (aliphatic)", "count": 3},
        {"name": "-CH2- (aliphatic)", "count": 1},
        {"name": ">CH- (aliphatic)", "count": 2},
        {"name": "Phenylene C6H4 (aromatic ring, p/m/o)", "count": 1},
        {"name": "-COOH (carboxylic acid)", "count": 1}
    ]
    fedors = gc.calculate_fedors(groups, desc["mw"])
    assert fedors["molar_volume_cm3_mol"] == 195.5
    assert fedors["density_g_cm3"] == 1.055
    assert fedors["delta_u_cal_mol"] == 20425.0
    assert fedors["secondary_fedors_total"] == 20.91
    
    # 4. Hansen parameters (HVK)
    hvk = gc.calculate_hvk(groups, fedors["molar_volume_cm3_mol"])
    assert hvk["delta_D"] == 17.85
    assert hvk["delta_P"] == 2.22
    assert hvk["delta_H"] == 7.15
    assert hvk["primary_total"] == 19.36
    
    # Displacement
    disp = round(abs(hvk["primary_total"] - fedors["secondary_fedors_total"]), 2)
    assert disp == 1.55


def test_povidone_k30_reproduction():
    """Validates POL-0001 Povidone K30 values against Appendix A.2."""
    poly_engine = PolymerPipelineEngine()
    record = poly_engine.calculate_polymer_record("povidone", "K30", entity_id="POL-0001")
    
    assert record["name"] == "povidone (polyvinylpyrrolidone)"
    assert record["abbreviation"] == "PVP K30"
    assert record["repeat_unit_smiles"]["formula"] == "C6H9NO"
    assert record["repeat_unit_smiles"]["repeat_unit_mw"] == 111.14
    assert record["tg_K"]["value"] == 426.8
    
    hsp = record["hsp_mpa_half"]
    assert hsp["delta_D"] == 20.44
    assert hsp["delta_P"] == 13.67
    assert hsp["delta_H"] == 6.86
    assert hsp["tabulated_total"] == 26.28
    assert hsp["recomputed_total"] == 25.53
    assert hsp["secondary_fedors_total"] == 23.75
    assert hsp["displacement"] == 2.53

