# Developer Documentation
## Architecture, Schemas, API Endpoints, and Extension Guide

### Architecture Overview
The system is built as a modular Python package adhering to strict separation of concerns:
- `engine/`: Pure scientific logic, stateless calculators, SMARTS pattern matching, and QC rules.
- `data/`: Version-controlled JSON constant registries and JSON/CSV storage.
- `api/`: FastAPI REST endpoints exposing calculation, verification, and import/export capabilities.
- `ui/`: Lightweight, dependency-free vanilla HTML5/CSS/JavaScript single page scientific application.
- `cli.py`: Automated command line interface for headless execution and continuous integration.

---

### REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/drugs` | List all saved drug records in dataset |
| `GET` | `/api/drugs/{id}` | Retrieve specific drug record by entity ID |
| `POST` | `/api/drugs/search_pubchem` | Search PubChem PUG REST by name or numeric CID |
| `POST` | `/api/drugs/calculate` | Execute live Pipeline A calculation from SMILES |
| `POST` | `/api/drugs/save` | Validate and commit drug record to dataset store |
| `DELETE` | `/api/drugs/{id}` | Delete drug record and log audit event |
| `GET` | `/api/polymers` | List all saved polymer records |
| `GET` | `/api/polymers/curated_carriers` | List curated polymer carriers and commercial grades |
| `POST` | `/api/polymers/save` | Validate and commit polymer record to store |
| `GET` | `/api/pairs/matrix` | Compute $M \times N$ pair miscibility matrix |
| `POST` | `/api/pairs/screen_pair` | Screen specific Drug-Polymer pair ($R_a$, RED, $\Delta \delta_t$) |
| `POST` | `/api/pairs/resampling_sensitivity` | Run 1,000 Monte Carlo HSP resampling iterations |
| `GET` | `/api/qc/summary` | Retrieve dashboard overview and active method registry |
| `POST` | `/api/qc/run_all` | Re-evaluate QC checks across all stored records |
| `GET` | `/api/export/pharmapolyscope_ready/{id}` | Generate dedicated manual-entry summary sheet |
| `GET` | `/api/export/csv` | Download synchronized `input_dataset.csv` |
| `GET` | `/api/export/json` | Download structured `input_dataset.json` source of truth |
| `GET` | `/api/audit` | Retrieve chronological audit trail events |

---

### Command Line Interface (CLI)
```bash
# Launch Web Application
uv run python cli.py serve --port 8000

# Execute Automated QC Battery
uv run python cli.py validate

# Generate Pharmapolyscope-Ready Sheet
uv run python cli.py export-ready --id DRG-0001
uv run python cli.py export-ready --id POL-0001

# Screen Drug-Polymer Pair
uv run python cli.py screen-pair --drug DRG-0001 --polymer POL-0001

# Synchronize CSV Export from JSON Store
uv run python cli.py sync-csv
```
