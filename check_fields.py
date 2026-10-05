import zipfile, pandas as pd, sys

need = ["Year", "Month", "FlightDate", "Reporting_Airline", "Flight_Number_Reporting_Airline",
        "Origin", "Dest", "OriginCityMarketID", "DestCityMarketID", "CRSDepTime", "ArrDelay",
        "ArrDel15", "Cancelled", "Diverted", "DivReachedDest", "DivArrDelay"]

for path in sys.argv[1:]:
    z = zipfile.ZipFile(path)
    print("=" * 70)
    print(path)
    print("members:", z.namelist())
    name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
    cols = list(pd.read_csv(z.open(name), nrows=0).columns)
    print("total columns:", len(cols))
    missing = [c for c in need if c not in cols]
    print("MISSING required fields:", missing or "none")

    df = pd.read_csv(z.open(name), usecols=need, low_memory=False)
    print("rows:", len(df), "| carriers:", len(df.Reporting_Airline.unique()))
    print("\ntrap-critical field profile:")
    for c in ["ArrDelay", "ArrDel15", "Cancelled", "Diverted", "DivReachedDest", "DivArrDelay", "CRSDepTime"]:
        s = df[c]
        print(f"  {c:16s} dtype={str(s.dtype):8s} nulls={s.isna().sum():7d} "
              f"sample={list(s.dropna().unique()[:4])}")
    canc = df[df.Cancelled == 1]
    print(f"\ncancelled rows: {len(canc)} | ArrDelay null: {canc.ArrDelay.isna().sum()} "
          f"| ArrDel15 null: {canc.ArrDel15.isna().sum()}")
    div = df[df.Diverted == 1]
    print(f"diverted rows: {len(div)} | DivReachedDest==1: {(div.DivReachedDest == 1).sum()} "
          f"| DivArrDelay notnull: {div.DivArrDelay.notna().sum()} | ArrDelay null: {div.ArrDelay.isna().sum()}")
    print(f"CRSDepTime min={df.CRSDepTime.min()} max={df.CRSDepTime.max()} "
          f"zeros={(df.CRSDepTime == 0).sum()} eq2400={(df.CRSDepTime == 2400).sum()}")
    print("B6 rows:", (df.Reporting_Airline == "B6").sum())
