"""Control: replay 14 CFR 399.81 on JetBlue over the window DOT's Dec-2024 order covers
and check we reproduce exactly the four flights the order names.

Order findings (DOT_JetBlue_Order_2024-12-21.pdf, "Facts and Conclusions" and para 2):
  Flight 2585 JFK-RDU  Jun 2022 - Oct 2022  (5 consecutive months)
  Flight 1802 FLL-JFK  Jun 2023 - Oct 2023  (5)
  Flight  384 MCO-JFK  Jun 2023 - Oct 2023  (5)
  Flight  460 FLL-BDL  Jun 2023 - Nov 2023  (6)

Both the reg (399.81(c)(3)) and the order say "city-pair market", so that is the primary
reading; the airport-pair reading is reported alongside for comparison.
"""
import sys
import pandas as pd
import scan_chronic as S

MONTHS = sys.argv[1] if len(sys.argv) > 1 else "2022-06:2023-11"
CARRIER = "B6"

EXPECTED = {
    ("JFK", "RDU"): (2585, "2022-06", "2022-10", 5),
    ("FLL", "JFK"): (1802, "2023-06", "2023-10", 5),
    ("MCO", "JFK"): (384, "2023-06", "2023-10", 5),
    ("FLL", "BDL"): (460, "2023-06", "2023-11", 6),
}

df = pd.concat([S.load_month(y, m, "bts_raw", [CARRIER]) for y, m in S.month_range(MONTHS)])
df = df.reset_index(drop=True)
df["dep_min"] = S.minutes(df.CRSDepTime)
df = S.late_flags(df)
df = S.sched_time(df)
df = S.cluster(df, "Origin", "Dest", "win", col="dep_min")
df = S.cluster(df, "OriginCityMarketID", "DestCityMarketID", "win_city", col="dep_min")
df = S.cluster(df, "Origin", "Dest", "win_sched", col="sched_min")
print(f"loaded {len(df):,} {CARRIER} rows over {MONTHS}")

# airport pairs that make up each city pair, for labelling
pairs = df.groupby(["OriginCityMarketID", "DestCityMarketID"]).apply(
    lambda g: sorted(set(zip(g.Origin, g.Dest))), include_groups=False).to_dict()


def report(label, okey, dkey, unit):
    ans, g, s = S.answer(df, okey=okey, dkey=dkey, unit=unit)
    hit = s[s.run_len >= 5]
    print("\n" + "=" * 78)
    print(f"{label}: {len(ans.get(CARRIER, []))} flight(s) over the line (run >= 5)")
    found = {}
    for ch, rows in hit.groupby("chain"):
        rows = rows.sort_values("period")
        o, d = rows.iloc[0].O, rows.iloc[0].D
        units = sorted(set(int(x) for x in rows.unit))
        u = int(rows.iloc[0].unit)
        sel = df[unit].isin(units)
        if okey == "Origin":
            sel &= (df.Origin == o) & (df.Dest == d)
            ap = [(o, d)]
        else:
            ap = pairs.get((o, d), [])
            sel &= df.OriginCityMarketID.eq(o) & df.DestCityMarketID.eq(d)
        fn = sorted(set(df[sel].Flight_Number_Reporting_Airline))
        months = [str(p) for p in rows.period]
        # dominant airport pair inside the cluster
        sub = df[sel]
        dom = sub.groupby(["Origin", "Dest"]).size().sort_values(ascending=False)
        key = tuple(dom.index[0]) if len(dom) else (o, d)
        found[key] = (fn, months, int(rows.run_len.max()))
        print(f"\n  {key[0]}-{key[1]}  modal dep {' / '.join(f'{x//60:02d}{x%60:02d}' for x in units)}  "
              f"airports in city pair: {ap if okey!='Origin' else ''}")
        print(f"    flight numbers in cluster: {fn if len(fn)<=14 else str(fn[:14])+' ...'}")
        print(f"    chronic run: {months[0]}..{months[-1]}  max consecutive = {int(rows.run_len.max())}")
        for r in rows.itertuples():
            print(f"      {r.period}  ops={int(r.ops):3d} late={int(r.late):3d} "
                  f"pct={r.pct_late:.3f} canc={int(r.canc):2d} streak={int(r.streak)}")

    print(f"\n  --- match against the order ---")
    ok = True
    for mk, (num, m0, m1, n) in EXPECTED.items():
        if mk in found:
            fn, months, run = found[mk]
            good = (months[0] == m0 and months[-1] == m1 and run == n and num in fn)
            ok &= good
            print(f"  {'MATCH ' if good else 'DIFFER'} {mk[0]}-{mk[1]} flight {num}: "
                  f"expected {m0}..{m1} ({n}) | got {months[0]}..{months[-1]} ({run}) | "
                  f"{num}{'' if num in fn else ' NOT'} in cluster")
        else:
            ok = False
            print(f"  MISSING {mk[0]}-{mk[1]} flight {num} (expected {m0}..{m1}, {n} months)")
    extra = [k for k in found if k not in EXPECTED]
    if extra:
        # Not a failure. RS-4 section 2 asks whether the replay returns everything the
        # order cites, not whether it returns nothing else; a consent order disposes of
        # what DOT chose to pursue and is not an audit of the whole schedule.
        print(f"  Also returned, not charged in the order: {extra}")
    print(f"\n  CONTROL {'RETURNS ALL FOUR CITED FLIGHTS' if ok else 'DOES NOT MATCH'}")
    return ok


report("A: AIRPORT-PAIR, window per DEPARTURE", "Origin", "Dest", "win")
report("B: AIRPORT-PAIR, window per SERVICE", "Origin", "Dest", "win_sched")
report("C: CITY-PAIR, window per departure", "OriginCityMarketID", "DestCityMarketID", "win_city")
