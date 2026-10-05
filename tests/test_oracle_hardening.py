"""Unabhängiges Orakel auf kleinen Zufallsgraphen: Kanten-/Knoten-Betweenness EXAKT als Bruch (Summe über Paare von sigma_sv * sigma_vt / sigma_st, anderer Rechenweg als Brandes), daraus
Kritische-Kante-Bypass und höchstbelasteter Knoten mit dem dokumentierten Gleichstand "kleinster Schlüssel". Ohne Toleranz im Ranking entschieden Gleitkomma-Rundungsreste symmetrischer Kanten.
Dazu: R (Robustheitsindex) gegen networkx-Komponenten, Schneider erhält die Gradfolge, R-Verlauf streng steigend und gleich dem neu berechneten R."""

import itertools
import random
from collections import deque
from fractions import Fraction

import pytest

import haer_algorithm as A
import haer_evaluation as E

nx = pytest.importorskip("networkx")


def _apsp(nbrs):
    n = len(nbrs)
    dist, sig = [], []
    for s in range(n):
        d, sg = [-1] * n, [0] * n
        d[s], sg[s] = 0, 1
        q = deque([s])
        while q:
            u = q.popleft()
            for v in nbrs[u]:
                if d[v] < 0:
                    d[v] = d[u] + 1
                    q.append(v)
                if d[v] == d[u] + 1:
                    sg[v] += sg[u]
        dist.append(d)
        sig.append(sg)
    return dist, sig


def _exact_between(nbrs):
    n = len(nbrs)
    dist, sig = _apsp(nbrs)
    node, edge = [Fraction(0)] * n, {}
    for s in range(n):
        for t in range(s + 1, n):
            if dist[s][t] <= 0:
                continue
            for v in range(n):
                if v not in (s, t) and dist[s][v] >= 0 and dist[v][t] >= 0 and dist[s][v] + dist[v][t] == dist[s][t]:
                    node[v] += Fraction(sig[s][v] * sig[v][t], sig[s][t])
            for u in range(n):
                for v in nbrs[u]:
                    if u < v:
                        c = 0
                        if dist[s][u] >= 0 and dist[v][t] >= 0 and dist[s][u] + 1 + dist[v][t] == dist[s][t]:
                            c += sig[s][u] * sig[v][t]
                        if dist[s][v] >= 0 and dist[u][t] >= 0 and dist[s][v] + 1 + dist[u][t] == dist[s][t]:
                            c += sig[s][v] * sig[u][t]
                        if c:
                            edge[(u, v)] = edge.get((u, v), Fraction(0)) + Fraction(c, sig[s][t])
    return node, edge


def _bypass_ref(adj, b):
    nbrs = [set(a) for a in adj]
    added = []
    for _ in range(b):
        _, eb = _exact_between([sorted(s) for s in nbrs])
        if not eb:
            break
        for (u, v), _load in sorted(eb.items(), key=lambda kv: (-kv[1], kv[0])):
            cands = sorted(w for w in nbrs[v] if w != u and w not in nbrs[u])
            if cands:
                nbrs[u].add(cands[0])
                nbrs[cands[0]].add(u)
                added.append((min(u, cands[0]), max(u, cands[0])))
                break
        else:
            break
    return added


def _graph(rng, n_lo=3, n_hi=12):
    n = rng.randrange(n_lo, n_hi + 1)
    pairs = list(itertools.combinations(range(n), 2))
    rng.shuffle(pairs)
    return n, sorted(pairs[:rng.randrange(n - 1, min(len(pairs), 2 * n) + 1)])


def test_bypass_and_highest_load_node_follow_exact_betweenness_ties_by_smallest_key():
    rng = random.Random(2)
    for _ in range(120):
        n, edges = _graph(rng)
        adj = A.adjacency(n, edges)
        b = rng.randrange(1, 5)
        assert A.harden_critical_bypass(adj, b)[1] == _bypass_ref(adj, b), (n, edges, b)
        node, _ = _exact_between(adj)
        assert E.highest_load_node(adj) == max(range(n), key=lambda v: (node[v], -v)), (n, edges)


def test_brandes_betweenness_matches_exact_values():
    rng = random.Random(3)
    for _ in range(60):
        n, edges = _graph(rng)
        adj = A.adjacency(n, edges)
        nb, eb, _ = A.betweenness_brandes(adj)
        node, edge = _exact_between(adj)
        assert all(abs(nb[v] - float(node[v])) < 1e-9 for v in range(n))
        assert all(abs(eb.get(e, 0.0) - float(edge.get(e, 0))) < 1e-9 for e in edges)


def _R_ref(n, adj):
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from((u, v) for u in range(n) for v in adj[u])
    total = 0
    while g.number_of_nodes():
        v = max(g.nodes, key=lambda x: (g.degree(x), -x))
        g.remove_node(v)
        total += max((len(c) for c in nx.connected_components(g)), default=0)
    return total / n / n


def test_schneider_keeps_degrees_and_r_history_is_strictly_increasing_and_correct():
    rng = random.Random(5)
    for it in range(40):
        n, edges = _graph(rng, 6, 18)
        adj = A.adjacency(n, edges)
        new_adj, accepted, hist = A.harden_schneider(adj, 40, it)
        assert [len(a) for a in adj] == [len(a) for a in new_adj]
        assert len(hist) == len(accepted) + 1 and all(hist[i + 1] > hist[i] for i in range(len(accepted)))
        assert abs(hist[0] - _R_ref(n, adj)) < 1e-12 and abs(hist[-1] - _R_ref(n, new_adj)) < 1e-12
        assert abs(E.robustness_R(new_adj) - _R_ref(n, new_adj)) < 1e-12
