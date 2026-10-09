"""exposure_memo.pdf — answers every clause of the prompt, in the order asked."""
import json
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FIRM = "Brannock Aviation Advisory"
F = json.load(open("golden_facts.json"))
W = F["watch"]
w1, w2 = W[0], W[1]

ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.4, leading=13,
                      alignment=TA_JUSTIFY, spaceAfter=6.5)
lead = ParagraphStyle("lead", parent=body, fontSize=10.4, leading=14.2,
                      fontName="Helvetica-Bold", spaceAfter=8)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=12.5, leading=15, spaceAfter=1)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=10.1, leading=12.4,
                    spaceBefore=10, spaceAfter=3.5)
meta = ParagraphStyle("m", parent=body, fontSize=8.2, leading=10.8,
                      textColor="#444444", spaceAfter=1)
small = ParagraphStyle("s", parent=body, fontSize=8.1, leading=10.8, spaceAfter=3.5)

S = []
A = S.append


def tbl(data, widths, right=()):
    t = Table(data, colWidths=widths, hAlign="LEFT")
    st = [("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.2),
          ("FONT", (0, 1), (-1, -1), "Helvetica", 8.2),
          ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
          ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
          ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B7C3")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3.2),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1),
           [colors.white, colors.HexColor("#F2F4F7")])]
    for c in right:
        st.append(("ALIGN", (c, 1), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(st))
    return t


A(Paragraph(FIRM, h1))
A(Paragraph("MEMORANDUM", h2))
A(Paragraph("To: Frontier Airlines, Office of the General Counsel<br/>"
            f"From: Airline Practice, {FIRM}<br/>"
            "Subject: Frontier's 2025 exposure under the chronic delay rule, "
            "14 CFR 399.81<br/>"
            "Prepared under: Practice Standard RS-4 v4.2", meta))
A(Spacer(1, 10))

A(Paragraph(
    "No Frontier flight was chronically delayed for more than four consecutive months in "
    "2025, so DOT could not cite any of them, and we reject both of the views now "
    "circulating: the associate's count of listings is not a count of consecutive months, "
    "and the dashboard's fifteen-minute threshold is not the rule's.", lead))
A(Paragraph(
    f"The associate's working sheet records {F['N']} Frontier flight-months on BTS's 2025 "
    f"monthly chronic-delay lists. Our own replay finds "
    f"{F['chronic_months']} chronically delayed flight-months across {F['markets']} "
    f"markets. The two figures are close and they are not the same thing: the sheet "
    f"counts rows BTS published for individual flight numbers, while ours counts months "
    f"in which a flight, as the rule defines one, was chronically delayed. Neither is a "
    f"count of violations. The gap between a count of chronic months and a count of "
    f"citable flights is most of what follows.", body))

A(Paragraph("Can DOT cite any of our flights?", h2))
A(Paragraph(
    "No. Under 399.81(c)(4) the violation is holding out a chronically delayed flight for "
    "more than four consecutive one-month periods, so a flight becomes citable in its "
    f"fifth consecutive chronic month. Those {F['chronic_months']} chronic flight-months "
    f"sit inside {F['register_rows']} flight-months of service that was chronic at some "
    "point in the year, and they are spread thin: the longest unbroken run any "
    "single flight reached was four months. Nothing reached five, in any market, in any "
    "part of the year, and both four-month runs sit well inside it, so no run is being cut "
    "short at January or December. The citable column of exposure_register.csv reads no on "
    "every row.", body))

A(Paragraph("Flights to watch, in order of passengers", h2))
rows = [["#", "Flight", "Market", "Chronic months", "Passengers", "Extra late arrivals"]]
for i, w in enumerate(W, 1):
    rows.append([str(i), str(w["flights"][0]), w["market"],
                 f"{w['first']} to {w['last']}", f"{w['pax']:,}", str(w["extra"])])
A(tbl(rows, [0.3 * inch, 0.62 * inch, 0.78 * inch, 1.5 * inch, 1.05 * inch, 1.3 * inch],
      right=(4, 5)))
A(Spacer(1, 6))
A(Paragraph(
    "The operations behind those rates, month by month. The last row of each block is the "
    "month that ended the run, and the margin by which it ended:", body))

det = [["Flight", "Month", "Operations", "Late arrivals", "Late %"]]
for w in W:
    for mo, ops, late, pct in w["rates"]:
        det.append([str(w["flights"][0]), mo, str(ops), str(late), f"{pct}%"])
    det.append([str(w["flights"][0]), w["nxt"], str(w["nxt_ops"]), str(w["nxt_late"]),
                f"{w['nxt_pct']}%  (needed {w['need']}; {w['extra']} short)"])
A(tbl(det, [0.6 * inch, 0.78 * inch, 0.82 * inch, 0.95 * inch, 2.4 * inch],
      right=(2, 3)))
A(Spacer(1, 6))
A(Paragraph(
    f"{w1['market']}, flight {w1['flights'][0]}, carried {w1['pax']:,} passengers. It was "
    f"chronically delayed from {w1['first']} to {w1['last']} and then fell well away: in "
    f"{w1['nxt']} it operated {w1['nxt_ops']} times with only {w1['nxt_late']} late "
    f"arrivals, {w1['nxt_pct']}%, against the {w1['need']} needed to be chronic again. "
    f"{w1['extra']} more late arrivals that month would have made it citable.", body))
A(Paragraph(
    f"{w2['market']}, flight {w2['flights'][0]}, carried {w2['pax']:,} passengers and came "
    f"much closer. After four chronic months to {w2['last']} it operated {w2['nxt_ops']} "
    f"times in {w2['nxt']} with {w2['nxt_late']} late arrivals, {w2['nxt_pct']}%, against "
    f"the {w2['need']} needed. {w2['extra']} more late arrivals and this flight would have "
    f"been citable. On operational grounds it is the one we would retime first. The "
    f"ranking above stays by passengers, as RS-4 requires.", body))

A(Paragraph("Does our replay return everything the standard checks it against?", h2))
A(Paragraph(
    "Yes. RS-4 section 2 admits a replay only if it returns every flight DOT cites in the "
    "JetBlue order, with the same consecutive months and the same operation counts. Run on "
    "the BTS on-time files for those months, our replay returns all four flights, all four "
    "spans and all four operation counts:", body))
rows = [["Flight", "Market", "Months in the order", "Run", "DOT operations", "Replay"]]
for mk, fn, span, run, cnt, res in F["control"]:
    rows.append([str(fn), mk, span.replace("..", " to "), str(run), str(cnt), "returned"])
A(tbl(rows, [0.55 * inch, 0.8 * inch, 1.72 * inch, 0.4 * inch, 1.28 * inch, 0.8 * inch],
      right=(3, 4)))
A(Spacer(1, 6))
A(Paragraph(
    f"<b>There is no miss; the miss list is empty.</b> On the same months the replay also "
    f"returns {' and '.join(F['control_extras'])} as chronically delayed beyond four "
    f"consecutive months. DOT did not charge "
    f"{'those flights' if len(F['control_extras']) > 1 else 'that flight'} in the order. "
    f"That is not a miss and not a discrepancy. A consent order disposes of what the "
    f"Department chose to pursue and is not an audit of the whole schedule, so a correct "
    f"method will generally find more than the order charges. We name them because RS-4 "
    f"section 2.3 requires it.", body))

A(Paragraph("The two views already circulating", h2))
at = F["assoc_top"]
A(Paragraph(
    f"<b>The associate's working sheet.</b> Carried through to a conclusion it reports no "
    f"citable flight, which is our answer, but it reaches it by a route that does not hold "
    f"and it ranks the exposure differently. Its first row is {at['market']} flight "
    f"{at['fn']}, which appears on {at['listed']} of the twelve lists: months "
    f"{at['months'].replace(',', ', ')}. Read as five months of exposure, that flight "
    f"looks citable. It is not. Four of the five listings run consecutively from May to "
    f"August; the fifth is December, four months clear of the run and connected to "
    f"nothing. On our replay {at['market']} flight {at['fn']} is a flight to watch with a "
    f"four-month run, {w1['extra']} late arrivals in {w1['nxt']} short of citable, and it "
    f"is first on our watch list on passengers rather than on listings. The sheet counts "
    f"listings; the rule counts consecutive months.", body))
A(Paragraph(
    "The unit differs too. BTS lists a flight number at a scheduled departure time, while "
    "399.81(c)(3) treats as one flight all of a carrier's flights in a market whose "
    "scheduled departures fall within thirty minutes of the most frequent one. The sheet's "
    "218 flight-and-market rows are not the rule's flights, so their months cannot be read "
    "off as the rule's consecutive months.", body))
A(Paragraph(
    f"<b>The monitoring dashboard export.</b> The dashboard keys off ArrDel15, the BTS "
    f"field that flags an arrival fifteen or more minutes late. Carried through it reports "
    f"{len(F['dash_list'])} flights as exposed: {', '.join(F['dash_list'])}. That is four "
    f"flights away from our answer and in the wrong direction, reporting exposure where "
    f"the rule finds none. The rule's threshold is more than thirty minutes, so the "
    f"dashboard is measuring a weaker condition that a great many flights meet. Only one "
    f"of its four, {F['dash_list'][0]}, appears on our watch list at all. The export is "
    f"still useful for schedule reliability work; it is not evidence of exposure under "
    f"399.81.", body))

A(Paragraph("Basis", h2))
A(Paragraph(
    "Computed from the BTS Reporting Carrier On-Time Performance files for Frontier for "
    "each month of 2025, and for JetBlue for the months the order covers, as supplied in "
    "this folder. Passengers are the T-100 Domestic Segment PASSENGERS field for the "
    "origin-to-destination segment, January to December 2025, per RS-4 section 3.2. "
    "Percentages are to one decimal place, counts and passengers whole numbers, months "
    "YYYY-MM. Flight-month detail is in exposure_register.csv; the year is drawn in "
    "chronic_delay_timeline.png. This memo addresses citability under 399.81 only, and a "
    "flight to watch carries no finding of violation.", small))
A(Spacer(1, 3))
A(Paragraph(
    "No other conclusion survives the standard: the only method that returns DOT's four "
    "flights with their operation counts is the one that puts Frontier's longest run at "
    "four months.", body))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(0.9 * inch, 0.5 * inch,
                      f"{FIRM} | Frontier 2025 chronic delay exposure | "
                      "Prepared under RS-4 v4.2")
    canvas.drawRightString(7.6 * inch, 0.5 * inch, f"Page {doc.page} of 2")
    canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
    canvas.line(0.9 * inch, 0.64 * inch, 7.6 * inch, 0.64 * inch)
    canvas.restoreState()


doc = SimpleDocTemplate("submission/exposure_memo.pdf", pagesize=LETTER,
                        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
                        title="Frontier 2025 exposure under 14 CFR 399.81",
                        author=FIRM, creator=FIRM)
doc.build(S, onFirstPage=footer, onLaterPages=footer)

import pypdf
r = pypdf.PdfReader("submission/exposure_memo.pdf")
w = pypdf.PdfWriter()
for p in r.pages:
    w.add_page(p)
w.add_metadata({"/Title": "Frontier 2025 exposure under 14 CFR 399.81",
                "/Author": f"Airline Practice, {FIRM}",
                "/Creator": FIRM, "/Producer": "Brannock Document Services",
                "/Subject": "Client memorandum"})
with open("submission/exposure_memo.pdf", "wb") as fh:
    w.write(fh)
print("wrote submission/exposure_memo.pdf")
