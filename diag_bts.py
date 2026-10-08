"""Why doesn't my per-flight-number replay reproduce BTS's Frontier rows?"""
import pandas as pd
import scan_chronic as S

F = pd.read_csv("bts_f9_rows.csv")
df = pd.read_parquet("cache_2025.parquet")
f9 = df[df.Reporting_Airline == "F9"].reset_index(drop=True)

dup = F[F.duplicated(["month", "O", "Dst", "fnum"], keep=False)].sort_values(
    ["month", "O", "Dst", "fnum"])
print(f"duplicate (month, market, flight number) keys: {len(dup)} rows")
print(dup[["month", "O", "Dst", "fnum", "dep", "ops", "late", "pct"]].to_string(index=False))

g = f9.groupby(["Month", "Origin", "Dest", "Flight_Number_Reporting_Airline"]).agg(
    ops=("late_rule", "size"), late=("late_rule", "sum"),
    canc=("Cancelled", "sum"), div=("Diverted", "sum")).reset_index()
g["pct"] = g.late / g.ops * 100
g = g.rename(columns={"Month": "month", "Origin": "O", "Dest": "Dst",
                      "Flight_Number_Reporting_Airline": "fnum"})

m = F.merge(g, on=["month", "O", "Dst", "fnum"], how="left", suffixes=("_bts", "_me"))
print(f"\nBTS rows matched to my groups: {m.ops_me.notna().sum()} of {len(m)}")
agree = (m.ops_bts == m.ops_me)
print(f"operations agree on {agree.sum()} of {m.ops_me.notna().sum()} matched rows")
print(f"late counts agree on {(m.late_bts == m.late_me).sum()}")

print("\n--- BTS rows where my operations count differs (first 15) ---")
d = m[m.ops_me.notna() & ~agree]
print(d[["month", "O", "Dst", "fnum", "dep", "ops_bts", "ops_me", "late_bts", "late_me",
         "canc", "div"]].head(15).to_string(index=False))
print(f"\noperations: BTS higher on {(d.ops_bts > d.ops_me).sum()}, "
      f"lower on {(d.ops_bts < d.ops_me).sum()}")

# does BTS's count equal my count minus cancellations? minus diversions?
for label, col in [("ops - cancellations", m.ops_me - m.canc),
                   ("ops - diversions", m.ops_me - m.div),
                   ("ops - cancellations - diversions", m.ops_me - m.canc - m.div)]:
    print(f"BTS operations == {label}: {(m.ops_bts == col).sum()} of {len(m)}")
for label, col in [("late - cancellations", m.late_me - m.canc),
                   ("late - diversions", m.late_me - m.div)]:
    print(f"BTS late       == {label}: {(m.late_bts == col).sum()} of {len(m)}")

print("\n--- my >50% rows BTS does NOT list (first 15) ---")
mine = g[(g.ops >= 10) & (g.pct > 50)]
key = set(zip(F.month, F.O, F.Dst, F.fnum))
ex = mine[~mine.apply(lambda r: (r.month, r.O, r.Dst, r.fnum) in key, axis=1)]
print(ex[["month", "O", "Dst", "fnum", "ops", "late", "pct", "canc", "div"]]
      .head(15).to_string(index=False))
print(f"\n{len(ex)} rows I flag that BTS does not; "
      f"of those, {(ex.canc > 0).sum()} have cancellations and {(ex.div > 0).sum()} diversions")
print(f"their percent-late range: {ex.pct.min():.2f}..{ex.pct.max():.2f}")
print(f"their operations range: {ex.ops.min()}..{ex.ops.max()}")
