"""
Molecular descriptors calculation engine using version-pinned RDKit.
Computes MW, Crippen LogP, Ertl TPSA, and Lipinski HBD/HBA with algorithm provenance.
"""

from typing import Dict, Any, Tuple
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors
import rdkit


def compute_molecular_descriptors(smiles: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Calculates molecular descriptors for a given SMILES string using RDKit.
    Returns:
      (descriptors_dict, provenance_dict)
    """
    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None:
        raise ValueError(f"Invalid SMILES string cannot be parsed: '{smiles}'")
    
    # 1. Molecular Weight (RDKit MolWt)
    mw = round(Descriptors.MolWt(mol), 2)
    
    # 2. LogP (Wildman-Crippen LogP)
    logp = round(Crippen.MolLogP(mol), 2)
    
    # 3. TPSA (Ertl Topological Polar Surface Area)
    tpsa = round(Descriptors.TPSA(mol), 1)
    
    # 4. Hydrogen Bond Donors & Acceptors (Lipinski Definitions)
    # Lipinski HBD: OH and NH count
    # Lipinski HBA: O and N count
    hbd = int(rdMolDescriptors.CalcNumLipinskiHBD(mol))
    hba = int(rdMolDescriptors.CalcNumLipinskiHBA(mol))
    
    descriptors = {
        "mw": mw,
        "logP": logp,
        "TPSA": tpsa,
        "HBD": hbd,
        "HBA": hba,
        "rdkit_version": rdkit.__version__
    }
    
    provenance = {
        "mw": "COMPUTED-DESCRIPTOR",
        "logP": "COMPUTED-DESCRIPTOR",
        "TPSA": "COMPUTED-DESCRIPTOR",
        "HBD": "COMPUTED-DESCRIPTOR",
        "HBA": "COMPUTED-DESCRIPTOR"
    }
    
    return descriptors, provenance


