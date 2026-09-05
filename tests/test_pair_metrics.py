"""
Tests for Hansen distance, RED calculation, and Greenhalgh difference.
"""

import pytest
from engine.pair_metrics import calculate_hansen_distance, calculate_red_sensitivity, calculate_greenhalgh_delta


def test_hansen_distance_exact():
    # Drug: 17.85, 2.22, 7.15
    # Poly: 20.44, 13.67, 6.86
    # 4*(17.85 - 20.44)^2 + (2.22 - 13.67)^2 + (7.15 - 6.86)^2 = 158.019 -> sqrt = 12.57
    ra = calculate_hansen_distance(17.85, 2.22, 7.15, 20.44, 13.67, 6.86)
    assert ra == 12.57


def test_red_sensitivity():
    ra = 12.57
    reds = calculate_red_sensitivity(ra, [7.0, 7.5, 8.0])
    assert reds["RED_at_R0_7_0"] == 1.80
    assert reds["RED_at_R0_7_5"] == 1.68
    assert reds["RED_at_R0_8_0"] == 1.57


def test_greenhalgh_miscibility_tiers():
    # Miscible < 7
    d, v = calculate_greenhalgh_delta(19.36, 26.28)
    assert d == 6.92
    assert "miscible" in v
    
    # Immiscible > 10
    d_imm, v_imm = calculate_greenhalgh_delta(15.0, 27.0)
    assert d_imm == 12.0
    assert "immiscible" in v_imm


def test_monte_carlo_resampling_10k():
    from engine.sensitivity import SensitivityEngine
    engine = SensitivityEngine()
    d_hsp = {"delta_D": 17.85, "delta_P": 2.22, "delta_H": 7.15}
    p_hsp = {"delta_D": 20.44, "delta_P": 13.67, "delta_H": 6.86}
    res = engine.analyze_hsp_resampling(d_hsp, p_hsp, r0_val=7.5, n_samples=10000)
    assert res["n_resamples"] == 10000
    assert res["base_Ra"] == 12.57
    assert res["base_RED"] == 1.68
    assert res["verdict_stability"] in ["STABLE", "BORDERLINE"]

