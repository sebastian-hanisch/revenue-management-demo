"""Plotly-Figuren der Buchungs-/Slot-Vergabe: Zeitleiste (Buchungssequenz, Annahme/Ablehnung je Politik),
Ertragsvergleich ueber Kapazitaet (FCFS-/Littlewood-/optional Hindsight-Aufschlag gegen DP).

Konventionen des Portfolios: Achsen `fixedrange` (Touch-Scrollen), Vorlage plotly_white, Farbcodierung
Premium/Spot konsistent (blau/gelb, wie im Plan). Plotly wird erst in den Funktionen importiert, damit
die reine Rechnung ohne Plotly testbar bleibt."""
import rvm_constants as C

LEGEND_BOTTOM = dict(orientation="h", yref="container", yanchor="bottom", y=0.0, x=0)


def _lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


# ---------------------------------------------------------------------------------------------------
# Zeitleiste: dieselbe Sequenz, mehrere Politiken uebereinander, farbcodiert nach Klasse
# ---------------------------------------------------------------------------------------------------
def timeline_figure(seq, accepted_by_policy, policies=(C.POLICY_FCFS, C.POLICY_LITTLEWOOD)):
    """seq: Liste 'hi'/'lo'/None je Epoche. accepted_by_policy: {policy: [bool/None je Epoche]}. Eine
    Zeile je Politik; gefuelltes Quadrat = angenommen, hohles Quadrat = abgelehnt, Farbe = Klasse."""
    import plotly.graph_objects as go

    fig = go.Figure()
    n = len(seq)
    xs = list(range(n))
    row_labels = [C.POLICY_LABELS.get(p, p) for p in policies]
    for row, policy in enumerate(policies):
        y = len(policies) - 1 - row
        accepted = accepted_by_policy[policy]
        for cls in (C.CLASS_HI, C.CLASS_LO):
            for accept_state in (True, False):
                idx = [i for i in xs if seq[i] == cls and accepted[i] == accept_state]
                if not idx:
                    continue
                fig.add_trace(go.Scatter(
                    x=idx, y=[y] * len(idx), mode="markers",
                    marker=dict(symbol="square" if accept_state else "square-open", size=13,
                               color=C.CLASS_COLORS[cls], line=dict(width=2, color=C.CLASS_COLORS[cls])),
                    name=f"{C.CLASS_LABELS[cls]}, {'angenommen' if accept_state else 'abgelehnt'}",
                    legendgroup=f"{cls}_{accept_state}",
                    showlegend=row == 0,
                    hovertemplate=f"Epoche %{{x}}<br>{C.CLASS_LABELS[cls]}, "
                                  f"{'angenommen' if accept_state else 'abgelehnt'}<extra></extra>",
                ))
    fig.update_layout(template="plotly_white", height=110 + 55 * len(policies), margin=dict(t=20, b=45),
                      legend=LEGEND_BOTTOM, xaxis_title="Epoche")
    fig.update_yaxes(tickmode="array", tickvals=list(range(len(policies))), ticktext=row_labels[::-1],
                     range=[-0.6, len(policies) - 0.4])
    fig.update_xaxes(range=[-0.6, n - 0.4])
    return _lock_axes(fig)


# ---------------------------------------------------------------------------------------------------
# Ertragsvergleich ueber Kapazitaet: FCFS-/Littlewood-Aufschlag gegen DP, optional Hindsight-Aufschlag
# ---------------------------------------------------------------------------------------------------
def capacity_sweep_figure(cap_stats, current_capacity, show_hindsight=False):
    """cap_stats: {capacity: PopulationStats}, aufsteigend nach Kapazitaet. Balken je Kapazitaetsstufe:
    FCFS-Aufschlag (grau), Littlewood-Aufschlag (gruen), optional Hindsight-Aufschlag (rot) gegen DP
    (0 %-Linie)."""
    import plotly.graph_objects as go

    caps = sorted(cap_stats)
    labels = [f"C={c}" + (" (eingestellt)" if c == current_capacity else "") for c in caps]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[cap_stats[c].fcfs_gap_pct for c in caps], name="FCFS",
                         marker_color=C.POLICY_COLORS[C.POLICY_FCFS],
                         hovertemplate="%{x}<br>FCFS: %{y:+.2f} %<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=[cap_stats[c].littlewood_gap_pct for c in caps], name="Littlewood",
                         marker_color=C.POLICY_COLORS[C.POLICY_LITTLEWOOD],
                         hovertemplate="%{x}<br>Littlewood: %{y:+.2f} %<extra></extra>"))
    if show_hindsight:
        fig.add_trace(go.Bar(x=labels, y=[cap_stats[c].hindsight_gap_pct for c in caps], name="Hindsight",
                             marker_color=C.HINDSIGHT_COLOR,
                             hovertemplate="%{x}<br>Hindsight: %{y:+.2f} %<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=C.POLICY_COLORS[C.POLICY_DP], width=2, dash="dot"),
                 annotation_text="DP-Optimum", annotation_position="top left", annotation_font=dict(size=11))
    fig.update_layout(template="plotly_white", height=C.CHART_HEIGHT, margin=dict(t=30, b=45), legend=LEGEND_BOTTOM,
                      barmode="group", yaxis_title="Abstand zum DP-Optimum (%)")
    return _lock_axes(fig)
