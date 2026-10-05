"""Bausteine (`adjacency`, `bfs_distances`, `degree_centrality`, `betweenness_brandes` + Hilfsfunktionen, `components`, die lastbasierte Kaskade, SIR-Ausbreitung/Epidemieschwelle) sind wortgleiche
Kopien aus `kas_algorithm.py` (Kaskaden-Demo, Stück 9 - dort schon aus `rob_algorithm.py`/`cen_algorithm.py` übernommen). `low_link` (Brücken-Erkennung) ist eine wortgleiche Kopie aus
`cen_algorithm.py` (Zentralität-Demo, Stück 6). `random_order`, `degree_order_adaptive`, `remove_sequence`, `robustness_index` sind wortgleiche Kopien aus `rob_algorithm.py` (Robustheit-Demo,
Stück 8). `degree_assortativity` ist eine wortgleiche Kopie aus `sk_algorithm.py` (Strukturkennzahlen-Demo, Stück 7).

Darauf drei NEUE Härtungsstrategien - ein begrenztes Budget B (zusätzliche Kanten) bzw. ein Trainingsaufwand (Versuche), um ein Netz gegen die geerbten Kennzahlen (R aus Stück 8, α* aus Stück 9,
β_c aus Stück 9, Assortativität aus Stück 7) widerstandsfähiger zu machen:

**Zufällig** (`harden_random`): b neue Kanten zwischen zufälligen, noch nicht benachbarten Knotenpaaren - die naive Referenz ohne jedes Strukturwissen.

**Kritische-Kante-Bypass** (`harden_critical_bypass`): b mal wiederholen - die aktuell am stärksten belastete Kante (Kanten-Betweenness, Brandes) finden und einen Umweg zu einem Nachbarn des
"hinteren" Endpunkts hinzufügen (kein Kandidat verfügbar → nächstbelastete Kante versuchen) - gezielt gegen den größten Engpass, mit vollständiger Betweenness-Neuberechnung nach jeder Kante.

**Schneider u. a. 2011** (`harden_schneider`, PNAS 108(10), 3838-3841): ein Kanten-Doppeltausch wie `configuration_null` (Maslov & Sneppen 2002, gradfolgen-erhaltend), aber NICHT zufällig
akzeptiert - nur wenn der Tausch den Robustheitsindex R (unter dem GÜNSTIGEN, grad-adaptiven Angriff aus Stück 8 - keine teure Betweenness-Neuberechnung je Versuch nötig) gegenüber dem Zustand vor
genau diesem einen Versuch strikt verbessert, sonst wird er sofort rückgängig gemacht (ein echter Hill-Climb, kein simuliertes Auskühlen - eine dokumentierte Vereinfachung, s. README)."""

import heapq
import math
import random
from collections import deque
from dataclasses import dataclass, field


# --- Wortgleiche Kopien aus kas_algorithm.py (Kaskaden-Demo, dort schon aus rob_algorithm.py/cen_algorithm.py uebernommen) -------------------------------


def adjacency(n, edges, order="fixed", seed=0):
    """Adjazenzliste aus Kanten (u, v, ...); "fixed" = aufsteigende Nachbarn, "shuffled" = je Knoten gemischt (Seed fest, Python-`random`). Wortgleiche Kopie aus `kas_algorithm.py`."""
    adj = [[] for _ in range(n)]
    for e in edges:
        u, v = int(e[0]), int(e[1])
        adj[u].append(v)
        adj[v].append(u)
    for lst in adj:
        lst.sort()
    if order == "shuffled":
        rng = random.Random(int(seed) * 1_000_003 + 5150)
        for lst in adj:
            rng.shuffle(lst)
    elif order != "fixed":
        raise ValueError(f"unbekannte Reihenfolge {order}")
    return adj


def bfs_distances(adj, s):
    """Abstand von s zu jedem erreichbaren Knoten (-1 = unerreichbar). Gibt (dist, Schritte) zurück. Wortgleiche Kopie aus `kas_algorithm.py`."""
    n = len(adj)
    dist = [-1] * n
    dist[s] = 0
    queue = deque([s])
    steps = 1
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            steps += 1
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
                steps += 1
    return dist, steps


def degree_centrality(adj):
    """Grad je Knoten (Zahl der Nachbarn). Wortgleiche Kopie aus `kas_algorithm.py`."""
    return [len(nbrs) for nbrs in adj]


def _key(u, v):
    return (u, v) if u < v else (v, u)


def _shortest_path_dag(adj, s):
    """BFS-Vorgänger-DAG von s: (dist, sigma, order (Entdeckungsreihenfolge), preds, Schritte). Wortgleiche Kopie aus `kas_algorithm.py`."""
    n = len(adj)
    dist = [-1] * n
    sigma = [0] * n
    dist[s] = 0
    sigma[s] = 1
    preds = [[] for _ in range(n)]
    order = [s]
    queue = deque([s])
    steps = 1
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            steps += 1
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
                order.append(v)
                steps += 1
            if dist[v] == dist[u] + 1:
                sigma[v] += sigma[u]
                preds[v].append(u)
    return dist, sigma, order, preds, steps


@dataclass
class BrandesRun:
    source: int
    dist: list
    sigma: list
    order: list             # BFS-Entdeckungsreihenfolge (Vorwärtsphase)
    preds: list
    delta: list = field(default_factory=list)          # Abhängigkeit je Knoten NACH der Rückwärtsphase
    edge_delta: dict = field(default_factory=dict)      # Kanten-Abhängigkeit dieser einen Quelle
    steps: int = 0


def brandes_source(adj, s):
    """Ein Brandes-Durchlauf von einer einzigen Quelle s. Wortgleiche Kopie aus `kas_algorithm.py`."""
    dist, sigma, order, preds, steps = _shortest_path_dag(adj, s)
    n = len(adj)
    delta = [0.0] * n
    edge_delta = {}
    for w in reversed(order):
        coeff = (1.0 + delta[w]) / sigma[w]
        steps += 1
        for v in preds[w]:
            steps += 1
            c = sigma[v] * coeff
            delta[v] += c
            e = _key(v, w)
            edge_delta[e] = edge_delta.get(e, 0.0) + c
    return BrandesRun(s, dist, sigma, order, preds, delta, edge_delta, steps)


def betweenness_brandes(adj):
    """Brandes (2001): eine BFS je Startknoten (O(n*m) insgesamt), liefert Knoten- UND Kanten-Betweenness (unnormiert). Gibt (Knoten-Liste, Kanten-Dict, Elementarschritte) zurück. Wortgleiche Kopie
    aus `kas_algorithm.py`. Ein Knoten ohne Nachbarn durchläuft eine triviale Ein-Knoten-BFS und trägt rechnerisch 0 bei - so liefert dieselbe Funktion unverändert auch die Restgraph-Betweenness."""
    n = len(adj)
    node_raw = [0.0] * n
    edge_raw = {}
    steps = 0
    for s in range(n):
        run = brandes_source(adj, s)
        steps += run.steps
        for v in range(n):
            if v != s:
                node_raw[v] += run.delta[v]
        for e, c in run.edge_delta.items():
            edge_raw[e] = edge_raw.get(e, 0.0) + c
    node_between = [v * 0.5 for v in node_raw]
    edge_between = {e: c * 0.5 for e, c in edge_raw.items()}
    return node_between, edge_between, steps


def components(adj):
    """Liste der Komponentengrößen (Reihenfolge = Fundreihenfolge des kleinsten Knotens jeder Komponente), über wiederholte BFS. Wortgleiche Kopie aus `kas_algorithm.py`."""
    n = len(adj)
    seen = [False] * n
    sizes = []
    for s in range(n):
        if seen[s]:
            continue
        dist, _ = bfs_distances(adj, s)
        comp = [v for v, d in enumerate(dist) if d >= 0]
        for v in comp:
            seen[v] = True
        sizes.append(len(comp))
    return sizes


# --- Low-Link / Brücken-Erkennung (wortgleiche Kopie aus cen_algorithm.py, Zentralität-Demo, dort aus bridges-demo übernommen) ---------------------------


@dataclass
class LowLink:
    disc: list                                            # Entdeckungszeit je Knoten (1, 2, ...)
    low: list                                             # kleinste Entdeckungszeit, die vom Teilbaum des Knotens über höchstens eine Rückwärtskante erreichbar ist
    parent: list
    root: list                                            # Wurzel der Tiefensuche-Komponente je Knoten
    size: list                                            # Größe des Teilbaums je Knoten
    bridges: list = field(default_factory=list)           # (u, v) mit u < v, in Fundreihenfolge
    articulation: set = field(default_factory=set)
    blocks: list = field(default_factory=list)            # frozenset von Kanten (u, v) je Block, in Fundreihenfolge
    steps: int = 0
    events: list = field(default_factory=list)
    comp_size: dict = field(default_factory=dict)         # Wurzel -> Größe der Komponente


def low_link(adj):
    """Tarjans Low-Link, iterativ: Baumkante (p, u) ist Brücke, wenn low[u] > disc[p]; p ist Artikulationspunkt, wenn ein Kind u low[u] >= disc[p] hat (Wurzel: mindestens zwei Kinder).
    Die Blöcke werden mit einem Kantenstapel abgetrennt (Hopcroft und Tarjan 1973). Wortgleiche Kopie aus `cen_algorithm.py`."""
    n = len(adj)
    disc, low, parent, root, size = [0] * n, [0] * n, [-1] * n, [-1] * n, [1] * n
    r = LowLink(disc, low, parent, root, size)
    clock = 0
    children = [0] * n
    pos = [0] * n
    edge_stack = []
    for s in range(n):
        if disc[s]:
            continue
        clock += 1
        disc[s] = low[s] = clock
        root[s] = s
        r.steps += 1
        r.events.append(("root", s))
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(adj[u]):
                v = adj[u][pos[u]]
                pos[u] += 1
                r.steps += 1
                if not disc[v]:
                    parent[v] = u
                    root[v] = s
                    children[u] += 1
                    edge_stack.append(_key(u, v))
                    clock += 1
                    disc[v] = low[v] = clock
                    r.steps += 1
                    stack.append(v)
                    r.events.append(("discover", v, u))
                elif v != parent[u] and disc[v] < disc[u]:
                    edge_stack.append(_key(u, v))
                    if disc[v] < low[u]:
                        low[u] = disc[v]
                    r.events.append(("back", u, v))
            else:
                stack.pop()
                p = parent[u]
                bridge_flag = artic_flag = False
                if p != -1:
                    size[p] += size[u]
                    if low[u] < low[p]:
                        low[p] = low[u]
                    if low[u] > disc[p]:
                        r.bridges.append(_key(p, u))
                        bridge_flag = True
                    if low[u] >= disc[p]:
                        block = []
                        while True:
                            e = edge_stack.pop()
                            block.append(e)
                            if e == _key(p, u):
                                break
                        r.blocks.append(frozenset(block))
                        if parent[p] != -1:
                            r.articulation.add(p)
                            artic_flag = True
                r.events.append(("finish", u, p, low[u], bridge_flag, artic_flag))
        if children[s] >= 2:
            r.articulation.add(s)
        r.comp_size[s] = size[s]
    return r


# --- Entfernungsstrategien / Robustheitsindex (wortgleiche Kopie aus rob_algorithm.py, Robustheit-Demo, Stück 8) ----------------------------------------


def random_order(n, seed):
    """Gleichverteilte Zufallspermutation der n Knoten (Python-`random`-Hauskonvention, plattformunabhängig). Wortgleiche Kopie aus `rob_algorithm.py`."""
    rng = random.Random(int(seed) * 1_000_003 + 3391)
    order = list(range(n))
    rng.shuffle(order)
    return order


def degree_order_adaptive(adj):
    """Wiederholt der Knoten mit dem AKTUELL höchsten Grad im Restgraphen (Cohen u. a. 2001). Effizient über einen Max-Heap mit mitgeführten Gradzählern und Nachbarmengen: bei jeder Entfernung werden
    nur die Grade der (ehemaligen) Nachbarn dekrementiert und eine neue Heap-Eintragung für sie gepusht (lazy deletion). Gleichstand nach kleinstem Index. Wortgleiche Kopie aus `rob_algorithm.py`."""
    n = len(adj)
    neighbours = [set(a) for a in adj]
    degree = [len(a) for a in adj]
    alive = [True] * n
    heap = [(-degree[v], v) for v in range(n)]
    heapq.heapify(heap)
    order = []
    while heap:
        neg_d, v = heapq.heappop(heap)
        if not alive[v] or -neg_d != degree[v]:
            continue
        order.append(v)
        alive[v] = False
        for u in neighbours[v]:
            if alive[u]:
                neighbours[u].discard(v)
                degree[u] -= 1
                heapq.heappush(heap, (-degree[u], u))
        neighbours[v] = set()
    return order


def remove_sequence(adj, order):
    """Entfernt die Knoten in `order` einen nach dem anderen (k=0..n Knoten entfernt) und misst nach JEDEM Schritt: Größe der größten Komponente S(k) (Riesenkomponente), Zahl der Komponenten unter
    den verbleibenden Knoten, mittlerer Restgrad. Gibt drei Listen der Länge n+1 zurück (Index k = Zustand nach k Entfernungen; k=0 ist das ursprüngliche Netz). Wortgleiche Kopie aus
    `rob_algorithm.py`."""
    n = len(adj)
    neighbours = [set(a) for a in adj]
    alive = [True] * n

    def _state():
        remaining = [v for v in range(n) if alive[v]]
        if not remaining:
            return 0, 0, 0.0
        sub_adj = [sorted(neighbours[v]) if alive[v] else [] for v in range(n)]
        alive_sizes = [len(comp) for comp in _alive_components(sub_adj, alive)]
        largest = max(alive_sizes) if alive_sizes else 0
        mean_degree = sum(len(neighbours[v]) for v in remaining) / len(remaining)
        return largest, len(alive_sizes), mean_degree

    largest_seq, count_seq, degree_seq = [], [], []
    l0, c0, d0 = _state()
    largest_seq.append(l0)
    count_seq.append(c0)
    degree_seq.append(d0)
    for v in order:
        alive[v] = False
        for u in neighbours[v]:
            neighbours[u].discard(v)
        neighbours[v] = set()
        largest, count, mean_degree = _state()
        largest_seq.append(largest)
        count_seq.append(count)
        degree_seq.append(mean_degree)
    return largest_seq, count_seq, degree_seq


def _alive_components(sub_adj, alive):
    """Liste der Komponenten (je eine Liste lebender Knoten) unter den noch lebenden Knoten, per BFS - tote (isolierte) Knoten werden nicht mitgezählt. Wortgleiche Kopie aus `rob_algorithm.py`."""
    n = len(sub_adj)
    seen = [False] * n
    comps = []
    for s in range(n):
        if not alive[s] or seen[s]:
            continue
        dist, _ = bfs_distances(sub_adj, s)
        comp = [v for v, d in enumerate(dist) if d >= 0 and alive[v]]
        for v in comp:
            seen[v] = True
        comps.append(comp)
    return comps


def robustness_index(sizes, n):
    """R = (1/n) * Sum_{k=1}^{n} S(k)/n (Schneider, Moreira, Andrade, Herrmann & Havlin 2011) - die Fläche unter der (normierten) Riesenkomponenten-Kurve, ein zusammenfassender Robustheitswert je
    Strategie/Instanz. `sizes` ist S(k) für k=0..n; die Summe läuft bewusst NUR über k=1..n. Wortgleiche Kopie aus `rob_algorithm.py`."""
    if n <= 0:
        return 0.0
    total = sum(sizes[k] for k in range(1, n + 1)) / n
    return total / n


# --- Lastbasierte Kaskade (Motter & Lai 2002, wortgleiche Kopie aus kas_algorithm.py) ---------------------------------------------------------------------


def _sub_adjacency(adj, alive):
    """Adjazenzliste des Restgraphen: tote Knoten (alive[v]=False) bekommen eine LEERE Nachbarliste (statt entfernt/umnummeriert zu werden) - so bleiben Knotenindizes über alle Runden stabil.
    Wortgleiche Kopie aus `kas_algorithm.py`."""
    n = len(adj)
    return [sorted(u for u in adj[v] if alive[u]) if alive[v] else [] for v in range(n)]


def _alive_giant_size(sub_adj, alive):
    """Größte Komponente NUR unter den lebenden Knoten. Wortgleiche Kopie aus `kas_algorithm.py`."""
    n = len(sub_adj)
    seen = [False] * n
    best = 0
    for s in range(n):
        if not alive[s] or seen[s]:
            continue
        dist, _ = bfs_distances(sub_adj, s)
        comp = [v for v, d in enumerate(dist) if d >= 0 and alive[v]]
        for v in comp:
            seen[v] = True
        best = max(best, len(comp))
    return best


def motter_lai_cascade(adj, alpha, initial_removed):
    """Motter & Lai (2002): Anfangslast Last_i(0) = Betweenness auf dem VOLLEN Graphen (einmal berechnet); Kapazität_i = (1+α)·Last_i(0). Rundenweise: Betweenness auf dem Restgraphen (nur noch
    lebende Knoten) neu berechnen; jeder lebende Knoten mit aktueller Last > Kapazität fällt aus. Wiederholt, bis keine neuen Ausfälle mehr auftreten oder die Sicherheitsgrenze n Runden erreicht
    ist. Wortgleiche Kopie aus `kas_algorithm.py`.

    Gibt (rounds, G) zurück: `rounds` ist eine Liste von {"round": r, "newly_failed": [...], "giant_size": int}; `G` ist der Gesamtausfallanteil / n."""
    n = len(adj)
    alpha = float(alpha)
    initial_removed = sorted(set(int(v) for v in initial_removed))
    if any(not (0 <= v < n) for v in initial_removed):
        raise ValueError("initial_removed außerhalb des gültigen Knotenbereichs")
    node_between0, _, _ = betweenness_brandes(adj)
    capacity = [(1.0 + alpha) * node_between0[v] for v in range(n)]
    alive = [True] * n
    for v in initial_removed:
        alive[v] = False

    rounds = [{"round": 0, "newly_failed": list(initial_removed), "giant_size": _alive_giant_size(_sub_adjacency(adj, alive), alive)}]
    total_failed = set(initial_removed)
    safety_bound = n
    round_idx = 0
    tol = 1e-9
    while round_idx < safety_bound:
        round_idx += 1
        cur = _sub_adjacency(adj, alive)
        node_between_cur, _, _ = betweenness_brandes(cur)
        newly_failed = [v for v in range(n) if alive[v] and node_between_cur[v] > capacity[v] + tol]
        if not newly_failed:
            break
        for v in newly_failed:
            alive[v] = False
        total_failed.update(newly_failed)
        rounds.append({"round": round_idx, "newly_failed": newly_failed, "giant_size": _alive_giant_size(_sub_adjacency(adj, alive), alive)})
    G = len(total_failed) / n if n else 0.0
    return rounds, G


def critical_tolerance(adj, initial_removed, alphas):
    """Kleinstes α aus dem gegebenen (aufsteigend sortierten) Sweep, ab dem KEINE globale Kaskade mehr auftritt - operationalisiert als "die Kaskade endet schon nach der Anfangsrunde". Gibt `None`
    zurück, wenn selbst das größte α im Sweep noch eine Kaskade auslöst. Wortgleiche Kopie aus `kas_algorithm.py`."""
    for alpha in sorted(float(a) for a in alphas):
        rounds, _ = motter_lai_cascade(adj, alpha, initial_removed)
        if len(rounds) == 1:
            return alpha
    return None


# --- SIR-Ausbreitung / Epidemieschwelle (Pastor-Satorras & Vespignani 2001, wortgleiche Kopie aus kas_algorithm.py) ---------------------------------------


@dataclass
class SIRResult:
    trace: list
    final_s: int
    final_i: int
    final_r: int
    outbreak_size: int
    steps_run: int
    states: list = field(default_factory=list)


def sir_simulate(adj, beta, mu, seed, patient_zero, max_steps=200, record_states=False):
    """Diskrete Zeit, S/I/R-Zustände. Wortgleiche Kopie aus `kas_algorithm.py`."""
    n = len(adj)
    beta = float(beta)
    mu = float(mu)
    patient_zero = int(patient_zero)
    if not (0 <= patient_zero < n):
        raise ValueError("patient_zero außerhalb des gültigen Knotenbereichs")
    rng = random.Random(int(seed) * 1_000_003 + 6421)
    state = [0] * n
    state[patient_zero] = 1
    trace = [(state.count(0), state.count(1), state.count(2))]
    states = [list(state)] if record_states else []
    steps_run = 0
    for _ in range(int(max_steps)):
        infected = [v for v in range(n) if state[v] == 1]
        if not infected:
            break
        newly_infected = set()
        for v in infected:
            for u in adj[v]:
                if state[u] == 0 and u not in newly_infected and rng.random() < beta:
                    newly_infected.add(u)
        newly_recovered = [v for v in infected if rng.random() < mu]
        for u in newly_infected:
            state[u] = 1
        for v in newly_recovered:
            state[v] = 2
        steps_run += 1
        trace.append((state.count(0), state.count(1), state.count(2)))
        assert trace[-1][0] + trace[-1][1] + trace[-1][2] == n
        if record_states:
            states.append(list(state))
    final_s, final_i, final_r = trace[-1]
    return SIRResult(trace, final_s, final_i, final_r, n - final_s, steps_run, states)


def sir_many_runs(adj, beta, mu, n_runs, seed, patient_zero, max_steps=200):
    """Endgröße über `n_runs` unabhängige stochastische Läufe. Wortgleiche Kopie aus `kas_algorithm.py`."""
    n_runs = int(n_runs)
    sizes = []
    for i in range(n_runs):
        run_seed = int(seed) * 1013 + i
        result = sir_simulate(adj, beta, mu, run_seed, patient_zero, max_steps)
        sizes.append(result.outbreak_size)
    sizes.sort()

    def percentile(p):
        if not sizes:
            return 0
        idx = min(len(sizes) - 1, max(0, int(round(p / 100 * (len(sizes) - 1)))))
        return sizes[idx]

    mean = sum(sizes) / len(sizes) if sizes else 0.0
    return {"mean": mean, "p10": percentile(10), "p50": percentile(50), "p90": percentile(90), "runs": sizes}


def epidemic_threshold_prediction(adj, mu):
    """β_c = μ·⟨k⟩/⟨k²⟩ (heterogene Mean-Field-Näherung, Pastor-Satorras & Vespignani 2001) - aus den GEMESSENEN Gradmomenten des konkreten Graphen. Gibt `None` zurück, wenn ⟨k²⟩=0. Wortgleiche
    Kopie aus `kas_algorithm.py`."""
    n = len(adj)
    if n == 0:
        return None
    degrees = [len(a) for a in adj]
    mean_k = sum(degrees) / n
    mean_k2 = sum(d * d for d in degrees) / n
    if mean_k2 <= 0:
        return None
    return float(mu) * mean_k / mean_k2


# --- Assortativität (wortgleiche Kopie aus sk_algorithm.py, Strukturkennzahlen-Demo, Stück 7) -------------------------------------------------------------


def _pearson(xs, ys):
    n = len(xs)
    if n == 0:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = sum((x - mx) ** 2 for x in xs)
    deny = sum((y - my) ** 2 for y in ys)
    den = math.sqrt(denx * deny)
    return num / den if den > 0.0 else float("nan")


def degree_assortativity(adj):
    """Pearson-Korrelation der Grade an beiden Enden jeder Kante (Newman 2002): jede Kante liefert BEIDE Richtungen (u,v) und (v,u). Assortativ (r>0): hochgradige Knoten hängen sich eher an
    hochgradige - die Signatur einer "Zwiebelstruktur" (Wu & Holme 2011). NaN bei konstantem Grad oder ohne Kante. Wortgleiche Kopie aus `sk_algorithm.py`."""
    n = len(adj)
    deg = [len(a) for a in adj]
    xs, ys = [], []
    for u in range(n):
        for v in adj[u]:
            if u < v:
                xs.append(deg[u])
                ys.append(deg[v])
                xs.append(deg[v])
                ys.append(deg[u])
    return _pearson(xs, ys)


# --- Härtung 1: Zufällig (NEU) ------------------------------------------------------------------------------------------------------------------------


def harden_random(adj, b, seed):
    """b neue Kanten zwischen zufälligen, noch nicht benachbarten Knotenpaaren (kein Selbstloop, keine Mehrfachkante) - die naive Referenzstrategie ohne jedes Strukturwissen. `b` wird auf die Zahl
    der tatsächlich fehlenden Kanten GEKAPPT (Sonderfall: b so groß wie der vollständige Graph). Gibt (neue Adjazenzliste, Liste der b hinzugefügten Kanten in Hinzufügereihenfolge, (u,v) mit
    u<v) zurück."""
    n = len(adj)
    nbrs = [set(a) for a in adj]
    b = max(0, int(b))
    max_possible = n * (n - 1) // 2 - sum(len(s) for s in nbrs) // 2
    b = min(b, max_possible)
    rng = random.Random(int(seed) * 1_000_003 + 4241)
    added = []
    max_attempts = max(10_000, n * n * 8)
    attempts = 0
    while len(added) < b and attempts < max_attempts:
        attempts += 1
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v or v in nbrs[u]:
            continue
        a, c = (u, v) if u < v else (v, u)
        nbrs[a].add(c)
        nbrs[c].add(a)
        added.append((a, c))
    new_adj = [sorted(s) for s in nbrs]
    return new_adj, added


# --- Härtung 2: Kritische-Kante-Bypass (NEU, Kanten-Betweenness aus Stück 6) --------------------------------------------------------------------------


LOAD_TOL = 1e-9                                         # relative Toleranz: Lasten, die sich nur um Gleitkomma-Rundung unterscheiden, sind GLEICH (symmetrische Kanten/Knoten)


def _ranked_by_load(items):
    """Kanten (oder Knoten) absteigend nach Last; Lasten, die bis auf `LOAD_TOL` (relativ) gleich sind, gelten als Gleichstand und werden nach Schlüssel aufsteigend geordnet. Ohne Toleranz entschieden
    Rundungsreste der Brandes-Summen (symmetrische Kanten haben mathematisch gleiche, als Gleitkommazahl aber verschiedene Lasten) statt des dokumentierten kleinsten Schlüssels."""
    items = sorted(items, key=lambda kv: (-kv[1], kv[0]))
    out = []
    i = 0
    while i < len(items):
        j = i
        top = items[i][1]
        while j + 1 < len(items) and top - items[j + 1][1] <= LOAD_TOL * max(1.0, abs(top)):
            j += 1
        out.extend(sorted(items[i:j + 1], key=lambda kv: kv[0]))
        i = j + 1
    return out


def harden_critical_bypass(adj, b):
    """b mal wiederholen: Kanten-Betweenness (Brandes) auf dem AKTUELLEN Graphen berechnen, die Kanten absteigend nach Last ordnen (Gleichstand: kleinster Kantenschlüssel). Für die am höchsten
    belastete Kante (u,v) mit u<v (Konvention: v ist der Endpunkt, an dem der Umweg ansetzt) einen Nachbarn w von v mit w≠u und (u,w) noch keine Kante wählen (kleinster Index bei Gleichstand),
    Kante (u,w) hinzufügen - ein Umweg, der den direkten Weg über die belastete Kante entlastet, OHNE sie selbst zu entfernen. Kein Kandidat verfügbar → nächstbelastete Kante versuchen; hat KEINE
    Kante mehr einen Kandidaten (z. B. vollständiger Graph), bricht die Härtung vorzeitig ab (Sonderfall: Kappung). Gibt (neue Adjazenzliste, Liste der tatsächlich hinzugefügten Kanten in
    Hinzufügereihenfolge) zurück."""
    nbrs = [set(a) for a in adj]
    added = []
    for _ in range(max(0, int(b))):
        cur_adj = [sorted(s) for s in nbrs]
        _, edge_between, _ = betweenness_brandes(cur_adj)
        if not edge_between:
            break
        ranked = _ranked_by_load(edge_between.items())
        placed = False
        for (u, v), _load in ranked:
            candidates = sorted(w for w in nbrs[v] if w != u and w not in nbrs[u])
            if candidates:
                w = candidates[0]
                nbrs[u].add(w)
                nbrs[w].add(u)
                added.append((min(u, w), max(u, w)))
                placed = True
                break
        if not placed:
            break
    new_adj = [sorted(s) for s in nbrs]
    return new_adj, added


# --- Härtung 3: Schneider u. a. 2011, Kanten-Doppeltausch als Hill-Climb (NEU) --------------------------------------------------------------------------


def _robustness_R_degree_adaptive(nbrs):
    """R (Schneider u. a. 2011) unter dem grad-adaptiven Angriff (Stück 8) - günstig genug, um bei jedem einzelnen Tauschversuch neu berechnet zu werden (KEINE teure Betweenness-Neuberechnung, im
    Gegensatz zum betweenness-adaptiven Angriff)."""
    n = len(nbrs)
    adj = [sorted(s) for s in nbrs]
    order = degree_order_adaptive(adj)
    sizes, _, _ = remove_sequence(adj, order)
    return robustness_index(sizes, n)


def harden_schneider(adj, n_trials, seed):
    """Kanten-Doppeltausch wie `configuration_null` (Maslov & Sneppen 2002, gradfolgen-erhaltend: zwei zufällige Kanten (a,b),(c,d) mit vier verschiedenen Knoten, Tausch zu (a,d),(c,b), verworfen
    falls das eine Mehrfachkante erzeugen würde), aber NICHT zufällig akzeptiert (Schneider, Moreira, Andrade, Herrmann & Havlin 2011, PNAS 108(10), 3838-3841): ein Tausch wird nur BEHALTEN, wenn
    er den Robustheitsindex R (grad-adaptiver Angriff, s. `_robustness_R_degree_adaptive`) gegenüber dem Zustand VOR genau diesem einen Versuch STRIKT verbessert - sonst wird er sofort exakt
    rückgängig gemacht (ein echter Hill-Climb, kein simuliertes Auskühlen - eine dokumentierte Vereinfachung, s. README "Grenzen"). `n_trials` ist die Zahl der VERSUCHE, nicht der Erfolge (wie bei
    `configuration_null`).

    Gibt (neue Adjazenzliste, Liste der akzeptierten Tausche in Reihenfolge [{"removed": [(a,b),(c,d)], "added": [(a,d) sortiert,(c,b) sortiert]}, ...], R-Verlauf [R vor dem ersten Versuch, R nach
    jedem AKZEPTIERTEN Tausch - EIN Eintrag mehr als akzeptierte Tausche]) zurück."""
    n = len(adj)
    nbrs = [set(a) for a in adj]
    edges = []
    for u in range(n):
        for v in adj[u]:
            if u < v:
                edges.append([u, v])
    rng = random.Random(int(seed) * 1_000_003 + 5303)
    current_R = _robustness_R_degree_adaptive(nbrs)
    accepted = []
    r_history = [current_R]
    m = len(edges)
    for _ in range(max(0, int(n_trials))):
        if m < 2:
            break
        i, j = rng.randrange(m), rng.randrange(m)
        if i == j:
            continue
        a, b = edges[i]
        c, d = edges[j]
        if len({a, b, c, d}) < 4:
            continue
        na, nb = (a, d) if a < d else (d, a)
        nc, nd = (c, b) if c < b else (b, c)
        if nb in nbrs[na] or nd in nbrs[nc]:
            continue                                            # würde eine Mehrfachkante erzeugen -- verwerfen, neu ziehen
        # Tausch probeweise durchführen
        nbrs[a].discard(b)
        nbrs[b].discard(a)
        nbrs[c].discard(d)
        nbrs[d].discard(c)
        nbrs[na].add(nb)
        nbrs[nb].add(na)
        nbrs[nc].add(nd)
        nbrs[nd].add(nc)
        new_R = _robustness_R_degree_adaptive(nbrs)
        if new_R > current_R:
            edges[i] = [na, nb]
            edges[j] = [nc, nd]
            accepted.append({"removed": [(min(a, b), max(a, b)), (min(c, d), max(c, d))], "added": [(min(na, nb), max(na, nb)), (min(nc, nd), max(nc, nd))]})
            current_R = new_R
            r_history.append(current_R)
        else:
            # exakt rückgängig machen - der Zustand vor diesem einen Versuch
            nbrs[na].discard(nb)
            nbrs[nb].discard(na)
            nbrs[nc].discard(nd)
            nbrs[nd].discard(nc)
            nbrs[a].add(b)
            nbrs[b].add(a)
            nbrs[c].add(d)
            nbrs[d].add(c)
    new_adj = [sorted(s) for s in nbrs]
    return new_adj, accepted, r_history
