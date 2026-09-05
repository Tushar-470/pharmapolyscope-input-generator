# Data Dictionary & Schema Specification
## Pharmapolyscope Input Generator Output Contract

### 1. Controlled Vocabularies

#### 1.1 Entity Types
- `drug`: Small organic molecule active pharmaceutical ingredient.
- `polymer`: Polymeric excipient or ASD carrier matrix.

#### 1.2 Provenance Categories
- `EXPERIMENTAL`: Measured on the specific material and form, with method and uncertainty reported (e.g. primary DSC $T_m$, helium pycnometry).
- `LITERATURE`: Quoted from a peer-reviewed publication or curated database without re-estimation (e.g. literature polymorph $T_m$, grade-specific polymer $T_g$).
- `CALCULATED`: Produced by the frozen arithmetic pipeline from structure plus published constants (e.g. $T_g = 0.70 \times T_m$, Fedors density, HVK HSP).
- `ESTIMATED`: Informed approximation outside the frozen arithmetic chain, used only as a flagged fallback (e.g. racemate estimate for an enantiomer).
- `COMPUTED-DESCRIPTOR`: Cheminformatics descriptor computed from canonical structure by a named algorithm (e.g. RDKit MolWt, Crippen LogP, Ertl TPSA).
- `ASSUMED`: Declared screening convention adopted in the absence of compound-specific data (e.g. $R_0 = 7.5\text{ MPa}^{1/2}$ with $[7.0, 8.0]$ band).
- `MANUFACTURER-SPEC`: Source type within literature for commercial grade datasheets (e.g. $M_n$, bulk density).

#### 1.3 Confidence Grades
- `high`: Exact-structure computations, primary DSC measurements.
- `medium`: Literature values with cross-source agreement within 5 K, frozen empirical correlations ($0.70 \times T_m$, Fedors surrogate).
- `low`: Fallback estimates, unmapped group approximations, or values with QC displacement flags.

---

### 2. Output Schema Fields (Table 19-1 / 28 Columns)

| Field Name | Mandatory | Type | Description |
|---|---|---|---|
| `entity_id` | Yes | String | Project identifier (`DRG-nnnn` / `POL-nnnn`) |
| `entity_type` | Yes | String | `drug` or `polymer` |
| `name` | Yes | String | INN (drugs) or pharmacopoeial name with grade (polymers) |
| `abbreviation` | Polymers | String | Grade abbreviation (e.g. `PVP K30`, `HPMCAS-M`, `Soluplus`) |
| `canonical_smiles` | Drugs | String | PubChem-canonical neutral active moiety SMILES |
| `repeat_unit_smiles`| Polymers | String / Object | Curated repeat-unit SMILES with attachment points |
| `mn` | Polymers | String / Float | Number-average molar mass (`MANUFACTURER-SPEC`) |
| `mw` | Drugs | Float | RDKit MolWt on calculation SMILES ($\text{g/mol}$) |
| `tm_K` | Drugs | Float / Object | Melting temperature in Kelvin (`LITERATURE`) |
| `tg_K` | Yes | Float / Object | Drug: $0.70 \times T_m$; Polymer: literature grade $T_g$ ($\text{K}$) |
| `density_g_cm3` | Yes | Float / Object | Drug: Fedors surrogate; Polymer: bulk density ($\text{g/cm}^3$) |
| `delta_D` | Yes | Float | Hoftyzer-van Krevelen dispersion parameter ($\text{MPa}^{1/2}$) |
| `delta_P` | Yes | Float | Hoftyzer-van Krevelen polar parameter ($\text{MPa}^{1/2}$) |
| `delta_H` | Yes | Float | Hoftyzer-van Krevelen hydrogen-bonding parameter ($\text{MPa}^{1/2}$) |
| `logP` | Drugs | Float / Object | RDKit Crippen LogP with PubChem XLogP3 cross-check |
| `TPSA` | Drugs | Float | Ertl Topological Polar Surface Area ($\text{\AA}^2$) |
| `HBD` | Drugs | Integer | Lipinski Hydrogen Bond Donors (count) |
| `HBA` | Drugs | Integer | Lipinski Hydrogen Bond Acceptors (count) |
| `BCS_class` | Drugs | String | BCS class I, II, III, or IV (`LITERATURE`) |
| `source` | Yes | String | Detailed citations, monographs, or datasheets |
| `method` | Yes | List / String | Controlled method IDs (e.g. `TG-RATIO-01`, `HSP-HVK-01`) |
| `algorithm` | Yes | String | Algorithm and constant table descriptions |
| `provenance` | Yes | Object / String | Semicolon-separated provenance mappings |
| `confidence` | Yes | String | `high`, `medium`, or `low` |
| `uncertainty` | Optional | Object / String | Quantified uncertainty bounds |
| `calculation_date`| Yes | String | ISO 8601 generation date |
| `software_version` | Yes | String | Generator version string (`input-generator/1.0`) |
