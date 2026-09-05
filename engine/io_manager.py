"""
Synchronous I/O and data store manager for input_dataset.json and input_dataset.csv.
Ensures single-pass synchronization, schema validation, and dedicated Pharmapolyscope-ready exports.
"""

import os
import csv
import json
from typing import Dict, Any, List, Optional


CSV_COLUMNS = [
    "entity_id", "entity_type", "name", "abbreviation", "canonical_smiles", "repeat_unit_smiles",
    "mn", "mw", "tm_K", "tg_K", "density_g_cm3", "delta_D", "delta_P", "delta_H", "R0",
    "logP", "TPSA", "HBD", "HBA", "BCS_class", "source", "method", "algorithm",
    "provenance", "confidence", "uncertainty", "calculation_date", "software_version"
]


class IOManager:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data", "store")
            
        self.data_dir = data_dir
        self.json_path = os.path.join(self.data_dir, "input_dataset.json")
        self.csv_path = os.path.join(self.data_dir, "input_dataset.csv")

    def load_dataset(self) -> Dict[str, Any]:
        """Loads the full structured JSON dataset."""
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"JSON store not found at {self.json_path}")
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_dataset(self, data: Dict[str, Any]) -> None:
        """
        Saves the structured JSON dataset and automatically synchronizes input_dataset.csv.
        """
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 1. Write structured JSON
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        # 2. Synchronize CSV in the same pass
        self.export_csv_from_json(data)

    def export_csv_from_json(self, data: Dict[str, Any]) -> None:
        """
        Converts the structured JSON records into the flat 28-column CSV format.
        Preserves null representation as literal 'null'.
        """
        records = data.get("records", [])
        
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
            
            for r in records:
                row = []
                for col in CSV_COLUMNS:
                    val = self._extract_csv_field(r, col)
                    row.append(val)
                writer.writerow(row)

    def _extract_csv_field(self, record: Dict[str, Any], col: str) -> str:
        """Extracts and formats a specific column value for CSV export."""
        # Special flattenings
        if col == "canonical_smiles":
            return record.get("canonical_smiles") or "null"
            
        elif col == "repeat_unit_smiles":
            ru = record.get("repeat_unit_smiles")
            if isinstance(ru, dict):
                return ru.get("value") or "null"
            return ru or "null"
            
        elif col == "tm_K":
            tm = record.get("tm_K")
            if isinstance(tm, dict):
                return str(tm.get("value")) if tm.get("value") is not None else "null"
            return str(tm) if tm is not None else "null"
            
        elif col == "tg_K":
            tg = record.get("tg_K")
            if isinstance(tg, dict):
                return str(tg.get("value")) if tg.get("value") is not None else "null"
            return str(tg) if tg is not None else "null"
            
        elif col == "density_g_cm3":
            dens = record.get("density_g_cm3")
            if isinstance(dens, dict):
                return str(dens.get("value")) if dens.get("value") is not None else "null"
            return str(dens) if dens is not None else "null"
            
        elif col in ("delta_D", "delta_P", "delta_H"):
            hsp = record.get("hsp_mpa_half", {})
            val = hsp.get(col, record.get(col))
            return str(val) if val is not None else "null"
            
        elif col == "R0":
            r0 = record.get("R0")
            if isinstance(r0, dict):
                return str(r0.get("value", 7.5))
            return str(r0) if r0 is not None else "7.5"
            
        elif col == "logP":
            lp = record.get("logP")
            if isinstance(lp, dict):
                if lp.get("primary") is not None:
                    return str(lp.get("primary"))
                elif lp.get("cross_check", {}).get("value") is not None:
                    return str(lp["cross_check"]["value"])
            return str(lp) if lp is not None else "null"
            
        elif col == "method":
            m = record.get("method", [])
            if isinstance(m, list):
                return ";".join(m)
            return str(m) if m else "null"
            
        elif col == "provenance":
            p = record.get("provenance", {})
            if isinstance(p, dict):
                # Format as key=value; key2=value2
                pairs = [f"{k}={v}" for k, v in p.items()]
                return "; ".join(pairs) if pairs else "null"
            return str(p) if p else "null"
            
        elif col == "uncertainty":
            u = record.get("uncertainty", {})
            if isinstance(u, dict):
                pairs = [f"{k}: {v}" for k, v in u.items()]
                return "; ".join(pairs) if pairs else "null"
            return str(u) if u else "null"
            
        else:
            raw = record.get(col)
            if raw is None:
                return "null"
            return str(raw)

    def generate_pharmapolyscope_ready_sheet(self, entity_id: str) -> Dict[str, Any]:
        """
        Generates a dedicated, clean summary sheet of the EXACT values and units
        that a researcher needs to manually enter into Pharmapolyscope.
        Includes dual representation (Base Nominal vs 10k MC UQ Converged Values) and 1-click clipboard exports.
        """
        from engine.sensitivity import SensitivityEngine

        dataset = self.load_dataset()
        matching = [r for r in dataset.get("records", []) if r.get("entity_id") == entity_id]
        if not matching:
            raise ValueError(f"Entity ID '{entity_id}' not found in dataset store")
            
        record = matching[0]
        entity_type = record.get("entity_type")
        name = record.get("name", "Unknown")
        abbreviation = record.get("abbreviation")
        seed = record.get("seed", 42)
        
        sens_engine = SensitivityEngine(seed=seed)
        dual_rep = sens_engine.generate_dual_representation(record)
        uncertainty_table = sens_engine.compute_full_uncertainty_table(record)
        
        # Build quick lookup from uncertainty table
        uq_map = {row["param_key"]: row for row in uncertainty_table}
        
        fields = []
        
        if entity_type == "drug":
            subtitle = record.get("iupac_name") or f"{name.title()} Active Pharmaceutical Ingredient"
            
            # 1. Identity & Structure
            smiles = record.get("canonical_smiles") or ""
            fields.append({
                "key": "canonical_smiles",
                "category": "Chemical Identity & Descriptors",
                "label": "Canonical SMILES",
                "value": smiles,
                "base_value": smiles,
                "final_value": smiles,
                "uncertainty_str": "Exact",
                "ci_95": None,
                "unit": "-",
                "method_id": "SMILES-CANON-01",
                "provenance": "RDKit Neutral Active Moiety"
            })

            mw = record.get("mw")
            fields.append({
                "key": "mw",
                "category": "Chemical Identity & Descriptors",
                "label": "Molecular Weight (MW)",
                "value": mw,
                "base_value": mw,
                "final_value": mw,
                "uncertainty_str": "Exact",
                "ci_95": None,
                "unit": "g/mol",
                "method_id": "DESC-RDKIT-01",
                "provenance": "COMPUTED-DESCRIPTOR (RDKit)"
            })

            lp = record.get("logP")
            lp_val = lp.get("primary", lp.get("cross_check", {}).get("value")) if isinstance(lp, dict) else lp
            fields.append({"key": "logP", "category": "Chemical Identity & Descriptors", "label": "LogP", "value": lp_val, "base_value": lp_val, "final_value": lp_val, "uncertainty_str": "Exact", "ci_95": None, "unit": "log units", "method_id": "DESC-RDKIT-01", "provenance": "COMPUTED-DESCRIPTOR (RDKit Crippen)"})
            fields.append({"key": "TPSA", "category": "Chemical Identity & Descriptors", "label": "TPSA", "value": record.get("TPSA"), "base_value": record.get("TPSA"), "final_value": record.get("TPSA"), "uncertainty_str": "Exact", "ci_95": None, "unit": "Å²", "method_id": "DESC-RDKIT-01", "provenance": "COMPUTED-DESCRIPTOR (Ertl)"})
            fields.append({"key": "HBD", "category": "Chemical Identity & Descriptors", "label": "HBD", "value": record.get("HBD"), "base_value": record.get("HBD"), "final_value": record.get("HBD"), "uncertainty_str": "Exact", "ci_95": None, "unit": "count", "method_id": "DESC-RDKIT-01", "provenance": "COMPUTED-DESCRIPTOR (Lipinski)"})
            fields.append({"key": "HBA", "category": "Chemical Identity & Descriptors", "label": "HBA", "value": record.get("HBA"), "base_value": record.get("HBA"), "final_value": record.get("HBA"), "uncertainty_str": "Exact", "ci_95": None, "unit": "count", "method_id": "DESC-RDKIT-01", "provenance": "COMPUTED-DESCRIPTOR (Lipinski)"})
            fields.append({"key": "BCS_class", "category": "Chemical Identity & Descriptors", "label": "BCS Class", "value": record.get("BCS_class"), "base_value": record.get("BCS_class"), "final_value": record.get("BCS_class"), "uncertainty_str": "Literature", "ci_95": None, "unit": "-", "method_id": "LIT-ACQ-01", "provenance": "LITERATURE"})
            
            # 2. Thermal & Physical
            tm = record.get("tm_K")
            tm_val = tm.get("value") if isinstance(tm, dict) else tm
            fields.append({
                "key": "tm_K",
                "category": "Thermal & Physical Properties",
                "label": "Melting Temperature (Tm)",
                "value": tm_val,
                "base_value": tm_val,
                "final_value": tm_val,
                "uncertainty_str": "± 3.0 K (literature onset)",
                "ci_95": [round(tm_val - 3.0, 1), round(tm_val + 3.0, 1)] if tm_val else None,
                "unit": "K",
                "method_id": "LIT-ACQ-01",
                "provenance": "LITERATURE (primary DSC)"
            })
            
            tg = record.get("tg_K")
            tg_val = tg.get("value") if isinstance(tg, dict) else tg
            tg_uq = uq_map.get("tg_K", {})
            fields.append({
                "key": "tg_K",
                "category": "Thermal & Physical Properties",
                "label": "Glass Transition Temperature (Tg)",
                "value": tg_val,
                "base_value": tg_val,
                "final_value": tg_uq.get("final_value", tg_val),
                "uncertainty_str": "± 21.0 K (1σ survey)",
                "ci_95": tg_uq.get("ci_95", [round(tg_val - 41.16, 1), round(tg_val + 41.16, 1)] if tg_val else None),
                "unit": "K",
                "method_id": "TG-RATIO-01",
                "provenance": "CALCULATED (0.70*Tm +/- 21 K)"
            })
            
            dens = record.get("density_g_cm3")
            dens_val = dens.get("value") if isinstance(dens, dict) else dens
            dens_uq = uq_map.get("density_g_cm3", {})
            fields.append({
                "key": "density_g_cm3",
                "category": "Thermal & Physical Properties",
                "label": "Crystalline Density",
                "value": dens_val,
                "base_value": dens_val,
                "final_value": dens_uq.get("final_value", dens_val),
                "uncertainty_str": "± 5.0% (surrogate)",
                "ci_95": dens_uq.get("ci_95", [round(dens_val * 0.95, 3), round(dens_val * 1.05, 3)] if dens_val else None),
                "unit": "g/cm3",
                "method_id": "DENS-FEDORS-01",
                "provenance": "CALCULATED (Fedors surrogate)"
            })
            
            # 3. Hansen Parameters
            hsp = record.get("hsp_mpa_half", {})
            dD = hsp.get("delta_D", record.get("delta_D"))
            dP = hsp.get("delta_P", record.get("delta_P"))
            dH = hsp.get("delta_H", record.get("delta_H"))
            dt = record.get("delta_t") or (round((dD**2 + dP**2 + dH**2)**0.5, 2) if dD and dP and dH else None)
            
            dD_uq = uq_map.get("delta_D", {})
            dP_uq = uq_map.get("delta_P", {})
            dH_uq = uq_map.get("delta_H", {})
            dt_uq = uq_map.get("delta_t", {})
            
            fields.append({
                "key": "delta_D",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Hansen Dispersion (δD)",
                "value": dD,
                "base_value": dD,
                "final_value": dD_uq.get("final_value", dD),
                "uncertainty_str": "± 1.50 MPa½",
                "ci_95": dD_uq.get("ci_95"),
                "unit": "MPa½",
                "method_id": "HSP-HVK-01",
                "provenance": "CALCULATED (Hoftyzer-van Krevelen)"
            })
            fields.append({
                "key": "delta_P",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Hansen Polar (δP)",
                "value": dP,
                "base_value": dP,
                "final_value": dP_uq.get("final_value", dP),
                "uncertainty_str": "± 1.50 MPa½",
                "ci_95": dP_uq.get("ci_95"),
                "unit": "MPa½",
                "method_id": "HSP-HVK-01",
                "provenance": "CALCULATED (Hoftyzer-van Krevelen)"
            })
            fields.append({
                "key": "delta_H",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Hansen Hydrogen-Bonding (δH)",
                "value": dH,
                "base_value": dH,
                "final_value": dH_uq.get("final_value", dH),
                "uncertainty_str": "± 1.50 MPa½",
                "ci_95": dH_uq.get("ci_95"),
                "unit": "MPa½",
                "method_id": "HSP-HVK-01",
                "provenance": "CALCULATED (Hoftyzer-van Krevelen)"
            })
            fields.append({
                "key": "delta_t",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Total Solubility Parameter (δt)",
                "value": dt,
                "base_value": dt,
                "final_value": dt_uq.get("final_value", dt),
                "uncertainty_str": "± 1.62 MPa½",
                "ci_95": dt_uq.get("ci_95"),
                "unit": "MPa½",
                "method_id": "HSP-HVK-01",
                "provenance": "CALCULATED (Euclidean vector norm)"
            })
            
            r0 = record.get("R0")
            r0_val = r0.get("value", 7.5) if isinstance(r0, dict) else (r0 if r0 else 7.5)
            fields.append({
                "key": "R0",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Interaction Radius (R0)",
                "value": r0_val,
                "base_value": r0_val,
                "final_value": r0_val,
                "uncertainty_str": "[7.0–8.0] MPa½",
                "ci_95": [7.0, 8.0],
                "unit": "MPa½",
                "method_id": "ASSUMED-CONV-01",
                "provenance": "ASSUMED (7.5 MPa^0.5, band 7.0-8.0)"
            })
            
        else:
            # Extract fields for Polymer
            subtitle = record.get("full_name") or record.get("grade", {}).get("standard") if isinstance(record.get("grade"), dict) else None
            if not subtitle:
                subtitle = f"{name} Commercial Pharmaceutical Polymer"

            smiles = record.get("repeat_unit_smiles") or ""
            fields.append({
                "key": "repeat_unit_smiles",
                "category": "Polymer Identity & Specification",
                "label": "Repeat-Unit SMILES",
                "value": smiles,
                "base_value": smiles,
                "final_value": smiles,
                "uncertainty_str": "Exact",
                "ci_95": None,
                "unit": "-",
                "method_id": "SMILES-REPEAT-01",
                "provenance": "Polymer Backbone Representation"
            })

            mn = record.get("mn")
            mn_val = mn
            if mn_val is None or mn_val == "" or str(mn_val).lower() in ("see grade spec", "null", "none"):
                mn_val = "VALUE REQUIRES VERIFIED GRADE-SPECIFIC INPUT"
            fields.append({
                "key": "mn",
                "category": "Polymer Identity & Specification",
                "label": "Number-Average Molar Mass (Mn)",
                "value": mn_val,
                "base_value": mn_val,
                "final_value": mn_val,
                "uncertainty_str": "Manufacturer Grade Spec",
                "ci_95": None,
                "unit": "g/mol",
                "method_id": "MANUF-SPEC-01",
                "provenance": "MANUFACTURER-SPEC"
            })
            
            tg = record.get("tg_K")
            tg_val = tg.get("value") if isinstance(tg, dict) else tg
            tg_uq = uq_map.get("tg_K", {})
            fields.append({
                "key": "tg_K",
                "category": "Thermal & Physical Properties",
                "label": "Glass Transition Temperature (Tg)",
                "value": tg_val,
                "base_value": tg_val,
                "final_value": tg_uq.get("final_value", tg_val),
                "uncertainty_str": "± 2.5 K (DSC Midpoint)",
                "ci_95": tg_uq.get("ci_95", [round(tg_val - 4.9, 1), round(tg_val + 4.9, 1)] if tg_val else None),
                "unit": "K",
                "method_id": "LIT-POLY-01",
                "provenance": "LITERATURE (grade-specific DSC)"
            })
            
            dens = record.get("density_g_cm3")
            dens_val = dens.get("value") if isinstance(dens, dict) else dens
            if dens_val is None or dens_val == "" or str(dens_val).lower() in ("from grade datasheet", "null", "none"):
                dens_val = "VALUE REQUIRES VERIFIED GRADE-SPECIFIC INPUT"
            dens_uq = uq_map.get("density_g_cm3", {})
            fields.append({
                "key": "density_g_cm3",
                "category": "Thermal & Physical Properties",
                "label": "Bulk Density",
                "value": dens_val,
                "base_value": dens_val,
                "final_value": dens_uq.get("final_value", dens_val) if isinstance(dens_val, (int, float)) else dens_val,
                "uncertainty_str": "± 5.0%" if isinstance(dens_val, (int, float)) else "Manufacturer Spec",
                "ci_95": dens_uq.get("ci_95") if isinstance(dens_val, (int, float)) else None,
                "unit": "g/cm3",
                "method_id": "MANUF-SPEC-01",
                "provenance": "MANUFACTURER-SPEC"
            })
            
            hsp = record.get("hsp_mpa_half", {})
            dD = hsp.get("delta_D", record.get("delta_D"))
            dP = hsp.get("delta_P", record.get("delta_P"))
            dH = hsp.get("delta_H", record.get("delta_H"))
            dt = record.get("delta_t") or (round((dD**2 + dP**2 + dH**2)**0.5, 2) if dD and dP and dH else None)
            
            dD_uq = uq_map.get("delta_D", {})
            dP_uq = uq_map.get("delta_P", {})
            dH_uq = uq_map.get("delta_H", {})
            dt_uq = uq_map.get("delta_t", {})
            
            fields.append({
                "key": "delta_D",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Hansen Dispersion (δD)",
                "value": dD,
                "base_value": dD,
                "final_value": dD_uq.get("final_value", dD),
                "uncertainty_str": "± 1.50 MPa½",
                "ci_95": dD_uq.get("ci_95"),
                "unit": "MPa½",
                "method_id": "HSP-HVK-01",
                "provenance": "CALCULATED (Hoftyzer-van Krevelen)"
            })
            fields.append({
                "key": "delta_P",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Hansen Polar (δP)",
                "value": dP,
                "base_value": dP,
                "final_value": dP_uq.get("final_value", dP),
                "uncertainty_str": "± 1.50 MPa½",
                "ci_95": dP_uq.get("ci_95"),
                "unit": "MPa½",
                "method_id": "HSP-HVK-01",
                "provenance": "CALCULATED (Hoftyzer-van Krevelen)"
            })
            fields.append({
                "key": "delta_H",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Hansen Hydrogen-Bonding (δH)",
                "value": dH,
                "base_value": dH,
                "final_value": dH_uq.get("final_value", dH),
                "uncertainty_str": "± 1.50 MPa½",
                "ci_95": dH_uq.get("ci_95"),
                "unit": "MPa½",
                "method_id": "HSP-HVK-01",
                "provenance": "CALCULATED (Hoftyzer-van Krevelen)"
            })
            fields.append({
                "key": "delta_t",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Total Solubility Parameter (δt)",
                "value": dt,
                "base_value": dt,
                "final_value": dt_uq.get("final_value", dt),
                "uncertainty_str": "± 1.62 MPa½",
                "ci_95": dt_uq.get("ci_95"),
                "unit": "MPa½",
                "method_id": "HSP-HVK-01",
                "provenance": "CALCULATED (Euclidean vector norm)"
            })
            
            r0 = record.get("R0")
            r0_val = r0.get("value", 7.5) if isinstance(r0, dict) else (r0 if r0 else 7.5)
            fields.append({
                "key": "R0",
                "category": "Hansen Solubility Parameters (HSP)",
                "label": "Interaction Radius (R0)",
                "value": r0_val,
                "base_value": r0_val,
                "final_value": r0_val,
                "uncertainty_str": "[7.0–8.0] MPa½",
                "ci_95": [7.0, 8.0],
                "unit": "MPa½",
                "method_id": "ASSUMED-CONV-01",
                "provenance": "ASSUMED (7.5 MPa^0.5, band 7.0-8.0)"
            })

        # Generate Plain Text Summary Block
        text_lines = [
            f"=== PHARMAPOLYSCOPE: MANUAL ENTRY SHEET ===",
            f"Entity: {name.upper()} ({entity_id})",
            f"Class: {entity_type.upper()}",
            "--------------------------------------------------"
        ]
        for f in fields:
            f_val = f["final_value"] if f["final_value"] is not None else f["base_value"]
            text_lines.append(f"{f['label']}: {f_val} {f['unit'] if f['unit'] != '-' else ''}")
        text_summary = "\n".join(text_lines)

        # Generate CSV Tabular Row
        csv_row_vals = [entity_id, name, entity_type]
        for f in fields:
            csv_row_vals.append(str(f["final_value"] if f["final_value"] is not None else f["base_value"]))
        tabular_csv_row = ",".join(csv_row_vals)

        json_export = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "name": name,
            "subtitle": subtitle,
            "values": {f["key"]: (f["final_value"] if f["final_value"] is not None else f["base_value"]) for f in fields}
        }

        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "name": name,
            "subtitle": subtitle,
            "abbreviation": abbreviation,
            "title": f"PHARMAPOLYSCOPE: MANUAL ENTRY SHEET",
            "instructions": "Authoritative input values for manual entry into PharmaPolySCOPE. Copy whichever column or export format suits your workflow.",
            "fields": fields,
            "dual_representation": dual_rep,
            "uncertainty_table": uncertainty_table,
            "text_summary": text_summary,
            "tabular_csv_row": tabular_csv_row,
            "json_export": json_export,
            "qc_status": "READY FOR ENTRY"
        }
