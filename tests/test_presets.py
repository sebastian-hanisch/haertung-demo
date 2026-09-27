"""Jede Zahl in den PRESET_HELP-Hilfetexten, nachgerechnet über die echten Auswertungsfunktionen (Hauskonvention: keine erfundenen Zahlen).

Erinnerung an die Kennzahlen-Richtung (wortgleich aus kaskaden-demo): JE GRÖSSER α*, desto VERWUNDBARER (mehr Sicherheitsspielraum nötig) - Härtung soll α* SENKEN. JE KLEINER β_c, desto
VERWUNDBARER - Härtung soll β_c ANHEBEN."""

import pytest

import haer_algorithm as A
import haer_evaluation as ev


def _approx(x, abs_tol=0.0005):
    return pytest.approx(x, abs=abs_tol)


def test_barbell_bypass_preset_numbers():
    settings = ev.Settings(kind="barbell", k_barbell=8, strategy="bypass", budget=1, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    adj = A.adjacency(inst.n, inst.edges)
    bridges_before = A.low_link(adj).bridges
    bridges_after = A.low_link(new_adj).bridges
    assert bridges_before == [(7, 8)]
    assert bridges_after == []
    assert a.R_before == _approx(0.2500)
    assert a.R_after == _approx(0.2500)
    assert a.alpha_before == 0.0 and a.alpha_after == 0.0


def test_schneider_wins_both_metrics_preset_numbers():
    settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="schneider", budget=8, n_trials=150, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    assert a.R_before == _approx(0.2055)
    assert a.R_after == _approx(0.2384)
    assert a.alpha_before == _approx(2.8)
    assert a.alpha_after == _approx(0.8)
    assert a.beta_c_after == a.beta_c_before                      # exakt invariant (Gradfolge erhalten)
    assert a.R_after > a.R_before                                 # R: hoeher = besser
    assert a.alpha_after < a.alpha_before                         # alpha*: NIEDRIGER = robuster


def test_skalenfrei_bypass_fails_despite_targeted_edge_preset_numbers():
    settings = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="bypass", budget=8, n_trials=150, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    assert a.R_before == _approx(0.1112, abs_tol=0.0001)
    assert a.R_after == _approx(0.1112, abs_tol=0.0001)
    assert a.alpha_before == _approx(17.0)
    assert a.alpha_after is None                                  # SCHLECHTER als vorher: kein Sweep-Wert bis 20.0 reicht mehr aus

    settings20 = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="bypass", budget=20, n_trials=400, seed=35)
    _inst2, _new_adj2, a20 = ev.analyse(settings20)
    assert a20.R_after == _approx(0.1112, abs_tol=0.0001)          # auch bei mehr Budget exakt kein R-Gewinn
    assert a20.alpha_after is None


def test_random_shows_a_genuine_tradeoff_preset_numbers():
    """Zufällige Härtung macht bei diesem Budget/Seed R SCHLECHTER, aber alpha* gleichzeitig BESSER - ein echter Zielkonflikt zwischen zwei Kennzahlen, die unterschiedliche Angriffsmodelle
    messen (Grad-Angriff fuer R, hoechstbelasteter Knoten/Kaskade fuer alpha*)."""
    settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", strategy="random", budget=8, n_trials=150, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    assert a.R_after < a.R_before                                 # R wird schlechter
    assert a.alpha_after < a.alpha_before                          # alpha* wird gleichzeitig BESSER (niedriger)
    assert a.beta_c_after < a.beta_c_before                        # beta_c wird ebenfalls schlechter


def test_schneider_r_history_is_monotonic_in_the_preset():
    settings = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="schneider", budget=8, n_trials=400, seed=35)
    inst, new_adj, a = ev.analyse(settings)
    for prev, cur in zip(a.r_history, a.r_history[1:]):
        assert cur >= prev - 1e-12
    assert a.R_after > a.R_before


def test_onion_check_mixed_confirmation_preset_numbers():
    grid_settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", n_trials=800, seed=35)
    _inst_g, _adj_g, check_grid = ev.onion_check(grid_settings)
    assert check_grid.assort_after < check_grid.assort_before     # GEGEN die Zwiebelstruktur-Hypothese auf dem reinen Raster
    assert check_grid.R_after > check_grid.R_before                # R steigt trotzdem klar

    random_settings = ev.Settings(kind="city", side=13, blocked=0.0, nettype="random", n_trials=800, seed=35)
    _inst_r, _adj_r, check_random = ev.onion_check(random_settings)
    assert check_random.assort_after > check_random.assort_before  # bestaetigt die Hypothese auf dem Zufallsgraph
    assert check_random.assort_after - check_random.assort_before > 0.05


def test_budget_sweep_schneider_r_curve_is_non_decreasing_preset_numbers():
    settings = ev.Settings(kind="city", side=10, blocked=0.2, nettype="grid", seed=35)
    inst, rows, baseline = ev.budget_sweep(settings)
    schneider_rows = sorted((r for r in rows if r["strategy"] == "schneider"), key=lambda r: r["budget"])
    r_values = [baseline["R"]] + [r["R"] for r in schneider_rows]
    for prev, cur in zip(r_values, r_values[1:]):
        assert cur >= prev - 1e-9


def test_skalenfrei_high_budget_comparison_preset_numbers():
    settings = ev.Settings(kind="ba", n_ba=150, m_ba=2, m0_ba=4, strategy="schneider", budget=20, n_trials=400, seed=35)
    inst, rows, baseline = ev.strategy_comparison(settings)
    by_strategy = {r["strategy"]: r for r in rows}
    assert by_strategy["schneider"]["R"] > baseline["R"]
    assert by_strategy["schneider"]["alpha"] < baseline["alpha"]   # niedriger = robuster
    assert by_strategy["bypass"]["R"] == _approx(baseline["R"], abs_tol=0.0005)
    assert by_strategy["bypass"]["alpha"] is None                  # schlechter als die Baseline (17.0)
