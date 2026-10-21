"""Render the results page.

Visual language follows the subject: signal-timing sheets and crash tables. Monospace
for figures an engineer would want to check, and the signal head's own colors
(amber = permissive, green = protected, red = crash).
"""

import json

import config as C

def chart(dark, winter_field="winter_left_rate", summer_field="summer_left_rate",
           title="Left-turn crashes by hour of day", show_totals=False):
    """Crash rate by hour, winter against summer, with the darkness band.

    Pass winter_field/summer_field to switch between left-turn and all-crash views.
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

    peak = max(max(v[winter_field], v[summer_field])
               for v in dark["by_hour"].values())
    peak = max(peak, 1)
    span = max(hi - lo, 1)

    def x(h):
        return L + (h - lo) / span * pw

    def y(v):
        return T + ph - (v / peak) * ph

    # evening window: winter is dark but summer is still light
    x0 = x(max(C.WINTER_SUNSET, lo))
    x1 = x(min(C.SUMMER_SUNSET, hi))

    # morning window: winter is still dark but summer is already light
    mx0 = x(max(C.SUMMER_SUNRISE, lo))
    mx1 = x(min(C.WINTER_SUNRISE, hi))

    def path(field):
        pts = [f"{x(h):.1f},{y(dark['by_hour'][h][field]):.1f}" for h in hours]
        return "M" + " L".join(pts)

    dots = "".join(
        f'<circle cx="{x(h):.1f}" cy="{y(dark["by_hour"][h][f]):.1f}" r="3.5" '
        f'fill="{col}"/>'
        for f, col in [(winter_field, "var(--amber)"), (summer_field, "var(--sky)")]
        for h in hours)

    ticks = "".join(
        f'<text x="{x(h):.1f}" y="{H - B + 18}" class="ax" text-anchor="middle">'
        f'{h % 12 or 12}{"am" if h < 12 else "pm"}</text>' for h in hours)

    grid = "".join(
        f'<line x1="{L}" y1="{y(v):.1f}" x2="{W - R}" y2="{y(v):.1f}" class="grid"/>'
        f'<text x="{L - 8}" y="{y(v) + 4:.1f}" class="ax" text-anchor="end">{v:.0f}</text>'
        for v in [peak * i / 4 for i in range(5)])

    totals_box = ""
    if show_totals:
        w_total = sum(v[winter_field] for v in dark["by_hour"].values())
        s_total = sum(v[summer_field] for v in dark["by_hour"].values())
        bx = W - R - 176
        br = W - R - 4
        by = T + 4
        totals_box = (
            f'<rect x="{bx}" y="{by}" width="172" height="44" fill="#1E2F3D" rx="2"/>'
            f'<text x="{bx + 7}" y="{by + 15}" class="ax" fill="#E8A33D">winter total</text>'
            f'<text x="{br}" y="{by + 15}" class="ax" text-anchor="end" fill="#E8A33D">'
            f'{w_total:.0f} / 1,000 days</text>'
            f'<text x="{bx + 7}" y="{by + 33}" class="ax" fill="#7FA8C9">summer total</text>'
            f'<text x="{br}" y="{by + 33}" class="ax" text-anchor="end" fill="#7FA8C9">'
            f'{s_total:.0f} / 1,000 days</text>'
        )

    return f'''<svg viewBox="0 0 {W} {H}" class="chart" role="img"
   aria-label="{title}, winter versus summer">
  <text x="{L}" y="22" class="title">{title}</text>
  <text x="{L}" y="40" class="subtitle">{C.CITY_NAME} signalized intersections, {dark['span']['start_year']}&ndash;{dark['span']['end_year']}</text>
  <rect x="{mx0:.1f}" y="{T}" width="{max(mx1 - mx0, 0):.1f}" height="{ph}" class="band"/>
  {'<text x="' + f"{(mx0 + mx1) / 2:.1f}" + f'" y="{T + 13}" class="bandlab" text-anchor="middle">dark in winter,</text><text x="' + f"{(mx0 + mx1) / 2:.1f}" + f'" y="{T + 25}" class="bandlab" text-anchor="middle">light in summer</text>' if mx1 - mx0 > 60 else ''}
  <rect x="{x0:.1f}" y="{T}" width="{max(x1 - x0, 0):.1f}" height="{ph}" class="band"/>
  <text x="{(x0 + x1) / 2:.1f}" y="{T + ph - 18:.1f}" class="bandlab" text-anchor="middle">dark in winter,</text>
  <text x="{(x0 + x1) / 2:.1f}" y="{T + ph - 6:.1f}" class="bandlab" text-anchor="middle">light in summer</text>
  {grid}
  <path d="{path(summer_field)}" class="line summer"/>
  <path d="{path(winter_field)}" class="line winter"/>
  {dots}
  {ticks}
  {totals_box}
  <text transform="translate({L - 42},{T + ph / 2:.1f}) rotate(-90)" text-anchor="middle" class="axtitle">crashes / 1,000 days</text>
  <text x="{L + pw / 2:.1f}" y="{H - 14}" class="axtitle" text-anchor="middle">Hour of day</text>
</svg>'''


def _row_note(h, transition_hours):
    """Annotation for the hour table describing the light condition.

    Hours where light conditions change mid-hour (transition_hours, set by the city's
    page) return an empty string; a footnote below the table explains why.
    """
    if h in transition_hours:                    return ""   # transition hours — see footnote
    if h < C.SUMMER_SUNRISE:                        return "dark in both seasons"
    if h < C.WINTER_SUNRISE:                        return "dark in winter, light in summer"
    if h < C.WINTER_SUNSET:                         return "light in both seasons"
    if h < C.SUMMER_SUNSET:                         return "dark in winter, light in summer"
    return                                        "dark in both seasons"


_ROW_TYPES = ["left", "right", "angle", "rear"]


def fmt_ratio(r):
    """Rare crash types can hit zero winter or summer crashes in a given hour,
    where the ratio is undefined (nan) rather than misleadingly large or small."""
    return "&mdash;" if r != r else f"{r:.2f}&times;"


def hour_rows(dark, transition_hours):
    out = []
    for h in sorted(dark["by_hour"]):
        v = dark["by_hour"][h]
        comparison = v["is_comparison"]
        note = _row_note(h, transition_hours)
        cells = "".join(
            f'<td class="m{" grp" if t != _ROW_TYPES[0] else ""}">{v[f"winter_{t}_rate"]:.1f}</td>'
            f'<td class="m">{v[f"summer_{t}_rate"]:.1f}</td>'
            f'<td class="m b">{fmt_ratio(v[f"{t}_ratio"])}</td>'
            for t in _ROW_TYPES
        )
        out.append(f'''<tr class="{'ctrl' if comparison else ''}">
      <td class="m">{h % 12 or 12}{"am" if h < 12 else "pm"}</td>
      {cells}
      <td class="m dim grp">{v['all_ratio']:.2f}&times;</td>
      <td class="note">{note}</td>
    </tr>''')
    return "\n".join(out)


def chart_type_diff(dark):
    """Difference in crash-type share (winter% − summer%) by hour.

    Four lines: left-turn (amber), right-turn (sky), angle (green), rear-end (red).
    A horizontal zero line is the reference. The left-turn line rising above zero
    in the dark band — while other types stay near zero — is the key visual.
    """
    hours = sorted(dark["by_hour"].keys())
    if not hours:
        return ""
    lo, hi = min(hours), max(hours)
    W, H = 720, 300
    L, R, T, B = 68, 20, 48, 64
    pw, ph = W - L - R, H - T - B
    span = max(hi - lo, 1)

    all_vals = [dark["by_hour"][h][f"{t}_diff_pp"]
                for h in hours
                for t in ("left", "right", "angle", "rear")]
    y_max = max(max(all_vals), 1)
    y_min = min(min(all_vals), -1)
    y_range = y_max - y_min

    def x(h):
        return L + (h - lo) / span * pw

    def y(v):
        return T + ph - (v - y_min) / y_range * ph

    # Dark band (evening: winter dark, summer light)
    x0 = x(max(C.WINTER_SUNSET, lo))
    x1 = x(min(C.SUMMER_SUNSET, hi))
    mx0 = x(max(C.SUMMER_SUNRISE, lo))
    mx1 = x(min(C.WINTER_SUNRISE, hi))

    types = [
        ("left",  "var(--amber)", "left-turn"),
        ("right", "var(--sky)",   "right-turn"),
        ("angle", "var(--green)", "right-angle"),
        ("rear",  "var(--red)",   "rear-end"),
    ]

    def path(field):
        pts = [f"{x(h):.1f},{y(dark['by_hour'][h][field]):.1f}" for h in hours]
        return "M" + " L".join(pts)

    lines = "".join(
        f'<path d="{path(f"{t}_diff_pp")}" fill="none" stroke="{col}" '
        f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        for t, col, _ in types)

    dots = "".join(
        f'<circle cx="{x(h):.1f}" cy="{y(dark["by_hour"][h][f"{t}_diff_pp"]):.1f}" '
        f'r="3" fill="{col}"/>'
        for t, col, _ in types
        for h in hours)

    ticks = "".join(
        f'<text x="{x(h):.1f}" y="{H - B + 18}" class="ax" text-anchor="middle">'
        f'{h % 12 or 12}{"am" if h < 12 else "pm"}</text>' for h in hours)

    # Y axis gridlines: zero line prominent, one positive and one negative tick
    grid_vals = [round(y_min / 2), 0, round(y_max / 2)]
    grid_parts = []
    for v in grid_vals:
        yv = y(v)
        line_attr = 'class="grid"' if v != 0 else 'stroke="#4A5E6E" stroke-width="1.5"'
        sign = "+" if v > 0 else ""
        grid_parts.append(
            f'<line x1="{L}" y1="{yv:.1f}" x2="{W - R}" y2="{yv:.1f}" {line_attr}/>'
            f'<text x="{L - 8}" y="{yv + 4:.1f}" class="ax" text-anchor="end">'
            f'{sign}{v:.0f}</text>'
        )
    grid = "".join(grid_parts)

    key = "".join(
        f'<span><i style="background:{col}"></i>{label}</span>'
        for _, col, label in types)

    return f'''<svg viewBox="0 0 {W} {H}" class="chart" role="img"
   aria-label="Crash type mix difference, winter minus summer by hour">
  <text x="{L}" y="18" class="title">Crash-type mix: winter minus summer (percentage points)</text>
  <rect x="{mx0:.1f}" y="{T}" width="{max(mx1 - mx0, 0):.1f}" height="{ph}" class="band"/>
  <rect x="{x0:.1f}" y="{T}" width="{max(x1 - x0, 0):.1f}" height="{ph}" class="band"/>
  <text x="{(x0 + x1) / 2:.1f}" y="{T + ph - 18:.1f}" class="bandlab" text-anchor="middle">dark in winter,</text>
  <text x="{(x0 + x1) / 2:.1f}" y="{T + ph - 6:.1f}" class="bandlab" text-anchor="middle">light in summer</text>
  {grid}
  {lines}
  {dots}
  {ticks}
  <text transform="translate({L - 42},{T + ph / 2:.1f}) rotate(-90)" text-anchor="middle" class="axtitle">pp difference</text>
  <text x="{L + pw / 2:.1f}" y="{H - 14}" class="axtitle" text-anchor="middle">Hour of day</text>
</svg>
<div class="key" style="padding-top:6px">{key}</div>'''


def chart_type_ratio(dark):
    """Winter/summer rate ratio by hour, one line per crash type.

    Three lines: left-turn (amber), angle (green), rear-end (red). A horizontal
    1x line is the reference -- above it means winter runs higher, below means
    summer runs higher. Unlike the mix-share chart, this plots the same ratio
    units used throughout the rest of the page (e.g. "2.09x"), so a type can't
    appear to trade off against another the way a share chart can suggest: each
    line here is independent of what the others are doing.

    Right-turn is left off this chart on purpose: its per-hour counts are so
    small (often 1-3 crashes) that a single crash swings its ratio by several
    multiples (e.g. 8x on a summer count of 1), which would stretch the shared
    y-axis and crush the other three lines' real signal. Right-turn's ratio is
    still shown in full in the table above, where an unstable or undefined
    value already renders as an em-dash rather than a misleading number.
    """
    hours = sorted(dark["by_hour"].keys())
    if not hours:
        return ""
    lo, hi = min(hours), max(hours)
    W, H = 720, 300
    L, R, T, B = 68, 20, 48, 64
    pw, ph = W - L - R, H - T - B
    span = max(hi - lo, 1)

    types = [
        ("left",  "var(--amber)", "left-turn"),
        ("angle", "var(--green)", "right-angle"),
        ("rear",  "var(--red)",   "rear-end"),
    ]

    all_vals = [dark["by_hour"][h][f"{t}_ratio"]
                for h in hours for t, _, _ in types
                if dark["by_hour"][h][f"{t}_ratio"] == dark["by_hour"][h][f"{t}_ratio"]]
    y_max = max(max(all_vals), 1) * 1.08
    y_min = 0

    def x(h):
        return L + (h - lo) / span * pw

    def y(v):
        return T + ph - (v - y_min) / (y_max - y_min) * ph

    # Dark band (evening: winter dark, summer light)
    x0 = x(max(C.WINTER_SUNSET, lo))
    x1 = x(min(C.SUMMER_SUNSET, hi))
    mx0 = x(max(C.SUMMER_SUNRISE, lo))
    mx1 = x(min(C.WINTER_SUNRISE, hi))

    def valid_points(field):
        return [(h, dark["by_hour"][h][field]) for h in hours
                if dark["by_hour"][h][field] == dark["by_hour"][h][field]]

    def path(field):
        # Break the line at any hour with an undefined (nan) ratio, rather than
        # skipping straight past it, which would visually connect two hours that
        # don't have a real value between them.
        segments, current = [], []
        for h in hours:
            v = dark["by_hour"][h][field]
            if v != v:
                if current:
                    segments.append(current)
                    current = []
                continue
            current.append((h, v))
        if current:
            segments.append(current)
        return " ".join(
            "M" + " L".join(f"{x(h):.1f},{y(v):.1f}" for h, v in seg)
            for seg in segments)

    lines = "".join(
        f'<path d="{path(f"{t}_ratio")}" fill="none" stroke="{col}" '
        f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        for t, col, _ in types)

    dots = "".join(
        f'<circle cx="{x(h):.1f}" cy="{y(v):.1f}" r="3" fill="{col}"/>'
        for t, col, _ in types
        for h, v in valid_points(f"{t}_ratio"))

    ticks = "".join(
        f'<text x="{x(h):.1f}" y="{H - B + 18}" class="ax" text-anchor="middle">'
        f'{h % 12 or 12}{"am" if h < 12 else "pm"}</text>' for h in hours)

    grid_vals = sorted({0, 1, round(y_max)} | ({2} if y_max > 2 else set()))
    grid_parts = []
    for v in grid_vals:
        yv = y(v)
        line_attr = 'class="grid"' if v != 1 else 'stroke="#4A5E6E" stroke-width="1.5"'
        grid_parts.append(
            f'<line x1="{L}" y1="{yv:.1f}" x2="{W - R}" y2="{yv:.1f}" {line_attr}/>'
            f'<text x="{L - 8}" y="{yv + 4:.1f}" class="ax" text-anchor="end">'
            f'{v:.0f}&times;</text>'
        )
    grid = "".join(grid_parts)

    key = "".join(
        f'<span><i style="background:{col}"></i>{label}</span>'
        for _, col, label in types)

    return f'''<svg viewBox="0 0 {W} {H}" class="chart" role="img"
   aria-label="Crash type rate ratio, winter divided by summer, by hour">
  <text x="{L}" y="18" class="title">Crash-type rate ratio: winter &divide; summer</text>
  <rect x="{mx0:.1f}" y="{T}" width="{max(mx1 - mx0, 0):.1f}" height="{ph}" class="band"/>
  <rect x="{x0:.1f}" y="{T}" width="{max(x1 - x0, 0):.1f}" height="{ph}" class="band"/>
  <text x="{(x0 + x1) / 2:.1f}" y="{T + ph - 18:.1f}" class="bandlab" text-anchor="middle">dark in winter,</text>
  <text x="{(x0 + x1) / 2:.1f}" y="{T + ph - 6:.1f}" class="bandlab" text-anchor="middle">light in summer</text>
  {grid}
  {lines}
  {dots}
  {ticks}
  <text transform="translate({L - 42},{T + ph / 2:.1f}) rotate(-90)" text-anchor="middle" class="axtitle">winter&thinsp;/&thinsp;summer ratio</text>
  <text x="{L + pw / 2:.1f}" y="{H - 14}" class="axtitle" text-anchor="middle">Hour of day</text>
</svg>
<div class="key" style="padding-top:6px">{key}</div>'''


def intersection_contrast_rows(dark):
    """Table rows for the intersection seasonal contrast, ranked by rate gap.

    All intersections clearing MIN_INTERSECTION_CONTRAST are shown. Direction
    indicator makes winter_higher / equal / summer_higher immediately visible.
    Rows where winter is not higher are rendered muted so the eye goes to the
    candidates first. Significant flag (ratio CI lo > 1.0) shown inline.
    """
    rows = []
    for s in dark["intersection_contrast"]:
        ci = f'[{s["ratio_lo"]:.2f}&ndash;{s["ratio_hi"]:.2f}]'
        fy = f'{s["failed_to_yield_pct"]:.0f}%' if s["failed_to_yield_pct"] is not None else "—"
        rows.append(
            f'<tr>'
            f'<td>{s["intersection"]}</td>'
            f'<td class="m">{s["winter_left"]}</td>'
            f'<td class="m">{s["summer_left"]}</td>'
            f'<td class="m b">{s["gap"]:.1f}</td>'
            f'<td class="m">{s["ratio"]:.2f}&times;&nbsp;{ci}</td>'
            f'<td class="m amber">{fy}</td>'
            f'</tr>'
        )
    return "\n".join(rows)


def top_rows(top):
    return "\n".join(f'''<tr>
      <td>{t['intersection']}</td>
      <td class="m b">{t['total_crashes']}</td>
      <td class="m">{t['left_turn_crashes']}</td>
      <td class="m">{t['right_turn_crashes']}</td>
      <td class="m">{t['right_angle_crashes']}</td>
      <td class="m">{t['rear_end_crashes']}</td>
      <td class="m dim">{t['other_crashes']}</td>
    </tr>''' for t in top)


def hour_label(h):
    """24h integer hour as page text: 19 -> '7pm', 6 -> '6am'."""
    return f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"


def signed_pp(x):
    """A percentage-point difference as page text, with a typographic minus:
    -13.94 -> '&minus;13.9', 5.2 -> '+5.2'."""
    return f"&minus;{abs(x):.1f}" if x < 0 else f"+{x:.1f}"


def window_rates(dark):
    """Crashes per 1,000 season-days for the summary table: all crashes over the
    full day, all crashes in the contrast hours, and left-turn crashes in the
    contrast hours, for winter and summer."""
    c = dark["contrast"]
    bh = dark["by_hour"]
    win_days = dark["season_days"]["winter"]
    sum_days = dark["season_days"]["summer"]
    return {
        "day_w": sum(v["winter_all_rate"] for v in bh.values()),
        "day_s": sum(v["summer_all_rate"] for v in bh.values()),
        "eve_w": sum(bh[h]["winter_all_rate"] for h in C.CONTRAST_HOURS if h in bh),
        "eve_s": sum(bh[h]["summer_all_rate"] for h in C.CONTRAST_HOURS if h in bh),
        "lt_w": c["winter_left"] / win_days * 1000,
        "lt_s": c["summer_left"] / sum_days * 1000,
    }


def funnel_rows(funnel):
    """Table rows for the filter funnel; the last row (the analysis population) bold."""
    rows = []
    for i, (label, n) in enumerate(funnel):
        bold = i == len(funnel) - 1
        num_cls = ' class="m b"' if bold else ' class="m"'
        lbl_cls = ' class="b"' if bold else ''
        rows.append(
            f'<tr><td{num_cls}>{n:,}</td><td{lbl_cls}>{label}</td></tr>')
    return "\n".join(rows)


def page(body, description, span):
    """Wrap a city's page text in the shared frame: document head and styling, top
    bar, and footer. `body` runs from the hero header through </main>."""
    head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{C.SITE_TITLE} &mdash; {C.CITY_NAME}, TX</title>
<meta name="description" content="{description}">
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

  /* ---- hero ---- */
  .hero {{ background:var(--night); color:#F2F5F7; padding:22px 0 46px; }}
  .hero h1 {{ font:600 clamp(26px,4.5vw,42px)/1.15 var(--mono); margin:14px 0 0;
    letter-spacing:-.02em; max-width:22ch; }}
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
    padding:10px 4px 4px; flex-wrap:wrap; }}
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
  .tab tr.sig {{ background:#FBF3E4; }}
  .tab tr.sig td:first-child {{ font-weight:600; }}
  .tab .grp {{ border-left:1px solid #4A5E6E; }}

  /* checks */
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
    .hero h1 {{ font-size:24px; }}
  }}
</style>
</head>
<body>

<div class="top"><div class="wrap">
  <span class="tag">{C.CITY_NAME}, TX &middot; signalized intersections</span>
  <span class="src">Based on TxDOT CRIS &middot; {span}</span>
</div></div>

'''
    foot = f'''<footer><div class="wrap">
  <p>An independent analysis of public TxDOT CRIS crash records. Not affiliated with
  the City of {C.CITY_NAME} or TxDOT. Any errors are the author&rsquo;s.</p>
  <p style="margin-top:14px"><a href="{C.REPO_URL}">Repository</a> &middot;
  <a href="https://cris.dot.state.tx.us/public/Query/app/home">CRIS data source</a></p>
</div></footer>

</body>
</html>'''
    return head + body + foot


def write_page(html, path=None):
    """Write the results page to docs/<city>/index.html."""
    path = path or (C.DOCS_DIR / "index.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def write_json(dark, mech, path=None):
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
        clean({"darkness": dark, "mechanism": mech}),
        indent=2, default=str), encoding="utf-8")
    return path
