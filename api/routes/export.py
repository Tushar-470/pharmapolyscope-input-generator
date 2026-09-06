"""
Export and Import API routes for JSON, CSV, and Pharmapolyscope-ready manual entry sheets.
"""

import os
import json
from fastapi import APIRouter, HTTPException, Response
from engine.io_manager import IOManager

router = APIRouter(prefix="/api/export", tags=["export"])

io_mgr = IOManager()


def generate_report_html(sheet: dict) -> str:
    category_order = [
        "Chemical Identity & Descriptors",
        "Polymer Identity & Specification",
        "Thermal & Physical Properties",
        "Hansen Solubility Parameters (HSP)"
    ]
    groups = {}
    for f in sheet.get("fields", []):
        cat = f.get("category", "General Properties")
        groups.setdefault(cat, []).append(f)

    sorted_categories = sorted(
        groups.keys(),
        key=lambda c: category_order.index(c) if c in category_order else 99
    )

    rows_html = []
    for cat in sorted_categories:
        rows_html.append(f"""
        <tr class="category-row">
            <td colspan="6"><strong>{cat}</strong></td>
        </tr>
        """)
        for f in groups[cat]:
            label = f.get("label", "")
            key = f.get("key", "")
            base_val = f.get("base_value", f.get("value", "-"))
            final_val = f.get("final_value", f.get("value", "-"))
            ci_95 = f.get("ci_95")
            unit = f.get("unit", "-") or "-"
            method_id = f.get("method_id", "COMPUTED")
            is_smiles = "smiles" in key.lower()
            
            ci_str = f.get("uncertainty_str", "-") or "-"
            if ci_95 and isinstance(ci_95, list) and len(ci_95) == 2:
                ci_display = f"{ci_str} <span class='ci-bracket'>[{ci_95[0]}–{ci_95[1]}]</span>"
            else:
                ci_display = ci_str

            base_val_str = f"{base_val:.4g}" if isinstance(base_val, float) else str(base_val if base_val is not None else "-")
            final_val_str = f"{final_val:.4g}" if isinstance(final_val, float) else str(final_val if final_val is not None else "-")

            val_class = "code-val" if is_smiles else "val-numeric"
            final_val_class = "code-val final" if is_smiles else "val-numeric final"

            rows_html.append(f"""
            <tr>
                <td class="param-label">{label}</td>
                <td class="{val_class}">{base_val_str}</td>
                <td class="{final_val_class}">{final_val_str}</td>
                <td class="ci-cell">{ci_display}</td>
                <td class="unit-cell">{unit}</td>
                <td class="method-cell"><span class="badge">{method_id}</span></td>
            </tr>
            """)

    table_rows = "".join(rows_html)
    name = sheet.get("name", "Unknown").upper()
    entity_id = sheet.get("entity_id", "")
    entity_type = sheet.get("entity_type", "entity").upper()
    subtitle = sheet.get("subtitle", "")
    qc_status = sheet.get("qc_status", "READY FOR ENTRY")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PharmaPolySCOPE Report - {entity_id} ({name})</title>
<style>
  @page {{
    size: portrait;
    margin: 8mm 10mm;
  }}
  *, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 8pt;
    line-height: 1.2;
    color: #0F172A;
    background: #F8FAFC;
    padding: 16px;
  }}
  .report-card {{
    max-width: 820px;
    margin: 0 auto;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .no-print-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #E2E8F0;
  }}
  .btn-print {{
    background: #0284C7;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
  }}
  .btn-print:hover {{ background: #0369A1; }}
  .header-box {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 2px solid #0284C7;
    padding-bottom: 6px;
    margin-bottom: 10px;
  }}
  .title {{ font-size: 13pt; font-weight: 800; color: #0F172A; letter-spacing: -0.2px; }}
  .subtitle {{ font-size: 9.5pt; font-weight: 600; color: #0284C7; margin-top: 2px; }}
  .meta-row {{ font-size: 7.5pt; color: #475569; margin-top: 4px; display: flex; gap: 8px; align-items: center; }}
  .status-pill {{
    background: #ECFDF5;
    color: #047857;
    border: 1px solid #10B981;
    border-radius: 9999px;
    padding: 3px 8px;
    font-size: 8pt;
    font-weight: 700;
  }}
  .info-bar {{
    background: #F0F9FF;
    border-left: 3px solid #0284C7;
    padding: 6px 10px;
    font-size: 7.5pt;
    color: #0369A1;
    margin-bottom: 10px;
    border-radius: 3px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    margin-bottom: 8px;
  }}
  col.col-param {{ width: 23%; }}
  col.col-base {{ width: 17%; }}
  col.col-final {{ width: 18%; }}
  col.col-ci {{ width: 19%; }}
  col.col-unit {{ width: 8%; }}
  col.col-method {{ width: 15%; }}
  th, td {{
    border: 0.5pt solid #CBD5E1;
    padding: 3px 5px;
    vertical-align: middle;
    word-break: break-all;
    overflow-wrap: anywhere;
  }}
  th {{
    background: #F1F5F9;
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
    color: #1E293B;
    text-align: left;
  }}
  th.num-header {{ text-align: right; }}
  .category-row td {{
    background: #F8FAFC;
    color: #0F172A;
    font-size: 7.5pt;
    font-weight: 700;
    padding: 3px 5px;
    border-top: 1pt solid #94A3B8;
  }}
  .param-label {{ font-size: 7.5pt; font-weight: 600; color: #0284C7; }}
  .val-numeric {{ font-size: 7.5pt; text-align: right; font-weight: 600; }}
  .val-numeric.final {{ color: #1D4ED8; font-weight: 700; background: #EFF6FF; }}
  .code-val {{ font-family: monospace; font-size: 6.5pt; }}
  .code-val.final {{ color: #1D4ED8; background: #EFF6FF; }}
  .ci-cell {{ font-size: 7pt; color: #334155; }}
  .ci-bracket {{ font-size: 6.5pt; color: #64748B; }}
  .unit-cell {{ font-size: 7.5pt; font-weight: 600; text-align: center; }}
  .method-cell {{ text-align: center; }}
  .badge {{
    display: inline-block;
    padding: 1px 4px;
    font-size: 6.5pt;
    border-radius: 9999px;
    border: 0.5pt solid #CBD5E1;
    background: #FFFFFF;
    color: #475569;
  }}
  .footer-row {{
    display: flex;
    justify-content: space-between;
    font-size: 6.8pt;
    color: #64748B;
    border-top: 0.5pt solid #E2E8F0;
    padding-top: 6px;
    margin-top: 6px;
  }}
  @media print {{
    body {{ background: #FFFFFF; padding: 0; }}
    .report-card {{ border: none; box-shadow: none; padding: 0; max-width: 100%; }}
    .no-print-bar {{ display: none !important; }}
    th, td, .val-numeric.final, .status-pill {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    tr {{ page-break-inside: avoid; break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="report-card">
  <div class="no-print-bar">
    <div style="font-size: 8.5pt; color: #64748B;">PharmaPolySCOPE Official Physicochemical Certificate</div>
    <div>
      <button class="btn-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
    </div>
  </div>

  <div class="header-box">
    <div>
      <div class="title">PHARMAPOLYSCOPE: MANUAL ENTRY SHEET</div>
      <div class="subtitle">{subtitle or name}</div>
      <div class="meta-row">
        <span><strong>Entity ID:</strong> <span style="font-family: monospace; font-weight: 700; color: #0284C7;">{entity_id}</span></span>
        <span style="color: #CBD5E1;">|</span>
        <span><strong>Class:</strong> {entity_type}</span>
        <span style="color: #CBD5E1;">|</span>
        <span><strong>Model:</strong> 10k Monte Carlo UQ (seed: 42)</span>
      </div>
    </div>
    <div>
      <span class="status-pill">✓ {qc_status}</span>
    </div>
  </div>

  <div class="info-bar">
    <strong>Authoritative Formulation Specification:</strong> Validated physicochemical parameters for manual entry into PharmaPolySCOPE. Transcribe either the Nominal Base or 10k MC Converged Final values into downstream ASD miscibility models.
  </div>

  <table>
    <colgroup>
      <col class="col-param">
      <col class="col-base">
      <col class="col-final">
      <col class="col-ci">
      <col class="col-unit">
      <col class="col-method">
    </colgroup>
    <thead>
      <tr>
        <th>Parameter</th>
        <th class="num-header">Nominal Base (Before UQ)</th>
        <th class="num-header">10k MC Final (After UQ)</th>
        <th>Uncertainty (95% CI)</th>
        <th style="text-align: center;">Unit</th>
        <th style="text-align: center;">Method</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>

  <div class="footer-row">
    <span>🔬 PharmaPolySCOPE Upstream Physicochemical Generator</span>
    <span>Quality-Assured Thermodynamic Dataset • Exact Single-Page Specification</span>
  </div>
</div>
</body>
</html>"""


@router.get("/pharmapolyscope_ready/{entity_id}")
def get_pharmapolyscope_ready_sheet(entity_id: str):
    """
    Returns the clean, dedicated summary sheet of values and units
    for manual transcription into Pharmapolyscope.
    """
    try:
        sheet = io_mgr.generate_pharmapolyscope_ready_sheet(entity_id)
        return sheet
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/report_html/{entity_id}")
def download_report_html(entity_id: str, download: bool = False):
    """
    Generates an authoritative, standalone, print-ready HTML report
    for the specified entity.
    """
    try:
        sheet = io_mgr.generate_pharmapolyscope_ready_sheet(entity_id)
        html_content = generate_report_html(sheet)
        headers = {}
        if download:
            clean_name = "".join(c if c.isalnum() else "_" for c in sheet.get("name", "entity"))
            filename = f"PharmaPolySCOPE_Report_{entity_id}_{clean_name}.html"
            headers["Content-Disposition"] = f"attachment; filename={filename}"
        return Response(content=html_content, media_type="text/html", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/csv")
def download_csv():
    """Streams the current input_dataset.csv file."""
    if not os.path.exists(io_mgr.csv_path):
        data = io_mgr.load_dataset()
        io_mgr.export_csv_from_json(data)
        
    with open(io_mgr.csv_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=input_dataset.csv"}
    )


@router.get("/json")
def download_json():
    """Streams the current input_dataset.json file."""
    data = io_mgr.load_dataset()
    content = json.dumps(data, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=input_dataset.json"}
    )
