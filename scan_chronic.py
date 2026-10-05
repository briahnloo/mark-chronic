"""Replay DOT's chronically-delayed-flight rule (14 CFR 399.81) on BTS on-time data.

Rule, as applied in DOT's Dec-2024 JetBlue consent order:
  * a "flight" = all of a carrier's flights in one origin-destination market whose
    scheduled departure is within 30 minutes of the most frequent scheduled departure
    time (so several flight numbers can be one flight)
  * chronically delayed in a month = operated >= 10 times that month AND arrived more
    than 30 minutes late (cancellations count as late) more than 50% of the time
  * violation = chronically delayed for MORE THAN FOUR consecutive months (5+)

The script prints three things per carrier:
  1. the violating flights under the rule
  2. TRAPS: shortcuts that change the answer (you want several of these to disagree)
  3. DETERMINISM: reasonable readings of the rule that must NOT change the answer,
     plus edge flags (streaks cut off by the window, tied modal times, near-miss).
     Only choose a carrier whose DETERMINISM line is clean.

Usage (on your own machine; needs pandas):
  python scan_chronic.py --months 2023-05:2023-11 --carriers B6     # control run
  python scan_chronic.py --months 2025-01:2025-12 --carriers all    # pick the carrier
"""
import argparse, os, sys, urllib.request, zipfile
import numpy as np
import pandas as pd

URL = "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip"
COLS = ["Year", "Month", "FlightDate", "Reporting_Airline", "Flight_Number_Reporting_Airline",
        "Origin", "Dest", "OriginCityMarketID", "DestCityMarketID", "CRSDepTime", "ArrDelay",
        "ArrDel15", "Cancelled", "Diverted", "DivReachedDest", "DivArrDelay"]


def month_range(spec):
    a, b = spec.split(":")
    return [(p.year, p.month) for p in pd.period_range(a, b, freq="M")]


def load_month(y, m, datadir, carriers):
    path = os.path.join(datadir, f"ontime_{y}_{m:02d}.zip")
    if not os.path.exists(path):
        print(f"downloading {y}-{m:02d} ...", file=sys.stderr)
        urllib.request.urlretrieve(URL.format(y=y, m=m), path)
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        df = pd.read_csv(z.open(name), usecols=COLS, low_memory=False)
    if carriers != ["all"]:
        df = df[df.Reporting_Airline.isin(carriers)]
    return df


def minutes(hhmm):
    hhmm = hhmm.astype(int)
    return (hhmm // 100) * 60 + hhmm % 100


def late_flags(df):
    canc = df.Cancelled == 1
    div = df.Diverted == 1
    div_ok = div & (df.DivReachedDest == 1) & df.DivArrDelay.le(30)
    base = df.ArrDelay.gt(30)
    df["late_rule"] = (base & ~div) | (div & ~div_ok) | canc     # diversions late unless reached dest <=30 late
    df["late_divall"] = (base & ~div) | div | canc                # every diversion late (ATCR convention)
    df["late_15"] = df.ArrDel15.fillna(0).eq(1)                   # ready-made BTS flag
    df["late_30_nocancel"] = base                                 # cancels silently on time
    return df


def sched_time(df):
    """Each flight number's scheduled departure time for the month: its modal CRSDepTime,
    ties going to the earlier time.

    399.81(c)(3) pools "all of a carrier's flights ... whose scheduled departure times are
    within 30 minutes of the most frequently occurring scheduled departure time". A flight
    number retimed mid-month is one scheduled service on a revised schedule, not two
    flights, so the window is applied to each service's scheduled time rather than to
    every individual departure. Clustering per departure instead splits one service across
    two windows and can make a fragment chronic while the service is not: FLL-BOS 170 in
    May 2023 was 27 ops / 51.9% at 2040 plus 4 ops at 2115, while the service was
    31 ops / 48.4%. It also undercounts operations against the order's own figures --
    DOT reports 31 for flight 2585 in month 5, which is the pooled cluster, not 2585's 29.
    """
    key = ["Reporting_Airline", "Origin", "Dest", "Year", "Month",
           "Flight_Number_Reporting_Airline"]
    n = df.groupby(key + ["dep_min"]).size().reset_index(name="n")
    n = n.sort_values(key + ["n", "dep_min"], ascending=[True] * len(key) + [False, True])
    modal = n.drop_duplicates(key)[key + ["dep_min"]].rename(columns={"dep_min": "sched_min"})
    out = df.merge(modal, on=key, how="left")
    out["sched_min"] = out.sched_min.fillna(out.dep_min).astype(int)
    return out


def cluster_ref(df, okey, dkey, out, col="sched_min"):
    """Reference implementation, kept so the fast path can be tested against it."""
    df[out] = -1
    df[out + "_tie"] = False
    df[out + "_wrap"] = False
    for _, idx in df.groupby(["Reporting_Airline", okey, dkey, "Year", "Month"]).groups.items():
        rest = df.loc[idx, col]
        while len(rest):
            counts = rest.value_counts()
            tops = pd.Series(counts[counts == counts.max()].index)
            mode = tops.min()
            members = rest[(rest - mode).abs() <= 30]
            df.loc[members.index, out] = mode
            df.loc[members.index, out + "_tie"] = bool((tops - mode).abs().gt(30).any())
            df.loc[members.index, out + "_wrap"] = bool(mode < 30 or mode > 1410)
            rest = rest.drop(members.index)
    return df


def cluster(df, okey, dkey, out, col="sched_min"):
    """Modal scheduled departure +/-30 min clustering per carrier/market/month.
    Also records whether a tie between modal times >30 min apart decided the clusters
    and whether the window touches midnight. Same result as cluster_ref, without the
    per-group pandas indexing (see test_cluster.py)."""
    n = len(df)
    win = np.full(n, -1, dtype=np.int64)
    tie = np.zeros(n, dtype=bool)
    wrap = np.zeros(n, dtype=bool)
    dep = df[col].to_numpy(dtype=np.int64)
    codes = pd.factorize(pd.MultiIndex.from_arrays(
        [df["Reporting_Airline"], df[okey], df[dkey], df["Year"], df["Month"]]))[0]
    order = np.argsort(codes, kind="stable")
    bounds = np.flatnonzero(np.diff(codes[order])) + 1
    for block in np.split(order, bounds):
        d = dep[block]
        rem = np.ones(len(d), dtype=bool)
        while rem.any():
            vals, cnts = np.unique(d[rem], return_counts=True)
            tops = vals[cnts == cnts.max()]
            mode = tops.min()
            members = rem & (np.abs(d - mode) <= 30)
            pos = block[members]
            win[pos] = mode
            tie[pos] = bool(np.any(np.abs(tops - mode) > 30))
            wrap[pos] = bool(mode < 30 or mode > 1410)
            rem &= ~members
    df[out] = win
    df[out + "_tie"] = tie
    df[out + "_wrap"] = wrap
    return df


def flight_months(df, okey, dkey, unit, late_col, drop_cancelled=False,
                  ops_excl_cancel=False, atleast=False, avg_fnum=False):
    d = df[df.Cancelled != 1] if drop_cancelled else df
    keys = ["Reporting_Airline", okey, dkey, "Year", "Month", unit]
    g = d.groupby(keys).agg(ops=(late_col, "size"), late=(late_col, "sum"),
                            canc=("Cancelled", "sum"),
                            fnums=("Flight_Number_Reporting_Airline",
                                   lambda s: frozenset(s.tolist())),
                            dom=("Flight_Number_Reporting_Airline",
                                 lambda s: s.value_counts().index[0])).reset_index()
    g = g.rename(columns={okey: "O", dkey: "D", unit: "unit"})
    g["pct_late"] = g.late / g.ops
    if avg_fnum:
        # The misreading that averages each flight number's own late rate inside the
        # cluster instead of pooling its operations: a 4-operation remnant then counts
        # as much as a 27-operation service.
        fn = ["Reporting_Airline", okey, dkey, "Year", "Month", unit,
              "Flight_Number_Reporting_Airline"]
        p = d.groupby(fn).agg(o=(late_col, "size"), l=(late_col, "sum")).reset_index()
        p["r"] = p.l / p.o
        m = p.groupby(fn[:-1]).r.mean().reset_index().rename(
            columns={okey: "O", dkey: "D", unit: "unit", "r": "pct_avg"})
        g = g.merge(m, on=["Reporting_Airline", "O", "D", "Year", "Month", "unit"],
                    how="left")
        g["pct_late"] = g.pct_avg.fillna(g.pct_late)
    flown = g.ops - g.canc if ops_excl_cancel else g.ops
    # 399.81(c)(1)-(2): operated at least 10 times AND arrived late MORE THAN 50% of the
    # time. atleast=True is the misreading that treats exactly 50% as qualifying.
    g["over"] = g.pct_late >= 0.5 if atleast else g.pct_late > 0.5
    g["thin"] = flown < 10
    g["chronic"] = (~g.thin) & g.over
    g["period"] = pd.PeriodIndex.from_fields(year=g.Year, month=g.Month, freq="M")
    return g


def streaks(g, tol, link="dom", skip_thin=False):
    """Run length of consecutive chronic months.

    The 30-minute window in 399.81(c)(3) groups flights *within* a month; neither the
    reg nor the order says how months link. DOT identifies each held-out flight by a
    single flight number (2585, 1802, 384, 460), and flight 460's schedule drifted
    2030 -> 2115 between Oct and Nov 2023 while staying one flight in the order. So by
    default a month continues the previous month's run when the two clusters are the same
    scheduled service: the flight number operating most of the cluster is the same
    (link="dom"). link="fnum" loosens that to any shared flight number, and link="modal"
    requires the modal times to be within `tol`; both are kept for determinism checks.

    skip_thin=True is the misreading that treats a month the flight operated fewer than
    10 times as not interrupting the run, instead of ending it: the reg conditions
    "chronically delayed" on operating at least 10 times, so a sub-10 month simply is not
    a chronically delayed month and the consecutive count restarts.

    `streak` = running count; `run_len` = full length of the run the month belongs to."""
    thin = set()
    if skip_thin:
        t = g[g.thin]
        thin = set(zip(t.Reporting_Airline, t.O, t.D, t.dom, t.period))
    g = g[g.chronic].sort_values("period").copy()
    g["streak"] = 1
    g["chain"] = -1
    seen = {}
    nxt = 0
    for i, r in g.iterrows():
        k = (r.Reporting_Airline, r.O, r.D)
        def contiguous(p):
            if p == r.period - 1:
                return True
            if not skip_thin:
                return False
            # every month strictly between must be one the flight operated < 10 times
            gap = [p + i for i in range(1, (r.period - p).n)]
            return bool(gap) and all((*k, r.dom, q) in thin for q in gap)

        prev = [(s, c) for (t, p, s, c, fn, dm) in seen.get(k, [])
                if contiguous(p) and (dm == r.dom if link == "dom"
                                      else bool(fn & r.fnums) if link == "fnum"
                                      else abs(t - r.unit) <= tol)]
        if prev:
            s, c = max(prev)
            g.at[i, "streak"], g.at[i, "chain"] = 1 + s, c
        else:
            g.at[i, "streak"], g.at[i, "chain"] = 1, nxt
            nxt += 1
        seen.setdefault(k, []).append((r.unit, r.period, g.at[i, "streak"],
                                       g.at[i, "chain"], r.fnums, r.dom))
    # One chain is one flight in DOT's sense, even where the modal departure time
    # drifts between months (order: JFK-RDU ran 2159 Jun-Aug, 2155 Sep-Oct, one flight).
    g["run_len"] = g.groupby("chain").streak.transform("max") if len(g) else g.streak
    return g


def answer(df, okey="Origin", dkey="Dest", unit="win", late="late_rule", drop=False,
           excl=False, tol=30, need=5, link="dom", atleast=False, skip_thin=False,
           avg_fnum=False):
    g = flight_months(df, okey, dkey, unit, late, drop, excl, atleast, avg_fnum)
    s = streaks(g, tol, link, skip_thin)
    hit = s[s.run_len >= need]
    ans = {}
    for c, h in hit.groupby("Reporting_Airline"):
        # one entry per chain: the market and the modal time the run started on
        firsts = h.sort_values("period").groupby("chain").first()
        ans[c] = sorted({(r.O, r.D, int(r.unit)) for r in firsts.itertuples()})
    return ans, g, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", required=True, help="e.g. 2025-01:2025-12")
    ap.add_argument("--carriers", default="all", help="comma list of Reporting_Airline codes, or all")
    ap.add_argument("--datadir", default="bts_raw")
    ap.add_argument("--out", default="scan_out")
    a = ap.parse_args()
    os.makedirs(a.datadir, exist_ok=True); os.makedirs(a.out, exist_ok=True)
    first, last = (pd.Period(x, "M") for x in a.months.split(":"))
    df = pd.concat([load_month(y, m, a.datadir, a.carriers.split(",")) for y, m in month_range(a.months)])
    df = df.reset_index(drop=True)
    df["dep_min"] = minutes(df.CRSDepTime)
    df = late_flags(df)
    df = sched_time(df)
    df = cluster(df, "Origin", "Dest", "win", col="dep_min")
    df = cluster(df, "OriginCityMarketID", "DestCityMarketID", "win_city", col="dep_min")
    df = cluster(df, "Origin", "Dest", "win_sched", col="sched_min")

    rule, g_rule, s_rule = answer(df)
    g_rule.to_csv(os.path.join(a.out, "flight_month_rule.csv"), index=False)
    s_rule.to_csv(os.path.join(a.out, "chronic_streaks_rule.csv"), index=False)

    def od(ans):  # compare on market only, ignoring the unit label
        return {c: sorted({(o, d) for o, d, _ in v}) for c, v in ans.items()}

    traps = {
        "flight-number unit": answer(df, unit="Flight_Number_Reporting_Airline", tol=0)[0],
        "ArrDel15 flag": answer(df, late="late_15")[0],
        "cancelled rows dropped": answer(df, late="late_30_nocancel", drop=True)[0],
        "cancels counted on time": answer(df, late="late_30_nocancel")[0],
        "4+ months": answer(df, need=4)[0],
        # The reg says "city-pair market", but the control shows DOT computed on airport
        # pairs: city-pair grouping reproduces 1 of the order's 4 flights and invents an
        # LGA-FLL violation. Taking the reg literally is therefore a trap, not a reading.
        "literal city-pair market": answer(df, okey="OriginCityMarketID",
                                           dkey="DestCityMarketID", unit="win_city")[0],
    }
    checks = {
        "all diversions late": answer(df, late="late_divall")[0],
        "cancels not counted as 'operated'": answer(df, excl=True)[0],
        "window applied per service, not per departure": answer(df, unit="win_sched")[0],
        "link months on modal time within 30 min": answer(df, link="modal", tol=30)[0],
        "link months on any shared flight number": answer(df, link="fnum")[0],
        "link months only on identical modal time": answer(df, link="modal", tol=0)[0],
    }

    print("\n=== per carrier ===")
    for c in sorted(set(df.Reporting_Airline)):
        r = rule.get(c, [])
        print(f"\n{c}: {len(r)} violating flight(s) under the rule (origin, dest, modal dep minutes): {r}")
        dis = [n for n, ans in traps.items() if od(ans).get(c, []) != od(rule).get(c, [])]
        print(f"  TRAPS that change the answer ({len(dis)}/{len(traps)}): {dis}")
        bad = [n for n, ans in checks.items() if ans.get(c, []) != r]
        sc = s_rule[s_rule.Reporting_Airline == c]
        left = sc[(sc.period == first) & (sc.run_len < 5)]
        right = sc[(sc.period == last) & (sc.run_len == 4)]
        if len(left):
            bad.append(f"chronic in first month with run<5 {sorted(set(zip(left.O, left.D)))}: streak may start before the window")
        if len(right):
            bad.append(f"4-month run ending in last month {sorted(set(zip(right.O, right.D)))}")
        mk = {(o, d) for o, d, _ in r}
        fl = df[(df.Reporting_Airline == c) & pd.Series(list(zip(df.Origin, df.Dest))).isin(mk).values]
        if fl.win_tie.any():
            bad.append("tied modal departure time on a flagged market")
        if fl.win_wrap.any():
            bad.append("departure window touches midnight on a flagged market")
        near = sc[sc.run_len == 4].drop_duplicates(["O", "D", "unit", "run_len"])
        print(f"  near-miss runs of exactly 4 months: {len(near)} {sorted(set(zip(near.O, near.D)))}")
        print(f"  DETERMINISM: {'clean' if not bad else bad}")
    print(f"\nDetail tables written to {a.out}/")


if __name__ == "__main__":
    main()
