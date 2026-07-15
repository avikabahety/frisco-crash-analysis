# Left-turn crashes after dark — Frisco, TX

An analysis of ten years of TxDOT crash records for Frisco intersections.

Between 6 and 8pm, Frisco's signalised intersections recorded roughly **twice as many
left-turn crashes in the winter months as in the summer months** — the same clock hours,
adjusted for the number of days in each season. Those hours are dark in winter and light
in summer.

At 5pm, which is daylight in both seasons, the difference is absent.

📊 **[Results →](https://mbahety.github.io/frisco-crash-analysis/)**

---

## Robustness checks

Each check addresses an alternative explanation that would account for the observed
difference. The difference persists in each case.

| Check | Alternative explanation addressed |
|---|---|
| Counts per calendar day, not shares | A proportion can rise while the underlying count falls |
| Mantel–Haenszel, stratified by intersection | Crashes after dark occur at a different set of intersections |
| Dry pavement only | Winter is both darker and wetter |
| Right-turn comparison | Night driving is generally more difficult |
| Impaired-driver crashes excluded | The difference is alcohol-related |

Sunset in Frisco falls around 5:25pm in December and 8:35pm in June. The seasonal
difference appears from 6pm, is absent at 5pm when both seasons are light, and narrows
after 8pm once both seasons are dark.

## Limitations

- **The difference is not shown to be confined to permissive-left intersections.** The
  comparison between more- and less-permissive intersections is not statistically
  distinguishable, and the classification is limited by construction: an intersection
  running protected-only left turns produces few left-turn crashes and so rarely meets
  the minimum needed to be classified.
- **Signal phasing was not observed.** The interpretation rests on contributing factors
  recorded by officers, not on signal timing plans.
- **Exposure is unknown.** The number of left turns attempted after dark is not
  available.
- **Reportable crashes only** — those for which an officer filed a CR-3: injury, death,
  or $1,000+ in property damage.

## Run it

Requires pandas and numpy.

```bash
# an existing environment with pandas + numpy will do
conda activate <your-env>

# otherwise
conda create --name frisco-crash python=3.11 -y
conda activate frisco-crash
conda install pandas numpy -y

python analyze.py
```

Outputs are written to `output/` and `docs/index.html`.

```bash
python analyze.py --inspect   # print the CRIS columns in the export, confirm the mapping
```

The export carries 142 columns; the analysis uses 14.
[Which ones, and why →](METHODOLOGY.md#fields-used)

## Data

`data/2016-2026-07-13_cris_list.csv` is a TxDOT CRIS export and is **not committed** — it
is large and can be regenerated:

1. Open [CRIS Query](https://cris.dot.state.tx.us/public/Query/app/home)
2. Filter **City = FRISCO**, Crash Year 2016–2026
3. Export the **crash-level Attribute List** to CSV
4. Save it to `data/` and point `CRASH_FILE` in `config.py` at it

`data/signal_installations.csv` **is** committed: signal installation dates published in
City of Frisco bulletins.

## Layout

```
config.py            parameters: windows, thresholds, column names, street names
analyze.py           entry point — runs the analyses and writes every artifact
check_aliases.py     verifies street-name canonicalisation against the data
src/data.py          load, clean, filter. one definition of the study population
src/stats.py         the statistical tests
src/analyses.py      the three analyses
src/report.py        the results page
docs/index.html      generated — served by GitHub Pages
output/              generated — results.json and CSVs
```

## Notes on the CRIS format

Two characteristics are worth knowing before reusing this data.

**Crash time is stored as `HHMM`** (`"1745"`), not as a time. Parsing it as a datetime
yields the year 1745 and an hour of zero, placing every crash at midnight without raising
an error. `src/data.py:parse_hour` handles the format explicitly.

**Traffic control type varies over time.** A growing city installs signals, so an
intersection recorded as stop-controlled in 2017 may be signalised by 2021. An all-time
modal control type mislabels such intersections and mixes two crash regimes into a single
baseline.

## Method

See [METHODOLOGY.md](METHODOLOGY.md).

## Licence

MIT. Crash data is public record from TxDOT. Not affiliated with the City of Frisco or
TxDOT; any errors are the author's.
