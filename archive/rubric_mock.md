# Mock rubric v2 — chronic delay task (Frontier 2025)

Built against prompt v3 and the three golden files, at the program's real weights:
recommendation and its critical parts 35%, instruction-following 7%, supplementary 58%.
No single criterion exceeds 20%.

**Kept outside `submission/` and outside `inputs.zip`.** This is my estimate of the
rubric, not the platform's.

Prompt v3 does not prescribe file names or CSV column names, so the instruction-following
block no longer tests them. It tests the three formats, the three precision rules, and
the ordering the client asked for.

31 criteria. Weights sum to 100 (35 + 7 + 58).

## A. The recommendation and its critical parts — 35%

| # | Criterion | Weight |
|---|---|---|
| A1 | States that DOT could cite **no** Frontier 2025 flight, up front and without hedging it into a maybe | 14 |
| A2 | The flights to watch are exactly two: ATL-JFK 4818 and ATL-EWR 4602, with no third added and neither omitted | 9 |
| A3 | Ranked by passengers, ATL-JFK first | 4 |
| A4 | Passenger figures 111,871 and 98,799 | 4 |
| A5 | Reports that the replay returns all four flights the JetBlue order cites, with the order's months | 4 |

## B. Instruction-following — 7%

| # | Criterion | Weight |
|---|---|---|
| B1 | Three deliverables in the formats asked: a PDF memo, a CSV register, a PNG chart | 2 |
| B2 | Percentages to one decimal place throughout | 2 |
| B3 | Counts and passengers as whole numbers | 1 |
| B4 | Months as YYYY-MM throughout | 2 |

## C. The supplementary asks — 58%

| # | Criterion | Weight |
|---|---|---|
| C1 | The memo gives the answer up front, in the opening sentence or two | 1 |
| C2 | Carries the figure 337 as the associate's count of Frontier flight-months on BTS's lists | 1 |
| C3 | ATL-JFK needed **13** more late arrivals in 2025-09 to tip over | 4 |
| C4 | ATL-EWR needed **2** more late arrivals in 2025-08 to tip over | 4 |
| C5 | ATL-JFK's four chronic months as 31/17, 30/20, 31/18, 31/17 operations and late arrivals | 4 |
| **C6** | **ATL-EWR's four chronic months as 30/20, 21/17, 30/18, 31/25 operations and late arrivals** | **5** |
| C7 | The closing month of each run: ATL-JFK 2025-09 at 30/3, ATL-EWR 2025-08 at 31/14 | 3 |
| C8 | States plainly that the replay holds up against what the standard tests it on | 2 |
| C9 | States that nothing is missed | 2 |
| C10 | Names FLL-BOS and MCO-LGA as flights the order did not charge, and does **not** present them as misses, discrepancies or errors | 3 |
| C11 | Gives the operation counts the order states and the replay reproduces: 31, 30, 27, 57 | 4 |
| C12 | Carries the associate's sheet through to the list it would have us report (no citable flight) | 1 |
| C13 | States the distance between the associate's sheet and the replay | 2 |
| C14 | Says where the top flight on the associate's sheet (ATL-JFK 4818, on five lists) actually lands: a four-month run, not citable, 13 short | 5 |
| C15 | Carries the dashboard export through to its own list and names its four flights (ATL-EWR, ATL-LGA, LAX-ATL, PHL-SJU) | 1 |
| C16 | States the distance between the dashboard list and the replay | 2 |
| **C17** | **The register identifies 333 chronically delayed flight-months across 168 markets in 2025** | **5** |
| C18 | Register covers every flight chronic in at least one month, one row per flight per month | 2 |
| C19 | Register operations and late arrivals are right on the chronic rows | 2 |
| C20 | Register's consecutive-month counter is right | 1 |
| C21 | Chart shows flights by month with the chronic months shaded | 2 |
| C22 | Chart marks the streaks that came closest to the line | 2 |

## Scoring notes

- A1 at 14% is the heaviest criterion. The answer "none" with nothing else earns 14.
- **C17 is the sharpest discriminator in the rubric.** 333 chronically delayed
  flight-months is produced by the correct method alone. Every method mistake gives a
  different total: flight-number unit 325, per-service window 312, city-pair 316,
  averaged rates 397, dropping cancellations 261, cancellations on time 225, ArrDel15
  678, ">=50%" 443. The memo states the figure and the register carries it, so a rubric
  built from the golden files would test it.
- **C5, C6 and C7 are the per-flight-month operation counts, 12% together.** C6 is the
  load-bearing one: ATL-EWR 2025-05 is 21 operations and 17 late under the rule's
  thirty-minute window, and 31 and 20 if the flight number is taken whole. ATL-JFK's four
  months happen to be identical under both units, so C5 does not discriminate on the unit
  and is weighted lower.
- C3, C4, C11 and C14 are the other control-dependent figures. None can be read off a
  single file in the archive.
- C10 rewards framing as well as fact: naming the two extras but calling them misses or
  discrepancies does not earn it.
