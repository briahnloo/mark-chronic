"""Search the whole folder for the old firm name, including inside xlsx, PDF and PNG."""
import pathlib
import re
import sys
import zipfile

NEEDLE = "halvors"
SKIP = {".venv", "__pycache__", "bts_raw", "archive", ".git"}
hits = []

for p in sorted(pathlib.Path(".").rglob("*")):
    if not p.is_file() or any(s in p.parts for s in SKIP):
        continue
    try:
        if p.suffix.lower() == ".pdf":
            import pdfplumber
            with pdfplumber.open(p) as d:
                txt = "\n".join((pg.extract_text() or "") for pg in d.pages)
                meta = str(d.metadata)
            if NEEDLE in (txt + meta).lower():
                hits.append((p, "pdf text or metadata"))
        elif p.suffix.lower() in (".xlsx", ".zip"):
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    blob = z.read(n)
                    if NEEDLE.encode() in blob.lower():
                        hits.append((p, f"inside member {n}"))
                        break
                    if n.lower().endswith((".pdf", ".xlsx")) and p.suffix == ".zip":
                        # nested document: check its extracted text too
                        import io
                        if n.lower().endswith(".xlsx"):
                            with zipfile.ZipFile(io.BytesIO(blob)) as z2:
                                if any(NEEDLE.encode() in z2.read(m).lower()
                                       for m in z2.namelist()):
                                    hits.append((p, f"inside nested {n}"))
                                    break
                        else:
                            import pdfplumber
                            with pdfplumber.open(io.BytesIO(blob)) as d:
                                t = "\n".join((pg.extract_text() or "") for pg in d.pages)
                                if NEEDLE in (t + str(d.metadata)).lower():
                                    hits.append((p, f"inside nested {n}"))
                                    break
        else:
            blob = p.read_bytes()
            if NEEDLE.encode() in blob.lower():
                hits.append((p, "raw bytes"))
    except Exception as e:
        print(f"  (could not scan {p}: {type(e).__name__})")

for p, where in hits:
    print(f"HIT  {p}  ({where})")
print(f"\n{len(hits)} hit(s) for {NEEDLE!r}")
sys.exit(1 if hits else 0)
