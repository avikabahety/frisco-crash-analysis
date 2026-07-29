"""Load and prepare the TxDOT CRIS crash export.

One source of truth for the filter funnel. Every analysis draws from `load()`, so
the population is identical across all of them.
"""

import re

import numpy as np
import pandas as pd

import config as C

# Street-name suffix normalisation, so "MAIN STREET" and "MAIN ST" are one place.
_SUFFIX = {
    "ROAD": "RD", "STREET": "ST", "DRIVE": "DR", "AVENUE": "AVE", "LANE": "LN",
    "PARKWAY": "PKWY", "BOULEVARD": "BLVD", "COURT": "CT", "TRAIL": "TRL",
    "HIGHWAY": "HWY", "TOLLWAY": "TLWY", "EXPRESSWAY": "EXPY", "CIRCLE": "CIR",
    "PLACE": "PL", "TERRACE": "TER", "NORTH": "N", "SOUTH": "S",
    "EAST": "E", "WEST": "W",
}
_ROUTE = re.compile(r"^(SH|US|FM|IH|SL|SS|BS|BI|RM)[\s\-]*0*(\d+)(.*)$")


def normalise_street(name):
    """'SH0121', 'SH 121', 'SH-121' -> 'SH121'. 'MAIN STREET' -> 'MAIN ST'.

    Then resolve route-number aliases: officers record the same physical road under
    either its route number or its local name (FM2934 and ELDORADO PKWY are one
    road), which would otherwise split a single intersection across two keys and
    undercount both halves. See config.STREET_ALIASES.
    """
    if not isinstance(name, str):
        return ""
    x = re.sub(r"\s+", " ", re.sub(r"[.,]", " ", name.upper().strip())).strip()
    if x in C.NULL_VALUES:
        return ""
    m = _ROUTE.match(x)
    if m:
        route = f"{m.group(1)}{int(m.group(2))}{m.group(3).rstrip()}".strip()
        return C.STREET_ALIASES.get(route, route)
    canonical = " ".join(_SUFFIX.get(p, p) for p in x.split(" ")).strip()
    return C.STREET_ALIASES.get(canonical, canonical)


def intersection_key(a, b):
    """Order-independent identity for an intersection. Empty if unusable."""
    a, b = normalise_street(a), normalise_street(b)
    if not a or not b or a == b:      # a street crossing itself is a data artifact
        return ""
    return " & ".join(sorted([a, b]))


def parse_hour(series):
    """CRIS stores time as HHMM ('1745'). Handle
    HHMM, HH:MM and AM/PM explicitly."""
    s = series.astype(str).str.strip().str.upper()
    hour = pd.Series(np.nan, index=s.index, dtype="float")

    has_colon = s.str.contains(":")
    if has_colon.any():
        parsed = pd.to_datetime(s[has_colon], errors="coerce", format="mixed")
        hour.loc[has_colon] = parsed.dt.hour

    digits = (~has_colon) & s.str.fullmatch(r"\d{1,4}")
    if digits.any():
        h = s[digits].str.zfill(4).str[:2].astype(int)
        hour.loc[digits] = h.where(h <= 23, np.nan)

    return hour


def _header_row(path, token="crash id", limit=60):
    """CRIS exports place a title, disclaimer and filter summary above the header."""
    with open(path, "r", errors="replace") as fh:
        for i, line in enumerate(fh):
            if token in line.lower():
                return i
            if i > limit:
                break
    return 0


def load(path=None):
    """Return the analysis frame and a record of the filter funnel.

    The dataframe contains every intersection crash. Individual analyses narrow further
    (e.g. to signalised intersections) from this common base.
    """
    path = path or C.CRASH_FILE
    raw = pd.read_csv(path, dtype=str, skiprows=_header_row(path), low_memory=False)
    col = C.COLUMNS
    funnel = [("CRIS export", len(raw))]

    df = pd.DataFrame(index=raw.index)
    df["crash_id"] = raw[col["crash_id"]]
    df["date"] = pd.to_datetime(raw[col["date"]], errors="coerce", format="mixed")
    df["hour"] = parse_hour(raw[col["time"]])
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    upper = lambda c: raw[col[c]].fillna("").astype(str).str.upper().str.strip()
    df["intersection_type"] = upper("intersection")
    df["collision"] = upper("collision")
    df["factors"] = upper("factors")
    df["control"] = upper("control")
    df["light"] = upper("light")
    df["surface"] = upper("surface")
    df["key"] = [intersection_key(a, b)
                 for a, b in zip(raw[col["street"]], raw[col["cross_street"]])]

    # 1. crashes that belong to an intersection
    df = df[df["intersection_type"].isin(C.INTERSECTION_TYPES)]
    funnel.append(("at or related to an intersection (signalised, stop-controlled, and other)", len(df)))

    # 2. crashes attributable to a named intersection
    df = df[df["key"] != ""]
    funnel.append(("both street names present", len(df)))

    # 3. crashes that can be placed in time
    df = df[df["hour"].notna() & df["date"].notna()]
    funnel.append(("time and date parse", len(df)))

    # 4. drop the provisional tail: recent months are under-reported in CRIS, and
    # the shortfall falls unevenly across the seasons being compared. See
    # config.ANALYSIS_END.
    if C.ANALYSIS_END:
        df = df[df["date"] <= pd.Timestamp(C.ANALYSIS_END)]
        funnel.append((f"on or before {C.ANALYSIS_END}", len(df)))

    # derived flags used across analyses
    df["is_left"] = df["collision"].str.contains("ONE STRAIGHT-ONE LEFT TURN", na=False)
    df["is_right"] = df["collision"].str.contains("ONE STRAIGHT-ONE RIGHT TURN", na=False)
    df["is_angle"] = df["collision"].str.contains("ANGLE - BOTH GOING STRAIGHT", na=False)
    df["is_rear"] = df["collision"].str.contains(
        "REAR END|ONE STRAIGHT-ONE STOPPED", na=False)
    df["signal"] = df["control"].str.contains("SIGNAL LIGHT", na=False)
    df["flashing_yellow"] = df["control"].str.contains("FLASHING YELLOW", na=False)

    df["dark"] = df["light"].str.contains("DARK", na=False)
    df["daylight"] = df["light"].str.contains("DAYLIGHT", na=False)
    df["dry"] = df["surface"].str.contains("DRY", na=False)

    # A driver only has to YIELD on a permissive phase. Under a protected left the
    # turning driver has right of way and cannot "fail to yield".
    df["failed_to_yield"] = df["factors"].str.contains(
        "FAILED TO YIELD RIGHT OF WAY - TURNING LEFT", na=False)
    df["ran_red"] = df["factors"].str.contains("DISREGARD STOP AND GO SIGNAL", na=False)
    df["impaired"] = df["factors"].str.contains(
        "UNDER INFLUENCE|IMPAIR|ALCOHOL|DRUG|INTOXICAT", na=False)

    df["winter"] = df["month"].isin(C.WINTER_MONTHS)
    df["summer"] = df["month"].isin(C.SUMMER_MONTHS)

    return df.reset_index(drop=True), funnel


def season_days(df):
    """Calendar days covered by winter and summer months, so seasonal crash counts
    can be compared as rates rather than raw totals."""
    days = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    return (int(days[days.month.isin(C.WINTER_MONTHS)].size),
            int(days[days.month.isin(C.SUMMER_MONTHS)].size))
