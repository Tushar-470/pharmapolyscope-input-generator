"""
Hansen Solubility Parameters (HSP) calculation and cross-method comparison engine.
Implements Hoftyzer-van Krevelen primary (HSP-HVK-01) and Fedors secondary method.
"""

from typing import Dict, Any, List, Optional
from engine.group_contribution import GroupContributionEngine


class HspEngine:
    def __init__(self, gc_engine: Optional[GroupContributionEngine] = None):
        self.gc = gc_engine if gc_engine else GroupContributionEngine()

    def calculate_hsp_from_groups(
        self,
        groups: List[Dict[str, Any]],
        mw: float,
        molar_volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates primary HVK partial parameters and secondary Fedors total parameter.
        Computes displacement and QC checks.
        """
        # 1. Fedors calculation (provides molar volume and secondary delta_t)
        fedors_res = self.gc.calculate_fedors(groups, mw)
        vm = molar_volume if molar_volume and molar_volume > 0 else fedors_res["molar_volume_cm3_mol"]
        
        # 2. HVK calculation
        hvk_res = self.gc.calculate_hvk(groups, vm)
        
        # 3. Cross-method displacement
        hvk_total = hvk_res["primary_total"]
        fedors_total = fedors_res["secondary_fedors_total"]
        displacement = round(abs(hvk_total - fedors_total), 2)
        
        qc_pass = displacement < 5.0
        qc_note = f"Displacement HVK ({hvk_total}) vs Fedors ({fedors_total}) = {displacement} MPa^0.5"
        if not qc_pass:
            qc_note += " (exceeds 5.0 MPa^0.5 QC threshold; confidence lowered)"
            
        return {
            "delta_D": hvk_res["delta_D"],
            "delta_P": hvk_res["delta_P"],
            "delta_H": hvk_res["delta_H"],
            "primary_total": hvk_total,
            "method_id": "HSP-HVK-01",
            "secondary_fedors_total": fedors_total,
            "displacement": displacement,
            "molar_volume_used": vm,
            "qc_pass": qc_pass,
            "qc_note": qc_note,
            "provenance": {
                "delta_D": "CALCULATED",
                "delta_P": "CALCULATED",
                "delta_H": "CALCULATED"
            },
            "confidence": "high" if displacement < 2.0 else ("medium" if qc_pass else "low"),
            "uncertainty": "approx. 1.0-1.5 MPa^0.5 per component",
            "breakdown": hvk_res["breakdown"]
        }
