"""Wiederverwendbares Panel: Kennzahlen (2 x 2), Zeitleiste, Baustein-Tabs (FCFS, Littlewood, DP exakt,
Vergleich) - Plan Abschnitt 6/8."""
import pandas as pd
import streamlit as st

import rvm_constants as C
import rvm_evaluation as E
import rvm_visualization as V


def fmt_money(v):
    return f"{v:,.0f}".replace(",", ".")


def fmt_pct(v):
    return f"{v:+.2f} %"


def render_metrics(columns, shown):
    """Vier Kennzahlen (Plan Abschnitt 6): Ertrag (Littlewood), Ertrag (FCFS), Abstand zum DP-Optimum
    (Littlewood), abgewiesene Premium-Anfragen (FCFS) - alle auf der EINEN gezeigten Sequenz."""
    m = columns
    lit_rev = shown.revenue[C.POLICY_LITTLEWOOD]
    fcfs_rev = shown.revenue[C.POLICY_FCFS]
    dp_rev = shown.revenue[C.POLICY_DP]
    gap = E.gap_pct(lit_rev, dp_rev)
    rej_hi_fcfs = E.rejected_hi_count(shown.detail, C.POLICY_FCFS)
    m[0].metric("Ertrag (Littlewood)", fmt_money(lit_rev),
               help="Ertrag der operativen Empfehlung (Littlewoods Schutzformel) auf der gezeigten Sequenz.")
    m[1].metric("Ertrag (FCFS)", fmt_money(fcfs_rev), delta=f"{fcfs_rev - lit_rev:+,.0f}".replace(",", "."),
               delta_color="inverse", help="Ertrag der blinden Annahme-Regel (Kontrast-Baseline) auf derselben Sequenz; Delta = FCFS minus Littlewood.")
    m[2].metric("Abstand zum DP-Optimum", fmt_pct(gap),
               help="Ertrag (Littlewood) gegen den echten DP-Optimalwert auf dieser Sequenz; negativ = etwas unter dem Optimum.")
    m[3].metric("Abgewiesene Premium-Anfragen (FCFS)", str(rej_hi_fcfs),
               help="Wie viele Premium-Anfragen FCFS auf dieser Sequenz ablehnen musste, weil vorher zu viele Spot-Buchungen angenommen wurden.")


def render_timeline(key, shown, policies=(C.POLICY_FCFS, C.POLICY_LITTLEWOOD)):
    fig = V.timeline_figure(shown.seq, shown.accepted, policies)
    st.plotly_chart(fig, width="stretch", key=key)
    st.caption("Gefülltes Quadrat = angenommen, hohles Quadrat = abgelehnt. Blau = Premium, Gelb = Spot.")


def render_policy_panel(prefix, policy, shown):
    """Beschreibung, Ertrags-Kennzahl und Zeitleiste einer Politik (je Tab im Vergleich-Expander)."""
    st.markdown(C.POLICY_DESCRIPTIONS[policy])
    detail = shown.detail[policy]
    c1, c2, c3 = st.columns(3)
    c1.metric("Ertrag", fmt_money(detail["revenue"]))
    c2.metric("Angenommen (Premium / Spot)", f"{detail['acc_hi']} / {detail['acc_lo']}")
    c3.metric("Abgelehnt (Premium / Spot)", f"{detail['rej_hi']} / {detail['rej_lo']}")
    render_timeline(f"{prefix}_timeline_chart", shown, policies=(policy,))


def render_exact_panel(shown, stats):
    """DP-Tab: Vergleichstabelle Littlewood gegen DP auf der gezeigten Sequenz, plus Population-Abstand."""
    st.markdown(C.POLICY_DESCRIPTIONS[C.POLICY_DP])
    dp_rev = shown.revenue[C.POLICY_DP]
    lit_rev = shown.revenue[C.POLICY_LITTLEWOOD]
    gap_shown = E.gap_pct(lit_rev, dp_rev)
    st.success(f"✅ Littlewoods geschlossene Formel liegt auf dieser Sequenz **{fmt_pct(gap_shown)}** vom "
              f"DP-Optimum entfernt, über {stats.n} Stichproben im Mittel **{fmt_pct(stats.littlewood_gap_pct)}** - "
              f"keine Rückwärts-Induktion in der Hauptansicht nötig.")
    render_policy_panel("tab_dp", C.POLICY_DP, shown)


def render_comparison_tab(shown, cap_stats, current_capacity):
    """Vergleichstabelle aller drei Politiken auf der gezeigten Sequenz, Ertragsvergleich über
    Kapazität (mit Hindsight als vierter, sekundärer Kurve - "Wert von Information")."""
    rows = []
    for policy in C.POLICY_KEYS:
        detail = shown.detail[policy]
        rows.append({
            "Politik": C.POLICY_LABELS[policy],
            "Ertrag": fmt_money(detail["revenue"]),
            "Abstand zum DP-Optimum": fmt_pct(E.gap_pct(detail["revenue"], shown.revenue[C.POLICY_DP])),
            "Angenommen (Premium)": str(detail["acc_hi"]),
            "Angenommen (Spot)": str(detail["acc_lo"]),
            "Abgelehnt (Premium)": str(detail["rej_hi"]),
        })
    rows.append({
        "Politik": "🔮 Hindsight (Referenz)", "Ertrag": fmt_money(shown.hindsight),
        "Abstand zum DP-Optimum": fmt_pct(E.gap_pct(shown.hindsight, shown.revenue[C.POLICY_DP])),
        "Angenommen (Premium)": "–", "Angenommen (Spot)": "–", "Abgelehnt (Premium)": "–",
    })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.plotly_chart(V.capacity_sweep_figure(cap_stats, current_capacity, show_hindsight=True), width="stretch",
                    key="comparison_tab_capacity_chart")
    st.caption("Hindsight ist keine online umsetzbare Politik (kennt die Zukunft) - sie zeigt nur, wie viel "
              "zusätzliches Wissen über die Zukunft noch bringen würde (\"Wert von Information\"), als "
              "Nebenrolle neben dem Klassenschutz-Effekt selbst.")
