"""Figuren (rvm_visualization): Zeitleiste, Ertragsvergleich ueber Kapazitaet - alle Achsen fest
(fixedrange), Grundstruktur der Traces."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import rvm_constants as C  # noqa: E402
import rvm_evaluation as E  # noqa: E402
import rvm_visualization as V  # noqa: E402


def _shown(seed=5, capacity=7):
    cfg = E.Config(n_epochs=30, capacity=capacity, r_hi=900.0, r_lo=400.0)
    pi_hi, pi_lo = E.demand_curve(30, 0.25, 0.35, seed)
    solved = E.solve_curve(cfg, pi_hi, pi_lo)
    return E.evaluate_sequence(cfg, pi_hi, pi_lo, solved, seed)


def test_timeline_figure_has_fixed_axes():
    shown = _shown()
    fig = V.timeline_figure(shown.seq, shown.accepted)
    assert fig.layout.xaxis.fixedrange is True
    assert fig.layout.yaxis.fixedrange is True


def test_timeline_figure_covers_every_non_none_epoch_across_its_traces():
    shown = _shown()
    fig = V.timeline_figure(shown.seq, shown.accepted, policies=(C.POLICY_FCFS,))
    n_points = sum(len(tr.x) for tr in fig.data)
    n_requests = sum(1 for c in shown.seq if c is not None)
    assert n_points == n_requests


def test_timeline_figure_supports_a_single_policy_row():
    shown = _shown()
    fig = V.timeline_figure(shown.seq, shown.accepted, policies=(C.POLICY_DP,))
    assert fig.layout.yaxis.range[1] - fig.layout.yaxis.range[0] < 1.5   # nur eine Zeile


def test_capacity_sweep_figure_has_fixed_axes_and_one_bar_group_per_capacity():
    cap_stats = E.capacity_sweep(30, 900.0, 400.0, 0.25, 0.35, 7, n=5)
    fig = V.capacity_sweep_figure(cap_stats, 7)
    assert fig.layout.xaxis.fixedrange is True
    assert fig.layout.yaxis.fixedrange is True
    assert len(fig.data) == 2   # FCFS, Littlewood (kein Hindsight)
    for tr in fig.data:
        assert len(tr.x) == len(cap_stats)


def test_capacity_sweep_figure_with_hindsight_adds_a_third_bar_trace():
    cap_stats = E.capacity_sweep(30, 900.0, 400.0, 0.25, 0.35, 7, n=5)
    fig = V.capacity_sweep_figure(cap_stats, 7, show_hindsight=True)
    assert len(fig.data) == 3


def test_capacity_sweep_figure_marks_the_current_capacity_in_the_labels():
    cap_stats = E.capacity_sweep(30, 900.0, 400.0, 0.25, 0.35, 7, n=5)
    fig = V.capacity_sweep_figure(cap_stats, 7)
    assert any("eingestellt" in x for x in fig.data[0].x)
