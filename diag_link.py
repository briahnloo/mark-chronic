"""Per-month clusters for the markets where month-linking is contentious."""
import pandas as pd
import scan_chronic as S

df = pd.concat([S.load_month(y, m, "bts_raw", ["B6"]) for y, m in S.month_range("2023-03:2023-11")])
df = df.reset_index(drop=True)
df["dep_min"] = S.minutes(df.CRSDepTime)
df = S.late_flags(df)
df = S.cluster(df, "Origin", "Dest", "win")

for O, D in [("FLL", "JFK"), ("FLL", "BOS"), ("FLL", "BDL")]:
    f = df[(df.Origin == O) & (df.Dest == D)]
    print("=" * 78)
    print(f"{O}-{D}")
    for (y, m), gm in f.groupby(["Year", "Month"]):
        for w, gc in gm.groupby("win"):
            cnt = gc.Flight_Number_Reporting_Airline.value_counts()
            dom = cnt.index[0]
            pct = gc.late_rule.mean()
            chronic = "CHRONIC" if len(gc) >= 10 and pct > 0.5 else "       "
            print(f"  {y}-{m:02d} modal {w//60:02d}{w%60:02d}  ops={len(gc):3d} "
                  f"late={int(gc.late_rule.sum()):3d} pct={pct:.3f} {chronic}  "
                  f"dominant={dom}({cnt.iloc[0]})  all={dict(cnt)}")
    print()

print("=" * 78)
print("Did flight 1802 operate FLL-JFK in Nov 2023?")
n = df[(df.Origin == "FLL") & (df.Dest == "JFK") & (df.Year == 2023) & (df.Month == 11)]
print("  flight numbers present:", dict(n.Flight_Number_Reporting_Airline.value_counts()))
print("  1802 present:", 1802 in set(n.Flight_Number_Reporting_Airline))
print("\nDid flight 170 operate FLL-BOS across Apr-Sep 2023 continuously?")
b = df[(df.Origin == "FLL") & (df.Dest == "BOS")]
print(b.groupby(["Year", "Month"]).Flight_Number_Reporting_Airline.apply(
    lambda s: dict(s.value_counts())).to_string())
