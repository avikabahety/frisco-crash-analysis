#!/usr/bin/env python3
"""Check a city's settings against its data, before the analysis is run.

Prints three things, for setting up cities/<city>_config.py:

  1. Recorded light condition by hour and season, at signalized intersections, and
     what that implies for the comparison, contrast and transition hours. Uses only
     light conditions, never crash outcomes, so the hours are fixed before the
     result is seen.
  2. How the fields the analysis searches are coded in this export: collision types,
     contributing factors, traffic control (including the flashing-yellow
     reference sample), light and surface condition, intersection type, agency.
  3. The most common street names, and route-numbered names, to spot roads that are
     recorded under both a route number and a local name (see STREET_ALIASES).

It does not change any output.

Run:  python check_setup.py --city plano
"""

import argparse

import pandas as pd

import config as C
from src.city import available_cities, use_city
from src.data import _header_row, load, normalise_street

p = argparse.ArgumentParser()
p.add_argument("--city", required=True, choices=available_cities())
use_city(p.parse_args().city)

pd.set_option("display.width", 150)
pd.set_option("display.max_rows", 200)

# An hour counts as light (or dark) in a season when at least this % of its crashes
# were recorded that way; otherwise it is mixed. A checking aid only: the hours the
# analysis uses are the ones set in the city's config.
SHARE = 90


def section(t):
    print("\n" + "=" * 86 + f"\n{t}\n" + "=" * 86)


def label(h):
    return f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"


raw = pd.read_csv(C.CRASH_FILE, dtype=str, skiprows=_header_row(C.CRASH_FILE),
                  low_memory=False)
df, funnel = load()
sig = df[df["signal"]]
print(f"{C.CITY_NAME}: {C.CRASH_FILE.name}")
print(f"  {len(raw):,} crashes in the export; {len(sig):,} at signalized intersections "
      f"on or before {C.ANALYSIS_END}")

# --------------------------------------------------------------------------
section("1. LIGHT CONDITION BY HOUR (signalized intersections)")
twilight = sig["light"].str.contains("DUSK|DAWN", na=False)


def season_class(g):
    day = g["daylight"].mean() * 100
    not_day = (g["dark"] | g["light"].str.contains("DUSK|DAWN", na=False)).mean() * 100
    if day >= SHARE:
        return day, not_day, "light"
    if not_day >= SHARE:
        return day, not_day, "dark"
    return day, not_day, "mixed"


rows, kind = [], {}
for h in range(5, 24):
    w = sig[sig["winter"] & (sig["hour"] == h)]
    s = sig[sig["summer"] & (sig["hour"] == h)]
    if len(w) < 20 or len(s) < 20:
        continue
    wd, wn, wc = season_class(w)
    sd, sn, sc = season_class(s)
    if "mixed" in (wc, sc):
        k = "mixed"
    elif wc == sc:
        k = f"{wc} in both"
    else:
        k = f"{wc} in winter, {sc} in summer"
    kind[h] = k
    rows.append({"hour": label(h), "winter n": len(w), "winter % daylight": round(wd),
                 "summer n": len(s), "summer % daylight": round(sd), "class": k})
print(pd.DataFrame(rows).to_string(index=False))
print(f"\n  light/dark = at least {SHARE}% of that season's crashes recorded that way")

print("\n  Configured hours vs. recorded light:")
checks = [("COMPARISON_HOUR", [C.COMPARISON_HOUR], "light in both"),
          ("CONTRAST_HOURS", C.CONTRAST_HOURS, "dark in winter, light in summer"),
          ("MIDDAY_HOURS", C.MIDDAY_HOURS, "light in both"),
          ("LATE_HOURS", C.LATE_HOURS, "dark in both")]
for name, hours, want in checks:
    for h in hours:
        got = kind.get(h, "too few crashes")
        print(f"    {'ok ' if got == want else 'CHECK'}  {name:<16} {label(h):>5}  "
              f"expected {want!r}, recorded {got!r}")
contrast = [h for h, k in kind.items() if k == "dark in winter, light in summer"]
light_before = [h for h, k in kind.items()
                if k == "light in both" and contrast and h < min(contrast)]
print(f"\n  Hours dark in winter and light in summer: {[label(h) for h in contrast]}")
if light_before:
    print(f"  Last hour light in both seasons before them: {label(max(light_before))}")
print(f"  Mixed hours (for TRANSITION_HOURS in the page file): "
      f"{[label(h) for h, k in kind.items() if k == 'mixed']}")

# --------------------------------------------------------------------------
section("2. HOW THE SEARCHED FIELDS ARE CODED (whole export)")


def counts(col, n=12):
    v = raw[C.COLUMNS[col]].fillna("(blank)").str.upper().str.strip()
    vc = v.value_counts()
    out = (vc.head(n) / len(v) * 100).round(1)
    print(f"\n  {C.COLUMNS[col]}  ({vc.size} distinct values; top {min(n, vc.size)}, % of crashes)")
    for val, pct in out.items():
        print(f"    {pct:5.1f}%  {val[:90]}")


for col in ["intersection", "control", "collision", "light", "surface"]:
    counts(col)

print("\n  Collision patterns the analysis searches for (signalized intersections):")
for name, flag in [("left-turn", "is_left"), ("right-turn", "is_right"),
                   ("right-angle", "is_angle"), ("rear-end", "is_rear")]:
    print(f"    {name:<12} {sig[flag].sum():>6,}  ({sig[flag].mean() * 100:.1f}%)")

left = sig[sig["is_left"]]
print("\n  Contributing factors on signalized left-turn crashes:")
print(f"    'failed to yield - turning left'   {left['failed_to_yield'].mean() * 100:5.1f}%")
print(f"    'disregard stop and go signal'     {left['ran_red'].mean() * 100:5.1f}%")
print(f"    impairment codes                   {left['impaired'].mean() * 100:5.1f}%")

fy = df[df["flashing_yellow"]]
print(f"\n  Flashing-yellow reference sample: {len(fy)} crashes, "
      f"{int(fy['is_left'].sum())} of them left-turn")
if fy["is_left"].sum():
    print(f"    of which cite 'failed to yield - turning left': "
          f"{fy.loc[fy['is_left'], 'failed_to_yield'].mean() * 100:.0f}%")

agency = raw["Agency"].fillna("(blank)").value_counts(normalize=True).mul(100).round(1)
print("\n  Reporting agency (% of crashes):")
for val, pct in agency.head(6).items():
    print(f"    {pct:5.1f}%  {val}")

# --------------------------------------------------------------------------
section("3. STREET NAMES (intersection crashes)")
inter = raw[raw[C.COLUMNS["intersection"]].fillna("").str.upper().str.strip()
            .isin(C.INTERSECTION_TYPES)]
names = pd.concat([inter[C.COLUMNS["street"]], inter[C.COLUMNS["cross_street"]]])
norm = names.map(normalise_street)
norm = norm[norm != ""]
top = norm.value_counts().head(40)
print("\n  Most common street names (after normalization, before aliases are applied):")
for i in range(0, len(top), 2):
    pair = list(top.items())[i:i + 2]
    print("    " + "".join(f"{n:<30}{c:>6,}      " for n, c in pair).rstrip())

routes = norm[norm.str.match(r"^(SH|US|FM|IH|SL|SS|BS|BI|RM)\d")].value_counts()
print("\n  Route-numbered names (possible aliases of a local name):")
for n, c in routes.head(20).items():
    note = f"  -> {C.STREET_ALIASES[n]}" if n in C.STREET_ALIASES else ""
    print(f"    {n:<12}{c:>6,}{note}")
print("\n  Run check_aliases.py to test candidate pairs against crash locations.")
