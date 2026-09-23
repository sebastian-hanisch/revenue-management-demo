"""Jedes einzelne Kriterium aus rvm_stories.criteria()/shown_criteria() an kuenstlichen Werten, die
genau an seiner Schwelle kippen (Plan Abschnitt 7 Fallstricke-Checkliste: Schwellen kuenstlich pruefen)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import rvm_constants as C  # noqa: E402
import rvm_stories as ST  # noqa: E402
from rvm_evaluation import PopulationStats, SequenceResult  # noqa: E402


def _stats(fcfs_gap_pct, littlewood_gap_pct):
    return PopulationStats(0, 0, 0, 0, fcfs_gap_pct, littlewood_gap_pct, 0, 600)


def _shown(fcfs, lit, dp):
    revenue = {C.POLICY_FCFS: fcfs, C.POLICY_LITTLEWOOD: lit, C.POLICY_DP: dp}
    return SequenceResult(0, (), (), revenue, {}, {}, 0.0)


def _all_ok(results):
    return all(ok for ok, _ in results)


# ---------------------------------------------------------------------------------------------------
# Population-Kriterien (criteria) - jede Schwelle einzeln
# ---------------------------------------------------------------------------------------------------
def test_standard_population_criteria_tip_at_their_thresholds():
    assert _all_ok(ST.criteria("Standard", _stats(-10.0, -3.0)))
    assert not _all_ok(ST.criteria("Standard", _stats(-9.999, -3.0)))
    assert not _all_ok(ST.criteria("Standard", _stats(-10.0, -3.001)))


def test_knappe_population_criteria_tip_at_their_thresholds():
    assert _all_ok(ST.criteria("Knappe Kapazität", _stats(-25.0, -3.0)))
    assert not _all_ok(ST.criteria("Knappe Kapazität", _stats(-24.999, -3.0)))
    assert not _all_ok(ST.criteria("Knappe Kapazität", _stats(-25.0, -3.001)))


def test_reichliche_population_criteria_tip_at_their_thresholds():
    assert _all_ok(ST.criteria("Reichliche Kapazität", _stats(-3.0, -1.0)))
    assert not _all_ok(ST.criteria("Reichliche Kapazität", _stats(-3.001, -1.0)))
    assert not _all_ok(ST.criteria("Reichliche Kapazität", _stats(-3.0, -1.001)))


def test_kleiner_aufschlag_population_criterion_tips_at_its_threshold():
    assert _all_ok(ST.criteria("Kleiner Preisaufschlag", _stats(-5.0, 0.0)))
    assert not _all_ok(ST.criteria("Kleiner Preisaufschlag", _stats(-5.001, 0.0)))


def test_grosser_aufschlag_population_criteria_tip_at_their_thresholds():
    assert _all_ok(ST.criteria("Großer Preisaufschlag", _stats(-20.0, -3.0)))
    assert not _all_ok(ST.criteria("Großer Preisaufschlag", _stats(-19.999, -3.0)))
    assert not _all_ok(ST.criteria("Großer Preisaufschlag", _stats(-20.0, -3.001)))


def test_criteria_raises_key_error_for_unknown_preset():
    import pytest
    with pytest.raises(KeyError):
        ST.criteria("Unbekanntes Preset", _stats(0.0, 0.0))


# ---------------------------------------------------------------------------------------------------
# Kriterien der gezeigten Sequenz (shown_criteria) - jede Schwelle einzeln, ueber revenue-Verhaeltnisse.
# shown_criteria berechnet den Prozentabstand selbst per Division (fcfs/dp - 1) * 100 - ein exakter
# Treffer auf der Fliesskomma-Schwelle ist nicht garantiert (Rundung), deshalb pruefen wir knapp inner-
# bzw. ausserhalb der Schwelle statt exakt auf ihr (siehe feedback_ci_unpinned_numeric_asserts.md: keine
# Fliesskomma-Gleichheit an einer berechneten Schwelle erzwingen).
# ---------------------------------------------------------------------------------------------------
EPS_OK, EPS_FAIL = 1e-6, 5e-3


def _revs(fcfs_gap_pct, lit_gap_pct, dp=1000.0):
    fcfs = dp * (1 + fcfs_gap_pct / 100)
    lit = dp * (1 + lit_gap_pct / 100)
    return fcfs, lit, dp


def test_standard_shown_criteria_tip_at_their_thresholds():
    assert _all_ok(ST.shown_criteria("Standard", _shown(*_revs(-5.0 - EPS_OK, -5.0 + EPS_OK))))
    assert not _all_ok(ST.shown_criteria("Standard", _shown(*_revs(-5.0 + EPS_FAIL, -5.0 + EPS_OK))))
    assert not _all_ok(ST.shown_criteria("Standard", _shown(*_revs(-5.0 - EPS_OK, -5.0 - EPS_FAIL))))


def test_knappe_shown_criteria_tip_at_their_thresholds():
    assert _all_ok(ST.shown_criteria("Knappe Kapazität", _shown(*_revs(-15.0 - EPS_OK, -5.0 + EPS_OK))))
    assert not _all_ok(ST.shown_criteria("Knappe Kapazität", _shown(*_revs(-15.0 + EPS_FAIL, -5.0 + EPS_OK))))
    assert not _all_ok(ST.shown_criteria("Knappe Kapazität", _shown(*_revs(-15.0 - EPS_OK, -5.0 - EPS_FAIL))))


def test_reichliche_shown_criteria_tip_at_their_thresholds():
    assert _all_ok(ST.shown_criteria("Reichliche Kapazität", _shown(*_revs(-5.0 + EPS_OK, -2.0 + EPS_OK))))
    assert not _all_ok(ST.shown_criteria("Reichliche Kapazität", _shown(*_revs(-5.0 - EPS_FAIL, -2.0 + EPS_OK))))
    assert not _all_ok(ST.shown_criteria("Reichliche Kapazität", _shown(*_revs(-5.0 + EPS_OK, -2.0 - EPS_FAIL))))


def test_kleiner_aufschlag_shown_criterion_tips_at_its_threshold():
    assert _all_ok(ST.shown_criteria("Kleiner Preisaufschlag", _shown(*_revs(-8.0 + EPS_OK, 0.0))))
    assert not _all_ok(ST.shown_criteria("Kleiner Preisaufschlag", _shown(*_revs(-8.0 - EPS_FAIL, 0.0))))


def test_grosser_aufschlag_shown_criteria_tip_at_their_thresholds():
    assert _all_ok(ST.shown_criteria("Großer Preisaufschlag", _shown(*_revs(-12.0 - EPS_OK, -5.0 + EPS_OK))))
    assert not _all_ok(ST.shown_criteria("Großer Preisaufschlag", _shown(*_revs(-12.0 + EPS_FAIL, -5.0 + EPS_OK))))
    assert not _all_ok(ST.shown_criteria("Großer Preisaufschlag", _shown(*_revs(-12.0 - EPS_OK, -5.0 - EPS_FAIL))))


def test_shown_criteria_raises_key_error_for_unknown_preset():
    import pytest
    with pytest.raises(KeyError):
        ST.shown_criteria("Unbekanntes Preset", _shown(*_revs(0.0, 0.0)))
