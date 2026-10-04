"""Politiken und Loeser: FCFS, Littlewoods geschlossene Schutzformel (1972), DP (exakte Rueckwaerts-
Induktion), Hindsight-Orakel.

Unveraendert uebernommen aus seefracht-planung/messreihe_revenue/revenue.py (Funktionen dp_optimal,
dp_accept, remaining_hi_dists, littlewood_protection_levels, simulate, hindsight_oracle) - bereits
gegen eine Handinstanz und mehrere Konsistenzchecks verifiziert (messreihe_revenue/check.py, 0
Abweichungen), nicht neu geschrieben. Nur Standardbibliothek, kein scipy noetig.

Wichtig fuer die App (siehe Plan Abschnitt 3 und 15): Littlewood ist die operative Empfehlung der
Hauptansicht, NICHT die DP-Politik - Littlewood kommt empirisch verblueffend nah ans DP-Optimum
(-0,06 % bis -1,29 % in den fuenf Presets, bis etwa -5 % im gesamten Reglerraster), DP dient nur als Referenz im
Exakt-Tab. DP-Optimalitaet gilt nur im ERWARTUNGSWERT ueber die Zukunftsunsicherheit an jedem
Entscheidungspunkt, nicht pfadweise fuer eine einzelne realisierte Sequenz - siehe check.py Punkt 3."""


def dp_optimal(pi_hi, pi_lo, r_hi, r_lo, capacity):
    """Rueckwaerts-Induktion: V[n][c] = optimaler Erwartungswert ab Epoche n (0-indexiert) mit c freien
    Slots. Liefert V (Liste von Listen, Laenge N+1 x C+1) - V[0][capacity] ist der optimale erwartete
    Gesamtertrag. Aus V lassen sich die optimalen Annahme-Entscheidungen ablesen (Bid-Preis-Vergleich)."""
    n_epochs = len(pi_hi)
    V = [[0.0] * (capacity + 1) for _ in range(n_epochs + 1)]
    for n in range(n_epochs - 1, -1, -1):
        hi, lo = pi_hi[n], pi_lo[n]
        none = 1.0 - hi - lo
        for c in range(capacity + 1):
            v_stay = V[n + 1][c]
            v_hi = max(r_hi + V[n + 1][c - 1], v_stay) if c > 0 else v_stay
            v_lo = max(r_lo + V[n + 1][c - 1], v_stay) if c > 0 else v_stay
            V[n][c] = hi * v_hi + lo * v_lo + none * v_stay
    return V


def dp_accept(V, n, c, fare):
    if c <= 0:
        return False
    return fare + V[n + 1][c - 1] >= V[n + 1][c]


def remaining_hi_dists(pi_hi):
    """dists[n] = Wahrscheinlichkeitsverteilung der Zahl der Premium-Ankuenfte in den Epochen n..N-1
    (Poisson-Binomial, exakt per Faltung). dists[N] = [1.0] (nichts mehr uebrig)."""
    n_epochs = len(pi_hi)
    dists = [None] * (n_epochs + 1)
    dists[n_epochs] = [1.0]
    for n in range(n_epochs - 1, -1, -1):
        prev = dists[n + 1]
        p = pi_hi[n]
        new = [0.0] * (len(prev) + 1)
        for k, v in enumerate(prev):
            new[k] += v * (1 - p)
            new[k + 1] += v * p
        dists[n] = new
    return dists


def littlewood_protection_levels(pi_hi, r_hi, r_lo):
    """y*(n) = kleinstes y mit P(verbleibende Premium-Nachfrage ab n > y) <= r_lo/r_hi (Littlewood 1972).
    Spot wird bei (n, c) nur angenommen, wenn c > y*(n) - sonst wird die Kapazitaet fuer erwartete
    Premium-Nachfrage geschuetzt."""
    dists = remaining_hi_dists(pi_hi)
    ratio = r_lo / r_hi
    levels = []
    for n in range(len(pi_hi)):
        dist = dists[n]
        tail = 0.0
        y = len(dist) - 1
        for k in range(len(dist) - 1, -1, -1):
            if tail <= ratio:
                y = k
            tail += dist[k]
        levels.append(y)
    return levels


def simulate(seq, policy, capacity, r_hi, r_lo, **kw):
    """policy in {'fcfs', 'littlewood', 'dp'}. Gibt (revenue, n_accepted_hi, n_accepted_lo,
    n_rejected_hi, n_rejected_lo) zurueck. Ohne No-Shows: angenommen = tatsaechlich befoerdert."""
    c = capacity
    revenue = 0.0
    acc_hi = acc_lo = rej_hi = rej_lo = 0
    if policy == "littlewood":
        levels = kw["levels"]
    elif policy == "dp":
        V = kw["V"]
    for n, cls in enumerate(seq):
        if cls is None:
            continue
        fare = r_hi if cls == "hi" else r_lo
        if policy == "fcfs":
            accept = c > 0
        elif policy == "littlewood":
            accept = c > 0 if cls == "hi" else c > levels[n]
        elif policy == "dp":
            accept = dp_accept(V, n, c, fare)
        else:
            raise ValueError(policy)
        if accept:
            c -= 1
            revenue += fare
            if cls == "hi":
                acc_hi += 1
            else:
                acc_lo += 1
        else:
            if cls == "hi":
                rej_hi += 1
            else:
                rej_lo += 1
    return dict(revenue=revenue, acc_hi=acc_hi, acc_lo=acc_lo, rej_hi=rej_hi, rej_lo=rej_lo)


def hindsight_oracle(seq, capacity, r_hi, r_lo):
    """Rueckblickend beste Auswahl: alle Anfragen nach Preis sortiert, die besten C nehmen (kein
    No-Show-Risiko in diesem Basismodell, daher immer erreichbar - reine obere Schranke fuer den
    Wert von Information, nicht online umsetzbar)."""
    fares = sorted((r_hi if c == "hi" else r_lo) for c in seq if c is not None)
    fares.reverse()
    return sum(fares[:capacity])
