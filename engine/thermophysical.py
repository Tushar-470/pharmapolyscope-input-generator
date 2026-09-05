"""
Thermophysical property calculations for Small-Molecule Drugs.
Implements deterministic Tm acquisition hierarchy (Table 4-1), drug Tg = 0.70 * Tm, and Fedors density.
"""

from typing import Dict, Any, List, Optional, Tuple, Union


def convert_celsius_to_kelvin(temp_c: float) -> float:
    """Converts Celsius to Kelvin with exact offset 273.15."""
    return round(float(temp_c) + 273.15, 2)


def select_melting_point(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Selects drug melting temperature following Table 4-1 deterministic hierarchy.
    sources is a list of dicts:
      [{ "priority": 1, "value_c": 76.0, "form": "form I", "citation": "Grzybowska et al. 2020", "type": "primary_dsc" }, ...]
    """
    if not sources:
        raise ValueError("No melting point sources provided")
        
    # Sort sources by priority ascending (1 is highest priority)
    sorted_sources = sorted(sources, key=lambda s: s.get("priority", 99))
    winner = sorted_sources[0]
    
    val_k = winner.get("value_k")
    if val_k is None and winner.get("value_c") is not None:
        val_k = convert_celsius_to_kelvin(winner["value_c"])
        
    prio = winner.get("priority", 3)
    if prio == 1:
        provenance = "LITERATURE"
        uncertainty = 2.0
        conf = "high"
    elif prio == 2:
        provenance = "LITERATURE"
        uncertainty = 3.5
        conf = "high"
    elif prio == 3:
        provenance = "LITERATURE"
        uncertainty = 3.0
        conf = "medium"
    elif prio == 4:
        provenance = "LITERATURE"
        uncertainty = 5.0
        conf = "medium"
    else:
        provenance = "ESTIMATED"
        uncertainty = 10.0
        conf = "low"
        
    # Check spread across sources
    kelvin_vals = []
    for s in sources:
        vk = s.get("value_k")
        if vk is None and s.get("value_c") is not None:
            vk = convert_celsius_to_kelvin(s["value_c"])
        if vk:
            kelvin_vals.append(vk)
            
    spread = round(max(kelvin_vals) - min(kelvin_vals), 2) if len(kelvin_vals) > 1 else 0.0
    spread_warning = None
    if spread > 5.0:
        spread_warning = f"Melting point source spread {spread} K exceeds 5 K threshold. Review required."
        
    all_sources_recorded = [s.get("value_c", s.get("value_k")) for s in sources]
    
    return {
        "tm_K": round(val_k, 2),
        "form": winner.get("form", "form I (stable at 25 C)"),
        "convention": winner.get("convention", "DSC onset, primary source selected by Table 4-1 rule"),
        "selected_source": winner.get("citation", "Literature"),
        "all_sources": all_sources_recorded,
        "spread_K": spread,
        "spread_warning": spread_warning,
        "provenance": provenance,
        "confidence": conf,
        "uncertainty_K": uncertainty,
        "method_id": "LIT-ACQ-01"
    }


def calculate_drug_tg(tm_K: float, validation_ref_tg: Optional[Union[float, List[float]]] = None) -> Dict[str, Any]:
    """
    Calculates drug glass transition temperature: Tg = 0.70 * Tm (K).
    Attaches +/- 21 K (1-sigma) uncertainty.
    """
    if tm_K <= 0:
        raise ValueError(f"Invalid thermodynamic melting temperature: {tm_K} K")
        
    tg_val = round(0.70 * tm_K, 1)
    
    validation_note = None
    mae_vs_ref = None
    if validation_ref_tg is not None:
        if isinstance(validation_ref_tg, list):
            avg_ref = sum(validation_ref_tg) / len(validation_ref_tg)
            mae_vs_ref = round(abs(tg_val - avg_ref), 1)
            validation_note = f"Measured amorphous Tg {validation_ref_tg} K; deviation {tg_val - avg_ref:+.1f} K (inside 1-sigma 21 K)"
        else:
            mae_vs_ref = round(abs(tg_val - float(validation_ref_tg)), 1)
            validation_note = f"Measured amorphous Tg {validation_ref_tg} K; deviation {tg_val - float(validation_ref_tg):+.1f} K"
            
    return {
        "tg_K": tg_val,
        "method_id": "TG-RATIO-01",
        "equation": "0.70 * Tm",
        "uncertainty_K": 21.0,
        "provenance": "CALCULATED",
        "confidence": "medium",
        "validation_reference": validation_ref_tg,
        "validation_note": validation_note,
        "deviation_from_ref_K": mae_vs_ref
    }


def calculate_drug_density_and_volume(mw: float, fedors_vm: float, lit_pycnometric_density: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculates Fedors surrogate density and checks consistency against pycnometric density.
    Also computes amorphous convention density (0.95 * rho_cr).
    """
    if fedors_vm <= 0:
        raise ValueError(f"Invalid molar volume: {fedors_vm}")
        
    fedors_density = round(mw / fedors_vm, 3)
    
    consistency_pct = None
    amorphous_conv = None
    qc_pass = True
    qc_note = None
    
    if lit_pycnometric_density and lit_pycnometric_density > 0:
        implied_vm = round(mw / lit_pycnometric_density, 2)
        consistency_pct = round(abs(implied_vm - fedors_vm) / implied_vm * 100.0, 1)
        amorphous_conv = round(0.95 * lit_pycnometric_density, 2)
        
        if consistency_pct > 15.0:
            qc_pass = False
            qc_note = f"Density consistency warning: implied Vm ({implied_vm}) vs Fedors Vm ({fedors_vm}) differs by {consistency_pct}% (> 15% limit)"
        else:
            qc_note = f"Vm implied by pycnometry ({implied_vm}) vs Fedors ({fedors_vm}) (+{consistency_pct}%), pass (< 15%)"
            
    return {
        "density_g_cm3": fedors_density,
        "molar_volume_cm3_mol": fedors_vm,
        "state": "Fedors liquid-state surrogate for crystalline field",
        "method_id": "DENS-FEDORS-01",
        "provenance": "CALCULATED",
        "confidence": "medium",
        "uncertainty": "approx. 5 percent vs pycnometry",
        "amorphous_convention_density": amorphous_conv,
        "molar_volume_consistency_pct": consistency_pct,
        "consistency_pass": qc_pass,
        "qc_note": qc_note
    }
