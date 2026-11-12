#!/usr/bin/env python3
"""
Build per-year daily OHLCV files and DATA_STATUS.json from weekly meta sidecars.

Reads every data/tick/XAUUSD_YYYY_wNN.meta.json, groups the weeks by year, and
writes:

  data/daily/XAUUSD_YYYY_daily_ohlcv.csv   — one row per day with ticks
  DATA_STATUS.json                          — machine-readable summary with
                                              overall totals + per-year sections

Usage:  python build_daily_ohlcv.py
"""

import datetime as dt
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TICK_DIR = os.path.join(REPO, "data", "tick")
DAILY_DIR = os.path.join(REPO, "data", "daily")
STATUS_PATH = os.path.join(REPO, "DATA_STATUS.json")

SCHEMA = {
    "timestamp": "string, UTC, 'YYYY-MM-DD HH:MM:SS.mmm' (millisecond precision)",
    "ask": "float, USD per troy ounce, 3 decimals",
    "bid": "float, USD per troy ounce, 3 decimals",
    "ask_volume": "float, millions of units (Dukascopy convention)",
    "bid_volume": "float, millions of units (Dukascopy convention)",
}


def load_metas():
    out = []
    for p in sorted(glob.glob(os.path.join(TICK_DIR, "*.meta.json"))):
        with open(p) as f:
            out.append(json.load(f))
    return out


def file_entry(m):
    return {
        "file": m["file"],
        "week": m["week_index"],
        "date_from": m["date_from"],
        "date_to_exclusive": m["date_to_exclusive"],
        "rows": m["rows"],
        "compressed_bytes": m["compressed_bytes"],
        "first_tick_utc": m["first_tick_utc"],
        "last_tick_utc": m["last_tick_utc"],
    }


def year_summary(year, metas, days):
    total_rows = sum(m["rows"] for m in metas)
    total_bytes = sum(m["compressed_bytes"] for m in metas)
    weekdays = sum(1 for d in days if dt.date.fromisoformat(d).weekday() < 5)
    sundays = sum(1 for d in days if dt.date.fromisoformat(d).weekday() == 6)
    return {
        "coverage": {
            "from": metas[0]["date_from"],
            "to_exclusive": metas[-1]["date_to_exclusive"],
            "first_tick_utc": metas[0]["first_tick_utc"],
            "last_tick_utc": metas[-1]["last_tick_utc"],
        },
        "totals": {
            "ticks": total_rows,
            "days_with_ticks": len(days),
            "weekdays_with_ticks": weekdays,
            "sundays_with_ticks": sundays,
            "weekly_files": len(metas),
            "compressed_bytes": total_bytes,
            "compressed_mb": round(total_bytes / 1e6, 1),
        },
        "price_range_usd_per_oz": {
            "low": min(m["price_low"] for m in metas),
            "high": max(m["price_high"] for m in metas),
        },
        "daily_ohlcv": f"data/daily/XAUUSD_{year}_daily_ohlcv.csv",
        "files": [file_entry(m) for m in metas],
    }


def main():
    metas = load_metas()
    if not metas:
        raise SystemExit("no meta files found — run the downloader first")

    by_year = {}
    for m in metas:
        by_year.setdefault(m["date_from"][:4], []).append(m)

    all_days = {}
    years = {}
    for year in sorted(by_year):
        ym = by_year[year]
        days = {}
        for m in ym:
            for d in m["days"]:
                days[d["date"]] = d          # dates are unique across weeks
        os.makedirs(DAILY_DIR, exist_ok=True)
        out_path = os.path.join(DAILY_DIR, f"XAUUSD_{year}_daily_ohlcv.csv")
        with open(out_path, "w") as f:
            f.write("date,open,high,low,close,ticks,ask_volume_m,bid_volume_m,avg_spread\n")
            for date in sorted(days):
                d = days[date]
                f.write(f"{d['date']},{d['open']},{d['high']},{d['low']},{d['close']},"
                        f"{d['ticks']},{d['ask_volume_m']},{d['bid_volume_m']},"
                        f"{d['avg_spread']}\n")
        all_days.update(days)
        years[year] = year_summary(year, ym, days)
        print(f"{year}: {len(days):>3} days, {years[year]['totals']['ticks']:>12,} ticks"
              f" -> {out_path}")

    overall_ticks = sum(y["totals"]["ticks"] for y in years.values())
    overall_bytes = sum(y["totals"]["compressed_bytes"] for y in years.values())
    status = {
        "dataset": f"XAUUSD tick-by-tick historical data ({', '.join(sorted(years))}) — spot gold vs US dollar",
        "instrument": "XAUUSD (Spot Gold / US Dollar, OTC)",
        "source": "Dukascopy Bank SA public data feed (https://datafeed.dukascopy.com), decoded via dukascopy-node + custom decoder, cross-validated row-by-row",
        "timezone": "UTC (GMT)",
        "schema": SCHEMA,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "coverage": {
            "from": metas[0]["date_from"],
            "to_exclusive": metas[-1]["date_to_exclusive"],
            "first_tick_utc": metas[0]["first_tick_utc"],
            "last_tick_utc": metas[-1]["last_tick_utc"],
        },
        "totals": {
            "ticks": overall_ticks,
            "days_with_ticks": len(all_days),
            "weekdays_with_ticks": sum(
                1 for d in all_days if dt.date.fromisoformat(d).weekday() < 5),
            "sundays_with_ticks": sum(
                1 for d in all_days if dt.date.fromisoformat(d).weekday() == 6),
            "weekly_files": len(metas),
            "compressed_bytes": overall_bytes,
            "compressed_mb": round(overall_bytes / 1e6, 1),
        },
        "price_range_usd_per_oz": {
            "low": min(y["price_range_usd_per_oz"]["low"] for y in years.values()),
            "high": max(y["price_range_usd_per_oz"]["high"] for y in years.values()),
        },
        "years": years,
        "update_policy": f"final — calendar year {', '.join(sorted(years))} is complete; the dataset is immutable",
        "license": "MIT (code and packaging); data belongs to its original source and is provided as-is for research/education",
    }
    with open(STATUS_PATH, "w") as f:
        json.dump(status, f, indent=1)
    print(f"status file : {STATUS_PATH}")
    print(f"ticks total : {overall_ticks:,} across {len(years)} years "
          f"({', '.join(years)})")
    print(f"size        : {overall_bytes / 1e6:.1f} MB gz")


if __name__ == "__main__":
    main()
