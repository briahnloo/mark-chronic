"""With the unit fixed at (flight number, scheduled departure time), where do BTS's
operation and late counts come from?"""
import pandas as pd

F = pd.read_csv("bts_f9_rows.csv")
df = pd.read_parquet("cache_2025.parquet")
f9 = df[df.Reporting_Airline == "F9"]

keys = ["Month", "Origin", "Dest", "Flight_Number_Reporting_Airline", "CRSDepTime"]
g = f9.groupby(keys).agg(
    ops=("late_rule", "size"), late=("late_rule", "sum"),
    l15=("late_15", "sum"), lnc=("late_30_nocancel", "sum"),
    ldiv=("late_divall", "sum"),
    canc=("Cancelled", "sum"), dvt=("Diverted", "sum")).reset_index()
g.columns = ["month", "O", "Dst", "fnum", "dep"] + list(g.columns[5:])

m = F.merge(g, on=["month", "O", "Dst", "fnum", "dep"], how="left",
            suffixes=("_bts", "_me"))
print(f"BTS rows matched on the exact time key: {m.ops_me.notna().sum()} of {len(m)}")
print(f"  operations agree: {(m.ops_bts == m.ops_me).sum()}")
for c, lbl in [("late_me", "cancels late"), ("l15", "ArrDel15"),
               ("lnc", "cancels on time"), ("ldiv", "all diversions late")]:
    print(f"  late agrees under {lbl:22s}: {(m.late_bts == m[c]).sum()}")

print("\n--- unmatched BTS rows (my data has no such flight at that exact time) ---")
u = m[m.ops_me.isna()]
print(f"{len(u)} rows; sample:")
print(u[["month", "O", "Dst", "fnum", "dep", "ops_bts", "late_bts"]].head(10)
      .to_string(index=False))
if len(u):
    r = u.iloc[0]
    act = f9[(f9.Month == r.month) & (f9.Origin == r.O) & (f9.Dest == r.Dst)
             & (f9.Flight_Number_Reporting_Airline == r.fnum)]
    print(f"\nwhat my data holds for {r.O}-{r.Dst} flight {int(r.fnum)} month {int(r.month)}:")
    print(act.groupby("CRSDepTime").agg(n=("late_rule", "size"),
                                        late=("late_rule", "sum")).to_string())
    print(f"BTS says dep={r.dep}, ops={r.ops_bts}, late={r.late_bts}")

print("\n--- matched rows where operations differ (sample) ---")
d = m[m.ops_me.notna() & (m.ops_bts != m.ops_me)]
print(f"{len(d)} rows")
print(d[["month", "O", "Dst", "fnum", "dep", "ops_bts", "ops_me", "late_bts", "late_me",
         "canc", "dvt"]].head(12).to_string(index=False))

# Does BTS aggregate a +/-30 minute band around the listed time?
print("\n--- testing a +/-30 minute band around BTS's listed departure time ---")


def band(r, lo, hi):
    a = f9[(f9.Month == r.month) & (f9.Origin == r.O) & (f9.Dest == r.Dst)
           & (f9.Flight_Number_Reporting_Airline == r.fnum)
           & (f9.dep_min >= lo) & (f9.dep_min <= hi)]
    return len(a), int(a.late_rule.sum())


sub = m.head(400)
hits = 0
for _, r in sub.iterrows():
    dm = int(r.dep) // 100 * 60 + int(r.dep) % 100
    o, l = band(r, dm - 30, dm + 30)
    hits += (o == r.ops_bts and l == r.late_bts)
print(f"exact ops+late match within a +/-30 min band: {hits} of {len(sub)}")
