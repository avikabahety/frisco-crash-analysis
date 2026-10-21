"""Plano results page: the words.

Charts, tables, styling, the header and the footer come from src/report.py; this
file holds only what is written for Plano. Numbers are filled in from the
analysis results.
"""

import config as C
from src import report as R

# Hours where light conditions change mid-hour, left unlabeled in the hour table
# (Plano, confirmed by check_setup.py: summer sunrise ~6:15am, winter sunrise ~7:25am,
# winter sunset ~5:25pm, summer sunset ~7:50-8:40pm from May to August). Keep the
# hour-table caption below in step with this list.
TRANSITION_HOURS = (6, 7, 17, 20)


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

    description = f"""Winter evening crashes at Plano signalized
 intersections run higher than summer. Left-turn crashes drive a disproportionate
 share of that difference. An analysis of TxDOT CRIS records, {span}."""

    body = f'''<header class="hero"><div class="wrap">
  <h1>Winter evening crashes at signalized intersections run <em>measurably higher.</em></h1>
  <p class="sub">Winter evening crashes at Plano&rsquo;s signalized intersections run
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
    <h2><span class="eye">the numbers</span>Zooming in on the 6pm&ndash;8pm window</h2>
    <p>Overall crash rates are nearly equal across seasons. The gap opens at
    6pm&ndash;8pm &mdash; when winter is dark and summer is still light &mdash; and left-turn
    crashes account for a disproportionate share of it.</p>
    <table class="tab">
      <thead><tr>
        <th style="text-align:left">Crashes per 1,000 days</th>
        <th>Winter</th><th>Summer</th>
        <th>Winter&thinsp;/&thinsp;Summer ratio</th>
      </tr></thead>
      <tbody>
        <tr>
          <td>All crashes &mdash; full day (6am&ndash;11pm)</td>
          <td class="m">{day_w_rate:.0f}</td><td class="m">{day_s_rate:.0f}</td>
          <td class="m">{day_w_rate / day_s_rate:.2f}&times;</td>
        </tr>
        <tr>
          <td>All crashes &mdash; 6pm&ndash;8pm window</td>
          <td class="m">{eve_w_rate:.0f}</td><td class="m">{eve_s_rate:.0f}</td>
          <td class="m">{eve_w_rate / eve_s_rate:.2f}&times;</td>
        </tr>
        <tr class="sig">
          <td>Left-turn crashes &mdash; 6pm&ndash;8pm window</td>
          <td class="m">{lt_w_rate:.0f}</td><td class="m">{lt_s_rate:.0f}</td>
          <td class="m">{lt_w_rate / lt_s_rate:.2f}&times;</td>
        </tr>
      </tbody>
    </table>
  </section>

  <section class="sec">
    <h2><span class="eye">crash types</span>Left-turn crashes stand out in the
    evening window</h2>
    <p>The chart below shows, hour by hour, how each crash type's rate compares between
    winter and summer: above 1&times; means more crashes in winter, below 1&times; more
    in summer. Right-turn is left off this particular chart because those crashes are
    too few per hour to chart reliably, but their hourly ratios are still shown in the
    hour-by-hour table further down. A gap in a line means too few crashes that hour to
    calculate a ratio.</p>
    <div class="figure">
      {R.chart_type_ratio(dark)}
    </div>
    <p style="margin-top:18px">At 6pm&ndash;8pm, left-turn crashes run at
    {lt_w_rate:.0f}&nbsp;per 1,000 winter days versus {lt_s_rate:.0f}&nbsp;per
    1,000 summer days &mdash; a rate ratio of {c['ratio']:.2f}&times;
    (95%&nbsp;CI&nbsp;{c['lo']:.2f}&ndash;{c['hi']:.2f}). Those hours are dark in
    winter and light in summer.</p>
    <p style="margin-top:18px">The same 6pm&ndash;8pm window, all five crash types
    side by side:</p>
    <table class="tab">
      <thead><tr>
        <th style="text-align:left">Crashes per 1,000 days &mdash; 6pm&ndash;8pm window</th>
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
    <p class="lede">Sunset in Plano falls around 5:25pm in December and 8:35pm in
    June; sunrise around 7:25am in December and 6:15am in June. The chart covers 6am
    to 11pm. Winter is dark while summer is light in two windows: in the evening from
    6pm to 8pm, and briefly in the early morning before 7am. The evening window is the
    one this analysis tests; the morning window is shorter and has too few crashes for
    a reliable comparison.</p>
    <p>At midday, when both seasons are light, winter and summer left-turn crash rates
    track closely ({dark['same_light']['midday']['ratio']:.2f}&times;). After 9pm, when
    both are dark, winter runs lower than summer
    ({dark['same_light']['late']['ratio']:.2f}&times;). A seasonal factor that raises
    winter evening crashes, such as school-term traffic or holiday driving, would be
    expected to show up in those hours too; it does not.</p>
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
    winter&thinsp;/&thinsp;summer. The shaded row ({R.hour_label(C.COMPARISON_HOUR)}) is the
    comparison hour: daylight in both seasons. Each row covers the full hour, e.g.
    6pm = 6:00pm&ndash;6:59pm.</p>
    <p class="cap">6am, 7am, 5pm, and 8pm are unlabeled: light conditions change
    mid-hour at those times and a single label would misrepresent part of each hour.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">robustness</span>Checks performed</h2>
    <p>Each of the following would be expected to remove the difference if the stated
    alternative explanation held. The observed difference persists in each case.</p>
    <ul class="checks">
      <li><span class="mark">&mdash;</span><div>
        <b>Dry pavement only.</b> Winter is both darker and wetter. Restricting to
        crashes where the officer recorded a dry road surface (from the CRIS surface
        condition field) does not reduce the difference, so wet roads do not explain
        it.
        <span class="det">all surfaces: {R.signed_pp(dark['headline']['diff_pp'])}&nbsp;pp
        &middot; dry pavement only: {R.signed_pp(dark['dry_only']['diff_pp'])}&nbsp;pp</span>
      </div></li>
      <li><span class="mark">&mdash;</span><div>
        <b>Other crash types.</b> If darkness simply made all driving harder, every
        type of crash would rise by a similar amount in the 6pm&ndash;8pm window. It
        does not: left-turn crashes roughly double, right-angle crashes do not rise,
        and rear-end crashes rise only modestly.
        <span class="det">left-turn {R.fmt_ratio(c['ratio'])}
        &middot; right-angle {R.fmt_ratio(c['angle_ratio'])}
        &middot; rear-end {R.fmt_ratio(c['rear_ratio'])}
        &middot; right-turn {R.fmt_ratio(c['right_ratio'])} (few crashes)</span>
      </div></li>
    </ul>
    <p class="cap">The pattern also holds within individual intersections: among the
    {wi['n_strata']} intersections with enough crashes to compare, left turns make up a
    larger part of crashes after dark than in daylight at {wi['agree']}. It also holds
    after excluding impaired-driver crashes
    ({R.signed_pp(dark['sober_only']['diff_pp'])}&nbsp;pp, impairment recorded in
    {dark['sober_only']['impaired_pct']:.1f}% of crashes in these hours).</p>
  </section>

  <section class="sec">
    <h2><span class="eye">where to look</span>Intersections worth a closer look</h2>
    <p>These intersections show the largest observed gap between winter and summer
    left-turn crashes during the 6pm&ndash;8pm window. The other intersections have
    either too few left-turn crashes in this window to compare individually or show
    only a small gap between winter and summer.</p>
    <table class="tab">
      <thead><tr>
        <th>Intersection</th>
        <th>Winter crashes</th><th>Summer crashes</th>
        <th>Rate gap</th><th>Rate ratio [95%&nbsp;CI]</th>
        <th>Failed to yield</th>
      </tr></thead>
      <tbody>{R.intersection_contrast_rows(dark)}</tbody>
    </table>
    <p class="cap">Crashes are counts over {span} during 6pm&ndash;8pm only. Rate gap is
    winter minus summer crashes per 1,000 season-days. Failed-to-yield column shows
    the share of left-turn crashes between 6pm&ndash;11pm where the officer recorded
    dark light conditions, citing failure to yield while turning left &mdash; the
    officer-recorded signature of a permissive left-turn phase. Sample sizes at individual intersections are small
    and confidence intervals are wide.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">limitations</span>What this analysis does not establish</h2>
    <div class="notclaim">
      <h3>These bound the interpretation of everything above.</h3>
      <ul>
        <li><b>Exposure is unknown.</b> The number of left turns attempted at these
        hours in each season is not available. If winter evenings carry less traffic
        than summer evenings, the risk per turn is higher than these figures indicate;
        if winter evenings carry more traffic than summer evenings, then the risk is
        lower.</li>
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
    <p>For background context, the table below ranks Plano's signalized
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
    the City of Plano. Several sit on state highways (SH121, SH190, and Preston Rd,
    which is SH289) or roads shared
    with neighboring cities, which may fall under TxDOT's or another jurisdiction's
    authority.</p>
  </section>

  <section class="sec">
    <h2><span class="eye">method</span>How the data was cut</h2>
    <p>All crash records held by TxDOT for Plano, {span}, narrowed to those that can
    be placed at a named intersection at a known time.</p>
    <table class="tab">
      <thead><tr><th>Records</th><th style="text-align:left">Step</th></tr></thead>
      <tbody>{R.funnel_rows(funnel)}</tbody>
    </table>
    <p class="cap">Crashes the officer coded as not related to an intersection, largely
    freeway and mid-block crashes, are excluded, as are driveway-access crashes. The analyses above use
    the signalized subset, since left-turn phasing exists only at a signal.</p>
    <p><a href="{C.REPO_URL}" style="color:#B87A18;font-weight:600;">Code, data and
    full method &rarr;</a></p>
  </section>

</main>

'''

    return R.write_page(R.page(body, description, span))
