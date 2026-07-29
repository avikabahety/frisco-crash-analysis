#!/usr/bin/env python3
"""Run the full Frisco crash analysis and write every artifact.

    python analyze.py            run everything
    python analyze.py --inspect  print the CRIS columns your export actually has

Outputs
    docs/index.html              the results page (served by GitHub Pages)
    output/results.json          every number, machine-readable
    output/hourly.csv            left-turn crashes by hour and season
    output/intersections.csv     dark-evening left-turn crashes by intersection
    output/intersection_contrast.csv  winter vs summer left-turn rate by intersection (6-8pm)
"""

import sys

import pandas as pd

import config as C
from src import analyses, report
from src.data import load
from src.stats import stars


def inspect():
    """Print the CRIS export's header and confirm config.COLUMNS matches it.

    CRIS field names vary between export versions, and a silently missing column is
    worse than a loud error. Run this once before trusting any number.
    """
    from src.data import _header_row

    purpose = {
        "crash_id": "record identity (one row per crash)",
        "date": "year, month, season; before/after split",
        "time": "hour of day  [stored as HHMM, e.g. '1745']",
        "street": "intersection identity (first street)",
        "cross_street": "intersection identity (second street)",
        "collision": "crash type: left-turn / angle / rear-end / right-turn",
        "factors": "permissive vs protected fingerprint; impairment",
        "control": "signalised filter; flashing-yellow calibration",
        "light": "DARK vs DAYLIGHT  <- the independent variable",
        "surface": "dry-pavement-only robustness check",
        "intersection": "scope filter: intersection / freeway / driveway",
    }

    raw = pd.read_csv(C.CRASH_FILE, dtype=str,
                      skiprows=_header_row(C.CRASH_FILE), nrows=5, low_memory=False)
    present = set(raw.columns)
    print(f"{C.CRASH_FILE.name}")
    print(f"  {len(raw.columns)} columns in the export, {len(C.COLUMNS)} used\n")

    print("USED BY THE ANALYSIS")
    missing = []
    for field, column in C.COLUMNS.items():
        ok = column in present
        if not ok:
            missing.append(column)
        print(f"  {'ok ' if ok else 'MISSING'}  {column:<28} {purpose.get(field, '')}")

    unused = sorted(present - set(C.COLUMNS.values()))
    print(f"\nNOT USED ({len(unused)} columns)")
    print("  Notable omissions and why:")
    print("    Average Daily Traffic Amount   only ~30% populated (on-system roads)")
    print("    At Intersection Flag           drops ~3,700 approach crashes")
    print("    Number of Lanes / Median Type  only ~30% populated")
    for i in range(0, len(unused), 3):
        print("    " + "  ".join(f"{c[:34]:<36}" for c in unused[i:i + 3]).rstrip())

    if missing:
        print(f"\n{len(missing)} REQUIRED COLUMN(S) MISSING: {missing}")
        print("Update config.COLUMNS to match your export, or re-export with these fields.")
        sys.exit(1)
    print("\nAll required columns present.")


def main():
    if "--inspect" in sys.argv:
        inspect()
        return

    if not C.CRASH_FILE.exists():
        print(f"Crash export not found: {C.CRASH_FILE}")
        print("Export from https://cris.dot.state.tx.us (Query -> City = FRISCO ->")
        print("crash-level Attribute List -> CSV) and place it there. See README.")
        sys.exit(1)

    print(f"Reading {C.CRASH_FILE.name}\n")
    df, funnel = load()
    funnel.append(("at signalised intersections — analysis population",
                   int(df["signal"].sum())))

    print("\nRunning analyses")
    dark = analyses.darkness(df)
    mech = analyses.mechanism(df)

    C.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- console summary --------------------------------------------------
    c = dark["contrast"]
    wi = dark["within_intersection"]
    conc = mech["concentration"]
    ctrl = dark["by_hour"].get(C.CONTROL_HOUR)

    def fh(h):
        """Format a 24h integer hour as 12h string, e.g. 18 -> '6pm'."""
        return '%d%s' % (h % 12 or 12, 'am' if h < 12 else 'pm')

    win_days = dark["season_days"]["winter"]
    sum_days = dark["season_days"]["summer"]

    # All-day totals (all hours present in by_hour, typically 6am-10pm)
    day_w = sum(v["winter_all"] for v in dark["by_hour"].values())
    day_s = sum(v["summer_all"] for v in dark["by_hour"].values())
    day_w_rate = day_w / win_days * 1000
    day_s_rate = day_s / sum_days * 1000

    # 6-8pm window totals
    all_w = sum(dark["by_hour"][h2]["winter_all"] for h2 in C.CONTRAST_HOURS
                if h2 in dark["by_hour"])
    all_s = sum(dark["by_hour"][h2]["summer_all"] for h2 in C.CONTRAST_HOURS
                if h2 in dark["by_hour"])
    all_w_rate = all_w / win_days * 1000
    all_s_rate = all_s / sum_days * 1000

    print(f"""
  ALL CRASHES  (6am-10pm, all hours)
    winter {day_w:,} total   {day_w_rate:.1f}/1,000 days
    summer {day_s:,} total   {day_s_rate:.1f}/1,000 days

    6-8pm window
    winter {all_w_rate:.1f}/1,000 days   summer {all_s_rate:.1f}/1,000 days   ratio {all_w_rate / all_s_rate:.2f}x
    (left-turn breakdown follows)

  LEFT-TURN FINDING  ({fh(c['hours'][0])}-{fh(c['hours'][-1] + 1)})
    winter {c['winter_left']}   summer {c['summer_left']}
    rate ratio {c['ratio']:.2f}x   95% CI [{c['lo']:.2f}, {c['hi']:.2f}]

  CONTROL HOUR  ({fh(C.CONTROL_HOUR)}, light in both seasons — no effect expected)
    left-turn ratio {ctrl['left_ratio']:.2f}x""" if ctrl else "    no data")

    print(f"""
  CHECKS
    dry pavement only     {dark['dry_only']['diff_pp']:+.1f} pp  p={dark['dry_only']['p']:.6f} {stars(dark['dry_only']['p'])}
    right-turn placebo    {dark['placebo']['right']['diff_pp']:+.1f} pp  p={dark['placebo']['right']['p']:.4f} {stars(dark['placebo']['right']['p'])}
    rates not shares      {fh(18)}: left {dark['by_hour'].get(18, {}).get('left_ratio', 0):.2f}x vs all {dark['by_hour'].get(18, {}).get('all_ratio', 0):.2f}x  ({fh(c['hours'][0])}-{fh(c['hours'][-1] + 1)} combined: {c['ratio']:.2f}x)
    within intersection   OR {wi['odds_ratio']:.2f}  p={wi['p']:.6f} {stars(wi['p'])}  ({wi['agree']}/{wi['n_strata']} move predicted way)
    excluding impaired    {dark['sober_only']['diff_pp']:+.1f} pp  p={dark['sober_only']['p']:.6f} {stars(dark['sober_only']['p'])}

  MECHANISM  (6-8pm left-turn crashes citing 'failed to yield while turning left')
    flashing yellow / permissive by definition  {mech['calibration']['failed_to_yield_pct']:.0f}%
    all signals                                 {mech['overall']['failed_to_yield_pct']:.0f}%
    6-8pm specifically                          {mech['contrast_hours']['failed_to_yield_pct']:.0f}%
    disregarded signal at 6-8pm                 {mech['contrast_hours']['ran_red_pct']:.0f}%

  INTERSECTION CONTRAST  (6-8pm, ranked by rate gap)""")
    for s in dark["intersection_contrast"]:
        sig_flag = " *" if s["significant"] else ""
        print("    %-35s  winter %2d  summer %2d  gap %+.1f  ratio %.2fx [%.2f-%.2f]%s" % (
            s["intersection"], s["winter_left"], s["summer_left"],
            s["gap"], s["ratio"], s["ratio_lo"], s["ratio_hi"], sig_flag))

    print(f"""
  NOT ESTABLISHED
    permissive vs protected distinction not resolvable""")
    if conc.get("testable"):
        print("    groups indistinguishable, p=%.2f" % conc["p"])
        print("    (protected intersections produce too few left-turn crashes to classify)")

    # ---- artifacts --------------------------------------------------------

    # hourly.csv — one row per hour. Columns:
    #
    # hour               clock hour (0-23)
    # winter_left        raw left-turn crash count, winter months (Nov-Feb)
    # summer_left        raw left-turn crash count, summer months (May-Aug)
    # winter_all         raw total crash count, winter months
    # summer_all         raw total crash count, summer months
    # winter_left_rate   left-turn crashes per 1,000 winter calendar days
    # summer_left_rate   left-turn crashes per 1,000 summer calendar days
    # winter_all_rate    all crashes per 1,000 winter calendar days
    # summer_all_rate    all crashes per 1,000 summer calendar days
    # left_ratio         winter/summer rate ratio for left-turn crashes
    # left_lo            95% CI lower bound for left_ratio (Poisson)
    # left_hi            95% CI upper bound for left_ratio (Poisson)
    # all_ratio          winter/summer rate ratio for all crashes at this hour
    # is_control         True for hour 17 (light in both seasons; no darkness contrast)
    pd.DataFrame([
        {"hour": k, **{kk: vv for kk, vv in v.items()}}
        for k, v in sorted(dark["by_hour"].items())
    ]).to_csv(C.OUTPUT_DIR / "hourly.csv", index=False)

    # intersections.csv — one row per intersection with at least 4 dark evening
    # left-turn crashes (hours 18-21). Drawn from the mechanism analysis. Columns:
    #
    # intersection         normalised street-name pair (e.g. PRESTON RD & SH121)
    # crashes              dark evening left-turn crash count at this intersection
    # failed_to_yield_pct  % coded "failed to yield right of way - turning left"
    #                      (signature of a permissive left-turn phase)
    # ran_red_pct          % coded "disregarded stop and go signal"
    #                      (signature of a protected phase or red-light running)
    pd.DataFrame(mech["sites"]).to_csv(C.OUTPUT_DIR / "intersections.csv", index=False)

    # intersection_contrast.csv — one row per intersection that clears
    # MIN_INTERSECTION_CONTRAST left-turn crashes in both winter and summer
    # during contrast hours (6-8pm). All qualifying intersections included
    # regardless of direction. Ranked by winter-minus-summer rate gap. Columns:
    #
    # intersection          normalised street-name pair
    # winter_left           raw left-turn crash count during 6-8pm, winter months
    # summer_left           raw left-turn crash count during 6-8pm, summer months
    # winter_rate           winter left-turn crashes per 1,000 winter days
    # summer_rate           summer left-turn crashes per 1,000 summer days
    # gap                   winter_rate - summer_rate (positive = winter higher)
    # ratio                 winter/summer rate ratio
    # ratio_lo              95% CI lower bound (Poisson)
    # ratio_hi              95% CI upper bound (Poisson)
    # significant           True if ratio_lo > 1.0
    # direction             winter_higher / equal / summer_higher
    # failed_to_yield_pct   % of dark evening left-turn crashes citing failure
    #                       to yield while turning left (null if < 4 crashes)
    pd.DataFrame(dark["intersection_contrast"]).to_csv(
        C.OUTPUT_DIR / "intersection_contrast.csv", index=False)

    report.write_json(dark, mech)
    page = report.render(dark, mech, funnel)

    written = [str(page.relative_to(C.ROOT)), "output/results.json",
               "output/hourly.csv", "output/intersections.csv",
               "output/intersection_contrast.csv"]
    print("\n  WROTE")
    for w in written:
        print(f"    {w}")
    print("\n  Preview the page:  cd docs && python -m http.server 8000\n")


if __name__ == "__main__":
    main()
