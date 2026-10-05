# Project Mark Task 1: Chronic Flight Delays

A start-to-finish plan for your first task, built on real U.S. DOT data and a real federal rule that DOT has already enforced with fines.

---

## 1. Where the data comes from (and why not the Stash)

**Stash starter kit** (unlock-the-stash.lovable.app): 111 packages across 15 domains. Each kit has 6 to 8 raw files (CSVs, overview.xlsx, data_dictionary.json with provenance). You get one claim, it's final, and the kit alone doesn't meet the bar: you still have to add files, come up with the decision, and find an honest trap in data you didn't pick. That's fine for a later task but slow for your first.

**Source it yourself (recommended).** U.S. federal data is public domain (17 U.S.C. 105), so licensing is easy. The strongest tasks pair a large raw table with a governing rule that ships inside the package, and that's exactly what this package does.

## 2. The task in one paragraph

**Domain:** Supply Chain & Logistics (air transport). **Objective:** Anomaly Detection / rule compliance. **Prompt shape:** *rule replayed on history* + *ranked list* + *drill-down to one leaf*.

Under 14 CFR 399.81, a flight is "chronically delayed" in a month if it operated at least 10 times and arrived more than 30 minutes late (cancellations count as late) more than 50% of the time. Holding one out for **more than four** consecutive months is an unfair and deceptive practice. In December 2024 DOT fined JetBlue $2M under this rule (the first fine ever) and in January 2025 sued Southwest. A carrier's compliance lead wants to know which of their 2025 flights crossed the line and must be retimed. There is exactly one right answer once the rule is applied correctly to the BTS records.

## 3. The honest traps (all real features of the data and rule, nothing planted)

| Trap | What the obvious approach does | What the rule requires | Measured trap it maps to |
|---|---|---|---|
| Unit of analysis | Groups by flight number | A "flight" is all of a carrier's flights in one O-D market whose scheduled departure is within 30 min of the most frequent departure time (stated in the JetBlue order), so several flight numbers can be one flight | Counts file rows instead of the real unit (11) |
| Ready-made late flag | Uses BTS `ArrDel15` | Threshold is >30 min, and `ArrDel15` is blank for cancellations | Uses ready-made measure (5) |
| Cancellations | `ArrDelay > 30` silently treats cancelled rows (blank delay) as on time, or drops them | Cancellations count as late and count as operations | Silent row drop / takes population a filter suggests |
| Streak length | "Four consecutive months" | *More than* four, so 5+ | Small shortcuts flip a thin margin |
| Control check | Never checks the method against a known case | The JetBlue 2023 months reproduce the flights DOT named | Never tests reading against the control (7) |

Diversions: BTS has `DivReachedDest` and `DivArrDelay`. The script counts a diversion as late unless it reached the destination 30 min late or less. Before you lock the carrier, check that this choice doesn't change the answer (if it does, pick another carrier so the task stays deterministic).

## 4. The input package (target: 23 files, 3 formats, all public domain)

| # | File | Source | Notes |
|---|---|---|---|
| 1 to 12 | `ontime_<CARRIER>_2025_01.csv` … `_12.csv` | BTS Reporting Carrier On-Time Performance, PREZIP: `https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_<M>.zip` | Filter each month to your carrier, keep **all** columns. Each file is 10k+ rows for any mid-size carrier. |
| 13 to 19 | `ontime_B6_2023_05.csv` … `_11.csv` | Same PREZIP pattern, 2023 | The months DOT used for JetBlue; this is the control. |
| 20 | `readme.html` | Inside every PREZIP zip | BTS field definitions (the only place `ArrDel15`, `DivArrDelay` are defined). |
| 21 | `14_CFR_399.81.pdf` | eCFR: https://www.ecfr.gov/current/title-14/section-399.81 (print to PDF) | The governing rule. |
| 22 | `DOT_JetBlue_Order_2024-12-21.pdf` | https://www.transportation.gov/sites/dot.gov/files/2025-01/JetBlue%20Airways%20Order%20-%202024-12-21.pdf | The 30-minute window definition and the four flights DOT cited. |
| 23 | `t100_domestic_segment_2025.csv` | TranStats > T-100 Domestic Segment (U.S. Carriers), Download page, year 2025, all months | Passengers by carrier, O-D, month. Joined to the flagged markets for the passenger ask. |

Record in a provenance sheet for each file: source URL, pull date, license ("U.S. Government work, public domain"), and for files 1 to 19 the one-line transform ("filtered PREZIP to Reporting_Airline = X, no other changes"). Formats: CSV, PDF, HTML.

**Why every file is necessary:** each 2025 month can break or extend a streak; the 2023 months are the control the memo must reproduce; the reg and order define the rule and the unit; the readme defines the fields; T-100 answers the passenger ask.

**Join:** the fix order joins the flagged flights to T-100 on carrier, origin, destination and month (BTS `Reporting_Airline` = T-100 `UNIQUE_CARRIER`), so the recommendation itself needs two tables.

## 5. Draft prompt (~1,350 characters; fill in the carrier after step 3)

> I run regulatory compliance at [CARRIER]. DOT has started fining carriers under the chronic-delay rule, and before the next schedule filing our general counsel wants to know which of our flights DOT could cite for 2025, and the order we should fix them in, starting with the ones that put the most passengers on those markets. Everything I could pull is in the folder: our BTS on-time files for each month of 2025, the BTS files for the JetBlue months DOT used in its order, the reg, the JetBlue order itself, and the 2025 T-100 segment data.
>
> I need one answer, not a menu of interpretations: are we exposed, and if so, exactly which flights, in what order?
>
> Please send back three things. First, a CSV exposure register with one row per flight per month for every flight that was chronically delayed in at least one month of 2025, showing operations, late arrivals, percent late and the running streak, with the flights DOT could cite clearly marked. Second, a PNG I can put in front of the GC showing those flights across the year, making it obvious where each one crosses the line. Third, a short memo as a PDF that leads with the recommendation, shows your approach reproduces the JetBlue flights DOT cited before you apply it to us, gives the passenger numbers behind the fix order, and names the flight that came closest to the line without crossing it and how many more late arrivals it would have taken to cross.

**Audit changes (2026-10-07):** "retime" became "which flights DOT could cite, in fix order" (a flight that crossed the line and then recovered was ambiguous under "retime"); the fix order is ranked by T-100 passengers, so the main recommendation now needs the T-100 join; the near-miss ask is now a count of late arrivals, which has one exact answer.

Check against the handbook: one committed decision ✓; vague on method, precise on answer ✓; doesn't name the trap or the decisive field ✓; 3 deliverables with multi-part asks ✓; everything needed is in the package ✓.

## 6. Steps, in order

**Step 1. Get the code and data running (30 min).** On your laptop: `pip install pandas`, then download `scan_chronic.py` from this project's files. The cloud session I run in can't reach transtats.bts.gov, so this part runs on your machine (or see the note at the end).

**Step 2. Validate on JetBlue 2023 (15 min).**
`python scan_chronic.py --months 2023-05:2023-11 --carriers B6`
Expected: FLL-JFK (DOT's flight 1802), MCO-JFK (384) and FLL-BDL (460) flagged. If those three come out, the method matches DOT. If not, send me the output before going further.

**Step 3. Pick the target carrier (30 min).**
`python scan_chronic.py --months 2025-01:2025-12 --carriers all`
It prints, per carrier, the violating flights under the rule, how many of the five shortcuts (TRAPS) change the answer, and a DETERMINISM line. Pick a carrier with **2 to 6 violating flights**, **3+ TRAPS that change the answer** (ideally flight-number and ArrDel15 both), **DETERMINISM: clean** (diversion handling, whether cancellations count as "operated", month-linking, airport vs city market, streaks cut off at January or December, tied or midnight departure times all leave the answer unchanged), and **exactly one near-miss** run of 4 months. Also check that no two flagged flights share a market (the T-100 passenger ranking would tie). Prefer a mid-size carrier (Frontier, Spirit, Alaska, Allegiant, JetBlue, Sun Country) so the zip stays small. If JetBlue itself qualifies, use it; "did we repeat it after the order?" is the best story. Paste the output here and I'll help you choose.

**Step 4. Build the package (1 hr).** Filter the 19 monthly files to the carrier, grab readme.html from any zip, print the reg to PDF, download the order, pull T-100 2025. Fill the provenance sheet and put it in the zip as `provenance.csv` (source URL, pull date, license, transform per file); the filtered CSVs are derived files, and a derived file without provenance is a blocking rejection. Zip it as `inputs.zip`.

**Step 5. Finalize the prompt (15 min).** Fill in the carrier, re-read it against the 5 prompt rules, keep it under 2,500 characters.

**Step 6. Build the golden deliverables (2 hrs).** Exactly the three files the prompt asks for:
- `exposure_register.csv`: carrier, origin, dest, modal scheduled departure, flight numbers in the cluster, month, operations, late arrivals (>30 min incl. cancellations), percent late, chronic Y/N, streak, over-the-line Y/N. The script's `chronic_streaks_rule.csv` is your starting point.
- `chronic_delay_timeline.png`: flights × months grid, chronic months shaded, month 5 of each streak marked as the violation point.
- `exposure_memo.pdf`, 1 to 2 pages, written like a compliance memo: recommendation in the first two sentences naming what it rejects; JetBlue reproduction (3 of 3 matched); the 2025 list in fix order with the T-100 passengers behind each rank; the near-miss flight and the exact number of extra late arrivals that would have tipped it; one paragraph on the traps refused, stated as decisions ("we grouped by market and departure window, not flight number, because…"); a closing line on why no other list survives.
Use an LLM to draft if you like, then edit so it reads like real work. One set of numbers across all three files.

**Step 7. Upload and read the rubric (30 min).** Paste the prompt in the box, upload `inputs.zip`, add the golden files. Read the generated rubric; don't edit it to chase the score.

**Step 8. Run the models and check the bar.** The two platform runs must average **under 50%** with at least one clearly stumped. Aim lower than 50% since regrading happens. If models pass too easily, the fix is in the data, not the wording: pick a carrier where more shortcuts disagree, or a near-miss flight that sits right on 50%.

**Step 9. Clear Readiness and submit.** Run the QC list (no TODOs, no disclaimers, every ask answered, numbers consistent), then submit. Review comes back within 24 hours; revisions are unlimited.

---

**Note on downloads:** this project runs on a built-in cloud environment with no settings, and its network policy blocks transtats.bts.gov and ecfr.gov. If you add a cloud environment with those hosts allowed (Project settings > Cloud environment > Add cloud environment > Network access: Custom), I can do steps 2 to 4 and 6 myself. Docs: https://code.claude.com/docs/en/cloud-environments#network-access

---

## 7. Rule audit (2026-10-07)

| Rule | Status | Note |
|---|---|---|
| 10+ files, 3+ formats, a 10k+ row table | Pass | 23 files; CSV, PDF, HTML; each monthly file is 10k+ rows for a mid-size carrier |
| Recommendation needs a 2+ table join | **Fixed** | Was only met by the passenger side ask. The fix order is now ranked by T-100 passengers, so the main answer needs the join |
| Provenance (URL, pull date, license, transform) | **Fixed** | `provenance.csv` now goes inside the zip; the filtered CSVs are derived files |
| Real, license-clean, no AI-made source files | Pass | All U.S. Government, public domain |
| No padding | Risk | The seven 2023 control months only serve the reproduction ask. Defensible, but the most likely place for a reviewer comment |
| Definitions in-package | Pass | Reg, order and BTS readme |
| Prompt: one decision, natural prose, under 2,500 characters, no method or trap leak | **Fixed** | "Which flights to retime" was ambiguous for a flight that crossed and then recovered; it now asks which flights DOT could cite, in fix order |
| 1 to 3 deliverables, multi-faceted asks | Pass | CSV + PNG + PDF memo |
| Golden: recommendation first, names what it rejects, one set of numbers | Pass (plan) | Built in step 6 |
| 25+ criteria from the prompt's structure | Likely pass | Register cells, ranking, control, near-miss count, chart |
| Honest traps only | Pass | Every trap comes from the rule text or the BTS field design |
| Determinism (no author-chosen cutoffs) | **Fixed, verify** | Added checks for diversions, cancellations as "operated", month linking, airport vs city market, streaks cut off at the window edges, tied or midnight departures, unique near-miss. Pick only a carrier that passes all of them |
| Under 50% on the two model runs | Unknown | Only measurable after upload |
