"""Plotly-Figuren: Karte für "Härtung in Aktion" (hinzugefügte/getauschte Kanten farbig hervorgehoben, mit Schieberegler über die Härtungsschritte), R/α*/β_c über das Budget (drei Strategien
überlagert je Kennzahl), Strategien im direkten Vergleich (Balken bei festem Budget), Zwiebelstruktur-Check (Assortativität vor/nach Schneider). Alle Achsen fest (fixedrange), Karten nutzen
`scaleanchor` mit autorange und zwei unsichtbaren Eckpunkten (Hauskonvention). Jede Referenzlinie (`add_hline`/`add_vline`) bekommt `annotation=dict(bgcolor="white")` - Pflicht-Checkliste dieser
Reihe (schon zweimal als Bug gefunden, s. robustheit-demo/kaskaden-demo)."""

import plotly.graph_objects as go

TEAL, ORANGE, BLUE, RED, PURPLE, GREY, LIGHT, GREEN = "#2F6B65", "#f58518", "#4c78a8", "#e45756", "#7b3fbf", "#b7bec7", "#e8ebee", "#54a24b"
STRATEGY_COLORS = {"random": GREY, "bypass": ORANGE, "schneider": TEAL}


def _lines(xy, pairs):
    xs, ys = [], []
    for u, v in pairs:
        xs += [xy[u][0], xy[v][0], None]
        ys += [xy[u][1], xy[v][1], None]
    return xs, ys


def _corners_trace(xy):
    pad = 0.4
    return go.Scatter(x=[xy[:, 0].min() - pad, xy[:, 0].max() + pad], y=[xy[:, 1].min() - pad, xy[:, 1].max() + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False)


# --- 1 · Härtung in Aktion ------------------------------------------------------------------------------------------------------------------------------


def build_hardening_map(xy, base_edges, steps, k):
    """Karte nach den ersten `k` Härtungsschritten: ursprüngliche (noch bestehende) Kanten dünn grau, in diesen `k` Schritten HINZUGEFÜGTE Kanten TEAL (dick), bei Schneider zusätzlich die dabei
    ENTFERNTEN Kanten gestrichelt hellgrau (nur die, die bis Schritt k schon wieder verschwunden sind). `steps`: Liste von {"added": [...], "removed": [...]} (s. `haer_evaluation.apply_strategy`)."""
    added_so_far, removed_so_far = [], []
    for step in steps[:k]:
        added_so_far += step["added"]
        removed_so_far += step["removed"]
    removed_set = set(removed_so_far)
    remaining_base = [(u, v) for u, v in base_edges if (u, v) not in removed_set]

    fig = go.Figure()
    bx, by = _lines(xy, remaining_base)
    fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=GREY, width=1.0), opacity=0.55, hoverinfo="skip", showlegend=False, name="Bestehende Kanten"))
    if removed_so_far:
        rx, ry = _lines(xy, removed_so_far)
        fig.add_trace(go.Scatter(x=rx, y=ry, mode="lines", line=dict(color=LIGHT, width=1.6, dash="dot"), hoverinfo="skip", showlegend=True, name=f"Entfernt ({len(removed_so_far)})"))
    if added_so_far:
        ax, ay = _lines(xy, added_so_far)
        fig.add_trace(go.Scatter(x=ax, y=ay, mode="lines", line=dict(color=TEAL, width=3.0), hoverinfo="skip", showlegend=True, name=f"Neu/getauscht ({len(added_so_far)})"))

    n = len(xy)
    touched = set()
    for u, v in added_so_far:
        touched.add(u)
        touched.add(v)
    other_xy = [xy[v] for v in range(n) if v not in touched]
    touched_xy = [xy[v] for v in range(n) if v in touched]
    if other_xy:
        fig.add_trace(go.Scatter(x=[p[0] for p in other_xy], y=[p[1] for p in other_xy], mode="markers", marker=dict(size=5.5, color=GREY), hoverinfo="skip", showlegend=False))
    if touched_xy:
        fig.add_trace(go.Scatter(x=[p[0] for p in touched_xy], y=[p[1] for p in touched_xy], mode="markers", marker=dict(size=7, color=TEAL), name=f"Betroffene Knoten ({len(touched_xy)})",
                                  hoverinfo="skip"))
    fig.add_trace(_corners_trace(xy))
    fig.update_layout(height=460, margin=dict(l=10, r=10, t=20, b=10), showlegend=True, legend=dict(orientation="h", y=1.08), plot_bgcolor="white")
    fig.update_xaxes(visible=False, fixedrange=True, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, fixedrange=True)
    return fig


# --- 2 · R/alpha*/beta_c ueber das Budget, alle drei Strategien ueberlagert -------------------------------------------------------------------------------


def _sweep_curve(rows, metric_key, baseline, y_title, title):
    fig = go.Figure()
    for strategy in ("random", "bypass", "schneider"):
        srows = [r for r in rows if r["strategy"] == strategy]
        xs = [r["budget"] for r in srows]
        ys = [r[metric_key] if r[metric_key] is not None else float("nan") for r in srows]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=STRATEGY_COLORS[strategy], width=2.4), marker=dict(size=6), name=strategy))
    if baseline is not None:
        fig.add_hline(y=baseline, line=dict(color=GREY, width=1.3, dash="dot"), annotation_text="vor der Härtung", annotation_position="bottom right", annotation=dict(bgcolor="white"))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.16), plot_bgcolor="white", title=dict(text=title, x=0.02, font=dict(size=13)))
    fig.update_xaxes(title="Budget-Ebene", fixedrange=True)
    fig.update_yaxes(title=y_title, fixedrange=True, gridcolor=LIGHT)
    return fig


def build_r_sweep(rows, r_before):
    return _sweep_curve(rows, "R", r_before, "R", "Robustheitsindex R über das Budget")


def build_alpha_sweep(rows, alpha_before):
    return _sweep_curve(rows, "alpha", alpha_before, "α*", "Kritische Toleranz α* über das Budget")


def build_beta_sweep(rows, beta_before):
    return _sweep_curve(rows, "beta_c", beta_before, "β_c", "Epidemieschwelle β_c über das Budget")


# --- 3 · Strategien im direkten Vergleich bei festem Budget ---------------------------------------------------------------------------------------------


def build_strategy_comparison_bars(rows, metric_key, baseline, title, y_title):
    labels = [r["strategy"] for r in rows]
    values = [r[metric_key] if r[metric_key] is not None else 0.0 for r in rows]
    colors = [STRATEGY_COLORS[s] for s in labels]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=values, marker_color=colors, text=[f"{v:.3f}" for v in values], textposition="outside"))
    top_candidates = values + ([baseline] if baseline is not None else [])
    top = max(top_candidates) * 1.3 if top_candidates and max(top_candidates) > 0 else 1.0
    if baseline is not None:
        fig.add_hline(y=baseline, line=dict(color=GREY, width=1.4, dash="dot"), annotation_text="vor der Härtung", annotation_position="top left", annotation=dict(bgcolor="white"))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), showlegend=False, plot_bgcolor="white", title=dict(text=title, x=0.02, font=dict(size=13)))
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title=y_title, range=[0, top], autorange=False, fixedrange=True, gridcolor=LIGHT)
    return fig


# --- 4 · Zwiebelstruktur? --------------------------------------------------------------------------------------------------------------------------------


def build_onion_bars(assort_before, assort_after):
    """Assortativität vor/nach der Schneider-Härtung als zwei Balken - steigt sie, ist das ein empirisches Indiz für die "Zwiebelstruktur" (Wu & Holme 2011)."""
    labels = ["vor der Härtung", "nach Schneider-Härtung"]
    values = [assort_before, assort_after]
    colors = [GREY, TEAL]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=values, marker_color=colors, text=[f"{v:.3f}" for v in values], textposition="outside"))
    fig.add_hline(y=0.0, line=dict(color=GREY, width=1.0, dash="dot"), annotation_text="neutral (r=0)", annotation_position="bottom right", annotation=dict(bgcolor="white"))
    lo = min(values + [0.0]) * 1.3 if min(values + [0.0]) < 0 else -0.1
    hi = max(values + [0.0]) * 1.3 if max(values + [0.0]) > 0 else 0.1
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), showlegend=False, plot_bgcolor="white", title=dict(text="Assortativität vor/nach Schneider-Härtung", x=0.02,
                       font=dict(size=13)))
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title="Grad-Assortativität r", range=[lo, hi], autorange=False, fixedrange=True, gridcolor=LIGHT)
    return fig


def build_r_history(r_history):
    """R-Verlauf des Schneider-Hill-Climbs (nur bei akzeptierten Tauschen ein neuer Punkt) - macht die monotone Verbesserung sichtbar (Korrektheits-Kette Punkt 2)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(r_history))), y=r_history, mode="lines+markers", line=dict(color=TEAL, width=2.4), marker=dict(size=5), name="R nach jedem akzeptierten Tausch"))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), showlegend=False, plot_bgcolor="white", title=dict(text="R-Verlauf des Hill-Climbs (nur akzeptierte Tausche)", x=0.02,
                       font=dict(size=13)))
    fig.update_xaxes(title="akzeptierter Tausch #", fixedrange=True)
    fig.update_yaxes(title="R", fixedrange=True, gridcolor=LIGHT)
    return fig
