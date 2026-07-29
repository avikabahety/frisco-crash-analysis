# Left-turn crashes after dark — Frisco, TX

Winter evening crashes at Frisco's signalised intersections run measurably higher than
summer. Left-turn crashes drive a disproportionate share of that difference — roughly
twice as many between 6 and 8pm in winter months as in summer months, at the same clock
hours, adjusted for days in each season. At 5pm, daylight in both seasons, the difference
is absent.

📊 **[Full results →](https://mbahety.github.io/frisco-crash-analysis/)**

---

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

The export carries 142 columns; the analysis uses 13.
[Which ones, and why →](METHODOLOGY.md#fields-used)

## Data

`data/2016-2026-07-13_cris_list.csv` is a TxDOT CRIS export and is **not committed** — it
is large and can be regenerated:

1. Open [CRIS Query](https://cris.dot.state.tx.us/public/Query/app/home)
2. Filter **City = FRISCO**, Crash Year 2016–2026
3. Export the **crash-level Attribute List** to CSV
4. Save it to `data/` and point `CRASH_FILE` in `config.py` at it

## Layout

```
config.py            parameters: windows, thresholds, column names, street names
analyze.py           entry point — runs the analyses and writes every artifact
check_aliases.py     verifies street-name canonicalisation against the data
src/data.py          load, clean, filter. one definition of the study population
src/stats.py         the statistical tests
src/analyses.py      the two analyses
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
