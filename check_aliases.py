#!/usr/bin/env python3
"""Check street-name aliases.

Officers record the same physical road under either its route number or its local
name (FM2934 and ELDORADO PKWY are one road). Unresolved, this splits a single
intersection across two keys and undercounts both halves.

This script:
  1. Shows what config.STREET_ALIASES merges, and how many crashes it moves.
  2. Searches for aliases not yet in the map, from the data alone: two street names
     whose crashes occupy the same ground are likely to be the same road.
  3. Reports the effect on intersection identity.

Run:  python check_aliases.py
"""

import numpy as np
import pandas as pd

import config as C
from src.data import _header_row, intersection_key, normalise_street

pd.set_option("display.width", 150)
M_PER_DEG = 111_320.0


def section(t):
    print("\n" + "=" * 82 + f"\n{t}\n" + "=" * 82)


raw = pd.read_csv(C.CRASH_FILE, dtype=str,
                  skiprows=_header_row(C.CRASH_FILE), low_memory=False)
col = C.COLUMNS

ir = raw[col["intersection"]].fillna("").str.upper().str.strip()
keep = ir.isin(C.INTERSECTION_TYPES)
df = raw[keep].copy()
# Lat/lon are read directly from the raw CSV — they are not in C.COLUMNS since the
# main analysis does not use coordinates, but they are needed here to detect aliases
# by comparing the geographic footprint of crash clusters for each street name.
df["lat"] = pd.to_numeric(df.get("Latitude"), errors="coerce")
df["lon"] = pd.to_numeric(df.get("Longitude"), errors="coerce")

# --------------------------------------------------------------------------
section("1. WHAT THE ALIAS MAP MERGES")


def _bare(name):
    """Normalisation WITHOUT alias resolution, to show the before state."""
    import re
    if not isinstance(name, str):
        return ""
    x = re.sub(r"\s+", " ", re.sub(r"[.,]", " ", name.upper().strip())).strip()
    if x in C.NULL_VALUES:
        return ""
    m = re.match(r"^(SH|US|FM|IH|SL|SS|BS|BI|RM)[\s\-]*0*(\d+)(.*)$", x)
    if m:
        return f"{m.group(1)}{int(m.group(2))}{m.group(3).rstrip()}".strip()
    from src.data import _SUFFIX
    return " ".join(_SUFFIX.get(p, p) for p in x.split(" ")).strip()


names_before = pd.concat([
    df[col["street"]].map(_bare), df[col["cross_street"]].map(_bare)])
names_before = names_before[names_before != ""]
counts = names_before.value_counts()

print(f"  {'route':<12}{'local name':<18}{'as route':>10}{'as local':>10}{'merged':>9}")
for route, local in C.STREET_ALIASES.items():
    a, b = int(counts.get(route, 0)), int(counts.get(local, 0))
    flag = "  <- both heavily used" if min(a, b) > 200 else ""
    print(f"  {route:<12}{local:<18}{a:>10,}{b:>10,}{a + b:>9,}{flag}")

# --------------------------------------------------------------------------
section("2. SEARCH FOR ALIASES NOT YET IN THE MAP (from coordinates alone)")
print("  Two street names are likely to be the same road if their crashes occupy the")
print("  same ground. For each pair of common street names, this compares the centre")
print("  of their crashes and the spread around it.\n")

rows = []
for side in (col["street"], col["cross_street"]):
    t = pd.DataFrame({"name": df[side].map(_bare),
                      "lat": df["lat"], "lon": df["lon"]})
    rows.append(t[(t["name"] != "") & t["lat"].notna()])
pts = pd.concat(rows)

common = pts["name"].value_counts()
common = common[common >= 100].index          # only roads with enough crashes
prof = pts[pts["name"].isin(common)].groupby("name").agg(
    n=("lat", "size"), lat=("lat", "median"), lon=("lon", "median"),
    lat_sd=("lat", "std"), lon_sd=("lon", "std"))

known = set(C.STREET_ALIASES.keys()) | set(C.STREET_ALIASES.values())
cands = []
for i, a in enumerate(prof.index):
    for b in prof.index[i + 1:]:
        ra, rb = prof.loc[a], prof.loc[b]
        # distance between the two roads' crash centroids
        dy = (ra["lat"] - rb["lat"]) * M_PER_DEG
        dx = (ra["lon"] - rb["lon"]) * M_PER_DEG * np.cos(np.radians(ra["lat"]))
        dist = float(np.hypot(dx, dy))
        # a road is a line, so compare its spread too: same road = same footprint
        spread_a = float(np.hypot(ra["lat_sd"], ra["lon_sd"]) * M_PER_DEG)
        spread_b = float(np.hypot(rb["lat_sd"], rb["lon_sd"]) * M_PER_DEG)
        if dist < 900 and abs(spread_a - spread_b) < 1400:
            cands.append({
                "name A": a, "name B": b,
                "n A": int(ra["n"]), "n B": int(rb["n"]),
                "centres apart (m)": round(dist),
                "known alias": "yes" if (a in known and b in known) else "",
            })

if cands:
    out = pd.DataFrame(cands).sort_values("centres apart (m)")
    print(out.head(20).to_string(index=False))
    print("\n  'known alias' = already handled in config.STREET_ALIASES.")
    print("  Other pairs with centres close together warrant a manual check: they may be")
    print("  genuine aliases, or two roads that happen to cross near the centre of town.")
    print("  Geometry alone cannot separate those cases. Confirm on a map before adding")
    print("  an entry to the alias map.")
else:
    print("  No further candidates found.")

# --------------------------------------------------------------------------
section("3. IMPACT ON INTERSECTION IDENTITY")

before = pd.Series([
    (" & ".join(sorted([_bare(a), _bare(b)]))
     if _bare(a) and _bare(b) and _bare(a) != _bare(b) else "")
    for a, b in zip(df[col["street"]], df[col["cross_street"]])])
after = pd.Series([intersection_key(a, b)
                   for a, b in zip(df[col["street"]], df[col["cross_street"]])])

b_keys = before[before != ""].value_counts()
a_keys = after[after != ""].value_counts()
print(f"  distinct intersections BEFORE alias merge : {len(b_keys):,}")
print(f"  distinct intersections AFTER  alias merge : {len(a_keys):,}")
print(f"  intersections collapsed                   : {len(b_keys) - len(a_keys):,}")
print(f"\n  rankable (>=10 crashes) before : {(b_keys >= 10).sum():,}")
print(f"  rankable (>=10 crashes) after  : {(a_keys >= 10).sum():,}")

print("\n  Intersections that GREW the most (these were split in two):")
grew = []
for key, n_after in a_keys.items():
    n_before = int(b_keys.get(key, 0))
    if n_after - n_before >= 5:
        grew.append({"intersection": key, "before": n_before, "after": int(n_after),
                     "gained": int(n_after) - n_before})
if grew:
    g = pd.DataFrame(grew).sort_values("gained", ascending=False)
    print(g.head(15).to_string(index=False))
    print("\n  'before' counts only the crashes recorded under the name that survived;")
    print("  the rest were sitting under the alias, as a separate intersection.")
else:
    print("    (none)")
