"""Nachfragekurve/Sequenz (rvm_scenario.make_periods, draw_sequence): Determinismus, Struktur,
Randfaelle. Unveraendert aus messreihe_revenue/revenue.py uebernommen."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rvm_scenario import draw_sequence, make_periods  # noqa: E402


def test_deterministic_for_the_same_seed():
    a = make_periods(30, 0.25, 0.35, 0)
    b = make_periods(30, 0.25, 0.35, 0)
    assert a == b


def test_different_seeds_usually_differ():
    a = make_periods(30, 0.25, 0.35, 0)
    b = make_periods(30, 0.25, 0.35, 1)
    assert a != b


def test_periods_have_one_entry_per_epoch():
    pi_hi, pi_lo = make_periods(20, 0.25, 0.35, 3)
    assert len(pi_hi) == 20 and len(pi_lo) == 20


def test_probabilities_stay_within_valid_bounds():
    pi_hi, pi_lo = make_periods(40, 0.3, 0.4, 7)
    for hi, lo in zip(pi_hi, pi_lo):
        assert 0.0 <= hi <= 0.9
        assert 0.0 <= lo <= 0.9
        assert hi + lo <= 0.9 + 1e-9   # genug Restwahrscheinlichkeit fuer "keine Anfrage"


def test_premium_probability_trends_up_and_spot_trends_down():
    """pi_hi(n) steigt im Mittel ueber die Epochen, pi_lo(n) faellt - das Rauschen kann einzelne Punkte
    verschieben, aber der Trend im Mittel der ersten gegen die zweite Haelfte muss stimmen."""
    pi_hi, pi_lo = make_periods(60, 0.25, 0.35, 0)
    half = len(pi_hi) // 2
    assert sum(pi_hi[:half]) / half < sum(pi_hi[half:]) / (len(pi_hi) - half)
    assert sum(pi_lo[:half]) / half > sum(pi_lo[half:]) / (len(pi_lo) - half)


def test_single_epoch_does_not_crash():
    pi_hi, pi_lo = make_periods(1, 0.25, 0.35, 0)
    assert len(pi_hi) == 1 and len(pi_lo) == 1


def test_zero_epochs_yields_empty_curve():
    pi_hi, pi_lo = make_periods(0, 0.25, 0.35, 0)
    assert pi_hi == [] and pi_lo == []


def test_extreme_pi_hi_max_still_clamps_hi_to_at_most_point_nine():
    """pi_hi_max weit ueber dem in der App erreichbaren Bereich (max 0.35, siehe DEMAND_MIX_PARAMS):
    das Sicherheitsnetz min(hi, 0.9) muss trotzdem halten, unabhaengig vom Regler-Bereich."""
    for seed in range(10):
        pi_hi, _ = make_periods(20, 5.0, 0.0, seed)
        assert all(hi <= 0.9 for hi in pi_hi)


def test_extreme_pi_lo_max_still_keeps_hi_plus_lo_within_point_nine():
    for seed in range(10):
        pi_hi, pi_lo = make_periods(20, 0.5, 5.0, seed)
        assert all(hi + lo <= 0.9 + 1e-9 for hi, lo in zip(pi_hi, pi_lo))


# ---------------------------------------------------------------------------------------------------
# draw_sequence
# ---------------------------------------------------------------------------------------------------
def test_draw_sequence_length_matches_periods():
    pi_hi, pi_lo = make_periods(25, 0.25, 0.35, 2)
    seq = draw_sequence(pi_hi, pi_lo, 5)
    assert len(seq) == 25
    assert all(c in ("hi", "lo", None) for c in seq)


def test_draw_sequence_deterministic_for_the_same_seed():
    pi_hi, pi_lo = make_periods(25, 0.25, 0.35, 2)
    a = draw_sequence(pi_hi, pi_lo, 9)
    b = draw_sequence(pi_hi, pi_lo, 9)
    assert a == b


def test_draw_sequence_different_seeds_usually_differ():
    pi_hi, pi_lo = make_periods(25, 0.25, 0.35, 2)
    a = draw_sequence(pi_hi, pi_lo, 1)
    b = draw_sequence(pi_hi, pi_lo, 2)
    assert a != b


def test_certain_arrival_always_produces_that_class():
    """pi_hi=1.0 an jeder Epoche -> jede Ziehung ist 'hi', unabhaengig vom Seed."""
    pi_hi = [1.0] * 10
    pi_lo = [0.0] * 10
    for seed in range(5):
        assert draw_sequence(pi_hi, pi_lo, seed) == ["hi"] * 10


def test_zero_arrival_probability_never_produces_a_request():
    pi_hi = [0.0] * 10
    pi_lo = [0.0] * 10
    for seed in range(5):
        assert draw_sequence(pi_hi, pi_lo, seed) == [None] * 10
