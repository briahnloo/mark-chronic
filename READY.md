# READY — chronic delay task (14 CFR 399.81), Frontier 2025

**Status: built and verified. Not submitted.**

Run 2026-10-07/08 in `/Users/bzliu/mark-chronic`, venv `.venv` (Python 3.13.3, pandas
3.0.6, matplotlib 3.11.2, reportlab 5.0.1, openpyxl, pyarrow, pdfplumber).

**The answer is a justified NO.** No Frontier flight was chronically delayed for more than
four consecutive months in 2025, so DOT could cite none of them. Two flights reached four
consecutive chronic months; ATL-EWR flight 4602 finished **two late arrivals** short of a
fifth.

Deliverables in `submission/`: `inputs.zip` (28.0 MB, 45 files), `exposure_register.csv`,
`exposure_memo.pdf`, `chronic_delay_timeline.png`. Prompt at `prompt.md` (2,178 chars).

---

## 1. The pins

| Pin | Value | Where it is stated |
|---|---|---|
| P1 answer | 0 citable flights | memo ¶1, register `citable` column, timeline subtitle |
| P2 watch list | ATL-JFK 4818 2025-05..08; ATL-EWR 4602 2025-04..07 | memo table, timeline boxes |
| P3 passengers | ATL-JFK 111,871; ATL-EWR 98,799 | memo table |
| P4 extra late arrivals | ATL-JFK 13; ATL-EWR **2** | memo table and ¶ per flight |
| P5 control | 4/4 flights, 4/4 operation counts 31/30/27/57 | memo control table |
| P6 circulating views | associate: 0 citable, top ATL-JFK 4818 on 5 lists; dashboard: 4 flights | memo §"two views" |
| P7 [N] | **337** | prompt, memo ¶2, working sheet cell E5 |

Supporting pins: register 582 rows / 333 chronic months; control extras FLL-BOS and
MCO-LGA; monthly rates 54.8/66.7/58.1/54.8 and 66.7/81.0/60.0/80.6.

**Every pin above was recomputed by `verify_independent.py`**, which imports none of my
code, reads only files inside `inputs.zip`, and reimplements the rule from its text.
Result: `ALL PINS REPRODUCED` (29 checks, exit 0).

That script earned its keep. Its first version ignored diversions — `ArrDelay` is blank on
every diverted row, so they scored silently on time. That reading **loses FLL-JFK 1802
from the control** and misses 22 chronic register rows. The control caught it, which is
exactly the role section 2 of the standard gives it. Fixed from the reg text: a diverted
flight has not arrived on time unless it reached its destination within 30 minutes.

## 2. Pin sensitivity (gate A)

| Mistake | Its answer | P1 | P2 | P4 | P5 | pins | control |
|---|---|---|---|---|---|---|---|
| averaged flight-number rates | **1 false YES** | Y | Y | Y | Y | **4** | 2/4, 2/4 |
| ArrDel15 | **4 false YES** | Y | Y | Y | · | **3** | 4/4, 4/4 |
| literal city-pair market | 0, **watch list emptied** | · | Y | Y | Y | **3** | 1/4, 1/4 |
| cancellations counted on time | 0, **watch list emptied** | · | Y | Y | Y | **3** | 2/4, 2/4 |
| ">50%" as "at least 50%" | 0, **watch list 2 → 7** | · | Y | Y | · | **2** | 4/4, 4/4 |
| 4-month runs counted | **2 false YES** | Y | · | · | · | 1 | 4/4, 4/4 |
| flight-number unit | 0 | · | · | · | Y | 1 | 4/4, **1/4** |
| per-service window | 0 | · | · | · | Y | 1 | 4/4, **2/4** |
| dropping cancellations | 0 | · | · | · | Y | 1 | 3/4, 3/4 |
| BTS lists read by flight number | 0, **top flight looks citable on 5 listings** | · | Y | Y | n/a | 2 | n/a |

Evidence: `pin_gate_out.txt`, `gate_2025_out.txt`, `bts_lists_out.txt`.

Dropped on test, as instructed: **"sub-10-operation month skipped"** moved only P5 and left
Frontier's 2025 output identical, so it earned nothing. Kept: **">50%" as "at least
50%"** — it moves two pins and, unlike most, the control does **not** catch it (4/4, 4/4),
so it has no built-in escape hatch.

The three mistakes the shipped control exposes (flight-number unit 1/4, per-service window
2/4, dropping cancellations 3/4) are the measured trap: a model that skips the control
replay keeps them, and a model that runs it cannot.

**T-100 ordering is deterministic.** ATL-JFK leads ATL-EWR under all 8 reasonable
definitions (passengers and departures × one direction or both × full year or run months),
by 10–24%. `t100_robust_out.txt`.

## 3. Gate P7: BTS's lists — reproduced in part, not exactly

| Question | Finding |
|---|---|
| Columns | rank, marketing carrier, operating carrier, flight number, month, origin-destination airports, scheduled departure time, operations, late operations, percent late, average minutes late. **Three different layouts** across the year (Jan–Sep "Rank", Oct–Nov "RANK" with a typo'd "MARKETING CARRER", Dec a 13-column "Year" sheet). |
| Unit | **One flight number at one scheduled departure time** on an airport pair. Settled by BTS's own duplicate keys: IAH-ATL flight 2400 appears twice in May 2025, at 1231 and 1639, 10 operations each. Not the rule's 30-minute cluster. |
| Totals | 7,108 rows across all carriers; 337 Frontier rows; operations 10–31, percent 51.61–100.00; `late/ops` reproduces the printed percent exactly. |
| Best convention | flight number + listed departure time, ±30-minute band, >30 min late with cancellations counted late: **284 of 337 exact on both operations and late counts**. |
| Residual | 53 rows differ by one or two operations **in both directions**. Not closable from the published data. |

**P7 FAILS.** Per your instruction the standard drops its BTS clause: RS-4 section 2 now
rests on the JetBlue order alone, and adds a sentence saying a published tabulation is not
an admissibility test and may be used only as corroboration. The memo states the 284/337
reconciliation and that it is corroboration, not a passed check.

The lists still earn their place: they are the source of [N] = 337 and of the associate's
sheet, and **they independently corroborate the watch list** — the only two Frontier flight
numbers on four consecutive lists are 4602 ATL-EWR (04–07) and 4818 ATL-JFK (05–08), the
same two flights the replay finds.

**The averaged reading did not fall out honestly.** Averaging the listed percentages to
market and departure window gives 0 citable, a longest run of 4, and a top row of ATL-BWI
2510 — it does not put ATL-EWR on top. So per your instruction the sheet uses the **plain
flight-number reading**. That reading is a better trap anyway: its top row, **ATL-JFK 4818,
is listed in five months** (05, 06, 07, 08, 12), so a reader counting listings rather than
consecutive listings reports a violation. Only four are consecutive; the fifth is December.

## 4. Rule-by-rule audit

| Rule | Status | Evidence |
|---|---|---|
| 10+ files, 3+ formats, a 10,000+ row table | **PASS** | 45 files; .csv 28, .xlsx 13, .pdf 3, .html 1; largest table 24,639 rows (`ontime_B6_2023_05.csv`); 25 of 25 on-time files exceed 10,000 rows |
| Real, license-clean, source/date/license recorded | **PASS** | `provenance.csv` describes all 44 non-self files with URL, pull date, licence, transform, rows, bytes, SHA-256; every government file marked public domain; all hashes re-verified after zipping |
| Never fabricate a source file | **PASS** | every source fetched from BTS, govinfo or DOT. bts.gov and transportation.gov 403 curl, so both were fetched through the browser; the twelve lists verified against the sizes read off the index pages and triplicate downloads confirmed byte-identical |
| No padding; removing any file breaks the answer | **PASS, with one caveat** | the 12 Frontier months give the answer; the 13 JetBlue months are the admissibility control and every one is load-bearing (the runs span 2022-06..10 and 2023-06..11, with May as the lead-in that proves the run starts in June); the 12 lists give [N] and the associate's sheet; T-100 gives the ranking; the rule and order define the test. **Caveat:** the two 2022-05 and 2023-05 lead-in months are load-bearing only for showing the runs do not start earlier |
| Recommendation needs a 2+ table join | **PASS** | the fix order joins the on-time files (runs) to T-100 (passengers); neither alone produces it |
| One deterministic recommendation | **PASS** | 0 citable under the admissible method and all 6 determinism variants for F9 (`gate_2025_out.txt`); the passenger ranking is stable under all 8 T-100 definitions |
| Prompt: natural prose, ≤2,500 chars, no method/trap leak | **PASS** | 2,178 chars; names no unit, no field, no cancellation or diversion handling, no threshold |
| 1–3 deliverables, visual prioritised | **PASS** | 3: register, memo, timeline |
| Honest traps only, no planted defects | **PASS** | every trap is a real property of the real data or a real reading of the rule: `ArrDel15` is BTS's own field; the lists really are per flight number; the cancellation and diversion fields really are blank where noted; "more than four" is the reg's own wording |
| Golden: decision first, one set of numbers | **PASS** | memo opens with the answer in one sentence; all three files built by one run of `make_goldens.py` + `make_memo.py` off one `golden_facts.json` |
| Determinism (no author-chosen cutoffs) | **PASS** | the two genuine forks — per-departure vs per-service window, and month-to-month linkage — are both settled by the control, not by preference |
| Control reproduces DOT's flights | **PASS** | 4/4 flights, 4/4 published operation counts, reproduced twice by independent code |
| Stay in folder, use a venv | **PASS** | all work in `/Users/bzliu/mark-chronic`; `~/mark-pm25` untouched |
| Scenario documents use the fictional firm only | **PASS** | "Halvorsen Aviation Advisory" throughout; no such firm exists (nearest is Halvorson Aviation Group — different spelling, different name); the standard and sheet never name Frontier or DOT as their author |
| Nothing submitted | **PASS** | nothing uploaded anywhere |

## 5. Clause-by-clause check of the prompt

| Prompt clause | Answered in | Check |
|---|---|---|
| "whether DOT could cite any of its 2025 flights" | memo ¶1 and §"Could the Department cite any of our flights?" | explicit **No**, with the "more than four" basis quoted |
| "which flights it should be watching" | memo §"Flights to watch" | 2 flights, named with flight numbers |
| "starting with the ones that carry the most passengers" | memo table, ranked | ATL-JFK 111,871 then ATL-EWR 98,799 |
| "one answer I can put my name to" | memo ¶1 | single unhedged answer |
| "Our replay standard governs the work and applies as written" | memo §"Does our replay return everything…" | admissibility test applied and reported |
| register: "one row per flight per month for every flight chronically delayed in at least one month" | `exposure_register.csv` | 582 rows, 168 markets, 333 chronic months |
| register columns, exact list and order | `exposure_register.csv` header | verified identical, in order |
| memo: "put the year at the top in one sentence" | memo ¶1 | one sentence |
| memo: "the associate's sheet counts 337" | memo ¶2 | 337 stated and interpreted |
| memo: "whether DOT could cite any … and if so which" | memo §2 | No; no list needed |
| memo: "flights to watch in order of passengers, with the passengers behind each rank" | memo table | both figures printed |
| memo: "how many more late arrivals in the following month would have made it citable" | memo table + per-flight ¶ | 13 and 2, with the operations and the threshold shown |
| memo: "whether your replay returns everything the standard checks it against, and list any miss" | memo §4 | "Yes, in full"; discloses FLL-BOS and MCO-LGA as extras and the 53 unreconciled BTS rows |
| memo: "take the associate's sheet and the dashboard list through to the flights each would have us report" | memo §5 | associate → 0 citable; dashboard → 4 flights, named |
| memo: "say how far each is from yours" | memo §5 | associate agrees on the answer, differs on the top entry and unit; dashboard is 4 flights off in the wrong direction |
| memo: "where the flight at the top of the associate's sheet stands on your replay" | memo §5 | ATL-JFK 4818 is a watch flight, 4-month run, needs 13 more |
| timeline: "flights by month" | `chronic_delay_timeline.png` | 26 flight rows × 12 months |
| timeline: "chronic months shaded" | same | red cells, legend |
| timeline: "streaks that came closest to the line marked" | same | both 4-month runs boxed and labelled |
| "Percents to one decimal place" | all three | register regex-checked; memo and chart formatted |
| "counts and passengers as whole numbers" | memo, register | verified |
| "months as YYYY-MM" | all three | register regex-checked |

## 6. What I would still look at

1. **Only one trap manufactures a false YES on the headline answer besides ArrDel15** —
   averaged flight-number rates. The rest of the pressure is on the watch list, the
   passenger ranking and the near-miss counts. That is by design for a NO answer, but it
   means a model that answers "none" and stops gets P1 right by luck. The memo's other
   clauses are what separate them.
2. **P7 did not pass.** The standard's BTS clause is gone and the memo discloses the
   284/337 reconciliation honestly. If you would rather the standard not mention published
   tabulations at all, that is a two-line edit to `make_standard.py`.
3. **The control's two extras** (FLL-BOS, MCO-LGA) are real and disclosed. A strict grader
   could read "returns every flight the order cites" as also forbidding extras; the
   standard deliberately says a settlement is not an exhaustive audit, and the memo says so.
4. **"Halvorson Aviation Group" exists.** Different spelling and different name from
   Halvorsen Aviation Advisory, and nothing in the package implies a real firm, but you
   chose the name so you should know the neighbour is there.

## 7. How to re-run

```
.venv/bin/python test_cluster.py        # fast clustering == reference, exit 0
.venv/bin/python control_b6.py 2022-06:2023-11
.venv/bin/python gate_2025.py           # all-carrier determinism and trap table
.venv/bin/python pin_gate.py            # pin sensitivity
.venv/bin/python bts_lists.py           # gate P7
.venv/bin/python build_package.py && .venv/bin/python make_standard.py \
  && .venv/bin/python make_assoc.py && .venv/bin/python make_dashboard.py
.venv/bin/python make_goldens.py && .venv/bin/python make_memo.py
.venv/bin/python make_zip.py
.venv/bin/python verify_filter.py       # filters kept the right bytes
.venv/bin/python verify_zip.py          # archive vs its own provenance
.venv/bin/python verify_independent.py  # every pin, independent code
```
