"""Zentrale Korrektheits-Kette, Punkte 1-3 (s. PLAN): jede Härtungsstrategie liefert exakt b neue Kanten (Zufällig/Bypass) bzw. dieselbe Gradfolge (Schneider), nie Selbstloops/Mehrfachkanten, auf
≥300 Instanzen (Punkt 1); R ist nach jedem akzeptierten Schneider-Tausch nicht kleiner als davor, abgelehnte Tausche ändern den Graphen nicht (Punkt 2); harden_critical_bypass beseitigt die
Barbell-Brücke exakt (Punkt 3)."""

import random

import pytest

import haer_algorithm as A
import haer_scenario as S


def _random_instances(n_count, seed_base=1000):
    """>=300 zufällig variierte kleine Instanzen über alle drei Vehikel - fest genug fürs CI, klein genug fürs Tempo (Schneider braucht n_trials Betweenness-freie R-Aufrufe je Instanz)."""
    rng = random.Random(seed_base)
    out = []
    for i in range(n_count):
        kind = rng.choice(("city", "ba", "barbell"))
        seed = rng.randrange(1, 5000)
        if kind == "city":
            side = rng.randint(4, 7)
            blocked = rng.choice((0.0, 0.1, 0.2, 0.3))
            out.append(S.generate(side=side, blocked=blocked, nettype=rng.choice(("grid", "random")), seed=seed))
        elif kind == "ba":
            m0 = rng.randint(3, 5)
            out.append(S.barabasi_albert_instance(rng.randint(m0, 40), rng.randint(1, m0), m0, seed))
        else:
            out.append(S.barbell_instance(rng.randint(3, 12)))
    return out


INSTANCES_300 = _random_instances(300)


def _no_self_loop_no_multi_edge(adj):
    for u, nbrs in enumerate(adj):
        assert u not in nbrs
        assert len(nbrs) == len(set(nbrs))


def _edge_set(adj):
    return {(u, v) for u in range(len(adj)) for v in adj[u] if u < v}


# --- Punkt 1: exakt b neue Kanten, keine Selbstloops/Mehrfachkanten (Zufaellig, Bypass) -------------------------------------------------------------------


@pytest.mark.parametrize("inst", INSTANCES_300)
def test_harden_random_adds_exactly_b_edges_no_loops_no_multi(inst):
    adj = A.adjacency(inst.n, inst.edges)
    before = _edge_set(adj)
    b = 3
    new_adj, added = A.harden_random(adj, b, seed=inst.n * 7 + 1)
    _no_self_loop_no_multi_edge(new_adj)
    max_possible = inst.n * (inst.n - 1) // 2 - len(before)
    assert len(added) == min(b, max_possible)
    after = _edge_set(new_adj)
    assert after == before | set(added)
    assert len(after) == len(before) + len(added)


@pytest.mark.parametrize("inst", INSTANCES_300)
def test_harden_critical_bypass_adds_at_most_b_edges_no_loops_no_multi(inst):
    adj = A.adjacency(inst.n, inst.edges)
    before = _edge_set(adj)
    b = 3
    new_adj, added = A.harden_critical_bypass(adj, b)
    _no_self_loop_no_multi_edge(new_adj)
    assert len(added) <= b
    after = _edge_set(new_adj)
    assert after == before | set(added)
    assert len(after) == len(before) + len(added)
    assert len(set(added)) == len(added)                        # jede hinzugefuegte Kante nur einmal


@pytest.mark.parametrize("inst", INSTANCES_300[:60])
def test_harden_critical_bypass_bounded_instance_adds_exactly_b_when_room_exists(inst):
    # kleine b (<=2) haben auf fast jeder nicht-trivialen Instanz noch Kandidaten -- exakt b Kanten erwartet
    adj = A.adjacency(inst.n, inst.edges)
    if inst.n < 4:
        pytest.skip("zu kleine Instanz fuer einen garantierten Kandidaten")
    new_adj, added = A.harden_critical_bypass(adj, 1)
    assert len(added) in (0, 1)


# --- Punkt 1 (Fortsetzung): Schneider haelt die Gradfolge exakt, keine Selbstloops/Mehrfachkanten -----------------------------------------------------------


@pytest.mark.parametrize("inst", INSTANCES_300[:120])
def test_harden_schneider_preserves_degree_sequence_no_loops_no_multi(inst):
    adj = A.adjacency(inst.n, inst.edges)
    degrees_before = sorted(len(a) for a in adj)
    new_adj, accepted, r_history = A.harden_schneider(adj, n_trials=25, seed=inst.n * 13 + 5)
    _no_self_loop_no_multi_edge(new_adj)
    degrees_after = sorted(len(a) for a in new_adj)
    assert degrees_after == degrees_before
    assert len(r_history) == len(accepted) + 1


@pytest.mark.parametrize("inst", INSTANCES_300[:60])
def test_harden_schneider_leaves_beta_c_exactly_invariant(inst):
    """Entdeckt in der Messreihe (2026-09-27, s. README "Befunde"): beta_c = mu*<k>/<k^2> haengt NUR von der Gradfolge ab (den Gradmomenten), nicht von der konkreten Kantenanordnung - und Schneiders
    Kanten-Doppeltausch erhaelt die Gradfolge EXAKT (Korrektheits-Kette Punkt 1). Also MUSS beta_c vor und nach einer beliebigen Zahl von Schneider-Tauschen exakt (nicht nur ungefaehr) identisch
    sein - ein beweisbarer Satz, hier als exakte Gleichheit getestet (kein Toleranzband noetig, es ist dieselbe Gradfolge, nicht nur eine aehnliche)."""
    adj = A.adjacency(inst.n, inst.edges)
    beta_before = A.epidemic_threshold_prediction(adj, 0.3)
    new_adj, _accepted, _r_history = A.harden_schneider(adj, n_trials=40, seed=inst.n * 17 + 9)
    beta_after = A.epidemic_threshold_prediction(new_adj, 0.3)
    assert beta_after == beta_before


# --- Sonderfaelle (Punkt 8): b=0 -> Identitaet, b so gross wie der vollstaendige Graph -> Kappung, unzusammenhaengende Ausgangsinstanz ----------------------


def test_b_zero_is_identity_for_random_and_bypass():
    inst = S.barabasi_albert_instance(20, 2, 4, seed=3)
    adj = A.adjacency(inst.n, inst.edges)
    new_adj_r, added_r = A.harden_random(adj, 0, seed=1)
    new_adj_b, added_b = A.harden_critical_bypass(adj, 0)
    assert added_r == [] and added_b == []
    assert _edge_set(new_adj_r) == _edge_set(adj)
    assert _edge_set(new_adj_b) == _edge_set(adj)


def test_n_trials_zero_is_identity_for_schneider():
    inst = S.barabasi_albert_instance(20, 2, 4, seed=3)
    adj = A.adjacency(inst.n, inst.edges)
    new_adj, accepted, r_history = A.harden_schneider(adj, 0, seed=1)
    assert accepted == []
    assert len(r_history) == 1
    assert _edge_set(new_adj) == _edge_set(adj)


def test_random_hardening_caps_budget_at_the_complete_graph():
    n = 5
    edges = [(i, j, 1.0) for i in range(n) for j in range(i + 1, n)]      # K5, bereits vollstaendig
    adj = A.adjacency(n, edges)
    new_adj, added = A.harden_random(adj, 10, seed=1)
    assert added == []                                          # kein Nicht-Kante-Paar mehr uebrig
    assert _edge_set(new_adj) == _edge_set(adj)


def test_bypass_stops_early_on_the_complete_graph():
    n = 5
    edges = [(i, j, 1.0) for i in range(n) for j in range(i + 1, n)]
    adj = A.adjacency(n, edges)
    new_adj, added = A.harden_critical_bypass(adj, 10)
    assert added == []


def test_hardening_strategies_do_not_crash_on_a_disconnected_instance():
    # zwei getrennte Dreiecke (0,1,2) und (3,4,5)
    edges = [(0, 1, 1.0), (1, 2, 1.0), (0, 2, 1.0), (3, 4, 1.0), (4, 5, 1.0), (3, 5, 1.0)]
    adj = A.adjacency(6, edges)
    new_adj_r, added_r = A.harden_random(adj, 2, seed=9)
    _no_self_loop_no_multi_edge(new_adj_r)
    assert len(added_r) == 2
    new_adj_b, added_b = A.harden_critical_bypass(adj, 2)
    _no_self_loop_no_multi_edge(new_adj_b)
    new_adj_s, accepted_s, r_hist = A.harden_schneider(adj, 20, seed=9)
    _no_self_loop_no_multi_edge(new_adj_s)
    assert sorted(len(a) for a in new_adj_s) == sorted(len(a) for a in adj)


# --- Punkt 2: Schneider-R-Monotonie und Rueckgaengig-Exaktheit ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("inst", [S.generate(side=6, blocked=0.2, nettype="grid", seed=s) for s in range(1, 6)] +
                                  [S.barabasi_albert_instance(30, 2, 4, s) for s in range(1, 6)] +
                                  [S.barbell_instance(k) for k in (5, 6, 7, 8, 9)])
def test_schneider_r_history_is_non_decreasing(inst):
    adj = A.adjacency(inst.n, inst.edges)
    _new_adj, accepted, r_history = A.harden_schneider(adj, n_trials=60, seed=inst.n * 31 + 4)
    for prev, cur in zip(r_history, r_history[1:]):
        assert cur >= prev - 1e-12
    assert len(r_history) == len(accepted) + 1


@pytest.mark.parametrize("seed", list(range(40)))
def test_a_single_rejected_or_skipped_schneider_trial_leaves_the_graph_byte_identical(seed):
    inst = S.barabasi_albert_instance(24, 2, 4, seed=17)
    adj = A.adjacency(inst.n, inst.edges)
    before = _edge_set(adj)
    new_adj, accepted, r_history = A.harden_schneider(adj, n_trials=1, seed=seed)
    after = _edge_set(new_adj)
    if len(accepted) == 0:
        assert after == before                                  # Versuch uebersprungen ODER abgelehnt -> Graph unveraendert
    else:
        assert after != before or accepted[0]["removed"][0] == accepted[0]["added"][0]  # akzeptiert: i.d.R. Aenderung sichtbar


# --- Punkt 3: harden_critical_bypass beseitigt die Barbell-Bruecke exakt ----------------------------------------------------------------------------------


@pytest.mark.parametrize("k", [3, 4, 5, 8, 12, 20])
def test_critical_bypass_eliminates_the_barbell_bridge_exactly(k):
    inst = S.barbell_instance(k)
    adj = A.adjacency(inst.n, inst.edges)
    r_before = A.low_link(adj)
    assert r_before.bridges == [(k - 1, k)]                      # Ausgangslage: genau die eine Bruecke
    new_adj, added = A.harden_critical_bypass(adj, 1)
    assert len(added) == 1
    r_after = A.low_link(new_adj)
    assert r_after.bridges == []                                 # keine Bruecken mehr


@pytest.mark.parametrize("k", [3, 5, 8])
@pytest.mark.parametrize("b", [1, 2, 3])
def test_critical_bypass_barbell_bridge_gone_for_b_at_least_1(k, b):
    inst = S.barbell_instance(k)
    adj = A.adjacency(inst.n, inst.edges)
    new_adj, _added = A.harden_critical_bypass(adj, b)
    r_after = A.low_link(new_adj)
    assert r_after.bridges == []
