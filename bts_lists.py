"""Gate P7: read BTS's twelve published 2025 chronic-delay lists, find the convention that
reproduces Frontier's rows exactly, fix [N], and test the BTS-list reading as a trap.

The lists are per flight number on an airport pair, with the month's operations, late
operations and percent late. That unit is NOT the 30-minute cluster 399.81(c)(3) defines,
which is what makes reading exposure straight off the lists a trap.
"""
import pathlib
import re
import numpy as np
import pandas as pd
import scan_chronic as S

D = pathlib.Path("sources/bts_chronic")
MON = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
CAR = "F9"
CARNAME = "FRONTIER"


# BTS ships three layouts across the year: a "Rank" sheet (Jan-Sep), the same with "RANK"
# and a typo'd "MARKETING CARRER" (Oct-Nov), and a 13-column "Year" sheet with carrier
# codes and shorter headings (Dec). Each is mapped onto one canonical schema; nothing is
# renamed by position, only by matching the heading text.
def pick(cols, *pats):
    for pat in pats:
        for c in cols:
            if re.search(pat, c, re.I):
                return c
    raise KeyError(f"no column matching {pats} in {cols}")


def load_lists():
    out = []
    for p in sorted(D.glob("btscd_*.xlsx")):
        raw = pd.read_excel(p, sheet_name=0, header=None)
        first = raw[0].astype(str).str.strip().str.lower()
        hdr = raw.index[first.isin(["rank", "year"])]
        assert len(hdr), f"{p.name}: no Rank/Year header row found"
        df = pd.read_excel(p, sheet_name=0, header=hdr[0])
        df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
        c = df.columns.tolist()
        o = pd.DataFrame({
            "operating": df[pick(c, r"^operating carrier name", r"^operating carrier$")],
            "marketing": df[pick(c, r"^marketing carrier name", r"^marketing carr")],
            "fnum": pd.to_numeric(df[pick(c, r"flight number")], errors="coerce"),
            "mon": df[pick(c, r"^month$")].astype(str).str.strip().str[:3],
            "ap": df[pick(c, r"^origin[ -]*dest")].astype(str).str.strip(),
            "dep": pd.to_numeric(df[pick(c, r"departure")], errors="coerce"),
            "ops": pd.to_numeric(df[pick(c, r"^number of operations", r"^total operation")],
                                 errors="coerce"),
            "late": pd.to_numeric(df[pick(c, r"^number of flight operati", r"^delay$")],
                                  errors="coerce"),
            "pct": pd.to_numeric(df[pick(c, r"^percent of flight", r"^percentage delay")],
                                 errors="coerce"),
            "avgmin": pd.to_numeric(df[pick(c, r"average number of minute", r"arrival delay")],
                                    errors="coerce"),
        })
        o = o[o.fnum.notna() & o.ops.notna()]
        o["source_file"] = p.name
        print(f"  {p.name:44s} header row {hdr[0]:2d}, {len(o):4d} rows, "
              f"{len(c)} cols, month {o.mon.iloc[0]}")
        out.append(o)
    return out


print("parsing the twelve published lists:")
L = pd.concat(load_lists(), ignore_index=True)
L["month"] = L.mon.map(MON)
L[["O", "Dst"]] = L.ap.str.replace(" ", "", regex=False).str.split("-", expand=True)
L["fnum"] = L.fnum.astype(int)

print(f"all carriers, all twelve lists: {len(L):,} rows")
print(f"  months present: {sorted(L.month.dropna().unique().tolist())}")
print(f"  operations range {L.ops.min():.0f}..{L.ops.max():.0f}; "
      f"percent range {L.pct.min():.2f}..{L.pct.max():.2f}")
print(f"  late/ops reproduces the printed percent: "
      f"{np.allclose((L.late/L.ops*100).round(2), L.pct.round(2))}")

F = L[(L.operating.astype(str).str.upper() == CARNAME)].copy()
print(f"\n{CARNAME} rows on the lists (operating carrier): {len(F)}")
mk = L[(L.marketing.astype(str).str.upper() == CARNAME)]
print(f"{CARNAME} rows as marketing carrier: {len(mk)}  (identical set: {len(F) == len(mk)})")
print("\nper month:", F.groupby("month").size().to_dict())

# ------------------------------------------------------------------ reproduce
df = pd.read_parquet("cache_2025.parquet")
f9 = df[df.Reporting_Airline == CAR].reset_index(drop=True)

CONV = {
    "late = ArrDelay>30, cancels late (rule)": "late_rule",
    "late = ArrDel15": "late_15",
    "late = ArrDelay>30, cancels dropped": "late_30_nocancel",
}
print("\n" + "=" * 96)
print("WHICH CONVENTION REPRODUCES BTS'S FRONTIER ROWS EXACTLY")
print("=" * 96)
# BTS's own duplicate keys settle the unit: IAH-ATL flight 2400 appears twice in May, at
# 1231 and 1639, 10 operations each. So a listed row is one flight number at one scheduled
# departure time, not a flight number for the month and not the 30-minute cluster.
UNITS = {
    "flight number only": ["Month", "Origin", "Dest", "Flight_Number_Reporting_Airline"],
    "flight number + scheduled departure time":
        ["Month", "Origin", "Dest", "Flight_Number_Reporting_Airline", "CRSDepTime"],
}
best = None
for ulabel, keys in UNITS.items():
    exp = set(F.set_index(["month", "O", "Dst", "fnum"] +
                          (["dep"] if "CRSDepTime" in keys else [])).index)
    for label, col in CONV.items():
        for drop in ([False, True] if col == "late_30_nocancel" else [False]):
            d = f9[f9.Cancelled != 1] if drop else f9
            g = d.groupby(keys).agg(ops=(col, "size"), late=(col, "sum")).reset_index()
            g["pct"] = g.late / g.ops * 100
            hit = g[(g.ops >= 10) & (g.pct > 50)]
            got = set(hit.set_index(keys).index)
            name = f"{ulabel} | {label}" + (" [rows dropped]" if drop else "")
            miss, extra = exp - got, got - exp
            print(f"\n{name}")
            print(f"  rows: BTS {len(exp)}, mine {len(got)}; "
                  f"missing {len(miss)}, extra {len(extra)}")
            if miss or extra:
                if len(miss) <= 8:
                    print(f"  missing: {sorted(miss)}")
                if len(extra) <= 8:
                    print(f"  extra:   {sorted(extra)}")
                continue
            # the rows match; now check BTS's own arithmetic, not just the identities
            rk = ["month", "O", "Dst", "fnum"] + (["dep"] if "CRSDepTime" in keys else [])
            m = hit.merge(F, left_on=keys, right_on=rk, suffixes=("_me", "_bts"))
            dops = int((m.ops_me != m.ops_bts).sum())
            dlate = int((m.late_me != m.late_bts).sum())
            print(f"  operation counts differ on {dops} rows; late counts differ on {dlate}")
            if not dops and not dlate:
                print("  EXACT MATCH on rows, operations and late counts")
                best = (name, hit)

print("\n" + "=" * 96)
if best:
    name, hit = best
    N = len(hit)
    print(f"P7 PASSES — convention: {name}")
    print(f"[N] = {N} Frontier flight-months on BTS's 2025 lists")
else:
    N = len(exp)
    print("P7 FAILS — no convention reproduces BTS's Frontier rows exactly.")
    print(f"[N] = {N} (taken from BTS's own lists)")

# ------------------------------------------------------------------ trap test
print("\n" + "=" * 96)
print("THE BTS-LIST READING AS A TRAP: consecutive months per flight number")
print("=" * 96)
F = F.sort_values(["O", "Dst", "fnum", "month"])
runs = []
for (o, d, fn), g in F.groupby(["O", "Dst", "fnum"]):
    ms = sorted(g.month.astype(int))
    run = [ms[0]]
    for m in ms[1:]:
        if m == run[-1] + 1:
            run.append(m)
        else:
            runs.append((o, d, fn, run)); run = [m]
    runs.append((o, d, fn, run))
runs.sort(key=lambda r: -len(r[3]))
print(f"{'market':10s}{'flight':>8s}{'months':>8s}  span")
for o, d, fn, r in runs[:12]:
    print(f"{o}-{d:6s}{fn:>8d}{len(r):>8d}  {r[0]:02d}..{r[-1]:02d}")
five = [r for r in runs if len(r[3]) >= 5]
print(f"\nFrontier flight numbers on 5+ consecutive BTS lists: {len(five)}")
for o, d, fn, r in five:
    print(f"  {o}-{d} flight {fn}: months {r[0]:02d}..{r[-1]:02d} ({len(r)})")
print("\nlongest run:", len(runs[0][3]) if runs else 0)

F.to_csv("bts_f9_rows.csv", index=False)
L.to_csv("bts_all_rows.csv", index=False)
print(f"\nwrote bts_f9_rows.csv ({len(F)} rows) and bts_all_rows.csv ({len(L)} rows)")
