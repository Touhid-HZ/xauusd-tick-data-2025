# Data Dictionary — XAUUSD Tick Data 2025

This document describes every field in the tick dataset. All files share the
exact same schema, so any parser you write works across the whole year.

## Tick files — `data/tick/XAUUSD_YYYY_wNN.csv.gz`

One gzip-compressed CSV file per week (`w01` covers the first 7 days of the
year, e.g. 2025-01-01 … 2025-01-07; `w53` may be shorter). Every row is **one
quote update (tick)** from Dukascopy Bank SA's spot gold feed. This repository
contains the complete 2025 set: `XAUUSD_2025_w*` — 53 weekly files covering
the full calendar year (w01 = Jan 1-7, …, w53 = Dec 31).

Header row (identical in every file):

```csv
timestamp,ask,bid,ask_volume,bid_volume
```

| Column       | Type   | Description                                                                 | Example                  |
|--------------|--------|-----------------------------------------------------------------------------|--------------------------|
| `timestamp`  | string | Quote time, **UTC (GMT)**, millisecond precision, `YYYY-MM-DD HH:MM:SS.mmm` | `2025-01-01 23:00:00.455` |
| `ask`        | float  | Best ask (offer) price in **USD per troy ounce**, 3 decimals                | `2626.592`               |
| `bid`        | float  | Best bid price in **USD per troy ounce**, 3 decimals                        | `2625.098`               |
| `ask_volume` | float  | Ask-side volume in **millions of units** (Dukascopy convention)             | `0.000450` (= 450 units) |
| `bid_volume` | float  | Bid-side volume in **millions of units** (Dukascopy convention)             | `0.000450` (= 450 units) |

Notes:

- `ask >= bid` holds for every row (no crossed quotes). The instantaneous
  spread is `ask - bid`.
- Timestamps are strictly chronological within each file (sorted).
- Multiple ticks can share the same millisecond — that is normal for a busy
  feed, not a duplication bug.
- Volume units: Dukascopy stores tick volumes as float32 values in millions
  of units, so `0.000120` means 120 units of the base instrument. Treat
  volumes as indicative feed activity, not exchange-traded contracts.
- Rows are raw feed snapshots: no interpolation, no deduplication, no
  gap-filling, no session filtering.

## Week sidecars — `data/tick/XAUUSD_YYYY_wNN.meta.json`

Machine-readable per-week statistics (used by the update pipeline, handy for
agents and notebooks):

| Key                | Meaning                                            |
|--------------------|----------------------------------------------------|
| `rows`             | Number of ticks in the week                        |
| `compressed_bytes` | `.csv.gz` file size                                |
| `first_tick_utc` / `last_tick_utc` | First/last tick timestamp (UTC)  |
| `trading_days`     | Number of days that produced at least one tick     |
| `price_high` / `price_low` | Extreme mid prices of the week (USD/oz)   |
| `days[]`           | Per-day aggregates: `date`, `ticks`, `open`, `high`, `low`, `close` (mid price), `ask_volume_m`, `bid_volume_m`, `avg_spread` |

## Daily bars — `data/daily/XAUUSD_YYYY_daily_ohlcv.csv` (one per year)

Daily aggregates derived from the tick files (mid price = `(ask + bid) / 2`):

| Column         | Type  | Description                                   |
|----------------|-------|-----------------------------------------------|
| `date`         | string| UTC date, `YYYY-MM-DD`                        |
| `open`         | float | First mid price of the day                    |
| `high`         | float | Highest mid price of the day                  |
| `low`          | float | Lowest mid price of the day                   |
| `close`        | float | Last mid price of the day                     |
| `ticks`        | int   | Number of ticks that day                      |
| `ask_volume_m` | float | Sum of ask volumes (millions of units)        |
| `bid_volume_m` | float | Sum of bid volumes (millions of units)        |
| `avg_spread`   | float | Average ask-bid spread in USD                 |

## Status file — `DATA_STATUS.json` (repo root)

Always-current machine-readable summary: coverage window, total tick count,
per-file inventory, price extremes and update policy. Ideal entry point for
automated pipelines and AI agents.

## Source & provenance

- Source: Dukascopy Bank SA public historical data feed
  (`https://datafeed.dukascopy.com`), hourly `.bi5` tick archives.
- Decoding: each record is a 20-byte big-endian struct
  `>IIIff` = `ms_offset_from_hour_start, ask_x1000, bid_x1000, ask_vol_m, bid_vol_m`.
- The decoder was cross-validated row-by-row against the popular
  [dukascopy-node](https://github.com/LeoEichler/dukascopy-node) exporter
  (11,708 / 11,708 rows identical, including timestamps, prices and volumes).
