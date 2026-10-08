"""Record the columns, unit and shape of BTS's published chronic-delay lists."""
import pathlib
import pandas as pd

D = pathlib.Path("sources/bts_chronic")
for p in sorted(D.glob("btscd_*.xlsx"))[:3]:
    x = pd.ExcelFile(p)
    print("=" * 90)
    print(p.name, "| sheets:", x.sheet_names)
    for sh in x.sheet_names:
        raw = pd.read_excel(p, sheet_name=sh, header=None, nrows=14)
        print(f"\n-- sheet {sh!r}  (first 14 rows, all columns) --")
        print(raw.to_string(max_colwidth=28))
