"""Unzip inputs.zip to a temp directory and check it against its own provenance.csv."""
import collections
import csv
import hashlib
import pathlib
import sys
import tempfile
import zipfile

fails = []


def check(name, got, want=True):
    ok = (got == want)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {got!r}" + ("" if ok else f" != {want!r}"))
    if not ok:
        fails.append(name)


tmp = pathlib.Path(tempfile.mkdtemp())
with zipfile.ZipFile("submission/inputs.zip") as z:
    z.extractall(tmp)
files = sorted(p for p in tmp.iterdir() if p.is_file())
print(f"extracted {len(files)} files to {tmp}\n")

check("10 or more files", len(files) >= 10)
exts = collections.Counter(p.suffix.lower() for p in files)
print("formats:", dict(exts))
check("3 or more distinct formats", len(exts) >= 3)

prov = list(csv.DictReader(open(tmp / "provenance.csv", newline="")))
named = {r["file"] for r in prov}
present = {p.name for p in files} - {"provenance.csv"}
check("provenance describes every file in the archive", named == present)
if named != present:
    print("   only in provenance:", sorted(named - present))
    print("   only in archive:   ", sorted(present - named))

bad_hash = []
for r in prov:
    p = tmp / r["file"]
    blob = p.read_bytes()
    if hashlib.sha256(blob).hexdigest() != r["sha256"] or len(blob) != int(r["bytes"]):
        bad_hash.append(r["file"])
check("every SHA-256 and byte count matches", bad_hash, [])

for col in ("url_or_origin", "pull_date", "license", "transform"):
    blanks = [r["file"] for r in prov if not r[col].strip()]
    check(f"provenance column {col!r} filled on every row", blanks, [])

scen = [r for r in prov if r["license"].startswith("scenario document")]
check("scenario documents marked as such", sorted(r["file"] for r in scen),
      ["associate_working_sheet.xlsx", "monitoring_dashboard_export.csv",
       "replay_standard.pdf"])

big = [(r["file"], int(r["rows"])) for r in prov if r["rows"] and int(r["rows"]) >= 10000]
check("at least one table with 10,000+ rows", len(big) >= 1)
print(f"   largest tables: {sorted(big, key=lambda t: -t[1])[:3]}")

# the files really are what their extension claims
import openpyxl
sig = {".pdf": b"%PDF", ".xlsx": b"PK", ".zip": b"PK"}
wrong = [p.name for p in files
         if p.suffix in sig and not p.read_bytes().startswith(sig[p.suffix])]
check("PDF and XLSX files have the right magic bytes", wrong, [])
check("readme.html is HTML",
      (tmp / "readme.html").read_bytes().lstrip()[:50].lower().startswith(b"<"), True)

# the on-time files still carry the fields the rule needs
need = ["Reporting_Airline", "Flight_Number_Reporting_Airline", "Origin", "Dest",
        "CRSDepTime", "ArrDelay", "ArrDel15", "Cancelled", "Diverted",
        "DivReachedDest", "DivArrDelay", "OriginCityMarketID", "DestCityMarketID"]
hdr = next(csv.reader(open(tmp / "ontime_F9_2025_01.csv", encoding="utf-8-sig")))
missing = [c for c in need if c not in hdr]
check("on-time files carry every field the rule and the traps need", missing, [])
check("on-time files keep all 110 columns", len(hdr), 110)

n_ontime = len([p for p in files if p.name.startswith("ontime_")])
n_lists = len([p for p in files if p.name.startswith("bts_chronic_list_")])
check("twelve Frontier months", len([p for p in files
                                     if p.name.startswith("ontime_F9_")]), 12)
check("thirteen JetBlue control months", len([p for p in files
                                              if p.name.startswith("ontime_B6_")]), 13)
check("twelve BTS lists", n_lists, 12)

print(f"\n{'ARCHIVE VERIFIED' if not fails else str(len(fails)) + ' FAILED: ' + str(fails)}")
sys.exit(1 if fails else 0)
