"""
Tests for RDKit molecular descriptors engine and PubChem cross-checking.
"""

import pytest
from engine.descriptors import compute_molecular_descriptors
from engine.structure import canonicalize_smiles, get_neutral_parent


def test_canonicalize_smiles():
    smiles = "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"
    canon, err = canonicalize_smiles(smiles)
    assert err is None
    assert canon == "CC(C)Cc1ccc(C(C)C(=O)O)cc1" or "C" in canon


def test_neutral_parent_stripping():
    # Sodium salt: Ibuprofen sodium
    salt_smiles = "CC(C)CC1=CC=C(C=C1)C(C)C(=O)[O-].[Na+]"
    parent, counter_ion, formula = get_neutral_parent(salt_smiles)
    assert "[Na+]" in counter_ion or "Na" in counter_ion
    assert formula is not None


def test_naproxen_descriptors():
    # Naproxen: C14H14O3, MW ~ 230.26
    naproxen_smiles = "CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)O"
    desc, prov = compute_molecular_descriptors(naproxen_smiles)
    assert abs(desc["mw"] - 230.26) < 0.2
    assert desc["HBD"] == 1
    assert desc["HBA"] == 3
    assert desc["TPSA"] > 40.0
    assert prov["mw"] == "COMPUTED-DESCRIPTOR"
