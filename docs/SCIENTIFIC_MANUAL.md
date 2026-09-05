# Scientific Method Manual
## Theoretical Foundations, Frozen Equations, and Constant Registries

### 1. Architectural Design Principles
The Input Generator is governed by the core principle of **epistemic transparency**:
- Standardize computational methodology where computation is scientifically legitimate.
- Preserve external inputs, literature measurements, and vendor specifications where properties cannot legitimately be generated from a universal formula.
- Do not manufacture false precision.

---

### 2. Dual Pipeline Specifications

```text
PIPELINE A (DRUGS)                          PIPELINE B (POLYMERS)
Drug Identity & PubChem CID                 Carrier & Named Commercial Grade
         ↓                                           ↓
Neutral-Parent Canonical SMILES             Curated Repeat-Unit SMILES
         ↓                                           ↓
RDKit Descriptors (MW, LogP, TPSA, HBD, HBA) Vendor Mn / Bulk Density / Lit Tg
         ↓                                           ↓
Deterministic Tm Acquisition (Table 4-1)    Composition Weighting (Copolymers/Esters)
         ↓                                           ↓
Tg = 0.70 * Tm (+/- 21 K)                   Repeat-Unit Hoftyzer-van Krevelen HSP
         ↓                                           ↓
Fedors Molar Volume & Density               Assigned R0 = 7.5 MPa^0.5
         ↓                                           ↓
Hoftyzer-van Krevelen HSP                   Automated QC & Provenance Attachment
         ↓                                           ↓
Assigned R0 = 7.5 MPa^0.5                   PHARMAPOLYSCOPE MANUAL ENTRY SHEET
         ↓
Automated QC Battery & Provenance
         ↓
PHARMAPOLYSCOPE MANUAL ENTRY SHEET
```

---

### 3. Frozen Scientific Equations

#### 3.1 Drug Glass Transition Temperature
$$\boxed{T_g = 0.70 \times T_m} \quad (T \in \text{Kelvin}, \text{drugs only})$$
- Method ID: `TG-RATIO-01`
- Reference: Koop et al. (2011), *Phys. Chem. Chem. Phys.*, 13(40), 19238–19255.
- Uncertainty: $\pm 21\text{ K}$ ($1\sigma$).
- Independent Validation MAE: $19.7\text{ K}$ (Armeli et al. 2023).

#### 3.2 Fedors Group Contribution Molar Volume & Density
$$\boxed{V_m = \sum_{i=1}^n \Delta V_i} \quad (\text{cm}^3/\text{mol})$$
$$\boxed{\rho = \frac{M}{V_m}} \quad (\text{g/cm}^3)$$
- Method ID: `DENS-FEDORS-01`
- Reference: Fedors, R.F. (1974), *Polym. Eng. Sci.*, 14(2), 147–154.
- Amorphous convention: $\rho_{am} \approx 0.95 \times \rho_{cr}$ (Hancock & Zografi 1997; Browne et al. 2020).

#### 3.3 Hoftyzer–van Krevelen Hansen Solubility Parameters
$$\boxed{\delta_D = \frac{\sum_{i=1}^n F_{d,i}}{V_m}}, \quad \boxed{\delta_P = \frac{\sqrt{\sum_{i=1}^n F_{p,i}^2}}{V_m}}, \quad \boxed{\delta_H = \sqrt{\frac{\sum_{i=1}^n E_{h,i}}{V_m}}}$$
$$\boxed{\delta_t = \sqrt{\delta_D^2 + \delta_P^2 + \delta_H^2}} \quad (\text{MPa}^{1/2})$$
- Method ID: `HSP-HVK-01`
- Reference: van Krevelen, D.W. (1990), *Properties of Polymers* (3rd ed.), Elsevier.
- Secondary Method: Fedors Total Parameter:
  $$\delta_{t,\text{Fedors}} = \sqrt{\frac{\sum \Delta U_i}{\sum \Delta V_i}} \times 2.0455 \quad (\text{MPa}^{1/2})$$

#### 3.4 Hansen Distance and Relative Energy Difference (RED)
$$\boxed{R_a^2 = 4(\delta_{D,1} - \delta_{D,2})^2 + (\delta_{P,1} - \delta_{P,2})^2 + (\delta_{H,1} - \delta_{H,2})^2}$$
$$\boxed{\text{RED} = \frac{R_a}{R_0}}$$
- Method ID: `R0-SCREEN-01`
- Screening Radius: $R_0 = 7.5\text{ MPa}^{1/2}$ (`ASSUMED`) with mandatory sensitivity band $[7.0, 8.0]\text{ MPa}^{1/2}$.

#### 3.5 Greenhalgh Scalar Total Difference
$$\boxed{\Delta \delta_t = |\delta_{t,1} - \delta_{t,2}|}$$
- Reference: Greenhalgh et al. (1999), *J. Pharm. Sci.*, 88(11), 1182–1190.
- $\Delta \delta_t < 2.0\text{ MPa}^{1/2}$: Likely glass solution.
- $\Delta \delta_t < 7.0\text{ MPa}^{1/2}$: Likely miscible.
- $\Delta \delta_t > 10.0\text{ MPa}^{1/2}$: Likely immiscible.
