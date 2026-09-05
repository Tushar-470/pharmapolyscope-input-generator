"""
Command-Line Interface (CLI) for Pharmapolyscope Physicochemical Input Generator.
Provides batch validation, pair screening, and Pharmapolyscope-ready sheet exports.
"""

import sys
import argparse
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from engine.io_manager import IOManager
from engine.qc import QualityControlEngine
from engine.pair_metrics import evaluate_drug_polymer_pair


def main():
    parser = argparse.ArgumentParser(
        prog="pharmapolyscope-input-generator",
        description="Independent Physicochemical Input Generator for Pharmapolyscope"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 1. Server command
    server_parser = subparsers.add_parser("serve", help="Launch the local scientific web application")
    server_parser.add_argument("--host", default="127.0.0.1", help="Host IP (default: 127.0.0.1)")
    server_parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # 2. Validate command
    subparsers.add_parser("validate", help="Run automated QC battery across all stored records")

    # 3. Export Ready command
    export_parser = subparsers.add_parser("export-ready", help="Print Pharmapolyscope-Ready manual entry sheet")
    export_parser.add_argument("--id", required=True, help="Entity ID (e.g. DRG-0001, POL-0001)")

    # 4. Screen Pair command
    pair_parser = subparsers.add_parser("screen-pair", help="Screen a drug-polymer pair")
    pair_parser.add_argument("--drug", required=True, help="Drug Entity ID (e.g. DRG-0001)")
    pair_parser.add_argument("--polymer", required=True, help="Polymer Entity ID (e.g. POL-0001)")
    pair_parser.add_argument("--r0", type=float, default=7.5, help="Assigned R0 radius (default: 7.5)")

    # 5. Sync CSV command
    subparsers.add_parser("sync-csv", help="Synchronize input_dataset.csv from input_dataset.json")

    args = parser.parse_args()

    io_mgr = IOManager()
    qc_engine = QualityControlEngine()

    if args.command == "serve":
        print(f"Starting Pharmapolyscope Physicochemical Input Generator on http://{args.host}:{args.port}")
        uvicorn.run("api.app:app", host=args.host, port=args.port, reload=args.reload)

    elif args.command == "validate":
        print("Executing Automated QC Battery on Dataset Records...\n")
        data = io_mgr.load_dataset()
        records = data.get("records", [])
        
        all_passed = True
        for r in records:
            e_id = r.get("entity_id")
            name = r.get("name")
            e_type = r.get("entity_type")
            
            if e_type == "drug":
                res = qc_engine.run_drug_qc(r)
            else:
                res = qc_engine.run_polymer_qc(r)
                
            status = res["status"]
            print(f"[{status}] {e_id} - {name} ({e_type})")
            if res.get("warnings"):
                for w in res["warnings"]:
                    print(f"   [FLAG] {w}")
            if res.get("errors"):
                all_passed = False
                for e in res["errors"]:
                    print(f"   [ERROR] {e}")
            print()
            
        print("QC Execution Complete.")
        if not all_passed:
            sys.exit(1)

    elif args.command == "export-ready":
        try:
            sheet = io_mgr.generate_pharmapolyscope_ready_sheet(args.id)
            print("=" * 75)
            print(sheet["title"])
            print("=" * 75)
            print(f"Entity: {sheet['name']} ({sheet['entity_id']})")
            print(f"QC Status: {sheet['qc_status']}")
            print("-" * 75)
            print(f"{'PARAMETER':<35} | {'VALUE':<18} | {'UNIT':<10}")
            print("-" * 75)
            for f in sheet["fields"]:
                val_str = str(f["value"]) if f["value"] is not None else "null"
                print(f"{f['label']:<35} | {val_str:<18} | {f['unit']:<10}")
            print("-" * 75)
            print(f"INSTRUCTIONS: {sheet['instructions']}")
            print("=" * 75)
        except Exception as e:
            print(f"Error generating sheet: {e}")
            sys.exit(1)

    elif args.command == "screen-pair":
        data = io_mgr.load_dataset()
        records = data.get("records", [])
        d_matches = [r for r in records if r.get("entity_id") == args.drug]
        p_matches = [r for r in records if r.get("entity_id") == args.polymer]
        
        if not d_matches or not p_matches:
            print("Specified drug or polymer ID not found.")
            sys.exit(1)
            
        res = evaluate_drug_polymer_pair(d_matches[0], p_matches[0], args.r0)
        print("=" * 70)
        print(f"PAIR MISCIBILITY SCREEN: {res['drug_name']} + {res['polymer_name']}")
        print("=" * 70)
        print(f"Drug delta_t:              {res['delta_t_drug']} MPa^0.5")
        print(f"Polymer delta_t:           {res['delta_t_polymer_tabulated']} MPa^0.5")
        print(f"Greenhalgh Delta delta_t:  {res['greenhalgh_delta_t_tabulated']} MPa^0.5 -> {res['greenhalgh_verdict']}")
        print(f"Hansen Distance Ra:        {res['hansen_distance_Ra']} MPa^0.5")
        print(f"RED @ R0=7.0:              {res['RED']['at_R0_7_0']}")
        print(f"RED @ R0=7.5 (standard):   {res['RED']['at_R0_7_5']}")
        print(f"RED @ R0=8.0:              {res['RED']['at_R0_8_0']}")
        print(f"Stability Classification:  {res['stability_grade']}")
        for note in res.get("qc_notes", []):
            print(f"NOTE: {note}")
        print("=" * 70)

    elif args.command == "sync-csv":
        data = io_mgr.load_dataset()
        io_mgr.export_csv_from_json(data)
        print(f"Synchronized {io_mgr.csv_path} from {io_mgr.json_path} successfully.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
