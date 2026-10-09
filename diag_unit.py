"""Is anything in the deliverables actually unit-dependent for the two watch flights?

If clustering and not clustering give the same months, rates and operations for ATL-JFK
4818 and ATL-EWR 4602, then the unit mistake costs a solver nothing on the headline and
the task is not discriminating.
"""
import pandas as pd
import scan_chronic as S

df = pd.read_parquet("cache_2025.parquet")
f9 = df[df.Reporting_Airline == "F9"].reset_index(drop=True)

WATCH = [("ATL", "JFK", 4818), ("ATL", "EWR", 4602)]

_, g_rule, _ = S.answer(f9)
_, g_fnum, _ = S.answer(f9, unit="Flight_Number_Reporting_Airline", tol=0)

print(f"{'market':9s}{'mon':>6s} | {'clustered':^28s} | {'by flight number':^28s}")
print(f"{'':9s}{'':>6s} |   ops  late   pct  flights |   ops  late   pct  flights")
diff_rows = 0
for o, d, fn in WATCH:
    for m in range(1, 13):
        a = g_rule[(g_rule.O == o) & (g_rule.D == d) & (g_rule.Month == m)
                   & g_rule.fnums.map(lambda s: fn in s)]
        b = g_fnum[(g_fnum.O == o) & (g_fnum.D == d) & (g_fnum.Month == m)
                   & (g_fnum.unit == fn)]
        if not len(a) and not len(b):
            continue
        ar = a.iloc[0] if len(a) else None
        br = b.iloc[0] if len(b) else None
        same = (ar is not None and br is not None
                and int(ar.ops) == int(br.ops) and int(ar.late) == int(br.late))
        diff_rows += not same
        fa = (f"{int(ar.ops):5d} {int(ar.late):5d} {ar.pct_late*100:5.1f}  "
              f"{len(ar.fnums):2d}" if ar is not None else " " * 22)
        fb = (f"{int(br.ops):5d} {int(br.late):5d} {br.pct_late*100:5.1f}   1"
              if br is not None else " " * 22)
        print(f"{o}-{d:5s}{m:>6d} | {fa}      | {fb}      {'' if same else '  <-- differs'}")
print(f"\nflight-months where the two units differ on operations or late arrivals: "
      f"{diff_rows}")

# how many of the whole register's chronic rows are unit-sensitive?
ch_rule = g_rule[g_rule.chronic]
multi = ch_rule.fnums.map(len) > 1
print(f"\nchronic flight-months under the rule: {len(ch_rule)}")
print(f"  of those, clusters holding more than one flight number: {int(multi.sum())} "
      f"({multi.mean()*100:.0f}%)")
print(f"  clusters holding exactly one flight number:            {int((~multi).sum())}")
