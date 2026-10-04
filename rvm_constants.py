"""Konstanten der Buchungs-/Slot-Vergabe-Demo (Welle 4, letzte der Seefracht-Linie).

Modell und Zahlen aus messreihe_revenue/ (siehe seefracht-planung/plan_revenue.html, ERGEBNIS.md).
Presets werden mit tools/tune_presets.py gegen die Abnahmekriterien in rvm_stories.py geprueft; die
Population-Stichprobe (30 Nachfragekurven-Seeds x 20 gezogene Sequenzen = 600) reproduziert
sweep_data.json (siehe tools/PRESET_SWEEP.md)."""

# --- Regler --------------------------------------------------------------------------------------------
CAPACITY_RANGE, CAPACITY_DEFAULT = (3, 15), 7
N_EPOCHS_RANGE, N_EPOCHS_DEFAULT = (15, 60), 30
SEED_RANGE, SEED_DEFAULT = (0, 9999), 0

R_LO = 400.0  # fester Spot-Preis; der Premium-Preis ergibt sich aus dem Preisaufschlag-Regler
R_HI_MULT_OPTIONS = (1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)
R_HI_MULT_DEFAULT = 2.25

DEMAND_MIX_OPTIONS = ("premium-arm", "ausgewogen", "premium-reich")
DEMAND_MIX_DEFAULT = "ausgewogen"
# pi_hi_max, pi_lo_max je Nachfragemix-Stufe; "ausgewogen" reproduziert die Messreihen-cfg (0.25/0.35)
DEMAND_MIX_PARAMS = {
    "premium-arm": (0.15, 0.45),
    "ausgewogen": (0.25, 0.35),
    "premium-reich": (0.35, 0.25),
}

# --- Auswertung -----------------------------------------------------------------------------------------
POPULATION_CURVE_SEEDS = 30       # Nachfragekurven-Seeds je Population (Plan Abschnitt 7 / sweep_data.json)
POPULATION_DRAWS_PER_SEED = 20    # gezogene Sequenzen je Nachfragekurve -> 30 x 20 = 600 Stichproben
SAMPLE_INSTANCES = 30              # "30 Sequenzen derselben Einstellung" (Plan Abschnitt 6, Kernabschnitt/Urteil)
VERDICT_Z = 2.0                    # klar ab mehr als VERDICT_Z Standardfehlern der gepaarten Differenz
CAPACITY_SWEEP_DELTA = 3           # drei Kapazitaetsstufen um den eingestellten Wert (Plan Abschnitt 6)

# --- Bausteine (Plan Abschnitt 3): drei Politiken, Littlewood ist die operative Empfehlung ---------------
POLICY_FCFS, POLICY_LITTLEWOOD, POLICY_DP = "fcfs", "littlewood", "dp"
POLICY_KEYS = (POLICY_FCFS, POLICY_LITTLEWOOD, POLICY_DP)
POLICY_LABELS = {POLICY_FCFS: "🐌 FCFS", POLICY_LITTLEWOOD: "📐 Littlewood", POLICY_DP: "🎯 DP (exakt)"}
POLICY_SHORT = {POLICY_FCFS: "FCFS", POLICY_LITTLEWOOD: "Littlewood", POLICY_DP: "DP (exakt)"}
POLICY_DESCRIPTIONS = {
    POLICY_FCFS: "Nimmt jede Anfrage an, solange ein Slot frei ist, ohne auf die Preisklasse zu achten. Die "
                 "Kontrast-Baseline: zeigt, wie teuer blinde Annahme wird.",
    POLICY_LITTLEWOOD: "Geschlossene Schutzformel (Littlewood 1972): Spot wird nur angenommen, wenn die "
                       "verbleibende Kapazität über dem Schutzniveau für erwartete künftige Premium-Nachfrage "
                       "liegt. Die operative Empfehlung der Hauptansicht - praktisch optimal, ohne "
                       "Rückwärts-Induktion.",
    POLICY_DP: "Rückwärts-Induktion über (Epoche, Restkapazität) - das echte Online-Optimum in diesem "
              "Modell. Referenz im Exakt-Tab, beweist wie nah Littlewood herankommt.",
}
EXACT_TAB_LABEL = "🎯 DP (exakt)"
COMPARISON_TAB_LABEL = "📊 Vergleich"

# --- Darstellung ------------------------------------------------------------------------------------------
CLASS_HI, CLASS_LO = "hi", "lo"
CLASS_LABELS = {CLASS_HI: "Premium", CLASS_LO: "Spot"}
CLASS_COLORS = {CLASS_HI: "#2a6fb0", CLASS_LO: "#e0a800"}   # Premium blau, Spot gelb (wie Plan)
POLICY_COLORS = {POLICY_FCFS: "#9aa5b4", POLICY_LITTLEWOOD: "#2e7d4f", POLICY_DP: "#2a6fb0"}
HINDSIGHT_COLOR = "#c0392b"
MARKER_LINE_COLOR = "#808895"
CHART_HEIGHT = 380

# --- Presets (Plan Abschnitt 7; Seeds >= POPULATION_CURVE_SEEDS, per tools/tune_presets.py abgestimmt) ----
# capacity/r_hi_mult/demand_mix bestimmen die POPULATION (Abnahmekriterien, unabhaengig vom Seed);
# seed bestimmt nur, welche EINE Sequenz beim Laden des Presets gezeigt wird.
PRESETS = {
    "Standard": dict(capacity=7, n_epochs=30, r_hi_mult=2.25, demand_mix="ausgewogen", seed=95),
    "Knappe Kapazität": dict(capacity=4, n_epochs=30, r_hi_mult=2.25, demand_mix="ausgewogen", seed=54),
    "Reichliche Kapazität": dict(capacity=12, n_epochs=30, r_hi_mult=2.25, demand_mix="ausgewogen", seed=53),
    "Kleiner Preisaufschlag": dict(capacity=7, n_epochs=30, r_hi_mult=1.25, demand_mix="ausgewogen", seed=41),
    "Großer Preisaufschlag": dict(capacity=7, n_epochs=30, r_hi_mult=5.0, demand_mix="ausgewogen", seed=69),
}
