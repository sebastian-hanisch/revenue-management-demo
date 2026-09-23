"""Abnahmekriterien der Presets (Detailplan plan_revenue.html, Abschnitt 7): welche Geschichte erzaehlt
jedes Beispielszenario, und woran erkennt man, dass sie traegt?

Einzige Quelle fuer `tools/tune_presets.py` (Abstimmung) und `tests/test_preset_stories.py` (Abnahme).
Zwei getrennte Kriterien-Funktionen (Muster mhs_stories.py):

- `criteria()`: Population-Kriterien ueber den Ertrags-Abstand zum DP-Optimum (fcfs_gap_pct,
  littlewood_gap_pct), gemessen ueber die volle Population (30 Nachfragekurven x 20 Sequenzen = 600,
  reproduziert sweep_data.json) - direkt aus dem Detailplan Abschnitt 7 uebernommen. Haengt NICHT vom
  Preset-Seed ab (die Population wird immer ueber Kurven-Seeds 0..29 gezogen).
- `shown_criteria()`: Kriterien an der EINEN gezeigten Sequenz (Preset-Seed) - zeigt sie den
  behaupteten Kontrast zwischen FCFS und Littlewood, ohne der dramatischste Einzelfall zu sein
  (tools/tune_presets.py waehlt den Seed am naechsten am Populationsmittel, kein Cherry-Picking)."""
import rvm_constants as C


def _pct(v):
    return f"{v:+.2f} %"


def criteria(name, stats):
    """stats: rvm_evaluation.PopulationStats. Rueckgabe: Liste (erfuellt, Text)."""
    fg, lg = stats.fcfs_gap_pct, stats.littlewood_gap_pct
    if name == "Standard":
        return [(fg <= -10.0, f"FCFS-Aufschlag <= -10 %: {_pct(fg)}"),
                (lg >= -3.0, f"Littlewood-Aufschlag >= -3 %: {_pct(lg)}")]
    if name == "Knappe Kapazität":
        return [(fg <= -25.0, f"FCFS-Aufschlag <= -25 %: {_pct(fg)}"),
                (lg >= -3.0, f"Littlewood-Aufschlag >= -3 %: {_pct(lg)}")]
    if name == "Reichliche Kapazität":
        return [(fg >= -3.0, f"FCFS-Aufschlag >= -3 %: {_pct(fg)}"),
                (lg >= -1.0, f"Littlewood-Aufschlag >= -1 %: {_pct(lg)}")]
    if name == "Kleiner Preisaufschlag":
        return [(fg >= -5.0, f"FCFS-Aufschlag >= -5 %: {_pct(fg)}")]
    if name == "Großer Preisaufschlag":
        return [(fg <= -20.0, f"FCFS-Aufschlag <= -20 %: {_pct(fg)}"),
                (lg >= -3.0, f"Littlewood-Aufschlag >= -3 %: {_pct(lg)}")]
    raise KeyError(name)


def shown_criteria(name, shown):
    """shown: rvm_evaluation.SequenceResult (die eine gezeigte Sequenz). Zeigt sie auf dieser EINEN
    Sequenz den behaupteten Kontrast zwischen FCFS und Littlewood?"""
    fcfs, lit, dp = shown.revenue[C.POLICY_FCFS], shown.revenue[C.POLICY_LITTLEWOOD], shown.revenue[C.POLICY_DP]
    fg = (fcfs / dp - 1) * 100 if dp else 0.0
    lg = (lit / dp - 1) * 100 if dp else 0.0
    if name == "Standard":
        return [(fg <= -5.0, f"FCFS auf der gezeigten Sequenz spürbar unter DP: {_pct(fg)}"),
                (lg >= -5.0, f"Littlewood nah am DP-Optimum: {_pct(lg)}")]
    if name == "Knappe Kapazität":
        return [(fg <= -15.0, f"FCFS auf der gezeigten Sequenz deutlich unter DP: {_pct(fg)}"),
                (lg >= -5.0, f"Littlewood nah am DP-Optimum: {_pct(lg)}")]
    if name == "Reichliche Kapazität":
        return [(fg >= -5.0, f"FCFS auf der gezeigten Sequenz nah am DP-Optimum: {_pct(fg)}"),
                (lg >= -2.0, f"Littlewood praktisch optimal: {_pct(lg)}")]
    if name == "Kleiner Preisaufschlag":
        return [(fg >= -8.0, f"FCFS auf der gezeigten Sequenz nah am DP-Optimum: {_pct(fg)}")]
    if name == "Großer Preisaufschlag":
        return [(fg <= -12.0, f"FCFS auf der gezeigten Sequenz deutlich unter DP: {_pct(fg)}"),
                (lg >= -5.0, f"Littlewood nah am DP-Optimum: {_pct(lg)}")]
    raise KeyError(name)
