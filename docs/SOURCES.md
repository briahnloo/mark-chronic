# Sources

Every input is U.S. Government work in the public domain. Large files are ignored by git and
refetched as below; small ones are committed under `sources/`.

## Ignored, refetch before running

| File | Source | How |
|---|---|---|
| `bts_raw/ontime_YYYY_MM.zip` (48 files, 2022-01 to 2025-12, ~1.3 GB) | BTS Reporting Carrier On-Time Performance PREZIPs, `https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip` | Automatic: `scan_chronic.load_month` downloads any month missing from `--datadir` |
| `sources/t100_domestic_segment_2025.csv` and the `T_T100D_SEGMENT_US_CARRIER_ONLY_*.zip` it came from | BTS T-100 Domestic Segment (U.S. Carriers), 2025, all months, `https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FIM` | Manual export with fields Year, Month, UniqueCarrier, Origin, Dest, Passengers, DepPerformed |
| `sources/bts_chronic/btscd_bundle.bin` | The twelve 2025 chronic-delay workbooks as one blob | Only needed to re-split; the workbooks themselves are committed |

## Committed

| File | Source | Note |
|---|---|---|
| `sources/CFR_14_399.81.pdf` | govinfo, official CFR 2025 edition, title 14 vol 4 | Ships in the package unmodified |
| `sources/DOT_JetBlue_Order_2024-12-21.pdf` | transportation.gov, DOT Order 2024-12-21 | Fetched through the browser; the site returns 403 to curl |
| `sources/ecfr_399_81.xml`, `.html` | eCFR | Working copies the thresholds were read from (`show_reg.py`) |
| `sources/order_text.txt` | Text extracted from the order PDF | Working copy |
| `sources/bts_chronic/btscd_*.xlsx` | `https://www.bts.gov/topics/chronically-delayed-flights` | Unmodified; sizes verified against the index page by `dedupe_bts.py` |

## Why the BTS lists came down as a bundle

bts.gov returns 403 to curl and Chrome blocks repeated automatic downloads from the site, so
the twelve workbooks were fetched in the page and concatenated into one blob with a length
index header. `split_bundle.py` slices it back apart without touching the bytes, and
`dedupe_bts.py` proves the result matches what BTS publishes.
