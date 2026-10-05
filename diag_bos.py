"""FLL-BOS flight 170: is the 6-month run an artifact of splitting one scheduled
service across two within-month clusters?"""
import pandas as pd
import scan_chronic as S

df = pd.concat([S.load_month(y, m, "bts_raw", ["B6"]) for y, m in S.month_range("2023-04:2023-09")])
df = df.reset_index(drop=True)
df["dep_min"] = S.minutes(df.CRSDepTime)
df = S.late_flags(df)
df = S.cluster(df, "Origin", "Dest", "win")

f = df[(df.Origin == "FLL") & (df.Dest == "BOS") & (df.Flight_Number_Reporting_Airline == 170)]
print("flight 170 FLL-BOS, per month: clusters it was split into")
for (y, m), gm in f.groupby(["Year", "Month"]):
    whole_pct = gm.late_rule.mean()
    chron_whole = "CHRONIC" if len(gm) >= 10 and whole_pct > 0.5 else "       "
    print(f"\n  {y}-{m:02d} flight 170 as ONE service: ops={len(gm):3d} "
          f"late={int(gm.late_rule.sum()):3d} pct={whole_pct:.3f} {chron_whole}")
    print(f"        scheduled times: {dict(gm.CRSDepTime.value_counts())}")
    for w, gc in gm.groupby("win"):
        pct = gc.late_rule.mean()
        ch = "CHRONIC" if len(gc) >= 10 and pct > 0.5 else "       "
        print(f"        cluster {w//60:02d}{w%60:02d}: ops={len(gc):3d} "
              f"late={int(gc.late_rule.sum()):3d} pct={pct:.3f} {ch}")

print("\n" + "=" * 70)
print("Same question for the four flights DOT DID cite (must stay chronic):")
for O, D, num, months in [("JFK", "RDU", 2585, "2022-06:2022-10"),
                          ("FLL", "JFK", 1802, "2023-06:2023-10"),
                          ("MCO", "JFK", 384, "2023-06:2023-10"),
                          ("FLL", "BDL", 460, "2023-06:2023-11")]:
    d2 = pd.concat([S.load_month(y, m, "bts_raw", ["B6"]) for y, m in S.month_range(months)])
    d2 = d2.reset_index(drop=True)
    d2["dep_min"] = S.minutes(d2.CRSDepTime)
    d2 = S.late_flags(d2)
    g = d2[(d2.Origin == O) & (d2.Dest == D) & (d2.Flight_Number_Reporting_Airline == num)]
    print(f"\n  {O}-{D} flight {num} as ONE service per month:")
    for (y, m), gm in g.groupby(["Year", "Month"]):
        pct = gm.late_rule.mean()
        ch = "CHRONIC" if len(gm) >= 10 and pct > 0.5 else "NOT    "
        print(f"    {y}-{m:02d} ops={len(gm):3d} late={int(gm.late_rule.sum()):3d} "
              f"pct={pct:.3f} {ch}")
