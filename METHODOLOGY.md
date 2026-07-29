# Methodology

## Fields used

The CRIS export carries 142 columns, out of which 13 are used. Run `python analyze.py --inspect`
to print your export's header and confirm each one is present — CRIS field names may vary
between export versions.

| CRIS column | Used for |
|---|---|
| `Crash ID` | Record identity; confirms one row per crash |
| `Crash Date` | Year, month, season |
| `Crash Time` | Hour of day. **Stored as `HHMM`** |
| `Street Name` | Intersection identity (first street) |
| `Intersecting Street Name` | Intersection identity (second street) |
| `Intersection Related` | The scope filter: intersection vs freeway mainlane vs driveway |
| `Manner of Collision` | Crash type: left-turn, right-turn, right-angle, rear-end |
| `Light Condition` | Dark vs daylight — the independent variable of the analysis |
| `Traffic Control Type` | Restricts to signalised intersections; identifies flashing-yellow control |
| `Contributing Factors` | Permissive vs protected fingerprint; impaired-driver flag |
| `Surface Condition` | The dry-pavement-only robustness check |
| `Latitude`, `Longitude` | Mapping only. **Not** the intersection key — see below |

### Fields deliberately not used

- **`Average Daily Traffic Amount`** and the other ADT columns are populated on only
  ~30% of records (on-system roads). Too sparse to normalise by exposure. Frisco's GIS
  traffic-volume layer would be the source if exposure is ever added.
- **`At Intersection Flag`** is narrower than `Intersection Related` and drops ~3,700
  approach crashes, including queue rear-ends on approaches.
- **`Latitude`/`Longitude` as the clustering key.** Coordinates are genuine GPS (90%
  carry 8 decimal places; 86.6% of distinct points are used by a single crash), but
  clustering on them alone chains freeway crashes into corridor-length blobs. The 
  normalised street-name pair is the key instead; coordinates are kept for mapping.
- **`Number of Lanes`, `Median Type`, `Median Width`** — ~30% populated, too sparse.

## Data

TxDOT Crash Records Information System (CRIS), City of Frisco, exported at crash level
with all attributes. The extract covers crash years 2016–2026 and was pulled on
13 July 2026.

CRIS holds **reportable crashes only**: those an officer filed on a CR-3 form, required
when a crash causes injury, death, or $1,000+ in property damage. Minor crashes and
crashes with no police response are absent. 

**Analysis is restricted to complete calendar years 2016–2025.** A crash enters CRIS only
after an officer files a CR-3 and TxDOT processes it, so the final months before any
extract date are under-reported. The analysis compares winter
(Nov–Feb) against summer (May–Aug), and a mid-year extract truncates summer closer to the
present than winter, so an incomplete tail would undercount summer and inflate the
winter/summer ratio. The
partial 2026 data is therefore excluded. The cutoff is
`config.ANALYSIS_END`; `check_completeness.py` compares recent months against their
historical levels to confirm where reporting has settled.

## Population

| Step | Why |
|---|---|
| `Intersection Related` ∈ {INTERSECTION, INTERSECTION RELATED} | Keeps crashes at an intersection *and* on its approach. Approach crashes (queue rear-ends, dilemma-zone crashes) are intersection failures occurring 150ft upstream, and using the `At Intersection Flag` field would drop ~3,700 of them. |
| Exclude `NON INTERSECTION` | Freeway mainlane. Zero of 12,162 carry a cross street, and their crash-type signature is a freeway's: single-vehicle, rear-end, sideswipe, with right-angle crashes at 2.6% against 15% city-wide. |
| Exclude `DRIVEWAY ACCESS` | Excluded. |
| Both street names present, no self-pairs | An intersection requires two distinct street names. Records where both fields carry the same name (e.g. `LEGACY DR & LEGACY DR`) are excluded as malformed. |
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

Crashes coded DAWN or DUSK in `Light Condition` field are excluded from both groups, as they represent the transition between the two conditions being compared.

### Robustness checks

**1. Counts, not shares.** Left-turn crashes are compared as Poisson rates per 1,000
calendar days (winter days and summer days counted separately), not as proportions of
total crashes. Winter and summer each contribute approximately 1,200 calendar days over
the study period.

**2. Stratified by intersection (Mantel–Haenszel).** The Mantel–Haenszel odds ratio
pools the dark/daylight left-turn odds ratio within each intersection, requiring at least
`MIN_STRATUM` crashes on each side (see `config.py`). A sign test across strata checks
whether the majority of intersections move in the predicted direction, complementing the
pooled test.

**3. Dry pavement only.** Restricted to crashes where `Surface Condition` = DRY. The
proportion test is re-run on this subset.

**4. Right-turn comparison.** The same dark/daylight proportion test run on right-turn
crashes. No effect expected or found.

**5. Impaired drivers excluded.** Crashes where `Contributing Factors` contains an
impairment code are dropped. The proportion test is re-run on the remainder.


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

## Known limitations

- **Hours dark year-round (21:00+) cannot be tested** — there is no daylight
  counterfactual at those hours, so the design has no traction beyond approximately 9pm.
- **Contributing factors are officer-coded.** The permissive/protected fingerprint rests
  on `FAILED TO YIELD RIGHT OF WAY - TURNING LEFT` vs `DISREGARD STOP AND GO SIGNAL`.
  These are officer judgements and may carry reporting variability.

## Statistical notes

Two-proportion z tests for share comparisons. Poisson log-ratio intervals for rate
ratios. Mantel–Haenszel for stratified pooling. Where two effects are compared, an
explicit interaction test on the log odds ratios: two effects can both be significant and
still be indistinguishable from each other, so comparing their magnitudes by inspection is
not sufficient.
