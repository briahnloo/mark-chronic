# Pipeline

Run from the repository root with the venv from the README. Steps are in dependency order.

## 1. Establish the method

```
.venv/bin/python test_cluster.py                                       # fast clustering == reference
.venv/bin/python control_b6.py 2022-06:2023-11                         # JetBlue control
.venv/bin/python scan_chronic.py --months 2025-01:2025-12 --carriers all   # writes scan_out/
```

`scan_chronic.py` downloads any missing month into `bts_raw/`. Its per-flight-month dump
`flight_month_rule.csv` is ignored; the `chronic_streaks_rule.csv` summary is kept.

## 2. Choose the carrier and check the pins

```
.venv/bin/python gate_2025.py      # all carriers, determinism variants and traps; writes cache_2025.parquet (~3 min)
.venv/bin/python pin_gate.py       # which pins each mistake moves
.venv/bin/python t100_robust.py    # passenger ranking under eight definitions
.venv/bin/python bts_lists.py      # gate P7 against BTS's published lists
```

## 3. Build the package and deliverables

```
.venv/bin/python build_package.py     # filtered inputs into package/
.venv/bin/python make_standard.py     # the replay standard
.venv/bin/python make_assoc.py        # the associate's working sheet
.venv/bin/python make_dashboard.py    # the dashboard export
.venv/bin/python make_goldens.py      # register, timeline chart, golden_facts.json
.venv/bin/python make_memo.py         # exposure_memo.pdf
.venv/bin/python make_zip.py          # provenance.csv and submission/inputs.zip
```

## 4. Verify before anything ships

| Check | What it proves |
|---|---|
| `verify_filter.py` | The filtered files hold exactly the carrier's rows, byte for byte |
| `verify_zip.py` | `inputs.zip` matches its own `provenance.csv` |
| `verify_independent.py` | Every pin, recomputed by code that imports nothing from the pipeline and reads only `inputs.zip` |
| `diff_numbers.py` | Any number stated in more than one deliverable agrees everywhere |
| `audit_package.py` | Every packaged file is needed, and what breaks without it |
| `grep_firm.py` | The old firm name appears nowhere, including inside xlsx, PDF and PNG |

`verify_independent.py` must print `ALL PINS REPRODUCED` and exit 0.
