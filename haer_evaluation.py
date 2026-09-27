"""Auswertung: Härtung einer einzelnen Instanz mit der gewählten Strategie (R/α*/β_c/Assortativität vor/nach), Budget-Sweep über alle drei Strategien (Schritt 2), Strategienvergleich bei festem
Budget (Schritt 3), Zwiebelstruktur-Check für Schneider (Schritt 4).

**Design-Entscheidung "Budget" bei Schneider:** Zufällig/Bypass verbrauchen ihr Budget B direkt als Zahl NEUER Kanten. Schneiders Kanten-Doppeltausch fügt dagegen NIE neue Kanten hinzu (die
Gradfolge bleibt exakt erhalten) - "B neue Kanten" ist für diese Strategie bedeutungslos. Um dennoch eine gemeinsame Aufwands-Achse für den Drei-Strategien-Vergleich (Schritt 2) zu haben, wird B
für Schneider stattdessen in eine Versuchszahl übersetzt (`n_trials = B * SCHNEIDER_TRIALS_PER_LEVEL`, kalibriert in der Vormessung) - eine grobe, aber nachvollziehbare "Aufwand"-Vergleichsbasis,
KEINE exakte Kostenäquivalenz (in der Einzel-Instanz-Analyse, Schritt 1, wählt der Nutzer die Versuchszahl für Schneider dagegen direkt über einen eigenen Regler, B wird dort ausgeblendet -
Hauskonvention gegen tote Regler, s. app.py)."""

from dataclasses import dataclass

import haer_algorithm as A
import haer_constants as C
import haer_scenario as S


@dataclass
class Settings:
    kind: str = "city"                   # "city" | "ba" | "barbell"
    # Betriebsnetz
    side: int = C.DEFAULT_SIDE
    blocked: float = C.DEFAULT_BLOCKED
    nettype: str = "grid"                # "grid" | "random"
    # Skalenfreies Netz
    n_ba: int = C.DEFAULT_N_BA
    m_ba: int = C.DEFAULT_M_BA
    m0_ba: int = C.DEFAULT_M0_BA
    # Barbell-Lehrbuch
    k_barbell: int = C.DEFAULT_BARBELL_K
    # Härtung
    strategy: str = "random"             # "random" | "bypass" | "schneider"
    budget: int = C.DEFAULT_BUDGET
    n_trials: int = C.DEFAULT_N_TRIALS
    # gemeinsam
    seed: int = C.DEFAULT_SEED


def instance(settings):
    if settings.kind == "city":
        return S.generate(settings.side, settings.blocked, settings.nettype, settings.seed)
    if settings.kind == "ba":
        return S.barabasi_albert_instance(settings.n_ba, settings.m_ba, settings.m0_ba, settings.seed)
    if settings.kind == "barbell":
        return S.barbell_instance(settings.k_barbell)
    raise ValueError(f"unbekannte Instanzart {settings.kind}")


def highest_load_node(adj):
    """Der Knoten mit der höchsten Betweenness (Motter & Lai: der Ausfall, der am ehesten eine Kaskade auslöst) - stets auf dem GEGEBENEN Graphen neu bestimmt (vor der Härtung: der ursprüngliche
    Hub; nach der Härtung: der dann höchstbelastete Knoten, der sich durch die Härtung verschoben haben kann)."""
    n = len(adj)
    node_between, _, _ = A.betweenness_brandes(adj)
    return max(range(n), key=lambda v: (node_between[v], -v))


def robustness_R(adj):
    """R (Schneider u. a. 2011) unter dem grad-adaptiven Angriff (Stück 8) - dieselbe Definition, mit der `harden_schneider` intern jeden Tauschversuch bewertet."""
    order = A.degree_order_adaptive(adj)
    sizes, _, _ = A.remove_sequence(adj, order)
    return A.robustness_index(sizes, len(adj))


def critical_alpha(adj, alphas=C.ALPHA_SWEEP):
    return A.critical_tolerance(adj, [highest_load_node(adj)], alphas)


def apply_strategy(adj, strategy, budget, n_trials, seed):
    """Wendet eine der drei Härtungsstrategien an. Gibt (neue Adjazenzliste, hinzugefügte Kanten in Reihenfolge [flach], entfernte Kanten in Reihenfolge [nur Schneider, flach], R-Verlauf [nur
    Schneider, sonst None], Schritte [{"added": [...], "removed": [...]}, ...] - EIN Eintrag je Härtungsschritt, für die "Härtung in Aktion"-Karte: bei Zufällig/Bypass je eine hinzugefügte Kante
    pro Schritt, bei Schneider die zwei hinzugefügten UND zwei entfernten Kanten je AKZEPTIERTEM Tauschversuch) zurück."""
    if strategy == "random":
        new_adj, added = A.harden_random(adj, budget, seed)
        return new_adj, added, [], None, [{"added": [e], "removed": []} for e in added]
    if strategy == "bypass":
        new_adj, added = A.harden_critical_bypass(adj, budget)
        return new_adj, added, [], None, [{"added": [e], "removed": []} for e in added]
    if strategy == "schneider":
        new_adj, accepted, r_history = A.harden_schneider(adj, n_trials, seed)
        added = [pair for step in accepted for pair in step["added"]]
        removed = [pair for step in accepted for pair in step["removed"]]
        steps = [{"added": step["added"], "removed": step["removed"]} for step in accepted]
        return new_adj, added, removed, r_history, steps
    raise ValueError(f"unbekannte Härtungsstrategie {strategy}")


def _effort_to_schneider_trials(effort):
    return max(1, int(round(effort * C.SCHNEIDER_TRIALS_PER_LEVEL)))


# --- Schritt 1: Härtung einer einzelnen Instanz mit einer Strategie -------------------------------------------------------------------------------------


@dataclass
class Analysis:
    n: int
    m: int
    strategy: str
    budget: int
    n_trials: int
    R_before: float
    R_after: float
    alpha_before: object
    alpha_after: object
    beta_c_before: float
    beta_c_after: float
    assort_before: float
    assort_after: float
    added_edges: list
    removed_edges: list
    r_history: object              # nur Schneider
    steps: list                    # fuer die "Haertung in Aktion"-Karte, s. apply_strategy


def analyse(settings):
    inst = instance(settings)
    adj = A.adjacency(inst.n, inst.edges)
    new_adj, added, removed, r_history, steps = apply_strategy(adj, settings.strategy, settings.budget, settings.n_trials, settings.seed)
    R_before, R_after = robustness_R(adj), robustness_R(new_adj)
    alpha_before, alpha_after = critical_alpha(adj), critical_alpha(new_adj)
    beta_before = A.epidemic_threshold_prediction(adj, C.MU_FOR_BETA_C)
    beta_after = A.epidemic_threshold_prediction(new_adj, C.MU_FOR_BETA_C)
    assort_before, assort_after = A.degree_assortativity(adj), A.degree_assortativity(new_adj)
    analysis = Analysis(inst.n, inst.m, settings.strategy, int(settings.budget), int(settings.n_trials), R_before, R_after, alpha_before, alpha_after, beta_before, beta_after, assort_before,
                         assort_after, added, removed, r_history, steps)
    return inst, new_adj, analysis


# --- Schritt 2: R/alpha*/beta_c ueber das Budget, alle drei Strategien ueberlagert ------------------------------------------------------------------------


def budget_sweep(settings, budgets=C.BUDGET_SWEEP):
    """Für jede der drei Strategien: R, α*, β_c NACH der Härtung bei jedem Budget-Wert in `budgets` (Schneider übersetzt denselben Wert über `_effort_to_schneider_trials`, s. Modul-Docstring).
    `settings.seed` bestimmt sowohl die Instanz als auch alle stochastischen Härtungsschritte (Zufällig/Schneider) - eine EINZIGE Instanz für den gesamten Sweep."""
    inst = instance(settings)
    adj = A.adjacency(inst.n, inst.edges)
    R0 = robustness_R(adj)
    alpha0 = critical_alpha(adj, C.ALPHA_SWEEP_COARSE)
    beta0 = A.epidemic_threshold_prediction(adj, C.MU_FOR_BETA_C)
    rows = []
    for strategy in C.STRATEGIES:
        for b in budgets:
            if strategy == "schneider":
                new_adj, _added, _removed, _rh, _steps = apply_strategy(adj, strategy, 0, _effort_to_schneider_trials(b), settings.seed)
            else:
                new_adj, _added, _removed, _rh, _steps = apply_strategy(adj, strategy, b, 0, settings.seed)
            rows.append({"strategy": strategy, "budget": b, "R": robustness_R(new_adj), "alpha": critical_alpha(new_adj, C.ALPHA_SWEEP_COARSE),
                         "beta_c": A.epidemic_threshold_prediction(new_adj, C.MU_FOR_BETA_C)})
    return inst, rows, {"R": R0, "alpha": alpha0, "beta_c": beta0}


# --- Schritt 3: Strategien im direkten Vergleich bei festem Budget ------------------------------------------------------------------------------------


def strategy_comparison(settings):
    """Alle drei Strategien bei GENAU dem Budget/n_trials aus `settings` (Schneider verwendet dabei `settings.n_trials` direkt - NICHT die Budget-Übersetzung aus `budget_sweep`, da hier der Nutzer
    die Versuchszahl selbst über den Regler wählt, s. app.py)."""
    inst = instance(settings)
    adj = A.adjacency(inst.n, inst.edges)
    R0 = robustness_R(adj)
    alpha0 = critical_alpha(adj, C.ALPHA_SWEEP_COARSE)
    beta0 = A.epidemic_threshold_prediction(adj, C.MU_FOR_BETA_C)
    assort0 = A.degree_assortativity(adj)
    rows = []
    for strategy in C.STRATEGIES:
        new_adj, added, removed, r_history, _steps = apply_strategy(adj, strategy, settings.budget, settings.n_trials, settings.seed)
        rows.append({"strategy": strategy, "R": robustness_R(new_adj), "alpha": critical_alpha(new_adj, C.ALPHA_SWEEP_COARSE), "beta_c": A.epidemic_threshold_prediction(new_adj, C.MU_FOR_BETA_C),
                     "assortativity": A.degree_assortativity(new_adj), "n_added": len(added), "n_swapped": len(removed)})
    return inst, rows, {"R": R0, "alpha": alpha0, "beta_c": beta0, "assortativity": assort0}


# --- Schritt 4: Zwiebelstruktur-Check (Wu & Holme 2011) -----------------------------------------------------------------------------------------------


@dataclass
class OnionCheck:
    n: int
    m: int
    n_trials: int
    n_accepted: int
    assort_before: float
    assort_after: float
    R_before: float
    R_after: float


def onion_check(settings):
    """Assortativität vor/nach der Schneider-Härtung (unabhängig von `settings.strategy` - dieser Check ist SPEZIFISCH für Schneider, s. PLAN Punkt 6): steigt sie, ist das ein empirisches Indiz für
    die "Zwiebelstruktur" (Wu & Holme 2011, Phys. Rev. E 84, 026106) - GEMESSEN, nicht angenommen."""
    inst = instance(settings)
    adj = A.adjacency(inst.n, inst.edges)
    new_adj, accepted, r_history = A.harden_schneider(adj, settings.n_trials, settings.seed)
    assort_before, assort_after = A.degree_assortativity(adj), A.degree_assortativity(new_adj)
    R_before, R_after = (r_history[0], r_history[-1]) if r_history else (robustness_R(adj), robustness_R(new_adj))
    return inst, new_adj, OnionCheck(inst.n, inst.m, int(settings.n_trials), len(accepted), assort_before, assort_after, R_before, R_after)
