"""Build the filtered input files for inputs.zip.

The on-time files are filtered by reading the raw CSV out of each PREZIP and keeping the
header plus every line whose Reporting_Airline field matches, byte for byte. Nothing is
parsed and re-serialised, so the kept lines are identical to BTS's own bytes.
"""
import csv
import hashlib
import io
import pathlib
import zipfile

OUT = pathlib.Path("package")
OUT.mkdir(exist_ok=True)
RAW = pathlib.Path("bts_raw")

F9_MONTHS = [(2025, m) for m in range(1, 13)]
B6_MONTHS = [(2022, m) for m in range(5, 11)] + [(2023, m) for m in range(5, 12)]


def member(zp):
    with zipfile.ZipFile(zp) as z:
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        return name, z.read(name)


def filter_carrier(zp, carrier):
    """Keep the header line and every data line for `carrier`, bytes untouched."""
    name, blob = member(zp)
    lines = blob.split(b"\n")
    header = lines[0]
    cols = next(csv.reader(io.StringIO(header.decode("utf-8-sig"))))
    ci = cols.index("Reporting_Airline")
    tag = b'"' + carrier.encode() + b'"'
    kept = [header]
    for ln in lines[1:]:
        if not ln.strip():
            continue
        # the carrier field is quoted and column 6 of a fixed layout; split only as far
        # as needed and verify the field rather than substring-matching the whole line
        parts = ln.split(b",", ci + 1)
        if len(parts) > ci and parts[ci] == tag:
            kept.append(ln)
    return header, kept, name


rows = []
for carrier, months, label in [("F9", F9_MONTHS, "F9"), ("B6", B6_MONTHS, "B6")]:
    for y, m in months:
        zp = RAW / f"ontime_{y}_{m:02d}.zip"
        assert zp.exists(), f"missing {zp}"
        header, kept, srcname = filter_carrier(zp, carrier)
        blob = b"\n".join(kept) + b"\n"
        out = OUT / f"ontime_{label}_{y}_{m:02d}.csv"
        out.write_bytes(blob)
        rows.append((out.name, len(kept) - 1, srcname))
        print(f"{out.name:28s} {len(kept)-1:7d} rows  {len(blob):10,d} bytes")

# readme.html, straight out of a PREZIP, unmodified
with zipfile.ZipFile(RAW / "ontime_2025_01.zip") as z:
    (OUT / "readme.html").write_bytes(z.read("readme.html"))
print(f"\nreadme.html {(OUT/'readme.html').stat().st_size:,} bytes (unmodified from PREZIP)")

# T-100 filtered to F9, header kept, lines byte-for-byte
src = pathlib.Path("sources/t100_domestic_segment_2025.csv")
lines = src.read_bytes().split(b"\n")
cols = next(csv.reader(io.StringIO(lines[0].decode("utf-8-sig"))))
ci = cols.index("UNIQUE_CARRIER")
kept = [lines[0]] + [ln for ln in lines[1:] if ln.strip()
                     and ln.split(b",", ci + 1)[ci].strip(b'"') == b"F9"]
(OUT / "t100_segment_F9_2025.csv").write_bytes(b"\n".join(kept) + b"\n")
print(f"t100_segment_F9_2025.csv {len(kept)-1:,} rows")

for src, dst in [("sources/DOT_JetBlue_Order_2024-12-21.pdf",
                  "DOT_JetBlue_Order_2024-12-21.pdf"),
                 ("sources/CFR_14_399.81.pdf", "14_CFR_399.81.pdf")]:
    (OUT / dst).write_bytes(pathlib.Path(src).read_bytes())
    print(f"{dst} copied")

for p in sorted(pathlib.Path("sources/bts_chronic").glob("btscd_*.xlsx")):
    (OUT / p.name.replace("btscd_", "bts_chronic_list_")).write_bytes(p.read_bytes())
print(f"12 BTS lists copied unmodified")

print(f"\n{len(list(OUT.iterdir()))} files staged in {OUT}/")
