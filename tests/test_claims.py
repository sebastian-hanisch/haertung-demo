"""Jede Zahl aus README.md ("Befunde"-Tabelle, Vorab-Hypothesen), nachgerechnet über die echten Auswertungsfunktionen (Hauskonvention: keine erfundenen Zahlen)."""

import statistics

import pytest

import haer_algorithm as A
import haer_evaluation as ev
import haer_scenario as S


def _approx(x, abs_tol=0.0005):
    return pytest.approx(x, abs=abs_tol)


def test_readme_barbell_bridge_gone_after_bypass():
    settings = ev.Settings(kind="barbell", k_barbell=8, strategy="bypass", budget=1, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.low_link(adj).bridges == [(7, 8)]
    assert A.low_link(new_adj).bridges == []
    assert a.R_before == _approx(0.2500) and a.R_after == _approx(0.2500)


def test_readme_betriebsnetz_schneider_r_and_alpha_both_improve_beta_c_invariant():
    settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="schneider", budget=8, n_trials=150, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    assert a.R_before == _approx(0.2055) and a.R_after == _approx(0.2384)
    assert a.alpha_before == _approx(2.8) and a.alpha_after == _approx(0.8)
    assert a.beta_c_before == _approx(0.0939) and a.beta_c_after == a.beta_c_before


def test_readme_betriebsnetz_random_tradeoff():
    settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="random", budget=8, n_trials=150, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    assert a.R_before == _approx(0.2055) and a.R_after == _approx(0.2026)
    assert a.alpha_before == _approx(2.8) and a.alpha_after == _approx(1.8)
    assert a.beta_c_before == _approx(0.0939) and a.beta_c_after == _approx(0.0880)


def test_readme_betriebsnetz_bypass_hurts_alpha_and_beta():
    settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="bypass", budget=8, n_trials=150, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    assert a.R_after == _approx(0.2058, abs_tol=0.001)
    assert a.alpha_before == _approx(2.8) and a.alpha_after == _approx(3.6)
    assert a.beta_c_before == _approx(0.0939) and a.beta_c_after == _approx(0.0854)


def test_readme_skalenfrei_bypass_zero_r_and_undefined_alpha_at_two_budgets():
    for budget, n_trials in ((8, 150), (20, 400)):
        settings = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="bypass", budget=budget, n_trials=n_trials, seed=35)
        inst, new_adj, a = ev.analyse(settings)
        assert a.R_before == _approx(0.1112, abs_tol=0.0001)
        assert a.R_after == _approx(0.1112, abs_tol=0.0001)
        assert a.alpha_before == _approx(17.0)
        assert a.alpha_after is None


def test_readme_skalenfrei_schneider_quadruples_robustness_at_high_budget():
    settings = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="schneider", budget=20, n_trials=400, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    assert a.R_before == _approx(0.1112, abs_tol=0.0001) and a.R_after == _approx(0.1588, abs_tol=0.001)
    assert a.alpha_before == _approx(17.0) and a.alpha_after == _approx(4.0)
    assert a.beta_c_after == a.beta_c_before


def test_readme_onion_structure_confirmed_on_random_variant_refuted_on_grid():
    grid_settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", n_trials=800, seed=35)
    _inst_g, _adj_g, check_grid = ev.onion_check(grid_settings)
    assert check_grid.assort_before == _approx(0.1000) and check_grid.assort_after == _approx(0.0471, abs_tol=0.001)
    assert check_grid.R_before == _approx(0.2055) and check_grid.R_after == _approx(0.2609, abs_tol=0.001)

    random_settings = ev.Settings(kind="city", side=13, blocked=0.0, nettype="random", n_trials=800, seed=35)
    _inst_r, _adj_r, check_random = ev.onion_check(random_settings)
    assert check_random.assort_before == _approx(0.0182, abs_tol=0.001) and check_random.assort_after == _approx(0.1105, abs_tol=0.002)


def test_readme_onion_structure_negligible_on_ba_and_barbell():
    ba_settings = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, n_trials=800, seed=35)
    _inst, _adj, check_ba = ev.onion_check(ba_settings)
    assert abs(check_ba.assort_after - check_ba.assort_before) < 0.02

    barbell_settings = ev.Settings(kind="barbell", k_barbell=8, n_trials=800, seed=35)
    _inst2, _adj2, check_barbell = ev.onion_check(barbell_settings)
    assert check_barbell.assort_after == check_barbell.assort_before


def test_readme_bypass_alpha_mean_is_reliably_worse_across_samples():
    """README: "Bypass verschlechtert alpha* VERLAESSLICH im Mittel ... stabil zwischen +1.6 und +5.2" (delta = alpha_nachher - alpha_vorher, hoeher = schlechter). Hier mit einer eigenen,
    unabhaengigen Stichprobe nachgerechnet (andere Seeds als in test_evaluation.py, um keinen Zufallstreffer zu verifizieren)."""
    deltas = []
    for i in range(20):
        seed = 9000 + i
        kind = ("city", "ba", "barbell")[i % 3]
        if kind == "city":
            inst = S.generate(side=6 + (i % 4), blocked=0.2, nettype=("grid", "random")[i % 2], seed=seed)
        elif kind == "ba":
            inst = S.barabasi_albert_instance(30 + (i % 6) * 8, 2, 4, seed)
        else:
            inst = S.barbell_instance(5 + i % 8)
        adj = A.adjacency(inst.n, inst.edges)
        alpha_before = ev.critical_alpha(adj)
        new_adj, _added, _removed, _rh, _steps = ev.apply_strategy(adj, "bypass", 5, 0, seed=seed)
        alpha_after = ev.critical_alpha(new_adj)
        if alpha_before is not None and alpha_after is not None:
            deltas.append(alpha_after - alpha_before)
    assert len(deltas) >= 10
    assert statistics.mean(deltas) > 0.0                          # zuverlaessig schlechter (hoeheres alpha*)
