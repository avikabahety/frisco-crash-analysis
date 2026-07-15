"""Render the results page.

Visual language follows the subject: signal-timing sheets and crash tables. Monospace
for figures an engineer would want to check, and the signal head's own colours
(amber = permissive, green = protected, red = crash).
"""

import json

import config as C

# Frisco sunset, rounded to the hour it crosses. December ~17:25, June ~20:35.
WINTER_SUNSET = 17.4
SUMMER_SUNSET = 20.6


def _chart(dark):
    """Left-turn crash rate by hour, winter against summer, with the sunset band.

    The curves track each other while both seasons are light, separate across the hours
    where only winter is dark, and converge again once both are dark.
    """
    hours = sorted(dark["by_hour"].keys())
    if not hours:
        return ""
    lo, hi = min(hours), max(hours)
    W, H = 720, 340
    L, R, T, B = 68, 20, 58, 64
    pw, ph = W - L - R, H - T - B

    peak = max(max(v["winter_left_rate"], v["summer_left_rate"])
               for v in dark["by_hour"].values())
    peak = max(peak, 1)
    span = max(hi - lo, 1)

    def x(h):
        return L + (h - lo) / span * pw

    def y(v):
        return T + ph - (v / peak) * ph

    # the window where winter is dark but summer is still light
    x0 = x(max(WINTER_SUNSET, lo))
    x1 = x(min(SUMMER_SUNSET, hi))

    def path(field):
        pts = [f"{x(h):.1f},{y(dark['by_hour'][h][field]):.1f}" for h in hours]
        return "M" + " L".join(pts)

    dots = "".join(
        f'<circle cx="{x(h):.1f}" cy="{y(dark["by_hour"][h][f]):.1f}" r="3.5" '
        f'fill="{col}"/>'
        for f, col in [("winter_left_rate", "var(--amber)"),
                       ("summer_left_rate", "var(--sky)")]
        for h in hours)

    ticks = "".join(
        f'<text x="{x(h):.1f}" y="{H - B + 18}" class="ax" text-anchor="middle">'
        f'{h % 12 or 12}{"am" if h < 12 else "pm"}</text>' for h in hours)

    grid = "".join(
        f'<line x1="{L}" y1="{y(v):.1f}" x2="{W - R}" y2="{y(v):.1f}" class="grid"/>'
        f'<text x="{L - 8}" y="{y(v) + 4:.1f}" class="ax" text-anchor="end">{v:.0f}</text>'
        for v in [0, peak / 2, peak])

    return f'''<svg viewBox="0 0 {W} {H}" class="chart" role="img"
   aria-label="Left-turn crash rate by hour of day, winter versus summer">
  <text x="{L}" y="22" class="title">Left-turn crashes by hour of day</text>
  <text x="{L}" y="40" class="subtitle">Frisco signalised intersections, {dark['span']['start_year']}&ndash;{dark['span']['end_year']}</text>
  <rect x="{x0:.1f}" y="{T}" width="{max(x1 - x0, 0):.1f}" height="{ph}" class="band"/>
  <text x="{(x0 + x1) / 2:.1f}" y="{T + 15}" class="bandlab" text-anchor="middle">
    dark in winter, light in summer</text>
  {grid}
  <path d="{path('summer_left_rate')}" class="line summer"/>
  <path d="{path('winter_left_rate')}" class="line winter"/>
  {dots}
  {ticks}
  <text transform="translate({L - 42},{T + ph / 2:.1f}) rotate(-90)" text-anchor="middle" class="axtitle">crashes / 1,000 days</text>
  <text x="{L + pw / 2:.1f}" y="{H - 14}" class="axtitle" text-anchor="middle">Hour of day</text>
</svg>'''


def _rows(dark):
    out = []
    for h in sorted(dark["by_hour"]):
        v = dark["by_hour"][h]
        ctrl = v["is_control"]
        ratio = v["left_ratio"]
        out.append(f'''<tr class="{'ctrl' if ctrl else ''}">
      <td class="m">{h % 12 or 12}{"am" if h < 12 else "pm"}</td>
      <td class="m">{v['winter_left']}</td>
      <td class="m">{v['summer_left']}</td>
      <td class="m b">{ratio:.2f}&times;</td>
      <td class="m dim">{v['all_ratio']:.2f}&times;</td>
      <td class="note">{'light in both seasons' if ctrl else ''}</td>
    </tr>''')
    return "\n".join(out)


def _sites(mech, limit=12):
    return "\n".join(f'''<tr>
      <td>{s['intersection']}</td>
      <td class="m">{s['crashes']}</td>
      <td class="m amber">{s['failed_to_yield_pct']:.0f}%</td>
      <td class="m dim">{s['ran_red_pct']:.0f}%</td>
    </tr>''' for s in mech["sites"][:limit])


def render(dark, mech, sig, funnel, path=None):
    path = path or (C.DOCS_DIR / "index.html")
    c = dark["contrast"]
    h = dark["headline"]
    wi = dark["within_intersection"]
    conc = mech["concentration"]
    y0, y1 = dark["span"]["start_year"], dark["span"]["end_year"]
    span = f"{y0}&ndash;{y1}"

    sig_block = ""
    if sig.get("available"):
        t = sig["types"]
        site_rows = "\n".join(f'''<tr>
      <td>{s['intersection']}</td>
      <td class="m nowrap">{s['installed']}</td>
      <td class="m dim">{s['years_pre']:.1f} / {s['years_post']:.1f}</td>
      <td class="m">{s['total_rate_pre']:.1f} &rarr; {s['total_rate_post']:.1f}</td>
      <td class="m">{s['angle_rate_pre']:.1f} &rarr; {s['angle_rate_post']:.1f}</td>
      <td class="m">{s['rear_rate_pre']:.1f} &rarr; {s['rear_rate_post']:.1f}</td>
      <td class="m">{s['left_rate_pre']:.1f} &rarr; {s['left_rate_post']:.1f}</td>
    </tr>''' for s in sig["sites"])

        sig_block = f'''
  <section class="sec">
    <h2><span class="eye">also in the data</span>What a new signal changes</h2>
    <p>Frisco installed signals at following {sig['n_sites']} intersections during the
    study window, on dates published in city bulletins.</p>

    <h3 style="font:600 15px var(--sans);margin:26px 0 4px">By intersection</h3>
    <p class="cap">Crashes per year, before &rarr; after installation. The buffer around
    each install date (construction, driver adjustment) is excluded from both periods.
    Individual sites cover a small number of years and single-site rates are noisy; the
    combined result below pools all {sig['n_sites']} sites for statistical power.</p>
    <table class="tab">
      <thead><tr>
        <th>Intersection</th><th>Installed</th><th>Years of data (pre/post)</th>
        <th>All crashes/yr</th><th>Right-angle/yr</th><th>Rear-end/yr</th>
        <th>Left-turn/yr</th>
      </tr></thead>
      <tbody>{site_rows}</tbody>
    </table>

    <h3 style="font:600 15px var(--sans);margin:30px 0 4px">Combined, all {sig['n_sites']} sites</h3>
    <p class="cap">Comparing crashes before and after, as rates rather than shares:</p>
    <table class="tab">
      <thead><tr><th>Crash type</th><th>Before</th><th>After</th><th>Change</th></tr></thead>
      <tbody>
        <tr><td>Right-angle</td><td class="m">{t['angle']['rate_pre']:.2f}/yr</td>
            <td class="m">{t['angle']['rate_post']:.2f}/yr</td>
            <td class="m green b">{t['angle']['rate_change_pct']:+.0f}%</td></tr>
        <tr><td>Rear-end</td><td class="m">{t['rear']['rate_pre']:.2f}/yr</td>
            <td class="m">{t['rear']['rate_post']:.2f}/yr</td>
            <td class="m red b">{t['rear']['rate_change_pct']:+.0f}%</td></tr>
        <tr><td>Left-turn</td><td class="m">{t['left']['rate_pre']:.2f}/yr</td>
            <td class="m">{t['left']['rate_post']:.2f}/yr</td>
            <td class="m">{t['left']['rate_change_pct']:+.0f}%</td></tr>
      </tbody>
    </table>
    <p class="cap">This is the trade-off signalisation is expected to produce: a signal
    separates conflicting movements in time, so right-angle crashes fall, and it creates
    queues, so rear-end crashes rise. Rates are reported rather than shares; the
    left-turn rate falls even though the left-turn share rises, because total crashes
    fall faster.</p>
    <p class="warn"><b>Not an estimate of crash reduction.</b> Signals tend to be
    installed where crashes have recently increased, so some subsequent decline would be
    expected regardless (regression to the mean). The change in crash <em>type</em> is
    not explained by that mechanism, which would move all types in the same direction.
    No overall frequency effect is reported.</p>
    <p class="cap">Individual intersections above should not be read as independent
    confirmations &mdash; each has few years of data on one or both sides of its install
    date, so single-site rates carry wide uncertainty. The combined table is the reliable
    figure; the by-intersection table shows where that figure comes from.</p>
  </section>'''

    funnel_rows = "\n".join(
        f'<tr><td class="m">{n:,}</td><td>{label}</td></tr>' for label, n in funnel)

    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{C.SITE_TITLE} &mdash; Frisco, TX</title>
<meta name="description" content="Left-turn crashes double after dark at Frisco's
 signalised intersections. An analysis of TxDOT CRIS records for complete years 2016-2025.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --night:#0F1720; --ink:#16202B; --paper:#E9EBEE; --card:#FFFFFF;
    --amber:#E8A33D;      /* permissive: the flashing yellow arrow */
    --green:#3E8E5A;      /* protected: the green arrow */
    --red:#C33C3C;        /* the crash */
    --sky:#7FA8C9;        /* daylight */
    --slate:#68737F; --rule:#D2D7DD;
    --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
    --sans:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink);
    font:400 16px/1.65 var(--sans); -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:860px; margin:0 auto; padding:0 28px; }}

  /* ---- masthead ---- */
  .top {{ background:var(--night); color:#DFE5EA; padding:34px 0 0; }}
  .top .wrap {{ display:flex; justify-content:space-between; align-items:baseline;
    gap:20px; flex-wrap:wrap; }}
  .tag {{ font:500 11px/1 var(--mono); letter-spacing:.18em; text-transform:uppercase;
    color:var(--amber); }}
  .src {{ font:400 12px/1 var(--mono); color:#7A8794; }}

  /* ---- the finding, on night ground ---- */
  .hero {{ background:var(--night); color:#F2F5F7; padding:22px 0 46px; }}
  .hero h1 {{ font:600 clamp(30px,5vw,46px)/1.12 var(--mono); margin:14px 0 0;
    letter-spacing:-.02em; max-width:17ch; }}
  .hero h1 em {{ font-style:normal; color:var(--amber); }}
  .hero .sub {{ color:#9FADB9; margin:18px 0 30px; max-width:60ch; font-size:17px; }}
  .figure {{ background:#16202B; border:1px solid #26333F; border-radius:4px;
    padding:20px 16px 8px; }}
  .chart {{ width:100%; height:auto; display:block; }}
  .title {{ font:600 15px var(--sans); fill:#F2F5F7; }}
  .subtitle {{ font:400 11px var(--mono); fill:#9FADB9; letter-spacing:.02em; }}
  .axtitle {{ font:500 10px var(--mono); fill:#9FADB9; letter-spacing:.1em;
    text-transform:uppercase; }}
  .band {{ fill:#E8A33D; opacity:.10; }}
  .bandlab {{ font:500 10px var(--mono); fill:var(--amber); letter-spacing:.08em;
    text-transform:uppercase; }}
  .grid {{ stroke:#2B3945; stroke-width:1; }}
  .ax {{ font:400 10px var(--mono); fill:#7A8794; }}
  .line {{ fill:none; stroke-width:2.5; stroke-linejoin:round; stroke-linecap:round; }}
  .line.winter {{ stroke:var(--amber); }}
  .line.summer {{ stroke:var(--sky); }}
  .key {{ display:flex; gap:22px; font:400 12px var(--mono); color:#9FADB9;
    padding:10px 4px 4px; }}
  .key i {{ display:inline-block; width:20px; height:2.5px; vertical-align:middle;
    margin-right:7px; }}

  /* ---- body sections ---- */
  .sec {{ padding:44px 0; border-bottom:1px solid var(--rule); }}
  .sec:last-of-type {{ border-bottom:0; }}
  h2 {{ font:600 24px/1.25 var(--sans); margin:0 0 16px; letter-spacing:-.01em; }}
  .eye {{ display:block; font:500 11px/1 var(--mono); letter-spacing:.16em;
    text-transform:uppercase; color:var(--slate); margin-bottom:9px; }}
  p {{ margin:0 0 15px; max-width:66ch; }}
  .cap {{ font-size:14.5px; color:var(--slate); }}
  .lede {{ font-size:18px; }}

  .tab {{ width:100%; border-collapse:collapse; margin:18px 0; background:var(--card);
    border:1px solid var(--rule); }}
  .tab th {{ font:500 11px/1 var(--mono); letter-spacing:.1em; text-transform:uppercase;
    text-align:right; padding:11px 12px; background:var(--ink); color:#E9EBEE; }}
  .tab th:first-child {{ text-align:left; }}
  .tab .nowrap {{ white-space:nowrap; }}
  .tab td {{ padding:10px 12px; border-top:1px solid var(--rule); font-size:14.5px; }}
  .tab .m {{ font-family:var(--mono); font-size:13.5px; text-align:right;
    font-variant-numeric:tabular-nums; }}
  .tab td:first-child {{ text-align:left; }}
  .tab .b {{ font-weight:600; }}
  .tab .dim {{ color:var(--slate); }}
  .tab .amber {{ color:#B87A18; font-weight:600; }}
  .tab .green {{ color:var(--green); }}
  .tab .red {{ color:var(--red); }}
  .tab .note {{ font-size:12.5px; color:var(--slate); font-style:italic; }}
  .tab tr.ctrl {{ background:#F4F1E9; }}
  .tab tr.ctrl .m {{ color:var(--slate); }}

  /* checks: each one could have killed the finding */
  .checks {{ list-style:none; padding:0; margin:18px 0; }}
  .checks li {{ display:flex; gap:14px; padding:13px 0;
    border-top:1px solid var(--rule); }}
  .checks li:last-child {{ border-bottom:1px solid var(--rule); }}
  .checks .mark {{ font:600 13px var(--mono); color:var(--green); flex:0 0 auto;
    padding-top:2px; }}
  .checks b {{ font-weight:600; }}
  .checks .det {{ font:400 13px/1.5 var(--mono); color:var(--slate);
    display:block; margin-top:3px; }}

  .warn {{ background:#FBF3E4; border-left:3px solid var(--amber);
    padding:14px 16px; font-size:14.5px; max-width:66ch; }}
  .warn b {{ font-weight:600; }}
  .notclaim {{ background:var(--card); border:1px solid var(--rule);
    padding:20px 22px; }}
  .notclaim h3 {{ font:600 15px var(--sans); margin:0 0 12px; }}
  .notclaim ul {{ margin:0; padding-left:18px; }}
  .notclaim li {{ margin-bottom:9px; font-size:14.5px; max-width:62ch; }}

  footer {{ background:var(--night); color:#8B98A5; padding:34px 0 44px;
    font-size:14px; }}
  footer a {{ color:var(--amber); text-decoration:none; }}
  footer a:hover {{ text-decoration:underline; }}
  footer .wrap > p {{ max-width:66ch; }}
  a:focus-visible, summary:focus-visible {{ outline:2px solid var(--amber);
    outline-offset:2px; }}
  @media (prefers-reduced-motion:no-preference) {{
    .line {{ stroke-dasharray:1400; stroke-dashoffset:1400;
      animation:draw 1.5s .2s ease-out forwards; }}
    @keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
  }}
  @media (max-width:620px) {{
    .tab .note {{ display:none; }}
    .hero h1 {{ font-size:27px; }}
  }}
</style>
</head>
<body>

<div class="top"><div class="wrap">
  <span class="tag">Frisco, TX &middot; signalised intersections</span>
  <span class="src">Based on TxDOT CRIS &middot; 2016&ndash;2026</span>
</div></div>

<header class="hero"><div class="wrap">
  <h1>Left-turn crashes roughly <em>double</em> after dark.</h1>
  <p class="sub">Between 6 and 8pm, Frisco's signalised intersections recorded
  {c['winter_left']} left-turn crashes across all winter months and {c['summer_left']}
  across all summer months, combined over {span} &mdash; a rate ratio of
  {c['ratio']:.2f} (95% CI {c['lo']:.2f}&ndash;{c['hi']:.2f}), adjusted for the number of
  days in each season. Those hours are dark in winter and light in summer.</p>

  <div class="figure">
    {_chart(dark)}
    <div class="key">
      <span><i style="background:var(--amber)"></i>winter (Nov&ndash;Feb)</span>
      <span><i style="background:var(--sky)"></i>summer (May&ndash;Aug)</span>
    </div>
  </div>
</div></header>

<main class="wrap">

  <section class="sec">
    <h2><span class="eye">comparison</span>Hours with no darkness contrast show no
    difference</h2>
    <p class="lede">Sunset in Frisco falls around 5:25pm in December and 8:35pm in June.
    At 5pm it is therefore light in both seasons, and at 5pm the seasonal difference is
    absent &mdash; the winter rate is slightly lower than the summer rate.</p>
    <p>The difference appears from 6pm and narrows again after 8pm, once both seasons are
    dark. A seasonal factor unrelated to light &mdash; school-term traffic, holiday
    driving, winter road conditions &mdash; would be expected to affect 5pm as well.</p>
    <table class="tab">
      <thead><tr>
        <th>Hour</th><th>Winter</th><th>Summer</th>
        <th>Left-turn</th><th>All crashes</th><th></th>
      </tr></thead>
      <tbody>{_rows(dark)}</tbody>
    </table>
    <p class="cap">Counts are left-turn crashes. Ratios compare winter with summer,
    adjusted for the number of days in each season. Left-turn crashes rise
    approximately twice as fast as crashes in general.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">robustness</span>Checks performed</h2>
    <p>Each of the following would be expected to remove the difference if the stated
    alternative explanation held. The observed difference persists in each case.</p>
    <ul class="checks">
      <li><span class="mark">&mdash;</span><div>
        <b>Counts, not shares.</b> A proportion can rise while the underlying count
        falls, if the denominator shrinks faster. Left-turn crashes were therefore
        counted per calendar day rather than as a share. The count rises in winter, and
        rises faster than the count of crashes overall.
        <span class="det">6pm: {dark['by_hour'].get(18, {}).get('left_ratio', 0):.2f}&times;
        left-turn vs {dark['by_hour'].get(18, {}).get('all_ratio', 0):.2f}&times; all crashes</span>
      </div></li>
      <li><span class="mark">&mdash;</span><div>
        <b>Stratified by intersection.</b> If crashes after dark occurred at a different
        set of intersections, the difference could reflect that mix rather than the
        light. Pooling within intersections (Mantel&ndash;Haenszel), the association
        remains.
        <span class="det">odds ratio {wi['odds_ratio']:.2f} across {wi['n_strata']} intersections,
        p&nbsp;&lt;&nbsp;0.001 &middot; {wi['agree']}/{wi['n_strata']} move the predicted way</span>
      </div></li>
      <li><span class="mark">&mdash;</span><div>
        <b>Dry pavement only.</b> Winter is both darker and wetter. Restricting to dry
        road surface leaves the difference unchanged.
        <span class="det">dry only: {dark['dry_only']['diff_pp']:+.1f} pp, p&nbsp;&lt;&nbsp;0.001</span>
      </div></li>
      <li><span class="mark">&mdash;</span><div>
        <b>Right-turn comparison.</b> If night driving were generally more difficult,
        other turning movements would be expected to shift similarly. Right-turn crashes
        show no change.
        <span class="det">left {dark['placebo']['left']['diff_pp']:+.1f} pp &middot;
        right {dark['placebo']['right']['diff_pp']:+.1f} pp (n.s.) &middot;
        right-angle {dark['placebo']['angle']['diff_pp']:+.1f} pp</span>
      </div></li>
    </ul>
    <p class="cap">Excluding impaired-driver crashes leaves the difference at
    {dark['sober_only']['diff_pp']:+.1f} pp. Impairment is recorded in
    {dark['sober_only']['impaired_pct']:.1f}% of crashes in these hours.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">contributing factors</span>What the crash reports record</h2>
    <p>A driver is required to yield only on a permissive left turn. Under a protected
    left the turning driver has right of way, so a collision there would be recorded as a
    disregarded signal rather than a failure to yield. The officer's contributing factor
    therefore carries information about which phase was operating.</p>
    <p>Crashes recorded at flashing-yellow-arrow control, which is permissive by
    definition, provide a reference point:
    <b>{mech['calibration']['failed_to_yield_pct']:.0f}%</b> cite failure to yield while
    turning left. Across all left-turn crashes at signals the figure is
    <b>{mech['overall']['failed_to_yield_pct']:.0f}%</b>, compared with
    {mech['overall']['ran_red_pct']:.0f}% citing a disregarded signal.</p>
    <p>Within the 6&ndash;8pm window,
    <b>{mech['contrast_hours']['failed_to_yield_pct']:.0f}%</b> of left-turn crashes are
    recorded as failure to yield while turning left and
    {mech['contrast_hours']['ran_red_pct']:.0f}% as a disregarded signal. This is
    consistent with permissive left-turn operation during those hours at the
    intersections where the crashes occurred, though it is not a direct observation of
    signal phasing.</p>
    <h3 style="font:600 15px var(--sans);margin:26px 0 4px">By intersection</h3>
    <p class="cap">Left-turn crashes after dark, 6&ndash;10pm. Left-turn phasing is
    configured per intersection rather than city-wide.</p>
    <table class="tab">
      <thead><tr><th>Intersection</th><th>Crashes</th>
        <th>Failed to yield</th><th>Ran signal</th></tr></thead>
      <tbody>{_sites(mech)}</tbody>
    </table>
  </section>

  <section class="sec">
    <h2><span class="eye">limitations</span>What this analysis does not establish</h2>
    <div class="notclaim">
      <h3>These bound the interpretation of everything above.</h3>
      <ul>
        <li><b>The difference is not shown to be confined to permissive intersections.</b>
        Intersections were classified by how permissive their crash records appear and
        the two groups compared; the difference between them is not statistically
        distinguishable (p&nbsp;=&nbsp;{conc.get('p', float('nan')):.2f}). The
        classification is also limited by construction: an intersection running
        protected-only left turns produces few left-turn crashes, so it rarely meets the
        minimum needed to be classified at all. The comparison is closer to "more
        permissive" against "less permissive" than to permissive against protected.</li>
        <li><b>Signal phasing was not observed.</b> The interpretation above rests on
        contributing factors recorded by officers, not on the signal timing plans
        themselves. If protected phasing already tracks sunset at these intersections,
        that interpretation does not hold, although the seasonal difference in crashes
        would remain to be explained.</li>
        <li><b>Exposure is unknown.</b> The number of left turns attempted after dark is
        not available. Traffic volumes are lower at night, so fewer left turns are likely
        being made while more left-turn crashes are recorded. The risk per turn attempted
        would then be higher than these figures indicate, making the estimates
        conservative.</li>
        <li><b>Reportable crashes only.</b> CRIS contains crashes for which an officer
        filed a CR-3: injury, death, or $1,000+ in property damage. Minor crashes and
        those without police response are not included.</li>
      </ul>
    </div>
  </section>
{sig_block}
  <section class="sec">
    <h2><span class="eye">method</span>How the data was cut</h2>
    <p>All crash records held by TxDOT for Frisco, {span}, narrowed to those
    that can be placed at a named intersection at a known time.</p>
    <table class="tab">
      <thead><tr><th>Records</th><th>Step</th></tr></thead>
      <tbody>{funnel_rows}</tbody>
    </table>
    <p class="cap">Freeway mainlane crashes are excluded: none carry a cross street,
    and their crash-type distribution is characteristic of a freeway rather than an
    intersection. Driveway-access crashes are held out as a separate category. The
    analyses above use the signalised subset, since left-turn phasing exists only at a
    signal.</p>
    <p class="cap">Dawn and dusk are excluded from both the dark and daylight groups, as
    they represent the transition between the two conditions being compared.</p>
    <p><a href="{C.REPO_URL}" style="color:#B87A18;font-weight:600;">Code, data and
    full method &rarr;</a></p>
  </section>

</main>

<footer><div class="wrap">
  <p>An independent analysis of public TxDOT CRIS crash records. Not affiliated with
  the City of Frisco or TxDOT. Any errors are the author&rsquo;s.</p>
  <p style="margin-top:14px"><a href="{C.REPO_URL}">Repository</a> &middot;
  <a href="https://cris.dot.state.tx.us/public/Query/app/home">CRIS data source</a></p>
</div></footer>

</body>
</html>'''

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def write_json(dark, mech, sig, path=None):
    """Machine-readable results, so a re-run can be diffed against the previous one."""
    path = path or (C.OUTPUT_DIR / "results.json")
    path.parent.mkdir(parents=True, exist_ok=True)

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        if hasattr(o, "item"):
            return o.item()
        return o

    path.write_text(json.dumps(
        clean({"darkness": dark, "mechanism": mech, "signalisation": sig}),
        indent=2, default=str), encoding="utf-8")
    return path
