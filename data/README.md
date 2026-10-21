# data/

One folder per city, holding that city's TxDOT CRIS export and any city reference
files.

## `<city>/<pull-date>_cris_list.csv` — not committed to GitHub
The CRIS export. Large and regenerable, so it is excluded from the repository
(see `.gitignore`).

Get it: https://cris.dot.state.tx.us/public/Query/app/home
→ Query tool → City = <CITY>, Crash Year 2016 onward
→ export the crash-level **Attribute List** (All Crash fields, not Unit and Person attributes) to CSV → save it in `data/<city>/`
→ set `CRASH_FILE` in `cities/<city>_config.py` to its name.

Name the file by the date it was pulled (e.g. `2016-2026-07-13_cris_list.csv`). The
pull date decides which recent months are still incomplete; see `ANALYSIS_END` in
the city's config and `python check_completeness.py --city <city>`.

| City | File | Pulled |
|---|---|---|
| Frisco | `frisco/2016-2026-07-13_cris_list.csv` | 13 July 2026 |

## `frisco/signal_installations.csv` — committed to GitHub
Signal installation dates from City of Frisco bulletins or estimated from local news.
Not used by the current analysis; kept for reference. Format:

```csv
intersection,install_date,notes
COIT RD & LYNDHURST DR,2021-04-05,fully operational; flashing mode from 04-01
```
