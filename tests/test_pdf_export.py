"""PDF-Export (rvm_pdf_export): Sonderzeichen-Bereinigung (fpdf2 stuerzt bei "-", "EUR"-Zeichen, Emoji
ab), Inhalt, Randfaelle."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import rvm_evaluation as E  # noqa: E402
from rvm_pdf_export import generate_rvm_pdf, pdf_text, verdict_text  # noqa: E402


def _shown(seed=5, capacity=7):
    cfg = E.Config(n_epochs=30, capacity=capacity, r_hi=900.0, r_lo=400.0)
    pi_hi, pi_lo = E.demand_curve(30, 0.25, 0.35, seed)
    solved = E.solve_curve(cfg, pi_hi, pi_lo)
    return E.evaluate_sequence(cfg, pi_hi, pi_lo, solved, seed)


def test_pdf_text_replaces_characters_that_crash_fpdf2_core_fonts():
    assert "-" in pdf_text("Gedankenstrich – hier")
    assert "–" not in pdf_text("Gedankenstrich – hier")
    assert "EUR" in pdf_text("Preis: 5€")
    assert "€" not in pdf_text("Preis: 5€")
    assert pdf_text("Emoji 🎟️🐌📐") == pdf_text(pdf_text("Emoji 🎟️🐌📐"))  # idempotent, kein Crash


def test_pdf_text_is_latin1_safe_after_replacement():
    pdf_text("ä ö ü ß – € ≥ ≤ → ≈ ± · „" '"' "'" "⚠️ ✅ ℹ️ 🐌 📐 🎯 📊 🎟️ 🔮").encode("latin-1")


def test_verdict_text_covers_better_worse_unclear_and_empty():
    for v in (E.Verdict("better", -2.0, 0.5, 20), E.Verdict("worse", 2.0, 0.5, 20),
             E.Verdict("unclear", 0.1, 0.5, 20), E.Verdict("unclear", 0.0, 0.0, 0)):
        text = verdict_text(v)
        assert isinstance(text, str) and len(text) > 0
        pdf_text(text).encode("latin-1")


def test_generate_pdf_produces_nonempty_bytes_for_a_typical_scenario():
    shown = _shown()
    cfg = E.Config(n_epochs=30, capacity=7, r_hi=900.0, r_lo=400.0)
    stats = E.population_stats(cfg, 0.25, 0.35, n_curve_seeds=5, draws_per_seed=2)
    v = E.verdict_from_population(stats)
    pdf_bytes = generate_rvm_pdf(7, 30, 900.0, 400.0, "ausgewogen", 5, shown, stats, v)
    assert isinstance(pdf_bytes, bytes) and len(pdf_bytes) > 500
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_pdf_handles_zero_capacity_without_crashing():
    cfg = E.Config(n_epochs=20, capacity=0, r_hi=900.0, r_lo=400.0)
    pi_hi, pi_lo = E.demand_curve(20, 0.25, 0.35, 0)
    solved = E.solve_curve(cfg, pi_hi, pi_lo)
    shown = E.evaluate_sequence(cfg, pi_hi, pi_lo, solved, 0)
    stats = E.population_stats(cfg, 0.25, 0.35, n_curve_seeds=3, draws_per_seed=1)
    v = E.verdict_from_population(stats)
    pdf_bytes = generate_rvm_pdf(0, 20, 900.0, 400.0, "ausgewogen", 0, shown, stats, v)
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_pdf_handles_large_multiplier_labels_without_crashing():
    shown = _shown()
    cfg = E.Config(n_epochs=30, capacity=7, r_hi=2000.0, r_lo=400.0)
    stats = E.population_stats(cfg, 0.25, 0.35, n_curve_seeds=3, draws_per_seed=1)
    v = E.verdict_from_population(stats)
    pdf_bytes = generate_rvm_pdf(7, 30, 2000.0, 400.0, "premium-reich", 5, shown, stats, v)
    assert pdf_bytes[:4] == b"%PDF"
