"""Check the byte-for-byte filtering kept exactly the right rows and nothing else."""
import pandas as pd
import scan_chronic as S

bad = 0

# on-time: filtered file must equal the carrier's rows in the original PREZIP
for carrier, y, m in [("F9", 2025, 1), ("F9", 2025, 7), ("B6", 2023, 6), ("B6", 2022, 10)]:
    orig = S.load_month(y, m, "bts_raw", [carrier])
    filt = pd.read_csv(f"package/ontime_{carrier}_{y}_{m:02d}.csv", low_memory=False)
    same_rows = len(orig) == len(filt)
    same_cols = len(filt.columns) == 110
    only = set(filt.Reporting_Airline.unique()) == {carrier}
    # compare a content fingerprint on shared key columns
    k = ["FlightDate", "Flight_Number_Reporting_Airline", "Origin", "Dest", "CRSDepTime"]
    fa = set(map(tuple, orig[k].astype(str).values))
    fb = set(map(tuple, filt[k].astype(str).values))
    ok = same_rows and same_cols and only and fa == fb
    bad += not ok
    print(f"{'OK  ' if ok else 'FAIL'} ontime_{carrier}_{y}_{m:02d}: "
          f"{len(filt):,} rows (orig {len(orig):,}), {len(filt.columns)} cols, "
          f"carriers={sorted(set(filt.Reporting_Airline.unique()))}, keys match={fa == fb}")

# T-100
t = pd.read_csv("sources/t100_domestic_segment_2025.csv")
tf = pd.read_csv("package/t100_segment_F9_2025.csv")
exp = t[t.UNIQUE_CARRIER == "F9"]
ok = len(exp) == len(tf) and set(tf.UNIQUE_CARRIER.unique()) == {"F9"} \
    and int(exp.PASSENGERS.sum()) == int(tf.PASSENGERS.sum())
bad += not ok
print(f"{'OK  ' if ok else 'FAIL'} t100: {len(tf):,} rows (expected {len(exp):,}), "
      f"passengers {int(tf.PASSENGERS.sum()):,} vs {int(exp.PASSENGERS.sum()):,}")

# the two watch-list markets must still be present with the figures the memo will quote
for o, d, want in [("ATL", "JFK", 111871), ("ATL", "EWR", 98799)]:
    got = int(tf[(tf.ORIGIN == o) & (tf.DEST == d)].PASSENGERS.sum())
    bad += got != want
    print(f"{'OK  ' if got == want else 'FAIL'} t100 {o}-{d} passengers {got:,} "
          f"(expected {want:,})")

print(f"\n{bad} problem(s)")
raise SystemExit(1 if bad else 0)
