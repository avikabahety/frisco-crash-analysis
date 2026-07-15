#!/usr/bin/env python3
"""Check how complete the recent months of the CRIS extract are.

A crash enters CRIS only after an officer files a CR-3 and TxDOT processes it, so
the final months of any extract are under-reported. Because the analysis compares
winter against summer, and an extract taken mid-year cuts summer off closer to the
present than winter, an incomplete tail biases the winter/summer ratio upward.

This script estimates where reporting has settled, by comparing each of the most
recent months against the same calendar month in prior years. A recent month that
sits well below its historical level is still filling in.

It does not change any output. It exists to justify (or revise) config.ANALYSIS_END.

Run:  python check_completeness.py
"""

import numpy as np
import pandas as pd

import config as C
from src.data import _header_row

pd.set_option("display.width", 150)

raw = pd.read_csv(C.CRASH_FILE, dtype=str,
                  skiprows=_header_row(C.CRASH_FILE), low_memory=False)
date = pd.to_datetime(raw[C.COLUMNS["date"]], errors="coerce", format="mixed")
date = date.dropna()

ym = date.dt.to_period("M")
monthly = ym.value_counts().sort_index()
last = monthly.index.max()

print(f"Extract spans {monthly.index.min()} to {last}")
print(f"Total crashes with a parseable date: {len(date):,}\n")

# Expected level for a calendar month = median of that month in earlier years.
by_month = {}
for period, count in monthly.items():
    by_month.setdefault(period.month, []).append((period.year, count))

print("Most recent 8 months vs the historical median for that calendar month")
print(f"  {'month':<10}{'crashes':>9}{'hist median':>13}{'% of usual':>12}   completeness")
recent = monthly.tail(8)
first_incomplete = None
for period, count in recent.items():
    hist = [c for (y, c) in by_month[period.month] if y < period.year]
    if not hist:
        print(f"  {str(period):<10}{count:>9}{'n/a':>13}{'n/a':>12}")
        continue
    med = float(np.median(hist))
    pct = count / med * 100 if med else np.nan
    bar = "#" * int(min(pct, 120) / 10)
    flag = "" if pct >= 90 else ("  <- likely still reporting" if pct >= 60
                                 else "  <- clearly incomplete")
    print(f"  {str(period):<10}{count:>9}{med:>13.0f}{pct:>11.0f}%   {bar}{flag}")
    if pct < 90 and first_incomplete is None:
        first_incomplete = period

print()
if first_incomplete is not None:
    settled_month = (first_incomplete - 1)
    end = settled_month.to_timestamp("M") + pd.offsets.MonthEnd(0)
    print(f"Reporting appears to drop off from {first_incomplete}.")
    print(f"Last month that looks complete: {settled_month}.")
    cut = pd.Timestamp(C.ANALYSIS_END)
    print(f"\nconfig.ANALYSIS_END is currently {C.ANALYSIS_END}.")
    if cut <= end:
        print("That cutoff sits at or before the last complete month: safe.")
    else:
        print(f"That cutoff is LATER than the last complete month ({settled_month}).")
        print("Consider moving ANALYSIS_END back to a complete calendar year.")
else:
    print("No recent month falls materially below its historical level.")
    print(f"config.ANALYSIS_END = {C.ANALYSIS_END} is safe, and may even be conservative.")

# What the cutoff currently discards.
if C.ANALYSIS_END:
    cut = pd.Timestamp(C.ANALYSIS_END)
    dropped = int((date > cut).sum())
    print(f"\nThe cutoff currently excludes {dropped:,} crashes "
          f"({dropped / len(date) * 100:.1f}% of dated records) after {C.ANALYSIS_END}.")
