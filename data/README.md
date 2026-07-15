# data/

## `2016-2026-07-13_cris_list.csv` — not committed
The TxDOT CRIS export. Large and regenerable, so it is gitignored.

Get it: https://cris.dot.state.tx.us/public/Query/app/home
→ Query tool → City = FRISCO, Crash Year 2016–2026
→ export the crash-level **Attribute List** to CSV → save here.

## `signal_installations.csv` — committed
Signal installation dates from City of Frisco bulletins or estimated from local news. Format:

```csv
intersection,install_date,notes
COIT RD & LYNDHURST DR,2021-04-05,fully operational; flashing mode from 04-01
```

`intersection` is matched by normalised street-name pair, so "Coit Rd and Lyndhurst
Drive", "COIT RD & LYNDHURST DR" and "Coit / Lyndhurst" all resolve to the same place.
`analyze.py` reports any row it cannot match to the crash data.
