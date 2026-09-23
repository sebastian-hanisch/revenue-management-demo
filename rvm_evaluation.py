"""Auswertung: eine Sequenz loesen/simulieren, Population ueber viele Nachfragekurven (Preset-Abnahme,
sweep_data.json-Reproduktion), Ertragsvergleich ueber Kapazitaet, gepaartes Urteil (Littlewood gegen
FCFS). Reine Rechnung ohne Streamlit.

Alle Ertragsvergleiche sind Prozent-Abstand zum DP-Optimum: gap_pct = (mean_policy / mean_dp - 1) * 100
(negativ = schlechter als DP) - dieselbe Kennzahl wie in messreihe_revenue/sweep.py und
dump_sweep.py, damit die Presets sweep_data.json exakt reproduzieren (Plan Abschnitt 7)."""
import math
import statistics
from dataclasses import dataclass, field

import rvm_constants as C
from rvm_scenario import draw_sequence, make_periods
from rvm_solve import dp_optimal, hindsight_oracle, littlewood_protection_levels, simulate


@dataclass(frozen=True)
class Config:
    """Alle Einstellungen, die eine Nachfragekurve/Politiken bestimmen (ohne Seed)."""
    n_epochs: int
    capacity: int
    r_hi: float
    r_lo: float = C.R_LO

    @property
    def ratio(self):
        return self.r_hi / self.r_lo


def config_from_controls(capacity, n_epochs, r_hi_mult, demand_mix, r_lo=C.R_LO):
    pi_hi_max, pi_lo_max = C.DEMAND_MIX_PARAMS[demand_mix]
    return Config(n_epochs=n_epochs, capacity=capacity, r_hi=r_hi_mult * r_lo, r_lo=r_lo), pi_hi_max, pi_lo_max


# ---------------------------------------------------------------------------------------------------
# Eine Nachfragekurve loesen (DP + Littlewood-Schutzniveaus), eine Sequenz simulieren
# ---------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Solved:
    pi_hi: tuple
    pi_lo: tuple
    V: tuple            # DP-Wertfunktion (Liste von Listen), tuple-verpackt fuer Hashbarkeit im Cache
    levels: tuple        # Littlewood-Schutzniveaus je Epoche


def solve_curve(cfg, pi_hi, pi_lo):
    V = dp_optimal(pi_hi, pi_lo, cfg.r_hi, cfg.r_lo, cfg.capacity)
    levels = littlewood_protection_levels(pi_hi, cfg.r_hi, cfg.r_lo)
    return Solved(tuple(pi_hi), tuple(pi_lo), tuple(tuple(row) for row in V), tuple(levels))


def demand_curve(n_epochs, pi_hi_max, pi_lo_max, curve_seed):
    return make_periods(n_epochs, pi_hi_max, pi_lo_max, curve_seed)


def accepted_sequence(seq, policy, capacity, r_hi, r_lo, **kw):
    """Wiederholt simulate()s Annahme-Logik, aber haelt je Epoche fest, ob angenommen wurde (None dort,
    wo in dieser Epoche keine Anfrage ankam) - fuer die Zeitleisten-Grafik (Muster dump_sweep.py)."""
    from rvm_solve import dp_accept

    c = capacity
    out = []
    levels = kw.get("levels")
    V = kw.get("V")
    for n, cls in enumerate(seq):
        if cls is None:
            out.append(None)
            continue
        fare = r_hi if cls == "hi" else r_lo
        if policy == C.POLICY_FCFS:
            accept = c > 0
        elif policy == C.POLICY_LITTLEWOOD:
            accept = c > 0 if cls == "hi" else c > levels[n]
        elif policy == C.POLICY_DP:
            accept = dp_accept(V, n, c, fare)
        else:
            raise ValueError(policy)
        if accept:
            c -= 1
        out.append(accept)
    return out


@dataclass(frozen=True)
class SequenceResult:
    seed: int
    seq: tuple
    levels: tuple
    revenue: dict         # policy -> revenue
    detail: dict           # policy -> volles simulate()-Ergebnis (revenue, acc_hi, acc_lo, rej_hi, rej_lo)
    accepted: dict          # policy -> Liste True/False/None je Epoche (fuer die Zeitleiste)
    hindsight: float


def evaluate_sequence(cfg, pi_hi, pi_lo, solved, draw_seed):
    """Zieht EINE Sequenz und wertet alle drei Politiken plus Hindsight darauf aus (gepaart: dieselbe
    Sequenz fuer alle Politiken)."""
    seq = draw_sequence(pi_hi, pi_lo, draw_seed)
    V = [list(row) for row in solved.V]
    levels = list(solved.levels)
    detail = {
        C.POLICY_FCFS: simulate(seq, C.POLICY_FCFS, cfg.capacity, cfg.r_hi, cfg.r_lo),
        C.POLICY_LITTLEWOOD: simulate(seq, C.POLICY_LITTLEWOOD, cfg.capacity, cfg.r_hi, cfg.r_lo, levels=levels),
        C.POLICY_DP: simulate(seq, C.POLICY_DP, cfg.capacity, cfg.r_hi, cfg.r_lo, V=V),
    }
    accepted = {
        C.POLICY_FCFS: accepted_sequence(seq, C.POLICY_FCFS, cfg.capacity, cfg.r_hi, cfg.r_lo),
        C.POLICY_LITTLEWOOD: accepted_sequence(seq, C.POLICY_LITTLEWOOD, cfg.capacity, cfg.r_hi, cfg.r_lo, levels=levels),
        C.POLICY_DP: accepted_sequence(seq, C.POLICY_DP, cfg.capacity, cfg.r_hi, cfg.r_lo, V=V),
    }
    revenue = {k: v["revenue"] for k, v in detail.items()}
    hs = hindsight_oracle(seq, cfg.capacity, cfg.r_hi, cfg.r_lo)
    return SequenceResult(draw_seed, tuple(seq), tuple(levels), revenue, detail, accepted, hs)


# ---------------------------------------------------------------------------------------------------
# Population ueber viele Nachfragekurven (Preset-Abnahme UND Kernabschnitt-Basis, je nach draws_per_seed)
# ---------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class PopulationStats:
    mean_fcfs: float
    mean_littlewood: float
    mean_dp: float
    mean_hindsight: float
    fcfs_gap_pct: float
    littlewood_gap_pct: float
    hindsight_gap_pct: float
    n: int
    revenues: dict = field(default_factory=dict)   # policy -> Liste aller Einzelwerte (fuer das Urteil)


def population_stats(cfg, pi_hi_max, pi_lo_max, n_curve_seeds=C.POPULATION_CURVE_SEEDS,
                     draws_per_seed=C.POPULATION_DRAWS_PER_SEED, curve_seed_start=0):
    """Reproduziert messreihe_revenue/dump_sweep.py stats_for(): n_curve_seeds Nachfragekurven,
    draws_per_seed gezogene Sequenzen je Kurve, gepaart je Sequenz ueber alle Politiken. Mit den
    Standardwerten (30 x 20 = 600) reproduziert das sweep_data.json exakt (Plan Abschnitt 7)."""
    revs = {C.POLICY_FCFS: [], C.POLICY_LITTLEWOOD: [], C.POLICY_DP: [], "hindsight": []}
    for i in range(n_curve_seeds):
        curve_seed = curve_seed_start + i
        pi_hi, pi_lo = make_periods(cfg.n_epochs, pi_hi_max, pi_lo_max, curve_seed)
        V = dp_optimal(pi_hi, pi_lo, cfg.r_hi, cfg.r_lo, cfg.capacity)
        levels = littlewood_protection_levels(pi_hi, cfg.r_hi, cfg.r_lo)
        for s in range(draws_per_seed):
            seq = draw_sequence(pi_hi, pi_lo, curve_seed * 1000 + s)
            revs[C.POLICY_FCFS].append(simulate(seq, C.POLICY_FCFS, cfg.capacity, cfg.r_hi, cfg.r_lo)["revenue"])
            revs[C.POLICY_LITTLEWOOD].append(simulate(seq, C.POLICY_LITTLEWOOD, cfg.capacity, cfg.r_hi, cfg.r_lo, levels=levels)["revenue"])
            revs[C.POLICY_DP].append(simulate(seq, C.POLICY_DP, cfg.capacity, cfg.r_hi, cfg.r_lo, V=V)["revenue"])
            revs["hindsight"].append(hindsight_oracle(seq, cfg.capacity, cfg.r_hi, cfg.r_lo))
    means = {k: statistics.fmean(v) for k, v in revs.items()}
    ref = means[C.POLICY_DP]
    return PopulationStats(
        mean_fcfs=means[C.POLICY_FCFS], mean_littlewood=means[C.POLICY_LITTLEWOOD], mean_dp=means[C.POLICY_DP],
        mean_hindsight=means["hindsight"],
        fcfs_gap_pct=gap_pct(means[C.POLICY_FCFS], ref),
        littlewood_gap_pct=gap_pct(means[C.POLICY_LITTLEWOOD], ref),
        hindsight_gap_pct=gap_pct(means["hindsight"], ref),
        n=len(revs[C.POLICY_DP]), revenues=revs,
    )


def population_from_controls(capacity, n_epochs, r_hi_mult, demand_mix, r_lo=C.R_LO, **kw):
    cfg, pi_hi_max, pi_lo_max = config_from_controls(capacity, n_epochs, r_hi_mult, demand_mix, r_lo)
    return population_stats(cfg, pi_hi_max, pi_lo_max, **kw)


# ---------------------------------------------------------------------------------------------------
# Ertragsvergleich ueber Kapazitaet (Kernabschnitt, Plan Abschnitt 6)
# ---------------------------------------------------------------------------------------------------
def capacity_levels_around(capacity, delta=C.CAPACITY_SWEEP_DELTA, bounds=C.CAPACITY_RANGE):
    lo, hi = bounds
    levels = sorted({max(lo, capacity - delta), capacity, min(hi, capacity + delta)})
    return levels


def capacity_sweep(n_epochs, r_hi, r_lo, pi_hi_max, pi_lo_max, capacity, delta=C.CAPACITY_SWEEP_DELTA,
                   n=C.SAMPLE_INSTANCES):
    """FCFS-/Littlewood-Aufschlag gegen DP ueber drei Kapazitaetsstufen um den eingestellten Wert,
    Basis: n Sequenzen derselben Einstellung je Stufe (Plan Abschnitt 6, nicht der eingestellte Seed)."""
    out = {}
    for cap in capacity_levels_around(capacity, delta):
        cfg = Config(n_epochs=n_epochs, capacity=cap, r_hi=r_hi, r_lo=r_lo)
        out[cap] = population_stats(cfg, pi_hi_max, pi_lo_max, n_curve_seeds=n, draws_per_seed=1)
    return out


# ---------------------------------------------------------------------------------------------------
# Gepaartes Urteil: Littlewood gegen FCFS (n Sequenzen derselben Einstellung, nicht der gezeigte Seed)
# ---------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Verdict:
    kind: str       # "better" (Littlewood verdient mehr) | "worse" | "unclear"
    diff: float      # Littlewood minus FCFS je Sequenz (positiv = Littlewood besser)
    se: float
    n: int


def _se(d):
    return statistics.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0


def verdict_from_population(stats):
    """Gepaarte Differenz Littlewood - FCFS ueber die Einzelsequenzen einer PopulationStats (dieselbe
    Sequenz je Instanz fuer beide Politiken - population_stats() zieht sie gepaart). 'Klar' heisst:
    |Differenz| > VERDICT_Z Standardfehler der gepaarten Differenz je Sequenz."""
    lit, fcfs = stats.revenues.get(C.POLICY_LITTLEWOOD), stats.revenues.get(C.POLICY_FCFS)
    if not lit or not fcfs:
        return Verdict("unclear", 0.0, 0.0, 0)
    d = [x - y for x, y in zip(lit, fcfs)]
    diff, se = statistics.fmean(d), _se(d)
    if se == 0:
        kind = "unclear" if diff == 0 else ("better" if diff > 0 else "worse")
    else:
        kind = "unclear" if abs(diff) <= C.VERDICT_Z * se else ("better" if diff > 0 else "worse")
    return Verdict(kind, diff, se, len(d))


# ---------------------------------------------------------------------------------------------------
# Kennzahlen der Hauptansicht (auf der EINEN gezeigten Sequenz)
# ---------------------------------------------------------------------------------------------------
def gap_pct(value, ref):
    return (value / ref - 1) * 100 if ref else 0.0


def rejected_hi_count(detail, policy):
    return detail[policy]["rej_hi"]
