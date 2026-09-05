# Contributing to PharmaPolySCOPE Input Generator

Thank you for your interest in contributing to the **PharmaPolySCOPE Physicochemical Input Generator**! We welcome contributions from pharmaceutical scientists, physical chemists, formulation engineers, and software developers.

---

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to the project maintainers.

---

## How to Contribute

### 1. Reporting Bugs
When reporting a bug, please create an Issue detailing:
- Clear description of the unexpected behavior or physical calculation discrepancy.
- Exact input parameters: generic name, PubChem CID, canonical SMILES, melting temperature ($T_m$), and literature source.
- Expected vs observed thermodynamic values ($T_g$, molar volume, density, $\delta_D$, $\delta_P$, $\delta_H$).
- Operating system and Python version.

### 2. Suggesting Excipients or Group Contributions
To propose additions to the commercial polymer library or functional group constants:
- Provide peer-reviewed literature citations or pharmacopoeial monograph references (Ph. Eur., USP, NF, JPE).
- Include tabulated experimental dry-state $T_g$, manufacturer bulk tapped densities, and published 3D Hansen solubility parameters.
- Provide the BigSMILES repeat-unit representation.

### 3. Pull Request Process
1. **Fork the repository** and create a feature branch (`git checkout -b feature/new-functional-group`).
2. **Install development dependencies**:
   ```bash
   uv sync
   ```
3. **Write Unit Tests**:
   - Add targeted tests in `tests/` validating your calculation against peer-reviewed benchmark figures.
4. **Verify Quality Control & Linting**:
   ```bash
   uv run pytest
   node -c ui/js/app.js
   ```
5. **Commit with Clear Messages**:
   - Use conventional commit standards (e.g. `feat: add sulfonate group contributions to Fedors registry`, `fix: enforce strict boundary on QC-08`).
6. **Submit a Pull Request**:
   - Describe the scientific rationale, include literature references, and confirm that all automated tests pass.

---

## Scientific Rigor & Epistemic Boundary

All calculation engines follow strict physical chemistry equations documented in the in-app **Scientific Manual & SOP Protocol**. Algorithmic modifications must preserve deterministic reproducibility (default random seed `42`) and cite peer-reviewed thermodynamic literature (e.g., Boyer–Kauzmann, Fedors 1974, Hoftyzer–van Krevelen 1990).
