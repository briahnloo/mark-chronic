"""Gate table for 2025: prove the NO is robust, show what each trap produces, and
build the watch list of four-month runs with T-100 passengers and the exact number of
extra late arrivals the following month would have needed."""
import math
import os
import pandas as pd
import scan_chronic as S

CACHE = "cache_2025.parquet"
T100 = "sources/t100_domestic_segment_2025.csv"


def prepared():
    if os.path.exists(CACHE):
        return pd.read_parquet(CACHE)
    df = pd.concat([S.load_month(y, m, "bts_raw", ["all"])
                    for y, m in S.month_range("2025-01:2025-12")]).reset_index(drop=True)
    df["dep_min"] = S.minutes(df.CRSDepTime)
    df = S.late_flags(df)
    df = S.sched_time(df)
    df = S.cluster(df, "Origin", "Dest", "win", col="dep_min")
    df = S.cluster(df, "OriginCityMarketID", "DestCityMarketID", "win_city", col="dep_min")
    df = S.cluster(df, "Origin", "Dest", "win_sched", col="sched_min")
    df.to_parquet(CACHE)
    return df


df = prepared()
print(f"2025 rows: {len(df):,}   carriers: {df.Reporting_Airline.nunique()}")

rule, g_rule, s_rule = S.answer(df)

VARIANTS = {
    "all diversions late": dict(late="late_divall"),
    "cancels not counted as operated": dict(excl=True),
    "window per service": dict(unit="win_sched"),
    "link on modal time <=30min": dict(link="modal", tol=30),
    "link on any shared flight no.": dict(link="fnum"),
    "link on identical modal time": dict(link="modal", tol=0),
}
TRAPS = {
    "flight-number unit": dict(unit="Flight_Number_Reporting_Airline", tol=0),
    "ArrDel15 flag": dict(late="late_15"),
    "cancelled rows dropped": dict(late="late_30_nocancel", drop=True),
    "cancels counted on time": dict(late="late_30_nocancel"),
    "4-month runs counted": dict(need=4),
    "literal city-pair market": dict(okey="OriginCityMarketID", dkey="DestCityMarketID",
                                     unit="win_city"),
}

var_ans = {n: S.answer(df, **kw)[0] for n, kw in VARIANTS.items()}
trap_ans = {n: S.answer(df, **kw)[0] for n, kw in TRAPS.items()}

t100 = pd.read_csv(T100)
pax = t100.groupby(["UNIQUE_CARRIER", "ORIGIN", "DEST"]).PASSENGERS.sum().to_dict()
pax_m = t100.set_index(["UNIQUE_CARRIER", "ORIGIN", "DEST", "MONTH"]).PASSENGERS.to_dict()

rows = []
for c in sorted(df.Reporting_Airline.unique()):
    adm = len(rule.get(c, []))
    vs = {n: len(a.get(c, [])) for n, a in var_ans.items()}
    ts = {n: a.get(c, []) for n, a in trap_ans.items()}
    sc = s_rule[s_rule.Reporting_Airline == c]
    near = sc[sc.run_len == 4]
    watch = []
    for ch, g in near.groupby("chain"):
        g = g.sort_values("period")
        o, d = g.iloc[0].O, g.iloc[0].D
        last = g.iloc[-1]
        nxt = last.period + 1
        # the cluster that would have continued this run in the following month
        cand = g_rule[(g_rule.Reporting_Airline == c) & (g_rule.O == o) & (g_rule.D == d)
                      & (g_rule.period == nxt) & (g_rule.dom == last.dom)]
        if len(cand):
            n0 = cand.iloc[0]
            ops, late = int(n0.ops), int(n0.late)
            need = math.floor(ops / 2) + 1
            extra = max(0, need - late)
            note = (f"{nxt}: {ops} ops, {late} late ({late/ops:.1%}); needed {need} "
                    f"-> {extra} more late arrivals to extend the run to five months")
            if ops < 10:
                note += " (but under 10 operations, so it could not be chronic)"
        else:
            ops = late = extra = None
            note = f"{nxt}: the flight did not operate in this market/window"
        watch.append(dict(market=f"{o}-{d}", modal=int(last.unit),
                          flights=sorted(set().union(*[set(x) for x in g.fnums])),
                          months=f"{g.iloc[0].period}..{last.period}",
                          pax_year=int(pax.get((c, o, d), 0)),
                          pax_run=int(sum(pax_m.get((c, o, d), 0) for _ in [0])),
                          extra_needed=extra, note=note))
    rows.append(dict(carrier=c, admissible=adm, variants=vs, traps=ts, watch=watch))

print("\n" + "=" * 100)
print("GATE TABLE 2025 — citable flights under the admissible method and every determinism variant")
print("=" * 100)
hdr = f"{'carrier':8s}{'admis':>6s}" + "".join(f"{n[:13]:>15s}" for n in VARIANTS)
print(hdr)
for r in rows:
    print(f"{r['carrier']:8s}{r['admissible']:>6d}" +
          "".join(f"{r['variants'][n]:>15d}" for n in VARIANTS))
allzero = all(r["admissible"] == 0 and all(v == 0 for v in r["variants"].values()) for r in rows)
print(f"\nevery cell zero across admissible + all 6 variants: {allzero}")

print("\n" + "=" * 100)
print("WHAT EACH TRAP PRODUCES (a non-empty list is a wrong YES)")
print("=" * 100)
print(f"{'carrier':8s}" + "".join(f"{n[:17]:>19s}" for n in TRAPS))
for r in rows:
    print(f"{r['carrier']:8s}" + "".join(f"{len(r['traps'][n]):>19d}" for n in TRAPS))
print("\ntrap detail (markets each trap would wrongly flag):")
for r in rows:
    hits = {n: v for n, v in r["traps"].items() if v}
    if hits:
        print(f"\n  {r['carrier']}:")
        for n, v in hits.items():
            print(f"    {n:28s} {len(v)}: {[(o,d) for o,d,_ in v]}")

print("\n" + "=" * 100)
print("WATCH LIST — runs of exactly four chronic months")
print("=" * 100)
for r in rows:
    if not r["watch"]:
        continue
    print(f"\n{r['carrier']}  ({len(r['watch'])} run(s))")
    for w in sorted(r["watch"], key=lambda x: -x["pax_year"]):
        print(f"  {w['market']:9s} modal {w['modal']//60:02d}{w['modal']%60:02d}  "
              f"{w['months']}  flights {w['flights']}")
        print(f"    T-100 2025 passengers on market: {w['pax_year']:,}")
        print(f"    {w['note']}")
