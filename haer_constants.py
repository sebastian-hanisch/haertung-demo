"""Regler-Grenzen, feste Annahmen, gemessene Werte und Presets."""

SPACING = 1.0                    # Abstand der Kreuzungen im Betriebsnetz-Raster
JITTER = 0.18
SEED_MAX = 999999
DEFAULT_SEED = 35

KINDS = ("city", "ba", "barbell")
KIND_LABELS = {"city": "Betriebsnetz (Raster/Zufallsgraph)", "ba": "Skalenfreies Netz (Barabási-Albert)", "barbell": "Barbell-Lehrbuch"}

# --- Betriebsnetz (wortgleich aus kaskaden-demo/robustheit-demo) ---------------------------------------------------------------------------------------
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 4, 20, 10
NETTYPES = ("grid", "random")
NETTYPE_LABELS = {"grid": "Raster (Straßennetz)", "random": "Zufallsgraph (gleiche Kantenzahl)"}
BLOCKED_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
DEFAULT_BLOCKED = 0.2

# --- Skalenfreies Netz (Barabási und Albert 1999) -----------------------------------------------------------------------------------------------------
N_BA_MIN, N_BA_MAX, DEFAULT_N_BA = 30, 300, 150
M0_BA_MIN, M0_BA_MAX, DEFAULT_M0_BA = 3, 12, 4
M_BA_MIN, DEFAULT_M_BA = 1, 2

# --- Barbell-Lehrbuch (wortgleich aus kaskaden-demo/centrality-demo) ----------------------------------------------------------------------------------
BARBELL_K_MIN, BARBELL_K_MAX, DEFAULT_BARBELL_K = 3, 40, 8

# --- Härtungsstrategien ---------------------------------------------------------------------------------------------------------------------------------
STRATEGIES = ("random", "bypass", "schneider")
STRATEGY_LABELS = {"random": "Zufällig", "bypass": "Kritische-Kante-Bypass", "schneider": "Schneider u. a. (Hill-Climb)"}

# Budget B (neue Kanten) fuer Zufall/Bypass. Fuer Schneider hat B keine direkte Bedeutung (kein Kantenzuwachs, s. README "Design-Entscheidung") - dort
# steuert stattdessen n_trials die Haertung, B wird ausgeblendet (Hauskonvention gegen tote Regler).
BUDGET_MIN, BUDGET_MAX, DEFAULT_BUDGET = 0, 25, 8

# Versuche des Schneider-Hill-Climbs (nur sichtbar, wenn strategy=="schneider"). Kalibriert in der Vormessung (tools/vormessung.py, 2026-09-27, s. README "Vormessung"): schon ab n_trials~100-150
# ist auf allen drei Vehikeln eine deutlich sichtbare R-Verbesserung erreicht (z. B. Skalenfrei n=80: R 0.131->0.160 bei n_trials=100, ~0.5s); n_trials=500 kostet auf der groessten Instanz
# (Betriebsnetz-Zufallsgraph, n~170) rund 20s - noch mit Spinner vertretbar, aber bewusst als Obergrenze gedeckelt.
N_TRIALS_MIN, N_TRIALS_MAX, DEFAULT_N_TRIALS = 20, 500, 150

# Fuer den gemeinsamen "Budget-Ebene"-Sweep (Schritt 2, alle drei Strategien ueberlagert, gegen eine gemeinsame x-Achse "Budget"): Zufall/Bypass verbrauchen die Ebene direkt als B (Kanten),
# Schneider uebersetzt dieselbe Ebene ueber diesen kalibrierten Faktor in eine Versuchszahl (n_trials = Ebene * SCHNEIDER_TRIALS_PER_LEVEL) - eine grobe, aber nachvollziehbare
# Vergleichsbasis "Aufwand", KEINE exakte Kostenaequivalenz (s. README Design-Entscheidung). Bewusst wenige Stuetzstellen (Rechenzeit: jeder Punkt braucht eine volle alpha*-Ermittlung je
# Strategie, s. ALPHA_SWEEP_COARSE unten).
BUDGET_SWEEP = (0, 2, 5, 10, 17, 25)
SCHNEIDER_TRIALS_PER_LEVEL = 12

# Groebere alpha*-Ermittlung fuer die Mehrfach-Sweeps (budget_sweep, strategy_comparison - je Punkt mehrere critical_tolerance-Aufrufe): Schrittweite 1.0 statt 0.2 (21 statt 101 Stuetzstellen),
# etwa 5x schneller, bei gleichem Wertebereich 0..20. Die EINZELNE Vorher/Nachher-Analyse (Schritt 1, analyse()) verwendet weiterhin die feine ALPHA_SWEEP.
ALPHA_SWEEP_COARSE = tuple(round(0.0 + 1.0 * i, 1) for i in range(21))

# mu nur zur Auswertung der Epidemieschwellen-FORMEL beta_c=mu*<k>/<k^2> (keine SIR-Simulation in dieser Demo - reine Kennzahl aus den Gradmomenten).
MU_FOR_BETA_C = 0.3

INITIAL_STRATEGY_HELP = "Der Ausgangspunkt für α* ist stets der Knoten mit der aktuell höchsten Betweenness (vor bzw. nach der Härtung neu bestimmt)."

# ALPHA_SWEEP: Basis fuer critical_tolerance (kritische Toleranz alpha*), wortgleich aus kaskaden-demo (0.0 .. 20.0 in 0.2-Schritten - ein skalenfreier
# Hub-Ausfall braucht dort einen sehr grossen Sicherheitsspielraum, s. kas_constants.py).
ALPHA_SWEEP = tuple(round(0.0 + 0.2 * i, 2) for i in range(101))

STEPS = {1: "1 · Härtung in Aktion", 2: "2 · R/α*/β_c über das Budget", 3: "3 · Strategien im direkten Vergleich", 4: "4 · Zwiebelstruktur?"}

# --- Gemessene Werte (Seed 35, sofern nicht anders angegeben; 2026-09-27, alle Werte über ev.*-Aufrufe nachgerechnet, s. tests/test_claims.py) -----------
# Zur Erinnerung (wortgleiche Konvention aus kaskaden-demo): JE GROESSER alpha*, desto VERWUNDBARER das Netz (mehr Sicherheitsspielraum noetig, um einen Kaskadenausbruch zu vermeiden) - Haertung
#   soll alpha* also SENKEN. JE KLEINER beta_c, desto VERWUNDBARER (eine Epidemie kann schon bei kleinerer Ansteckungswahrscheinlichkeit ausbrechen) - Haertung soll beta_c ANHEBEN.
#
# BARBELL (k=8) + BYPASS b=1: R/alpha*/beta_c praktisch unveraendert (0.2500->0.2500, 0.0->0.0 - alpha* war schon vorher am Boden, s. kaskaden-demo), ABER die Bruecke (7,8) ist DANACH exakt weg
#   (low_link findet 0 Bruecken) - der Single Point of Failure ist beseitigt, obwohl die drei geerbten Kennzahlen das kaum zeigen (sie messen etwas anderes als "gibt es noch eine Bruecke").
# BETRIEBSNETZ (n=100, budget=8/n_trials=150): Schneider verbessert BEIDE Kennzahlen klar (R 0.2055->0.2384 hoeher=besser; alpha* 2.8->0.8 NIEDRIGER=besser) und laesst beta_c EXAKT unveraendert.
#   Zufall zeigt dagegen einen echten ZIELKONFLIKT: R wird SCHLECHTER (0.2055->0.2026), aber alpha* wird BESSER (2.8->1.8) - UND beta_c wird schlechter (0.0939->0.0880). Bypass bewegt R kaum
#   (+0.0003) und macht sowohl alpha* (2.8->3.6, schlechter) als auch beta_c (0.0939->0.0854, schlechter) SCHLECHTER, trotz des gezielten Angriffs auf die hoechstbelastete Kante.
# SKALENFREI (n=150, budget=8 UND budget=20): Bypass aendert R NICHT MESSBAR (0.1112->0.1112, exakt gleich bei BEIDEN Budgets) und macht alpha* UNDEFINIERT (17.0 -> kein Sweep-Wert bis 20.0 reicht
#   mehr aus, also SCHLECHTER als 17.0) sowie beta_c schlechter - ein robuster NEGATIVER Befund fuer die "gezielte" Strategie auf dem Hub-dominierten Netz. Schneider dagegen verbessert R UND alpha*
#   klar (budget=20: R 0.1112->0.1588, alpha* 17.0->4.0 - eine Vervierfachung der Robustheit) und laesst beta_c wieder exakt unveraendert.
# BETA_C: bleibt unter SCHNEIDER-Haertung in JEDEM gemessenen Fall exakt (nicht nur ungefaehr) unveraendert - beta_c haengt nur von der Gradfolge ab, die Schneider per Konstruktion exakt erhaelt
#   (Satz, s. tests/test_hardening.py::test_harden_schneider_leaves_beta_c_exactly_invariant). Bei Zufall/Bypass aendert sich beta_c dagegen (neue Kanten aendern Grade) meist zum SCHLECHTEREN.
# ZWIEBELSTRUKTUR (Wu & Holme 2011, n_trials=800): NUR beim Betriebsnetz-Zufallsgraph (n=169) bestaetigt sich die Hypothese deutlich (Assortativitaet 0.0182->0.1105, +0.0923). Beim reinen Raster
#   (n=100) geht sie sogar in die GEGENRICHTUNG (0.1000->0.0471, -0.0529) trotz klar steigendem R (0.2055->0.2609). Beim Skalenfrei-Netz bleibt sie praktisch unveraendert (-0.1692->-0.1681). Beim
#   Barbell (k=8) bewegt sich gar nichts (nur 7 akzeptierte Tausche moeglich, zu kleine Instanz). Fazit: die Zwiebelstruktur-Hypothese bestaetigt sich NICHT durchgaengig, nur auf einem von vier
#   getesteten Faellen deutlich - ein ehrlicher, gemischter Befund, keine allgemeine Bestaetigung bei diesen Instanzgroessen.
PRESET_HELP_MEASURED_AT = "2026-09-27"

PRESETS = {
    "Barbell-Bypass (Brücke verschwindet)": {"kind": "barbell", "kbarbell": 8, "strategy": "bypass", "budget": 1, "seed": 35, "step": 4},
    "Schneider gewinnt auf beiden Kennzahlen": {"kind": "city", "side": 10, "blocked": 0.2, "nettype": "grid", "strategy": "schneider", "budget": 8, "ntrials": 150, "seed": 35, "step": 3},
    "Skalenfrei härten: Bypass versagt trotz Zielkante": {"kind": "ba", "nba": 150, "mba": 2, "m0ba": 4, "strategy": "bypass", "budget": 8, "ntrials": 150, "seed": 35, "step": 3},
    "Zufällig: R gegen α* im Widerspruch": {"kind": "city", "side": 10, "blocked": 0.2, "nettype": "grid", "strategy": "random", "budget": 8, "ntrials": 150, "seed": 35, "step": 3},
    "Schneider-Optimierung in Aktion": {"kind": "ba", "nba": 150, "mba": 2, "m0ba": 4, "strategy": "schneider", "budget": 8, "ntrials": 400, "seed": 35, "step": 1},
    "Zwiebelstruktur: bestätigt sich nicht überall": {"kind": "city", "side": 13, "blocked": 0.0, "nettype": "random", "strategy": "schneider", "budget": 8, "ntrials": 800, "seed": 35, "step": 4},
    "Budget-Sweep Betriebsnetz": {"kind": "city", "side": 10, "blocked": 0.2, "nettype": "grid", "strategy": "schneider", "budget": 8, "ntrials": 150, "seed": 35, "step": 2},
    "Drei-Strategien-Vergleich Skalenfrei (hohes Budget)": {"kind": "ba", "nba": 150, "mba": 2, "m0ba": 4, "strategy": "schneider", "budget": 20, "ntrials": 400, "seed": 35, "step": 3},
}
PRESET_HELP = {
    "Barbell-Bypass (Brücke verschwindet)": "R/α*/β_c ändern sich kaum (0.2500→0.2500, 0.0→0.0) - aber die Brücke (7,8) ist danach exakt weg (0 Brücken statt 1): der Single Point of Failure ist "
                                             "beseitigt, obwohl die drei geerbten Kennzahlen das kaum zeigen (sie messen etwas anderes als „gibt es noch eine Brücke“).",
    "Schneider gewinnt auf beiden Kennzahlen": "R steigt (0.2055→0.2384, höher=besser) UND α* sinkt (2.8→0.8, niedriger=robuster) gleichzeitig - β_c bleibt dabei EXAKT unverändert (Schneider "
                                                "erhält die Gradfolge, von der β_c allein abhängt, s. README „Befunde“).",
    "Skalenfrei härten: Bypass versagt trotz Zielkante": "Bypass ändert R auf dem skalenfreien Netz NICHT MESSBAR (0.1112→0.1112, exakt gleich bei B=8 UND B=20) und macht α* SCHLECHTER "
                                                          "(17.0→undefiniert, d. h. > 20) - trotz des gezielten Angriffs auf die höchstbelastete Kante. Schneider verbessert im selben Fall beide "
                                                          "Kennzahlen klar.",
    "Zufällig: R gegen α* im Widerspruch": "Ein echter Zielkonflikt: Zufällige Härtung macht R SCHLECHTER (0.2055→0.2026), aber α* gleichzeitig BESSER (2.8→1.8) - und β_c wird ebenfalls "
                                            "schlechter (0.0939→0.0880). Die drei geerbten Kennzahlen messen unterschiedliche Angriffsmodelle und können gegenläufig reagieren.",
    "Schneider-Optimierung in Aktion": "R steigt beim Skalenfrei-Netz deutlich (0.1112→0.1377 bei 150 Versuchen) - der R-Verlauf zeigt jeden akzeptierten Tausch als monotonen Schritt nach oben "
                                       "(Korrektheits-Kette Punkt 2).",
    "Zwiebelstruktur: bestätigt sich nicht überall": "Beim Betriebsnetz-Zufallsgraph (n=169) bestätigt sich Wu & Holmes Zwiebelstruktur-Hypothese deutlich (Assortativität 0.018→0.111 bei 800 "
                                                      "Versuchen) - beim reinen Raster geht sie dagegen in die GEGENRICHTUNG (0.100→0.047) trotz klar steigendem R. Kein durchgängiger Befund.",
    "Budget-Sweep Betriebsnetz": "Schneiders R-Kurve steigt sauber monoton mit dem Budget (0.2055→0.2428), während Bypass und Zufall über das Budget NICHT monoton verlaufen (Bypass fällt bei "
                                 "B=25 sogar unter den Wert bei B=17 zurück) - reines Betweenness- bzw. Zufalls-Greedy optimiert nicht direkt für R.",
    "Drei-Strategien-Vergleich Skalenfrei (hohes Budget)": "Bei hohem Aufwand (B=20/400 Versuche) gewinnt Schneider klar auf BEIDEN Kennzahlen (R 0.1112→0.1588, α* 17.0→4.0, eine Vervierfachung "
                                                            "der Robustheit), während Bypass weiterhin exakt 0 R-Wirkung zeigt und α* sogar undefiniert (also schlechter) macht.",
}
