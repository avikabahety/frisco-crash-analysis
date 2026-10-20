"""Frisco results page: the words.

Charts, tables, styling, the header and the footer come from src/report.py; this
file holds only what is written for Frisco. Numbers are filled in from the
analysis results.
"""

import config as C
from src import report as R

# Hours where light conditions change mid-hour, left unlabelled in the hour table
# (Frisco: summer sunrise ~6:15am, winter sunrise ~7:25am, winter sunset ~5:25pm).
TRANSITION_HOURS = (6, 7, 17)


def render(dark, mech, funnel, top):
    c = dark["contrast"]
    wi = dark["within_intersection"]
    conc = mech["concentration"]
    y0, y1 = dark["span"]["start_year"], dark["span"]["end_year"]
    span = f"{y0}&ndash;{y1}"
    win_days = dark["season_days"]["winter"]
    sum_days = dark["season_days"]["summer"]

    r = R.window_rates(dark)
    day_w_rate, day_s_rate = r["day_w"], r["day_s"]
    eve_w_rate, eve_s_rate = r["eve_w"], r["eve_s"]
    lt_w_rate, lt_s_rate = r["lt_w"], r["lt_s"]

    description = f"""Winter evening crashes at Frisco signalised
 intersections run higher than summer. Left-turn crashes drive a disproportionate
 share of that difference. An analysis of TxDOT CRIS records, {span}."""

    body = f'''<header class="hero"><div class="wrap">
  <h1>Winter evening crashes at signalised intersections run <em>measurably higher.</em></h1>
  <p class="sub">Winter evening crashes at Frisco&rsquo;s signalised intersections run
  measurably higher than summer. Left-turn crashes drive a disproportionate share of
  that difference.</p>
  <div class="figure">
    {R.chart(dark, "winter_all_rate", "summer_all_rate", "All crashes by hour of day")}
    <div class="key">
      <span><i style="background:var(--amber)"></i>winter (Nov&ndash;Feb)</span>
      <span><i style="background:var(--sky)"></i>summer (May&ndash;Aug)</span>
    </div>
  </div>
</div></header>

<main class="wrap">

  <section class="sec">
    <h2><span class="eye">the numbers</span>Zooming in on the 6&ndash;8pm window</h2>
    <p>Overall crash rates are nearly equal across seasons. The gap opens at
    6&ndash;8pm &mdash; when winter is dark and summer is still light &mdash; and left-turn
    crashes account for a disproportionate share of it.</p>
    <table class="tab">
      <thead><tr>
        <th style="text-align:left">Crashes per 1,000 days</th>
        <th>Winter</th><th>Summer</th>
        <th>Winter&thinsp;/&thinsp;Summer ratio</th>
      </tr></thead>
      <tbody>
        <tr>
          <td>All crashes &mdash; full day (6am&ndash;10pm)</td>
          <td class="m">{day_w_rate:.0f}</td><td class="m">{day_s_rate:.0f}</td>
          <td class="m">{day_w_rate / day_s_rate:.2f}&times;</td>
        </tr>
        <tr>
          <td>All crashes &mdash; 6&ndash;8pm window</td>
          <td class="m">{eve_w_rate:.0f}</td><td class="m">{eve_s_rate:.0f}</td>
          <td class="m">{eve_w_rate / eve_s_rate:.2f}&times;</td>
        </tr>
        <tr class="sig">
          <td>Left-turn crashes &mdash; 6&ndash;8pm window</td>
          <td class="m">{lt_w_rate:.0f}</td><td class="m">{lt_s_rate:.0f}</td>
          <td class="m">{lt_w_rate / lt_s_rate:.2f}&times;</td>
        </tr>
      </tbody>
    </table>
  </section>

  <section class="sec">
    <h2><span class="eye">crash types</span>Left-turn crashes stand out in the
    evening window</h2>
    <p>The chart below shows each crash type's share of that hour's crashes, winter
    minus summer &mdash; positive values mean a bigger share in winter, negative means
    a bigger share in summer, zero means no difference. In the evening hours where
    winter is dark and summer is still light, left-turn crashes show a pronounced
    positive difference.</p>
    <div class="figure">
      {R.chart_type_diff(dark)}
    </div>
    <p class="cap" style="margin-top:12px">To understand the crash type mix chart,
    here is an example: 7pm: right-angle crashes made up 19 of 151 winter crashes
    that hour (12.6%) versus 26 of 98 summer crashes (26.5%) &mdash; a difference of
    &minus;13.9 percentage points, the point plotted for right-angle at 7pm above.
    This measures each type's share of that hour's crash mix, not how often it
    happens.</p>
    <p style="margin-top:18px"><b>Same comparison, as a rate ratio:</b> The chart
    below shows crash type (left-turn, right-angle and rear-end), plotted as a
    winter&thinsp;/&thinsp;summer rate ratio. Right-turn is left off this particular
    chart: its per-hour counts are small so one crash can swing its ratio
    several-fold, which would stretch the shared scale and hide the other three
    lines' real signal &mdash; but right-turn ratio is still shown in full in the
    table below. A gap in a line means too few crashes that hour in one season for a
    ratio to be defined.</p>
    <div class="figure">
      {R.chart_type_ratio(dark)}
    </div>
    <p style="margin-top:18px">At 6&ndash;8pm, left-turn crashes run at
    {lt_w_rate:.0f}&nbsp;per 1,000 winter days versus {lt_s_rate:.0f}&nbsp;per
    1,000 summer days &mdash; a rate ratio of {c['ratio']:.2f}&times;
    (95%&nbsp;CI&nbsp;{c['lo']:.2f}&ndash;{c['hi']:.2f}). Those hours are dark in
    winter and light in summer.</p>
    <p style="margin-top:18px">The same 6&ndash;8pm window, all five crash types
    side by side:</p>
    <table class="tab">
      <thead><tr>
        <th style="text-align:left">Crashes per 1,000 days &mdash; 6&ndash;8pm window</th>
        <th>Winter</th><th>Summer</th>
        <th>Winter&thinsp;/&thinsp;Summer ratio</th>
      </tr></thead>
      <tbody>
        <tr class="sig">
          <td>Left-turn</td>
          <td class="m">{lt_w_rate:.0f}</td><td class="m">{lt_s_rate:.0f}</td>
          <td class="m">{c['ratio']:.2f}&times;</td>
        </tr>
        <tr>
          <td>Right-turn</td>
          <td class="m">{c['winter_right'] / win_days * 1000:.0f}</td>
          <td class="m">{c['summer_right'] / sum_days * 1000:.0f}</td>
          <td class="m">{R.fmt_ratio(c['right_ratio'])}</td>
        </tr>
        <tr>
          <td>Right-angle</td>
          <td class="m">{c['winter_angle'] / win_days * 1000:.0f}</td>
          <td class="m">{c['summer_angle'] / sum_days * 1000:.0f}</td>
          <td class="m">{R.fmt_ratio(c['angle_ratio'])}</td>
        </tr>
        <tr>
          <td>Rear-end</td>
          <td class="m">{c['winter_rear'] / win_days * 1000:.0f}</td>
          <td class="m">{c['summer_rear'] / sum_days * 1000:.0f}</td>
          <td class="m">{R.fmt_ratio(c['rear_ratio'])}</td>
        </tr>
        <tr>
          <td>Other</td>
          <td class="m">{c['winter_other'] / win_days * 1000:.0f}</td>
          <td class="m">{c['summer_other'] / sum_days * 1000:.0f}</td>
          <td class="m">{R.fmt_ratio(c['other_ratio'])}</td>
        </tr>
      </tbody>
    </table>
    <p class="cap">The "other" category includes single-vehicle crashes,
    same-direction sideswipes, and other less common collision patterns such as two
    vehicles both turning left, or a left-turning vehicle crashing into an oncoming
    right-turning vehicle.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">comparison</span>The pattern is most prominent when light conditions differ</h2>
    <p class="lede">Sunset in Frisco falls around 5:25pm in December and 8:35pm in
    June; sunrise around 7:25am in December and 6:15am in June. The chart covers 6am
    to 10pm, with two windows where winter is dark and summer is light: around 7am and
    from 6&ndash;8pm.</p>
    <p>Outside those windows winter and summer left-turn crashes track closely &mdash;
    at midday both seasons are light, after 9pm both are dark. A seasonal factor
    unrelated to light &mdash; school-term traffic, holiday driving, winter road
    conditions &mdash; would be expected to affect those hours too. It does not.</p>
    <div class="figure">
      {R.chart(dark)}
      <div class="key">
        <span><i style="background:var(--amber)"></i>winter (Nov&ndash;Feb)</span>
        <span><i style="background:var(--sky)"></i>summer (May&ndash;Aug)</span>
      </div>
    </div>
    <div class="figure" style="margin-top:16px">
      {R.chart(dark, "winter_right_rate", "summer_right_rate", "Right-turn crashes by hour of day")}
      <div class="key">
        <span><i style="background:var(--amber)"></i>winter (Nov&ndash;Feb)</span>
        <span><i style="background:var(--sky)"></i>summer (May&ndash;Aug)</span>
      </div>
    </div>
    <div class="figure" style="margin-top:16px">
      {R.chart(dark, "winter_angle_rate", "summer_angle_rate", "Right-angle crashes by hour of day")}
      <div class="key">
        <span><i style="background:var(--amber)"></i>winter (Nov&ndash;Feb)</span>
        <span><i style="background:var(--sky)"></i>summer (May&ndash;Aug)</span>
      </div>
    </div>
    <div class="figure" style="margin-top:16px">
      {R.chart(dark, "winter_rear_rate", "summer_rear_rate", "Rear-end crashes by hour of day")}
      <div class="key">
        <span><i style="background:var(--amber)"></i>winter (Nov&ndash;Feb)</span>
        <span><i style="background:var(--sky)"></i>summer (May&ndash;Aug)</span>
      </div>
    </div>
    <p style="margin-top:28px">Below is the same comparison, broken out by crash type,
    in tabular format.</p>
    <div style="overflow-x:auto">
    <table class="tab">
      <thead>
        <tr>
          <th rowspan="2">Hour</th>
          <th colspan="3">Left-turn</th>
          <th colspan="3" class="grp">Right-turn</th>
          <th colspan="3" class="grp">Right-angle</th>
          <th colspan="3" class="grp">Rear-end</th>
          <th rowspan="2" class="grp">All-crash<br>ratio</th>
          <th rowspan="2"></th>
        </tr>
        <tr>
          <th style="text-align:right">Winter</th><th>Summer</th><th>Ratio</th>
          <th class="grp">Winter</th><th>Summer</th><th>Ratio</th>
          <th class="grp">Winter</th><th>Summer</th><th>Ratio</th>
          <th class="grp">Winter</th><th>Summer</th><th>Ratio</th>
        </tr>
      </thead>
      <tbody>{R.hour_rows(dark, TRANSITION_HOURS)}</tbody>
    </table>
    </div>
    <p class="cap">Winter and summer columns are crashes per 1,000 season-days, not
    raw counts &mdash; that keeps every type directly comparable despite winter and
    summer covering a different number of calendar days. Ratios are
    winter&thinsp;/&thinsp;summer.</p>
    <p class="cap">6am, 7am, and 5pm are unlabelled: light conditions change
    mid-hour at those times and a single label would misrepresent part of each hour.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">robustness</span>Checks performed</h2>
    <p>Each of the following would be expected to remove the difference if the stated
    alternative explanation held. The observed difference persists in each case.</p>
    <ul class="checks">
      <li><span class="mark">&mdash;</span><div>
        <b>Dry pavement only.</b> Winter is both darker and wetter. Restricting to
        crashes where the officer recorded dry road surface (from the CRIS surface
        condition field) leaves the difference unchanged, ruling out road conditions
        as an explanation.
        <span class="det">dry pavement only: {dark['dry_only']['diff_pp']:+.1f}&nbsp;pp,
        p&nbsp;&lt;&nbsp;0.001</span>
      </div></li>
      <li><span class="mark">&mdash;</span><div>
        <b>Right-turn comparison.</b> If night driving were generally more difficult,
        other turning movements would shift similarly. Right-turn crashes show no
        change in the same window, making a general night-driving explanation unlikely.
        <span class="det">left-turn {dark['placebo']['left']['diff_pp']:+.1f}&nbsp;pp
        &middot; right-turn {dark['placebo']['right']['diff_pp']:+.1f}&nbsp;pp
        &middot; right-angle {dark['placebo']['angle']['diff_pp']:+.1f}&nbsp;pp</span>
      </div></li>
      <li><span class="mark">&mdash;</span><div>
        <b>Rates, not counts.</b> Left-turn crashes are compared as rates per calendar
        day rather than as shares of total crashes, so a shrinking denominator cannot
        produce a spurious rise.
        <span class="det">6pm: {dark['by_hour'].get(18, {}).get('left_ratio', 0):.2f}&times;
        left-turn vs {dark['by_hour'].get(18, {}).get('all_ratio', 0):.2f}&times;
        all crashes</span>
      </div></li>
    </ul>
    <p class="cap">The association also survives stratification by intersection
    (Mantel&ndash;Haenszel OR&nbsp;{wi['odds_ratio']:.2f} across {wi['n_strata']}
    intersections, {wi['agree']}/{wi['n_strata']} moving the predicted way) and
    exclusion of impaired-driver crashes
    ({dark['sober_only']['diff_pp']:+.1f}&nbsp;pp, impairment recorded in
    {dark['sober_only']['impaired_pct']:.1f}% of crashes in these hours).</p>
  </section>

  <section class="sec">
    <h2><span class="eye">where to look</span>Intersections worth a closer look</h2>
    <p>These intersections show the largest observed gap between winter and summer
    left-turn crashes during the 6&ndash;8pm window. Two of these intersections are on
    SH121 and are likely managed by the City of Plano. The remaining two intersections
    represent a starting point for Frisco&rsquo;s evaluation of whether any
    countermeasure is appropriate to reduce winter left-turn crashes.</p>
    <table class="tab">
      <thead><tr>
        <th>Intersection</th>
        <th>Winter crashes</th><th>Summer crashes</th>
        <th>Rate gap</th><th>Rate ratio [95%&nbsp;CI]</th>
        <th>Failed to yield</th>
      </tr></thead>
      <tbody>{R.intersection_contrast_rows(dark)}</tbody>
    </table>
    <p class="cap">Crashes are counts over {span} during 6&ndash;8pm only. Rate gap is
    winter minus summer crashes per 1,000 season-days. Failed-to-yield column shows
    the share of left-turn crashes between 6&ndash;10pm where the officer recorded
    dark light conditions, citing failure to yield while turning left &mdash; the
    officer-recorded signature of a permissive left-turn phase. Sample sizes at individual intersections are small
    and confidence intervals are wide.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">limitations</span>What this analysis does not establish</h2>
    <div class="notclaim">
      <h3>These bound the interpretation of everything above.</h3>
      <ul>
        <li><b>Exposure is unknown.</b> The number of left turns attempted after dark
        is not available. Traffic volumes are lower at night, so the risk per turn
        attempted is likely higher than these figures indicate, making the estimates
        conservative.</li>
        <li><b>Reportable crashes only.</b> CRIS contains crashes for which an officer
        filed a CR-3: injury, death, or $1,000+ in property damage. Minor crashes and
        those without police response are not included.</li>
        <li><b>Whether the increase concentrates at specific intersection types is not
        confirmed.</b> The analysis attempted to compare intersections that appear more
        permissive against those that appear less so; the two groups are not
        statistically distinguishable
        (p&nbsp;=&nbsp;{conc.get('p', float('nan')):.2f}). Intersections with
        protected-only phasing produce few left-turn crashes and rarely meet the
        minimum count needed to be classified, so the comparison is inherently
        limited.</li>
      </ul>
    </div>
  </section>

  <section class="sec">
    <h2><span class="eye">for reference</span>Signalized intersections with the most crashes overall</h2>
    <p>For background context, the table below ranks Frisco's signalized
    intersections by total crash count of any type, all hours and seasons combined,
    {span}.</p>
    <div style="overflow-x:auto">
    <table class="tab">
      <thead><tr>
        <th>Intersection</th>
        <th>Total</th><th>Left-turn</th><th>Right-turn</th>
        <th>Right-angle</th><th>Rear-end</th><th>Other</th>
      </tr></thead>
      <tbody>{R.top_rows(top)}</tbody>
    </table>
    </div>
    <p class="cap">Not every intersection listed here is necessarily maintained by
    the City of Frisco. Several sit on state highways (US380, SH121) or roads shared
    with neighboring cities, which may fall under TxDOT's or another jurisdiction's
    authority.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">method</span>How the data was cut</h2>
    <p>All crash records held by TxDOT for Frisco, {span}, narrowed to those that can
    be placed at a named intersection at a known time.</p>
    <table class="tab">
      <thead><tr><th>Records</th><th style="text-align:left">Step</th></tr></thead>
      <tbody>{R.funnel_rows(funnel)}</tbody>
    </table>
    <p class="cap">Freeway mainlane crashes are excluded: none carry a cross street and
    their crash-type distribution is characteristic of a freeway, not an intersection.
    Driveway-access crashes are excluded. The analyses above use
    the signalised subset, since left-turn phasing exists only at a signal.</p>
    <p><a href="{C.REPO_URL}" style="color:#B87A18;font-weight:600;">Code, data and
    full method &rarr;</a></p>
  </section>

</main>

'''

    return R.write_page(R.page(body, description, span))
