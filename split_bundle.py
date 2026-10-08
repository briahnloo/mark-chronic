"""Split the one-download bundle of BTS chronic-delay xlsx files back into real files.

bts.gov 403s curl and Chrome blocks multiple automatic downloads from the site, so the
twelve 2025 files were fetched same-origin in the page and concatenated into one blob with
a length index header. Bytes are untouched; this only slices them apart.
"""
import hashlib
import pathlib
import sys

SEP = b"---BLOBSTART---\n"
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "sources/bts_chronic/btscd_bundle.bin")
out = pathlib.Path("sources/bts_chronic")

raw = src.read_bytes()
i = raw.index(SEP)
index = [l.split("\t") for l in raw[:i].decode().strip().split("\n")]
body = raw[i + len(SEP):]

pos = 0
for name, size in index:
    size = int(size)
    blob = body[pos:pos + size]
    pos += size
    assert len(blob) == size, f"{name}: short read {len(blob)} of {size}"
    assert blob[:2] == b"PK", f"{name}: not a zip/xlsx (starts {blob[:4]!r})"
    (out / name).write_bytes(blob)
    print(f"{name:42s} {size:7d}  {hashlib.sha256(blob).hexdigest()}")
assert pos == len(body), f"trailing {len(body) - pos} bytes unaccounted for"
print(f"\n{len(index)} files, {pos} bytes, fully accounted for")
