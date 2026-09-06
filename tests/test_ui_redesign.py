"""
Regression tests for Scientific UI/UX Redesign.
Validates 3-panel architecture data contracts, provenance labels, polymer grade distinctions, and clean scalar rendering.
"""

import pytest
import os
from api.routes.drugs import render_smiles_svg, search_pubchem
from engine.io_manager import IOManager
from engine.polymer_pipeline import PolymerPipelineEngine


def test_ui_files_exist_and_clean():
    """Validates that redesigned HTML, CSS, and JS files exist with high-density scientific structure."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ui_dir = os.path.join(base_dir, "ui")
    
    html_path = os.path.join(ui_dir, "index.html")
    css_path = os.path.join(ui_dir, "css", "style.css")
    js_path = os.path.join(ui_dir, "js", "app.js")
    
    assert os.path.exists(html_path)
    assert os.path.exists(css_path)
    assert os.path.exists(js_path)
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "sidebar" in html_content
    assert "main-content" in html_content
    assert "calc-inspector-modal" in html_content
    assert "Drug Parameters" in html_content
    assert "Polymer Grade Parameters" in html_content
    assert "Pharmapolyscope Ready Sheet" in html_content


def test_live_smiles_svg_rendering():
    """Validates that 2D depiction SVG renders instantly from SMILES."""
    res = render_smiles_svg("CC(C)CC1=CC=C(C=C1)C(C)C(=O)O")
    assert res["valid"] is True
    assert res["svg"] is not None
    assert "<svg" in res["svg"]


def test_pubchem_live_lookup():
    """Validates PubChem REST resolution by name and CID."""
    # Lookup by name
    res_name = search_pubchem("Ibuprofen")
    assert res_name["found"] is True
    assert res_name["data"]["canonical_smiles"] is not None
    assert res_name["svg"] is not None
    assert "<svg" in res_name["svg"]

    # Lookup by CID
    res_cid = search_pubchem("3672")
    assert res_cid["found"] is True
    assert res_cid["data"]["cid"] == 3672


def test_polymer_family_vs_grade_distinction():
    """Validates that polymer pipeline maintains strict separation between carrier family and commercial grade."""
    engine = PolymerPipelineEngine()
    carriers = engine.list_available_carriers()
    assert len(carriers) >= 5
    
    # Verify PVP family has multiple distinct grades
    pvp = next(c for c in carriers if c["carrier"] == "povidone")
    assert "K30" in pvp["grades"]
    assert "K17" in pvp["grades"]
    assert "K90" in pvp["grades"]
    
    # Verify HPMCAS family has distinct grades (M, L, H)
    hpmcas = next(c for c in carriers if "hypromellose acetate succinate" in c["carrier"] or "hpmcas" in c["name"].lower())
    assert "M" in hpmcas["grades"]
    assert "L" in hpmcas["grades"]
    assert "H" in hpmcas["grades"]


def test_manual_entry_sheet_provenance_and_units():
    """Validates that manual-entry sheet outputs have explicit units and unambiguous values."""
    io_mgr = IOManager()
    
    # Drug sheet
    drg_sheet = io_mgr.generate_pharmapolyscope_ready_sheet("DRG-0001")
    for field in drg_sheet["fields"]:
        assert field["unit"] is not None and field["unit"] != ""
        assert field["value"] is not None and field["value"] != ""
        assert field["provenance"] is not None and field["provenance"] != ""
        assert "[object Object]" not in str(field["value"])
        assert "undefined" not in str(field["value"])
        assert "NaN" not in str(field["value"])
        
    # Polymer sheet
    pol_sheet = io_mgr.generate_pharmapolyscope_ready_sheet("POL-0001")
    for field in pol_sheet["fields"]:
        assert field["unit"] is not None and field["unit"] != ""
        assert field["value"] is not None and field["value"] != ""
        assert field["provenance"] is not None and field["provenance"] != ""
        assert "[object Object]" not in str(field["value"])
        assert "undefined" not in str(field["value"])
        assert "NaN" not in str(field["value"])


def test_benchmark_outputs_unaltered():
    """Verifies that the UI redesign has zero side-effects on the frozen scientific benchmark outputs."""
    io_mgr = IOManager()
    dataset = io_mgr.load_dataset()
    
    drg = next(r for r in dataset["records"] if r["entity_id"] == "DRG-0001")
    pol = next(r for r in dataset["records"] if r["entity_id"] == "POL-0001")
    
    # Ibuprofen targets
    assert drg["mw"] == 206.28
    assert drg["tm_K"]["value"] == 349.15
    assert drg["tg_K"]["value"] == 244.4
    assert drg["density_g_cm3"]["value"] == 1.055
    assert drg["hsp_mpa_half"]["delta_D"] == 17.85
    assert drg["hsp_mpa_half"]["delta_P"] == 2.22
    assert drg["hsp_mpa_half"]["delta_H"] == 7.15
    assert drg["R0"]["value"] == 7.5
    
    # Polymer targets
    assert pol["tg_K"]["value"] == 426.8
    assert pol["hsp_mpa_half"]["delta_D"] == 20.44
    assert pol["hsp_mpa_half"]["delta_P"] == 13.67
    assert pol["hsp_mpa_half"]["delta_H"] == 6.86


def test_calculate_drug_properties_endpoint():
    """Validates that calculate_drug_properties endpoint handles arbitrary SMILES without error."""
    from api.routes.drugs import calculate_drug_properties, DrugCalculateRequest
    
    # Test with custom compound
    req = DrugCalculateRequest(
        name="Naproxen",
        smiles="CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)O",
        tm_value_k=426.15,
        bcs_class="II"
    )
    res = calculate_drug_properties(req)
    assert "calculated_record" in res
    rec = res["calculated_record"]
    assert rec["mw"] > 200.0
    assert rec["tg_K"]["tg_K"] > 0
    assert rec["density_g_cm3"]["density_g_cm3"] > 0
    assert rec["hsp_mpa_half"]["delta_D"] > 0
    assert len(res["groups_matched"]) > 0


def test_html_report_generation():
    """Validates that standalone HTML report generates with all required headers, tables, and styles."""
    from api.routes.export import download_report_html
    
    # Drug report test
    resp_drg = download_report_html("DRG-0001", download=False)
    html_drg = resp_drg.body.decode("utf-8")
    assert "<!DOCTYPE html>" in html_drg
    assert "PHARMAPOLYSCOPE: MANUAL ENTRY SHEET" in html_drg
    assert "ibuprofen" in html_drg.lower()
    assert "DRG-0001" in html_drg
    assert "Nominal Base" in html_drg
    assert "10k MC Final" in html_drg
    assert "@page" in html_drg
    
    # Polymer report test
    resp_pol = download_report_html("POL-0001", download=True)
    html_pol = resp_pol.body.decode("utf-8")
    assert "<!DOCTYPE html>" in html_pol
    assert "POL-0001" in html_pol
    assert "povidone" in html_pol.lower()
    assert "Content-Disposition" in resp_pol.headers
    assert "PharmaPolySCOPE_Report_POL-0001" in resp_pol.headers["Content-Disposition"]
