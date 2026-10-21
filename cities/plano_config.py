"""Plano, TX. Settings that differ by city; everything shared is in config.py.

Hours and street aliases were set from `python check_setup.py --city plano` and
`python check_aliases.py --city plano`, using recorded light conditions, street names
and crash locations only. They were fixed and committed before the left-turn
analysis was first run for Plano.
"""

from config import DATA_DIR

# ---------------------------------------------------------------- input files
# TxDOT CRIS export: Query tool -> Crash Year 2016-2025, City = PLANO -> crash-level
# Attribute List (all crash fields). Pulled 21 October 2026. Query saved alongside
# as Plano_2016_to_2025_crash_report.qry. CSV not committed to GitHub (see .gitignore).
CRASH_FILE = DATA_DIR / "plano" / "2016-2026-10-21_cris_list_plano.csv"

# ------------------------------------------------------- reporting completeness
# Same study period as Frisco. The extract holds 2016-2025 only, so this removes
# nothing; it guards against a later re-pull that includes the current year.
# Run `python check_completeness.py --city plano` to see where reporting has settled.
ANALYSIS_END = "2025-12-31"

# ---------------------------------------------------------------- street aliases
# Only different names for the SAME road at the SAME place are merged. Each entry
# was confirmed from crash coordinates: the crashes under both names sit at the same
# points (within ~60m).
#
# Naming follows Frisco: highways and tollways keep their route number (US75, SH121,
# SH190); SH289 and FM2478 take their local names, Preston Rd and Custer Rd.
#
# Deliberately NOT merged:
#   - E/W halves of a road (E/W Parker Rd, Park Blvd, Plano Pkwy, Spring Creek Pkwy,
#     15th St). At US75 the E/W label identifies which frontage-road signal a crash
#     was at: E-labelled crashes sit on the east side, W-labelled on the west, so
#     each US75 interchange stays two intersections.
#   - FM544, FM2514, SH5: no location where they label the same intersection as
#     another name; SH5's local name changes along its length.
#   - Dallas N Tollway vs Dallas Pkwy: different roads (tollway vs frontage), as in
#     Frisco.
# N/S DALLAS PKWY: the prefix does not reliably mark a side, so a Dallas Pkwy
# interchange is one intersection, as in Frisco.
STREET_ALIASES = {
    "SH289": "PRESTON RD",
    "FM2478": "CUSTER RD",
    "S CUSTER RD": "CUSTER RD",
    "N CENTRAL EXPY": "US75",
    "CENTRAL EXPY": "US75",
    "FM75": "US75",                    # no such road; crashes sit on US75's points
    "W PRESIDENT GEORGE BUSH HWY": "SH190",
    "E PRESIDENT GEORGE BUSH HWY": "SH190",
    "PRESIDENT GEORGE BUSH FWY": "SH190",
    "PRESIDENT GEORGE BUSH TPKE": "SH190",
    "E PRESIDENT GEORGE BUSH TPKE": "SH190",
    "PRESIDENT GEORGE BUSH TURNPIKE": "SH190",
    "TX 190": "SH190",
    "HWY 121": "SH121",
    "STATE HWY 121": "SH121",
    "N DALLAS PKWY": "DALLAS PKWY",
    "S DALLAS PKWY": "DALLAS PKWY",
    "N JUPITER RD": "JUPITER RD",
}

# ------------------------------------------------------------- analysis windows
# Same as Frisco, confirmed from recorded light conditions at signalized
# intersections (check_setup.py):
#   4:00-4:59pm comparison hour  - daylight in both seasons (winter 94%, summer 100%)
#   6:00-7:59pm contrast hours   - dark in winter (daylight 7% / 1%), light in summer (99%)
#   10am-4pm midday              - daylight in both; 9pm-11pm late - dark in both
#   6am, 7am, 5pm, 8pm           - mixed; not used (transition hours on the page)
CONTRAST_HOURS = [18, 19]
COMPARISON_HOUR = 16
EVENING_HOURS = [18, 19, 20, 21, 22]
MIDDAY_HOURS = [10, 11, 12, 13, 14, 15]
LATE_HOURS = [21, 22]

# Plano sunset and sunrise in decimal hours, used to shade the darkness bands on the
# results page charts. Frisco's values: Plano is ~10 miles away and its sun times
# differ by about a minute (December sunset ~5:25pm, June ~8:35pm; December sunrise
# ~7:25am, June ~6:15am).
WINTER_SUNSET = 17.4
SUMMER_SUNSET = 20.6
WINTER_SUNRISE = 7.4
SUMMER_SUNRISE = 6.25

# ------------------------------------------------------------------- reporting
# Used by the shared page header, footer and chart subtitles. The page text
# itself is in cities/plano_report.py.
CITY_NAME = "Plano"
