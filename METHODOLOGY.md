# Methodology

## Fields used

The CRIS export carries 142 columns. Fourteen are used. Run `python analyze.py --inspect`
to print your export's header and confirm each one is present — CRIS field names vary
between export versions, and a silently missing column is worse than a loud error.

| CRIS column | Used for |
|---|---|
| `Crash ID` | Record identity; confirms one row per crash |
| `Crash Date` | Year, month, season. Also the before/after split for signal installations |
| `Crash Time` | Hour of day. **Stored as `HHMM`** — see the parsing note below |
| `Street Name` | Intersection identity (first street) |
| `Intersecting Street Name` | Intersection identity (second street) |
| `Intersection Related` | The scope filter: intersection vs freeway mainlane vs driveway |
| `Manner of Collision` | Crash type: left-turn, right-turn, right-angle, rear-end |
| `Light Condition` | **Dark vs daylight — the independent variable of the whole analysis** |
| `Traffic Control Type` | Restricts to signalised intersections; identifies flashing-yellow control |
| `Contributing Factors` | Permissive vs protected fingerprint; impaired-driver flag |
| `Surface Condition` | The dry-pavement-only robustness check |
| `Crash Severity` | KABCO code → injury flag |
| `Latitude`, `Longitude` | Mapping only. **Not** the intersection key — see below |

### Fields deliberately not used

- **`Average Daily Traffic Amount`** and the other ADT columns are populated on only
  ~30% of records (on-system roads). Too sparse to normalise by exposure. Frisco's GIS
  traffic-volume layer would be the source if exposure is ever added.
- **`At Intersection Flag`** is narrower than `Intersection Related` and drops ~3,700
  approach crashes, including the queue rear-ends that signalisation actually causes.
- **`Latitude`/`Longitude` as the clustering key.** Coordinates are genuine GPS (90%
  carry 8 decimal places; 86.6% of distinct points are used by a single crash), but
  clustering on them alone chains freeway crashes into corridor-length blobs — one
  reached 4,413 crashes spanning kilometres. The normalised street-name pair is the key
  instead; coordinates are kept for mapping.
- **`Number of Lanes`, `Median Type`, `Median Width`** — ~30% populated, on-system only.

## Data

TxDOT Crash Records Information System (CRIS), City of Frisco, exported at crash level
with all attributes. The extract covers crash years 2016–2026 and was pulled on
13 July 2026.

CRIS holds **reportable crashes only**: those an officer filed on a CR-3 form, required
when a crash causes injury, death, or $1,000+ in property damage. Minor crashes and
crashes with no police response are absent. Injury and fatal crashes are close to
complete; low-severity crashes are undercounted.

**Analysis is restricted to complete calendar years 2016–2025.** A crash enters CRIS only
after an officer files a CR-3 and TxDOT processes it, so the final months before any
extract date are under-reported. This is not neutral here: the analysis compares winter
(Nov–Feb) against summer (May–Aug), and a mid-year extract truncates summer closer to the
present than winter, so an incomplete tail would undercount summer and inflate the
winter/summer ratio — biasing the headline result in the direction it already points. The
partial 2026 data is therefore excluded rather than trusted. The cutoff is
`config.ANALYSIS_END`; `check_completeness.py` compares recent months against their
historical levels to confirm where reporting has settled.

## Population

| Step | Why |
|---|---|
| `Intersection Related` ∈ {INTERSECTION, INTERSECTION RELATED} | Keeps crashes at an intersection *and* on its approach. Approach crashes (queue rear-ends, dilemma-zone crashes) are intersection failures occurring 150ft upstream, and `At Intersection Flag` would drop ~3,700 of them. |
| Exclude `NON INTERSECTION` | Freeway mainlane. **Zero of 12,162 carry a cross street**, and their crash-type signature is a freeway's: single-vehicle, rear-end, sideswipe, with right-angle crashes at 2.6% against 15% city-wide. |
| Exclude `DRIVEWAY ACCESS` | A real problem (access management) but a different one. Held out rather than mixed in. |
| Both street names present, no self-pairs | An intersection needs an identity. `LEGACY DR & LEGACY DR` is an artifact. |
| Signalised only, for the main analyses | Left-turn phasing only exists at a signal. |

**Intersection identity** is the normalised, order-independent street-name pair. Street
names are canonicalised before pairing: route numbers are standardised (`SH 121`,
`SH-121`, `SH0121` → `SH121`), suffixes are standardised (`MAIN STREET` → `MAIN ST`), and
routes carrying a local name are resolved to that name (FM 2934 → Eldorado Pkwy,
FM 3537 → Main St, FM 2478 → Custer Rd, SH 289 → Preston Rd), since officers record the
same road under either designation. Dallas Pkwy and the Dallas North Tollway are distinct
roads and are not combined.

Coordinates are genuine GPS rather than snapped to a reference point: 90% carry eight
decimal places and 86.6% of distinct points are used by a single crash. They are retained
for mapping but are not used as the intersection key, since clustering on coordinates
alone joins freeway crashes into corridor-length groups.

Pooled results — the rate ratio, the dark/daylight comparison, the robustness checks and
the comparison hour — are computed across all signalised crashes and do not depend on how
crashes are keyed to intersections.

## The darkness analysis

**Hypothesis.** Left-turn crashes are over-represented in darkness, because a permissive
left turn requires judging a gap in oncoming traffic and darkness degrades that
judgment.

**The principal confound.** Night has less traffic and less congestion, so the crash *mix*
changes at night for reasons unrelated to darkness.

**The design.** The clock hour is held fixed, and dark crashes are compared against
daylight crashes at that same hour. 6pm is dark in December and light in June, while the
traffic pattern at 6pm is broadly similar in both. Only hours containing both dark and
daylight crashes can be used: the sunset transition hours.

Frisco's sunset moves from ~17:25 in December to ~20:35 in June. Therefore:

- **17:00** — light in both seasons. No darkness contrast; used as a comparison hour.
- **18:00–19:00** — dark in winter, light in summer. Maximum contrast.
- **21:00+** — dark in both seasons. No contrast, so untestable.

Dawn and dusk are excluded from both groups, as they represent the transition between the
two conditions being compared.

### Robustness checks

Each addresses an alternative explanation that would account for the observed difference.

**1. Counts, not shares.** Proportions sum to 100%, so the left-turn share could rise
purely because rear-end and right-angle crashes fall at night. Left-turn crashes are
therefore counted per 1,000 calendar days, winter against summer, at the same hour.
Winter and summer cover a near-identical number of days.

**2. Stratified by intersection (Mantel–Haenszel).** Crashes after dark may occur at a
different set of intersections than daylight crashes. Pooling the odds ratio within
intersections tests whether the association holds inside the same intersection. A sign
test across strata is reported alongside.

**3. Dry pavement only.** Winter is both darker and wetter.

**4. Right-turn comparison.** If night driving were generally more difficult, other
turning movements would be expected to shift similarly.

Impaired-driver crashes are excluded as a further check.

### Excess crashes

Only the left-turn-specific excess is attributed: what remains after allowing for the
general increase in crashes after dark. Expected winter left-turn crashes are computed by
scaling summer left-turn crashes by the winter/summer ratio for all crashes at that hour;
the excess is the remainder.

Traffic volumes are lower after dark, so fewer left turns are likely being attempted while
more left-turn crashes are recorded. The risk per turn attempted would then be higher than
this figure indicates, making the estimate conservative.

## The mechanism analysis

A driver is required to yield only on a permissive phase. Under a protected left (green
arrow, opposing traffic held at red) the turning driver has right of way, so a collision
would be recorded as a disregarded signal rather than a failure to yield. The officer's
contributing factor therefore carries information about which phase was operating:

- `FAILED TO YIELD RIGHT OF WAY - TURNING LEFT` → permissive
- `DISREGARD STOP AND GO SIGNAL` → protected (or red-light running)

**Calibration:** crashes recorded at flashing-yellow-arrow control are permissive by
definition and provide a reference point for the factor distribution under permissive
operation.

Left-turn phasing is configured per intersection, so results are reported per intersection
rather than as a city-wide characterisation.

### Concentration test (not resolved)

Whether the darkness effect is concentrated at permissive-leaning intersections was
tested and is not resolved by this data.

- Intersections were classified on midday crashes (off-peak daylight) and the effect
  tested on separate evening crashes, so that classification and test do not share data.
- An interaction test comparing the two groups' odds ratios is not significant.
- The classification is limited by construction: an intersection running protected-only
  left turns produces few left-turn crashes and so rarely meets the minimum needed to be
  classified. The comparison is closer to "more permissive" against "less permissive"
  than to permissive against protected.

The result is recorded in `results.json` and stated on the results page.

## The signalisation analysis

Before/after at intersections with **known installation dates** from City of Frisco
bulletins, with a 60-day buffer excluded around each install (construction, flashing
mode, driver adjustment) and a minimum of one year on each side.

**Reported as rates, not shares.** After signalisation the left-turn *share* rises while
the left-turn *rate* falls, because total crashes fall faster than left-turn crashes do. A
proportion can rise while the quantity it measures declines, so rates are used throughout.

**What the crash-type shift supports.** Right-angle crashes fall sharply while rear-end
crashes rise sharply — the trade-off signalisation is expected to produce. Regression to
the mean would move every crash type in the same direction and does not account for one
type rising while another falls.

**What is not reported.** The overall change in crash frequency. Signals tend to be
installed where crashes have recently increased, so some subsequent decline would be
expected regardless. A causal frequency estimate requires Empirical Bayes with a
calibrated safety performance function.

## Known limitations

- **Reportable crashes only** (CR-3 threshold).
- **No exposure data.** CRIS ADT is populated on only ~30% of records (on-system roads).
  Frisco's GIS traffic-volume layer would supply this.
- **Signal timings unknown.** The countermeasure is inferred, not verified.
- **Hours dark year-round (21:00+) cannot be tested** — there is no daylight
  counterfactual at 10pm.
- **Contributing factors are officer-coded** and carry the usual reporting variability.

## Statistical notes

Two-proportion z tests for share comparisons. Poisson log-ratio intervals for rate
ratios. Mantel–Haenszel for stratified pooling. Where two effects are compared, an
explicit interaction test on the log odds ratios: two effects can both be significant and
still be indistinguishable from each other, so comparing their magnitudes by inspection is
not sufficient.
