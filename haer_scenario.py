"""Drei Instanzen dieser Demo, wortgleich aus `kas_scenario.py`/`rob_scenario.py`/`cen_scenario.py` übernommen. **Betriebsnetz**: ein gestörtes Straßenraster (oder ein Zufallsgraph gleicher
Kantenzahl) - enge, fast reguläre Gradverteilung, keine echten Hubs. **Skalenfreies Netz** (Barabási-Albert 1999): wenige extrem gut vernetzte Hubs - der Vehikel-Kontrast für alle drei Härtungs-
strategien (ein Hub-Bypass hebelt anders als ein zufälliges Kantenpaar). **Barbell-Lehrbuch**: die beiden Brückenendknoten sind der einzige Engpass zwischen den beiden Cliquen - der dramatischste
Lehrbuchfall für `harden_critical_bypass` (schon EINE Bypass-Kante beseitigt den Single Point of Failure vollständig, s. `tests/test_algorithm_base.py`).

Knoten sind von 0 bis n-1 durchnummeriert; Kanten (u, v, w) mit u < v, sortiert; w = Länge (nur zur Anzeige, für die Härtung selbst ungewichtet)."""

import math
import random
from dataclasses import dataclass

import numpy as np

import haer_constants as C


@dataclass(frozen=True)
class Instance:
    xy: np.ndarray                 # (n, 2)
    edges: tuple                   # ((u, v, w), ...) sortiert
    kind: str = "city"             # "city" | "ba" | "barbell"
    nettype: str = "grid"          # nur kind == "city": "grid" | "random"
    side: int = 0                  # nur kind == "city"
    blocked: float = 0.0           # nur kind == "city"
    seed: int = 0
    blocked_edges: tuple = ()      # gesperrte Straßen (u, v), nur zur Anzeige (nur beim Raster)
    m_ba: int = 0                  # nur kind == "ba"
    m0_ba: int = 0                 # nur kind == "ba"
    k_barbell: int = 0             # nur kind == "barbell"

    @property
    def n(self):
        return len(self.xy)

    @property
    def m(self):
        return len(self.edges)


def make_rng(seed, salt):
    """Zufallsquelle mit fester, plattformunabhängiger Zahlenfolge (Python-`random`, nicht numpy: die Instanzen und alle daraus gezählten Zahlen ändern sich nie mit einer Bibliotheksversion)."""
    return random.Random(int(seed) * 1_000_003 + int(salt))


# --- Betriebsnetz (wortgleiche Kopie aus kas_scenario.py/rob_scenario.py/cen_scenario.py) ---------------------------------------------------------------


def grid_edges(side):
    out = []
    for r in range(side):
        for c in range(side):
            v = r * side + c
            if c + 1 < side:
                out.append((v, v + 1))
            if r + 1 < side:
                out.append((v, v + side))
    return out


def block(pairs, share, rng):
    """Sperrt genau `round(share * Zahl der Straßen)` Straßen, zufällig und OHNE Rücksicht auf den Zusammenhang. Gibt (verbleibende, gesperrte) zurück."""
    target = int(round(share * len(pairs)))
    order = list(range(len(pairs)))
    rng.shuffle(order)
    removed = set(order[:target])
    kept = [pairs[j] for j in range(len(pairs)) if j not in removed]
    return kept, [pairs[j] for j in sorted(removed)]


def random_pairs(n, m, rng):
    """`m` verschiedene Kanten zwischen zufälligen verschiedenen Knotenpaaren (einfacher Graph)."""
    max_m = n * (n - 1) // 2
    m = min(m, max_m)
    chosen = set()
    while len(chosen) < m:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v:
            continue
        chosen.add((min(u, v), max(u, v)))
    return sorted(chosen)


def generate(side=C.DEFAULT_SIDE, blocked=C.DEFAULT_BLOCKED, nettype="grid", seed=C.DEFAULT_SEED, jitter=C.JITTER):
    if nettype not in C.NETTYPES:
        raise ValueError(f"unbekannter Netztyp {nettype}")
    side = int(side)
    if side < 2:
        raise ValueError("Seitenlänge mindestens 2")
    n = side * side
    rng = make_rng(seed, 4711)
    xy = np.array([[c * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING, r * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING] for r in range(side) for c in range(side)], dtype=float)
    kept, removed = block(grid_edges(side), float(blocked), rng)
    if nettype == "random":
        rng2 = make_rng(seed, 9173)
        kept = random_pairs(n, len(kept), rng2)
        removed = []
    edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in kept)
    return Instance(xy, edges, "city", nettype, side, float(blocked), int(seed), tuple(removed))


# --- Skalenfreies Netz (Barabási und Albert 1999, wortgleiche Kopie aus kas_scenario.py/rob_scenario.py) -----------------------------------------------


def barabasi_albert_instance(n, m, m0, seed):
    """Kern: ein Kreis über m0 Knoten (m0 Kanten, jeder Kernknoten Grad 2, von Anfang an zusammenhängend). Jeder weitere Knoten t=m0..n-1 hängt sich mit m Kanten an m verschiedene bereits vorhandene
    Knoten an, gezogen proportional zum aktuellen Grad (bevorzugte Anbindung): eine Liste der Kantenenden (jeder Knoten so oft darin, wie er schon Kanten hat) macht die gewichtete Ziehung effizient -
    ein zufällig gezogenes Element der Liste trifft jeden Knoten mit Wahrscheinlichkeit proportional zu seinem Grad. Exakte Kantenzahl m0+(n-m0)*m."""
    n = int(n)
    m = int(m)
    m0 = int(m0)
    if m0 < 3:
        raise ValueError("m0 muss mindestens 3 sein (Kern ist ein Kreis über m0 Knoten, ein Kreis über 2 Knoten wäre eine Mehrfachkante)")
    if not (1 <= m <= m0):
        raise ValueError(f"m muss zwischen 1 und m0={m0} liegen")
    if n < m0:
        raise ValueError("n muss mindestens m0 sein")
    rng = make_rng(seed, 8117)
    edges = []
    stubs = []
    for i in range(m0):
        j = (i + 1) % m0
        u, v = min(i, j), max(i, j)
        edges.append((u, v))
        stubs.append(u)
        stubs.append(v)
    for new in range(m0, n):
        chosen = set()
        while len(chosen) < m:
            cand = stubs[rng.randrange(len(stubs))]
            if cand != new and cand not in chosen:
                chosen.add(cand)
        for t in sorted(chosen):
            edges.append((t, new))
            stubs.append(t)
            stubs.append(new)
    edges.sort()
    xy = np.zeros((n, 2), dtype=float)
    for i in range(m0):
        ang = 2 * math.pi * i / m0
        xy[i] = [1.6 * math.cos(ang), 1.6 * math.sin(ang)]
    layout_rng = make_rng(seed, 2477)
    for i in range(m0, n):
        ang = 2 * math.pi * layout_rng.random()
        rad = 0.3 + 1.3 * layout_rng.random()
        xy[i] = [rad * math.cos(ang), rad * math.sin(ang)]
    out_edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in edges)
    return Instance(xy, out_edges, "ba", "grid", 0, 0.0, int(seed), (), int(m), int(m0))


# --- Barbell-Lehrbuch (wortgleiche Kopie aus kas_scenario.py/cen_scenario.py) ----------------------------------------------------------------------------


def barbell_instance(k=C.DEFAULT_BARBELL_K):
    """Der **Barbell-Graph**: zwei vollständige Graphen K_k (Knoten 0..k-1 links, k..2k-1 rechts), verbunden durch eine einzelne Brücke zwischen Knoten k-1 (letzter links) und k (erster rechts).
    Jeder Clique-Knoten ohne Brückenende hat Grad k-1; die beiden Brückenenden haben Grad k - der einzige Engpass zwischen den beiden Cliquen, fällt er aus ist der Graph SOFORT in zwei Hälften
    der Größe k-1 und k getrennt."""
    k = int(k)
    if not C.BARBELL_K_MIN <= k <= C.BARBELL_K_MAX:
        raise ValueError(f"k muss zwischen {C.BARBELL_K_MIN} und {C.BARBELL_K_MAX} liegen")
    n = 2 * k
    pairs = [(i, j) for i in range(k) for j in range(i + 1, k)]
    pairs += [(k + i, k + j) for i in range(k) for j in range(i + 1, k)]
    pairs.append((k - 1, k))
    pairs = sorted(pairs)
    # Layout: linke Clique als Kreis um (0,0), rechte Clique als Kreis um (3,0), Brücke waagerecht dazwischen.
    xy = np.zeros((n, 2), dtype=float)
    for i in range(k):
        ang = 2 * math.pi * i / k
        xy[i] = [-1.5 + 0.9 * math.cos(ang), 0.9 * math.sin(ang)]
        xy[k + i] = [1.5 + 0.9 * math.cos(ang), 0.9 * math.sin(ang)]
    edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in pairs)
    return Instance(xy, edges, "barbell", "grid", 0, 0.0, 0, (), 0, 0, int(k))
