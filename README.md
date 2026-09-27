# Kritische Knoten härten – Zufällig, Kritische-Kante-Bypass, Schneider u. a. 2011 – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-haertung-demo.streamlit.app/)**

Zehntes Stück der **Graphen-und-Netzwerke-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", ein Zusammenfluss aus Zentralität (Stück 6, [centrality-demo](https://github.com/sebastian-hanisch/centrality-demo)), Robustheit (Stück 8, [robustheit-demo](https://github.com/sebastian-hanisch/robustheit-demo)) und Kaskaden/Ausbreitung (Stück 9, [kaskaden-demo](https://github.com/sebastian-hanisch/kaskaden-demo)): bisher wurde nur GEMESSEN, wie verwundbar ein Netz ist – jetzt geht es darum, mit einem begrenzten Härtungsbudget B (zusätzliche Kanten) oder einem Trainingsaufwand (Versuche) etwas dagegen zu tun. Drei Strategien: **Zufällig** (B zufällige neue Kanten zwischen nicht benachbarten Knoten), **Kritische-Kante-Bypass** (wiederholt die aktuell am stärksten belastete Kante finden und einen Umweg drumherum bauen, ohne sie zu entfernen) und **Schneider u. a. 2011** (PNAS 108(10), 3838–3841: ein Kanten-Doppeltausch wie das Konfigurationsmodell aus Stück 7, aber NUR akzeptiert, wenn er den Robustheitsindex R aus Stück 8 unter gezieltem Grad-Angriff verbessert – ein echter, gradfolgen-erhaltender Hill-Climb). Gemessen wird die Wirkung auf alle drei geerbten Kennzahlen (R, kritische Toleranz α\*, Epidemieschwelle β_c) sowie, als Zusatzbefund, ob Schneiders Optimierung eine "Zwiebelstruktur" erzeugt (Wu & Holme 2011, Phys. Rev. E 84, 026106).

**Einordnung in die Reihe:** die Reihe hat zwölf Stücke, dies ist das zehnte (Details in `graphen-planung/PLAN.md` des Portfolio-Ordners):

```
1 BFS und DFS (Wurzel)                                                        [gebaut: bfs-dfs-demo]
 ├─ 2 Brücken und Artikulationspunkte ─ 4 Euler-Touren                        [gebaut: bridges-demo, euler-tour-demo]
 ├─ 3 Starke Zusammenhangskomponenten, topologische Sortierung                [gebaut: scc-demo]
 ├─ 5 Graphfärbung                                                            [gebaut: graph-coloring-demo]
 ├─ 6 Zentralität ─ 7 Strukturkennzahlen ─ 8 Robustheit ─ 9 Kaskaden/Ausbr.   [gebaut: centrality-demo, strukturkennzahlen-demo, robustheit-demo, kaskaden-demo]
 │                            └─ 10 Kritische Knoten härten                   [gebaut: haertung-demo ─ DIESES STÜCK]
 └─ 11 Bandbreite ─ 12 Bandbreite von G(n,k,b) und Cliquenüberdeckung         [nicht gebaut]
```

**Wichtige Leserichtung** (wortgleiche Konvention aus Stück 8/9): höheres R = robuster. **Niedrigeres** α\* = robuster (weniger Sicherheitsspielraum nötig, um einen Kaskadenausbruch zu vermeiden). **Höheres** β_c = robuster (eine Epidemie braucht eine größere Ansteckungswahrscheinlichkeit, um sich auszubreiten). Härtung soll also R und β_c ANHEBEN, α\* dagegen SENKEN.

Ergebnis in Kürze – und eine ehrliche Überraschung: Die "smarte", gezielte **Kritische-Kante-Bypass**-Strategie schneidet auf dem skalenfreien Netz auffällig SCHLECHT ab – R ändert sich exakt NICHT (0.1112→0.1112, sowohl bei Budget 8 als auch bei Budget 20) und die kritische Toleranz α\* wird sogar UNDEFINIERT (schlechter als 17.0 – keine Kaskaden-Grenze mehr im gesamten getesteten Bereich bis 20.0). **Schneiders Hill-Climb** gewinnt dagegen auf demselben Netz klar auf beiden Kennzahlen (R 0.1112→0.1588, α\* 17.0→4.0 bei Budget 20/400 Versuchen) und lässt β_c dabei PROVABLY exakt unverändert (β_c hängt nur von der Gradfolge ab, die Schneider per Konstruktion exakt erhält). Über eine breitere Stichprobe (24–80 zufällige Instanzen) verschlechtert **Bypass** die kritische Toleranz sogar VERLÄSSLICH im Mittel – ein Gegenbeispiel zur naheliegenden Annahme, dass die gezielteste Strategie automatisch auch die beste ist. Die Zwiebelstruktur-Hypothese (Wu & Holme 2011) bestätigt sich nur auf EINEM von vier getesteten Vehikeln deutlich.

## Warum dieses Problem

Die Vorgänger-Stücke haben gezeigt, WIE verwundbar Netze gegenüber gezieltem Angriff (Stück 8), lastbasierten Kaskaden und Epidemien (Stück 9) sind – aber nie, was man dagegen TUN kann. In der Praxis (Stromnetze, Lieferketten, Kommunikationsnetze) steht man selten vor der Wahl "alles neu bauen", sondern vor einem KLEINEN Budget: ein paar zusätzliche Leitungen, ein paar redundante Verbindungen. Diese Demo vergleicht drei realistische Handlungsoptionen dafür – von "irgendwo eine Kante hinzufügen" bis zu einem literaturbekannten, gezielten Optimierungsverfahren – und deckt dabei auf, dass "gezielter" nicht automatisch "besser" bedeutet, sobald man mehrere Kennzahlen gleichzeitig im Blick behält.

## Vorab-Hypothesen (vor der Messung notiert, hier geprüft)

| Hypothese | Ergebnis |
|---|---|
| **H1** Jede Härtungsstrategie fügt exakt B neue Kanten hinzu (Zufällig/Bypass) bzw. erhält die Gradfolge exakt (Schneider), nie Selbstloops/Mehrfachkanten. | ✅ Bestätigt auf ≥300 zufälligen Instanzen (`tests/test_hardening.py`). |
| **H2** Schneiders R ist nach jedem AKZEPTIERTEN Tausch nicht kleiner als davor; ein ABGELEHNTER Tausch lässt den Graphen unverändert. | ✅ Bestätigt als Invariante über ganze Versuchsfolgen (Satz durch Konstruktion, exakt getestet). |
| **H3** Kritische-Kante-Bypass beseitigt die Barbell-Brücke exakt bei B≥1. | ✅ Bestätigt exakt (0 Brücken danach, `low_link`-Gegenprobe). |
| **H4** Kritische Toleranz α\* verbessert sich nach Härtung im Mittel über viele Instanzen, für JEDE der drei Strategien. | ❌ **Widerlegt für Bypass** (verschlechtert α\* im Mittel VERLÄSSLICH, über mehrere unabhängige Stichproben deutlich positiv/schlechter). Für Zufall/Schneider **nicht robust bestätigbar** (Mittelwert nahe null, Standardabweichung deutlich größer als der Mittelwert – kein verlässlicher Effekt in eine feste Richtung). Nur in Einzelfällen (z. B. dem Betriebsnetz- und Skalenfrei-Standardpreset) verbessert Schneider α\* klar. |
| **H5** Epidemieschwelle β_c ändert sich nach Härtung (Richtung offen). | ✅ Gemessen, Richtung tatsächlich instanz- und strategieabhängig – UND: unter Schneider-Härtung EXAKT (nicht nur ungefähr) unverändert, ein beweisbarer Satz (β_c hängt nur von der Gradfolge ab, die Schneider exakt erhält). |
| **H6** Schneiders Optimierung erzeugt eine "Zwiebelstruktur" (Wu & Holme 2011: Assortativität steigt). | ⚠️ **Nur teilweise bestätigt:** deutlich bestätigt auf dem Betriebsnetz-Zufallsgraphen (Assortativität 0.018→0.111), aber WIDERLEGT auf dem reinen Straßenraster (0.100→0.047, Rückgang trotz klar steigendem R) und praktisch ohne Effekt auf dem skalenfreien Netz und dem Barbell. |
| **H7** "Gezieltere" Strategien schneiden nie schlechter ab als die naive Zufallsstrategie. | ❌ **Widerlegt:** Bypass gibt auf dem skalenfreien Netz exakt 0 R-Gewinn (bei zwei verschiedenen Budgets) und macht α\* undefiniert, während Zufall auf demselben Netz sowohl R als auch (bei höherem Budget) α\* verbessert. |
| **H8** Sonderfälle (Budget=0, Budget größer als der vollständige Graph, unzusammenhängende Ausgangsinstanz) laufen ohne Fehler und liefern die erwarteten Randwerte. | ✅ Bestätigt (Identität bei Budget=0, Kappung bei zu großem Budget, keine Abstürze auf getrennten Instanzen). |

## Befunde (gemessen, keine Behauptungen)

Seed 35, Standardeinstellungen sofern nicht anders angegeben; alle Zahlen über `haer_evaluation`-Funktionen nachgerechnet (`tests/test_presets.py`, `tests/test_claims.py`).

| Frage | Ergebnis |
|---|---|
| **Stimmt das Verfahren?** | ✅ Jede Strategie liefert exakt B neue Kanten (Zufällig/Bypass) bzw. die exakt erhaltene Gradfolge (Schneider) auf ≥300 Instanzen; Schneiders R-Verlauf ist über jede Versuchsfolge nicht-fallend; ein abgelehnter Tauschversuch lässt den Graphen byte-identisch; Bypass beseitigt die Barbell-Brücke exakt bei B≥1; β_c bleibt unter Schneider-Härtung exakt invariant. |
| **Barbell (k=8) + Bypass B=1** | R/α\*/β_c ändern sich kaum (0.2500→0.2500, 0.0→0.0 exakt) – aber die Brücke (7,8) ist danach WEG (0 statt 1 Brücke): der Single Point of Failure ist beseitigt, obwohl die drei geerbten Kennzahlen das kaum zeigen. |
| **Betriebsnetz (n=100, Budget=8/n_trials=150), Schneider** | R UND α\* verbessern sich gleichzeitig (R 0.2055→0.2384, α\* 2.8→0.8) – β_c bleibt EXAKT unverändert (0.0939→0.0939). |
| **Betriebsnetz, Zufällig** | Ein echter Zielkonflikt: R wird SCHLECHTER (0.2055→0.2026), α\* gleichzeitig BESSER (2.8→1.8) – und β_c wird ebenfalls schlechter (0.0939→0.0880). |
| **Betriebsnetz, Bypass** | R bewegt sich kaum (+0.0003), α\* wird SCHLECHTER (2.8→3.6) und β_c ebenfalls (0.0939→0.0854) – trotz des gezielten Angriffs auf die höchstbelastete Kante. |
| **Skalenfrei (n=150), Bypass, Budget=8 UND Budget=20** | R bleibt EXAKT unverändert (0.1112→0.1112 bei BEIDEN Budgets) und α\* wird UNDEFINIERT (17.0→>20, also schlechter) – ein robuster negativer Befund für die gezielte Strategie auf dem Hub-dominierten Netz. |
| **Skalenfrei, Schneider, Budget=20/400 Versuche** | R UND α\* verbessern sich klar (R 0.1112→0.1588, α\* 17.0→4.0 – eine Vervierfachung der Robustheit), β_c bleibt exakt unverändert. |
| **Zwiebelstruktur (Wu & Holme 2011), n_trials=800** | Betriebsnetz-Zufallsgraph (n=169): Assortativität 0.018→0.111 (bestätigt). Betriebsnetz-Raster (n=100): 0.100→0.047 (WIDERLEGT, Rückgang trotz steigendem R). Skalenfrei (n=150): −0.169→−0.168 (praktisch kein Effekt). Barbell (k=8): unverändert (nur 7 akzeptierte Tausche, zu kleine Instanz). |
| **α\*-Mittelwert über 24–80 zufällige Instanzen** | Bypass verschlechtert α\* VERLÄSSLICH im Mittel (deutlich positiver Mittelwert, d. h. höher/verwundbarer, über mehrere unabhängige Stichproben stabil zwischen +1.6 und +5.2). Zufall und Schneider zeigen dagegen keinen verlässlichen Effekt in eine feste Richtung (Standardabweichung deutlich größer als der Mittelwert). |

Presets (8), alle mit den Zahlen in ihren Hilfetexten (`tests/test_presets.py`):

| Preset | Was es zeigt |
|---|---|
| Barbell-Bypass (Brücke verschwindet) | R/α\*/β_c kaum verändert, aber die Brücke ist danach exakt weg |
| Schneider gewinnt auf beiden Kennzahlen | R steigt UND α\* sinkt gleichzeitig, β_c exakt invariant |
| Skalenfrei härten: Bypass versagt trotz Zielkante | R exakt unverändert, α\* wird undefiniert (schlechter) |
| Zufällig: R gegen α\* im Widerspruch | Echter Zielkonflikt zwischen zwei Kennzahlen |
| Schneider-Optimierung in Aktion | R-Verlauf des Hill-Climbs, monoton steigend |
| Zwiebelstruktur: bestätigt sich nicht überall | Zufallsgraph bestätigt, reines Raster widerlegt die Hypothese |
| Budget-Sweep Betriebsnetz | Schneiders R-Kurve monoton, Bypass/Zufall nicht |
| Drei-Strategien-Vergleich Skalenfrei (hohes Budget) | Schneider gewinnt klar auf beiden Kennzahlen, Bypass bleibt wirkungslos |

## Modell und Verfahren

- **Betriebsnetz, Skalenfreies Netz, Barbell** (`haer_scenario.py`, wortgleich aus `kas_scenario.py`/`rob_scenario.py`/`cen_scenario.py`): dieselben drei Vehikel wie in den Stücken 6/8/9.
- **Zufällige Härtung** (`harden_random`): B neue Kanten zwischen zufälligen, noch nicht benachbarten Knotenpaaren.
- **Kritische-Kante-Bypass** (`harden_critical_bypass`): B mal wiederholen – Kanten-Betweenness (Brandes 2001) auf dem aktuellen Graphen berechnen, die höchstbelastete Kante finden, einen Umweg über einen Nachbarn hinzufügen, der sie entlastet, ohne sie zu entfernen.
- **Schneider u. a. 2011** (`harden_schneider`, PNAS 108(10), 3838–3841): Kanten-Doppeltausch wie das Konfigurationsmodell (Stück 7), aber nur akzeptiert, wenn er den Robustheitsindex R (Stück 8, unter grad-adaptivem Angriff) gegenüber dem Zustand vor genau diesem Versuch strikt verbessert – ein echter Hill-Climb, gradfolgen-erhaltend.
- **Gemessene Kennzahlen:** R (`robustness_index` unter `degree_order_adaptive`-Angriff), kritische Toleranz α\* (`critical_tolerance`, Motter-Lai-Kaskade, Stück 9), Epidemieschwelle β_c (`epidemic_threshold_prediction`, Stück 9), Grad-Assortativität (`degree_assortativity`, Stück 7) als Zwiebelstruktur-Indiz.

## Design-Entscheidungen

- **"Budget" bedeutet bei Schneider keine neuen Kanten.** Schneiders Kanten-Doppeltausch fügt nie neue Kanten hinzu (die Gradfolge bleibt exakt erhalten) – "B neue Kanten" ist für diese Strategie bedeutungslos. Die Sidebar zeigt deshalb bei Schneider statt eines Budget-Reglers einen `n_trials`-Regler (Zahl der Tauschversuche) – Hauskonvention gegen tote Regler. Für den gemeinsamen Budget-Sweep (Schritt 2, alle drei Strategien über eine gemeinsame x-Achse) wird dieselbe Budget-Ebene für Schneider in eine Versuchszahl übersetzt (`n_trials = Ebene × 12`, kalibriert in der Vormessung) – eine grobe, aber nachvollziehbare Vergleichsbasis "Aufwand", KEINE exakte Kostenäquivalenz.
- **Der "höchstbelastete Knoten" für α\* wird bei JEDER Auswertung neu bestimmt** (vor der Härtung: der ursprüngliche Hub; nach der Härtung: der dann höchstbelastete Knoten). Das ist konsistent mit der Kaskaden-Demo (Stück 9), macht α\* aber empfindlich gegenüber Verschiebungen der Zentralitätsstruktur durch die Härtung selbst – ein Teil der Erklärung für die stark schwankenden α\*-Mittelwerte über viele Instanzen (s. Grenzen).
- **Kritische-Kante-Bypass-Konvention:** bei der höchstbelasteten Kante (u, v) mit u < v wird der Umweg über einen Nachbarn von v (dem größeren Endpunkt der sortierten Kante) gesucht – eine willkürliche, aber deterministische und dokumentierte Wahl (der Plantext ließ offen, welcher der beiden Endpunkte "u" bzw. "v" ist).
- **Grobe Alpha*-Ermittlung in den Mehrfach-Sweeps:** `budget_sweep`/`strategy_comparison` verwenden eine gröbere α-Sweep-Auflösung (Schrittweite 1.0 statt 0.2) als die Einzel-Analyse (Schritt 1), um die Rechenzeit bei vielen aufeinanderfolgenden `critical_tolerance`-Aufrufen im Rahmen zu halten (s. Vormessung unten).

## Vormessung (Kalibrierung)

Ein Schneider-Hill-Climb mit `n_trials=100` zeigt auf allen drei Vehikeln schon eine deutlich sichtbare R-Verbesserung (z. B. Skalenfrei n=80: R 0.131→0.160, ~0.5s). `n_trials=500` kostet auf der größten getesteten Instanz (Betriebsnetz-Zufallsgraph, n≈170) rund 20s – noch mit Spinner vertretbar, aber bewusst als Obergrenze gedeckelt (`N_TRIALS_MAX=500`). Die kritische Toleranz α\* ist der eigentliche Kostentreiber der Mehrfach-Sweeps (jeder Punkt braucht bis zu 20+ volle Kaskadensimulationen) – deshalb die gröbere `ALPHA_SWEEP_COARSE` und bewusst wenige Budget-Stützstellen (6) in Schritt 2.

## Was die App zeigt

1. **Vier Schritte** (Schritt-Regler): **Härtung in Aktion** (Karte mit Schieberegler über die hinzugefügten/getauschten Kanten) → **R/α\*/β_c über das Budget** (drei Kurven je Kennzahl, alle drei Strategien überlagert) → **Strategien im direkten Vergleich** (Balken bei festem Budget/n_trials) → **Zwiebelstruktur?** (Assortativität vor/nach Schneider-Härtung, plus Brücken-Zähler für die aktuelle Strategie).
2. **Härtungsstrategie** (Zufällig / Kritische-Kante-Bypass / Schneider): schaltet zwischen Budget-Regler (Zufällig/Bypass) und Versuche-Regler (Schneider) um – nie beide gleichzeitig sichtbar.
3. Regler: Instanz (Betriebsnetz / Skalenfreies Netz / Barbell), instanzspezifische Parameter, Härtungsstrategie, Budget B bzw. Versuche n_trials, Zufalls-Seed (+🎲); Permalink in der Adresszeile.

## Was nicht funktioniert hat / Grenzen

- **Schneiders Hill-Climb ist ein echter Hill-Climb, kein simuliertes Auskühlen.** Er bleibt in einem lokalen Optimum stecken – ein Tausch, der KURZFRISTIG R senkt, aber langfristig einen besseren Zustand freischalten würde, wird nie akzeptiert. Diese Vereinfachung ist im Code und in der App dokumentiert.
- **R, α\* und β_c messen unterschiedliche Angriffsmodelle** (Grad-Angriff, Betweenness-basierte Kaskade um den jeweils aktuellen Hub, Gradmomente) und können sich GEGENLÄUFIG entwickeln – eine Strategie, die eine Kennzahl verbessert, verbessert die anderen nicht automatisch mit (s. Befunde oben, besonders das Zufällig-Betriebsnetz-Beispiel).
- **Der "höchstbelastete Knoten" für α\* wird nach der Härtung neu bestimmt** und kann sich an eine strukturell ganz andere Stelle verschieben – das macht α\*-Mittelwerte über viele, unterschiedlich strukturierte Instanzen sehr rauschanfällig (Standardabweichung teils 10× größer als der Mittelwert).
- **Kritische-Kante-Bypass entfernt die belastete Kante nicht, sondern baut nur einen Umweg.** Auf dichten/kleinen Instanzen kann irgendwann kein Kandidat mehr gefunden werden – die Härtung bricht dann vor Erreichen des Budgets ab.
- **"Budget" ist bei Schneider kein Kantenzuwachs** – die gemeinsame Budget-Achse in Schritt 2 ist für Schneider eine grobe Übersetzung in eine Versuchszahl, keine exakte Kostenäquivalenz (s. Design-Entscheidungen).
- **Die Zwiebelstruktur-Hypothese (Wu & Holme 2011) bestätigt sich NICHT durchgängig** – nur auf einem von vier getesteten Vehikel/Varianten-Kombinationen deutlich, auf einer sogar in die Gegenrichtung.
- **Synthetische Instanzen.** Betriebsnetz, skalenfreies Netz und Barbell sind erzeugt, keine echten Infrastrukturdaten.

## Tests

`tests/test_scenario.py` (Rauchtests der drei Instanzen), `tests/test_algorithm_base.py` (wortgleich kopierte Bausteine gegen networkx), `tests/test_hardening.py` (Korrektheits-Kette Punkte 1–3: exakte Kantenzahl/Gradfolge auf ≥300 Instanzen, Schneider-R-Monotonie und Rückgängig-Exaktheit, Barbell-Bypass beseitigt die Brücke exakt, β_c-Invarianz unter Schneider, Sonderfälle), `tests/test_evaluation.py` (Korrektheits-Kette Punkte 4–8: α\*-Mittelwert ehrlich gemessen inkl. der korrigierten Leserichtung, β_c-Richtung offen, Zwiebelstruktur-Check, Determinismus, Sonderfälle), `tests/test_presets.py` (jede Zahl der Preset-Hilfetexte), `tests/test_claims.py` (jede README-Zahl über die echten Auswertungsfunktionen), `tests/test_app.py` (AppTest – Voreinstellung, jedes Preset, jeder Schritt für jede Instanzart und Strategie, bedingte Regler, Permalink-Grenzen, Footer).

```
python -m pytest tests/ -v
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-App |
| `haer_algorithm.py` | Bausteine (wortgleich aus kaskaden-demo/robustheit-demo/centrality-demo/strukturkennzahlen-demo), drei Härtungsstrategien |
| `haer_scenario.py` | Betriebsnetz, skalenfreies Netz, Barbell (wortgleich aus kaskaden-demo) |
| `haer_evaluation.py` | Analyse, Budget-Sweep, Strategienvergleich, Zwiebelstruktur-Check |
| `haer_visualization.py` | Plotly-Figuren (Härtungskarte, Sweep-Kurven, Vergleichsbalken, Onion-Balken) |
| `haer_presets.py`, `haer_constants.py` | Permalink, Presets, gemessene Werte |
| `tests/` | Tests |

## Bewusst nicht umgesetzt

Simuliertes Auskühlen (Simulated Annealing) statt eines reinen Hill-Climbs für Schneiders Optimierung – hätte lokale Optima vermeiden können, ist aber bewusst als Vereinfachung dokumentiert (s. Grenzen). Bandbreitenminimierung (Stück 11/12 der Reihe) – ein eigenständiges, unabhängiges Thema.

## Lokal ausführen

```
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\streamlit run app.py
```

## Literatur

- Schneider, C. M., Moreira, A. A., Andrade, J. S., Herrmann, H. J., & Havlin, S. (2011). *Mitigation of malicious attacks on networks.* Proceedings of the National Academy of Sciences 108(10), 3838–3841.
- Wu, Z.-X., & Holme, P. (2011). *Onion structure and network robustness.* Physical Review E 84, 026106.
- Maslov, S., & Sneppen, K. (2002). *Specificity and stability in topology of protein networks.* Science 296(5569), 910–913 (Kanten-Doppeltausch-Mechanik, wortgleich aus `strukturkennzahlen-demo`).
- Brandes, U. (2001). *A faster algorithm for betweenness centrality.* Journal of Mathematical Sociology 25(2), 163–177 (wortgleich aus `kaskaden-demo`/`robustheit-demo`/`centrality-demo`).
- Motter, A. E., & Lai, Y.-C. (2002). *Cascade-based attacks on complex networks.* Physical Review E 66, 065102(R) (wortgleich aus `kaskaden-demo`).
- Pastor-Satorras, R., & Vespignani, A. (2001). *Epidemic spreading in scale-free networks.* Physical Review Letters 86(14), 3200–3203 (wortgleich aus `kaskaden-demo`).

Gebaut mit Streamlit, Plotly, NumPy und pandas.
