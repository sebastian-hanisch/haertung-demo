"""Rauchtests der drei Instanzen, wortgleiche Kopien aus kaskaden-demo/robustheit-demo (Struktur unveraendert kopiert, nur Modulname angepasst)."""

import pytest

import haer_constants as C
import haer_scenario as S


def test_city_grid_has_expected_node_and_edge_bounds():
    inst = S.generate(side=6, blocked=0.0, nettype="grid", seed=1)
    assert inst.n == 36
    assert inst.m == 2 * 6 * 5     # vollstaendiges Raster: side*(side-1) horizontal + side*(side-1) vertikal


def test_city_blocked_removes_the_right_share():
    inst = S.generate(side=10, blocked=0.3, nettype="grid", seed=7)
    full = 2 * 10 * 9
    assert inst.m == full - round(0.3 * full)
    assert len(inst.blocked_edges) == round(0.3 * full)


def test_city_random_has_same_edge_count_as_grid_option():
    grid = S.generate(side=8, blocked=0.2, nettype="grid", seed=3)
    rand = S.generate(side=8, blocked=0.2, nettype="random", seed=3)
    assert rand.n == grid.n
    assert rand.m == grid.m
    assert rand.blocked_edges == ()


def test_city_generate_is_deterministic_given_the_same_seed():
    a = S.generate(side=9, blocked=0.2, nettype="grid", seed=42)
    b = S.generate(side=9, blocked=0.2, nettype="grid", seed=42)
    assert a.edges == b.edges
    assert (a.xy == b.xy).all()


def test_city_rejects_too_small_side():
    with pytest.raises(ValueError):
        S.generate(side=1)


def test_ba_instance_has_exact_edge_count():
    n, m, m0 = 60, 2, 4
    inst = S.barabasi_albert_instance(n, m, m0, seed=5)
    assert inst.n == n
    assert inst.m == m0 + (n - m0) * m


def test_ba_instance_is_deterministic():
    a = S.barabasi_albert_instance(50, 2, 4, seed=11)
    b = S.barabasi_albert_instance(50, 2, 4, seed=11)
    assert a.edges == b.edges


def test_ba_rejects_bad_parameters():
    with pytest.raises(ValueError):
        S.barabasi_albert_instance(50, 2, 2, seed=1)          # m0 < 3
    with pytest.raises(ValueError):
        S.barabasi_albert_instance(50, 5, 4, seed=1)          # m > m0


def test_barbell_has_two_cliques_and_one_bridge():
    k = 6
    inst = S.barbell_instance(k)
    assert inst.n == 2 * k
    assert inst.m == 2 * (k * (k - 1) // 2) + 1


def test_barbell_rejects_out_of_range_k():
    with pytest.raises(ValueError):
        S.barbell_instance(C.BARBELL_K_MIN - 1)
    with pytest.raises(ValueError):
        S.barbell_instance(C.BARBELL_K_MAX + 1)
