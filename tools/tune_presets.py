"""Preset-Abstimmung: traegt die Geschichte jedes Presets in der POPULATION (600 Stichproben,
reproduziert sweep_data.json) und an der EINEN Sequenz, die das Preset zeigt?

Aufruf (im Projektordner): ./venv/Scripts/python.exe tools/tune_presets.py <modus>
  population   Population-Kriterien aller Presets (haengen nicht vom Seed ab)
  seeds        je Preset: welcher Seed (>= POPULATION_CURVE_SEEDS) traegt shown_criteria() und liegt
               dabei am naechsten am Populationsmittel (kein Cherry-Picking des dramatischsten Falls)

Grundsatz (aus den Hafen-/Seefracht-Demos): den Seed nicht nach dem schoensten Einzelfall waehlen,
sondern typisch; der Preset-Seed liegt AUSSERHALB der Population (Seeds ab POPULATION_CURVE_SEEDS).
Alles ist deterministisch (kein Loeser mit Zeitgrenze): die Ergebnisse haengen nicht vom Rechner ab."""
import sys

sys.path.insert(0, ".")
import rvm_constants as C
import rvm_evaluation as E
import rvm_stories as ST

NAMES = list(C.PRESETS)
POPULATION = C.POPULATION_CURVE_SEEDS
SEED_SEARCH = range(POPULATION, POPULATION + 800)


def cfg_of(name):
    p = C.PRESETS[name]
    pi_hi_max, pi_lo_max = C.DEMAND_MIX_PARAMS[p["demand_mix"]]
    cfg = E.Config(n_epochs=p["n_epochs"], capacity=p["capacity"], r_hi=p["r_hi_mult"] * C.R_LO, r_lo=C.R_LO)
    return cfg, pi_hi_max, pi_lo_max


def cmd_population():
    for name in NAMES:
        cfg, pi_hi_max, pi_lo_max = cfg_of(name)
        stats = E.population_stats(cfg, pi_hi_max, pi_lo_max)
        print(f"\n### {name}  (capacity={cfg.capacity}, r_hi={cfg.r_hi:.0f}, r_lo={cfg.r_lo:.0f})")
        for ok, text in ST.criteria(name, stats):
            print(("  OK   " if ok else "  FAIL ") + text)
        print(f"  mean_fcfs={stats.mean_fcfs:.1f} mean_littlewood={stats.mean_littlewood:.1f} "
              f"mean_dp={stats.mean_dp:.1f} mean_hindsight={stats.mean_hindsight:.1f} n={stats.n}")


def cmd_seeds():
    for name in NAMES:
        cfg, pi_hi_max, pi_lo_max = cfg_of(name)
        stats = E.population_stats(cfg, pi_hi_max, pi_lo_max)
        mean_fcfs, mean_lit, mean_dp = stats.mean_fcfs, stats.mean_littlewood, stats.mean_dp
        best = None
        holds_count = 0
        for seed in SEED_SEARCH:
            pi_hi, pi_lo = E.demand_curve(cfg.n_epochs, pi_hi_max, pi_lo_max, seed)
            solved = E.solve_curve(cfg, pi_hi, pi_lo)
            shown = E.evaluate_sequence(cfg, pi_hi, pi_lo, solved, seed)
            if not all(ok for ok, _ in ST.shown_criteria(name, shown)):
                continue
            holds_count += 1
            rf, rl, rd = shown.revenue[C.POLICY_FCFS], shown.revenue[C.POLICY_LITTLEWOOD], shown.revenue[C.POLICY_DP]
            score = abs(rf - mean_fcfs) + abs(rl - mean_lit) + abs(rd - mean_dp)
            if best is None or score < best[0]:
                best = (score, seed, shown)
        print(f"\n### {name}: traegt an {holds_count} von {len(SEED_SEARCH)} Seeds (Suchbereich "
              f"{SEED_SEARCH.start}..{SEED_SEARCH.stop - 1}); Populationsmittel FCFS={mean_fcfs:.1f}, "
              f"Littlewood={mean_lit:.1f}, DP={mean_dp:.1f}")
        if best:
            score, seed, shown = best
            print(f"  bester Seed (naechster am Populationsmittel): {seed}  "
                  f"FCFS={shown.revenue[C.POLICY_FCFS]:.1f}  Littlewood={shown.revenue[C.POLICY_LITTLEWOOD]:.1f}  "
                  f"DP={shown.revenue[C.POLICY_DP]:.1f}")
        else:
            print("  KEIN Seed im Suchbereich erfuellt shown_criteria() - Kriterien oder Suchbereich pruefen.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "population"
    {"population": cmd_population, "seeds": cmd_seeds}.get(mode, lambda: sys.exit(__doc__))()
