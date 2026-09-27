"""Kritische Knoten härten – Zusammenfluss von Zentralität, Robustheit, Kaskaden/Ausbreitung – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zehntes Stück der Graphen-und-Netzwerke-Reihe: bisher wurde nur GEMESSEN, wie verwundbar ein Netz ist (Stück 6 Zentralität, 8 Robustheit, 9 Kaskaden/Ausbreitung) - jetzt geht es darum, mit einem
begrenzten Härtungsbudget B (zusätzliche Kanten) oder einem Trainingsaufwand (Versuche) etwas dagegen zu tun. Drei Strategien: Zufällig, Kritische-Kante-Bypass (Kanten-Betweenness aus Stück 6) und
Schneider u. a. 2011 (Kanten-Doppeltausch als Hill-Climb gegen den Robustheitsindex R aus Stück 8).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import haer_algorithm as A
import haer_constants as C
import haer_evaluation as ev
import haer_visualization as viz
from haer_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, store_from_widget, sync_query_params, push_to_widget

st.set_page_config(page_title="Kritische Knoten härten – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analyse(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _budget_sweep(settings):
    return ev.budget_sweep(settings)


@st.cache_data(show_spinner=False)
def _strategy_comparison(settings):
    return ev.strategy_comparison(settings)


@st.cache_data(show_spinner=False)
def _onion_check(settings):
    return ev.onion_check(settings)


def _german(x):
    return f"{x:,}".replace(",", ".") if isinstance(x, int) else x


def _fmt_alpha(a):
    return f"{a:.2f}" if a is not None else "n/a"


st.title("🔧 Kritische Knoten härten")
st.markdown(
    """
**Zehntes Stück der Graphen-und-Netzwerke-Reihe**, ein Zusammenfluss aus Zentralität (Stück 6), Robustheit (Stück 8) und Kaskaden/Ausbreitung (Stück 9): bisher wurde nur GEMESSEN, wie
verwundbar ein Netz ist - jetzt geht es darum, mit einem begrenzten Härtungsbudget B (zusätzliche Kanten) etwas dagegen zu tun. Drei Strategien: **Zufällig** (B zufällige neue Kanten),
**Kritische-Kante-Bypass** (wiederholt die aktuell am stärksten belastete Kante finden und einen Umweg drumherum bauen) und **Schneider u. a. 2011** (Kanten-Doppeltausch, aber nur akzeptiert,
wenn er den Robustheitsindex R verbessert - ein gradfolgen-erhaltender Hill-Climb, PNAS 108(10), 3838-3841). Gemessen wird die Verbesserung in R, kritischer Toleranz α\\* und Epidemieschwelle
β_c - UND, als Zusatzbefund, ob Schneiders Optimierung eine "Zwiebelstruktur" erzeugt (Wu & Holme 2011, Phys. Rev. E 84, 026106).
"""
)
st.caption(
    "Kind der Zentralität-, Robustheits- und Kaskaden-Demo (Stücke 6, 8, 9 der Graphen-und-Netzwerke-Reihe). Der Barbell zeigt den dramatischsten Lehrbuchfall: schon EINE Bypass-Kante um die "
    "Brücke herum beseitigt den Single Point of Failure vollständig (Schritt 4)."
)

with st.expander("So funktioniert die Messung", expanded=True):
    st.markdown(
        """
1. **Zufällig** (`harden_random`): B neue Kanten zwischen zufälligen, noch nicht benachbarten Knotenpaaren - die naive Referenz ohne jedes Strukturwissen.
2. **Kritische-Kante-Bypass** (`harden_critical_bypass`): B mal wiederholen - die aktuell am stärksten belastete Kante (Kanten-Betweenness, Brandes) finden und einen Umweg über einen Nachbarn
   hinzufügen, der sie entlastet, ohne sie zu entfernen.
3. **Schneider u. a. 2011** (`harden_schneider`, PNAS 108(10), 3838-3841): ein Kanten-Doppeltausch wie das Konfigurationsmodell (Stück 7), aber NUR akzeptiert, wenn er den Robustheitsindex R
   (Stück 8, unter gezieltem Grad-Angriff) gegenüber dem Zustand vor genau diesem einen Versuch strikt verbessert - ein echter Hill-Climb, gradfolgen-erhaltend.
4. **Gemessen:** R (Schneider u. a. 2011), kritische Toleranz α\\* der Motter-Lai-Kaskade (Stück 9), Epidemieschwelle β_c (Stück 9) - jeweils vor/nach der Härtung - und die Grad-Assortativität
   (Stück 7) vor/nach Schneiders Härtung als Zwiebelstruktur-Indiz (Wu & Holme 2011).
5. **Leserichtung:** höheres R = robuster. NIEDRIGERES α\\* = robuster (weniger Sicherheitsspielraum nötig, um einen Kaskadenausbruch zu vermeiden). HÖHERES β_c = robuster (eine Epidemie braucht
   eine größere Ansteckungswahrscheinlichkeit, um sich auszubreiten). Härtung soll also R und β_c anheben, α\\* dagegen senken.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    rows_of_4 = [preset_names[i:i + 4] for i in range(0, len(preset_names), 4)]
    for row in rows_of_4:
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()
ss = st.session_state

with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                     help="Betriebsnetz: gestörtes Straßenraster oder Zufallsgraph. Skalenfreies Netz: Barabási-Albert, bevorzugte Anbindung. Barbell: Lehrbuchbeispiel, von Hand nachrechenbar.")

    side, blocked, nettype = C.DEFAULT_SIDE, C.DEFAULT_BLOCKED, "grid"
    n_ba, m_ba, m0_ba = C.DEFAULT_N_BA, C.DEFAULT_M_BA, C.DEFAULT_M0_BA
    k_barbell = C.DEFAULT_BARBELL_K

    if kind == "city":
        side = st.slider("Seitenlänge des Rasters", *bounds("side_slider"), value=int(ss["side_slider"]), key="side_widget", on_change=store_from_widget, args=("side_slider",),
                          help="Die Instanz hat Seitenlänge² Kreuzungen.")
        nettype = st.radio("Netztyp", options=list(C.NETTYPES), format_func=lambda v: C.NETTYPE_LABELS[v], key="nettype_widget", on_change=store_from_widget, args=("nettype_select",),
                            index=list(C.NETTYPES).index(ss["nettype_select"]))
        if nettype == "grid":
            blocked = st.select_slider("Gesperrter Anteil der Straßen", options=list(C.BLOCKED_OPTIONS), value=float(ss["blocked_select"]), format_func=lambda v: f"{v * 100:.0f} %",
                                        key="blocked_widget", on_change=store_from_widget, args=("blocked_select",))
        else:
            blocked = 0.0
    elif kind == "ba":
        n_ba = st.slider("Zahl der Knoten n", *bounds("nba_slider"), value=int(ss["nba_slider"]), key="nba_widget", on_change=store_from_widget, args=("nba_slider",))
        m0_ba = st.slider("Kerngröße m0 (Kreis aus m0 Knoten)", *bounds("m0ba_slider"), value=int(ss["m0ba_slider"]), key="m0ba_widget", on_change=store_from_widget, args=("m0ba_slider",))
        if ss["mba_slider"] > m0_ba:
            ss["mba_slider"] = m0_ba
            push_to_widget("mba_slider")
        if C.M_BA_MIN < m0_ba:
            m_ba = st.slider("Neue Kanten je Knoten m (bevorzugte Anbindung)", C.M_BA_MIN, m0_ba, value=int(ss["mba_slider"]), key="mba_widget", on_change=store_from_widget, args=("mba_slider",))
        else:
            m_ba = C.M_BA_MIN                                        # m0 == M_BA_MIN: keine Wahl möglich (min==max würde den Regler zum Absturz bringen)
    else:
        k_barbell = st.slider("Cliquengröße k (Barbell hat 2k Knoten)", *bounds("kbarbell_slider"), value=int(ss["kbarbell_slider"]), key="kbarbell_widget", on_change=store_from_widget,
                               args=("kbarbell_slider",), help="Zwei vollständige Graphen K_k, durch eine einzelne Brücke verbunden.")

    st.markdown("---")
    strategy = st.radio("Härtungsstrategie", options=list(C.STRATEGIES), format_func=lambda v: C.STRATEGY_LABELS[v], key="strategy_select",
                         help="Zufällig: naive Referenz. Kritische-Kante-Bypass: gezielt gegen die höchstbelastete Kante. Schneider: gradfolgen-erhaltender Hill-Climb gegen R.")

    if strategy != "schneider":
        budget = st.slider("Budget B (neue Kanten)", *bounds("budget_slider"), value=int(ss["budget_slider"]), key="budget_widget", on_change=store_from_widget, args=("budget_slider",),
                            help="Zahl der neu hinzugefügten Kanten.")
        n_trials = int(ss["ntrials_slider"])
    else:
        budget = int(ss["budget_slider"])
        n_trials = st.slider("Versuche n_trials (Schneider-Hill-Climb)", *bounds("ntrials_slider"), value=int(ss["ntrials_slider"]), key="ntrials_widget", on_change=store_from_widget,
                              args=("ntrials_slider",), help="Zahl der Tauschversuche - nicht der Erfolge. Größere Instanzen/mehr Versuche können einige Sekunden dauern.")

    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

step = st.select_slider("Schritt", options=list(C.STEPS), key="haer_step", format_func=lambda s: C.STEPS[s])

sync_query_params({"kind_select": kind, "side_slider": int(side) if kind == "city" else int(ss["side_slider"]),
                    "blocked_select": float(blocked) if kind == "city" and nettype == "grid" else float(ss["blocked_select"]), "nettype_select": nettype if kind == "city" else ss["nettype_select"],
                    "nba_slider": int(n_ba) if kind == "ba" else int(ss["nba_slider"]), "m0ba_slider": int(m0_ba) if kind == "ba" else int(ss["m0ba_slider"]),
                    "mba_slider": int(m_ba) if kind == "ba" else int(ss["mba_slider"]), "kbarbell_slider": int(k_barbell) if kind == "barbell" else int(ss["kbarbell_slider"]),
                    "strategy_select": strategy, "budget_slider": int(budget), "ntrials_slider": int(n_trials), "seed_input": int(seed), "haer_step": int(step)})

base_settings = dict(kind=kind, side=int(side), blocked=float(blocked), nettype=nettype, n_ba=int(n_ba), m_ba=int(m_ba), m0_ba=int(m0_ba), k_barbell=int(k_barbell), strategy=strategy,
                      budget=int(budget), n_trials=int(n_trials), seed=int(seed))
settings = ev.Settings(**base_settings)

with st.spinner("Härte das Netz..."):
    inst, new_adj, analysis = _analyse(settings)
adj = A.adjacency(inst.n, inst.edges)

st.markdown("## 🎯 Die Instanz und ihre Härtung")
st.markdown(f"**{_german(inst.n)} Knoten, {_german(inst.m)} Kanten**, Strategie **{C.STRATEGY_LABELS[strategy]}**. R: **{analysis.R_before:.3f} → {analysis.R_after:.3f}** "
            f"({analysis.R_after - analysis.R_before:+.3f}). α\\*: **{_fmt_alpha(analysis.alpha_before)} → {_fmt_alpha(analysis.alpha_after)}**. "
            f"β_c: **{analysis.beta_c_before:.4f} → {analysis.beta_c_after:.4f}**.")

if step == 1:
    n_steps = len(analysis.steps)
    if n_steps > 0:
        k = st.slider("Härtungsschritt", 0, n_steps, value=n_steps, key=f"k_slider_{kind}_{seed}_{strategy}_{budget}_{n_trials}",
                       help="0 = Ausgangsnetz, Maximum = vollständig gehärtetes Netz.")
    else:
        k = 0
        st.info("Bei dieser Einstellung wurde keine einzige Kante hinzugefügt/getauscht (z. B. Budget=0 oder kein Kandidat verfügbar).")
    base_edges = [(u, v) for u, v, _ in inst.edges]
    st.plotly_chart(viz.build_hardening_map(inst.xy, base_edges, analysis.steps, k), width="stretch",
                     key=f"s1_map_{kind}_{seed}_{strategy}_{budget}_{n_trials}_{k}")
    st.caption(f"Nach {k} von {n_steps} Härtungsschritten (Strategie: {C.STRATEGY_LABELS[strategy]}).")
    if strategy == "schneider" and analysis.r_history:
        st.plotly_chart(viz.build_r_history(analysis.r_history), width="stretch", key=f"s1_rhist_{kind}_{seed}_{n_trials}")
elif step == 2:
    with st.spinner("Rechne Budget-Sweep für alle drei Strategien (kann einige Sekunden dauern)..."):
        sweep_inst, rows, baseline = _budget_sweep(settings)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(viz.build_r_sweep(rows, baseline["R"]), width="stretch", key=f"s2_r_{kind}_{seed}_{side}_{blocked}_{nettype}_{n_ba}_{m_ba}_{m0_ba}_{k_barbell}")
    with c2:
        st.plotly_chart(viz.build_alpha_sweep(rows, baseline["alpha"]), width="stretch", key=f"s2_alpha_{kind}_{seed}_{side}_{blocked}_{nettype}_{n_ba}_{m_ba}_{m0_ba}_{k_barbell}")
    with c3:
        st.plotly_chart(viz.build_beta_sweep(rows, baseline["beta_c"]), width="stretch", key=f"s2_beta_{kind}_{seed}_{side}_{blocked}_{nettype}_{n_ba}_{m_ba}_{m0_ba}_{k_barbell}")
    st.caption("Schneiders Budget-Ebene wird intern in eine Versuchszahl übersetzt (kein Kantenzuwachs bei Schneider, s. „So funktioniert die Messung“/README) - eine grobe, aber "
               "nachvollziehbare Vergleichsbasis, keine exakte Kostenäquivalenz.")
elif step == 3:
    with st.spinner("Vergleiche alle drei Strategien..."):
        cmp_inst, rows, baseline = _strategy_comparison(settings)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(viz.build_strategy_comparison_bars(rows, "R", baseline["R"], "Robustheitsindex R", "R"), width="stretch", key=f"s3_r_{kind}_{seed}_{budget}_{n_trials}")
    with c2:
        st.plotly_chart(viz.build_strategy_comparison_bars(rows, "alpha", baseline["alpha"], "Kritische Toleranz α*", "α*"), width="stretch", key=f"s3_alpha_{kind}_{seed}_{budget}_{n_trials}")
    with c3:
        st.plotly_chart(viz.build_strategy_comparison_bars(rows, "beta_c", baseline["beta_c"], "Epidemieschwelle β_c", "β_c"), width="stretch", key=f"s3_beta_{kind}_{seed}_{budget}_{n_trials}")
    st.dataframe([{"Strategie": C.STRATEGY_LABELS[r["strategy"]], "R": round(r["R"], 4), "α*": r["alpha"], "β_c": round(r["beta_c"], 4) if r["beta_c"] is not None else None,
                   "Assortativität": round(r["assortativity"], 4) if r["assortativity"] == r["assortativity"] else None, "neue Kanten": r["n_added"], "getauschte Kanten": r["n_swapped"]}
                  for r in rows], width="stretch", hide_index=True)
    best_R = max(rows, key=lambda r: r["R"])
    st.caption(f"Bei Budget B={budget} (Schneider: n_trials={n_trials}) verbessert **{C.STRATEGY_LABELS[best_R['strategy']]}** R am meisten "
               f"({best_R['R']:.3f} gegen {baseline['R']:.3f} vorher).")
else:
    with st.spinner("Prüfe die Zwiebelstruktur-Hypothese (Schneider-Härtung)..."):
        onion_inst, onion_adj, check = _onion_check(settings)
    st.plotly_chart(viz.build_onion_bars(check.assort_before, check.assort_after), width="stretch", key=f"s4_onion_{kind}_{seed}_{n_trials}")
    st.caption(f"Schneider-Härtung ({check.n_accepted} von {check.n_trials} Versuchen akzeptiert): Assortativität {check.assort_before:.3f} → {check.assort_after:.3f} "
               f"({check.assort_after - check.assort_before:+.3f}). R: {check.R_before:.3f} → {check.R_after:.3f}.")
    st.markdown("---")
    r_before = A.low_link(adj)
    r_after = A.low_link(new_adj)
    b1, b2 = st.columns(2)
    b1.metric("Brücken vorher", len(r_before.bridges))
    b2.metric(f"Brücken nachher ({C.STRATEGY_LABELS[strategy]})", len(r_after.bridges))
    if kind == "barbell":
        if strategy == "bypass" and budget >= 1:
            st.success("Barbell + Kritische-Kante-Bypass mit B≥1: die Brücke ist vollständig beseitigt (0 Brücken) - der Single Point of Failure existiert nicht mehr.")
        else:
            st.caption("Für die Barbell-Bypass-Demonstration: Instanz „Barbell-Lehrbuch“, Strategie „Kritische-Kante-Bypass“, Budget ≥ 1 wählen (s. Preset „Barbell-Bypass“).")

st.markdown("---")

st.markdown("## 🎯 Was die Härtung bringt")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Knoten", _german(inst.n))
r2.metric("Kanten", _german(inst.m))
r3.metric("R vorher → nachher", f"{analysis.R_before:.3f} → {analysis.R_after:.3f}")
r4.metric("α* vorher → nachher", f"{_fmt_alpha(analysis.alpha_before)} → {_fmt_alpha(analysis.alpha_after)}")

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Schneiders Hill-Climb ist ein echter Hill-Climb, kein simuliertes Auskühlen** | Bleibt in einem lokalen Optimum stecken - ein Tausch, der KURZFRISTIG R senkt, aber langfristig einen besseren Zustand freischalten würde, wird nie akzeptiert. | - |
| **R (Grad-adaptiver Angriff) und α\\*/β_c (Betweenness- bzw. Gradmoment-basiert) messen UNTERSCHIEDLICHE Angriffsmodelle** | Eine Strategie, die R verbessert, verbessert α\\*/β_c nicht zwangsläufig mit (gemessen, s. README "Befunde") - die drei Kennzahlen können sich sogar gegenläufig entwickeln. | - |
| **Kritische-Kante-Bypass entfernt die belastete Kante NICHT, sondern baut nur einen Umweg** | Auf Netzen ohne nahe Nachbarn (dichte, kleine Instanzen) kann kein Kandidat mehr gefunden werden - die Härtung bricht dann vor Erreichen des Budgets ab (Sonderfall, s. Tests). | - |
| **"Budget" ist bei Schneider kein Kantenzuwachs** | Die gemeinsame Budget-Achse in Schritt 2 ist für Schneider eine grobe Übersetzung in eine Versuchszahl, keine exakte Kostenäquivalenz (s. Design-Entscheidung README). | - |
| **Synthetische Instanzen** | Betriebsnetz, skalenfreies Netz und Barbell sind erzeugt, keine echten Infrastrukturdaten. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Zufällige Härtung.** B neue Kanten zwischen zufälligen, noch nicht benachbarten Knotenpaaren.

**Kritische-Kante-Bypass.** B mal wiederholen: Kanten-Betweenness (Brandes 2001) auf dem aktuellen Graphen berechnen, die am höchsten belastete Kante $(u,v)$ finden, einen Nachbarn $w$ von $v$
mit $w\neq u$ und $(u,w)\notin E$ wählen, Kante $(u,w)$ hinzufügen.

**Schneider u. a. 2011 (PNAS 108(10), 3838-3841).** Kanten-Doppeltausch wie das Konfigurationsmodell (zwei zufällige Kanten $(a,b),(c,d)$ mit vier verschiedenen Knoten, Tausch zu $(a,d),(c,b)$,
verworfen bei drohender Mehrfachkante), aber nur akzeptiert, wenn der Robustheitsindex $R$ danach STRIKT größer ist als davor:

$$R = \frac{1}{n}\sum_{k=1}^{n} \frac{S(k)}{n}$$

mit $S(k)$ = Größe der größten Komponente nach $k$ Entfernungen unter dem grad-adaptiven Angriff (Cohen u. a. 2001). Abgelehnte Tausche werden exakt rückgängig gemacht.

**Kritische Toleranz $\alpha^*$ (Motter & Lai 2002).** Kleinstes $\alpha$, ab dem der Ausfall des höchstbelasteten Knotens KEINE Sekundärausfälle mehr auslöst (Kapazität $=(1+\alpha)\cdot$
Anfangslast).

**Epidemieschwelle $\beta_c=\mu\langle k\rangle/\langle k^2\rangle$ (Pastor-Satorras & Vespignani 2001).** Aus den gemessenen Gradmomenten des GEHÄRTETEN Graphen - Härtung ändert die
Gradverteilung (außer bei Schneider, der sie exakt erhält) und damit $\beta_c$ in eine Richtung, die von der Instanz abhängt (nicht vorausgesetzt).

**Zwiebelstruktur (Wu & Holme 2011, Phys. Rev. E 84, 026106).** Hypothese: robuste Netze haben eine radial nach außen abnehmende Gradstruktur mit überproportional vielen Kanten innerhalb
derselben Schicht - hier über die Grad-Assortativität (Newman 2002) vor/nach Schneiders Härtung gemessen.

**Literatur.** Schneider, C. M., Moreira, A. A., Andrade, J. S., Herrmann, H. J., & Havlin, S. (2011). *Mitigation of malicious attacks on networks.* PNAS 108(10), 3838–3841. Wu, Z.-X., & Holme,
P. (2011). *Onion structure and network robustness.* Physical Review E 84, 026106. Brandes, U. (2001). *A faster algorithm for betweenness centrality.* Journal of Mathematical Sociology 25(2),
163–177. Motter, A. E., & Lai, Y.-C. (2002). *Cascade-based attacks on complex networks.* Physical Review E 66, 065102(R). Pastor-Satorras, R., & Vespignani, A. (2001). *Epidemic spreading in
scale-free networks.* Physical Review Letters 86(14), 3200–3203.

Implementiert in `haer_algorithm.py` (Härtungsstrategien, geerbte Bausteine), `haer_scenario.py` (Instanzen), `haer_evaluation.py` (Analyse, Sweeps, Vergleich, Zwiebelstruktur-Check).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
