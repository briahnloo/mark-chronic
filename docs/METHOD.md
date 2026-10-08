# Method

How `scan_chronic.py` reads 14 CFR 399.81, and how each reading was settled.

## The rule as replayed

- **A flight** is all of a carrier's operations in one origin-destination market whose
  scheduled departure is within 30 minutes of the most frequent scheduled departure time.
  Several flight numbers can be one flight. This is the unit DOT applied in the December
  2024 JetBlue order.
- **Late** means arriving more than 30 minutes late. Cancellations count as late and count
  as operations. A diverted flight is late unless it reached its destination within 30
  minutes of schedule.
- **Chronically delayed in a month** means operated at least 10 times that month and late
  on more than 50% of them.
- **A violation** is chronic delay for more than four consecutive months, so five or more.

## How the readings were settled

The method was fixed by reproducing DOT's own findings, not by tuning. `control_b6.py`
replays the 18 months the JetBlue order covers and must return all four cited flights with
the order's months and footnote 6's operation counts (31, 30, 27, 57). It does, and also
finds two runs the order does not charge (FLL-BOS and MCO-LGA). A settlement covers what
DOT chose to pursue, so those are reported as extras, not failures.

| Question | Settled by |
|---|---|
| Month-to-month linkage across a retime | `diag_460.py`, `diag_link.py`: flight 460's 45-minute retime between 2023-10 and 2023-11 |
| Whether a long run is a clustering artifact | `diag_bos.py`: FLL-BOS flight 170 |
| Airport pair or city pair | Both reported by the control; the rule's text says city-pair market |
| Fields the rule needs exist and where they are null | `check_fields.py` |
| The fast clustering matches the reference | `test_cluster.py`, 1.56M real rows plus synthetic edge cases |

## Traps

Readings that look reasonable and change the answer. `gate_2025.py` and `pin_gate.py`
measure each one against every pin:

- grouping by flight number instead of the 30-minute cluster
- using BTS's `ArrDel15` flag, which marks 15 minutes, not 30, and is blank for cancellations
- dropping cancellations, or counting them on time
- reading ">50%" as "at least 50%"
- counting four-month runs as violations
- averaging BTS's published per-flight-number percentages

`READY.md` section 2 has the measured effect of each one.

## BTS's published lists

BTS lists one flight number at one scheduled departure time, not the rule's cluster. The
best convention found reproduces 284 of BTS's 337 Frontier rows exactly. The other 53 differ
by one or two operations and can't be closed from published data, so the published lists are
not used as an admissibility control (`bts_lists.py`, `diag_bts*.py`).
