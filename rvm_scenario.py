"""Buchungsszenario: Nachfragekurve und eine konkrete gezogene Buchungssequenz.

Unveraendert uebernommen aus seefracht-planung/messreihe_revenue/revenue.py (Funktionen make_periods,
draw_sequence) - bereits gegen eine Handinstanz und mehrere Konsistenzchecks verifiziert
(messreihe_revenue/check.py, 0 Abweichungen), nicht neu geschrieben. Nur Standardbibliothek.

Zwei Frachtklassen - Spot (niedriger Preis, bucht ueberwiegend frueh) und Premium (hoher Preis, bucht
ueberwiegend spaet) - bewerben sich laufend um C Container-Slots auf einer Abfahrt. Jede der N
Buchungsgelegenheiten (diskrete Epochen statt Kalenderzeit, Standardformulierung der Revenue-
Management-Literatur) bringt mit Wahrscheinlichkeit pi_hi(n) eine Premium-Anfrage, mit pi_lo(n) eine
Spot-Anfrage, sonst keine."""
import random


def make_periods(n_epochs, pi_hi_max, pi_lo_max, seed):
    """pi_hi(n) steigt linear ueber die Epochen, pi_lo(n) faellt - realistische Spot-frueh/Premium-spaet-
    Nachfragekurve. Etwas Rauschen je Instanz, damit nicht jede Route exakt dieselbe Kurve hat."""
    rng = random.Random(seed)
    pi_hi, pi_lo = [], []
    for n in range(n_epochs):
        frac = n / (n_epochs - 1) if n_epochs > 1 else 0.0
        hi = pi_hi_max * (0.15 + 0.85 * frac) * rng.uniform(0.85, 1.15)
        lo = pi_lo_max * (1.0 - 0.85 * frac) * rng.uniform(0.85, 1.15)
        hi = max(0.0, min(hi, 0.9))
        lo = max(0.0, min(lo, 0.9 - hi))
        pi_hi.append(hi)
        pi_lo.append(lo)
    return pi_hi, pi_lo


def draw_sequence(pi_hi, pi_lo, seed):
    """Eine konkrete Realisierung: Liste ueber die Epochen, Eintrag 'hi'/'lo'/None."""
    rng = random.Random(seed)
    seq = []
    for hi, lo in zip(pi_hi, pi_lo):
        u = rng.random()
        if u < hi:
            seq.append("hi")
        elif u < hi + lo:
            seq.append("lo")
        else:
            seq.append(None)
    return seq
