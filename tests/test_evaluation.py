"""Auswertung (rvm_evaluation): Population reproduziert sweep_data.json exakt, Kapazitaetsvergleich,
gepaartes Urteil (inkl. exaktem Schwellenwert-Test), Kennzahlen auf der gezeigten Sequenz.

Die Referenzzahlen unten sind woertlich aus seefracht-planung/messreihe_revenue/sweep_data.json
abgeschrieben (nicht zur Laufzeit von dort gelesen - das Referenz-Repo ist kein Teil dieses Repos und
in CI nicht ausgecheckt, siehe mhs_test-Muster in mehrhafenstau-demo)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import rvm_constants as C  # noqa: E402
import rvm_evaluation as E  # noqa: E402

# cfg (n_epochs, capacity, pi_hi_max, pi_lo_max, r_hi, r_lo) -> population (aus sweep_data.json)
SWEEP_PRESETS = {
    "standard": (dict(n_epochs=30, capacity=7, pi_hi_max=0.25, pi_lo_max=0.35, r_hi=900.0, r_lo=400.0),
                dict(mean_fcfs=3804.6666666666665, mean_littlewood=4433.666666666667, mean_dp=4491.5,
                     mean_hindsight=4857.166666666667, fcfs_gap_pct=-15.291847563917027,
                     littlewood_gap_pct=-1.28761735129318, hindsight_gap_pct=8.141303944487731, n=600)),
    "knapp": (dict(n_epochs=30, capacity=4, pi_hi_max=0.25, pi_lo_max=0.35, r_hi=900.0, r_lo=400.0),
             dict(mean_fcfs=2018.0, mean_littlewood=3144.0, mean_dp=3151.0, mean_hindsight=3306.3333333333335,
                  fcfs_gap_pct=-35.95683909869882, littlewood_gap_pct=-0.22215169787369593,
                  hindsight_gap_pct=4.929651962340009, n=600)),
    "reichlich": (dict(n_epochs=30, capacity=12, pi_hi_max=0.25, pi_lo_max=0.35, r_hi=900.0, r_lo=400.0),
                 dict(mean_fcfs=5963.5, mean_littlewood=6013.666666666667, mean_dp=6017.0,
                      mean_hindsight=6116.833333333333, fcfs_gap_pct=-0.8891474156556445,
                      littlewood_gap_pct=-0.05539859287573279, hindsight_gap_pct=1.6591878566284413, n=600)),
    "kleiner_aufschlag": (dict(n_epochs=30, capacity=7, pi_hi_max=0.25, pi_lo_max=0.35, r_hi=500.0, r_lo=400.0),
                          dict(mean_fcfs=2964.6666666666665, mean_littlewood=3022.8333333333335, mean_dp=3045.1666666666665,
                               mean_hindsight=3175.1666666666665, fcfs_gap_pct=-2.6435334683378,
                               littlewood_gap_pct=-0.7334026599529198, hindsight_gap_pct=4.269060259427504, n=600)),
    "grosser_aufschlag": (dict(n_epochs=30, capacity=7, pi_hi_max=0.25, pi_lo_max=0.35, r_hi=2000.0, r_lo=400.0),
                          dict(mean_fcfs=6114.666666666667, mean_littlewood=8834.666666666666, mean_dp=8919.333333333334,
                               mean_hindsight=9482.666666666666, fcfs_gap_pct=-31.444801554675237,
                               littlewood_gap_pct=-0.9492488227819895, hindsight_gap_pct=6.315868151580828, n=600)),
}

# Beispielsequenz (aus sweep_data.json "example": seed=7, capacity=4, r_hi=900, r_lo=400, draw_seed=seed*1000+3)
EXAMPLE_SEED, EXAMPLE_CAPACITY = 7, 4
EXAMPLE_SEQ = [None, "lo", None, "lo", None, None, "lo", None, None, "lo", "hi", None, "hi", None, None, None,
              None, None, "lo", None, "lo", "hi", "hi", "hi", "lo", "hi", "hi", None, "hi", "hi"]
EXAMPLE_LEVELS = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0]
EXAMPLE_ACCEPTED_LITTLEWOOD = [None, False, None, False, None, None, False, None, None, False, True, None, True,
                               None, None, None, None, None, False, None, False, True, True, False, False, False,
                               False, None, False, False]
EXAMPLE_ACCEPTED_FCFS = [None, True, None, True, None, None, True, None, None, True, False, None, False, None,
                         None, None, None, None, False, None, False, False, False, False, False, False, False,
                         None, False, False]
EXAMPLE_REVENUE_FCFS, EXAMPLE_REVENUE_LITTLEWOOD = 1600.0, 3600.0
EXAMPLE_REVENUE_DP, EXAMPLE_REVENUE_HINDSIGHT = 3600.0, 3600.0


def _population_for(cfg_dict):
    cfg = E.Config(n_epochs=cfg_dict["n_epochs"], capacity=cfg_dict["capacity"], r_hi=cfg_dict["r_hi"], r_lo=cfg_dict["r_lo"])
    return E.population_stats(cfg, cfg_dict["pi_hi_max"], cfg_dict["pi_lo_max"])


def test_population_reproduces_sweep_data_json_exactly_for_every_preset_cfg():
    """rvm_evaluation.population_stats() ist eine Wiederverwendung derselben Kernlogik (rvm_solve,
    rvm_scenario) mit derselben Stichprobenmethodik (30 x 20 = 600, dump_sweep.py) - die Zahlen muessen
    exakt (nicht nur auf Marge) mit sweep_data.json uebereinstimmen."""
    for name, (cfg_dict, pop) in SWEEP_PRESETS.items():
        stats = _population_for(cfg_dict)
        assert stats.n == pop["n"]
        assert abs(stats.mean_fcfs - pop["mean_fcfs"]) < 1e-6, name
        assert abs(stats.mean_littlewood - pop["mean_littlewood"]) < 1e-6, name
        assert abs(stats.mean_dp - pop["mean_dp"]) < 1e-6, name
        assert abs(stats.mean_hindsight - pop["mean_hindsight"]) < 1e-6, name
        assert abs(stats.fcfs_gap_pct - pop["fcfs_gap_pct"]) < 1e-6, name
        assert abs(stats.littlewood_gap_pct - pop["littlewood_gap_pct"]) < 1e-6, name
        assert abs(stats.hindsight_gap_pct - pop["hindsight_gap_pct"]) < 1e-6, name


def test_example_sequence_reproduces_sweep_data_json():
    """dump_sweep.py zieht die Beispielsequenz mit demand_curve(seed) und draw_sequence(pi, seed*1000+3)
    - derselbe Aufruf ueber rvm_evaluation muss dieselbe Sequenz und denselben Ertrag liefern."""
    cfg = E.Config(n_epochs=30, capacity=EXAMPLE_CAPACITY, r_hi=900.0, r_lo=400.0)
    pi_hi, pi_lo = E.demand_curve(30, 0.25, 0.35, EXAMPLE_SEED)
    solved = E.solve_curve(cfg, pi_hi, pi_lo)
    shown = E.evaluate_sequence(cfg, pi_hi, pi_lo, solved, EXAMPLE_SEED * 1000 + 3)
    assert list(shown.seq) == EXAMPLE_SEQ
    assert shown.revenue[C.POLICY_FCFS] == EXAMPLE_REVENUE_FCFS
    assert shown.revenue[C.POLICY_LITTLEWOOD] == EXAMPLE_REVENUE_LITTLEWOOD
    assert shown.revenue[C.POLICY_DP] == EXAMPLE_REVENUE_DP
    assert shown.hindsight == EXAMPLE_REVENUE_HINDSIGHT
    assert list(shown.levels) == EXAMPLE_LEVELS
    assert list(shown.accepted[C.POLICY_LITTLEWOOD]) == EXAMPLE_ACCEPTED_LITTLEWOOD
    assert list(shown.accepted[C.POLICY_FCFS]) == EXAMPLE_ACCEPTED_FCFS


# ---------------------------------------------------------------------------------------------------
# Kapazitaetsvergleich
# ---------------------------------------------------------------------------------------------------
def test_capacity_levels_around_clamps_to_bounds():
    assert E.capacity_levels_around(3, delta=3, bounds=(3, 15)) == [3, 6]
    assert E.capacity_levels_around(15, delta=3, bounds=(3, 15)) == [12, 15]
    assert E.capacity_levels_around(7, delta=3, bounds=(3, 15)) == [4, 7, 10]


def test_capacity_sweep_returns_stats_for_each_level():
    out = E.capacity_sweep(30, 900.0, 400.0, 0.25, 0.35, 7, n=10)
    assert set(out) == {4, 7, 10}
    for stats in out.values():
        assert stats.n == 10


def test_capacity_gap_shrinks_as_capacity_grows():
    """Strukturkonsistenz mit ERGEBNIS.md: der FCFS-Aufschlag (negativ) wird bei wachsender Kapazitaet
    kleiner im Betrag (die Luecke lebt an der Kapazitaetsgrenze)."""
    out = E.capacity_sweep(30, 900.0, 400.0, 0.25, 0.35, 7, n=30)
    caps = sorted(out)
    gaps = [abs(out[c].fcfs_gap_pct) for c in caps]
    assert gaps[0] > gaps[-1]


# ---------------------------------------------------------------------------------------------------
# Gepaartes Urteil
# ---------------------------------------------------------------------------------------------------
def test_verdict_better_when_littlewood_clearly_earns_more():
    stats = E.PopulationStats(0, 0, 0, 0, 0, 0, 0, 3,
                              revenues={C.POLICY_LITTLEWOOD: [110, 120, 115], C.POLICY_FCFS: [100, 100, 100]})
    v = E.verdict_from_population(stats)
    assert v.kind == "better" and v.diff > 0


def test_verdict_worse_when_fcfs_clearly_earns_more():
    stats = E.PopulationStats(0, 0, 0, 0, 0, 0, 0, 3,
                              revenues={C.POLICY_LITTLEWOOD: [90, 95, 92], C.POLICY_FCFS: [100, 100, 100]})
    v = E.verdict_from_population(stats)
    assert v.kind == "worse" and v.diff < 0


def test_verdict_unclear_exactly_at_the_threshold():
    """Konstruiert so, dass |Differenz| exakt VERDICT_Z * SE trifft: littlewood-fcfs = [3, 1] -> Mittel 2,
    Standardfehler 1 (n=2), VERDICT_Z=2 -> Schwelle exakt 2. Der Vergleich ist <=, nicht < -> 'unclear'."""
    stats = E.PopulationStats(0, 0, 0, 0, 0, 0, 0, 2,
                              revenues={C.POLICY_LITTLEWOOD: [3.0, 1.0], C.POLICY_FCFS: [0.0, 0.0]})
    v = E.verdict_from_population(stats)
    assert abs(v.diff - 2.0) < 1e-9 and abs(v.se - 1.0) < 1e-9
    assert v.kind == "unclear"


def test_verdict_constant_difference_with_zero_standard_error_is_decisive():
    stats = E.PopulationStats(0, 0, 0, 0, 0, 0, 0, 2,
                              revenues={C.POLICY_LITTLEWOOD: [1100.0, 1100.0], C.POLICY_FCFS: [1000.0, 1000.0]})
    v = E.verdict_from_population(stats)
    assert v.se == 0.0 and v.kind == "better"


def test_verdict_no_samples_is_unclear_with_n_zero():
    stats = E.PopulationStats(0, 0, 0, 0, 0, 0, 0, 0, revenues={})
    v = E.verdict_from_population(stats)
    assert v.kind == "unclear" and v.n == 0


# ---------------------------------------------------------------------------------------------------
# Kennzahlen der Hauptansicht
# ---------------------------------------------------------------------------------------------------
def test_gap_pct_matches_direct_computation():
    assert abs(E.gap_pct(90.0, 100.0) - (-10.0)) < 1e-9
    assert E.gap_pct(100.0, 0.0) == 0.0   # kein Referenzwert -> 0, kein Crash


def test_rejected_hi_count_reads_the_right_field():
    detail = {C.POLICY_FCFS: {"revenue": 0, "acc_hi": 1, "acc_lo": 2, "rej_hi": 5, "rej_lo": 0}}
    assert E.rejected_hi_count(detail, C.POLICY_FCFS) == 5


def test_config_from_controls_applies_the_multiplier_and_demand_mix():
    cfg, pi_hi_max, pi_lo_max = E.config_from_controls(7, 30, 2.25, "ausgewogen")
    assert cfg.r_hi == 2.25 * C.R_LO and cfg.r_lo == C.R_LO
    assert (pi_hi_max, pi_lo_max) == C.DEMAND_MIX_PARAMS["ausgewogen"]


def test_population_stats_at_zero_capacity_does_not_divide_by_zero():
    """Randfall: Kapazitaet 0 -> DP-Ertrag ist immer 0 -> gap_pct darf nicht durch 0 teilen (Regressions-
    test fuer einen beim Bau gefundenen Bug: population_stats() nutzte anfangs direkte Division)."""
    cfg = E.Config(n_epochs=20, capacity=0, r_hi=900.0, r_lo=400.0)
    stats = E.population_stats(cfg, 0.25, 0.35, n_curve_seeds=5, draws_per_seed=2)
    assert stats.mean_dp == 0.0 and stats.mean_fcfs == 0.0 and stats.mean_littlewood == 0.0
    assert stats.fcfs_gap_pct == 0.0 and stats.littlewood_gap_pct == 0.0 and stats.hindsight_gap_pct == 0.0
