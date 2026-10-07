"""Does ATL-JFK outrank ATL-EWR under every reasonable T-100 definition?

The memo ranks the watch list by passengers, so the ordering is a pin. If a different but
equally defensible passenger definition flips it, the recommendation is not deterministic
and the carrier fails the gate.
"""
import pandas as pd

t = pd.read_csv("sources/t100_domestic_segment_2025.csv")
t = t[t.UNIQUE_CARRIER == "F9"]
print("columns:", list(t.columns))

MK = [("ATL", "JFK"), ("ATL", "EWR")]
RUN = {("ATL", "JFK"): range(5, 9), ("ATL", "EWR"): range(4, 8)}


def val(o, d, field, both, months):
    s = t[t.MONTH.isin(months)] if months is not None else t
    m = ((s.ORIGIN == o) & (s.DEST == d))
    if both:
        m |= ((s.ORIGIN == d) & (s.DEST == o))
    return s[m][field].sum()


fields = [c for c in ["PASSENGERS", "DEPARTURES_PERFORMED", "SEATS"] if c in t.columns]
rows = []
for field in fields:
    for both in (False, True):
        for mlabel, months in [("full year", None), ("run months", "run")]:
            v = {}
            for o, d in MK:
                mo = RUN[(o, d)] if months == "run" else None
                v[(o, d)] = val(o, d, field, both, mo if mo is not None else range(1, 13))
            jfk, ewr = v[("ATL", "JFK")], v[("ATL", "EWR")]
            rows.append((field, "both dirs" if both else "one dir", mlabel,
                         jfk, ewr, "JFK" if jfk > ewr else ("EWR" if ewr > jfk else "tie")))

print(f"\n{'field':22s}{'direction':11s}{'months':12s}{'ATL-JFK':>12s}{'ATL-EWR':>12s}  leader")
for r in rows:
    print(f"{r[0]:22s}{r[1]:11s}{r[2]:12s}{r[3]:>12,.0f}{r[4]:>12,.0f}  {r[5]}")

leaders = {r[5] for r in rows}
print(f"\ndistinct leaders across {len(rows)} definitions: {leaders}")
print("ORDERING IS STABLE" if leaders == {"JFK"} else "ORDERING FLIPS — pin is not deterministic")
