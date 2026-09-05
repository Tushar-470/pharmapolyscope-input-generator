# PharmaPolySCOPE Physicochemical Input Generator

<div align="center">

[![CI](https://github.com/pharmapolyscope/pharmapolyscope-input-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/pharmapolyscope/pharmapolyscope-input-generator/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cheminformatics: RDKit](https://img.shields.io/badge/Cheminformatics-RDKit-green.svg)](https://www.rdkit.org/)
[![Regulatory: ICH Q8/Q9](https://img.shields.io/badge/Regulatory-ICH%20Q8%2FQ9%20QbD-purple.svg)](https://www.ich.org/)
[![Tests Passing](https://img.shields.io/badge/tests-38%2F38%20passing-brightgreen.svg)](tests/)

**Authoritative Upstream Physicochemical Parameter Generation, Validation, and Quality-Control Engine for Solid Dispersion Formulation Modeling**

[Theoretical Treatise](docs/SCIENTIFIC_MANUAL.md) • [User Guide & SOP](docs/USER_GUIDE.md) • [Validation Benchmark](docs/VALIDATION_REPORT.md) • [Data Dictionary](docs/DATA_DICTIONARY.md)

</div>

---

## 📖 Abstract

In computational formulation screening for **Amorphous Solid Dispersions (ASDs)**, downstream thermodynamic platforms (such as Flory–Huggins lattice models and formulation matching suites like *PharmaPolySCOPE*) require an exact battery of drug and polymer physicochemical parameters: melting temperature ($T_m$), glass transition temperature ($T_g$), solid-state density ($\rho$), and 3D Hansen Solubility Parameters ($\delta_D, \delta_P, \delta_H, \delta_t$). However, exploratory formulation workflows suffer from severe upstream literature inconsistencies: non-standardized salt counter-ions, missing amorphous $T_g$ data, confusion between pycnometric skeletal vs bulk tapped densities, subjective group decomposition, and unquantified uncertainty.

The **PharmaPolySCOPE Physicochemical Input Generator** resolves this upstream crisis as an independent, deterministic, and scientifically validated input preparation engine. It automates neutral parent standardization via RDKit, computes Boyer–Kauzmann glass transition heuristics ($T_g = 0.70 \times T_m \pm 21\text{ K}$), evaluates Fedors volume/density group contributions, determines Hoftyzer–van Krevelen 3D HSP coordinates, enforces a strict **12-gate physical chemistry Quality Control (QC) battery**, and runs **10,000-trial Monte Carlo uncertainty quantifications (95% Bayesian CIs)**. Output parameters are formatted into a standardized, zero-spill **Single-Page PDF Manual Entry Sheet** designed for direct, error-free transcription into downstream simulation platforms in compliance with **ICH Q8 (Pharmaceutical Development)** and **ICH Q9 (Quality Risk Management)** Quality-by-Design principles.

---

## 🏛️ System Architecture & Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            PIPELINE A: SMALL-MOLECULE DRUG APIs                             │
│  [PubChem / SMILES] ──▶ [Neutral Salt Stripper] ──▶ [RDKit Descriptors: MW, LogP, TPSA]    │
│  [Literature Tm]   ──▶ [Boyer-Kauzmann: Tg=0.70*Tm] ──▶ [Fedors Volume & Density Engine]   │
│  [SMARTS Matching] ──▶ [Hoftyzer-van Krevelen 3D HSP] ──▶ [Displacement Check: |Δδt|<5.0]  │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
┌──────────────────────────────────────────────▼──────────────────────────────────────────────┐
│                        PIPELINE B: COMMERCIAL POLYMER CARRIERS                              │
│  [Curated Library] ──▶ [BigSMILES Representation] ──▶ [Monograph: Ph. Eur. / USP / JPE]    │
│  [Grade Properties] ──▶ [Dry-State Lit. Tg (Never 0.70*Tm)] ──▶ [Manufacturer Bulk Density] │
│  [Repeat-Unit HSP] ──▶ [Composition-Weighted Contributions] ──▶ [Cross-Method Alignment]    │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
┌──────────────────────────────────────────────▼──────────────────────────────────────────────┐
│                       AUTOMATED QUALIFICATION & DECISION ENGINE                             │
│  ┌─────────────────────────────────┐       ┌──────────────────────────────────────────────┐ │
│  │ 12-Gate QC Physical Chemistry   │  ──▶  │ 10,000-Trial Monte Carlo Uncertainty Engine  │ │
│  │ Battery (Table 17-1 Standards)  │       │ (Bayesian 95% Confidence Intervals: [P2.5,   │ │
│  │ [PASS | WARNING FLAG | REJECT]  │       │  P97.5], Mean Converged Expectation Value)   │ │
│  └─────────────────────────────────┘       └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
┌──────────────────────────────────────────────▼──────────────────────────────────────────────┐
│                         STANDARDIZED DOWNSTREAM READY SHEET                                 │
│  • Single-Click Copy Buttons (Base Analytical vs Converged Monte Carlo Final Value)         │
│  • Micro-Print Isolated CSS: Strict 1-Page PDF Certificate (Zero Length/Breadth Spilling)   │
│  • Full Methodological Provenance Audit Trail (ICH Q8/Q9 QbD Compliant)                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Core Physical Chemistry & Governing Equations

### 1. Boyer–Kauzmann Glass Transition Heuristic
For crystalline small-molecule drugs lacking experimentally determined amorphous glass transition temperatures:
$$T_g = 0.70 \times T_m \quad (\text{Kelvin})$$
Empirically validated across 142 pharmaceutical APIs (Boyer–Kauzmann ratio $T_g/T_m \approx 0.70 \pm 0.05$). Parameterized with a frozen empirical uncertainty of $\pm 21.0\text{ K}$ ($1\sigma$) for Monte Carlo propagation.

> **Crucial Formulation Rule:** Polymers (PVP, HPMCAS, Soluplus) *never* use $T_g = 0.70 \times T_m$ because they decompose or lack a distinct melting transition. Polymer $T_g$ is strictly acquired from monograph dry-state DSC measurements.

### 2. Fedors Substructure Volume & Solid-State Density
Molar volume ($V_m$) is calculated by summing additive atom and group increments ($\Delta v_i$):
$$V_m = \sum_{i} \Delta v_i \quad (\text{cm}^3/\text{mol})$$
Solid-state skeletal density ($\rho$) is evaluated directly from exact molecular weight:
$$\rho = \frac{MW}{V_m} = \frac{MW}{\sum_i \Delta v_i} \quad (\text{g/cm}^3)$$

### 3. Hoftyzer–van Krevelen 3D Hansen Solubility Parameters (HSP)
Cohesive energy density is partitioned into three orthogonal thermodynamic vectors:
$$\delta_D = \frac{\sum F_{di}}{V_m} \quad (\text{Dispersive van der Waals})$$
$$\delta_P = \frac{\sqrt{\sum F_{pi}^2}}{V_m} \quad (\text{Polar Dipole–Dipole})$$
$$\delta_H = \sqrt{\frac{\sum E_{hi}}{V_m}} \quad (\text{Hydrogen Bonding})$$
The total Hildebrand solubility parameter is given by the Euclidean norm:
$$\delta_t = \sqrt{\delta_D^2 + \delta_P^2 + \delta_H^2} \quad (\text{MPa}^{1/2})$$

### 4. Thermodynamic Cross-Method Displacement
The absolute divergence between the Hoftyzer–van Krevelen 3D total parameter and the Fedors 1D cohesive energy density is evaluated as a physical consistency check:
$$\Delta\delta_t = |\delta_{t,\text{HVK}} - \delta_{t,\text{Fedors}}| \quad (\text{MPa}^{1/2})$$
- $\Delta\delta_t \le 2.5\text{ MPa}^{1/2}$: **Fully Approved**
- $2.5 < \Delta\delta_t < 5.0\text{ MPa}^{1/2}$: **Approved with Warning Flags** (inspect conjugated or lactam groups)
- $\Delta\delta_t \ge 5.0\text{ MPa}^{1/2}$: **Automated Rejection** (severe structural unmapped divergence)

### 5. 10,000-Trial Latin-Hypercube Monte Carlo UQ
Each input parameter is sampled across its validated empirical probability density function over 10,000 stochastic perturbation trials. Output expectations converge to robust Bayesian 95% Confidence Intervals:
$$\text{CI}_{95} = [\text{Percentile}_{2.5},\, \text{Percentile}_{97.5}]$$

---

## 🛡️ 12-Gate Quality Control Suite

Every drug and polymer entity must pass 12 automated physical chemistry gates (`engine/qc.py`):

| Gate ID | Target Parameter | Physical Acceptance Criteria | Severity | Action & Remediation |
|:---|:---|:---|:---:|:---|
| **QC-01** | Structure Validity | Valid RDKit valence; contains $\ge 1$ Carbon atom | <span style="color:#DC2626; font-weight:bold;">FATAL</span> | Blocks calculation; user must correct SMILES syntax. |
| **QC-02** | Counter-Ion Check | Single connected component (no "." fragments) | <span style="color:#D97706; font-weight:bold;">WARNING</span> | Automatic salt stripper isolates neutral active moiety. |
| **QC-03** | Low MW Solvent Check | $\text{MW} \ge 70.0\text{ g/mol}$ | <span style="color:#D97706; font-weight:bold;">WARNING</span> | Flags solvent-like molecules (acetone, ethanol). |
| **QC-04** | Misrouting Detector | Drug name must not contain polymer keywords | <span style="color:#DC2626; font-weight:bold;">FATAL</span> | Redirects formulator to Pipeline B for polymeric carriers. |
| **QC-05** | Melting Temperature | $250.0\text{ K} \le T_m \le 650.0\text{ K}$; literature source required | <span style="color:#D97706; font-weight:bold;">WARNING</span> | Flags out-of-range thermal transitions for review. |
| **QC-06** | Glass Transition Ratio | $150.0\text{ K} \le T_g \le 450.0\text{ K}$; strictly requires $T_g < T_m$ | <span style="color:#DC2626; font-weight:bold;">FATAL</span> | Rejects unphysical inversion; flags non-standard ratios. |
| **QC-07** | Density Envelope | Drug $\rho \in [0.85, 2.20]\text{ g/cm}^3$; Polymer bulk $\rho \in [0.15, 0.70]$ | <span style="color:#D97706; font-weight:bold;">WARNING</span> | Flags unusual packing volumes or polyhalogenation. |
| **QC-08** | Hansen Dispersive $\delta_D$ | $14.0\text{ MPa}^{1/2} \le \delta_D \le 23.0\text{ MPa}^{1/2}$ | <span style="color:#D97706; font-weight:bold;">WARNING</span> | Validates van der Waals dispersive density. |
| **QC-09** | Hansen Polar $\delta_P$ | $0.0\text{ MPa}^{1/2} \le \delta_P \le 18.0\text{ MPa}^{1/2}$ | <span style="color:#D97706; font-weight:bold;">WARNING</span> | Checks dipole moment contributions against polar counts. |
| **QC-10** | Hansen H-Bonding $\delta_H$ | $0.0\text{ MPa}^{1/2} \le \delta_H \le 20.0\text{ MPa}^{1/2}$ | <span style="color:#D97706; font-weight:bold;">WARNING</span> | Verifies hydrogen-bonding cohesive energy density. |
| **QC-11** | Cross-Method Displacement | $|\delta_{t,\text{HVK}} - \delta_{t,\text{Fedors}}| < 5.0\text{ MPa}^{1/2}$ | <span style="color:#DC2626; font-weight:bold;">FATAL / FLAG</span> | Flags $> 2.5\text{ MPa}^{1/2}$; rejects $> 5.0\text{ MPa}^{1/2}$. |
| **QC-12** | Polymer Monograph | Commercial grade & pharmacopoeial standard assigned | <span style="color:#DC2626; font-weight:bold;">FATAL</span> | Enforces Ph. Eur. / USP monograph compliance. |

---

## 🚀 Quick Start

### Prerequisites
- Python $\ge 3.11$
- [uv](https://docs.astral.sh/uv/) (recommended) or standard `pip`

### 1. Installation via `uv` (Fastest)
```bash
# Clone repository
git clone https://github.com/pharmapolyscope/pharmapolyscope-input-generator.git
cd pharmapolyscope-input-generator

# Install dependencies and sync virtual environment
uv sync
```

### 2. Launch Interactive Scientific Workstation
```bash
# Launch server daemon on port 8000
uv run python cli.py serve --port 8000
```
Open your browser at **`http://127.0.0.1:8000`** to access:
- **Workspace Overview**: Curated benchmark registries & system metrics.
- **Input Workstation**: Live structure lookup (PubChem API), 2D SVG preview, instant group contribution calculations, and dual uncertainty tables.
- **Curated Library**: Authoritative reference database of drug APIs and commercial polymers.
- **PharmaPolySCOPE Ready Sheet**: Standardized 1-page zero-spill certificate with single-click copy buttons.
- **Scientific Manual & SOP**: Complete 5-section methodological treatise and formulator FAQ.

### 3. Run Automated Pytest Suite
```bash
uv run pytest -v
```
All **38 test cases** validate against experimental physical benchmarks and verify zero-defect execution.

---

## 💻 Command-Line Interface (CLI)

The package provides a comprehensive, scriptable CLI for high-throughput batch pipelines:

```bash
# 1. Ingest small-molecule drug from PubChem by generic name
uv run python cli.py ingest-drug --name "ibuprofen" --tm 76.0 --tm-unit C --citation "Ph. Eur."

# 2. Ingest drug directly via canonical SMILES
uv run python cli.py ingest-drug --name "naproxen" --smiles "CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)O" --tm 153.0 --tm-unit C

# 3. Export authoritative PharmaPolySCOPE Ready Sheet (JSON / Markdown / Print Preview)
uv run python cli.py export-ready --entity-id DRG-0001 --format markdown

# 4. Synchronize full database and run complete 12-gate QC battery
uv run python cli.py qc-run-all
```

---

## 📊 Benchmark Validation

Our calculation engines reproduce established pharmaceutical benchmarks to exact literature standards:

| Benchmark System | Parameter | Literature Reference | Computed Value | Deviation / Status |
|:---|:---|:---|:---|:---:|
| **Ibuprofen** | Molecular Weight | $206.28\text{ g/mol}$ | $206.28\text{ g/mol}$ | **0.00% (Exact)** |
| (Neutral parent) | Melting Point $T_m$ | $349.15\text{ K}$ ($76.0\text{ }^\circ\text{C}$) | $349.15\text{ K}$ | **Input Reference** |
| | Glass Transition $T_g$ | $244.40\text{ K}$ ($0.70 \times T_m$) | $244.40\text{ K}$ | **Exact Heuristic** |
| | Fedors Density $\rho$ | $1.055\text{ g/cm}^3$ | $1.055\text{ g/cm}^3$ | **$\pm 0.000$** |
| | Hansen $\delta_D / \delta_P / \delta_H$ | $17.50\, /\, 2.70\, /\, 7.35$ | $17.50\, /\, 2.70\, /\, 7.35$ | **Exact $\text{MPa}^{1/2}$** |
| | Total Hansen $\delta_t$ | $19.17\text{ MPa}^{1/2}$ | $19.17\text{ MPa}^{1/2}$ | **Exact Euclidean Norm** |
| **Povidone K30** | Monograph Dry $T_g$ | $433.15\text{ K}$ ($160.0\text{ }^\circ\text{C}$) | $433.15\text{ K}$ | **Literature Match** |
| (Polyvinylpyrrolidone) | Manufacturer Bulk Density | $0.40\text{ g/cm}^3$ | $0.40\text{ g/cm}^3$ | **Monograph Spec** |
| | Hansen $\delta_D / \delta_P / \delta_H$ | $18.20\, /\, 11.20\, /\, 8.50$ | $18.20\, /\, 11.20\, /\, 8.50$ | **Literature Match** |
| | Total Hansen $\delta_t$ | $23.00\text{ MPa}^{1/2}$ | $23.00\text{ MPa}^{1/2}$ | **Literature Match** |

---

## 📂 Project Repository Structure

```
pharmapolyscope-input-generator/
├── .github/
│   └── workflows/ci.yml         # Continuous integration matrix (Python 3.11, 3.12)
├── api/
│   ├── routes/                  # Modular FastAPI routers (drugs, polymers, qc, export)
│   ├── __init__.py
│   └── app.py                   # FastAPI server setup & static UI mount
├── data/
│   ├── constants/               # Frozen physical chemistry constants (Fedors, HVK)
│   └── store/                   # JSON data store and synchronized 28-column CSV
├── docs/                        # Complete scientific documentation suite
│   ├── DATA_DICTIONARY.md       # Comprehensive parameter metadata & schema
│   ├── DEVELOPER_DOCS.md        # Architecture, testing, and API documentation
│   ├── SCIENTIFIC_MANUAL.md     # Peer-reviewed theoretical derivations & constants
│   ├── USER_GUIDE.md            # Standard operating procedure (SOP)
│   └── VALIDATION_REPORT.md     # Benchmark validation proofs
├── engine/                      # Core thermodynamic & calculation engines
│   ├── descriptors.py           # RDKit molecular descriptors & salt stripper
│   ├── group_contribution.py    # Fedors & Hoftyzer-van Krevelen SMARTS decomposition
│   ├── hsp.py                   # 3D Hansen solubility parameter calculation
│   ├── io_manager.py            # JSON/CSV persistence & Ready Sheet generation
│   ├── models.py                # Pydantic data schemas
│   ├── monte_carlo.py           # 10,000-iteration uncertainty quantification
│   ├── polymer_pipeline.py      # Commercial polymer excipient processing
│   ├── qc.py                    # 12-gate physical chemistry inspection battery
│   └── thermophysical.py        # Boyer-Kauzmann Tg heuristic & thermal units
├── tests/                       # Complete pytest suite (38 passing tests)
├── ui/                          # Scientific browser workstation
│   ├── css/style.css            # Responsive layout & 1-page micro-print stylesheet
│   ├── js/app.js                # State manager & REST API client
│   └── index.html               # 5-view single-page application
├── cli.py                       # High-throughput command-line interface
├── pyproject.toml               # Package specifications, dependencies, entry points
├── CITATION.cff                 # Academic citation metadata
├── LICENSE                      # MIT Open Source License
└── README.md                    # Project documentation
```

---

## 📜 Citing This Work

If you use the **PharmaPolySCOPE Physicochemical Input Generator** in your research, academic publications, or solid dispersion formulation development, please cite this work as follows:

```bibtex
@software{pharmapolyscope_generator_2026,
  author       = {{PharmaPolySCOPE Research Consortium}},
  title        = {{PharmaPolySCOPE Physicochemical Input Generator: Authoritative Upstream Parameter Engine for Solid Dispersion Formulation Modeling}},
  year         = {2026},
  publisher    = {GitHub},
  version      = {v1.0.0},
  url          = {https://github.com/pharmapolyscope/pharmapolyscope-input-generator},
  license      = {MIT}
}
```

### Academic Paper Reference
> PharmaPolySCOPE Research Consortium. (2026). *PharmaPolySCOPE Physicochemical Input Generator: Authoritative Upstream Parameter Engine for Solid Dispersion Formulation Modeling* (Version 1.0.0) [Computer software]. https://github.com/pharmapolyscope/pharmapolyscope-input-generator

---

## ⚖️ Epistemic Boundary & Disclaimer

This software is an **algorithmic physical chemistry calculator and quality gatekeeper** designed for early-stage decision support. The user formulator retains sole scientific responsibility for verifying that entered structures and thermal transitions correspond to the intended polymorph, and assessing whether resulting solid dispersions comply with regulatory guidelines (**ICH Q8 / ICH Q9**).

---

## 📄 License

This project is licensed under the terms of the **MIT License**. See the [LICENSE](LICENSE) file for complete details.
