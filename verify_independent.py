"""Independent recomputation of every pin in the deliverables.

Imports nothing from scan_chronic.py, gate_2025.py or make_goldens.py, reads only the
files that ship inside inputs.zip, and reimplements 14 CFR 399.81 from the regulation
text. Written against the rule, not against the other implementation.

399.81(c): a flight is chronically delayed in a month if it is operated at least 10 times
that month and arrives more than 30 minutes late (cancelled flights counting as late) more
than 50 percent of the time. (c)(3): "one single flight" means all of a carrier's flights
in a city-pair market whose scheduled departure times are within 30 minutes of the most
frequently occurring scheduled departure time. (c)(4): holding such a flight out for more
than four consecutive one-month periods is the violation.
"""
import collections
import csv
import glob
import json
import math
import re
import sys
import zipfile

P = "package"
fails = []


def check(name, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {got!r}" + ("" if ok else f"  expected {want!r}"))
    if not ok:
        fails.append(name)
    return ok


def hhmm(v):
    v = int(v)
    return (v // 100) * 60 + v % 100


def read_ontime(path):
    """Yield the handful of fields the rule needs, straight from the shipped CSV."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            yield r


def month_flights(rows):
    """Group a month's rows into the rule's flights and score each one.

    Clustering is done independently here: repeatedly take the most frequent scheduled
    departure time still unassigned (earliest wins a tie) and absorb everything within
    30 minutes of it.
    """
    by_market = collections.defaultdict(list)
    for r in rows:
        by_market[(r["Origin"], r["Dest"])].append(r)

    out = []
    for (o, d), rs in by_market.items():
        pool = list(rs)
        while pool:
            freq = collections.Counter(hhmm(r["CRSDepTime"]) for r in pool)
            top = max(freq.values())
            mode = min(t for t, c in freq.items() if c == top)
            inside = [r for r in pool if abs(hhmm(r["CRSDepTime"]) - mode) <= 30]
            pool = [r for r in pool if abs(hhmm(r["CRSDepTime"]) - mode) > 30]

            ops = len(inside)
            late = 0
            for r in inside:
                if r["Cancelled"] in ("1", "1.00", "1.0"):
                    late += 1                      # cancelled flights count as late
                    continue
                if r["Diverted"] in ("1", "1.00", "1.0"):
                    # A diverted flight has not arrived on time unless it in fact reached
                    # its scheduled destination within 30 minutes. ArrDelay is blank on
                    # every diverted row, so ignoring diversions silently scores them all
                    # on time; doing that loses FLL-JFK 1802 from the JetBlue control.
                    reached = r.get("DivReachedDest") in ("1", "1.00", "1.0")
                    dad = r.get("DivArrDelay")
                    on_time = reached and dad not in ("", None) and float(dad) <= 30
                    late += 0 if on_time else 1
                    continue
                ad = r["ArrDelay"]
                if ad not in ("", None) and float(ad) > 30:
                    late += 1
            nums = collections.Counter(int(r["Flight_Number_Reporting_Airline"])
                                       for r in inside)
            out.append(dict(O=o, D=d, mode=mode, ops=ops, late=late,
                            pct=late / ops * 100,
                            chronic=(ops >= 10 and late / ops > 0.5),
                            dom=nums.most_common(1)[0][0]))
    return out


def scan(paths):
    """Return {(origin, dest, dominant flight number): {month: record}}."""
    months = {}
    for p in sorted(paths):
        m = int(re.search(r"_(\d{4})_(\d{2})\.csv$", p).group(2))
        months[m] = month_flights(list(read_ontime(p)))
    return months


def runs(months):
    """Longest consecutive chronic runs, flights linked month to month by the flight
    number operating most of the cluster."""
    chains = []
    live = {}
    for m in sorted(months):
        seen = {}
        for f in months[m]:
            if not f["chronic"]:
                continue
            k = (f["O"], f["D"], f["dom"])
            prev = live.get(k)
            if prev and prev[-1]["m"] == m - 1:
                prev.append(dict(m=m, **f))
                seen[k] = prev
            else:
                ch = [dict(m=m, **f)]
                chains.append(ch)
                seen[k] = ch
        live = seen
    return chains


# ------------------------------------------------------------------ Frontier 2025
print("recomputing Frontier 2025 from the packaged on-time files ...")
f9m = scan(glob.glob(f"{P}/ontime_F9_2025_*.csv"))
f9c = runs(f9m)
longest = max((len(c) for c in f9c), default=0)
citable = [c for c in f9c if len(c) >= 5]
watch = sorted((c for c in f9c if len(c) == 4),
               key=lambda c: -sum(1 for _ in c))

check("longest consecutive chronic run, Frontier 2025", longest, 4)
check("citable flights (runs of five or more)", len(citable), 0)
check("flights with exactly four consecutive chronic months", len(watch), 2)

# passengers, from the packaged T-100
pax = collections.Counter()
with open(f"{P}/t100_segment_F9_2025.csv", newline="", encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        pax[(r["ORIGIN"], r["DEST"])] += float(r["PASSENGERS"])

info = []
for c in watch:
    o, d, dom = c[0]["O"], c[0]["D"], c[-1]["dom"]
    nxt = c[-1]["m"] + 1
    cand = [f for f in f9m.get(nxt, []) if (f["O"], f["D"], f["dom"]) == (o, d, dom)]
    n0 = cand[0]
    need = math.floor(n0["ops"] / 2) + 1
    info.append(dict(market=f"{o}-{d}", dom=dom, first=c[0]["m"], last=c[-1]["m"],
                     pax=int(pax[(o, d)]), extra=max(0, need - n0["late"]),
                     nxt=nxt, nxt_ops=n0["ops"], nxt_late=n0["late"],
                     nxt_pct=round(n0["late"] / n0["ops"] * 100, 1), need=need,
                     rates=[round(x["pct"], 1) for x in c]))
info.sort(key=lambda x: -x["pax"])

check("watch list, ranked by passengers",
      [(i["market"], i["dom"]) for i in info], [("ATL", "JFK"), ("ATL", "EWR")] and
      [("ATL-JFK", 4818), ("ATL-EWR", 4602)])
check("ATL-JFK passengers", info[0]["pax"], 111871)
check("ATL-EWR passengers", info[1]["pax"], 98799)
check("ATL-JFK chronic months", (info[0]["first"], info[0]["last"]), (5, 8))
check("ATL-EWR chronic months", (info[1]["first"], info[1]["last"]), (4, 7))
check("ATL-JFK extra late arrivals needed", info[0]["extra"], 13)
check("ATL-EWR extra late arrivals needed", info[1]["extra"], 2)
check("ATL-EWR following month", (info[1]["nxt"], info[1]["nxt_ops"],
                                  info[1]["nxt_late"], info[1]["nxt_pct"]),
      (8, 31, 14, 45.2))
check("ATL-JFK following month", (info[0]["nxt"], info[0]["nxt_ops"],
                                  info[0]["nxt_late"], info[0]["nxt_pct"]),
      (9, 30, 3, 10.0))
check("ATL-JFK monthly rates", info[0]["rates"], [54.8, 66.7, 58.1, 54.8])
check("ATL-EWR monthly rates", info[1]["rates"], [66.7, 81.0, 60.0, 80.6])

# ------------------------------------------------------------------ the control
print("\nrecomputing the JetBlue control from the packaged on-time files ...")
b6m = {}
for p in sorted(glob.glob(f"{P}/ontime_B6_*.csv")):
    y, m = re.search(r"_(\d{4})_(\d{2})\.csv$", p).groups()
    b6m[(int(y) - 2022) * 12 + int(m)] = month_flights(list(read_ontime(p)))
b6c = runs(b6m)
ORDER = {("JFK", "RDU"): (2585, 6, 10, 5, 31), ("FLL", "JFK"): (1802, 18, 22, 5, 30),
         ("MCO", "JFK"): (384, 18, 22, 5, 27), ("FLL", "BDL"): (460, 18, 23, 6, 57)}
got = {}
for c in b6c:
    if len(c) < 5:
        continue
    got[(c[0]["O"], c[0]["D"])] = (c[0]["m"], c[-1]["m"], len(c),
                                   sum(x["ops"] for x in c[4:]),
                                   {x["dom"] for x in c})
for k, (fn, m0, m1, n, ops) in ORDER.items():
    g = got.get(k)
    check(f"control {k[0]}-{k[1]} flight {fn}",
          None if not g else (g[0], g[1], g[2], g[3], fn in g[4]),
          (m0, m1, n, ops, True))
check("control extras beyond the order",
      sorted(f"{a}-{b}" for a, b in got if (a, b) not in ORDER),
      ["FLL-BOS", "MCO-LGA"])

# ------------------------------------------------------------------ [N] and the views
print("\nrecomputing [N] and the circulating views ...")
import openpyxl
wb = openpyxl.load_workbook(f"{P}/associate_working_sheet.xlsx")
rows2 = [r for r in wb["List extract"].iter_rows(min_row=6, values_only=True)
         if r[0] is not None]
check("[N], Frontier flight-months on BTS's lists", len(rows2), 337)
check("[N] as printed on the working sheet", wb["By flight"]["D4"].value, 337)
tab2 = wb["By flight"]
first = [c.value for c in tab2[8]]
check("first row of the roll-up tab", (first[0], first[1], first[2], first[3]),
      ("ATL", "JFK", 4818, 5))

listed = collections.defaultdict(set)
for r in rows2:
    mo, fn, o, d = r[0], r[2], r[3], r[4]
    listed[(o, d, int(fn))].add(int(str(mo)[-2:]))
top_months = sorted(listed[("ATL", "JFK", 4818)])
check("months ATL-JFK 4818 is listed in", top_months, [5, 6, 7, 8, 12])


def consec(ms):
    best = run = 1
    for a, b in zip(sorted(ms), sorted(ms)[1:]):
        run = run + 1 if b == a + 1 else 1
        best = max(best, run)
    return best


check("its longest consecutive stretch of listings", consec(top_months), 4)
check("Frontier flight numbers on five consecutive BTS lists",
      sum(1 for ms in listed.values() if consec(ms) >= 5), 0)

dash = set()
with open(f"{P}/monitoring_dashboard_export.csv", newline="") as fh:
    for r in csv.DictReader(fh):
        if int(r["flag_months_consecutive_max"]) >= 5:
            dash.add(r["market"])
check("dashboard problem-flight list",
      sorted(dash), ["ATL-EWR", "ATL-LGA", "LAX-ATL", "PHL-SJU"])

# ------------------------------------------------------------------ the register
print("\nchecking the register against this recomputation ...")
with open("submission/exposure_register.csv", newline="") as fh:
    reg = list(csv.DictReader(fh))
check("register columns", list(reg[0].keys()),
      ["carrier", "market", "scheduled_departure", "flight_numbers", "month",
       "operations", "late_arrivals", "pct_late", "chronically_delayed",
       "consecutive_months", "citable"])
check("register rows", len(reg), 582)
check("register chronic months", sum(1 for r in reg if r["chronically_delayed"] == "yes"), 333)
check("register distinct markets", len({r["market"] for r in reg}), 168)
check("register citable values", sorted({r["citable"] for r in reg}), ["no"])
check("register months are YYYY-MM",
      all(re.fullmatch(r"2025-\d{2}", r["month"]) for r in reg), True)
check("register percentages to one decimal",
      all(re.fullmatch(r"\d+\.\d", r["pct_late"]) for r in reg), True)
mine = {(f"{f['O']}-{f['D']}", m, f["mode"]): (f["ops"], f["late"])
        for m in f9m for f in f9m[m] if f["chronic"]}
agree = 0
for r in reg:
    if r["chronically_delayed"] != "yes":
        continue
    k = (r["market"], int(r["month"][-2:]),
         hhmm(r["scheduled_departure"]))
    if k in mine and mine[k] == (int(r["operations"]), int(r["late_arrivals"])):
        agree += 1
check("chronic register rows whose operations and late arrivals I reproduce",
      agree, 333)

print(f"\n{'ALL PINS REPRODUCED' if not fails else str(len(fails)) + ' FAILED: ' + str(fails)}")
sys.exit(1 if fails else 0)
