#!/usr/bin/env python3
"""Run the full Frisco crash analysis and write every artifact.

    python analyze.py            run everything
    python analyze.py --inspect  print the CRIS columns your export actually has

Outputs
    docs/index.html              the results page (served by GitHub Pages)
    output/results.json          every number, machine-readable
    output/hourly.csv            left-turn crashes by hour and season
    output/intersections.csv     dark-evening left-turn crashes by intersection
    output/signalisation.csv     before/after each signal installation
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
        "lat": "mapping only (not the intersection key)",
        "lon": "mapping only (not the intersection key)",
        "severity": "KABCO code -> injury flag",
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

    print("\nRunning analyses")
    dark = analyses.darkness(df)
    mech = analyses.mechanism(df)
    sig = analyses.signalisation(df)

    C.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- headline ---------------------------------------------------------
    c = dark["contrast"]
    h = dark["headline"]
    wi = dark["within_intersection"]
    print(f"""
  FINDING
    Left-turn crashes, {c['hours'][0]}:00-{c['hours'][-1] + 1}:00
      winter {c['winter_left']}   summer {c['summer_left']}
      rate ratio {c['ratio']:.2f}x   95% CI [{c['lo']:.2f}, {c['hi']:.2f}]

    Share of crashes that are left-turn, same hours:
      dark {h['dark_pct']:.1f}%   daylight {h['day_pct']:.1f}%
      difference {h['diff_pp']:+.1f} pp   p={h['p']:.6f} {stars(h['p'])}

  CHECKS
    within intersection   OR {wi['odds_ratio']:.2f}  p={wi['p']:.6f} {stars(wi['p'])}
    dry pavement only     {dark['dry_only']['diff_pp']:+.1f} pp  p={dark['dry_only']['p']:.6f} {stars(dark['dry_only']['p'])}
    excluding impaired    {dark['sober_only']['diff_pp']:+.1f} pp  p={dark['sober_only']['p']:.6f} {stars(dark['sober_only']['p'])}
    placebo: right turns  {dark['placebo']['right']['diff_pp']:+.1f} pp  p={dark['placebo']['right']['p']:.4f} {stars(dark['placebo']['right']['p'])}

  CONTROL HOUR ({C.CONTROL_HOUR}:00, light in both seasons)""")
    ctrl = dark["by_hour"].get(C.CONTROL_HOUR)
    if ctrl:
        print(f"    left-turn ratio {ctrl['left_ratio']:.2f}x  "
              f"(no darkness contrast, so no effect expected)")

    print(f"""
  MECHANISM
    left-turn crashes citing 'failed to yield while turning left'
      at flashing yellow (permissive by definition) {mech['calibration']['failed_to_yield_pct']:.0f}%
      at all signals                                 {mech['overall']['failed_to_yield_pct']:.0f}%
      6-8pm specifically                             {mech['contrast_hours']['failed_to_yield_pct']:.0f}%
      (citing a disregarded signal, 6-8pm:           {mech['contrast_hours']['ran_red_pct']:.0f}%)

  NOT SHOWN
    the effect is NOT demonstrably confined to permissive intersections""")
    conc = mech["concentration"]
    if conc.get("testable"):
        print(f"      groups indistinguishable, p={conc['p']:.2f}")
        print(f"      and the test cannot work: protected intersections produce too few")
        print(f"      left-turn crashes to be classified at all")

    if sig.get("available"):
        t = sig["types"]
        print(f"""
  SIGNAL INSTALLATIONS ({sig['n_sites']} sites, rates per site-year)
    right-angle {t['angle']['rate_pre']:.2f} -> {t['angle']['rate_post']:.2f}  ({t['angle']['rate_change_pct']:+.0f}%)
    rear-end    {t['rear']['rate_pre']:.2f} -> {t['rear']['rate_post']:.2f}  ({t['rear']['rate_change_pct']:+.0f}%)
    left-turn   {t['left']['rate_pre']:.2f} -> {t['left']['rate_post']:.2f}  ({t['left']['rate_change_pct']:+.0f}%)
    (frequency change is NOT reported: regression to the mean)""")

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

    if sig.get("available"):
        # signalisation.csv — one row per intersection with a known signal installation
        # date, at least 1 year of crash data on both sides of the install, and a 60-day
        # buffer excluded around the install date (construction, driver adjustment).
        # Drawn from the before/after signalisation analysis. Columns:
        #
        # intersection       normalised street-name pair
        # installed          date the signal became operational
        # n_pre              raw crash count before installation
        # n_post             raw crash count after installation
        # years_pre          years of data before installation (after buffer exclusion)
        # years_post         years of data after installation (after buffer exclusion)
        # angle_pre          right-angle crash share before (%) — expected to fall
        # angle_post         right-angle crash share after (%)
        # angle_rate_pre     right-angle crashes per year before
        # angle_rate_post    right-angle crashes per year after
        # rear_rate_pre      rear-end crashes per year before — expected to rise
        # rear_rate_post     rear-end crashes per year after
        # left_rate_pre      left-turn crashes per year before
        # left_rate_post     left-turn crashes per year after
        # total_rate_pre     all crashes per year before
        # total_rate_post    all crashes per year after
        pd.DataFrame(sig["sites"]).to_csv(
            C.OUTPUT_DIR / "signalisation.csv", index=False)

    report.write_json(dark, mech, sig)
    page = report.render(dark, mech, sig, funnel)

    written = [str(page.relative_to(C.ROOT)), "output/results.json",
               "output/hourly.csv", "output/intersections.csv"]
    if sig.get("available"):
        written.append("output/signalisation.csv")
    print("\n  WROTE")
    for w in written:
        print(f"    {w}")
    print("\n  Preview the page:  cd docs && python -m http.server 8000\n")


if __name__ == "__main__":
    main()
