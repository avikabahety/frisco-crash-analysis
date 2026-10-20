# Left-turn crashes after dark

This analysis compares winter evening crashes at signalized intersections against
summer evening crashes at the same clock hours. In Frisco, TX, left-turn crashes drive
a disproportionate share of the difference. Left-turn crashes are roughly twice as many
between 6 and 8pm in winter months as in summer months, adjusted for number of days in
each season.

The same analysis is being applied to other Collin County cities. Each city has its
own results page.

| City | Results |
|---|---|
| Frisco, TX | [Full results →](https://avikabahety.github.io/frisco-crash-analysis/frisco/) |

---

## Run it

Requires pandas and numpy.

```bash
# an existing environment with pandas + numpy will do
conda activate <your-env>

# otherwise
conda create --name crash-analysis python=3.11 -y
conda activate crash-analysis
conda install pandas numpy -y

python analyze.py --city frisco
```

Every script takes `--city`. Outputs are written to `output/<city>/` and
`docs/<city>/index.html`.

```bash
python analyze.py --city frisco --inspect    # print the CRIS columns in the export, confirm the mapping
python check_completeness.py --city frisco   # where recent-month reporting has settled
python check_aliases.py --city frisco        # look for street-name aliases in the data
```

The export carries 142 columns; the analysis uses 11.
[Which ones, and why →](METHODOLOGY.md#fields-used)

## Data

Each city's TxDOT CRIS export lives in `data/<city>/` and is **not committed to
GitHub** — it is large and can be regenerated. See [data/README.md](data/README.md).

## Layout

```
config.py               shared settings: CRIS column map, filters, thresholds, seasons
cities/
  frisco_config.py      Frisco settings: data file, cutoff date, street aliases, sunset hours
  frisco_report.py      Frisco results page text
analyze.py              entry point — runs the analyses for one city, writes every artifact
check_aliases.py        verifies street-name canonicalisation against the data
check_completeness.py   measures CRIS reporting lag, to set the cutoff date
compare_outputs.py      maintainer check: Frisco run vs. saved baseline
src/city.py             loads the selected city's settings and page text
src/data.py             load, clean, filter. one definition of the study population
src/stats.py            the statistical tests
src/analyses.py         the analyses
src/report.py           shared page parts: charts, tables, styling, header, footer
data/<city>/            CRIS export (not committed to GitHub) and city reference files
output/<city>/          generated — results.json and CSVs (not committed to GitHub)
docs/<city>/            generated — results page, served by GitHub Pages
tests/baseline/frisco/  reference outputs used by compare_outputs.py
```

## Adding a city

1. Export the city's CRIS data to `data/<city>/` (see [data/README.md](data/README.md)).
2. Create `cities/<city>_config.py` with every setting listed in `REQUIRED` in
   `src/city.py`. `cities/frisco_config.py` is a starting point; the data file,
   cutoff date and street aliases must be set for the new city. Analysis hours are
   set from the city's sunset times before its results are looked at.
3. Create `cities/<city>_report.py`, the page text, written for that city's
   results. Charts, tables and the page frame come from `src/report.py`.
4. Run `python analyze.py --city <city>`.

The method, thresholds and seasons in `config.py` are shared, so every city is
analysed the same way.

## Notes on the CRIS format

Two characteristics are worth knowing before reusing this data.

**Crash time is stored as `HHMM`** (`"1745"`), not as a time. Parsing it as a datetime
yields the year 1745 and an hour of zero, placing every crash at midnight without raising
an error. `src/data.py:parse_hour` handles the format explicitly.

**Traffic control type varies over time.** A growing city installs signals, so an
intersection recorded as stop-controlled in 2017 may be signalized by 2021. An all-time
modal control type mislabels such intersections and mixes two crash regimes into a single
baseline.

## Method

See [METHODOLOGY.md](METHODOLOGY.md).

## Licence

MIT. Crash data is public record from TxDOT. Not affiliated with any city or with
TxDOT; any errors are the author's.
