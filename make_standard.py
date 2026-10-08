"""replay_standard.pdf — Brannock Aviation Advisory's internal methodology standard.

Says nothing about the unit of analysis, cancellation or diversion handling, airport
versus city, or how the thresholds are read. It fixes the scope, the admissibility test
and the reporting definitions the engagement needs, and nothing else.
"""
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

FIRM = "Brannock Aviation Advisory"
DOC = "RS-4"
VER = "4.2"
EFF = "14 January 2025"

ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.3, leading=12.8,
                      alignment=TA_JUSTIFY, spaceAfter=6.5)
defn = ParagraphStyle("d", parent=body, leftIndent=15, spaceAfter=6.5)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=12.5, leading=15, spaceAfter=1)
sub = ParagraphStyle("sub", parent=ss["Heading2"], fontSize=10.2, leading=12.4,
                     spaceBefore=1, spaceAfter=6)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=9.9, leading=12,
                    spaceBefore=10, spaceAfter=3.5)
quote = ParagraphStyle("q", parent=body, leftIndent=15, rightIndent=12,
                       fontName="Times-Italic", spaceBefore=3, spaceAfter=7)

S = []
A = S.append

A(Paragraph(FIRM, h1))
A(Paragraph(f"Practice Standard {DOC} &mdash; Replaying the Chronic Delay Rule", sub))

hdr = [["Document", DOC, "Version", VER],
       ["Effective", EFF, "Supersedes", "RS-3 v3.1 (11 March 2021)"],
       ["Owner", "Methods Committee", "Next review", "January 2026, or on amendment"],
       ["Applies to", "All engagements advising a carrier on its exposure under "
        "14 CFR 399.81", "", ""]]
t = Table(hdr, colWidths=[0.78 * inch, 2.35 * inch, 0.82 * inch, 2.25 * inch],
          hAlign="LEFT")
t.setStyle(TableStyle([
    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 7.8),
    ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 7.8),
    ("FONT", (1, 0), (1, -1), "Helvetica", 7.8),
    ("FONT", (3, 0), (3, -1), "Helvetica", 7.8),
    ("SPAN", (1, 3), (3, 3)),
    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#333333")),
    ("LINEABOVE", (0, 0), (-1, 0), 0.7, colors.HexColor("#1F3864")),
    ("LINEBELOW", (0, -1), (-1, -1), 0.7, colors.HexColor("#1F3864")),
    ("TOPPADDING", (0, 0), (-1, -1), 2.2),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
    ("LEFTPADDING", (0, 0), (0, -1), 0)]))
A(t)
A(Spacer(1, 11))

A(Paragraph("1. Scope and standing", h2))
A(Paragraph(
    "This standard governs any replay of 14 CFR 399.81 the firm performs on a carrier's "
    "operating data, whether the engagement is a compliance review, a schedule-design "
    "opinion or support to counsel. It applies the rule as the Department of "
    "Transportation applies it in its enforcement orders, and it applies the rule as "
    "written. Where the regulation's text and the Department's demonstrated practice both "
    "bear on a question, the engagement answers to both, and reports any point at which it "
    "cannot do so.", body))
A(Paragraph(
    "The standard does not tell the engagement team how to compute anything. It sets out "
    "what a computation must survive before its output may be put in front of a client, "
    "and how the result is to be reported. The choice of method, and its defence, remain "
    "the engagement partner's. Departures from this standard require the written agreement "
    "of the Methods Committee and must be disclosed in the deliverable.", body))

A(Paragraph("2. Admissibility of a replay", h2))
A(Paragraph(
    "2.1 A replay may support advice given under the firm's name only if, run on the "
    "Bureau of Transportation Statistics Reporting Carrier On-Time Performance data for "
    "the relevant periods, it returns every flight cited in the Department's consent order "
    "against JetBlue Airways (Order 2024-12-21, Docket DOT-OST-2024-0001), with the same "
    "consecutive months and the same operation counts the Department states for each:", body))

rows = [["Flight", "Market", "Consecutive months", "Operations counted"],
        ["2585", "JFK-RDU", "June 2022 to October 2022 (5)", "31"],
        ["1802", "FLL-JFK", "June 2023 to October 2023 (5)", "30"],
        ["384", "MCO-JFK", "June 2023 to October 2023 (5)", "27"],
        ["460", "FLL-BDL", "June 2023 to November 2023 (6)", "57"]]
t2 = Table(rows, colWidths=[0.62 * inch, 0.85 * inch, 2.55 * inch, 1.35 * inch],
           hAlign="LEFT")
t2.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
    ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B7C3")),
    ("ALIGN", (3, 1), (3, -1), "RIGHT"),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
A(t2)
A(Spacer(1, 7))

A(Paragraph(
    "2.2 The test is conjunctive. All four flights, all four spans and all four operation "
    "counts must be returned. The order is the only published matter in which the "
    "Department has both identified chronically delayed flights and shown the arithmetic "
    "behind them, so it is the only available check on whether a replay computes what the "
    "Department computes rather than something that merely resembles it. Returning the "
    "list of flights while missing the operation counts is not a pass: the counts are what "
    "separate one reading of the rule from another, and a method can reproduce the names "
    "while counting quite different operations beneath them.", body))
A(Paragraph("A replay that misses any of them is not the replay, however close it comes.",
            quote))
A(Paragraph(
    "2.3 The test is a floor, not a ceiling. It asks whether the replay returns everything "
    "the Department found; it does not ask whether the replay returns nothing further. A "
    "consent order disposes of the matters the Department chose to pursue in that "
    "proceeding and is not an audit of the carrier's whole schedule, so a replay that "
    "satisfies 2.1 may also identify flights the order does not charge. That is an "
    "expected property of a correct method, not a defect in it, and it is not a ground on "
    "which to reject a replay. The engagement identifies any such flight in the "
    "deliverable, states that the order did not charge it, and does not describe it as a "
    "discrepancy, a miss or an error.", body))
A(Paragraph(
    "2.4 The engagement records the outcome of 2.1 in the deliverable in terms the reader "
    "can check line by line against the order, and states any item the replay does not "
    "return. Where a replay fails 2.1, the engagement does not issue advice on exposure "
    "under 399.81 and refers the method back to the Methods Committee.", body))

A(Paragraph("3. Reporting definitions", h2))
A(Paragraph(
    "The following terms carry a fixed meaning in every deliverable issued under this "
    "standard. They are reporting conventions adopted for consistency across engagements; "
    "they are not interpretations of the regulation, and the engagement team may not vary "
    "them or substitute a near equivalent.", body))
A(Paragraph(
    "<b>3.1 Flights to watch.</b> Any flight that is chronically delayed in four "
    "consecutive calendar months of the review year. A flight to watch is not a violation "
    "and is never to be reported as one, nor as exposure, nor as a probable citation. The "
    "category exists for a practical reason: four consecutive months is the last point at "
    "which the carrier can still act on its own schedule before the question passes out of "
    "its hands.", defn))
A(Paragraph(
    "<b>3.2 Passengers.</b> The PASSENGERS field of the Department's T-100 Domestic "
    "Segment data for the flight's origin-to-destination segment, summed over January to "
    "December of the review year. One direction only, as the flight is operated. No other "
    "traffic measure is substituted, no other period is used, and the figure is not "
    "pro-rated to the months in which the flight was chronically delayed.", defn))
A(Paragraph(
    "<b>3.3 Fix order.</b> Where the engagement is asked for an order of work &mdash; a "
    "fix order, a retiming sequence, a remediation list &mdash; that order is by "
    "passengers as defined in 3.2, highest first, whatever the engagement's own view of "
    "operational priority. Ties are broken by the earlier first chronic month. Where the "
    "team considers a different order operationally preferable it may say so in the body "
    "of the deliverable, but the ranking itself does not change.", defn))

A(Paragraph("4. Form of the deliverable", h2))
A(Paragraph(
    "4.1 Every deliverable states its answer before its method. Percentages are given to "
    "one decimal place, counts and passenger figures as whole numbers, and months in "
    "YYYY-MM form throughout, including in tables and chart axes.", body))
A(Paragraph(
    "4.2 Where a view already circulating inside the firm or with the client disagrees "
    "with the replay, the deliverable carries that view through to the conclusion it would "
    "support, names that conclusion, and states the distance between it and the "
    "engagement's own. A view is not answered by being left out, and the client is "
    "entitled to know why the number they have already seen is not the number we are "
    "giving them.", body))
A(Paragraph(
    "4.3 No deliverable issued under this standard characterises a flight as citable, in "
    "violation, or exposed to enforcement except on a replay that has satisfied section 2.", body))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(0.9 * inch, 0.52 * inch,
                      f"{FIRM} | Practice Standard {DOC} v{VER} | Effective {EFF}")
    canvas.drawRightString(7.6 * inch, 0.52 * inch, f"Page {doc.page} of 2")
    canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
    canvas.line(0.9 * inch, 0.66 * inch, 7.6 * inch, 0.66 * inch)
    canvas.drawString(0.9 * inch, 0.38 * inch,
                      "Internal. Not for distribution outside the engagement.")
    canvas.restoreState()


doc = SimpleDocTemplate(
    "package/replay_standard.pdf", pagesize=LETTER,
    leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    topMargin=0.8 * inch, bottomMargin=0.85 * inch,
    title=f"Practice Standard {DOC} - Replaying the Chronic Delay Rule",
    author=FIRM, subject="Methodology standard", creator=FIRM)
doc.build(S, onFirstPage=footer, onLaterPages=footer)

import pypdf
r = pypdf.PdfReader("package/replay_standard.pdf")
w = pypdf.PdfWriter()
for p in r.pages:
    w.add_page(p)
w.add_metadata({"/Title": f"Practice Standard {DOC} - Replaying the Chronic Delay Rule",
                "/Author": FIRM, "/Creator": f"{FIRM} Methods Committee",
                "/Producer": "Brannock Document Services",
                "/Subject": "Methodology standard"})
with open("package/replay_standard.pdf", "wb") as fh:
    w.write(fh)
print("wrote package/replay_standard.pdf")
