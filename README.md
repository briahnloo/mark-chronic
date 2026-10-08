# mark-chronic

A replay of DOT's chronically-delayed-flight rule, 14 CFR 399.81, on BTS on-time data, and
the task package built from it: could DOT cite any of Frontier's 2025 flights, and which
flights came close enough to watch?

**Answer: no.** No Frontier flight was chronically delayed for more than four consecutive
months in 2025. Two flights reached four: ATL-JFK 4818 (2025-05 to 2025-08) and ATL-EWR
4602 (2025-04 to 2025-07). ATL-EWR 4602 finished two late arrivals short of a fifth month.

## Layout

| Path | What it is |
|---|---|
| `scan_chronic.py` | The 399.81 replay engine. Everything else imports it or checks it. |
| `control_b6.py`, `diag_*.py` | The JetBlue control and the diagnostics that settled the method |
| `gate_2025.py`, `pin_gate.py`, `t100_robust.py` | Carrier selection, pin sensitivity, passenger-ranking robustness |
| `bts_lists.py`, `assoc_*.py` | Parsing BTS's published lists and the two readings of them |
| `build_package.py`, `make_*.py` | Builders for the package inputs and the three deliverables |
| `verify_*.py`, `diff_numbers.py`, `audit_package.py`, `grep_firm.py` | Checks run before anything ships |
| `sources/` | The rule, DOT's JetBlue order and BTS's twelve 2025 chronic-delay lists |
| `scan_*/` | Streak summaries from the 2022-2025 all-carrier scans |
| `submission/` | The final register, memo and timeline chart |
| `archive/` | The pre-final deliverables, mock rubric and simulation output |
| `docs/` | Sources, method and pipeline notes |
| `READY.md` | Status, every pin and where it is stated, and the checks behind them |

## Setup

```
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The raw BTS data (about 1.5 GB) is not in the repository. `docs/SOURCES.md` lists where
each ignored file comes from, and `docs/PIPELINE.md` gives the order to rebuild everything.

All source data is U.S. Government work in the public domain (17 U.S.C. 105).
