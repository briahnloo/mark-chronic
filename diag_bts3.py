"""Close the last 53 rows: which exact form of the 30-minute band does BTS use?"""
import numpy as np
import pandas as pd

F = pd.read_csv("bts_f9_rows.csv")
df = pd.read_parquet("cache_2025.parquet")
f9 = df[df.Reporting_Airline == "F9"].copy()
f9["dm"] = f9.dep_min

F["dm"] = (F.dep.astype(int) // 100) * 60 + F.dep.astype(int) % 100

idx = {}
for k, g in f9.groupby(["Month", "Origin", "Dest", "Flight_Number_Reporting_Airline"]):
    idx[k] = g

LATE = {"cancels late": "late_rule", "all div late": "late_divall",
        "cancels on time": "late_30_nocancel", "ArrDel15": "late_15"}


def score(tol, lo_open, hi_open, latecol, same_fnum=True):
    ok = 0
    for _, r in F.iterrows():
        k = (r.month, r.O, r.Dst, r.fnum)
        g = idx.get(k)
        if g is None:
            continue
        if not same_fnum:
            g = f9[(f9.Month == r.month) & (f9.Origin == r.O) & (f9.Dest == r.Dst)]
        d = g.dm.to_numpy()
        m = ((d > r.dm - tol) if lo_open else (d >= r.dm - tol)) & \
            ((d < r.dm + tol) if hi_open else (d <= r.dm + tol))
        if m.sum() == r.ops and int(g[latecol].to_numpy()[m].sum()) == r.late:
            ok += 1
    return ok


print(f"{'tol':>5s}{'low':>7s}{'high':>7s}  late definition          matched of", len(F))
best = (0, None)
for tol in (30, 31, 29, 60, 15):
    for lo_open, hi_open in [(False, False), (True, False), (False, True), (True, True)]:
        for lbl, col in LATE.items():
            n = score(tol, lo_open, hi_open, col)
            if n > best[0]:
                best = (n, (tol, lo_open, hi_open, lbl))
            if n > 250:
                print(f"{tol:>5d}{'open' if lo_open else 'closed':>7s}"
                      f"{'open' if hi_open else 'closed':>7s}  {lbl:22s} {n:>6d}")
print("\nbest:", best)

# where does the best variant still differ?
tol, lo_open, hi_open, lbl = best[1]
col = LATE[lbl]
rows = []
for _, r in F.iterrows():
    g = idx.get((r.month, r.O, r.Dst, r.fnum))
    d = g.dm.to_numpy()
    m = ((d > r.dm - tol) if lo_open else (d >= r.dm - tol)) & \
        ((d < r.dm + tol) if hi_open else (d <= r.dm + tol))
    o, l = int(m.sum()), int(g[col].to_numpy()[m].sum())
    if (o, l) != (r.ops, r.late):
        rows.append((int(r.month), r.O, r.Dst, int(r.fnum), int(r.dep),
                     int(r.ops), o, int(r.late), l, sorted(set(g.dm.tolist()))[:8]))
print(f"\n{len(rows)} rows still differ under the best variant; first 14:")
print(f"{'mon':>4s} {'market':9s}{'flight':>7s}{'dep':>6s}{'opsB':>6s}{'opsM':>6s}"
      f"{'ltB':>5s}{'ltM':>5s}  scheduled times present")
for t in rows[:14]:
    print(f"{t[0]:>4d} {t[1]}-{t[2]:5s}{t[3]:>7d}{t[4]:>6d}{t[5]:>6d}{t[6]:>6d}"
          f"{t[7]:>5d}{t[8]:>5d}  {t[9]}")
