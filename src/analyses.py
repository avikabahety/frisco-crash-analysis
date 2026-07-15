"""The analyses.

Each returns a plain dict so the report layer never touches a DataFrame, and so
results can be serialised to JSON and diffed between runs.

Findings are reported with the tests that could have refuted them. Where a test
came back negative, that is recorded too -- see `mechanism()['concentration']`.
"""

import numpy as np
import pandas as pd

import config as C
from src import stats
from src.data import season_days


# --------------------------------------------------------------------------
# 1. Does darkness raise left-turn crashes?
# --------------------------------------------------------------------------
def darkness(df):
    """The core finding, plus every test that could have overturned it.

    Design: hold the CLOCK HOUR fixed and compare dark against daylight crashes at
    that hour. 6pm is dark in December and light in June, but the traffic pattern
    at 6pm is similar in both. So the light is what differs, not the hour.
    """
    sig = df[df["signal"]]
    out = {}

    # Only hours containing enough of both dark and daylight crashes can separate the
    # two conditions: the sunset transition hours.
    usable = [h for h in range(24)
              if ((sig["hour"] == h) & sig["dark"]).sum() >= C.MIN_CELL
              and ((sig["hour"] == h) & sig["daylight"]).sum() >= C.MIN_CELL]
    out["usable_hours"] = usable

    pool = sig[sig["hour"].isin(usable)]
    dark, day = pool[pool["dark"]], pool[pool["daylight"]]
    p1, p2, diff, z, p = stats.compare_proportions(
        dark["is_left"].sum(), len(dark), day["is_left"].sum(), len(day))
    out["headline"] = {
        "dark_pct": p1 * 100, "day_pct": p2 * 100, "diff_pp": diff, "p": p,
        "n_dark": len(dark), "n_day": len(day),
        "k_dark": int(dark["is_left"].sum()), "k_day": int(day["is_left"].sum()),
    }

    # ---- absolute counts, not shares -------------------------------------
    # A proportion can rise while the underlying count falls, if the denominator
    # shrinks faster. Counting crashes per calendar day tests whether left-turn
    # crashes genuinely increase after dark, independent of the crash mix.
    win_days, sum_days = season_days(df)
    out["season_days"] = {"winter": win_days, "summer": sum_days}

    hours = {}
    for h in [C.CONTROL_HOUR] + C.EVENING_HOURS:
        w = sig[sig["winter"] & (sig["hour"] == h)]
        s = sig[sig["summer"] & (sig["hour"] == h)]
        if len(w) < 20 or len(s) < 20:
            continue
        lt_ratio, lo, hi = stats.rate_ratio(
            int(w["is_left"].sum()), win_days, int(s["is_left"].sum()), sum_days)
        all_ratio, _, _ = stats.rate_ratio(len(w), win_days, len(s), sum_days)
        hours[h] = {
            "winter_left": int(w["is_left"].sum()), "summer_left": int(s["is_left"].sum()),
            "winter_all": len(w), "summer_all": len(s),
            "winter_left_rate": w["is_left"].sum() / win_days * 1000,
            "summer_left_rate": s["is_left"].sum() / sum_days * 1000,
            "winter_all_rate": len(w) / win_days * 1000,
            "summer_all_rate": len(s) / sum_days * 1000,
            "left_ratio": lt_ratio, "left_lo": lo, "left_hi": hi,
            "all_ratio": all_ratio,
            "is_control": h == C.CONTROL_HOUR,
        }
    out["by_hour"] = hours

    # The contrast hours pooled, as a rate ratio.
    cw = sig[sig["winter"] & sig["hour"].isin(C.CONTRAST_HOURS)]
    cs = sig[sig["summer"] & sig["hour"].isin(C.CONTRAST_HOURS)]
    ratio, lo, hi = stats.rate_ratio(
        int(cw["is_left"].sum()), win_days, int(cs["is_left"].sum()), sum_days)
    out["contrast"] = {
        "winter_left": int(cw["is_left"].sum()), "summer_left": int(cs["is_left"].sum()),
        "ratio": ratio, "lo": lo, "hi": hi, "hours": C.CONTRAST_HOURS,
    }

    # ---- within-intersection ---------------------------------------------
    # Crashes after dark may occur at a different set of intersections than daylight
    # crashes. If so, the difference would reflect that mix rather than the light.
    strata, agree = [], 0
    for _, g in pool.groupby("key"):
        d, l = g[g["dark"]], g[g["daylight"]]
        if len(d) < C.MIN_STRATUM or len(l) < C.MIN_STRATUM:
            continue
        a, c = int(d["is_left"].sum()), int(l["is_left"].sum())
        strata.append((a, len(d) - a, c, len(l) - c))
        if a / len(d) > c / len(l):
            agree += 1
    or_mh, chi, p_mh = stats.mantel_haenszel(strata)
    z_sign, p_sign = stats.sign_test(agree, len(strata))
    out["within_intersection"] = {
        "n_strata": len(strata), "odds_ratio": or_mh, "p": p_mh,
        "agree": agree, "p_sign": p_sign,
    }

    # ---- weather ----------------------------------------------------------
    # Winter is darker AND wetter. Restrict to dry pavement.
    dry = pool[pool["dry"]]
    d, l = dry[dry["dark"]], dry[dry["daylight"]]
    _, _, diff_dry, _, p_dry = stats.compare_proportions(
        d["is_left"].sum(), len(d), l["is_left"].sum(), len(l))
    out["dry_only"] = {"diff_pp": diff_dry, "p": p_dry, "n": len(dry)}

    # ---- impairment -------------------------------------------------------
    sober = pool[~pool["impaired"]]
    d, l = sober[sober["dark"]], sober[sober["daylight"]]
    _, _, diff_sob, _, p_sob = stats.compare_proportions(
        d["is_left"].sum(), len(d), l["is_left"].sum(), len(l))
    out["sober_only"] = {"diff_pp": diff_sob, "p": p_sob,
                         "impaired_pct": pool["impaired"].mean() * 100}

    # ---- placebo ----------------------------------------------------------
    # If every crash type shifts the same way after dark, the explanation is general
    # night-time driving difficulty rather than anything specific to left turns.
    # Right-turn crashes provide the comparison.
    placebo = {}
    for label, col in [("left", "is_left"), ("right", "is_right"),
                       ("angle", "is_angle"), ("rear", "is_rear")]:
        pa, pb, diff_c, _, p_c = stats.compare_proportions(
            dark[col].sum(), len(dark), day[col].sum(), len(day))
        placebo[label] = {"dark_pct": pa * 100, "day_pct": pb * 100,
                          "diff_pp": diff_c, "p": p_c}
    out["placebo"] = placebo

    # ---- excess crashes ---------------------------------------------------
    # Only the left-turn-specific excess is attributed: what remains after allowing
    # for the general increase in crashes after dark.
    excess = 0.0
    for h, v in hours.items():
        if v["is_control"] or h not in C.EVENING_HOURS:
            continue
        expected = v["summer_left_rate"] * v["all_ratio"]
        excess += max(v["winter_left_rate"] - expected, 0) / 1000 * win_days
    years = (df["date"].max() - df["date"].min()).days / 365.25
    out["excess"] = {"total": excess, "per_year": excess / years, "years": years}
    out["span"] = {"start_year": int(df["date"].min().year),
                   "end_year": int(df["date"].max().year),
                   "start": df["date"].min().date().isoformat(),
                   "end": df["date"].max().date().isoformat()}

    return out


# --------------------------------------------------------------------------
# 2. Are these permissive-phase crashes?
# --------------------------------------------------------------------------
def mechanism(df):
    """What contributing factors are recorded for left-turn crashes.

    A driver is required to yield only on a permissive phase; under a protected left
    the turning driver has right of way. The contributing factor therefore carries
    information about which phase was operating. Calibrated against flashing-yellow
    control, which is permissive by definition.
    """
    sig = df[df["signal"]]
    left = sig[sig["is_left"]]
    out = {"n_left": len(left)}

    fy = df[df["flashing_yellow"] & df["is_left"]]
    out["calibration"] = {
        "n": len(fy),
        "failed_to_yield_pct": fy["failed_to_yield"].mean() * 100 if len(fy) else np.nan,
        "ran_red_pct": fy["ran_red"].mean() * 100 if len(fy) else np.nan,
    }
    out["overall"] = {
        "failed_to_yield_pct": left["failed_to_yield"].mean() * 100,
        "ran_red_pct": left["ran_red"].mean() * 100,
        "neither_pct": (~left["failed_to_yield"] & ~left["ran_red"]).mean() * 100,
    }

    by_hour = {}
    for h in range(24):
        m = left[left["hour"] == h]
        if len(m) < 15:
            continue
        by_hour[h] = {"n": len(m),
                      "failed_to_yield_pct": m["failed_to_yield"].mean() * 100,
                      "ran_red_pct": m["ran_red"].mean() * 100}
    out["by_hour"] = by_hour

    # Contrast hours specifically: if lefts were protected at 6-8pm, these crashes
    # should read as red-light running. They do not.
    ch = left[left["hour"].isin(C.CONTRAST_HOURS)]
    out["contrast_hours"] = {
        "n": len(ch),
        "failed_to_yield_pct": ch["failed_to_yield"].mean() * 100,
        "ran_red_pct": ch["ran_red"].mean() * 100,
    }

    # Left-turn crashes after dark by intersection. Phasing is configured per
    # intersection rather than city-wide, so results are reported per intersection.
    dark_eve = left[left["hour"].isin(C.EVENING_HOURS) & left["dark"]]
    sites = []
    for key, g in dark_eve.groupby("key"):
        if len(g) < 4:
            continue
        sites.append({"intersection": key, "crashes": len(g),
                      "failed_to_yield_pct": g["failed_to_yield"].mean() * 100,
                      "ran_red_pct": g["ran_red"].mean() * 100})
    out["sites"] = sorted(sites, key=lambda s: -s["crashes"])

    # ---- a test that does not distinguish the groups ----------------------
    # Whether the darkness effect is concentrated at permissive-leaning intersections
    # is not resolvable here. The two groups are statistically indistinguishable, and
    # the classification is limited by construction: an intersection running
    # protected-only left turns produces few left-turn crashes, so it rarely meets the
    # minimum needed to be classified. The comparison is closer to "more permissive"
    # against "less permissive" than to permissive against protected. Reported so the
    # limitation travels with the result.
    mid = left[left["hour"].isin(C.MIDDAY_HOURS)]
    scores = {k: g["failed_to_yield"].mean()
              for k, g in mid.groupby("key") if len(g) >= 4}
    conc = {"testable": len(scores) >= 6, "n_classified": len(scores)}
    if conc["testable"]:
        s = pd.Series(scores)
        cut = s.median()
        hi_keys, lo_keys = set(s[s >= cut].index), set(s[s < cut].index)
        ev = sig[sig["hour"].isin(C.EVENING_HOURS)]
        cells = {}
        for label, keys in [("permissive_leaning", hi_keys), ("protected_leaning", lo_keys)]:
            m = ev[ev["key"].isin(keys)]
            d, l = m[m["dark"]], m[m["daylight"]]
            cells[label] = (int(d["is_left"].sum()), len(d),
                            int(l["is_left"].sum()), len(l))
        a = cells["permissive_leaning"]
        b = cells["protected_leaning"]
        or1, or2, z, p = stats.interaction(a[0], a[1], a[2], a[3],
                                           b[0], b[1], b[2], b[3])
        conc.update({"median_cut": cut * 100, "or_permissive": or1,
                     "or_protected": or2, "p": p,
                     "distinguishable": bool(p < 0.05) if not np.isnan(p) else False})
    out["concentration"] = conc

    return out


# --------------------------------------------------------------------------
# 3. What changes when a signal is installed?
# --------------------------------------------------------------------------
def signalisation(df, install_path=None):
    """Before/after at intersections with known signal installation dates.

    Reported as rates, not shares. A share can rise while the underlying rate falls:
    after signalisation the left-turn share rises while the left-turn rate falls,
    because total crashes fall faster. Shares alone would invert the sign.
    """
    path = install_path or C.INSTALL_FILE
    try:
        raw = pd.read_csv(path, dtype=str)
    except FileNotFoundError:
        return {"available": False}

    from src.data import intersection_key
    import re as _re

    def key_of(name):
        parts = [p for p in _re.split(r"\s*(?:&|/|\+|\bAND\b|\bAT\b)\s*",
                                      str(name), flags=_re.I) if p.strip()]
        return intersection_key(parts[0], parts[1]) if len(parts) >= 2 else ""

    name_col = next((c for c in raw.columns
                     if _re.search(r"intersect|name|location", c, _re.I)), raw.columns[0])
    date_col = next((c for c in raw.columns
                     if _re.search(r"date|install|operational", c, _re.I)), raw.columns[1])
    raw["key"] = raw[name_col].map(key_of)
    raw["install"] = pd.to_datetime(raw[date_col], errors="coerce", format="mixed")
    inst = raw[(raw["key"] != "") & raw["install"].notna()]

    first, last = df["date"].min(), df["date"].max()
    buf = pd.Timedelta(days=C.BUFFER_DAYS)
    inst = inst[
        ((inst["install"] - buf - first).dt.days / 365.25 >= C.MIN_YEARS)
        & ((last - inst["install"] - buf).dt.days / 365.25 >= C.MIN_YEARS)
        & inst["key"].isin(set(df["key"]))
    ]
    if not len(inst):
        return {"available": False}

    pre_frames, post_frames, pre_years, post_years, sites = [], [], 0.0, 0.0, []
    for _, r in inst.iterrows():
        site = df[df["key"] == r["key"]]
        pre = site[site["date"] < r["install"] - buf]
        post = site[site["date"] >= r["install"] + buf]
        y_pre = (r["install"] - buf - first).days / 365.25
        y_post = (last - r["install"] - buf).days / 365.25
        pre_frames.append(pre)
        post_frames.append(post)
        pre_years += y_pre
        post_years += y_post

        def rate(frame, col, years):
            return frame[col].sum() / years if years > 0 else np.nan

        sites.append({
            "intersection": r["key"], "installed": r["install"].date().isoformat(),
            "n_pre": len(pre), "n_post": len(post),
            "years_pre": y_pre, "years_post": y_post,
            "angle_pre": pre["is_angle"].mean() * 100 if len(pre) else np.nan,
            "angle_post": post["is_angle"].mean() * 100 if len(post) else np.nan,
            "angle_rate_pre": rate(pre, "is_angle", y_pre),
            "angle_rate_post": rate(post, "is_angle", y_post),
            "rear_rate_pre": rate(pre, "is_rear", y_pre),
            "rear_rate_post": rate(post, "is_rear", y_post),
            "left_rate_pre": rate(pre, "is_left", y_pre),
            "left_rate_post": rate(post, "is_left", y_post),
            "total_rate_pre": len(pre) / y_pre if y_pre > 0 else np.nan,
            "total_rate_post": len(post) / y_post if y_post > 0 else np.nan,
        })

    pre = pd.concat(pre_frames)
    post = pd.concat(post_frames)
    types = {}
    for label, col in [("angle", "is_angle"), ("rear", "is_rear"),
                       ("left", "is_left"), ("injury", "is_injury")]:
        k_pre, k_post = int(pre[col].sum()), int(post[col].sum())
        r_pre = k_pre / pre_years
        r_post = k_post / post_years
        _, _, diff, _, p_share = stats.compare_proportions(
            k_post, len(post), k_pre, len(pre))
        types[label] = {
            "share_pre": k_pre / len(pre) * 100, "share_post": k_post / len(post) * 100,
            "share_diff_pp": diff, "share_p": p_share,
            "rate_pre": r_pre, "rate_post": r_post,
            "rate_change_pct": (r_post / r_pre - 1) * 100 if r_pre else np.nan,
        }

    return {
        "available": True, "n_sites": len(inst),
        "n_pre": len(pre), "n_post": len(post),
        "years_pre": pre_years, "years_post": post_years,
        "types": types, "sites": sorted(sites, key=lambda s: -s["n_pre"]),
    }
