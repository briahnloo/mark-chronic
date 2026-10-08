"""Dedupe the BTS chronic-delay downloads and verify every file against the sizes read
off the index pages, and that the duplicate copies are byte-identical."""
import hashlib
import pathlib
import re

D = pathlib.Path("sources/bts_chronic")
EXPECT = {
    "01_Jan_2025_Chronic_Delay.xlsx": 65297,
    "02_Feb_2025_Chronic_Delay.xlsx": 75363,
    "03_Mar_2025_Chronic_Delay.xlsx": 66381,
    "04_Apr_2025_Chronic_Delay.xlsx": 67575,
    "05_May_2025_Chronic_Delay.xlsx": 68431,
    "06_June_2025_Chronic_Delay.xlsx": 125109,
    "07_July_2025_Chronic_Delay.xlsx": 151767,
    "08_August_2025_Chronic_Delay_0.xlsx": 42372,
    "09_September_2025_Chronic_Delay_0.xlsx": 23167,
    "Table_8_Chronic_Delay_October_2025.xlsx": 29417,
    "Table_8_Chronic_Delay_November_2025.xlsx": 31288,
    "Table_8_Chronic_Delay_December_2025_0.xlsx": 86563,
}

groups = {}
for p in D.glob("btscd_*.xlsx"):
    base = re.sub(r" \(\d+\)(?=\.xlsx$)", "", p.name)[len("btscd_"):]
    groups.setdefault(base, []).append(p)

bad = 0
for base, paths in sorted(groups.items()):
    digests = {hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    keep = D / ("btscd_" + base)
    if len(digests) != 1:
        print(f"MISMATCH {base}: {len(digests)} distinct digests across {len(paths)} copies")
        bad += 1
        continue
    if not keep.exists():
        paths[0].rename(keep)
    for p in paths:
        if p != keep:
            p.unlink()
    size = keep.stat().st_size
    ok = EXPECT.get(base) == size
    bad += not ok
    print(f"{'OK  ' if ok else 'SIZE'} {base:44s} {size:7d} "
          f"(expected {EXPECT.get(base)})  {digests.pop()[:16]}  copies={len(paths)}")

missing = set(EXPECT) - set(groups)
if missing:
    print("MISSING:", sorted(missing))
print(f"\n{len(groups)} of {len(EXPECT)} files, {bad} problem(s)")
raise SystemExit(1 if bad or missing else 0)
