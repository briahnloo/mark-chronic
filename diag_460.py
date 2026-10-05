"""Why is FLL-BDL (flight 460) not chronic in 2023-11, when DOT says it was?"""
import pandas as pd
import scan_chronic as S

df = pd.concat([S.load_month(y, m, "bts_raw", ["B6"]) for y, m in S.month_range("2023-10:2023-11")])
df = df.reset_index(drop=True)
df["dep_min"] = S.minutes(df.CRSDepTime)
df = S.late_flags(df)
df = S.cluster(df, "Origin", "Dest", "win")

f = df[(df.Origin == "FLL") & (df.Dest == "BDL")].copy()
print("FLL-BDL rows by month and cluster:")
print(f.groupby(["Year", "Month", "win"]).agg(
    n=("win", "size"),
    flights=("Flight_Number_Reporting_Airline", lambda s: sorted(set(s))),
    late_rule=("late_rule", "sum"),
    canc=("Cancelled", "sum"),
    div=("Diverted", "sum"),
).to_string())

print("\n--- all FLL-BDL departures in 2023-11, flight 460 only ---")
n = f[(f.Month == 11) & (f.Flight_Number_Reporting_Airline == 460)]
print(f"rows={len(n)}  distinct CRSDepTime={sorted(set(n.CRSDepTime))}")
print(f"late_rule={int(n.late_rule.sum())}  pct={n.late_rule.mean():.4f}")
print(f"cancelled={int((n.Cancelled==1).sum())}  diverted={int((n.Diverted==1).sum())}")
print(f"ArrDelay>30 count={int(n.ArrDelay.gt(30).sum())}")
print(f"ArrDel15==1 count={int(n.ArrDel15.eq(1).sum())}")

print("\nalternative late definitions for 2023-11 flight 460:")
for col in ["late_rule", "late_divall", "late_15", "late_30_nocancel"]:
    print(f"  {col:18s} late={int(n[col].sum()):3d}/{len(n)}  pct={n[col].mean():.4f}  "
          f"chronic={'YES' if n[col].mean() > 0.5 and len(n) >= 10 else 'no'}")

print("\n--- the whole 2023-11 cluster that contains 460 ---")
w = n.win.iloc[0] if len(n) else None
cl = f[(f.Month == 11) & (f.win == w)]
print(f"cluster modal={w} ({w//60:02d}{w%60:02d})  rows={len(cl)}  "
      f"flights={sorted(set(cl.Flight_Number_Reporting_Airline))}")
print(f"late_rule={int(cl.late_rule.sum())}  pct={cl.late_rule.mean():.4f}")
print(f"\n2023-10 ops for 460-cluster + 2023-11 ops = DOT's 57?")
w10 = f[(f.Month == 10) & (f.Flight_Number_Reporting_Airline == 460)].win.iloc[0]
c10 = f[(f.Month == 10) & (f.win == w10)]
print(f"  2023-10 cluster rows={len(c10)}  2023-11 cluster rows={len(cl)}  sum={len(c10)+len(cl)}")

print("\n--- per-flight detail, 2023-11 FLL-BDL ---")
cols = ["FlightDate", "Flight_Number_Reporting_Airline", "CRSDepTime", "ArrDelay",
        "ArrDel15", "Cancelled", "Diverted", "DivReachedDest", "DivArrDelay", "late_rule"]
print(cl.sort_values("FlightDate")[cols].to_string(index=False))
