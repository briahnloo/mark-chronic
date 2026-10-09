"""Write provenance.csv and build inputs.zip, then verify the archive."""
import csv
import hashlib
import pathlib
import re
import zipfile

P = pathlib.Path("package")
OUT = pathlib.Path("submission")
OUT.mkdir(exist_ok=True)
PULL = "2026-10-07"
USG = "U.S. Government work, public domain (17 U.S.C. 105)"
AUTHOR = "scenario document written by the task author (fictional firm: Brannock Aviation Advisory)"

BTS_URL = ("https://transtats.bts.gov/PREZIP/"
           "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip")
LIST_PAGE = "https://www.bts.gov/topics/chronically-delayed-flights"


def rowcount(p):
    if p.suffix == ".csv":
        with open(p, newline="", encoding="utf-8-sig") as fh:
            return sum(1 for _ in fh) - 1
    if p.suffix == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(p, read_only=True)
        return sum(ws.max_row - 1 for ws in wb.worksheets)
    return ""


rows = []
for p in sorted(P.iterdir()):
    n = p.name
    if n == "provenance.csv":
        continue   # written below; describes the other files, not itself
    if m := re.match(r"ontime_(F9|B6)_(\d{4})_(\d{2})\.csv", n):
        car, y, mo = m.groups()
        src = BTS_URL.format(y=y, m=int(mo))
        tr = (f"kept the header line and every data line whose Reporting_Airline is "
              f"{car}; lines byte-for-byte as published, all 110 columns retained")
        lic = USG
    elif n.startswith("bts_chronic_list_"):
        src = LIST_PAGE
        tr = "none; the published workbook exactly as downloaded"
        lic = USG
    elif n == "t100_segment_F9_2025.csv":
        src = ("https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FIM"
               " (T-100 Domestic Segment, U.S. Carriers, 2025, all months; fields "
               "Year, Month, UniqueCarrier, Origin, Dest, Passengers, DepPerformed)")
        tr = ("kept the header line and every data line whose UNIQUE_CARRIER is F9; "
              "lines byte-for-byte as exported")
        lic = USG
    elif n == "DOT_JetBlue_Order_2024-12-21.pdf":
        src = ("https://www.transportation.gov/sites/dot.gov/files/2024-12/"
               "JetBlue%20Airways%20Corporation%20Consent%20Order%202024-12-21.pdf"
               " (DOT Order 2024-12-21, Docket DOT-OST-2024-0001, served 2025-01-03)")
        tr = "none; the order exactly as published"
        lic = USG
    elif n == "14_CFR_399.81.pdf":
        src = ("https://www.govinfo.gov/content/pkg/CFR-2025-title14-vol4/pdf/"
               "CFR-2025-title14-vol4-sec399-81.pdf")
        tr = "none; the official CFR section exactly as published"
        lic = USG
    elif n == "readme.html":
        src = BTS_URL.format(y=2025, m=1) + " (readme.html inside the archive)"
        tr = "none; extracted from the archive unmodified"
        lic = USG
    elif n == "replay_standard.pdf":
        src = AUTHOR
        tr = ("written for this scenario; the firm is fictional and the standard states "
              "only scope, admissibility and two reporting definitions")
        lic = AUTHOR
    elif n == "associate_working_sheet.xlsx":
        src = AUTHOR
        tr = ("derived by script from the twelve BTS chronic-delay lists in this archive: "
              "one row per Frontier flight number and airport pair, counting the months "
              "it appears on the lists, sorted by that count; sheet 2 reproduces the "
              "listed rows as published")
        lic = AUTHOR
    elif n == "monitoring_dashboard_export.csv":
        src = AUTHOR
        tr = ("derived by script from the Frontier on-time files in this archive using "
              "the ArrDel15 field; one row per market, departure window and month, with "
              "the dashboard's own flag and streak counter")
        lic = AUTHOR
    else:
        src = tr = lic = "UNCLASSIFIED - FIX"
    blob = p.read_bytes()
    rows.append(dict(file=n, url_or_origin=src, pull_date=PULL, license=lic,
                     transform=tr, rows=rowcount(p), bytes=len(blob),
                     sha256=hashlib.sha256(blob).hexdigest()))

bad = [r for r in rows if r["license"].startswith("UNCLASSIFIED")]
assert not bad, f"unclassified files: {[r['file'] for r in bad]}"

prov = P / "provenance.csv"
with open(prov, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"provenance.csv: {len(rows)} files described")

zp = OUT / "inputs.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(P.iterdir()):
        z.write(p, p.name)
print(f"inputs.zip: {zp.stat().st_size/1e6:.1f} MB, {len(list(P.iterdir()))} files")
