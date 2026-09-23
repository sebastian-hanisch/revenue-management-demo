"""Traegt die Geschichte jedes echten Presets - Population (600 Stichproben) UND die eine gezeigte
Sequenz (Preset-Seed)? Reproduziert tools/tune_presets.py, siehe tools/PRESET_SWEEP.md."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import rvm_constants as C  # noqa: E402
import rvm_evaluation as E  # noqa: E402
import rvm_stories as ST  # noqa: E402


def _cfg_and_mix(name):
    p = C.PRESETS[name]
    pi_hi_max, pi_lo_max = C.DEMAND_MIX_PARAMS[p["demand_mix"]]
    cfg = E.Config(n_epochs=p["n_epochs"], capacity=p["capacity"], r_hi=p["r_hi_mult"] * C.R_LO, r_lo=C.R_LO)
    return p, cfg, pi_hi_max, pi_lo_max


def _population(name):
    p, cfg, pi_hi_max, pi_lo_max = _cfg_and_mix(name)
    return E.population_stats(cfg, pi_hi_max, pi_lo_max)


def _shown(name):
    p, cfg, pi_hi_max, pi_lo_max = _cfg_and_mix(name)
    pi_hi, pi_lo = E.demand_curve(cfg.n_epochs, pi_hi_max, pi_lo_max, p["seed"])
    solved = E.solve_curve(cfg, pi_hi, pi_lo)
    return E.evaluate_sequence(cfg, pi_hi, pi_lo, solved, p["seed"])


import pytest  # noqa: E402


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_population_meets_its_criteria(name):
    stats = _population(name)
    for ok, text in ST.criteria(name, stats):
        assert ok, f"{name}: {text}"


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_shown_sequence_meets_its_criteria(name):
    shown = _shown(name)
    for ok, text in ST.shown_criteria(name, shown):
        assert ok, f"{name}: {text}"


# ---------------------------------------------------------------------------------------------------
# Exakte Reproduktion von sweep_data.json (Plan Abschnitt 7: Zahlen auf +/- 0,5 Prozentpunkte) -
# hier sogar exakt, da dieselbe unveraenderte Kernlogik und Stichprobenmethodik verwendet wird.
# ---------------------------------------------------------------------------------------------------
EXPECTED_GAPS = {
    "Standard": (-15.291847563917027, -1.28761735129318),
    "Knappe Kapazität": (-35.95683909869882, -0.22215169787369593),
    "Reichliche Kapazität": (-0.8891474156556445, -0.05539859287573279),
    "Kleiner Preisaufschlag": (-2.6435334683378, None),
    "Großer Preisaufschlag": (-31.444801554675237, -0.9492488227819895),
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_population_reproduces_sweep_data_within_half_a_percentage_point(name):
    stats = _population(name)
    fcfs_expected, lit_expected = EXPECTED_GAPS[name]
    assert abs(stats.fcfs_gap_pct - fcfs_expected) <= 0.5
    if lit_expected is not None:
        assert abs(stats.littlewood_gap_pct - lit_expected) <= 0.5
