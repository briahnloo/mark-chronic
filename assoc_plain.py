"""The plain flight-number reading of BTS's lists, which is what the working sheet records.

Each listed row is one Frontier flight number on one airport pair in one month. The sheet
counts how many months each flight number appears and how many of those are consecutive.
"""
import pandas as pd

F = pd.read_csv("bts_f9_rows.csv")


def longest_run(ms):
    ms = sorted(set(int(m) for m in ms))
    best = run = 1
    span = (ms[0], ms[0])
    s = ms[0]
    for a, b in zip(ms, ms[1:]):
        if b == a + 1:
            run += 1
        else:
            run, s = 1, b
        if run > best:
            best, span = run, (s, b)
    if best == 1:
        span = (ms[0], ms[0])
    return best, span


rows = []
for (o, d, fn), g in F.groupby(["O", "Dst", "fnum"]):
    n, span = longest_run(g.month)
    rows.append(dict(market=f"{o}-{d}", flight_number=int(fn),
                     months_listed=len(g),
                     consecutive_months=n,
                     longest_run=f"2025-{span[0]:02d}..2025-{span[1]:02d}",
                     months=",".join(f"{int(m):02d}" for m in sorted(g.month)),
                     worst_pct=round(float(g.pct.max()), 1),
                     mean_pct=round(float(g.pct.mean()), 1),
                     total_operations=int(g.ops.sum()),
                     total_late=int(g.late.sum())))
A = pd.DataFrame(rows).sort_values(
    ["consecutive_months", "months_listed", "mean_pct"], ascending=False)
print(f"[N] listed Frontier flight-months: {len(F)}")
print(f"distinct flight/market combinations: {len(A)}\n")
print(A.head(12).to_string(index=False))
print(f"\nflights on 5+ consecutive lists: {(A.consecutive_months >= 5).sum()}")
A.to_csv("assoc_plain.csv", index=False)
print("wrote assoc_plain.csv")
