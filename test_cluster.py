"""Prove cluster() matches cluster_ref() on real BTS data, and time both."""
import time
import pandas as pd
import scan_chronic as S

fails = 0
for y, m, carriers in [(2025, 1, ["all"]), (2022, 6, ["B6"]), (2023, 2, ["all"])]:
    df = S.load_month(y, m, "bts_raw", carriers).reset_index(drop=True)
    df["dep_min"] = S.minutes(df.CRSDepTime)
    df = S.sched_time(df)
    for okey, dkey, out, col in [("Origin", "Dest", "win", "dep_min"),
                                 ("OriginCityMarketID", "DestCityMarketID", "win_city", "dep_min"),
                                 ("Origin", "Dest", "win_sched", "sched_min")]:
        a = df.copy()
        t0 = time.time(); S.cluster_ref(a, okey, dkey, out, col=col); t_ref = time.time() - t0
        b = df.copy()
        t0 = time.time(); S.cluster(b, okey, dkey, out, col=col); t_fast = time.time() - t0
        same = all(a[c].equals(b[c]) for c in (out, out + "_tie", out + "_wrap"))
        print(f"{y}-{m:02d} {carriers[0]:4s} {out:10s} on {col:9s} rows={len(df):7d} "
              f"ref={t_ref:6.2f}s fast={t_fast:5.2f}s speedup={t_ref/max(t_fast,1e-9):5.1f}x "
              f"identical={same}")
        if not same:
            fails += 1
            for c in (out, out + "_tie", out + "_wrap"):
                if not a[c].equals(b[c]):
                    d = a.index[a[c] != b[c]][:5]
                    print("   MISMATCH", c, "first rows:", list(d))
                    print(a.loc[d, ["Reporting_Airline", okey, dkey, "dep_min", c]].to_string())
                    print(b.loc[d, [c]].to_string())

# edge cases the real data may not contain
edge = pd.DataFrame({
    "Reporting_Airline": ["X"] * 8,
    "Origin": ["A"] * 8, "Dest": ["B"] * 8, "Year": [2025] * 8, "Month": [1] * 8,
    # two equally frequent modes 120 min apart (tie), plus a midnight-window departure
    "dep_min": [600, 600, 720, 720, 5, 5, 1415, 1415],
})
a, b = edge.copy(), edge.copy()
S.cluster_ref(a, "Origin", "Dest", "win", col="dep_min")
S.cluster(b, "Origin", "Dest", "win", col="dep_min")
ok = all(a[c].equals(b[c]) for c in ("win", "win_tie", "win_wrap"))
print(f"\nedge case (tied modes 120min apart + midnight window): identical={ok}")
print(b[["dep_min", "win", "win_tie", "win_wrap"]].to_string(index=False))
if not ok:
    fails += 1

print("\nALL IDENTICAL" if not fails else f"\n{fails} MISMATCH(ES)")
raise SystemExit(1 if fails else 0)
