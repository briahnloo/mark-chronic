"""Build all three golden deliverables from one run of the admissible replay."""
import math
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import scan_chronic as S

OUT = pathlib.Path("submission")
OUT.mkdir(exist_ok=True)
CAR = "F9"

df = pd.read_parquet("cache_2025.parquet")
f9 = df[df.Reporting_Airline == CAR].reset_index(drop=True)
ans, g, s = S.answer(f9)

# ---------------------------------------------------------------- register
chain = s.set_index(["O", "D", "unit", "period"])[["streak", "run_len", "chain"]]
reg = g.merge(chain, left_on=["O", "D", "unit", "period"], right_index=True, how="left")
reg = reg[reg.chronic | reg.index.isin(
    reg[reg.O.isin(s.O) & reg.D.isin(s.D)].index)]
# the prompt asks for every flight chronically delayed in at least one month: all months
# of any cluster-chain that is chronic somewhere
chronic_keys = set(zip(s.O, s.D, s.unit))
reg = g[[(o, d, u) in chronic_keys for o, d, u in zip(g.O, g.D, g.unit)]].copy()
reg = reg.merge(chain, left_on=["O", "D", "unit", "period"], right_index=True, how="left")
reg["streak"] = reg.streak.fillna(0).astype(int)
reg["run_len"] = reg.run_len.fillna(0).astype(int)

R = pd.DataFrame({
    "carrier": CAR,
    "market": reg.O + "-" + reg.D,
    "scheduled_departure": reg.unit.map(lambda u: f"{int(u)//60:02d}{int(u)%60:02d}"),
    "flight_numbers": reg.fnums.map(lambda f: " ".join(str(x) for x in sorted(f))),
    "month": reg.period.astype(str),
    "operations": reg.ops.astype(int),
    "late_arrivals": reg.late.astype(int),
    "pct_late": (reg.pct_late * 100).round(1),
    "chronically_delayed": reg.chronic.map({True: "yes", False: "no"}),
    "consecutive_months": reg.streak,
    "citable": "no",
}).sort_values(["market", "scheduled_departure", "month"]).reset_index(drop=True)
R.to_csv(OUT / "exposure_register.csv", index=False)
print(f"exposure_register.csv: {len(R)} rows, "
      f"{(R.chronically_delayed == 'yes').sum()} chronic months, "
      f"{R.market.nunique()} markets, citable={set(R.citable)}")

# ---------------------------------------------------------------- watch list
t100 = pd.read_csv("package/t100_segment_F9_2025.csv")
pax = t100.groupby(["ORIGIN", "DEST"]).PASSENGERS.sum().to_dict()

watch = []
for ch, h in s[s.run_len == 4].groupby("chain"):
    h = h.sort_values("period")
    o, d, last = h.iloc[0].O, h.iloc[0].D, h.iloc[-1]
    nxt = last.period + 1
    cand = g[(g.O == o) & (g.D == d) & (g.period == nxt) & (g.dom == last.dom)]
    n0 = cand.iloc[0]
    need = math.floor(int(n0.ops) / 2) + 1
    watch.append(dict(
        market=f"{o}-{d}", window=int(last.unit),
        flights=sorted(set().union(*[set(x) for x in h.fnums])),
        first=str(h.iloc[0].period), last=str(last.period),
        months=[str(p) for p in h.period],
        pax=int(pax.get((o, d), 0)),
        nxt=str(nxt), nxt_ops=int(n0.ops), nxt_late=int(n0.late),
        nxt_pct=round(float(n0.pct_late) * 100, 1),
        need=need, extra=max(0, need - int(n0.late)),
        rates=[(str(r.period), int(r.ops), int(r.late), round(r.pct_late * 100, 1))
               for r in h.itertuples()]))
watch.sort(key=lambda w: -w["pax"])
for w in watch:
    print(f"  {w['market']} {w['window']//60:02d}{w['window']%60:02d} {w['first']}..{w['last']} "
          f"pax {w['pax']:,} extra {w['extra']}")

# ---------------------------------------------------------------- control
dfb = pd.concat([S.load_month(y, m, "bts_raw", ["B6"])
                 for y, m in S.month_range("2022-05:2023-11")]).reset_index(drop=True)
dfb["dep_min"] = S.minutes(dfb.CRSDepTime)
dfb = S.late_flags(dfb)
dfb = S.sched_time(dfb)
dfb = S.cluster(dfb, "Origin", "Dest", "win", col="dep_min")
dfb = S.cluster(dfb, "OriginCityMarketID", "DestCityMarketID", "win_city", col="dep_min")
dfb = S.cluster(dfb, "Origin", "Dest", "win_sched", col="sched_min")
ansb, gb, sb = S.answer(dfb)
ORDER = {("JFK", "RDU"): (2585, "2022-06", "2022-10", 5, 31),
         ("FLL", "JFK"): (1802, "2023-06", "2023-10", 5, 30),
         ("MCO", "JFK"): (384, "2023-06", "2023-10", 5, 27),
         ("FLL", "BDL"): (460, "2023-06", "2023-11", 6, 57)}
ctl = {}
for ch, h in sb[sb.run_len >= 5].groupby("chain"):
    h = h.sort_values("period")
    o, d = h.iloc[0].O, h.iloc[0].D
    ctl[(o, d)] = (str(h.iloc[0].period), str(h.iloc[-1].period),
                   int(h.run_len.max()), int(h.iloc[4:].ops.sum()),
                   sorted(set().union(*[set(x) for x in h.fnums])))
ctl_rows = []
for k, (fn, m0, m1, r, c) in ORDER.items():
    got = ctl.get(k)
    ok = got and got[0] == m0 and got[1] == m1 and got[2] == r and got[3] == c
    ctl_rows.append((f"{k[0]}-{k[1]}", fn, f"{m0}..{m1}", r, c,
                     "matched" if ok else "DIFFERS", got))
    print(f"  control {k[0]}-{k[1]} {fn}: {'matched' if ok else 'DIFFERS'} {got[:4] if got else None}")
extra_ctl = sorted(k for k in ctl if k not in ORDER)
print(f"  control extras: {extra_ctl}")

# ---------------------------------------------------------------- other views
assoc = pd.read_csv("bts_f9_rows.csv")
N = len(assoc)
ap = pd.read_csv("assoc_plain.csv")
assoc_top = ap.sort_values(["months_listed", "mean_pct"], ascending=False).iloc[0]
dash = pd.read_csv("package/monitoring_dashboard_export.csv")
dash_list = sorted(set(dash[dash.flag_months_consecutive_max >= 5].market))
trap_ans = S.answer(f9, late="late_15")[0].get(CAR, [])
print(f"\n[N]={N}  assoc top={assoc_top.market} {assoc_top.flight_number} "
      f"({assoc_top.months_listed} lists, {assoc_top.consecutive_months} consecutive)")
print(f"dashboard list: {dash_list}")

# ---------------------------------------------------------------- timeline
months = [f"2025-{m:02d}" for m in range(1, 13)]

# One row per chain. A chain's modal departure can drift between months, so its months are
# matched on the dominant flight number, not on a single fixed departure minute.
series = []
for ch, h in s.groupby("chain"):
    h = h.sort_values("period")
    o, d = h.iloc[0].O, h.iloc[0].D
    dom = h.iloc[-1].dom
    # the chain's own months, taken from its own rows
    cells = {str(r.period): (int(r.ops), float(r.pct_late)) for r in h.itertuples()}
    chron = set(cells)
    # context months: among clusters in this market/month run by the same flight number,
    # the one whose modal departure is nearest the chain's, and only within 90 minutes
    ref = int(h.iloc[-1].unit)
    pool = g[(g.O == o) & (g.D == d) & (g.dom == dom)]
    for mo in months:
        if mo in cells:
            continue
        cand = pool[pool.period.astype(str) == mo]
        if not len(cand):
            continue
        cand = cand.assign(gap=(cand.unit - ref).abs()).sort_values(["gap", "unit"])
        if int(cand.iloc[0].gap) <= 90:
            cells[mo] = (int(cand.iloc[0].ops), float(cand.iloc[0].pct_late))
    units = sorted({int(u) for u in h.unit})
    lbl = f"{o}-{d}  " + "/".join(f"{u//60:02d}{u%60:02d}" for u in units[:2])
    series.append((int(h.run_len.max()), lbl, cells, chron, int(dom)))
series.sort(key=lambda t: (-t[0], t[1]))
rows_t = series[:26]

fig, ax = plt.subplots(figsize=(11.6, 0.42 * len(rows_t) + 2.6))
for i, (rl, lbl, cells, ms, dom) in enumerate(rows_t):
    y = len(rows_t) - i - 1
    for j, mo in enumerate(months):
        if mo not in cells:
            continue
        ops, pct = cells[mo]
        chron = mo in ms
        col = "#C0392B" if chron else ("#D5DBDB" if ops >= 10 else "#F2F4F4")
        ax.add_patch(plt.Rectangle((j, y - 0.34), 0.92, 0.68, facecolor=col,
                                   edgecolor="white", linewidth=0.8))
        if ops >= 10:
            ax.text(j + 0.46, y, f"{pct*100:.0f}", ha="center", va="center",
                    fontsize=5.8, color="white" if chron else "#566573")
    ax.text(-0.3, y, f"{lbl}  (fl {dom})", ha="right", va="center", fontsize=7.2,
            fontweight="bold" if rl == 4 else "normal")
    if rl == 4:
        js = sorted(months.index(m) for m in ms)
        ax.add_patch(plt.Rectangle((min(js) - 0.07, y - 0.45), max(js) - min(js) + 1.06,
                                   0.90, fill=False, edgecolor="#1A5276", linewidth=2.0))
        ax.text(12.35, y, "4 consecutive - closest to the line", fontsize=7.2,
                va="center", color="#1A5276", fontweight="bold")

ax.set_xlim(-5.2, 19.0)
ax.set_ylim(-0.8, len(rows_t) - 0.2)
ax.set_xticks([j + 0.46 for j in range(12)])
ax.set_xticklabels([m[-2:] for m in months], fontsize=8)
ax.set_yticks([])
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_xlabel("month of 2025", fontsize=9)
ax.set_title("Frontier 2025: chronically delayed flight-months, and the streaks that came "
             "closest to the line\nNo flight reached a fifth consecutive chronic month, so "
             "none is citable under 14 CFR 399.81",
             fontsize=10.5, fontweight="bold", loc="left")
leg = [mpatches.Patch(facecolor="#C0392B", label="chronically delayed that month"),
       mpatches.Patch(facecolor="#D5DBDB", label="operated 10+ times, not chronic"),
       mpatches.Patch(facecolor="#F2F4F4", label="operated fewer than 10 times"),
       mpatches.Patch(facecolor="white", edgecolor="#1A5276", linewidth=1.9,
                      label="four consecutive chronic months (flight to watch)")]
ax.legend(handles=leg, loc="lower left", bbox_to_anchor=(0.0, -0.085 - 1.4/len(rows_t)),
          ncol=2, fontsize=7.6, frameon=False)
fig.text(0.012, 0.012, "Numbers in cells are the month's late-arrival percentage. "
         "Cancellations count as late arrivals. Rows are one flight in the sense of "
         "14 CFR 399.81(c)(3); the label gives the market, the modal departure time(s) "
         "and the flight number operating most of it.",
         fontsize=7.0, color="#566573")
plt.tight_layout()
meta = {"Software": "Brannock Aviation Advisory",
        "Title": "Frontier 2025 chronic delay timeline"}
plt.savefig(OUT / "chronic_delay_timeline.png", dpi=190, bbox_inches="tight",
            facecolor="white", metadata=meta)
plt.close()
print(f"\nchronic_delay_timeline.png: {len(rows_t)} flight rows")

# stash the figures the memo and the verifier both need
import json
pathlib.Path("golden_facts.json").write_text(json.dumps(dict(
    citable=len(ans.get(CAR, [])), N=N,
    watch=watch, control=[(a, b, c, d, e, f) for a, b, c, d, e, f, _ in ctl_rows],
    control_extras=[f"{a}-{b}" for a, b in extra_ctl],
    assoc_top=dict(market=assoc_top.market, fn=int(assoc_top.flight_number),
                   listed=int(assoc_top.months_listed),
                   consec=int(assoc_top.consecutive_months),
                   months=assoc_top.months),
    assoc_five=int((ap.consecutive_months >= 5).sum()),
    dash_list=dash_list, trap15=[f"{o}-{d}" for o, d, _ in trap_ans],
    register_rows=len(R), chronic_months=int((R.chronically_delayed == "yes").sum()),
    markets=int(R.market.nunique()),
), indent=1, default=str))
print("wrote golden_facts.json")
