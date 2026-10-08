"""The associate's reading of BTS's lists: average the listed percentages up to the market
and departure window, then count consecutive months.

This is the natural way to read lists that are published per flight number when the rule
speaks about a flight in a market, and it is the reading the working sheet records.
"""
import numpy as np
import pandas as pd

F = pd.read_csv("bts_f9_rows.csv")
F["dm"] = (F.dep.astype(int) // 100) * 60 + F.dep.astype(int) % 100

# cluster the listed rows within each market-month on the modal listed departure time,
# the same +/-30 minutes the rule uses
rows = []
for (mo, o, d), g in F.groupby(["month", "O", "Dst"]):
    rem = g.copy()
    while len(rem):
        vals, cnts = np.unique(rem.dm, return_counts=True)
        mode = vals[cnts == cnts.max()].min()
        sel = rem[(rem.dm - mode).abs() <= 30]
        rows.append(dict(month=int(mo), market=f"{o}-{d}", window=int(mode),
                         flights=",".join(str(int(x)) for x in sorted(set(sel.fnum))),
                         listed_rows=len(sel),
                         avg_pct=round(float(sel.pct.mean()), 1),
                         pooled_pct=round(float(sel.late.sum() / sel.ops.sum() * 100), 1),
                         operations=int(sel.ops.sum()), late=int(sel.late.sum())))
        rem = rem.drop(sel.index)
A = pd.DataFrame(rows).sort_values(["market", "window", "month"])
print(f"associate's clustered rows: {len(A)}  ([N] listed flight-months: {len(F)})")


def runs(df, col):
    out = []
    for (mk, w), g in df.groupby(["market", "window"]):
        ms = sorted(g[g[col] > 50].month)
        if not ms:
            continue
        run = [ms[0]]
        for m in ms[1:]:
            if m == run[-1] + 1:
                run.append(m)
            else:
                out.append((mk, w, run)); run = [m]
        out.append((mk, w, run))
    return sorted(out, key=lambda r: -len(r[2]))


for col, lbl in [("avg_pct", "averaging the listed percentages"),
                 ("pooled_pct", "pooling the listed operations")]:
    r = runs(A, col)
    print(f"\n--- {lbl} ---")
    for mk, w, m in r[:6]:
        print(f"  {mk:9s} window {w//60:02d}{w%60:02d}  {len(m)} month(s)  "
              f"{m[0]:02d}..{m[-1]:02d}")
    five = [x for x in r if len(x[2]) >= 5]
    print(f"  markets on 5+ consecutive months: {len(five)} -> "
          f"{[(mk, f'{m[0]:02d}..{m[-1]:02d}') for mk, w, m in five]}")

top = A.sort_values("avg_pct", ascending=False).iloc[0]
print(f"\ntop row by averaged listed percentage: {top.market} window "
      f"{top.window//60:02d}{top.window%60:02d} month {top.month:02d} "
      f"flights {top.flights} avg {top.avg_pct}%")
A.to_csv("assoc_clustered.csv", index=False)
print("wrote assoc_clustered.csv")
