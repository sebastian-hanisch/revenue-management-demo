"""AppTest: Skelett und Footer, jedes Preset, Permalink, alle Regler an Min und Max, die bedingte
Meldung in beiden Zuständen, Urteil, Vergleichstabelle, PDF, Texte."""
import pathlib

import pytest
from streamlit.testing.v1 import AppTest

import rvm_constants as C
from rvm_presets import SETTING_SPECS

APP = str(pathlib.Path(__file__).resolve().parent.parent / "app.py")
FOOTER = (
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zum Thema: [Seefracht optimieren](https://sebastianhanisch.net/seefracht-optimierung.html)."
)


@pytest.fixture(autouse=True)
def clean_cache():
    """st.cache_data ist prozessweit: Tests, die Einstellungen aendern, duerfen keine
    zwischengespeicherten Ergebnisse anderer Tests sehen."""
    import streamlit as st
    st.cache_data.clear()
    yield


def fresh(**query):
    at = AppTest.from_file(APP, default_timeout=180)
    for k, v in query.items():
        at.query_params[k] = v
    at.run()
    assert not at.exception, at.exception
    return at


def set_and_run(at, **values):
    for key, value in values.items():
        if key.endswith("_input"):
            at.number_input(key=key).set_value(value)
        elif key in ("r_hi_mult_select", "demand_mix_select"):
            at.select_slider(key=key).set_value(value)
        else:
            at.slider(key=key).set_value(value)
    at.run()
    assert not at.exception, at.exception
    return at


def main_metrics(at):
    return [(m.label, m.value) for m in at.metric[:4]]


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception, at.exception
    return at


def message(at, needle):
    for group in (at.success, at.warning, at.info, at.error):
        for x in group:
            if needle in x.value:
                return x.value
    return None


# ---------------------------------------------------------------------------------------------------
# Skelett
# ---------------------------------------------------------------------------------------------------
def test_skeleton_and_footer():
    at = fresh()
    assert [h.value for h in at.sidebar.header] == ["⚙️ Einstellungen"]                # genau EIN Header
    assert len(at.title) == 1 and "Buchungs-/Slot-Vergabe" in at.title[0].value
    assert any(v.value.startswith("## 🎯") for v in at.markdown)
    assert any(v.value.startswith("### 📐") for v in at.markdown)
    assert [e.label for e in at.expander] == ["🔧 Wie wir das erreichen – Politiken im Vergleich",
                                              "Wie funktioniert diese Demo?", "📐 Mathematische Formulierung"]
    assert any(c.value == FOOTER for c in at.caption)
    presets = [b.label for b in at.button if b.label in C.PRESETS]
    assert presets == list(C.PRESETS) and len(presets) == 5 and all(len(n) <= 22 for n in presets)
    assert [s.label for s in at.sidebar.slider] == ["Slots (Kapazität)", "Buchungsfenster (Epochen)"]
    assert [s.label for s in at.sidebar.select_slider] == ["Premium-Preisaufschlag", "Nachfragemix (Premium/Spot)"]
    assert [n.label for n in at.sidebar.number_input] == ["Seed"]
    assert any(b.label == "🎲 Neue Buchungssequenz" for b in at.sidebar.button)


def test_main_metrics_are_2x2_with_the_right_labels():
    at = fresh()
    labels = [m[0] for m in main_metrics(at)]
    assert labels == ["Ertrag (Littlewood)", "Ertrag (FCFS)", "Abstand zum DP-Optimum", "Abgewiesene Premium-Anfragen (FCFS)"]


def test_charts_are_present_with_unique_keys():
    at = fresh()
    charts = at.get("plotly_chart")
    keys = [c.key for c in charts]
    assert len(set(keys)) == len(keys) and all(keys)
    assert len(keys) == 6   # Zeitleiste, Kapazitaetsvergleich, 3 Politik-Tab-Zeitleisten, Vergleichs-Tab-Kapazitaetsvergleich


# ---------------------------------------------------------------------------------------------------
# Presets, Permalink
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_loads_within_widget_bounds_and_shows_its_story(name):
    at = fresh()
    click(at, name)
    preset = C.PRESETS[name]
    assert at.slider(key="capacity_slider").value == preset["capacity"]
    assert at.slider(key="n_epochs_slider").value == preset["n_epochs"]
    assert at.select_slider(key="r_hi_mult_select").value == preset["r_hi_mult"]
    assert at.select_slider(key="demand_mix_select").value == preset["demand_mix"]
    assert at.number_input(key="seed_input").value == preset["seed"]

    labels = [m[0] for m in main_metrics(at)]
    assert labels[0] == "Ertrag (Littlewood)" and labels[1] == "Ertrag (FCFS)"


def test_permalink_is_clamped_snapped_and_ignores_garbage():
    at = fresh(cap="99", ep="abc", mult="2.3", mix="nonsense", junk="ignored")
    assert at.slider(key="capacity_slider").value == C.CAPACITY_RANGE[1]           # geklemmt
    assert at.slider(key="n_epochs_slider").value == C.N_EPOCHS_DEFAULT             # Muell ignoriert
    assert at.select_slider(key="r_hi_mult_select").value == 2.25                    # auf naechste Stufe geklemmt
    assert at.select_slider(key="demand_mix_select").value == C.DEMAND_MIX_DEFAULT   # ungueltige Stufe ignoriert


def test_permalink_roundtrip_reflects_settings():
    at = fresh(cap="6", ep="40", mult="1.75", mix="premium-reich", seed="11")
    values = {k: at.session_state[k] for k in SETTING_SPECS}
    assert values == {"capacity_slider": 6, "n_epochs_slider": 40, "r_hi_mult_select": 1.75,
                      "demand_mix_select": "premium-reich", "seed_input": 11}
    for key, spec in SETTING_SPECS.items():
        got = at.query_params[spec.url_param]
        got = got[0] if isinstance(got, list) else got
        assert got == spec.encoder(at.session_state[key]), key


def test_new_sequence_button_changes_only_the_seed():
    at = fresh()
    before = {k: at.session_state[k] for k in SETTING_SPECS if k != "seed_input"}
    click(at, "🎲 Neue Buchungssequenz")
    assert {k: at.session_state[k] for k in SETTING_SPECS if k != "seed_input"} == before
    assert C.SEED_RANGE[0] <= at.session_state["seed_input"] <= C.SEED_RANGE[1]


def test_new_sequence_button_actually_randomizes_not_just_stays_in_range():
    """Regressionstest gegen einen beim Bau gefundenen Mutanten: randomize_seed() muss tatsaechlich
    wuerfeln, nicht nur einen festen Wert im gueltigen Bereich setzen."""
    at = fresh()
    seeds = set()
    for _ in range(8):
        click(at, "🎲 Neue Buchungssequenz")
        seeds.add(at.session_state["seed_input"])
    assert len(seeds) > 1


# ---------------------------------------------------------------------------------------------------
# Regler an den Grenzen
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("key,value", [("capacity_slider", C.CAPACITY_RANGE[0]), ("capacity_slider", C.CAPACITY_RANGE[1]),
                                       ("n_epochs_slider", C.N_EPOCHS_RANGE[0]), ("n_epochs_slider", C.N_EPOCHS_RANGE[1])])
def test_every_slider_works_at_its_minimum_and_maximum(key, value):
    at = set_and_run(fresh(), **{key: value})
    assert at.session_state[key] == value and len(at.metric) >= 4


@pytest.mark.parametrize("value", [C.R_HI_MULT_OPTIONS[0], C.R_HI_MULT_OPTIONS[-1]])
def test_price_multiplier_works_at_its_lowest_and_highest_step(value):
    at = set_and_run(fresh(), r_hi_mult_select=value)
    assert at.session_state["r_hi_mult_select"] == value


@pytest.mark.parametrize("value", list(C.DEMAND_MIX_OPTIONS))
def test_demand_mix_works_at_every_step(value):
    at = set_and_run(fresh(), demand_mix_select=value)
    assert at.session_state["demand_mix_select"] == value


def test_seed_input_works_at_its_minimum_and_maximum():
    at = set_and_run(fresh(), seed_input=C.SEED_RANGE[0])
    assert at.session_state["seed_input"] == C.SEED_RANGE[0]
    at = set_and_run(fresh(), seed_input=C.SEED_RANGE[1])
    assert at.session_state["seed_input"] == C.SEED_RANGE[1]


def test_extreme_combination_runs_without_exception():
    at = fresh(cap="3", ep="15", mult="1.25", mix="premium-arm", seed="0")
    assert not at.exception
    at = fresh(cap="15", ep="60", mult="5.0", mix="premium-reich", seed="9999")
    assert not at.exception


# ---------------------------------------------------------------------------------------------------
# Bedingte Meldung
# ---------------------------------------------------------------------------------------------------
def test_message_class_protection_pays_off_for_the_scarce_capacity_preset():
    at = fresh()
    click(at, "Knappe Kapazität")
    msg = message(at, "lohnt sich Klassenschutz deutlich")
    assert msg is not None


def test_message_barely_matters_for_the_generous_capacity_preset():
    at = fresh()
    click(at, "Reichliche Kapazität")
    msg = message(at, "kaum einen Unterschied")
    assert msg is not None


# ---------------------------------------------------------------------------------------------------
# Kernabschnitt: Urteil
# ---------------------------------------------------------------------------------------------------
def test_verdict_sentence_present():
    at = fresh()
    texts = [x.value for group in (at.success, at.warning, at.info) for x in group if "Littlewood gegen FCFS" in x.value]
    assert len(texts) >= 1


def _fake_verdict(monkeypatch, kind, diff, se=1.0, n=30):
    import rvm_evaluation as E_mod
    monkeypatch.setattr(E_mod, "verdict_from_population", lambda stats: E_mod.Verdict(kind, diff, se, n))


def test_verdict_sentence_better_and_worse(monkeypatch):
    _fake_verdict(monkeypatch, "better", 30.0)
    at = fresh()
    assert any("mehr Ertrag" in x.value for x in at.success)
    _fake_verdict(monkeypatch, "worse", -30.0)
    at = fresh()
    assert any("weniger Ertrag" in x.value for x in at.warning)


def test_verdict_sentence_unclear(monkeypatch):
    _fake_verdict(monkeypatch, "unclear", 2.0)
    at = fresh()
    assert any("Kein klarer Unterschied" in x.value for x in at.info)


def test_verdict_sentence_no_comparable_sequences(monkeypatch):
    _fake_verdict(monkeypatch, "unclear", 0.0, se=0.0, n=0)
    at = fresh()
    assert any("Kein Vergleich möglich" in x.value for x in at.info)


# ---------------------------------------------------------------------------------------------------
# Bausteine im Vergleich, PDF, Texte
# ---------------------------------------------------------------------------------------------------
def test_comparison_table_has_one_row_per_policy_plus_hindsight():
    at = fresh()
    dfs = at.dataframe
    comparison_df = dfs[-1].value
    assert list(comparison_df["Politik"])[:3] == [C.POLICY_LABELS[p] for p in C.POLICY_KEYS]
    assert "Hindsight" in comparison_df["Politik"].iloc[-1]
    assert "Abstand zum DP-Optimum" in comparison_df.columns


def test_each_policy_tab_shows_a_timeline():
    at = fresh()
    charts = at.get("plotly_chart")
    assert sum(1 for c in charts if c.key.startswith("tab_fcfs_") or c.key.startswith("tab_littlewood_")
              or c.key.startswith("tab_dp_")) == 3


def test_pdf_download_button_is_offered():
    at = fresh()
    buttons = at.get("download_button")
    assert len(buttons) == 1 and buttons[0].proto.label == "📄 Ergebnis als PDF herunterladen"


def test_texts_state_the_model_and_that_littlewood_not_dp_is_the_recommendation():
    at = fresh()
    text = "\n".join(m.value for m in at.expander[1].markdown)
    for needle in ("Littlewood", "Premium", "Spot", "Rückwärts-Induktion", "Overbooking"):
        assert needle in text, needle
    math_text = "\n".join(m.value for m in at.expander[2].markdown)
    for needle in ("Littlewoods Regel", "y^\\ast", "Handinstanz", "Hindsight-Orakel"):
        assert needle in math_text, needle
