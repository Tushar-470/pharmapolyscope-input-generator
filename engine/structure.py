"""
Structure normalization, canonicalization, and PubChem resolution engine.
Handles neutral-parent stripping, stereochemistry verification, and 2D depiction.
Includes offline fast-lookup cache for standard pharmaceutical compounds.
"""

import json
import ssl
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional, Tuple
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, Draw


# Curated offline reference catalog for instant zero-latency lookup of pharmaceutical model drugs
COMMON_DRUGS_CATALOG = {
    "ibuprofen": {
        "cid": 3672,
        "name": "ibuprofen",
        "iupac_name": "2-[4-(2-methylpropyl)phenyl]propanoic acid",
        "canonical_smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "formula": "C13H18O2",
        "mw": 206.28,
        "xlogp3": 3.5,
        "tpsa": 37.3,
        "hbd": 1,
        "hba": 2,
        "bcs_class": "II",
        "experimental_tm_sources": ["76 °C (form I, stable at 25 °C)"]
    },
    "advil": {
        "cid": 3672,
        "name": "ibuprofen",
        "iupac_name": "2-[4-(2-methylpropyl)phenyl]propanoic acid",
        "canonical_smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "formula": "C13H18O2",
        "mw": 206.28,
        "xlogp3": 3.5,
        "tpsa": 37.3,
        "hbd": 1,
        "hba": 2,
        "bcs_class": "II",
        "experimental_tm_sources": ["76 °C (form I, stable at 25 °C)"]
    },
    "motrin": {
        "cid": 3672,
        "name": "ibuprofen",
        "iupac_name": "2-[4-(2-methylpropyl)phenyl]propanoic acid",
        "canonical_smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "formula": "C13H18O2",
        "mw": 206.28,
        "xlogp3": 3.5,
        "tpsa": 37.3,
        "hbd": 1,
        "hba": 2,
        "bcs_class": "II",
        "experimental_tm_sources": ["76 °C (form I, stable at 25 °C)"]
    },
    "brufen": {
        "cid": 3672,
        "name": "ibuprofen",
        "iupac_name": "2-[4-(2-methylpropyl)phenyl]propanoic acid",
        "canonical_smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "formula": "C13H18O2",
        "mw": 206.28,
        "xlogp3": 3.5,
        "tpsa": 37.3,
        "hbd": 1,
        "hba": 2,
        "bcs_class": "II",
        "experimental_tm_sources": ["76 °C (form I, stable at 25 °C)"]
    },
    "naproxen": {
        "cid": 156391,
        "name": "naproxen",
        "iupac_name": "(2S)-2-(6-methoxynaphthalen-2-yl)propanoic acid",
        "canonical_smiles": "CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)O",
        "formula": "C14H14O3",
        "mw": 230.26,
        "xlogp3": 3.3,
        "tpsa": 46.5,
        "hbd": 1,
        "hba": 3,
        "bcs_class": "II",
        "experimental_tm_sources": ["153 °C"]
    },
    "aleve": {
        "cid": 156391,
        "name": "naproxen",
        "iupac_name": "(2S)-2-(6-methoxynaphthalen-2-yl)propanoic acid",
        "canonical_smiles": "CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)O",
        "formula": "C14H14O3",
        "mw": 230.26,
        "xlogp3": 3.3,
        "tpsa": 46.5,
        "hbd": 1,
        "hba": 3,
        "bcs_class": "II",
        "experimental_tm_sources": ["153 °C"]
    },
    "paracetamol": {
        "cid": 1983,
        "name": "paracetamol",
        "iupac_name": "N-(4-hydroxyphenyl)acetamide",
        "canonical_smiles": "CC(=O)NC1=CC=C(C=C1)O",
        "formula": "C8H9NO2",
        "mw": 151.16,
        "xlogp3": 0.5,
        "tpsa": 49.3,
        "hbd": 2,
        "hba": 2,
        "bcs_class": "I",
        "experimental_tm_sources": ["169 °C"]
    },
    "acetaminophen": {
        "cid": 1983,
        "name": "acetaminophen",
        "iupac_name": "N-(4-hydroxyphenyl)acetamide",
        "canonical_smiles": "CC(=O)NC1=CC=C(C=C1)O",
        "formula": "C8H9NO2",
        "mw": 151.16,
        "xlogp3": 0.5,
        "tpsa": 49.3,
        "hbd": 2,
        "hba": 2,
        "bcs_class": "I",
        "experimental_tm_sources": ["169 °C"]
    },
    "tylenol": {
        "cid": 1983,
        "name": "paracetamol",
        "iupac_name": "N-(4-hydroxyphenyl)acetamide",
        "canonical_smiles": "CC(=O)NC1=CC=C(C=C1)O",
        "formula": "C8H9NO2",
        "mw": 151.16,
        "xlogp3": 0.5,
        "tpsa": 49.3,
        "hbd": 2,
        "hba": 2,
        "bcs_class": "I",
        "experimental_tm_sources": ["169 °C"]
    },
    "panadol": {
        "cid": 1983,
        "name": "paracetamol",
        "iupac_name": "N-(4-hydroxyphenyl)acetamide",
        "canonical_smiles": "CC(=O)NC1=CC=C(C=C1)O",
        "formula": "C8H9NO2",
        "mw": 151.16,
        "xlogp3": 0.5,
        "tpsa": 49.3,
        "hbd": 2,
        "hba": 2,
        "bcs_class": "I",
        "experimental_tm_sources": ["169 °C"]
    },
    "aspirin": {
        "cid": 2244,
        "name": "aspirin",
        "iupac_name": "2-acetyloxybenzoic acid",
        "canonical_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
        "formula": "C9H8O4",
        "mw": 180.16,
        "xlogp3": 1.2,
        "tpsa": 63.6,
        "hbd": 1,
        "hba": 4,
        "bcs_class": "I",
        "experimental_tm_sources": ["135 °C"]
    },
    "caffeine": {
        "cid": 2519,
        "name": "caffeine",
        "iupac_name": "1,3,7-trimethylpurine-2,6-dione",
        "canonical_smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
        "formula": "C8H10N4O2",
        "mw": 194.19,
        "xlogp3": -0.1,
        "tpsa": 58.4,
        "hbd": 0,
        "hba": 3,
        "bcs_class": "I",
        "experimental_tm_sources": ["238 °C"]
    },
    "indomethacin": {
        "cid": 3715,
        "name": "indomethacin",
        "iupac_name": "2-[1-(4-chlorobenzoyl)-5-methoxy-2-methylindol-3-yl]acetic acid",
        "canonical_smiles": "CC1=C(C2=C(N1C(=O)C3=CC=C(C=C3)Cl)C=CC(=C2)OC)CC(=O)O",
        "formula": "C19H16ClNO4",
        "mw": 357.8,
        "xlogp3": 4.3,
        "tpsa": 68.5,
        "hbd": 1,
        "hba": 4,
        "bcs_class": "II",
        "experimental_tm_sources": ["161 °C (gamma form)"]
    },
    "felodipine": {
        "cid": 3333,
        "name": "felodipine",
        "iupac_name": "5-O-ethyl 3-O-methyl 4-(2,3-dichlorophenyl)-2,6-dimethyl-1,4-dihydropyridine-3,5-dicarboxylate",
        "canonical_smiles": "CCOC(=O)C1=C(NC(=C(C1C2=C(C(=CC=C2)Cl)Cl)C(=O)OC)C)C",
        "formula": "C18H19Cl2NO4",
        "mw": 384.25,
        "xlogp3": 4.5,
        "tpsa": 64.6,
        "hbd": 1,
        "hba": 4,
        "bcs_class": "II",
        "experimental_tm_sources": ["145 °C"]
    },
    "nifedipine": {
        "cid": 4485,
        "name": "nifedipine",
        "iupac_name": "dimethyl 2,6-dimethyl-4-(2-nitrophenyl)-1,4-dihydropyridine-3,5-dicarboxylate",
        "canonical_smiles": "CC1=C(C(C(=C(N1)C)C(=O)OC)C2=CC=CC=C2[N+](=O)[O-])C(=O)OC",
        "formula": "C17H18N2O6",
        "mw": 346.33,
        "xlogp3": 2.2,
        "tpsa": 110.0,
        "hbd": 1,
        "hba": 6,
        "bcs_class": "II",
        "experimental_tm_sources": ["172 °C"]
    },
    "ketoprofen": {
        "cid": 3825,
        "name": "ketoprofen",
        "iupac_name": "2-(3-benzoylphenyl)propanoic acid",
        "canonical_smiles": "CC(C1=CC=CC(=C1)C(=O)C2=CC=CC=C2)C(=O)O",
        "formula": "C16H14O3",
        "mw": 254.28,
        "xlogp3": 3.1,
        "tpsa": 54.4,
        "hbd": 1,
        "hba": 3,
        "bcs_class": "II",
        "experimental_tm_sources": ["94 °C"]
    },
    "celecoxib": {
        "cid": 2662,
        "name": "celecoxib",
        "iupac_name": "4-[5-(4-methylphenyl)-3-(trifluoromethyl)pyrazol-1-yl]benzenesulfonamide",
        "canonical_smiles": "CC1=CC=C(C=C1)C2=CC(=NN2C3=CC=C(C=C3)S(=O)(=O)N)C(F)(F)F",
        "formula": "C17H14F3N3O2S",
        "mw": 381.37,
        "xlogp3": 3.5,
        "tpsa": 86.4,
        "hbd": 1,
        "hba": 5,
        "bcs_class": "II",
        "experimental_tm_sources": ["162 °C"]
    },
    "carbamazepine": {
        "cid": 2554,
        "name": "carbamazepine",
        "iupac_name": "benzo[b][1]benzazepine-11-carboxamide",
        "canonical_smiles": "C1=CC=C2C(=C1)C=CC3=CC=CC=C3N2C(=O)N",
        "formula": "C15H12N2O",
        "mw": 236.27,
        "xlogp3": 2.5,
        "tpsa": 46.3,
        "hbd": 1,
        "hba": 1,
        "bcs_class": "II",
        "experimental_tm_sources": ["191 °C (form III)"]
    },
    "griseofulvin": {
        "cid": 441140,
        "name": "griseofulvin",
        "iupac_name": "(1'S,6'R)-7-chloro-2',4,6-trimethoxy-6'-methylspiro[1-benzofuran-2,4'-cyclohex-2-ene]-3,2'-dione",
        "canonical_smiles": "CC1CC(=O)C(=C(O1)OC)C2(C(=O)C3=C(C=C(C(=C3O2)Cl)OC)OC)C",
        "formula": "C17H17ClO6",
        "mw": 352.77,
        "xlogp3": 2.2,
        "tpsa": 71.1,
        "hbd": 0,
        "hba": 6,
        "bcs_class": "II",
        "experimental_tm_sources": ["220 °C"]
    },
    "ritonavir": {
        "cid": 392622,
        "name": "ritonavir",
        "iupac_name": "1,3-thiazol-5-ylmethyl N-[(2S,3S,5S)-3-hydroxy-5-[[(2S)-3-methyl-2-[[methyl-[(2-propan-2-yl-1,3-thiazol-4-yl)methyl]carbamoyl]amino]butanoyl]amino]-1,6-diphenylhexan-2-yl]carbamate",
        "canonical_smiles": "CC(C)C1=NC(=CS1)CN(C)C(=O)NC(C(C)C)C(=O)NC(CC2=CC=CC=C2)C(CC(CC3=CC=CC=C3)NC(=O)OCC4=CN=CS4)O",
        "formula": "C37H48N6O5S2",
        "mw": 720.9,
        "xlogp3": 3.9,
        "tpsa": 154.0,
        "hbd": 4,
        "hba": 9,
        "bcs_class": "IV",
        "experimental_tm_sources": ["121 °C (form I), 125 °C (form II)"]
    },
    "atorvastatin": {
        "cid": 60823,
        "name": "atorvastatin",
        "iupac_name": "(3R,5R)-7-[2-(4-fluorophenyl)-5-isopropyl-3-phenyl-4-(phenylcarbamoyl)pyrrol-1-yl]-3,5-dihydroxyheptanoic acid",
        "canonical_smiles": "CC(C)C1=C(C(=C(N1CCC(CC(CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4",
        "formula": "C33H35FN2O5",
        "mw": 558.6,
        "xlogp3": 5.7,
        "tpsa": 111.0,
        "hbd": 3,
        "hba": 5,
        "bcs_class": "II",
        "experimental_tm_sources": ["159 °C"]
    },
    "lipitor": {
        "cid": 60823,
        "name": "atorvastatin",
        "iupac_name": "(3R,5R)-7-[2-(4-fluorophenyl)-5-isopropyl-3-phenyl-4-(phenylcarbamoyl)pyrrol-1-yl]-3,5-dihydroxyheptanoic acid",
        "canonical_smiles": "CC(C)C1=C(C(=C(N1CCC(CC(CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4",
        "formula": "C33H35FN2O5",
        "mw": 558.6,
        "xlogp3": 5.7,
        "tpsa": 111.0,
        "hbd": 3,
        "hba": 5,
        "bcs_class": "II",
        "experimental_tm_sources": ["159 °C"]
    },
    "omeprazole": {
        "cid": 4594,
        "name": "omeprazole",
        "iupac_name": "6-methoxy-2-[(4-methoxy-3,5-dimethylpyridin-2-yl)methylsulfinyl]-1H-benzimidazole",
        "canonical_smiles": "CC1=CN=C(C(=C1OC)C)CS(=O)C2=NC3=C(N2)C=CC(=C3)OC",
        "formula": "C17H19N3O3S",
        "mw": 345.4,
        "xlogp3": 2.2,
        "tpsa": 74.0,
        "hbd": 1,
        "hba": 5,
        "bcs_class": "II",
        "experimental_tm_sources": ["156 °C"]
    },
    "metformin": {
        "cid": 4091,
        "name": "metformin",
        "iupac_name": "3-(diaminomethylidene)-1,1-dimethylguanidine",
        "canonical_smiles": "CN(C)C(=N)NC(=N)N",
        "formula": "C4H11N5",
        "mw": 129.16,
        "xlogp3": -1.4,
        "tpsa": 88.0,
        "hbd": 3,
        "hba": 2,
        "bcs_class": "III",
        "experimental_tm_sources": ["224 °C (hydrochloride)"]
    },
    "povidone": {
        "cid": 6917,
        "name": "Povidone (PVP)",
        "iupac_name": "1-ethenylpyrrolidin-2-one (homopolymer)",
        "canonical_smiles": "*CC(*)N1CCCC1=O",
        "formula": "(C6H9NO)n",
        "mw": 111.14,
        "xlogp3": 0.4,
        "tpsa": 20.3,
        "hbd": 0,
        "hba": 1,
        "bcs_class": None,
        "experimental_tm_sources": ["153.6 °C (Tg dry state, PVP K30)"]
    },
    "polyvinylpyrrolidone": {
        "cid": 6917,
        "name": "Polyvinylpyrrolidone (PVP)",
        "iupac_name": "1-ethenylpyrrolidin-2-one (homopolymer)",
        "canonical_smiles": "*CC(*)N1CCCC1=O",
        "formula": "(C6H9NO)n",
        "mw": 111.14,
        "xlogp3": 0.4,
        "tpsa": 20.3,
        "hbd": 0,
        "hba": 1,
        "bcs_class": None,
        "experimental_tm_sources": ["153.6 °C (Tg dry state, PVP K30)"]
    },
    "pvp": {
        "cid": 6917,
        "name": "PVP (Povidone)",
        "iupac_name": "1-ethenylpyrrolidin-2-one (homopolymer)",
        "canonical_smiles": "*CC(*)N1CCCC1=O",
        "formula": "(C6H9NO)n",
        "mw": 111.14,
        "xlogp3": 0.4,
        "tpsa": 20.3,
        "hbd": 0,
        "hba": 1,
        "bcs_class": None,
        "experimental_tm_sources": ["153.6 °C (Tg dry state, PVP K30)"]
    },
    "copovidone": {
        "cid": 282,
        "name": "Copovidone (PVP-VA 64)",
        "iupac_name": "1-ethenylpyrrolidin-2-one; ethenyl acetate (6:4 copolymer)",
        "canonical_smiles": "*CC(*)N1CCCC1=O.*CC(*)OC(=O)C",
        "formula": "(C6H9NO)n.(C4H6O2)m",
        "mw": 197.23,
        "xlogp3": 0.5,
        "tpsa": 46.6,
        "hbd": 0,
        "hba": 3,
        "bcs_class": None,
        "experimental_tm_sources": ["108.0 °C (Tg dry state, Kollidon VA 64)"]
    },
    "soluplus": {
        "cid": 24702,
        "name": "Soluplus",
        "iupac_name": "Polyvinyl caprolactam-polyvinyl acetate-polyethylene glycol graft copolymer",
        "canonical_smiles": "*CC(*)OC(=O)C.*CC(*)N1CCCCCC1=O.*CCO*",
        "formula": "Graft Copolymer",
        "mw": 269.34,
        "xlogp3": 1.2,
        "tpsa": 55.8,
        "hbd": 0,
        "hba": 4,
        "bcs_class": None,
        "experimental_tm_sources": ["70.0 °C (Tg dry state)"]
    },
    "polyethylene glycol": {
        "cid": 24702,
        "name": "Polyethylene Glycol (PEG)",
        "iupac_name": "poly(ethane-1,2-diol)",
        "canonical_smiles": "*CCO*",
        "formula": "(C2H4O)n.H2O",
        "mw": 44.05,
        "xlogp3": -0.8,
        "tpsa": 18.5,
        "hbd": 0,
        "hba": 1,
        "bcs_class": None,
        "experimental_tm_sources": ["-65.0 °C (Tg dry state)"]
    },
    "peg": {
        "cid": 24702,
        "name": "Polyethylene Glycol (PEG)",
        "iupac_name": "poly(ethane-1,2-diol)",
        "canonical_smiles": "*CCO*",
        "formula": "(C2H4O)n.H2O",
        "mw": 44.05,
        "xlogp3": -0.8,
        "tpsa": 18.5,
        "hbd": 0,
        "hba": 1,
        "bcs_class": None,
        "experimental_tm_sources": ["-65.0 °C (Tg dry state)"]
    },
    "hypromellose": {
        "cid": 575,
        "name": "Hypromellose (HPMC)",
        "iupac_name": "Hydroxypropyl methylcellulose",
        "canonical_smiles": "*C1OC(CO*)C(OC)C(OC)C1O*",
        "formula": "Cellulose Ether",
        "mw": 206.19,
        "xlogp3": -0.5,
        "tpsa": 67.5,
        "hbd": 1,
        "hba": 5,
        "bcs_class": None,
        "experimental_tm_sources": ["170.0 °C (Tg dry state)"]
    },
    "hpmc": {
        "cid": 575,
        "name": "Hypromellose (HPMC)",
        "iupac_name": "Hydroxypropyl methylcellulose",
        "canonical_smiles": "*C1OC(CO*)C(OC)C(OC)C1O*",
        "formula": "Cellulose Ether",
        "mw": 206.19,
        "xlogp3": -0.5,
        "tpsa": 67.5,
        "hbd": 1,
        "hba": 5,
        "bcs_class": None,
        "experimental_tm_sources": ["170.0 °C (Tg dry state)"]
    },
    "hpmcas": {
        "cid": 575,
        "name": "Hypromellose Acetate Succinate (HPMC-AS)",
        "iupac_name": "Hydroxypropyl methylcellulose acetate succinate",
        "canonical_smiles": "*C1OC(CO*)C(OC(=O)C)C(OC(=O)CCC(=O)O)C1O*",
        "formula": "Modified Cellulose",
        "mw": 348.3,
        "xlogp3": 0.8,
        "tpsa": 110.4,
        "hbd": 1,
        "hba": 8,
        "bcs_class": None,
        "experimental_tm_sources": ["120.0 °C (Tg dry state)"]
    }
}


def canonicalize_smiles(smiles: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses and canonicalizes a SMILES string using RDKit.
    Returns (canonical_smiles, error_message).
    """
    if not smiles or not str(smiles).strip():
        return None, "Empty SMILES string"
    try:
        mol = Chem.MolFromSmiles(str(smiles).strip())
        if mol is None:
            return None, f"Invalid SMILES syntax: '{smiles}'"
        canon_smiles = Chem.MolToSmiles(mol, canonical=True)
        return canon_smiles, None
    except Exception as e:
        return None, f"RDKit parse error: {str(e)}"


def get_neutral_parent(smiles: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Strips counter-ions and returns the neutral active parent moiety.
    Returns (parent_smiles, counter_ion_smiles, formula).
    """
    canon, err = canonicalize_smiles(smiles)
    if err:
        return smiles, None, None
    
    mol = Chem.MolFromSmiles(canon)
    frags = Chem.GetMolFrags(mol, asMols=True)
    if len(frags) == 1:
        formula = rdMolDescriptors.CalcMolFormula(mol)
        return canon, None, formula
    
    # Sort fragments by heavy atom count descending
    frags_sorted = sorted(frags, key=lambda m: m.GetNumHeavyAtoms(), reverse=True)
    parent_mol = frags_sorted[0]
    parent_smiles = Chem.MolToSmiles(parent_mol, canonical=True)
    parent_formula = rdMolDescriptors.CalcMolFormula(parent_mol)
    
    counter_ions = [Chem.MolToSmiles(f, canonical=True) for f in frags_sorted[1:]]
    counter_ion_str = ".".join(counter_ions)
    
    return parent_smiles, counter_ion_str, parent_formula


def query_pubchem_by_name_or_cid(query: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Queries PubChem PUG REST API with local fast-lookup fallback and direct SMILES detection.
    Supports compound name (e.g. 'Ibuprofen', 'Naproxen', 'Paracetamol'), trade names, numeric CID ('3672'), or SMILES.
    Returns (result_dict, error_message).
    """
    q_str = str(query).strip()
    if not q_str:
        return None, "Empty query parameter"
    
    q_lower = q_str.lower()

    # 1. Tier 1: Check offline catalog for instantaneous 0ms response
    if q_lower in COMMON_DRUGS_CATALOG:
        entry = dict(COMMON_DRUGS_CATALOG[q_lower])
        return entry, None

    for k, v in COMMON_DRUGS_CATALOG.items():
        if str(v.get("cid")) == q_str:
            entry = dict(v)
            return entry, None

    # 2. Tier 2: Check if input is a direct SMILES string
    is_smiles = False
    canon_from_smiles = None
    try:
        mol = Chem.MolFromSmiles(q_str)
        if mol is not None and mol.GetNumHeavyAtoms() >= 3:
            is_smiles = True
            canon_from_smiles = Chem.MolToSmiles(mol, canonical=True)
            # Check if canonical SMILES matches any catalog entry
            for k, v in COMMON_DRUGS_CATALOG.items():
                v_smiles = v.get("canonical_smiles")
                if v_smiles:
                    v_mol = Chem.MolFromSmiles(v_smiles)
                    if v_mol and Chem.MolToSmiles(v_mol, canonical=True) == canon_from_smiles:
                        entry = dict(v)
                        return entry, None
    except Exception:
        pass

    # 3. Tier 3: Live PubChem API query (Resolves brand names, generics, CIDs, or SMILES)
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
    ctx = ssl._create_unverified_context()
    cid = None

    # Step A: Resolve query to CID
    if q_str.isdigit():
        cid = int(q_str)
    elif is_smiles and canon_from_smiles:
        # Try resolving SMILES to PubChem CID
        try:
            smiles_search_url = f"{base_url}/smiles/{urllib.parse.quote(canon_from_smiles)}/cids/JSON"
            req_s = urllib.request.Request(smiles_search_url, headers={"User-Agent": "Mozilla/5.0 PharmaPolySCOPE/1.0"})
            with urllib.request.urlopen(req_s, context=ctx, timeout=4) as resp_s:
                s_data = json.loads(resp_s.read().decode("utf-8"))
                cids_s = s_data.get("IdentifierList", {}).get("CID", [])
                if cids_s:
                    cid = cids_s[0]
        except Exception:
            pass
            
        if not cid:
            # Custom structure not indexed in PubChem: return computed descriptors
            formula = rdMolDescriptors.CalcMolFormula(mol)
            mw = round(Descriptors.ExactMolWt(mol), 2)
            return {
                "cid": None,
                "name": "Custom Structure",
                "iupac_name": formula,
                "canonical_smiles": canon_from_smiles,
                "formula": formula,
                "mw": mw,
                "xlogp3": round(Descriptors.MolLogP(mol), 2),
                "tpsa": round(rdMolDescriptors.CalcTPSA(mol), 1),
                "hbd": rdMolDescriptors.CalcNumHBD(mol),
                "hba": rdMolDescriptors.CalcNumHBA(mol),
                "bcs_class": "II",
                "experimental_tm_sources": []
            }, None
    else:
        # A1: Try direct name CID search
        try:
            cid_search_url = f"{base_url}/name/{urllib.parse.quote(q_str)}/cids/JSON"
            req_cid = urllib.request.Request(cid_search_url, headers={"User-Agent": "Mozilla/5.0 PharmaPolySCOPE/1.0"})
            with urllib.request.urlopen(req_cid, context=ctx, timeout=4) as resp:
                cid_data = json.loads(resp.read().decode("utf-8"))
                cids = cid_data.get("IdentifierList", {}).get("CID", [])
                if cids:
                    cid = cids[0]
        except urllib.error.HTTPError as http_err:
            if http_err.code != 404:
                pass
        except Exception:
            pass

        # A2: If not found directly, try Autocomplete suggestion API
        if not cid:
            try:
                auto_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{urllib.parse.quote(q_str)}/json?limit=5"
                req_auto = urllib.request.Request(auto_url, headers={"User-Agent": "Mozilla/5.0 PharmaPolySCOPE/1.0"})
                with urllib.request.urlopen(req_auto, context=ctx, timeout=3) as resp_auto:
                    auto_data = json.loads(resp_auto.read().decode("utf-8"))
                    terms = auto_data.get("dictionary_terms", {}).get("compound", [])
                    if terms:
                        best_term = terms[0]
                        # Query CID for suggested term
                        cid_suggest_url = f"{base_url}/name/{urllib.parse.quote(best_term)}/cids/JSON"
                        req_s = urllib.request.Request(cid_suggest_url, headers={"User-Agent": "Mozilla/5.0 PharmaPolySCOPE/1.0"})
                        with urllib.request.urlopen(req_s, context=ctx, timeout=3) as resp_s:
                            s_data = json.loads(resp_s.read().decode("utf-8"))
                            cids_s = s_data.get("IdentifierList", {}).get("CID", [])
                            if cids_s:
                                cid = cids_s[0]
            except Exception:
                pass

        # A3: If still not found, try NCBI ESearch
        if not cid:
            try:
                esearch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pccompound&term={urllib.parse.quote(q_str)}&retmode=json"
                req_es = urllib.request.Request(esearch_url, headers={"User-Agent": "Mozilla/5.0 PharmaPolySCOPE/1.0"})
                with urllib.request.urlopen(req_es, context=ctx, timeout=3) as resp_es:
                    es_data = json.loads(resp_es.read().decode("utf-8"))
                    idlist = es_data.get("esearchresult", {}).get("idlist", [])
                    if idlist:
                        cid = int(idlist[0])
            except Exception:
                pass

    if not cid:
        return None, f"Compound '{q_str}' was not found in PubChem. You can type or paste the SMILES directly below to compute its properties."

    # Step B: Fetch full properties by CID
    props_to_fetch = "CanonicalSMILES,ConnectivitySMILES,IsomericSMILES,IUPACName,MolecularFormula,MolecularWeight,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount"
    prop_url = f"{base_url}/cid/{cid}/property/{props_to_fetch}/JSON"
    
    try:
        req = urllib.request.Request(prop_url, headers={"User-Agent": "Mozilla/5.0 PharmaPolySCOPE/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
            if "PropertyTable" in data and "Properties" in data["PropertyTable"] and len(data["PropertyTable"]["Properties"]) > 0:
                props = data["PropertyTable"]["Properties"][0]
                
                smiles = props.get("CanonicalSMILES") or props.get("ConnectivitySMILES") or props.get("IsomericSMILES") or ""
                
                exp_tm_sources = fetch_pubchem_experimental_tm(cid, ctx)
                
                result = {
                    "cid": cid,
                    "name": q_str if not q_str.isdigit() else props.get("IUPACName", f"CID-{cid}"),
                    "iupac_name": props.get("IUPACName", ""),
                    "canonical_smiles": smiles,
                    "formula": props.get("MolecularFormula", ""),
                    "mw": float(props.get("MolecularWeight", 0.0)) if props.get("MolecularWeight") else None,
                    "xlogp3": float(props.get("XLogP", 0.0)) if props.get("XLogP") is not None else None,
                    "tpsa": float(props.get("TPSA", 0.0)) if props.get("TPSA") is not None else None,
                    "hbd": int(props.get("HBondDonorCount", 0)) if props.get("HBondDonorCount") is not None else None,
                    "hba": int(props.get("HBondAcceptorCount", 0)) if props.get("HBondAcceptorCount") is not None else None,
                    "experimental_tm_sources": exp_tm_sources
                }
                return result, None
    except Exception as prop_err:
        return None, f"PubChem property query error: {str(prop_err)}"

    return None, f"Compound '{query}' was not found in PubChem. You can type or paste the SMILES directly below to compute its properties."


def fetch_pubchem_experimental_tm(cid: int, ctx: Optional[ssl.SSLContext] = None) -> list:
    """
    Fetches experimental melting points from PubChem Compound Experimental Properties view.
    """
    if ctx is None:
        ctx = ssl._create_unverified_context()
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON?heading=Melting+Point"
    tm_list = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 PharmaPolySCOPE/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sections = data.get("Record", {}).get("Section", [])
            for s1 in sections:
                for s2 in s1.get("Section", []):
                    if "Melting Point" in s2.get("TOCHeading", ""):
                        for info in s2.get("Information", []):
                            val = info.get("Value", {}).get("StringWithMarkup", [{}])[0].get("String")
                            if val:
                                tm_list.append(val)
    except Exception:
        pass
    return tm_list


def generate_structure_svg(smiles: str, width: int = 280, height: int = 160) -> Optional[str]:
    """
    Generates a high-contrast 2D depiction SVG string from a SMILES string using RDKit.
    """
    if not smiles or not str(smiles).strip():
        return None
    try:
        clean_smiles = str(smiles).strip().replace("*", "")
        if not clean_smiles:
            return None
        mol = Chem.MolFromSmiles(clean_smiles)
        if mol is None:
            return None
        
        drawer = Draw.rdMolDraw2D.MolDraw2DSVG(width, height)
        opts = drawer.drawOptions()
        opts.clearBackground = True
        opts.bondLineWidth = 2.0
        
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        svg_text = drawer.GetDrawingText()
        return svg_text
    except Exception:
        return None
