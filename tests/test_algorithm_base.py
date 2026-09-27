"""Rauchtests der wortgleich kopierten Bausteine (adjacency, betweenness_brandes, components, low_link, degree_order_adaptive/remove_sequence/robustness_index, degree_assortativity) gegen
networkx als Gegenprobe."""

import networkx as nx
import pytest

import haer_algorithm as A
import haer_scenario as S


def _nx_graph(adj):
    g = nx.Graph()
    g.add_nodes_from(range(len(adj)))
    for u, nbrs in enumerate(adj):
        for v in nbrs:
            if u < v:
                g.add_edge(u, v)
    return g


INSTANCES = [S.generate(side=6, blocked=0.2, nettype="grid", seed=s) for s in range(1, 4)] + \
    [S.barabasi_albert_instance(30, 2, 4, s) for s in range(1, 4)] + \
    [S.barbell_instance(k) for k in (4, 6, 8)]


@pytest.mark.parametrize("inst", INSTANCES)
def test_betweenness_matches_networkx_unnormalized(inst):
    adj = A.adjacency(inst.n, inst.edges)
    node_between, _, _ = A.betweenness_brandes(adj)
    g = _nx_graph(adj)
    want = nx.betweenness_centrality(g, normalized=False)
    for v in range(inst.n):
        assert node_between[v] == pytest.approx(want[v], abs=1e-6)


@pytest.mark.parametrize("inst", INSTANCES)
def test_components_matches_networkx(inst):
    adj = A.adjacency(inst.n, inst.edges)
    sizes = sorted(A.components(adj))
    g = _nx_graph(adj)
    want = sorted(len(c) for c in nx.connected_components(g))
    assert sizes == want


@pytest.mark.parametrize("inst", INSTANCES)
def test_low_link_bridges_match_networkx(inst):
    adj = A.adjacency(inst.n, inst.edges)
    g = _nx_graph(adj)
    r = A.low_link(adj)
    want = {tuple(sorted(e)) for e in nx.bridges(g)} if nx.is_connected(g) else set()
    if nx.is_connected(g):
        got = {tuple(sorted(e)) for e in r.bridges}
        assert got == want


def test_barbell_bridge_is_found_exactly():
    inst = S.barbell_instance(8)
    adj = A.adjacency(inst.n, inst.edges)
    r = A.low_link(adj)
    assert r.bridges == [(7, 8)]


@pytest.mark.parametrize("inst", INSTANCES)
def test_degree_order_adaptive_is_a_permutation(inst):
    adj = A.adjacency(inst.n, inst.edges)
    order = A.degree_order_adaptive(adj)
    assert sorted(order) == list(range(inst.n))


@pytest.mark.parametrize("inst", INSTANCES)
def test_remove_sequence_length_and_endpoints(inst):
    adj = A.adjacency(inst.n, inst.edges)
    order = A.degree_order_adaptive(adj)
    sizes, counts, degrees = A.remove_sequence(adj, order)
    assert len(sizes) == len(counts) == len(degrees) == inst.n + 1
    assert sizes[0] == max(sorted(A.components(adj), reverse=True)[:1], default=0)
    assert sizes[-1] == 0


def test_robustness_index_is_1_for_a_never_disconnected_star_like_case():
    # 4 isolierte Knoten (kein Zusammenhang je Knoten selbst) -> R = mittlere Groesse der groessten Komponente/n ueber die gesamte Entfernung
    adj = [[] for _ in range(4)]
    order = list(range(4))
    sizes, _, _ = A.remove_sequence(adj, order)
    r = A.robustness_index(sizes, 4)
    assert 0.0 <= r <= 1.0


@pytest.mark.parametrize("inst", INSTANCES)
def test_degree_assortativity_matches_networkx(inst):
    adj = A.adjacency(inst.n, inst.edges)
    g = _nx_graph(adj)
    got = A.degree_assortativity(adj)
    want = nx.degree_pearson_correlation_coefficient(g)
    if want != want:                                    # NaN (konstanter Grad, z. B. Barbell-Cliquenrand oder BA-Kern)
        assert got != got
    else:
        assert got == pytest.approx(want, abs=1e-9)


def test_isolated_node_has_zero_betweenness_and_does_not_break_computation():
    n = 5
    edges = [(0, 1, 1.0), (1, 2, 1.0)]
    adj = A.adjacency(n, edges)
    node_between, _, _ = A.betweenness_brandes(adj)
    assert node_between[3] == 0.0 and node_between[4] == 0.0
    assert node_between[1] == pytest.approx(1.0)
