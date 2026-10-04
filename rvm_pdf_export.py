"""PDF-Export des Ergebnisses (fpdf2, Helvetica-Kernschrift, nur Text und Tabellen).

Die Kernschriften kennen nur Latin-1: Umlaute sind erlaubt, aber "-" (Gedankenstrich), "-" (Minuszeichen),
"EUR"-Zeichen, Emoji usw. lassen fpdf2 abstuerzen. Deshalb laeuft jeder Text durch pdf_text()."""
import time

import rvm_constants as C

_REPLACEMENTS = {
    "–": "-", "—": "-", "‑": "-", "−": "-", "≥": ">=", "≤": "<=", "→": "->", "≈": "ca.", "€": "EUR", "±": "+-",
    "·": "-", "“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "⚠️": "(!)", "⚠": "(!)", "✅": "", "ℹ️": "",
    "🐌": "", "📐": "", "🎯": "", "📊": "", "🎟️": "", "🔮": "",
}


def pdf_text(text):
    """Text fuer die Helvetica-Kernschrift: bekannte Sonderzeichen ersetzen, den Rest Latin-1-sicher machen."""
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def _fmt(v):
    return f"{v:,.0f}".replace(",", ".")


def _pct(v):
    return f"{v:+.2f} %"


def verdict_text(v):
    if v.n == 0:
        return "Kein Vergleich möglich: keine Stichprobensequenz verfügbar."
    if v.kind == "better":
        return f"Littlewood gegen FCFS: im Mittel {abs(v.diff):.2f} mehr Ertrag je Sequenz (Differenz {v.diff:+.2f}, Standardfehler {v.se:.2f}, n={v.n})."
    if v.kind == "worse":
        return f"Littlewood gegen FCFS: im Mittel {abs(v.diff):.2f} weniger Ertrag je Sequenz (Differenz {v.diff:+.2f}, Standardfehler {v.se:.2f}, n={v.n})."
    return f"Kein klarer Unterschied zwischen Littlewood und FCFS bei dieser Einstellung (Differenz {v.diff:+.2f}, Standardfehler {v.se:.2f}, n={v.n})."


def generate_rvm_pdf(capacity, n_epochs, r_hi, r_lo, demand_mix, seed, shown, stats, verdict, compress=True):
    """Ergebnis der aktuellen Einstellung als PDF: Einstellungen, Ertrag je Politik auf der gezeigten
    Sequenz, Vergleichstabelle, Population (600 Stichproben), Urteil, Hinweise zum Modell."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.set_compression(compress)
    pdf.add_page()

    def line(text, height=7, width=0):
        pdf.cell(width, height, pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def heading(text):
        pdf.set_font("Helvetica", "B", 12)
        line(text, 8)
        pdf.set_font("Helvetica", "", 10)

    def pairs(rows):
        for label, value in rows:
            pdf.cell(85, 6, pdf_text(label), border=0)
            line(value, 6)

    def table(headers, widths, rows):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        for header, width in zip(headers, widths):
            pdf.cell(width, 7, pdf_text(header), border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(7)
        pdf.set_font("Helvetica", "", 9)
        for row in rows:
            for value, width in zip(row, widths):
                pdf.cell(width, 7, pdf_text(str(value)), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.ln(7)

    def keep_together(height):
        if pdf.get_y() + height > pdf.h - pdf.b_margin:
            pdf.add_page()

    def note(text, size=8):
        pdf.set_font("Helvetica", "I", size)
        pdf.set_text_color(110, 110, 110)
        pdf.multi_cell(0, 5, pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    pdf.set_font("Helvetica", "B", 16)
    line("Buchungs-/Slot-Vergabe: Wer bekommt den letzten Container-Slot?", 10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    line(f"Erstellt: {time.strftime('%d.%m.%Y %H:%M')}  -  sebastianhanisch.net", 6)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    heading("Einstellungen")
    pairs([("Slots (Kapazität)", str(capacity)), ("Buchungsfenster (Epochen)", str(n_epochs)),
          ("Premium- / Spot-Preis", f"{_fmt(r_hi)} / {_fmt(r_lo)}"), ("Nachfragemix", demand_mix),
          ("Seed", str(seed))])
    pdf.ln(3)

    heading("Ertrag auf der gezeigten Sequenz")
    pairs([("Ertrag (Littlewood, Empfehlung)", _fmt(shown.revenue[C.POLICY_LITTLEWOOD])),
          ("Ertrag (FCFS, blind)", _fmt(shown.revenue[C.POLICY_FCFS])),
          ("Ertrag (DP, exakt)", _fmt(shown.revenue[C.POLICY_DP])),
          ("Ertrag (Hindsight, Referenz)", _fmt(shown.hindsight)),
          ("Abgewiesene Premium-Anfragen (FCFS)", str(shown.detail[C.POLICY_FCFS]["rej_hi"]))])
    pdf.ln(3)

    keep_together(50)
    heading("Vergleichstabelle (gezeigte Sequenz)")
    rows = []
    for policy in C.POLICY_KEYS:
        d = shown.detail[policy]
        gap = (d["revenue"] / shown.revenue[C.POLICY_DP] - 1) * 100 if shown.revenue[C.POLICY_DP] else 0.0
        rows.append([C.POLICY_SHORT[policy], _fmt(d["revenue"]), _pct(gap), d["acc_hi"], d["acc_lo"], d["rej_hi"]])
    table(["Politik", "Ertrag", "Abstand DP", "Angen. Premium", "Angen. Spot", "Abgel. Premium"],
         [35, 25, 25, 30, 25, 30], rows)
    pdf.ln(3)

    keep_together(60)
    heading(f"Population ({stats.n} Stichproben derselben Einstellung, nicht der gezeigte Seed)")
    pairs([("FCFS-Aufschlag gegen DP", _pct(stats.fcfs_gap_pct)),
          ("Littlewood-Aufschlag gegen DP", _pct(stats.littlewood_gap_pct)),
          ("Hindsight-Aufschlag gegen DP", _pct(stats.hindsight_gap_pct))])
    note(verdict_text(verdict), 9)
    pdf.ln(3)

    keep_together(70)
    heading("Hinweise zum Modell")
    pdf.set_font("Helvetica", "", 9)
    for text in [
        "Zwei Frachtklassen: Spot (niedriger Preis, bucht überwiegend früh) und Premium (hoher Preis, bucht überwiegend spät) bewerben sich laufend um Container-Slots. Jede Anfrage muss sofort angenommen oder abgelehnt werden (online), ohne die Zukunft zu kennen.",
        "Littlewoods Regel (1972): Spot wird nur angenommen, wenn die verbleibende Kapazität über dem Schutzniveau für erwartete künftige Premium-Nachfrage liegt - eine geschlossene Formel, keine Rückwärts-Induktion.",
        "DP (Rückwärts-Induktion über Epoche und Restkapazität) ist das echte Online-Optimum, aber nur im ERWARTUNGSWERT an jedem Entscheidungspunkt - nicht pfadweise für eine einzelne Sequenz optimal.",
        "Kein No-Show/Overbooking, nur zwei Frachtklassen, Nachfragewahrscheinlichkeiten exakt bekannt (kein Prognosefehler) - bewusste Vereinfachungen, um den Klassenschutz-Effekt sauber zu isolieren.",
    ]:
        pdf.multi_cell(0, 5, pdf_text("- " + text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())
