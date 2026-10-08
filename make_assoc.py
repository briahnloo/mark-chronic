"""associate_working_sheet.xlsx — a scenario document.

A working spreadsheet an associate kept while going through BTS's twelve published 2025
monthly chronic-delay lists. Tab 1 is the listings as published; tab 2 rolls them up per
flight number and market. It records counts only and draws no conclusion.

Everything is derived by this script from the published lists. No figure is invented.
"""
import datetime as dt
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FIRM = "Brannock Aviation Advisory"
AUTHOR = "J. Reyes"

F = pd.read_csv("bts_f9_rows.csv")
N = len(F)


def longest_run(ms):
    ms = sorted(set(int(m) for m in ms))
    best, run, s, span = 1, 1, ms[0], (ms[0], ms[0])
    for a, b in zip(ms, ms[1:]):
        run, s = (run + 1, s) if b == a + 1 else (1, b)
        if run > best:
            best, span = run, (s, b)
    return best, span


rows = []
for (o, d, fn), g in F.groupby(["O", "Dst", "fnum"]):
    n, span = longest_run(g.month)
    rows.append(dict(
        origin=o, dest=d, flight_number=int(fn),
        months_on_lists=len(g),
        months=" ".join(f"2025-{int(m):02d}" for m in sorted(g.month)),
        longest_consecutive=n,
        consecutive_from=f"2025-{span[0]:02d}",
        consecutive_to=f"2025-{span[1]:02d}",
        operations=int(g.ops.sum()), late_arrivals=int(g.late.sum()),
        highest_listed_pct=round(float(g.pct.max()), 1),
        mean_listed_pct=round(float(g.pct.mean()), 1)))
A = pd.DataFrame(rows).sort_values(
    ["months_on_lists", "mean_listed_pct"], ascending=False).reset_index(drop=True)

wb = Workbook()

HDR = Font(bold=True, color="FFFFFF", size=9.5)
FILL = PatternFill("solid", fgColor="1F3864")
BOLD = Font(bold=True, size=10)
NOTE = Font(italic=True, size=8.5, color="595959")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

# ---------------------------------------------------------------- tab 1: source
ws1 = wb.active
ws1.title = "List extract"
ws1["A1"] = "BTS chronically delayed flights, monthly lists, 2025 - Frontier rows only"
ws1["A1"].font = Font(bold=True, size=11)
ws1["A2"] = ("Transcribed from the twelve published workbooks in this folder. "
             "Columns as published. Frontier rows only; all carriers appear in the source.")
ws1["A2"].font = NOTE
ws1["A3"] = f"Extracted {dt.date(2026, 10, 7):%d %b %Y} by {AUTHOR}"
ws1["A3"].font = NOTE

keep = ["month", "operating", "fnum", "O", "Dst", "dep", "ops", "late", "pct", "avgmin",
        "source_file"]
heads = ["month", "operating carrier", "flight number", "origin", "destination",
         "scheduled departure", "operations", "late arrivals", "percent late",
         "average minutes late", "source workbook"]
R = F[keep].sort_values(["month", "O", "Dst", "fnum"])
for j, c in enumerate(heads, 1):
    cell = ws1.cell(row=5, column=j, value=c)
    cell.font = HDR
    cell.fill = FILL
    cell.border = BOX
    cell.alignment = Alignment(horizontal="center", wrap_text=True)
for i, r in enumerate(R.itertuples(index=False), 6):
    for j, v in enumerate(r, 1):
        cell = ws1.cell(row=i, column=j, value=(f"2025-{int(v):02d}" if j == 1 else v))
        cell.font = Font(size=9)
        cell.border = BOX
for j, w in enumerate([9, 17, 13, 8, 12, 18, 11, 12, 12, 19, 44], 1):
    ws1.column_dimensions[get_column_letter(j)].width = w
ws1.freeze_panes = "A6"

# ---------------------------------------------------------------- tab 2: roll-up
ws2 = wb.create_sheet("By flight")
ws2["A1"] = "Frontier flights by number of monthly lists they appear on, 2025"
ws2["A1"].font = Font(bold=True, size=11)
ws2["A2"] = ("Rolled up from the List extract tab. Sorted by months on lists, then by "
             "mean listed percent. Counts only.")
ws2["A2"].font = NOTE

ws2["A4"] = "Rows on the 2025 lists"
ws2["A4"].font = BOLD
ws2["D4"] = N
ws2["D4"].font = Font(bold=True, size=12)
ws2["D4"].border = BOX
ws2["D4"].alignment = Alignment(horizontal="center")
ws2["A5"] = "Distinct flight numbers and markets"
ws2["A5"].font = BOLD
ws2["D5"] = len(A)
ws2["D5"].font = Font(size=11)
ws2["D5"].border = BOX
ws2["D5"].alignment = Alignment(horizontal="center")

cols = list(A.columns)
for j, c in enumerate(cols, 1):
    cell = ws2.cell(row=7, column=j, value=c.replace("_", " "))
    cell.font = HDR
    cell.fill = FILL
    cell.border = BOX
    cell.alignment = Alignment(horizontal="center", wrap_text=True)
for i, r in enumerate(A.itertuples(index=False), 8):
    for j, v in enumerate(r, 1):
        cell = ws2.cell(row=i, column=j, value=v)
        cell.font = Font(size=9)
        cell.border = BOX
for j, w in enumerate([8, 8, 13, 15, 40, 17, 15, 14, 11, 13, 16, 15], 1):
    ws2.column_dimensions[get_column_letter(j)].width = w
ws2.freeze_panes = "A8"

wb.properties.creator = f"{AUTHOR}, {FIRM}"
wb.properties.lastModifiedBy = f"{AUTHOR}, {FIRM}"
wb.properties.title = "Chronic delay list extract 2025"
# openpyxl core properties have no company field; creator and lastModifiedBy carry it
wb.properties.created = dt.datetime(2026, 10, 7, 9, 14)
wb.properties.modified = dt.datetime(2026, 10, 7, 16, 2)
OUT = "package/associate_working_sheet.xlsx"
wb.save(OUT)

# openpyxl stamps itself into docProps/app.xml as the generating Application. Rewrite
# that part so the workbook carries the firm's own details instead of a library name.
import shutil
import tempfile
import zipfile

APP = ("<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n"
       '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/'
       'extended-properties" xmlns:vt="http://schemas.openxmlformats.org/'
       'officeDocument/2006/docPropsVTypes">'
       "<Application>Microsoft Excel</Application>"
       "<DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop>"
       f"<Company>{FIRM}</Company>"
       "<LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc>"
       "<HyperlinksChanged>false</HyperlinksChanged>"
       "<AppVersion>16.0300</AppVersion></Properties>")

tmp = tempfile.mktemp(suffix=".xlsx")
with zipfile.ZipFile(OUT) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
    for it in src.infolist():
        data = src.read(it.filename)
        if it.filename == "docProps/app.xml":
            data = APP.encode()
        dst.writestr(it, data)
shutil.move(tmp, OUT)

with zipfile.ZipFile(OUT) as z:
    leaks = [n for n in z.namelist()
             if b"openpyxl" in z.read(n).lower() or b"python" in z.read(n).lower()]
assert not leaks, f"tool name still present in {leaks}"

top = A.iloc[0]
print("wrote package/associate_working_sheet.xlsx")
print(f"[N] = {N}; tab2 row 1 = {top.origin}-{top.dest} flight {top.flight_number}, "
      f"{top.months_on_lists} lists ({top.months}), longest consecutive "
      f"{top.longest_consecutive}")
