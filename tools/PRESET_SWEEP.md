# Preset-Abstimmung (Buchungs-/Slot-Vergabe)

`python tools/tune_presets.py population` — Population-Kriterien (30 Nachfragekurven-Seeds x 20 gezogene
Sequenzen je Kurve = 600 Stichproben, Seeds 0..29) aller fuenf Presets, direkt aus `plan_revenue.html`
Abschnitt 7 uebernommen. Ergebnis (2026-09-23): **alle fuenf Presets erfuellen ihre Kriterien**, und die
gemessenen Werte reproduzieren `seefracht-planung/messreihe_revenue/sweep_data.json` exakt (dieselbe
Kernlogik, unveraendert uebernommen):

| Preset | FCFS-Aufschlag | Littlewood-Aufschlag |
|---|---|---|
| Standard | -15,29 % (Kriterium <= -10 %) | -1,29 % (Kriterium >= -3 %) |
| Knappe Kapazität | -35,96 % (Kriterium <= -25 %) | -0,22 % (Kriterium >= -3 %) |
| Reichliche Kapazität | -0,89 % (Kriterium >= -3 %) | -0,06 % (Kriterium >= -1 %) |
| Kleiner Preisaufschlag | -2,64 % (Kriterium >= -5 %) | — |
| Großer Preisaufschlag | -31,44 % (Kriterium <= -20 %) | -0,95 % (Kriterium >= -3 %) |

Die Population haengt NICHT vom Preset-Seed ab (immer Kurven-Seeds 0..29) - der Seed bestimmt nur, welche
EINE Sequenz beim Laden des Presets angezeigt wird.

`python tools/tune_presets.py seeds` — sucht je Preset einen Seed >= 30 (außerhalb der Population), der
`rvm_stories.shown_criteria()` erfuellt, und waehlt darunter NICHT den dramatischsten Kontrast, sondern
den mit FCFS-/Littlewood-/DP-Ertrag am naechsten am Populationsmittel (kein Cherry-Picking). Suchbereich
Seeds 30..829 (800 Seeds). Ergebnis:

| Preset | traegt an X/800 Seeds | gewaehlter Seed | FCFS | Littlewood | DP |
|---|---|---|---|---|---|
| Standard | 320/800 | 95 | 3800,0 | 4400,0 | 4400,0 |
| Knappe Kapazität | 626/800 | 54 | 2100,0 | 3100,0 | 3100,0 |
| Reichliche Kapazität | 718/800 | 53 | 6000,0 | 6000,0 | 6000,0 |
| Kleiner Preisaufschlag | 759/800 | 41 | 3000,0 | 3000,0 | 3000,0 |
| Großer Preisaufschlag | 433/800 | 69 | 6000,0 | 8800,0 | 8800,0 |

Diese Seeds stehen in `rvm_constants.PRESETS`. `tests/test_preset_stories.py` prueft beide
Kriterienfunktionen gegen die tatsaechlich geladenen Presets, `tests/test_stories.py` prueft jedes
einzelne Kriterium an kuenstlichen Werten, die genau an seiner Schwelle kippen.
