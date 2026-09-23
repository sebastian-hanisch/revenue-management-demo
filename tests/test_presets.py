"""Regler-Spezifikation, Permalink, Presets, Seed-Knopf (rvm_presets) - reine Logik ohne AppTest."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import rvm_constants as C  # noqa: E402
from rvm_presets import bounds, options, parse_setting, SETTING_SPECS  # noqa: E402


def test_bounds_reads_spec_range():
    assert bounds("capacity_slider") == C.CAPACITY_RANGE
    assert bounds("n_epochs_slider") == C.N_EPOCHS_RANGE
    assert bounds("seed_input") == C.SEED_RANGE


def test_options_reads_the_step_list():
    assert options("r_hi_mult_select") == C.R_HI_MULT_OPTIONS
    assert options("demand_mix_select") == C.DEMAND_MIX_OPTIONS


# ---------------------------------------------------------------------------------------------------
# Permalink-Parsing
# ---------------------------------------------------------------------------------------------------
def test_parse_setting_clamps_to_spec_range():
    spec = SETTING_SPECS["capacity_slider"]
    assert parse_setting(spec, "99") == C.CAPACITY_RANGE[1]
    assert parse_setting(spec, "0") == C.CAPACITY_RANGE[0]


def test_parse_setting_ignores_garbage():
    spec = SETTING_SPECS["seed_input"]
    assert parse_setting(spec, "not-a-number") is None


def test_parse_setting_rejects_non_finite_floats():
    spec = SETTING_SPECS["n_epochs_slider"]
    assert parse_setting(spec, "nan") is None
    assert parse_setting(spec, "inf") is None


def test_parse_setting_snaps_multiplier_to_the_nearest_step():
    spec = SETTING_SPECS["r_hi_mult_select"]
    assert parse_setting(spec, "2.3") == 2.25
    assert parse_setting(spec, "0.1") == 1.25    # unter der kleinsten Stufe -> kleinste Stufe
    assert parse_setting(spec, "99") == 5.0       # ueber der groessten Stufe -> groesste Stufe


def test_parse_setting_accepts_only_valid_demand_mix_strings():
    spec = SETTING_SPECS["demand_mix_select"]
    assert parse_setting(spec, "premium-reich") == "premium-reich"
    assert parse_setting(spec, "nonsense") is None


# ---------------------------------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------------------------------
def test_every_preset_has_all_five_fields_within_spec_bounds():
    for name, preset in C.PRESETS.items():
        assert set(preset) == {"capacity", "n_epochs", "r_hi_mult", "demand_mix", "seed"}
        assert C.CAPACITY_RANGE[0] <= preset["capacity"] <= C.CAPACITY_RANGE[1]
        assert C.N_EPOCHS_RANGE[0] <= preset["n_epochs"] <= C.N_EPOCHS_RANGE[1]
        assert preset["r_hi_mult"] in C.R_HI_MULT_OPTIONS
        assert preset["demand_mix"] in C.DEMAND_MIX_OPTIONS
        assert C.SEED_RANGE[0] <= preset["seed"] <= C.SEED_RANGE[1]


def test_preset_seeds_lie_outside_the_population():
    assert all(preset["seed"] >= C.POPULATION_CURVE_SEEDS for preset in C.PRESETS.values())


def test_preset_names_are_short_for_the_button_row():
    assert all(len(name) <= 22 for name in C.PRESETS)
    assert len(C.PRESETS) == 5


def test_only_capacity_varies_between_standard_knapp_and_reichlich():
    std, knp, rei = C.PRESETS["Standard"], C.PRESETS["Knappe Kapazität"], C.PRESETS["Reichliche Kapazität"]
    for other in (knp, rei):
        assert other["r_hi_mult"] == std["r_hi_mult"] and other["demand_mix"] == std["demand_mix"]
        assert other["n_epochs"] == std["n_epochs"]
    assert knp["capacity"] < std["capacity"] < rei["capacity"]


def test_only_price_multiplier_varies_between_the_two_markup_presets_and_standard():
    std = C.PRESETS["Standard"]
    kla, gro = C.PRESETS["Kleiner Preisaufschlag"], C.PRESETS["Großer Preisaufschlag"]
    for other in (kla, gro):
        assert other["capacity"] == std["capacity"] and other["demand_mix"] == std["demand_mix"]
    assert kla["r_hi_mult"] < std["r_hi_mult"] < gro["r_hi_mult"]
