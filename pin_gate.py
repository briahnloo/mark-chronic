"""Pin-sensitivity gate (Plan v2.3).

Lists every figure a grader can check ("pins"), then recomputes all of them under each
plausible model mistake, and reports which pins each mistake moves. A mistake that moves
several pins is a trap worth keeping; one that moves none is dead weight.

Pins covered here:
  P1  the answer                      F9 2025 citable flights
  P2  watch-list markets and months   the four-consecutive-month runs
  P3  passengers                      T-100 2025 on each watch-list market
  P4  extra late arrivals needed      to extend each run to five months
  P5  the JetBlue control             4 flights, their months, and 31/30/27/57
  P6  each view's list and top entry  (derived from P1/P2 per mistake)
Pin P7 ([N], F9 flight-months on BTS's published lists) is in bts_lists.py; it needs the
twelve 2025 xlsx files.
"""
import math
import pandas as pd
import scan_chronic as S

CAR = "F9"
CACHE = "cache_2025.parquet"   # written by gate_2025.py


def prepared():
    return pd.read_parquet(CACHE)

# Every mistake as a kwargs delta from the admissible method.
MISTAKES = {
    "flight-number unit": dict(unit="Flight_Number_Reporting_Airline", tol=0),
    "per-service window": dict(unit="win_sched"),
    "city-pair market": dict(okey="OriginCityMarketID", dkey="DestCityMarketID",
                             unit="win_city"),
    "averaged flight-number rates": dict(avg_fnum=True),
    "dropping cancellations": dict(late="late_30_nocancel", drop=True),
    "cancellations counted on time": dict(late="late_30_nocancel"),
    "ArrDel15": dict(late="late_15"),
    "4-month runs": dict(need=4),
    '">50%" read as "at least 50%"': dict(atleast=True),
}

# ---------------------------------------------------------------- 2025 pins


def pins_2025(df, **kw):
    """P1, P2, P3, P4 under one reading."""
    ans, g, s = S.answer(df, **kw)
    citable = sorted(ans.get(CAR, []))
    sc = s[s.Reporting_Airline == CAR]
    runs = []
    for ch, h in sc[sc.run_len == 4].groupby("chain"):
        h = h.sort_values("period")
        o, d, last = h.iloc[0].O, h.iloc[0].D, h.iloc[-1]
        nxt = last.period + 1
        cand = g[(g.Reporting_Airline == CAR) & (g.O == o) & (g.D == d)
                 & (g.period == nxt) & (g.dom == last.dom)]
        extra = None
        if len(cand):
            n0 = cand.iloc[0]
            extra = max(0, math.floor(int(n0.ops) / 2) + 1 - int(n0.late))
        runs.append((str(o), str(d), f"{h.iloc[0].period}..{last.period}", extra))
    return dict(P1=citable, P2=sorted((o, d, m) for o, d, m, _ in runs),
                P4=sorted((o, d, e) for o, d, _, e in runs))


# ---------------------------------------------------------------- control pins

CONTROL = {("JFK", "RDU"): (2585, "2022-06", "2022-10", 5, 31),
           ("FLL", "JFK"): (1802, "2023-06", "2023-10", 5, 30),
           ("MCO", "JFK"): (384, "2023-06", "2023-10", 5, 27),
           ("FLL", "BDL"): (460, "2023-06", "2023-11", 6, 57)}


def pins_control(dfb, **kw):
    """P5: how much of DOT's published finding this reading reproduces."""
    kw = {k: v for k, v in kw.items() if k != "need"}  # the order's own runs are 5 and 6
    ans, g, s = S.answer(dfb, **kw)
    hit = s[s.run_len >= 5]
    found = {}
    for ch, h in hit.groupby("chain"):
        h = h.sort_values("period")
        o, d = h.iloc[0].O, h.iloc[0].D
        if kw.get("okey", "Origin") != "Origin":   # city-pair: label by dominant airports
            sub = dfb[dfb.OriginCityMarketID.eq(o) & dfb.DestCityMarketID.eq(d)]
            dom = sub.groupby(["Origin", "Dest"]).size().sort_values(ascending=False)
            o, d = dom.index[0] if len(dom) else (o, d)
        rows = h.sort_values("period")
        # the order's footnote 6 cites operations in the month(s) past the fourth
        ops = int(rows.iloc[4:].ops.sum()) if len(rows) >= 5 else None
        found[(str(o), str(d))] = (str(rows.iloc[0].period), str(rows.iloc[-1].period),
                                   int(rows.run_len.max()), ops)
    flights = sum(1 for k, (n, m0, m1, r, _) in CONTROL.items()
                  if k in found and found[k][0] == m0 and found[k][1] == m1
                  and found[k][2] == r)
    counts = sum(1 for k, (n, m0, m1, r, c) in CONTROL.items()
                 if k in found and found[k][3] == c)
    extra = sorted(k for k in found if k not in CONTROL)
    return dict(flights=flights, counts=counts, extra=extra)


# ---------------------------------------------------------------- run

if __name__ == "__main__":
    df = prepared()
    f9 = df[df.Reporting_Airline == CAR].reset_index(drop=True)
    print(f"F9 2025 rows: {len(f9):,}")

    dfb = pd.concat([S.load_month(y, m, "bts_raw", ["B6"])
                     for y, m in S.month_range("2022-06:2023-11")]).reset_index(drop=True)
    dfb["dep_min"] = S.minutes(dfb.CRSDepTime)
    dfb = S.late_flags(dfb)
    dfb = S.sched_time(dfb)
    dfb = S.cluster(dfb, "Origin", "Dest", "win", col="dep_min")
    dfb = S.cluster(dfb, "OriginCityMarketID", "DestCityMarketID", "win_city", col="dep_min")
    dfb = S.cluster(dfb, "Origin", "Dest", "win_sched", col="sched_min")
    print(f"B6 control rows: {len(dfb):,}\n")

    base = pins_2025(f9)
    bctl = pins_control(dfb)
    print("=" * 100)
    print("ADMISSIBLE METHOD — the pins as the golden files will state them")
    print("=" * 100)
    print(f"P1 answer: {len(base['P1'])} citable flight(s) {base['P1']}")
    print(f"P2 watch list: {base['P2']}")
    print(f"P4 extra late arrivals needed: {base['P4']}")
    print(f"P5 control: {bctl['flights']}/4 flights, {bctl['counts']}/4 operation counts, "
          f"extra={bctl['extra']}")

    rows = []
    for name, kw in MISTAKES.items():
        p = pins_2025(f9, **kw)
        c = pins_control(dfb, **kw)
        rows.append(dict(
            mistake=name,
            P1=len(p["P1"]), P1m=p["P1"] != base["P1"],
            P2m=p["P2"] != base["P2"], P4m=p["P4"] != base["P4"],
            P5m=(c["flights"], c["counts"]) != (bctl["flights"], bctl["counts"]),
            ctl=f"{c['flights']}/4 {c['counts']}/4",
            top=p["P1"][0] if p["P1"] else (p["P2"][0][:2] if p["P2"] else None),
            detail=p["P1"] or p["P2"]))

    print("\n" + "=" * 100)
    print("PIN SENSITIVITY — which pins each mistake moves")
    print("=" * 100)
    print(f"{'mistake':32s}{'answer':>8s}{'P1':>5s}{'P2':>5s}{'P4':>5s}{'P5':>5s}"
          f"{'pins':>6s}  control")
    for r in rows:
        n = sum([r["P1m"], r["P2m"], r["P4m"], r["P5m"]])
        print(f"{r['mistake']:32s}{r['P1']:>8d}"
              f"{'  Y  ' if r['P1m'] else '  .  '}"
              f"{'  Y  ' if r['P2m'] else '  .  '}"
              f"{'  Y  ' if r['P4m'] else '  .  '}"
              f"{'  Y  ' if r['P5m'] else '  .  '}"
              f"{n:>6d}  {r['ctl']}")
    print("\nP1 = the answer, P2 = watch-list markets/months, P4 = extra late arrivals,")
    print("P5 = the JetBlue control's flights and operation counts.")

    print("\n" + "=" * 100)
    print("WHAT EACH MISTAKE WOULD REPORT (its list and top entry)")
    print("=" * 100)
    for r in rows:
        print(f"\n  {r['mistake']}")
        print(f"    top entry: {r['top']}")
        print(f"    list: {r['detail']}")
