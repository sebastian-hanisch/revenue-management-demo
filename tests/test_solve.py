"""Politiken/Loeser (rvm_solve): Handinstanz, Hindsight-Dominanz (hart, pfadweise), DP-Theoriewert
gegen simuliertes Mittel, DP im ERWARTUNGSWERT nie schlechter als Littlewood/FCFS (statistisch, NICHT
pfadweise - siehe ERGEBNIS.md "Vorbehalte" und Plan Abschnitt 12), Randfaelle. Portiert aus
messreihe_revenue/check.py (0 Abweichungen dort)."""
import pathlib
import statistics as st
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rvm_scenario import draw_sequence, make_periods  # noqa: E402
from rvm_solve import (dp_accept, dp_optimal, hindsight_oracle, littlewood_protection_levels,  # noqa: E402
                        remaining_hi_dists, simulate)

R_HI, R_LO = 900.0, 400.0


# ---------------------------------------------------------------------------------------------------
# Handinstanz (fester Regressionstest, aus check.py)
# ---------------------------------------------------------------------------------------------------
def test_hand_instance_rejects_the_sure_spot_to_protect_the_sure_premium():
    """2 Epochen: Epoche 0 IMMER Spot, Epoche 1 IMMER Premium, Kapazitaet 1. Optimal: Epoche 0 (Spot)
    ABLEHNEN, um den einen Platz fuer die sichere Premium-Anfrage in Epoche 1 zu behalten
    (R_HI > R_LO) -> erwarteter Ertrag = R_HI = 900 exakt."""
    V = dp_optimal([0.0, 1.0], [1.0, 0.0], R_HI, R_LO, 1)
    assert abs(V[0][1] - R_HI) < 1e-9

    # Die Annahme-Entscheidung selbst: in Epoche 0 (Spot, fare=R_LO) muss dp_accept ablehnen.
    assert dp_accept(V, 0, 1, R_LO) is False
    # In Epoche 1 (Premium, fare=R_HI, c=1 falls Epoche 0 abgelehnt wurde) muss dp_accept annehmen.
    assert dp_accept(V, 1, 1, R_HI) is True

    # Auf der einzigen moeglichen Sequenz simuliert: DP erreicht exakt R_HI.
    seq = ["lo", "hi"]
    result = simulate(seq, "dp", 1, R_HI, R_LO, V=V)
    assert result["revenue"] == R_HI
    assert result["rej_lo"] == 1 and result["acc_hi"] == 1


# ---------------------------------------------------------------------------------------------------
# 1) Hindsight dominiert jede Politik auf DERSELBEN Sequenz - harte Invariante, pfadweise
# ---------------------------------------------------------------------------------------------------
def test_hindsight_dominates_every_policy_on_the_same_sequence():
    tested = bad = 0
    for seed in range(200):
        pi_hi, pi_lo = make_periods(30, 0.25, 0.35, seed // 4)
        seq = draw_sequence(pi_hi, pi_lo, seed)
        cap = 8
        hs = hindsight_oracle(seq, cap, R_HI, R_LO)
        V = dp_optimal(pi_hi, pi_lo, R_HI, R_LO, cap)
        levels = littlewood_protection_levels(pi_hi, R_HI, R_LO)
        for pol, kw in [("fcfs", {}), ("littlewood", dict(levels=levels)), ("dp", dict(V=V))]:
            rev = simulate(seq, pol, cap, R_HI, R_LO, **kw)["revenue"]
            tested += 1
            if rev > hs + 1e-9:
                bad += 1
    assert tested == 600
    assert bad == 0, f"{bad} von {tested} Politik-Anwendungen schlugen das Hindsight-Optimum"


# ---------------------------------------------------------------------------------------------------
# 2) DP-Theoriewert stimmt mit dem simulierten Mittel ueberein (Gesetz der grossen Zahlen)
# ---------------------------------------------------------------------------------------------------
def test_dp_theoretical_value_matches_simulated_mean_over_many_samples():
    pi_hi, pi_lo = make_periods(25, 0.3, 0.3, 0)
    cap = 6
    V = dp_optimal(pi_hi, pi_lo, R_HI, R_LO, cap)
    theory = V[0][cap]
    sims = [simulate(draw_sequence(pi_hi, pi_lo, 10_000 + seed), "dp", cap, R_HI, R_LO, V=V)["revenue"]
           for seed in range(2000)]
    mean_sim = st.fmean(sims)
    se = st.stdev(sims) / len(sims) ** 0.5
    assert abs(theory - mean_sim) <= 4 * se, f"Theorie {theory:.2f} vs. simuliertes Mittel {mean_sim:.2f} +/- {se:.2f}"


# ---------------------------------------------------------------------------------------------------
# 3) DP ist im ERWARTUNGSWERT nie schlechter als Littlewood/FCFS - NICHT pfadweise (siehe Plan Abschnitt 12)
# ---------------------------------------------------------------------------------------------------
def test_dp_is_never_worse_than_littlewood_or_fcfs_in_expectation():
    """Statistischer Vergleich ueber viele Stichproben je Instanz - KEINE Pfad-fuer-Pfad-Behauptung.
    DP ist nur im Erwartungswert an jedem Entscheidungspunkt optimal; eine ungueneue Einzelsequenz kann
    eine "suboptimale" Politik im Einzelfall trotzdem besser aussehen lassen (siehe ERGEBNIS.md)."""
    violations = 0
    for seed in range(10):
        pi_hi, pi_lo = make_periods(30, 0.2, 0.35, seed)
        cap = 7
        V = dp_optimal(pi_hi, pi_lo, R_HI, R_LO, cap)
        levels = littlewood_protection_levels(pi_hi, R_HI, R_LO)
        revs = {"fcfs": [], "littlewood": [], "dp": []}
        for s in range(400):
            seq = draw_sequence(pi_hi, pi_lo, seed * 10_000 + s)
            for pol, kw in [("fcfs", {}), ("littlewood", dict(levels=levels)), ("dp", dict(V=V))]:
                revs[pol].append(simulate(seq, pol, cap, R_HI, R_LO, **kw)["revenue"])
        m_dp, m_lit, m_fcfs = st.fmean(revs["dp"]), st.fmean(revs["littlewood"]), st.fmean(revs["fcfs"])
        if m_dp < m_lit - 1.0 or m_dp < m_fcfs - 1.0:
            violations += 1
    assert violations == 0


# ---------------------------------------------------------------------------------------------------
# Randfaelle (Plan Abschnitt 11)
# ---------------------------------------------------------------------------------------------------
def test_zero_capacity_rejects_everything_and_earns_nothing():
    pi_hi, pi_lo = make_periods(20, 0.25, 0.35, 0)
    seq = draw_sequence(pi_hi, pi_lo, 0)
    V = dp_optimal(pi_hi, pi_lo, R_HI, R_LO, 0)
    levels = littlewood_protection_levels(pi_hi, R_HI, R_LO)
    for pol, kw in [("fcfs", {}), ("littlewood", dict(levels=levels)), ("dp", dict(V=V))]:
        result = simulate(seq, pol, 0, R_HI, R_LO, **kw)
        assert result["revenue"] == 0.0
        assert result["acc_hi"] == 0 and result["acc_lo"] == 0
    assert hindsight_oracle(seq, 0, R_HI, R_LO) == 0.0


def test_very_large_capacity_accepts_every_arrival_and_all_policies_agree():
    """Kapazitaet weit ueber der Nachfrage: jede Anfrage wird angenommen, FCFS == Littlewood == DP ==
    Hindsight (alle nehmen alles)."""
    n_epochs = 25
    pi_hi, pi_lo = make_periods(n_epochs, 0.25, 0.35, 0)
    seq = draw_sequence(pi_hi, pi_lo, 0)
    cap = n_epochs   # kann nie ueberschritten werden (hoechstens eine Anfrage je Epoche)
    V = dp_optimal(pi_hi, pi_lo, R_HI, R_LO, cap)
    levels = littlewood_protection_levels(pi_hi, R_HI, R_LO)
    revs = {}
    for pol, kw in [("fcfs", {}), ("littlewood", dict(levels=levels)), ("dp", dict(V=V))]:
        revs[pol] = simulate(seq, pol, cap, R_HI, R_LO, **kw)["revenue"]
    hs = hindsight_oracle(seq, cap, R_HI, R_LO)
    expected = sum(R_HI if c == "hi" else R_LO for c in seq if c is not None)
    assert revs["fcfs"] == revs["littlewood"] == revs["dp"] == hs == expected


def test_fare_ratio_one_makes_every_policy_identical():
    """r_hi == r_lo: die Klassen sind fuer die Politiken ununterscheidbar (Littlewoods Schutzformel
    schuetzt bei ratio=1 gar nichts mehr, da r_lo/r_hi=1 die Bedingung P(...) <= 1 immer erfuellt ist)."""
    n_epochs, cap = 25, 6
    pi_hi, pi_lo = make_periods(n_epochs, 0.25, 0.35, 3)
    r_same = 500.0
    V = dp_optimal(pi_hi, pi_lo, r_same, r_same, cap)
    levels = littlewood_protection_levels(pi_hi, r_same, r_same)
    assert all(y == 0 for y in levels)   # Schutzniveau 0: Spot wird wie Premium behandelt
    for seed in range(20):
        seq = draw_sequence(pi_hi, pi_lo, seed)
        rev_fcfs = simulate(seq, "fcfs", cap, r_same, r_same)["revenue"]
        rev_lit = simulate(seq, "littlewood", cap, r_same, r_same, levels=levels)["revenue"]
        rev_dp = simulate(seq, "dp", cap, r_same, r_same, V=V)["revenue"]
        assert rev_fcfs == rev_lit == rev_dp


def test_zero_epochs_yields_zero_value_and_empty_sequence():
    V = dp_optimal([], [], R_HI, R_LO, 5)
    assert V == [[0.0] * 6]
    seq = draw_sequence([], [], 0)
    assert seq == []
    for pol, kw in [("fcfs", {}), ("littlewood", dict(levels=[])), ("dp", dict(V=V))]:
        assert simulate(seq, pol, 5, R_HI, R_LO, **kw)["revenue"] == 0.0
    assert hindsight_oracle(seq, 5, R_HI, R_LO) == 0.0


# ---------------------------------------------------------------------------------------------------
# Littlewoods Schutzformel: Struktur der Schutzniveaus und Poisson-Binomial-Verteilung
# ---------------------------------------------------------------------------------------------------
def test_remaining_hi_dists_sums_to_one_and_shrinks_towards_the_end():
    pi_hi, _ = make_periods(20, 0.3, 0.3, 0)
    dists = remaining_hi_dists(pi_hi)
    for dist in dists:
        assert abs(sum(dist) - 1.0) <= 1e-9
    assert dists[-1] == [1.0]   # nichts mehr uebrig am Ende


def test_protection_levels_are_non_increasing_towards_the_end():
    """Je naeher am Ende, desto weniger verbleibende Premium-Nachfrage ist noch zu schuetzen - das
    Schutzniveau y*(n) darf nicht steigen, wenn n waechst (siehe Beispielsequenz in sweep_data.json)."""
    pi_hi, _ = make_periods(30, 0.25, 0.35, 7)
    levels = littlewood_protection_levels(pi_hi, R_HI, R_LO)
    assert all(levels[i] >= levels[i + 1] for i in range(len(levels) - 1))


def test_protection_level_uses_less_than_or_equal_at_the_exact_boundary():
    """Konstruierte Instanz, bei der die kumulierte Restwahrscheinlichkeit (tail) exakt auf die Schwelle
    ratio=1.0 trifft: 2 Epochen, Epoche 0 IMMER Premium, Epoche 1 NIE - die verbleibende Premium-Zahl ist
    danach exakt 1 (Wahrscheinlichkeit 1.0). Bei ratio=1.0 (r_hi=r_lo) darf Spot gar nicht geschuetzt
    werden (Klassen sind fuer die Formel ununterscheidbar) - levels[0] muss 0 sein. Das prueft den Fall
    tail==ratio exakt (<=, nicht <, siehe rvm_solve.littlewood_protection_levels)."""
    pi_hi = [1.0, 0.0]
    r_same = 500.0
    levels = littlewood_protection_levels(pi_hi, r_same, r_same)
    assert levels[0] == 0
    assert levels[1] == 0


def test_higher_premium_price_never_lowers_the_protection_level():
    pi_hi, _ = make_periods(30, 0.25, 0.35, 1)
    low = littlewood_protection_levels(pi_hi, 600.0, R_LO)
    high = littlewood_protection_levels(pi_hi, 3000.0, R_LO)
    assert all(h >= l for l, h in zip(low, high))
