"""
Buchungs-/Slot-Vergabe (Revenue Management) - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Welle 4 (letzte) der Seefracht-Linie: welche Buchungen soll eine Reederei annehmen, wenn Container-
Slots knapp sind und zwei Frachtklassen um sie konkurrieren - guenstige "Spot"-Fracht, die frueh bucht,
und teure "Premium"-Fracht, die erst spaet bucht? Anders als bei den ersten drei Wellen ist die exakte
DP-Loesung hier NICHT die Hauptempfehlung: Littlewoods klassische, 1972 hergeleitete geschlossene
Formel kommt verblueffend nah ans DP-Optimum und ist die operative Empfehlung der Hauptansicht; DP
dient nur als Referenz im Exakt-Tab.

Lauffaehig mit: streamlit run app.py
"""
import streamlit as st

import rvm_constants as C
import rvm_evaluation as E
import rvm_visualization as VZ
from rvm_pdf_export import generate_rvm_pdf
from rvm_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings,
                         options, randomize_seed, SETTING_SPECS, sync_query_params)
from rvm_ui_panel import render_comparison_tab, render_exact_panel, render_metrics, render_policy_panel, render_timeline

st.set_page_config(page_title="Buchungs-/Slot-Vergabe – Sebastian Hanisch", layout="wide")

SCENARIO_KEYS = list(SETTING_SPECS)
FCFS_GAP_MESSAGE_THRESHOLD = -10.0   # ab hier "lohnt sich Klassenschutz deutlich" (Standard-Preset-Schwelle)


@st.cache_data(show_spinner=False, max_entries=64)
def _demand_curve(n_epochs, pi_hi_max, pi_lo_max, seed):
    return E.demand_curve(n_epochs, pi_hi_max, pi_lo_max, seed)


@st.cache_data(show_spinner=False, max_entries=64)
def _solve(n_epochs, capacity, r_hi, r_lo, pi_hi_max, pi_lo_max, seed):
    pi_hi, pi_lo = _demand_curve(n_epochs, pi_hi_max, pi_lo_max, seed)
    cfg = E.Config(n_epochs=n_epochs, capacity=capacity, r_hi=r_hi, r_lo=r_lo)
    return cfg, pi_hi, pi_lo, E.solve_curve(cfg, pi_hi, pi_lo)


@st.cache_data(show_spinner=False, max_entries=64)
def _shown(n_epochs, capacity, r_hi, r_lo, pi_hi_max, pi_lo_max, seed):
    cfg, pi_hi, pi_lo, solved = _solve(n_epochs, capacity, r_hi, r_lo, pi_hi_max, pi_lo_max, seed)
    return E.evaluate_sequence(cfg, pi_hi, pi_lo, solved, seed)


@st.cache_data(show_spinner=False, max_entries=32)
def _population_600(n_epochs, capacity, r_hi, r_lo, pi_hi_max, pi_lo_max):
    cfg = E.Config(n_epochs=n_epochs, capacity=capacity, r_hi=r_hi, r_lo=r_lo)
    return E.population_stats(cfg, pi_hi_max, pi_lo_max)


@st.cache_data(show_spinner=False, max_entries=32)
def _population_30(n_epochs, capacity, r_hi, r_lo, pi_hi_max, pi_lo_max):
    cfg = E.Config(n_epochs=n_epochs, capacity=capacity, r_hi=r_hi, r_lo=r_lo)
    return E.population_stats(cfg, pi_hi_max, pi_lo_max, n_curve_seeds=C.SAMPLE_INSTANCES, draws_per_seed=1)


@st.cache_data(show_spinner=False, max_entries=32)
def _capacity_sweep(n_epochs, r_hi, r_lo, pi_hi_max, pi_lo_max, capacity):
    return E.capacity_sweep(n_epochs, r_hi, r_lo, pi_hi_max, pi_lo_max, capacity)


st.title("🎟️ Buchungs-/Slot-Vergabe: Wer bekommt den letzten Container-Slot?")
st.markdown(
    """
Eine Reederei nimmt Buchungen über Wochen hinweg an, aber die Container-Slots sind knapp: **Spot-Fracht** (günstig) bucht meist früh, **Premium-Fracht** (teuer) meist erst kurz vor Abfahrt. Wer früh
jede Anfrage annimmt, hat am Ende keinen Platz mehr für die teuren Spätbucher - der klassische **Klassenschutz**-Effekt der Revenue-Management-Literatur (Littlewood 1972). Wie das Modell funktioniert,
steht im Expander „Wie funktioniert diese Demo?“ weiter unten, die formale Beschreibung im Expander „📐 Mathematische Formulierung“.
"""
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Standard": "Der Grundfall: FCFS lässt bereits spürbar Ertrag liegen.",
    "Knappe Kapazität": "Der dramatischste Fall der ganzen Seefracht-Linie: mehr als ein Drittel Ertrag verschenkt.",
    "Reichliche Kapazität": "Genug Platz für alle - bewusst der unspektakuläre Referenzfall, Klassenschutz bringt kaum etwas.",
    "Kleiner Preisaufschlag": "Fast gleicher Preis für beide Klassen - Klassenschutz lohnt sich kaum.",
    "Großer Preisaufschlag": "Premium ist fünfmal so teuer wie Spot - Klassenschutz wird fast so wichtig wie bei knapper Kapazität.",
}
preset_names = list(C.PRESETS.keys())
for row in (preset_names[:3], preset_names[3:]):
    cols = st.columns(3)
    for col, name in zip(cols, row):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    capacity = st.slider("Slots (Kapazität)", *bounds("capacity_slider"), key="capacity_slider",
                         help="Wie viele Container-Slots insgesamt vergeben werden.")
    r_hi_mult = st.select_slider("Premium-Preisaufschlag", options("r_hi_mult_select"), key="r_hi_mult_select",
                                 help=f"Vielfaches des Spot-Preises (r_lo={C.R_LO:.0f}); steuert r_hi.")
    demand_mix = st.select_slider("Nachfragemix (Premium/Spot)", options("demand_mix_select"), key="demand_mix_select",
                                  help="premium-arm/ausgewogen/premium-reich - steuert die maximale Ankunftswahrscheinlichkeit je Klasse.")
    n_epochs = st.slider("Buchungsfenster (Epochen)", *bounds("n_epochs_slider"), key="n_epochs_slider",
                         help="Länge der Buchungsperiode vor Abfahrt (diskrete Buchungsgelegenheiten).")
    seed = st.number_input("Seed", *bounds("seed_input"), key="seed_input", step=1,
                           help="Bestimmt Nachfragekurve und die gezeigte Buchungssequenz.")
    st.button("🎲 Neue Buchungssequenz", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Seed.")

sync_query_params({key: st.session_state[key] for key in SCENARIO_KEYS})

capacity, n_epochs, seed = int(capacity), int(n_epochs), int(seed)
r_hi_mult = float(r_hi_mult)
r_hi = r_hi_mult * C.R_LO
pi_hi_max, pi_lo_max = C.DEMAND_MIX_PARAMS[demand_mix]

shown = _shown(n_epochs, capacity, r_hi, C.R_LO, pi_hi_max, pi_lo_max, seed)
stats_600 = _population_600(n_epochs, capacity, r_hi, C.R_LO, pi_hi_max, pi_lo_max)
stats_30 = _population_30(n_epochs, capacity, r_hi, C.R_LO, pi_hi_max, pi_lo_max)
verdict = E.verdict_from_population(stats_30)
cap_stats = _capacity_sweep(n_epochs, r_hi, C.R_LO, pi_hi_max, pi_lo_max, capacity)

# ---------------------------------------------------------------------------------------------------
# Hauptansicht
# ---------------------------------------------------------------------------------------------------
st.markdown("## 🎯 Wie viel Ertrag lässt reines Windhundprinzip liegen?")
st.caption(f"{capacity} Slots, Preisverhältnis {r_hi_mult:g}x (Premium {r_hi:.0f} / Spot {C.R_LO:.0f}), "
          f"Nachfragemix {demand_mix}, {n_epochs} Epochen, Seed {seed}.")

metric_rows = [st.columns(2), st.columns(2)]
render_metrics(metric_rows[0] + metric_rows[1], shown)

if stats_600.fcfs_gap_pct <= FCFS_GAP_MESSAGE_THRESHOLD:
    st.success(f"✅ FCFS liegt bei dieser Einstellung im Mittel **{stats_600.fcfs_gap_pct:+.2f} %** unter dem "
              f"DP-Optimum - hier lohnt sich Klassenschutz deutlich.")
else:
    st.info(f"ℹ️ FCFS liegt bei dieser Einstellung im Mittel nur **{stats_600.fcfs_gap_pct:+.2f} %** unter dem "
           f"DP-Optimum - bei dieser Einstellung macht Windhundprinzip kaum einen Unterschied.")

st.markdown("#### 🕐 Buchungssequenz: FCFS gegen Littlewood")
render_timeline("main_timeline_chart", shown)

pdf_slot = st.container()

st.markdown("---")

# ---------------------------------------------------------------------------------------------------
# Kernabschnitt
# ---------------------------------------------------------------------------------------------------
st.markdown("### 📐 Wie stark hängt die Lücke von Kapazität und Preisaufschlag ab?")
st.markdown(
    """
Kernfrage dieser Demo: wie sehr wächst der Ertragsverlust von FCFS mit knapper werdender Kapazität - und wie nah bleibt Littlewoods geschlossene Formel dabei am DP-Optimum? Balken: FCFS- und
Littlewood-Aufschlag gegen das DP-Optimum über drei Kapazitätsstufen um den eingestellten Wert.
"""
)
st.plotly_chart(VZ.capacity_sweep_figure(cap_stats, capacity), width="stretch", key="main_capacity_chart")
st.caption(f"Basis: {C.SAMPLE_INSTANCES} Sequenzen derselben Einstellung je Kapazitätsstufe (nicht der eingestellte "
          f"Seed). Rechenzeit gemessen: DP + Littlewood-Formel zusammen brauchen selbst beim größten Regler-Stand "
          f"({C.N_EPOCHS_RANGE[1]} Epochen, {C.CAPACITY_RANGE[1]} Slots) nur etwa 1 ms (Entwicklungsrechner, maschinenabhängig) - ohne Knopf möglich, "
          f"live bei jedem Reglerzug.")

st.markdown(f"**Urteil in drei Zuständen** (gepaarte Differenz über {C.SAMPLE_INSTANCES} Stichprobensequenzen "
           f"gleicher Einstellung, > {C.VERDICT_Z:.0f} Standardfehler): Littlewood gegen FCFS")
if verdict.n == 0:
    st.info("ℹ️ Kein Vergleich möglich: keine Stichprobensequenz verfügbar.")
elif verdict.kind == "better":
    st.success(f"✅ **Littlewood gegen FCFS**: im Mittel **{abs(verdict.diff):.2f} mehr Ertrag** je Sequenz "
              f"(Differenz {verdict.diff:+.2f}, Standardfehler {verdict.se:.2f}, n={verdict.n}).")
elif verdict.kind == "worse":
    st.warning(f"⚠️ **Littlewood gegen FCFS**: im Mittel **{abs(verdict.diff):.2f} weniger Ertrag** je Sequenz "
              f"(Differenz {verdict.diff:+.2f}, Standardfehler {verdict.se:.2f}, n={verdict.n}).")
else:
    st.info(f"ℹ️ Kein klarer Unterschied zwischen Littlewood und FCFS bei dieser Einstellung (Differenz "
           f"{verdict.diff:+.2f}, Standardfehler {verdict.se:.2f}, n={verdict.n}).")

with pdf_slot:
    st.download_button(
        "📄 Ergebnis als PDF herunterladen",
        data=generate_rvm_pdf(capacity, n_epochs, r_hi, C.R_LO, demand_mix, seed, shown, stats_600, verdict),
        file_name="revenue_management_ergebnis.pdf", mime="application/pdf", key="primary_pdf_download",
        help="Einstellungen, Ertrag je Politik, Vergleichstabelle, Population und Urteil.")

st.markdown("---")

# ---------------------------------------------------------------------------------------------------
# Bausteine im Vergleich
# ---------------------------------------------------------------------------------------------------
with st.expander("🔧 Wie wir das erreichen – Politiken im Vergleich"):
    tabs = st.tabs([C.POLICY_LABELS[C.POLICY_FCFS], C.POLICY_LABELS[C.POLICY_LITTLEWOOD], C.EXACT_TAB_LABEL,
                   C.COMPARISON_TAB_LABEL])
    with tabs[0]:
        render_policy_panel("tab_fcfs", C.POLICY_FCFS, shown)
    with tabs[1]:
        render_policy_panel("tab_littlewood", C.POLICY_LITTLEWOOD, shown)
    with tabs[2]:
        render_exact_panel(shown, stats_600)
    with tabs[3]:
        render_comparison_tab(shown, cap_stats, capacity)

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        """
**Spot und Premium.** Zwei Frachtklassen bewerben sich laufend um Container-Slots: **Spot** (niedriger Preis, bucht überwiegend früh) und **Premium** (hoher Preis, bucht überwiegend spät). N diskrete
Buchungsgelegenheiten (Epochen); je Epoche kommt mit Wahrscheinlichkeit π_hi(n) eine Premium-Anfrage, mit π_lo(n) eine Spot-Anfrage, sonst keine - beide Wahrscheinlichkeiten wandern über die Epochen
(Spot früh häufiger, Premium spät häufiger). Jede Anfrage muss **sofort** angenommen oder abgelehnt werden (online), ohne die Zukunft zu kennen.

**Littlewoods Schutzformel und warum sie fast reicht.** Spot wird nur angenommen, wenn die verbleibende Kapazität über dem Schutzniveau für erwartete künftige Premium-Nachfrage liegt (geschlossene
Formel, 1972). Sie kommt empirisch verblüffend nah ans echte DP-Optimum (in den fünf Presets -0,06 % bis -1,29 %; über das gesamte Reglerraster bei 30 Epochen zwischen etwa +0,1 % und -5 %, am weitesten bei knapper Kapazität und premium-armer Nachfrage) - die eigentliche Botschaft dieser Demo: man braucht fast nie die volle
Rückwärts-Induktion.

**Warum FCFS bei knapper Kapazität und großem Preisunterschied am meisten verliert.** FCFS füllt die Slots blind mit den früh eintreffenden Spot-Buchungen und muss danach jede Premium-Anfrage
ablehnen - siehe die Zeitleiste oben und den Kernabschnitt (die Lücke lebt an der Kapazitätsgrenze, nicht im komfortablen Bereich).

**Grenzen dieses Modells** (bewusst so gewählt, damit die Aussage ehrlich bleibt):

- **Kein No-Show/Overbooking** - das klassische Littlewood-Modell (1972) ohne Ausfallquote, um den Klassenschutz-Effekt sauber zu isolieren.
- **Nur zwei Frachtklassen** - Littlewoods Formel ist für genau diesen Fall bewiesen nah-optimal.
- **Nachfragewahrscheinlichkeiten exakt bekannt**, kein Prognosefehler - der natürliche ML-Baustein für eine spätere Version, hier nicht getestet.
- **Nachfragekurven synthetisch**, nicht an echten Buchungsdaten kalibriert.
- **Keine dynamische Preisanpassung** - nur Annahme/Ablehnung, keine Preisänderung.
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Epochen und Ankünfte.** Epoche $n \in \{0, \dots, N-1\}$; mit Wahrscheinlichkeit $\pi_{hi}(n)$ trifft eine Premium-Anfrage ein (Preis $r_{hi}$), mit $\pi_{lo}(n)$ eine Spot-Anfrage (Preis $r_{lo}$),
sonst keine.

**Littlewoods Regel (1972).** Spot bei Restkapazität $c$ nur annehmen, wenn $c > y^\ast(n)$; $y^\ast(n)$ ist das kleinste $y$ mit $P(\text{verbleibende Premium-Nachfrage ab } n > y) \leq r_{lo} / r_{hi}$.

**DP (exakt).** $V(n, c) = \pi_{hi}(n) \cdot \max(r_{hi} + V(n+1, c-1),\, V(n+1, c)) + \pi_{lo}(n) \cdot \max(r_{lo} + V(n+1, c-1),\, V(n+1, c)) + (\text{Rest}) \cdot V(n+1, c)$, mit $V(N, \cdot) = 0$.
$V(0, C)$ ist der optimale erwartete Gesamtertrag; DP ist nur im **Erwartungswert** an jedem Entscheidungspunkt optimal, nicht pfadweise für eine einzelne realisierte Sequenz.

**Handinstanz.** Zwei Epochen, Epoche 0 sicher Spot, Epoche 1 sicher Premium, Kapazität 1: DP verwirft den Spot korrekt in Epoche 0, um die Kapazität für die sichere Premium-Anfrage zu schützen -
Erwartungswert $= r_{hi}$ exakt (`tests/test_solve.py`, portiert aus `messreihe_revenue/check.py`).

**Hindsight-Orakel.** Rückblickend beste Auswahl: alle eingetroffenen Anfragen nach Preis sortiert, die besten $C$ nehmen - keine online umsetzbare Politik, nur obere Schranke für den Wert von Information.

Implementiert in `rvm_scenario.py` (Nachfragekurve, Sequenz), `rvm_solve.py` (DP, Littlewood-Formel, Simulation, Hindsight) und `rvm_evaluation.py` (Population, Kapazitätsvergleich, Urteil).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zum Thema: [Seefracht optimieren](https://sebastianhanisch.net/seefracht-optimierung.html)."
)
