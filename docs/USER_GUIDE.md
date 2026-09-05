# User Guide: Standard Operating Procedure (SOP)
## Pharmapolyscope Physicochemical Input Generator

### Purpose
This User Guide provides the operational protocol for generating, quality-controlling, documenting, and exporting physicochemical input values for manual entry into the frozen **Pharmapolyscope** software.

---

### Step-by-Step 11-Step Workflow

#### Step 1: Structure Acquisition
1. Open the application at `http://127.0.0.1:8000` or launch via CLI `uv run python cli.py serve`.
2. Navigate to **Pipeline A: Drugs**.
3. In the PubChem Compound Search field, enter the generic compound name (e.g. `ibuprofen`, `naproxen`, `indomethacin`) or numeric PubChem CID (e.g. `3672`).
4. Click **Search**. The system retrieves canonical SMILES, IUPAC name, formula, and computed properties.

#### Step 2: Identity & Neutral Parent Verification
1. Inspect the 2D structure depiction.
2. Ensure the calculation entity represents the neutral free acid or free base of the active moiety.
3. Confirm stereochemistry corresponds to the marketed formulation.

#### Step 3: Melting Temperature ($T_m$) Acquisition
1. Apply the deterministic Table 4-1 hierarchy:
   - **Priority 1**: Primary peer-reviewed DSC onset of the stable polymorph at 25 °C.
   - **Priority 2**: Alternative polymorph DSC onset.
   - **Priority 3**: Curated database range midpoint (e.g. Merck Index / PubChem).
   - **Priority 4**: Manufacturer certificate of analysis.
   - **Priority 5**: Enantiomer/racemate approximation (`ESTIMATED`, $\pm 10\text{ K}$ uncertainty).
2. Enter the temperature in Celsius or Kelvin (automatic conversion with offset $+273.15$).

#### Step 4: Glass Transition Temperature ($T_g$) Calculation
1. The system automatically computes drug glass transition temperature:
   $$T_g = 0.70 \times T_m \quad (\text{Kelvin})$$
2. Attaches standard uncertainty: $\pm 21\text{ K}$ ($1\sigma$).

#### Step 5: Fedors Density Calculation
1. The system matches functional groups via SMARTS patterns against the Fedors (1974) database.
2. Computes molar volume $V_m = \sum \Delta V_i$ and surrogate density $\rho = M / V_m$.
3. If experimental pycnometric density is available, enter it to verify volume consistency ($< 15\%$).

#### Step 6: Hoftyzer–van Krevelen Hansen Parameter Calculation
1. The system computes partial parameters:
   $$\delta_D = \frac{\sum F_{d,i}}{V_m},\quad \delta_P = \frac{\sqrt{\sum F_{p,i}^2}}{V_m},\quad \delta_H = \sqrt{\frac{\sum E_{h,i}}{V_m}}$$
2. Calculates total solubility parameter $\delta_t = \sqrt{\delta_D^2 + \delta_P^2 + \delta_H^2}$.
3. Computes secondary Fedors total parameter $\delta_{t,\text{Fedors}}$ and reports displacement.

#### Step 7: Molecular Descriptors Generation
1. Molecular Weight (MW), Crippen LogP, Ertl TPSA, and Lipinski HBD/HBA counts are computed via pinned RDKit and cross-checked against PubChem.

#### Step 8: Unit Normalization
1. All temperatures are verified in Kelvin (K).
2. All densities are in $\text{g/cm}^3$.
3. All solubility parameters are in $\text{MPa}^{1/2}$.

#### Step 9: Automated Quality Control Battery
1. Click **Save to Store**. The automated QC engine verifies ranges, consistency, and provenance completeness.
2. Records receive status `APPROVED` or `APPROVED with flags`.

#### Step 10: Polymer Carrier Processing (Pipeline B)
1. Navigate to **Pipeline B: Polymers**.
2. Select the specific polymer carrier and commercial grade (e.g. Povidone K30, Copovidone VA64, HPMC E5, HPMCAS-M, Soluplus).
3. Review grade specifications: $M_n$, bulk density, dry-state literature $T_g$.
4. Click **Save Polymer Record to Store**.

#### Step 11: Manual Transfer into PharmaPolySCOPE
1. Navigate to **PharmaPolySCOPE Ready Sheet**.
2. Select the target Drug or Polymer.
3. Transcribe each validated value into the corresponding field in the frozen PharmaPolySCOPE interface, or use single-click copy buttons.
4. Perform second-person spot check or export the 1-page PDF certificate before executing formulation screening.
