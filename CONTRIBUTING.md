# Contributing

Thanks for your interest in improving this dataset.

## Ways to help

- **Found a data issue?** (gap, bad print, timestamp anomaly) — open an issue
  and mention the week file (`XAUUSD_2025_wNN.csv.gz`) and a sample timestamp.
- **Want another instrument or year?** — the downloader scripts are generic;
  open a feature request or fork and go. For 2026 data see the companion
  repository [xauusd-tick-data-2026](https://github.com/Touhid-HZ/xauusd-tick-data-2026).
- **Bug fixes to scripts** — PRs welcome. Keep scripts dependency-light
  (requests / stdlib for the downloader; pandas + matplotlib only for
  analysis/build steps).

## Rebuilding the data yourself

```bash
pip install requests
python scripts/download_weeks_node.py --from 2025-01-01 --to 2026-01-01 \
    --work-dir ./work          # needs Node.js (npx dukascopy-node)
python scripts/build_daily_ohlcv.py
python scripts/make_chart.py
python scripts/verify_data.py
```

## Data conventions (please keep)

- One gzip CSV per 7-day chunk anchored to January 1 of the year
  (w01 = Jan 1-7, ..., w53 = the final day(s) of 2025).
- UTC timestamps, ISO format, millisecond precision, sorted.
- Never edit raw week files — regenerate them from source instead.
