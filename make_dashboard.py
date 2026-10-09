"""monitoring_dashboard_export.csv — a scenario document.

The firm's own delay-monitoring dashboard, which was built for schedule reliability work
and keys off the ArrDel15 field in the BTS on-time data. It names that field in its own
column headings. Its problem-flight list is whatever its own threshold produces; it was
never built to replay 399.81 and does not claim to.

Derived entirely by this script from the on-time files in the package.
"""
import pandas as pd
import scan_chronic as S

df = pd.read_parquet("cache_2025.parquet")
f9 = df[df.Reporting_Airline == "F9"].reset_index(drop=True)

# Unit: market and departure window, as the dashboard groups them.
ans, g, s = S.answer(f9, late="late_15")
g = g.sort_values(["O", "D", "unit", "period"])

rows = []
for r in g.itertuples():
    rows.append(dict(
        report_month=str(r.period),
        carrier="F9",
        market=f"{r.O}-{r.D}",
        departure_window=f"{int(r.unit)//60:02d}{int(r.unit)%60:02d}",
        flight_numbers=" ".join(str(x) for x in sorted(r.fnums)),
        operations=int(r.ops),
        arrdel15_count=int(r.late),
        arrdel15_rate_pct=round(r.pct_late * 100, 1),
        cancellations=int(r.canc),
        flag_over_threshold=1 if r.chronic else 0,
    ))
D = pd.DataFrame(rows)
D = D[D.operations >= 10].reset_index(drop=True)

# the export carries the dashboard's own consecutive-month counters
sm = s[s.Reporting_Airline == "F9"].copy()
sm["market"] = sm.O + "-" + sm.D
sm["departure_window"] = sm.unit.map(lambda u: f"{int(u)//60:02d}{int(u)%60:02d}")
sm["report_month"] = sm.period.astype(str)
key = ["report_month", "market", "departure_window"]
D = D.merge(sm[key + ["streak", "run_len"]], on=key, how="left")
D["flag_months_consecutive"] = D.streak.fillna(0).astype(int)
D["flag_months_consecutive_max"] = D.run_len.fillna(0).astype(int)
D = D.drop(columns=["streak", "run_len"])

prob = D[D.flag_over_threshold == 1]
print(f"rows: {len(D):,}  flagged months: {len(prob)}")

# the dashboard's own standing list of problem flights: markets it flags in 5+ months
run = {}
for c, lst in ans.items():
    run[c] = lst
print(f"rows with flag_months_consecutive_max >= 5: {len(ans.get('F9', []))} market(s)")
for o, d, u in ans.get("F9", []):
    print(f"  {o}-{d} window {u//60:02d}{u%60:02d}")

D.to_csv("package/monitoring_dashboard_export.csv", index=False)
print(f"\nwrote package/monitoring_dashboard_export.csv ({len(D):,} rows, "
      f"{len(D.columns)} columns)")
print("columns:", list(D.columns))
