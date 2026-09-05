"""
Drug-Polymer Pair Miscibility and Screening Metrics Engine.
Computes Hansen distance Ra, RED across R0 sensitivity band [7.0, 7.5, 8.0], and Greenhalgh Delta delta_t.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


def calculate_hansen_distance(
    delta_D1: float, delta_P1: float, delta_H1: float,
    delta_D2: float, delta_P2: float, delta_H2: float
) -> float:
    """
    Computes Hansen distance Ra with classic 4x dispersion weighting:
    Ra^2 = 4*(delta_D1 - delta_D2)^2 + (delta_P1 - delta_P2)^2 + (delta_H1 - delta_H2)^2
    """
    ra_sq = 4.0 * ((delta_D1 - delta_D2) ** 2) + ((delta_P1 - delta_P2) ** 2) + ((delta_H1 - delta_H2) ** 2)
    return round(math.sqrt(ra_sq), 2)


def calculate_red_sensitivity(ra: float, r0_list: Optional[List[float]] = None) -> Dict[str, float]:
    """
    Calculates Relative Energy Difference (RED = Ra / R0) across standard screening radii.
    Default band is [7.0, 7.5, 8.0] MPa^0.5.
    """
    if r0_list is None:
        r0_list = [7.0, 7.5, 8.0]
    
    red_results = {}
    for r0 in r0_list:
        red_val = round(ra / r0, 2)
        key = f"RED_at_R0_{str(r0).replace('.', '_')}"
        red_results[key] = red_val
    return red_results


def calculate_greenhalgh_delta(delta_t1: float, delta_t2: float) -> Tuple[float, str]:
    """
    Computes Greenhalgh scalar solubility parameter difference: |delta_t1 - delta_t2|.
    Applies Greenhalgh et al. 1999 miscibility thresholds:
      - < 2.0 MPa^0.5: likely glass solution
      - < 7.0 MPa^0.5: likely miscible
      - > 10.0 MPa^0.5: likely immiscible
    """
    diff = round(abs(delta_t1 - delta_t2), 2)
    if diff < 2.0:
        verdict = f"{diff} MPa^0.5 (< 2: likely glass solution / miscible)"
    elif diff < 7.0:
        verdict = f"{diff} MPa^0.5 (< 7: likely miscible)"
    elif diff <= 10.0:
        verdict = f"{diff} MPa^0.5 (7-10: moderate / borderline)"
    else:
        verdict = f"{diff} MPa^0.5 (> 10: likely immiscible)"
    return diff, verdict


def evaluate_drug_polymer_pair(
    drug_record: Dict[str, Any],
    polymer_record: Dict[str, Any],
    r0_assigned: float = 7.5
) -> Dict[str, Any]:
    """
    Performs full pair miscibility screening between a Drug and a Polymer record.
    """
    drug_id = drug_record.get("entity_id", "DRG-xxxx")
    drug_name = drug_record.get("name", "Unknown Drug")
    
    poly_id = polymer_record.get("entity_id", "POL-xxxx")
    poly_name = polymer_record.get("abbreviation") or polymer_record.get("name", "Unknown Polymer")
    
    # Extract HSP components
    d_hsp = drug_record.get("hsp_mpa_half", {})
    p_hsp = polymer_record.get("hsp_mpa_half", {})
    
    d_dD = d_hsp.get("delta_D", drug_record.get("delta_D", 0.0))
    d_dP = d_hsp.get("delta_P", drug_record.get("delta_P", 0.0))
    d_dH = d_hsp.get("delta_H", drug_record.get("delta_H", 0.0))
    d_dt = d_hsp.get("primary_total", round(math.sqrt(d_dD**2 + d_dP**2 + d_dH**2), 2))
    
    p_dD = p_hsp.get("delta_D", polymer_record.get("delta_D", 0.0))
    p_dP = p_hsp.get("delta_P", polymer_record.get("delta_P", 0.0))
    p_dH = p_hsp.get("delta_H", polymer_record.get("delta_H", 0.0))
    # Prefer tabulated if present for Greenhalgh comparison reference, or recomputed
    p_dt_tab = p_hsp.get("tabulated_total", round(math.sqrt(p_dD**2 + p_dP**2 + p_dH**2), 2))
    p_dt_recomp = p_hsp.get("recomputed_total", round(math.sqrt(p_dD**2 + p_dP**2 + p_dH**2), 2))
    
    # 1. Hansen distance Ra
    ra = calculate_hansen_distance(d_dD, d_dP, d_dH, p_dD, p_dP, p_dH)
    
    # 2. RED across band
    red_7_0 = round(ra / 7.0, 2)
    red_7_5 = round(ra / 7.5, 2)
    red_8_0 = round(ra / 8.0, 2)
    
    # 3. Greenhalgh difference
    greenhalgh_tab, g_verdict_tab = calculate_greenhalgh_delta(d_dt, p_dt_tab)
    greenhalgh_recomp, g_verdict_recomp = calculate_greenhalgh_delta(d_dt, p_dt_recomp)
    
    # 4. Stability and Borderline assessment
    # Check if RED crosses 1.0 boundary in 7.0-8.0 band
    crosses_boundary = (red_7_0 < 1.0 and red_8_0 > 1.0) or (red_7_0 > 1.0 and red_8_0 < 1.0)
    
    # Check if Greenhalgh and RED conflict
    # e.g., Greenhalgh < 7 (miscible) but RED > 1.0 (outside sphere) -> Classic Borderline (e.g. Ibuprofen/PVP)
    greenhalgh_miscible = greenhalgh_tab < 7.0 or greenhalgh_recomp < 7.0
    red_miscible = red_7_5 <= 1.0
    conflict = greenhalgh_miscible != red_miscible
    
    qc_notes = []
    if crosses_boundary:
        stability = "BORDERLINE"
        qc_notes.append("RED boundary crosses 1.0 within assigned R0 band [7.0, 8.0]")
    elif conflict:
        stability = "BORDERLINE"
        qc_notes.append(f"Greenhalgh criterion (Δδt={greenhalgh_tab} MPa^0.5, likely miscible) conflicts with RED ({red_7_5}, outside sphere). Exported as BORDERLINE; experimental confirmation recommended.")
    elif red_7_5 <= 1.0:
        stability = "STABLE_MISCIBLE"
        qc_notes.append("Pair consistently inside sphere and miscible across band")
    else:
        stability = "STABLE_IMMISCIBLE"
        qc_notes.append("Pair consistently outside sphere across band")
        
    return {
        "pair": [drug_id, poly_id],
        "drug_id": drug_id,
        "drug_name": drug_name,
        "polymer_id": poly_id,
        "polymer_name": poly_name,
        "delta_t_drug": d_dt,
        "delta_t_polymer_tabulated": p_dt_tab,
        "delta_t_polymer_recomputed": p_dt_recomp,
        "greenhalgh_delta_t_tabulated": greenhalgh_tab,
        "greenhalgh_delta_t_recomputed": greenhalgh_recomp,
        "greenhalgh_verdict": g_verdict_tab,
        "hansen_distance_Ra": ra,
        "RED": {
            "at_R0_7_0": red_7_0,
            "at_R0_7_5": red_7_5,
            "at_R0_8_0": red_8_0
        },
        "RED_at_7_5": red_7_5,
        "stability_grade": stability,
        "borderline_flag": stability == "BORDERLINE",
        "qc_notes": qc_notes
    }
