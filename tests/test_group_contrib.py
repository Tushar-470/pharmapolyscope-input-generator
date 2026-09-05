"""
Tests for group contribution engine (Fedors & Hoftyzer-van Krevelen).
"""

import pytest
from engine.group_contribution import GroupContributionEngine


def test_fedors_constant_loading():
    engine = GroupContributionEngine()
    ch3 = engine.find_group("-CH3 (aliphatic)", "fedors")
    assert ch3 is not None
    assert ch3["delta_u_cal_mol"] == 1125
    assert ch3["delta_v_cm3_mol"] == 33.5


def test_hvk_constant_loading():
    engine = GroupContributionEngine()
    cooh = engine.find_group("-COOH (carboxylic acid)", "hvk")
    assert cooh is not None
    assert cooh["Fd"] == 530.0
    assert cooh["Fp"] == 420.0
    assert cooh["Eh"] == 10000.0


def test_invalid_molar_volume():
    engine = GroupContributionEngine()
    groups = [{"name": ">CH- (aliphatic)", "count": 1}]  # V = -1.0
    with pytest.raises(ValueError):
        engine.calculate_fedors(groups, 100.0)
