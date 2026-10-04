"""Unabhängige Orakel für das Revenue-Management-Modell: (1) die DP-Wertfunktion gegen den
Bellman-Optimalitäts-LP (scipy.optimize.linprog) und gegen Brute Force über ALLE Markov-Politiken
auf winzigen Instanzen, (2) Littlewoods Schutzniveaus gegen exakte Bruch-Arithmetik über die
vollständig aufgezählte Poisson-Binomial-Verteilung, (3) der exakte Erwartungsertrag jeder Politik
(Markov-Kette über die Restkapazität) und (4) eine unabhängige Neuberechnung der Erträge der
fünf Preset-Sequenzen."""

import itertools
import random
from fractions import Fraction

import numpy as np
import pytest

import rvm_constants as C
from rvm_evaluation import Config, evaluate_sequence, solve_curve
from rvm_scenario import draw_sequence, make_periods
from rvm_solve import dp_optimal, hindsight_oracle, littlewood_protection_levels, simulate

linprog = pytest.importorskip("scipy.optimize").linprog


def _random_curve(rng, n):
    hi, lo = [], []
    for _ in range(n):
        h = rng.choice([0.0, rng.random() * 0.6, rng.random() * 0.9])
        hi.append(h)
        lo.append(rng.random() * (1 - h) if rng.random() < 0.8 else 0.0)
    return hi, lo


def _bellman_lp(pi_hi, pi_lo, r_hi, r_lo, cap):
    """Kleinste Lösung von V[n][c] >= Erwartungswert jeder Annahme-Kombination (LP-Form der DP)."""
    n_ep = len(pi_hi)
    n_var = n_ep * (cap + 1)
    rows, rhs = [], []
    for n in range(n_ep):
        for c in range(cap + 1):
            for a_hi, a_lo in itertools.product((0, 1), repeat=2):
                if c == 0 and (a_hi or a_lo):
                    continue
                row = np.zeros(n_var)
                row[n * (cap + 1) + c] = -1.0
                const = 0.0
                for prob, accept, fare in ((pi_hi[n], a_hi, r_hi), (pi_lo[n], a_lo, r_lo),
                                           (1 - pi_hi[n] - pi_lo[n], 0, 0.0)):
                    if accept:
                        const += prob * fare
                        if n + 1 < n_ep:
                            row[(n + 1) * (cap + 1) + c - 1] += prob
                    elif n + 1 < n_ep:
                        row[(n + 1) * (cap + 1) + c] += prob
                rows.append(row)
                rhs.append(-const)
    res = linprog(np.ones(n_var), A_ub=np.array(rows), b_ub=np.array(rhs),
                  bounds=[(None, None)] * n_var, method="highs")
    return res.x.reshape(n_ep, cap + 1)


def test_dp_value_function_equals_bellman_lp():
    rng = random.Random(1)
    for _ in range(60):
        n_ep, cap = rng.randint(1, 8), rng.randint(0, 5)
        hi, lo = _random_curve(rng, n_ep)
        r_lo = rng.choice([1.0, 100.0, 400.0])
        r_hi = r_lo * rng.choice([1.0, 1.25, 2.0, 5.0, 10.0])
        v = dp_optimal(hi, lo, r_hi, r_lo, cap)
        lp = _bellman_lp(hi, lo, r_hi, r_lo, cap)
        for n in range(n_ep):
            for c in range(cap + 1):
                assert v[n][c] == pytest.approx(lp[n][c], abs=1e-6 * max(1.0, r_hi))


def test_dp_optimum_equals_best_of_all_markov_policies_bruteforce():
    rng = random.Random(2)
    for t in range(12):
        n_ep, cap = 3, 1 + t % 2
        hi, lo = _random_curve(rng, n_ep)
        r_lo, r_hi = 100.0, 100.0 * rng.choice([1.5, 3.0, 6.0])
        keys = [(n, c, k) for n in range(n_ep) for c in range(1, cap + 1) for k in ("hi", "lo")]
        outcomes = list(itertools.product(("hi", "lo", None), repeat=n_ep))
        weights = []
        for oc in outcomes:
            w = 1.0
            for n, k in enumerate(oc):
                w *= hi[n] if k == "hi" else lo[n] if k == "lo" else 1 - hi[n] - lo[n]
            weights.append(w)
        best = 0.0
        for bits in itertools.product((0, 1), repeat=len(keys)):
            policy = dict(zip(keys, bits))
            value = 0.0
            for w, oc in zip(weights, outcomes):
                c, rev = cap, 0.0
                for n, k in enumerate(oc):
                    if k is not None and c > 0 and policy[(n, c, k)]:
                        c -= 1
                        rev += r_hi if k == "hi" else r_lo
                value += w * rev
            best = max(best, value)
        assert dp_optimal(hi, lo, r_hi, r_lo, cap)[0][cap] == pytest.approx(best, abs=1e-9)


def _littlewood_exact(pi_hi, r_hi, r_lo):
    n_ep, ratio, levels = len(pi_hi), Fraction(r_lo) / Fraction(r_hi), []
    for n in range(n_ep):
        k = n_ep - n
        dist = [Fraction(0)] * (k + 1)
        for bits in itertools.product((0, 1), repeat=k):
            pr = Fraction(1)
            for b, e in zip(bits, range(n, n_ep)):
                p = Fraction(pi_hi[e])
                pr *= p if b else 1 - p
            dist[sum(bits)] += pr
        levels.append(next(y for y in range(k + 1) if sum(dist[y + 1:], Fraction(0)) <= ratio))
    return levels


def test_littlewood_levels_match_exact_fraction_enumeration():
    rng = random.Random(3)
    for t in range(80):
        n_ep = rng.randint(1, 10)
        hi, _lo = make_periods(n_ep, rng.choice([0.15, 0.25, 0.35]), 0.3, t)
        mult = rng.choice(C.R_HI_MULT_OPTIONS)
        assert littlewood_protection_levels(hi, mult * C.R_LO, C.R_LO) == _littlewood_exact(hi, mult * C.R_LO, C.R_LO)
    # Handrechnung: zwei Epochen mit pi=0.5 -> P(D>0)=0.75, P(D>1)=0.25
    assert littlewood_protection_levels([0.5, 0.5], 4.0, 2.0)[0] == 1   # Verhältnis 0.5
    assert littlewood_protection_levels([0.5, 0.5], 4.0, 1.0)[0] == 1   # Verhältnis 0.25, Gleichheit zählt
    assert littlewood_protection_levels([0.5, 0.5], 5.0, 1.0)[0] == 2   # Verhältnis 0.2


def _exact_policy_value(hi, lo, r_hi, r_lo, cap, accept):
    dist, revenue = {cap: 1.0}, 0.0
    for n in range(len(hi)):
        nxt = {}
        for c, p in dist.items():
            for k, pk, fare in (("hi", hi[n], r_hi), ("lo", lo[n], r_lo), (None, 1 - hi[n] - lo[n], 0.0)):
                if pk <= 0:
                    continue
                if k is not None and c > 0 and accept(n, c, k, fare):
                    nxt[c - 1] = nxt.get(c - 1, 0.0) + p * pk
                    revenue += p * pk * fare
                else:
                    nxt[c] = nxt.get(c, 0.0) + p * pk
        dist = nxt
    return revenue


def test_exact_policy_values_dp_attains_optimum_and_others_stay_below():
    rng = random.Random(4)
    for t in range(60):
        n_ep, cap = rng.randint(1, 14), rng.randint(0, 6)
        hm, lm = rng.choice(list(C.DEMAND_MIX_PARAMS.values()))
        hi, lo = make_periods(n_ep, hm, lm, t)
        r_hi = C.R_LO * rng.choice(C.R_HI_MULT_OPTIONS)
        v = dp_optimal(hi, lo, r_hi, C.R_LO, cap)
        levels = littlewood_protection_levels(hi, r_hi, C.R_LO)
        value_dp = _exact_policy_value(hi, lo, r_hi, C.R_LO, cap, lambda n, c, k, f: f + v[n + 1][c - 1] >= v[n + 1][c])
        value_fcfs = _exact_policy_value(hi, lo, r_hi, C.R_LO, cap, lambda n, c, k, f: True)
        value_lw = _exact_policy_value(hi, lo, r_hi, C.R_LO, cap, lambda n, c, k, f: k == "hi" or c > levels[n])
        assert value_dp == pytest.approx(v[0][cap], abs=1e-8)
        assert value_fcfs <= v[0][cap] + 1e-8 and value_lw <= v[0][cap] + 1e-8


def test_simulate_and_hindsight_against_independent_playback():
    rng = random.Random(5)
    for t in range(60):
        n_ep, cap = rng.randint(1, 12), rng.randint(0, 5)
        hi, lo = make_periods(n_ep, 0.25, 0.35, t)
        r_hi = C.R_LO * rng.choice(C.R_HI_MULT_OPTIONS)
        seq = draw_sequence(hi, lo, t)
        levels = littlewood_protection_levels(hi, r_hi, C.R_LO)
        revenue_lw, c = 0.0, cap
        for n, k in enumerate(seq):
            if k is not None and c > 0 and (k == "hi" or c > levels[n]):
                c -= 1
                revenue_lw += r_hi if k == "hi" else C.R_LO
        assert simulate(seq, "littlewood", cap, r_hi, C.R_LO, levels=levels)["revenue"] == revenue_lw
        fares = [r_hi if k == "hi" else C.R_LO for k in seq if k is not None]
        best = max(sum(comb) for m in range(min(cap, len(fares)) + 1) for comb in itertools.combinations(fares, m))
        assert hindsight_oracle(seq, cap, r_hi, C.R_LO) == best


def test_preset_sequences_recomputed_with_lp_decisions():
    expected = {"Standard": (3800.0, 4400.0, 4400.0), "Knappe Kapazität": (2100.0, 3100.0, 3100.0),
                "Reichliche Kapazität": (6000.0, 6000.0, 6000.0), "Kleiner Preisaufschlag": (3000.0, 3000.0, 3000.0),
                "Großer Preisaufschlag": (6000.0, 8800.0, 8800.0)}   # tools/PRESET_SWEEP.md
    for name, p in C.PRESETS.items():
        hm, lm = C.DEMAND_MIX_PARAMS[p["demand_mix"]]
        hi, lo = make_periods(p["n_epochs"], hm, lm, p["seed"])
        seq = draw_sequence(hi, lo, p["seed"])
        r_hi, cap = p["r_hi_mult"] * C.R_LO, p["capacity"]
        lp = _bellman_lp(hi, lo, r_hi, C.R_LO, cap)
        levels = littlewood_protection_levels(hi, r_hi, C.R_LO)

        def play(accept):
            c, rev = cap, 0.0
            for n, k in enumerate(seq):
                fare = r_hi if k == "hi" else C.R_LO
                if k is not None and c > 0 and accept(n, c, k, fare):
                    c -= 1
                    rev += fare
            return rev

        def nxt(n):
            return lp[n + 1] if n + 1 < len(hi) else [0.0] * (cap + 1)

        got = (play(lambda n, c, k, f: True), play(lambda n, c, k, f: k == "hi" or c > levels[n]),
               play(lambda n, c, k, f: f + nxt(n)[c - 1] >= nxt(n)[c] - 1e-9))
        assert got == expected[name]
        cfg = Config(p["n_epochs"], cap, r_hi)
        shown = evaluate_sequence(cfg, hi, lo, solve_curve(cfg, hi, lo), p["seed"])
        assert (shown.revenue["fcfs"], shown.revenue["littlewood"], shown.revenue["dp"]) == got
