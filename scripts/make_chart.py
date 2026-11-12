#!/usr/bin/env python3
"""
Render one overview chart per year: XAUUSD daily close (mid price).

Reads every data/daily/XAUUSD_YYYY_daily_ohlcv.csv and writes
charts/XAUUSD_YYYY_daily_close.png for each.

Usage:  python make_chart.py   (requires matplotlib, pandas)
"""

import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DAILY_GLOB = os.path.join(REPO, "data", "daily", "XAUUSD_*_daily_ohlcv.csv")
CHART_DIR = os.path.join(REPO, "charts")


def render(daily_path):
    year = os.path.basename(daily_path).split("_")[1]
    out = os.path.join(CHART_DIR, f"XAUUSD_{year}_daily_close.png")
    df = pd.read_csv(daily_path, parse_dates=["date"])
    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=150, constrained_layout=True)
    ax.plot(df["date"], df["close"], color="#C9A227", linewidth=1.6)
    ax.fill_between(df["date"], df["close"], df["close"].min(),
                    color="#C9A227", alpha=0.08)
    lo, hi = df["low"].min(), df["high"].max()
    ax.set_title(f"XAUUSD — Spot Gold {year}, Daily Close (UTC, mid price)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("USD per troy ounce")
    ax.set_xlabel(f"Data: Dukascopy tick-by-tick, {len(df):,} trading days — "
                  f"range ${lo:,.0f} to ${hi:,.0f}")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True, alpha=0.25)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    os.makedirs(CHART_DIR, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print("chart saved:", out)


def main():
    paths = sorted(glob.glob(DAILY_GLOB))
    if not paths:
        raise SystemExit("no daily OHLCV files found — run build_daily_ohlcv.py first")
    for p in paths:
        render(p)


if __name__ == "__main__":
    main()
