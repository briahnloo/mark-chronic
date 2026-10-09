"""Part C.12: one line per packaged file, and what breaks without it."""
import csv
import hashlib
import zipfile

BREAKS = {
    "ontime_F9_2025": "the month's Frontier operations; without it that month's chronic "
                      "status, and any run crossing it, cannot be computed",
    "ontime_B6_2022": "a month of the JetBlue control window; without it the order's "
                      "run for that flight cannot be verified",
    "ontime_B6_2023": "a month of the JetBlue control window; without it the order's "
                      "run for that flight cannot be verified",
    "bts_chronic_list": "one of the twelve published lists the associate's sheet is "
                        "built from; without it [N] and that month's listings are wrong",
    "t100_segment_F9_2025.csv": "the passenger figures; without it the watch list cannot "
                                "be ordered and the fix order cannot be given",
    "DOT_JetBlue_Order": "the flights, months and operation counts the standard tests "
                         "the method against; without it admissibility cannot be shown",
    "14_CFR_399.81.pdf": "the rule itself: the 10-operation floor, the 30-minute and "
                         "50-percent thresholds, the 30-minute window and 'more than four'",
    "readme.html": "the BTS field notes; without them ArrDelay, ArrDel15, Cancelled, "
                   "Diverted and DivReachedDest cannot be read correctly",
    "replay_standard.pdf": "the engagement's own rules: the admissibility test and the "
                           "definitions of flights to watch and passengers",
    "associate_working_sheet.xlsx": "the first circulating view and the source of 337; "
                                    "the memo cannot carry it through without it",
    "monitoring_dashboard_export.csv": "the second circulating view; the memo cannot "
                                       "carry it through without it",
    "provenance.csv": "the source, date, licence and hash of every other file",
}


def why(n):
    for k, v in BREAKS.items():
        if n.startswith(k) or n == k:
            return v
    return "UNCLASSIFIED"


z = zipfile.ZipFile("submission/inputs.zip")
prov = {r["file"]: r for r in csv.DictReader(
    z.open("provenance.csv").read().decode().splitlines())}

print(f"{'file':44s}{'fmt':6s}{'size':>11s}{'rows':>9s}  sha256")
tot = 0
fmts = set()
for n in sorted(z.namelist()):
    b = z.read(n)
    tot += len(b)
    fmt = n.rsplit(".", 1)[-1]
    fmts.add(fmt)
    rows = prov.get(n, {}).get("rows", "")
    print(f"{n:44s}{fmt:6s}{len(b):>11,d}{str(rows):>9s}  "
          f"{hashlib.sha256(b).hexdigest()[:16]}")
print(f"\n{len(z.namelist())} files, {tot/1e6:.1f} MB uncompressed, formats {sorted(fmts)}")

print("\n--- what breaks without each file ---")
seen = set()
for n in sorted(z.namelist()):
    w = why(n)
    key = w[:40]
    if key in seen:
        continue
    seen.add(key)
    grp = [m for m in z.namelist() if why(m) == w]
    label = n if len(grp) == 1 else f"{n}  (and {len(grp)-1} more of its kind)"
    print(f"  {label}\n      {w}")

bad = [n for n in z.namelist() if why(n) == "UNCLASSIFIED"]
print(f"\nunclassified files: {bad or 'none'}")

# nothing that gives the answer away
LEAK = ["exposure_register", "exposure_memo", "chronic_delay_timeline", "golden",
        "scan_chronic", "gate_", "pin_", "verify_", "make_", ".py", "READY"]
leaks = [n for n in z.namelist() if any(l in n for l in LEAK)]
print(f"golden output, scripts or scan tables in the archive: {leaks or 'none'}")
