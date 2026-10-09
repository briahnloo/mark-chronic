"""Score the deliverables a solver making exactly one method mistake would ship.

For each mistake the solver is assumed competent at everything else: correct file names,
correct columns, correct formatting, and an honest report of whatever its own method
produced, including its own control result. The question is how much of the mock rubric
survives the one mistake.
"""
import json
import math
import pandas as pd
import scan_chronic as S

CAR = "F9"
G = json.load(open("golden_facts.json"))
TRUE_WATCH = [("ATL-JFK", 4818), ("ATL-EWR", 4602)]
TRUE_EXTRA = {"ATL-JFK": 13, "ATL-EWR": 2}
TRUE_OPS = [31, 30, 27, 57]

MISTAKES = {
    "flight-number unit": dict(unit="Flight_Number_Reporting_Airline", tol=0),
    "per-service window": dict(unit="win_sched"),
    "city-pair market": dict(okey="OriginCityMarketID", dkey="DestCityMarketID",
                             unit="win_city"),
    "averaged flight-number rates": dict(avg_fnum=True),
    "dropping cancellations": dict(late="late_30_nocancel", drop=True),
    "cancellations counted on time": dict(late="late_30_nocancel"),
    "ArrDel15": dict(late="late_15"),
    '">=50%"': dict(atleast=True),
    "4-month runs counted": dict(need=4),
}

df = pd.read_parquet("cache_2025.parquet")
f9 = df[df.Reporting_Airline == CAR].reset_index(drop=True)
t100 = pd.read_csv("package/t100_segment_F9_2025.csv")
pax = t100.groupby(["ORIGIN", "DEST"]).PASSENGERS.sum().to_dict()

dfb = pd.concat([S.load_month(y, m, "bts_raw", ["B6"])
                 for y, m in S.month_range("2022-05:2023-11")]).reset_index(drop=True)
dfb["dep_min"] = S.minutes(dfb.CRSDepTime)
dfb = S.late_flags(dfb)
dfb = S.sched_time(dfb)
dfb = S.cluster(dfb, "Origin", "Dest", "win", col="dep_min")
dfb = S.cluster(dfb, "OriginCityMarketID", "DestCityMarketID", "win_city", col="dep_min")
dfb = S.cluster(dfb, "Origin", "Dest", "win_sched", col="sched_min")
ORDER = {("JFK", "RDU"): ("2022-06", "2022-10", 5, 31),
         ("FLL", "JFK"): ("2023-06", "2023-10", 5, 30),
         ("MCO", "JFK"): ("2023-06", "2023-10", 5, 27),
         ("FLL", "BDL"): ("2023-06", "2023-11", 6, 57)}


def outputs(**kw):
    """What this solver's three files would say."""
    ans, g, s = S.answer(f9, **kw)
    citable = sorted(ans.get(CAR, []))
    sc = s[s.Reporting_Airline == CAR]
    watch = []
    for ch, h in sc[sc.run_len == 4].groupby("chain"):
        h = h.sort_values("period")
        o, d, last = h.iloc[0].O, h.iloc[0].D, h.iloc[-1]
        cand = g[(g.O == o) & (g.D == d) & (g.period == last.period + 1)
                 & (g.dom == last.dom)]
        extra = None
        if len(cand):
            n0 = cand.iloc[0]
            extra = max(0, math.floor(int(n0.ops) / 2) + 1 - int(n0.late))
        watch.append(dict(market=f"{o}-{d}", dom=int(last.dom),
                          pax=int(pax.get((o, d), 0)), extra=extra,
                          rates=[(str(r.period), int(r.ops), int(r.late))
                                 for r in h.itertuples()],
                          close=(None if not len(cand)
                                 else (str(last.period + 1), int(cand.iloc[0].ops),
                                       int(cand.iloc[0].late)))))
    watch.sort(key=lambda w: -w["pax"])

    # the same method run on the control window
    ck = {k: v for k, v in kw.items() if k != "need"}
    _, gb, sb = S.answer(dfb, **ck)
    got = {}
    for ch, h in sb[sb.run_len >= 5].groupby("chain"):
        h = h.sort_values("period")
        o, d = h.iloc[0].O, h.iloc[0].D
        if ck.get("okey", "Origin") != "Origin":
            sub = dfb[dfb.OriginCityMarketID.eq(o) & dfb.DestCityMarketID.eq(d)]
            dom = sub.groupby(["Origin", "Dest"]).size().sort_values(ascending=False)
            o, d = dom.index[0] if len(dom) else (o, d)
        got[(o, d)] = (str(h.iloc[0].period), str(h.iloc[-1].period),
                       int(h.run_len.max()), int(h.iloc[4:].ops.sum()))
    flights = sum(1 for k, v in ORDER.items()
                  if k in got and got[k][:3] == v[:3])
    counts = sum(1 for k, v in ORDER.items() if k in got and got[k][3] == v[3])
    ch = g[g.chronic]
    return dict(citable=citable, watch=watch, cflights=flights, ccounts=counts,
                chronic_months=len(ch), markets=ch.groupby(["O", "D"]).ngroups)


base = outputs()
assert len(base["citable"]) == 0 and len(base["watch"]) == 2, "baseline drifted"

CRIT = [("A1", 14), ("A2", 9), ("A3", 4), ("A4", 4), ("A5", 4),
        ("B1", 2), ("B2", 2), ("B3", 1), ("B4", 2),
        ("C1", 1), ("C2", 1), ("C3", 4), ("C4", 4), ("C5", 4), ("C6", 5), ("C7", 3),
        ("C8", 2), ("C9", 2), ("C10", 3), ("C11", 4), ("C12", 1), ("C13", 2),
        ("C14", 5), ("C15", 1), ("C16", 2), ("C17", 5), ("C18", 2), ("C19", 2),
        ("C20", 1), ("C21", 2), ("C22", 2)]
assert sum(w for _, w in CRIT) == 100, sum(w for _, w in CRIT)
WT = dict(CRIT)


TRUE_RATES = {
    "ATL-JFK": [("2025-05", 31, 17), ("2025-06", 30, 20),
                ("2025-07", 31, 18), ("2025-08", 31, 17)],
    "ATL-EWR": [("2025-04", 30, 20), ("2025-05", 21, 17),
                ("2025-06", 30, 18), ("2025-07", 31, 25)],
}
TRUE_CLOSE = {"ATL-JFK": ("2025-09", 30, 3), "ATL-EWR": ("2025-08", 31, 14)}


def score(o, name):
    """Which criteria this solver earns. Everything not method-dependent is granted."""
    e = {}
    # A flight this solver calls citable is not a flight it offers "to watch": its memo
    # presents that flight as a violation, so the close-call asks go unanswered for it.
    cit = {f"{o_}-{d_}" for o_, d_, _ in o["citable"]}
    reported = [w for w in o["watch"] if w["market"] not in cit]
    wl = [(w["market"], w["dom"]) for w in reported]
    byk = {w["market"]: w for w in reported}
    ex = {k: v["extra"] for k, v in byk.items()}

    e["A1"] = len(o["citable"]) == 0
    e["A2"] = wl == TRUE_WATCH
    e["A3"] = bool(wl) and wl[0] == TRUE_WATCH[0]
    e["A4"] = wl == TRUE_WATCH          # passengers follow from naming the right markets
    e["A5"] = o["cflights"] == 4

    # a competent solver gets the mechanics right whatever its method
    for k in ("B1", "B2", "B3", "B4", "C1", "C2", "C21"):
        e[k] = True

    e["C3"] = ex.get("ATL-JFK") == TRUE_EXTRA["ATL-JFK"]
    e["C4"] = ex.get("ATL-EWR") == TRUE_EXTRA["ATL-EWR"]
    # the per-flight-month operations: unit- and cancellation-dependent
    e["C5"] = "ATL-JFK" in byk and byk["ATL-JFK"]["rates"] == TRUE_RATES["ATL-JFK"]
    e["C6"] = "ATL-EWR" in byk and byk["ATL-EWR"]["rates"] == TRUE_RATES["ATL-EWR"]
    e["C7"] = all(k in byk and byk[k]["close"] == v for k, v in TRUE_CLOSE.items())
    # the standard's test, honestly reported by this solver's own method
    e["C8"] = o["cflights"] == 4 and o["ccounts"] == 4
    e["C9"] = o["cflights"] == 4 and o["ccounts"] == 4
    e["C10"] = o["cflights"] == 4 and o["ccounts"] == 4
    e["C11"] = o["ccounts"] == 4
    # the two circulating views are read off the shipped files, so only the part that
    # depends on this solver's own replay can be lost
    e["C12"] = True
    e["C13"] = len(o["citable"]) == 0
    e["C14"] = ("ATL-JFK", 4818) in wl and ex.get("ATL-JFK") == 13
    e["C15"] = True
    e["C16"] = len(o["citable"]) == 0
    # the register's own totals, which the memo states
    e["C17"] = (o["chronic_months"], o["markets"]) == (333, 168)
    e["C18"] = name not in ("city-pair market", "flight-number unit", "per-service window")
    e["C19"] = name not in ("ArrDel15", "dropping cancellations",
                            "cancellations counted on time", "averaged flight-number rates")
    e["C20"] = name != "4-month runs counted" and e["C18"]
    e["C22"] = len(o["watch"]) == 2 and wl == TRUE_WATCH
    return e


rows = []
for name, kw in MISTAKES.items():
    o = outputs(**kw)
    e = score(o, name)
    pts = sum(WT[k] for k, v in e.items() if v)
    lost = [k for k, _ in CRIT if not e.get(k)]
    rows.append((name, pts, lost, o))

b = score(base, "none")
print(f"sanity: the admissible method scores {sum(WT[k] for k, v in b.items() if v)}/100")

print("\n" + "=" * 104)
print("SIMULATED MISTAKES — score on the mock rubric")
print("=" * 104)
print(f"{'mistake':32s}{'score':>7s}  {'its answer':>12s}  criteria lost")
for name, pts, lost, o in sorted(rows, key=lambda r: -r[1]):
    ans = f"{len(o['citable'])} citable"
    print(f"{name:32s}{pts:>6d}%  {ans:>12s}  {' '.join(lost)}")

flag = [(n, p) for n, p, _, _ in rows if p >= 45]
print("\nmistakes at or above 45%:", flag or "none")

print("\n" + "=" * 104)
print("WHAT EACH WOULD SHIP")
print("=" * 104)
for name, pts, lost, o in sorted(rows, key=lambda r: -r[1]):
    wl = [(w["market"], w["dom"], w["pax"], w["extra"]) for w in o["watch"]]
    print(f"\n  {name}  ({pts}%)")
    print(f"    citable: {o['citable'] if o['citable'] else 'none'}")
    print(f"    watch list: {wl}")
    print(f"    control: {o['cflights']}/4 flights, {o['ccounts']}/4 operation counts")
