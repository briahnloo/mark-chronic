"""Part C.10: every number that appears in more than one deliverable must agree."""
import csv
import json
import re
import sys

import pdfplumber
from PIL import Image

F = json.load(open("golden_facts.json"))
fails = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
    if not ok:
        fails.append(name)


with pdfplumber.open("submission/exposure_memo.pdf") as d:
    memo = re.sub(r"\s+", " ", " ".join((p.extract_text() or "") for p in d.pages))
reg = list(csv.DictReader(open("submission/exposure_register.csv", newline="")))
prompt = open("prompt.md").read()

# --- figures that appear in more than one place
shared = {
    "337 (prompt, memo, working sheet)": ["337"],
    "111,871 passengers (memo, T-100)": ["111,871"],
    "98,799 passengers (memo, T-100)": ["98,799"],
    "13 extra late arrivals (memo)": ["13 more late arrivals"],
    "2 extra late arrivals (memo)": ["2 more late arrivals"],
    "operation counts 31/30/27/57 (memo, order)": ["31", "30", "27", "57"],
    "flight 4818 (memo, register, chart)": ["4818"],
    "flight 4602 (memo, register, chart)": ["4602"],
}
for label, needles in shared.items():
    check(label, all(n in memo for n in needles))

check("337 appears in the prompt", "337" in prompt)

# --- memo figures against golden_facts
w1, w2 = F["watch"][0], F["watch"][1]
check("memo watch order matches passengers",
      memo.index(f"{w1['pax']:,}") < memo.index(f"{w2['pax']:,}"))
check("memo ATL-JFK months", f"{w1['first']} to {w1['last']}" in memo)
check("memo ATL-EWR months", f"{w2['first']} to {w2['last']}" in memo)
check("memo cites the register by name", "exposure_register.csv" in memo)
check("memo cites the chart by name", "chronic_delay_timeline.png" in memo)

# --- register figures against the memo's claims
chronic = [r for r in reg if r["chronically_delayed"] == "yes"]
check(f"register chronic month count {len(chronic)} appears in the memo",
      str(len(chronic)) in memo, f"({len(chronic)})")
check(f"register row count {len(reg)} appears in the memo",
      str(len(reg)) in memo, f"({len(reg)})")
mk = len({r["market"] for r in reg})
check(f"register market count {mk} appears in the memo", str(mk) in memo, f"({mk})")
check("memo sets 333 beside the associate's 337",
      abs(memo.index("333") - memo.index("337")) < 300,
      f"(gap {abs(memo.index('333') - memo.index('337'))} chars)")
check("register citable all 'no'", {r["citable"] for r in reg} == {"no"})
check("register max streak is 4",
      max(int(r["consecutive_months"]) for r in reg) == 4,
      f"(max {max(int(r['consecutive_months']) for r in reg)})")

# the two watch flights' monthly rows must match what the memo prints
for w in (w1, w2):
    o, d = w["market"].split("-")
    for mo, ops, late, pct in w["rates"]:
        row = [r for r in reg if r["market"] == w["market"] and r["month"] == mo
               and str(w["flights"][0]) in r["flight_numbers"]]
        ok = bool(row) and int(row[0]["operations"]) == ops \
            and int(row[0]["late_arrivals"]) == late \
            and abs(float(row[0]["pct_late"]) - pct) < 0.05
        check(f"register {w['market']} {mo} matches the run the memo describes", ok)
        check(f"memo prints {w['market']} {mo} rate {pct}%", f"{pct}%" in memo)

# --- chart
im = Image.open("submission/chronic_delay_timeline.png")
check("chart is legible at 100% (>=1400px wide)", im.size[0] >= 1400, str(im.size))
check("chart names no tool", "matplotlib" not in str(im.text).lower())

# --- nothing the prompt did not ask for
asked = ["carrier", "market", "scheduled_departure", "flight_numbers", "month",
         "operations", "late_arrivals", "pct_late", "chronically_delayed",
         "consecutive_months", "citable"]
check("register columns are the plain set", list(reg[0].keys()) == asked,
      str(list(reg[0].keys())))

# the per-month operations the memo now prints must match the register exactly
for w in F["watch"]:
    for mo, ops, late, pct in w["rates"]:
        check(f"memo prints {w['market']} {mo} operations {ops} and late {late}",
              f"{ops}" in memo and f"{late}" in memo)
    check(f"memo prints {w['market']} closing month {w['nxt']} ops {w['nxt_ops']}",
          str(w["nxt_ops"]) in memo and str(w["nxt_late"]) in memo)

print(f"\n{'ALL CROSS-FILE NUMBERS AGREE' if not fails else str(len(fails))+' FAILED: '+str(fails)}")
sys.exit(1 if fails else 0)
