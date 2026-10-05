# Buchungs-/Slot-Vergabe: Wer bekommt den letzten Container-Slot? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-revenue-management-demo.streamlit.app/)**

Interaktive Fall-Demo zum **Revenue Management** einer Reederei: Container-Slots sind knapp, **Spot-Fracht** (günstig) bucht meist früh, **Premium-Fracht** (teuer) meist erst kurz vor Abfahrt. Wer früh
jede günstige Anfrage annimmt, hat am Ende keinen Platz mehr für die teuren Spätbucher – der klassische **Klassenschutz**-Effekt der Revenue-Management-Literatur (Littlewood 1972). Die Demo beantwortet:
**Wie viel Ertrag lässt reines Windhundprinzip liegen – und reicht Littlewoods einfache, 1972 hergeleitete Formel, um das fast zu vermeiden?**

Teil des Portfolios für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, **Welle 4 (letzte) der Seefracht-Linie** (Schwesterlinie zur Hafen-Linie, nach `leercontainer-demo`,
`mehrhafenstau-demo`, `slow-steaming-demo`). Anders als die ersten drei Wellen ist diese die einzige mit einer „baut aus“-Kante: sie hebt `freight_demo`s stillschweigende Annahme auf, dass die zu
konsolidierenden Sendungen schon feststehen – hier wird erst entschieden, welche Buchungen überhaupt angenommen werden (die angenommenen Buchungen wären die Sendungen, die `freight_demo` konsolidiert).
Vehikel: eine Abfahrt mit C Container-Slots, N diskrete Buchungsgelegenheiten vor Abfahrt.

## Warum dieses Problem

Bei knapper Kapazität (Preset „Knappe Kapazität“, 4 Slots) kostet reines FCFS (annehmen, solange Platz ist, ohne auf die Preisklasse zu achten) **über ein Drittel** (36,0 %) des erreichbaren Ertrags – der stärkste
Heuristik-Abstand der ganzen Seefracht-Linie. Die eigentliche Überraschung: Littlewoods klassische, 1972 hergeleitete geschlossene Schutzformel kommt dabei verblüffend nah ans echte DP-Optimum
(in den fünf Presets -0,06 % bis -1,29 %; über das gesamte Reglerraster bei 30 Epochen zwischen etwa +0,1 % und -5 %, am weitesten bei knapper Kapazität und premium-armer Nachfrage) – ein Lehrbuchergebnis bestätigt sich empirisch. Die Kernbotschaft dieser Demo ist deshalb ungewöhnlich für die Seefracht-Linie: **man braucht die
schwere Rückwärts-Induktion fast nie**, die einfache Formel reicht.

## Modell

Zwei Frachtklassen: **Spot** (niedriger Preis r_lo, bucht überwiegend früh) und **Premium** (hoher Preis r_hi > r_lo, bucht überwiegend spät). N diskrete Buchungsgelegenheiten (Standardformulierung der
Revenue-Management-Literatur); je Epoche kommt mit Wahrscheinlichkeit π_hi(n) eine Premium-Anfrage, mit π_lo(n) eine Spot-Anfrage, sonst keine – beide Wahrscheinlichkeiten wandern über die Epochen
(Spot früh häufiger, Premium spät häufiger). Jede Anfrage muss **sofort** angenommen oder abgelehnt werden (online), ohne die Zukunft zu kennen. Kein No-Show/Overbooking, nur zwei Frachtklassen,
Nachfragewahrscheinlichkeiten exakt bekannt (kein Prognosefehler in Version 1). Formal im Expander „📐 Mathematische Formulierung“ der App.

## Methodik – drei Bausteine statt einer Reglerfamilie

Wie bei den vorherigen Wellen sind das drei Bausteine, kein stetiger Regler – aber anders als dort ist die operative Empfehlung **nicht** der Exakt-Baustein:

- **🐌 FCFS**: nimmt jede Anfrage an, solange ein Slot frei ist, ohne auf die Preisklasse zu achten – die **Kontrast-Baseline**.
- **📐 Littlewood**: geschlossene Schutzformel (1972), schützt Kapazität für erwartete künftige Premium-Nachfrage – die **operative Empfehlung der Hauptansicht**, praktisch optimal, ohne
  Rückwärts-Induktion.
- **🎯 DP (exakt)**: Rückwärts-Induktion über (Epoche, Restkapazität) – das echte Online-Optimum, aber nur die **Referenz im Exakt-Tab**, beweist wie nah Littlewood herankommt.

Zusätzlich ein **Hindsight-Orakel** (rückblickend beste Auswahl, keine online umsetzbare Politik) als vierte, sekundäre Kurve im Vergleichs-Tab („Wert von Information“).

**Kernlogik unverändert übernommen**: `rvm_scenario.py` (`make_periods`, `draw_sequence`) und `rvm_solve.py` (`dp_optimal`, `dp_accept`, `remaining_hi_dists`, `littlewood_protection_levels`,
`simulate`, `hindsight_oracle`) sind direkt aus `seefracht-planung/messreihe_revenue/revenue.py` übernommen – bereits gegen eine Handinstanz und mehrere Konsistenzchecks verifiziert
(`messreihe_revenue/check.py`: 0 Abweichungen). Reine Standardbibliothek, kein scipy nötig (anders als Welle 3).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen mit `python -m pytest tests/` nachvollziehbar (`test_evaluation.py`, `test_preset_stories.py`); Population = 600 Stichproben (30 Nachfragekurven-Seeds × 20 gezogene Sequenzen je Kurve),
reproduziert `seefracht-planung/messreihe_revenue/sweep_data.json` **exakt** (nicht nur auf Marge), da die Kernlogik unverändert übernommen wurde.

| Frage | Befund | Test |
|---|---|---|
| Lässt FCFS wirklich Ertrag liegen? | Ja, und stark kapazitätsabhängig: knapp (C=4) −36,0 %, Standard (C=7) −15,3 %, reichlich (C=12) −0,9 % gegenüber DP | `test_preset_stories.py`, `test_evaluation.py` |
| Ist Littlewoods 1972er-Formel praktisch optimal? | Ja, über alle 5 Presets zwischen −0,06 % und −1,29 % vom DP-Optimum entfernt – keine Rückwärts-Induktion in der Hauptansicht nötig | `test_preset_stories.py` |
| Ist das Preisverhältnis der zweite starke Hebel? | Ja: kleiner Aufschlag (1,25×) FCFS nur −2,6 %, großer Aufschlag (5×) FCFS **−31,4 %** | `test_evaluation.py` |
| Dominiert Hindsight immer jede Politik auf derselben Sequenz? | Ja, harte Invariante: 0 Verletzungen in 600 Politik-Anwendungen | `test_solve.py::test_hindsight_dominates_every_policy_on_the_same_sequence` |
| Stimmt der DP-Theoriewert mit dem simulierten Mittel überein? | Ja, innerhalb von 4 Standardfehlern über 2000 Stichproben | `test_solve.py::test_dp_theoretical_value_matches_simulated_mean_over_many_samples` |
| Ist DP im Mittel nie schlechter als Littlewood/FCFS? | Ja, 0 Verletzungen über 10 Instanzen à 400 Stichproben – **nur im Erwartungswert**, nicht pfadweise | `test_solve.py::test_dp_is_never_worse_than_littlewood_or_fcfs_in_expectation` |
| Handinstanz: Spot sicher zuerst, Premium sicher danach, Kapazität 1? | DP verwirft den Spot korrekt, Erwartungswert = r_hi exakt (900,0) | `test_solve.py::test_hand_instance_rejects_the_sure_spot_to_protect_the_sure_premium` |

## Ehrliche Grenzen

- **Kein No-Show/Overbooking** – das klassische Littlewood-Modell (1972) ohne Ausfallquote, um den Klassenschutz-Effekt sauber zu isolieren.
- **Nur zwei Frachtklassen** – Littlewoods Formel ist für genau diesen Fall bewiesen nah-optimal; mit mehr Klassen bräuchte es EMSR-b o. Ä.
- **Nachfragewahrscheinlichkeiten exakt bekannt**, kein Prognosefehler – widerspricht der ursprünglich vorgesehenen OR+ML-Positionierung dieser Welle; der natürliche ML-Baustein für eine
  Folgeversion (geschätzte statt bekannte π-Kurven), hier bewusst nicht umgesetzt.
- **Nachfragekurven synthetisch**, nicht an echten Buchungsdaten kalibriert.
- **Keine dynamische Preisanpassung** – nur Annahme/Ablehnung, keine Preisänderung.
- DP-Optimalität gilt nur **im Erwartungswert** über die Zukunftsunsicherheit an jedem Entscheidungspunkt, nicht pfadweise für eine einzelne realisierte Sequenz – eine ungünstige Zufallssequenz kann
  eine „suboptimale“ Politik im Einzelfall trotzdem besser aussehen lassen als DP.

## Tests

`python -m pytest tests/ -v` – 130 Tests, rund 23 Sekunden. Zusammensetzung:

- **Szenario** (`test_scenario.py`): Determinismus, Struktur der Nachfragekurve/Sequenz, Nachfrage-Trend (Premium steigt, Spot fällt), Randfälle (0/1 Epochen, extreme π-Werte gegen das
  Sicherheitsnetz der Wahrscheinlichkeits-Clamps).
- **Politiken/Löser** (`test_solve.py`): Handinstanz als fester Regressionstest, **Hindsight-Dominanz** (harte pfadweise Invariante, 600 Politik-Anwendungen), DP-Theoriewert gegen simuliertes Mittel
  (2000 Stichproben), DP im Erwartungswert nie schlechter als Littlewood/FCFS (statistisch, **nicht** pfadweise), Randfälle (Kapazität 0, sehr große Kapazität, Preisverhältnis 1, 0 Epochen),
  Struktur der Littlewood-Schutzniveaus (nicht steigend, Boundary-Test tail<=ratio exakt).
- **Auswertung** (`test_evaluation.py`): Population reproduziert `sweep_data.json` exakt (nicht nur auf Marge), Beispielsequenz reproduziert `sweep_data.json` exakt, Kapazitätsvergleich, gepaartes
  Urteil (inkl. exaktem Schwellenwert-Test bei genau zwei Standardfehlern), Randfall Kapazität 0 (Division durch 0 abgefangen – beim Bau gefundener Bug, siehe unten).
- **Regler** (`test_presets.py`): Permalink-Parsing/-Klemmen/-Runden (inkl. Stufen-Regler auf die nächste Stufe), Presets innerhalb ihrer eigenen Grenzen, Seeds außerhalb der Population.
- **Presets** (`test_stories.py`, `test_preset_stories.py`): jedes einzelne Kriterium an künstlichen Werten, die genau an seiner Schwelle kippen; echte Presets erfüllen Population- UND
  Sequenz-Kriterien; Reproduktion von `sweep_data.json` auf ±0,5 Prozentpunkte.
- **Unabhängige Orakel** (`test_oracle_rvm.py`): DP-Wertfunktion gegen den Bellman-LP (`scipy.optimize.linprog`) und gegen Brute Force über alle Markov-Politiken, Littlewood-Schutzniveaus gegen exakte Bruch-Arithmetik, exakter Erwartungsertrag jeder Politik per Markov-Kette (DP erreicht `V[0][C]`, FCFS/Littlewood liegen darunter), Ertrag der fünf Preset-Sequenzen unabhängig nachgespielt. Exakt gerechnet liegt FCFS im Standard-Preset bei −14,7 % (Population aus 600 Stichproben: −15,3 %), bei knapper Kapazität bei −35,4 % (−36,0 %): die Tabellenwerte sind Stichprobenwerte mit etwa ±0,7 Prozentpunkten Unsicherheit.
- **Figuren** (`test_visualization.py`): Zeitleiste, Kapazitätsvergleich – alle Achsen fest (`fixedrange`).
- **PDF** (`test_pdf_export.py`): Sonderzeichen-Bereinigung (fpdf2 stürzt bei „–“, „€“, Emoji ab), Randfälle (Kapazität 0, großer Preisaufschlag).
- **End-to-End** (`test_app.py`, AppTest): Skelett und Footer, jedes Preset, Permalink, alle Regler an Min und Max, die bedingte Meldung in beiden Zuständen, Urteil in allen Zuständen,
  Vergleichstabelle, PDF, Texte, dass Littlewood (nicht DP) als Empfehlung im Text steht.

Zusätzlich ein Fehler-Einbau-Test (`tools/mutation_check.py`, 25 Mutanten über `rvm_scenario`, `rvm_solve`, `rvm_evaluation`, `rvm_presets`, `rvm_stories`): **24 gefunden, 1 überlebt, 0 Fehler in der
Mutantenliste.** Der eine Überlebende ist gleichwertig (kein sichtbarer Unterschied im Verhalten): `dp_accept`s Tie-Break (`>=` → `>`) trifft nur den exakten Indifferenzpunkt
`fare + V[n+1][c-1] == V[n+1][c]` – dort liefern Annehmen und Ablehnen per Definition denselben Erwartungswert, die DP-Wertfunktion ist an dieser Stelle unabhängig von der Wahl.

## Dateistruktur

| Datei | Inhalt | Herkunft |
|---|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets, Sidebar, Hauptansicht, Kernabschnitt, Bausteine im Vergleich, Texte | neu |
| `rvm_constants.py` | Regler-Grenzen, `PRESETS`, Bausteine, Farben, feste Modellparameter | neu |
| `rvm_presets.py` | `SETTING_SPECS`, Permalink (Bereiche und Stufenlisten), Presets, Seed-Knopf | Muster `mhs_presets.py` |
| `rvm_scenario.py` | Nachfragekurve, Sequenz (`make_periods`, `draw_sequence`) | `messreihe_revenue/revenue.py`, unverändert |
| `rvm_solve.py` | DP, Littlewood-Formel, Simulation, Hindsight-Orakel | `messreihe_revenue/revenue.py`, unverändert |
| `rvm_evaluation.py` | Eine Sequenz lösen/simulieren, Population (Preset-Abnahme), Kapazitätsvergleich, gepaartes Urteil | Muster `mhs_evaluation.py` |
| `rvm_visualization.py` | Zeitleiste, Kapazitätsvergleich-Balken (alle Achsen fest) | Muster `mhs_visualization.py` |
| `rvm_ui_panel.py` | Kennzahlen (2×2), Zeitleiste, Baustein-Tabs | Muster `mhs_ui_panel.py` |
| `rvm_pdf_export.py` | PDF-Export (`fpdf2`, Sonderzeichen-Bereinigung) | Muster `mhs_pdf_export.py` |
| `rvm_stories.py` | Abnahmekriterien der Presets (Population UND gezeigte Sequenz) | Muster `mhs_stories.py` |
| `tools/tune_presets.py`, `tools/PRESET_SWEEP.md` | Preset-Abstimmung und ihr Bericht | neu |
| `tools/mutation_check.py` | Fehler-Einbau-Test | neu |
| `tests/` | siehe oben | neu |

## Bewusst nicht umgesetzt (mögliche Erweiterungen)

- **Overbooking/No-Show** (Newsvendor-artige Buchungslimit-Formel) – eigene Vorab-Messreihe wert, würde den sauberen Klassenschutz-Befund verwässern.
- **Mehr als zwei Frachtklassen** (EMSR-b o. Ä. statt der geschlossenen Littlewood-Formel).
- **Prognoseunschärfe** (geschätzte statt bekannte π-Kurven) – der natürliche ML-Baustein für eine Folgeversion, passt zur OR+ML-Positionierung des Portfolios.
- **Kalibrierung an echten Buchungsdaten** statt synthetischer Nachfragekurven.
- **Dynamische Preisanpassung** statt reiner Annahme/Ablehnung.

## Lokal ausführen

```bash
pip install -r requirements-dev.txt
streamlit run app.py
```

Tests: `python -m pytest tests/ -v`. Preset-Abstimmung: `python tools/tune_presets.py population|seeds`. Fehler-Einbau: `python tools/mutation_check.py`.

---

Gebaut mit Streamlit, Plotly und fpdf2.

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zum Thema: [Seefracht optimieren](https://sebastianhanisch.net/seefracht-optimierung.html).
