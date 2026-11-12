#!/usr/bin/env python3
"""
Merge the weekly .csv.gz tick files into ONE plain CSV for MetaTrader 5.

MetaTrader cannot read gzip, so this produces an uncompressed CSV
(MQL5-friendly, same schema) named XAUUSD_ALL.csv by default.
Expected output size: ~3.5 GB per year — make sure you have room,
or pass --year / --weeks to merge a subset.

Usage (from repo root):
    python scripts/metatrader/prepare_csv.py                     # all years
    python scripts/metatrader/prepare_csv.py --year 2025         # one year
    python scripts/metatrader/prepare_csv.py --year 2025 --weeks w01 w02
"""

import argparse
import glob
import gzip
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TICK_DIR = os.path.join(REPO, "data", "tick")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default=None,
                    help="only merge this year (e.g. 2025); default: all years")
    ap.add_argument("--weeks", nargs="*", default=None,
                    help="week ids to merge, e.g. w01 w02 (requires --year)")
    ap.add_argument("--out", default=None,
                    help="output file name (default: XAUUSD_ALL.csv or "
                         "XAUUSD_<year>_ALL.csv)")
    args = ap.parse_args()

    if args.weeks and not args.year:
        raise SystemExit("--weeks requires --year (week ids repeat across years)")
    if args.weeks:
        files = [os.path.join(TICK_DIR, f"XAUUSD_{args.year}_{w}.csv.gz")
                 for w in args.weeks]
    elif args.year:
        files = sorted(glob.glob(
            os.path.join(TICK_DIR, f"XAUUSD_{args.year}_w*.csv.gz")))
    else:
        files = sorted(glob.glob(
            os.path.join(TICK_DIR, "XAUUSD_20??_w*.csv.gz")))
    files = [f for f in files if os.path.exists(f)]
    if not files:
        raise SystemExit("no tick files found")

    out_name = args.out or (f"XAUUSD_{args.year}_ALL.csv" if args.year
                            else "XAUUSD_ALL.csv")
    out_path = os.path.join(os.getcwd(), out_name)
    n = 0
    with open(out_path, "w", newline="\n") as fout:
        fout.write("timestamp,ask,bid,ask_volume,bid_volume\n")
        for path in files:
            with gzip.open(path, "rt") as fin:
                fin.readline()                  # skip the per-file header
                for line in fin:
                    fout.write(line)
                    n += 1
            print(f"merged {os.path.basename(path)} (total {n:,} ticks)")
    size_gb = os.path.getsize(out_path) / 1e9
    print(f"\nwrote {out_path}: {n:,} ticks, {size_gb:.2f} GB")
    print("next: copy it to  <MT5 data folder>\\MQL5\\Files\\  and run "
          "ImportXAUUSDTicks.mq5")


if __name__ == "__main__":
    main()
