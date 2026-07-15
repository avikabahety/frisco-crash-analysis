"""Configuration for the Frisco crash analysis.

Every tunable parameter lives here. Nothing else in the codebase hard-codes a
threshold, a window, or a field name.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
DOCS_DIR = ROOT / "docs"

# ---------------------------------------------------------------- input files
# TxDOT CRIS export: Query tool -> City = FRISCO -> crash-level Attribute List.
# Large, regenerable, and therefore not committed (see .gitignore).
CRASH_FILE = DATA_DIR / "2016-2026-07-13_cris_list.csv"

# Signal installation dates collected from City of Frisco bulletins. Committed.
INSTALL_FILE = DATA_DIR / "signal_installations.csv"

# ------------------------------------------------------- reporting completeness
# A crash enters CRIS only after an officer files a CR-3 and TxDOT processes it, so
# the most recent months of any extract are incomplete. This matters here because
# the incomplete tail is asymmetric across the seasons being compared: an extract
# taken in July 2026 includes a near-complete Jan-Feb (winter) but only a partial,
# under-reported May-Jul (summer). That undercounts summer and inflates the
# winter/summer ratio -- biasing the headline result upward. Analysis is therefore
# truncated to complete calendar years. Move this forward when a newer extract is
# pulled; run `python check_completeness.py` to see where reporting has settled.
ANALYSIS_END = "2025-12-31"

# ------------------------------------------------------------------- CRIS map
# Confirmed against the Frisco export. CRIS field names vary by export version;
# run `python analyze.py --inspect` to print the columns your file actually has.
COLUMNS = {
    "crash_id": "Crash ID",
    "date": "Crash Date",
    "time": "Crash Time",
    "lat": "Latitude",
    "lon": "Longitude",
    "severity": "Crash Severity",
    "street": "Street Name",
    "cross_street": "Intersecting Street Name",
    "collision": "Manner of Collision",
    "factors": "Contributing Factors",
    "control": "Traffic Control Type",
    "light": "Light Condition",
    "surface": "Surface Condition",
    "intersection": "Intersection Related",
}

# CRIS severity is text like "K - FATAL INJURY". The code before the dash is the key.
SEVERITY = {"K": "K", "A": "A", "B": "B", "C": "C", "N": "O", "O": "O", "99": "O"}

# ---------------------------------------------------------------- street aliases
# Officers record the same physical road under either its route number or its local
# name, so one intersection ends up split across two keys and each half is
# undercounted. These are the same road:
#
#   FM2934  = Eldorado Pkwy      FM3537 = Main St
#   FM2478  = Custer Rd          SH289  = Preston Rd
#
# Source: City of Frisco, Related Agencies / Streets
# (https://www.friscotexas.gov/420/Related-Agencies)
#
# Canonicalised to the LOCAL name, because that is what residents, city staff and
# traffic engineers actually use: "Eldorado Pkwy & Custer Rd" beats "FM2934 & FM2478".
#
# Deliberately NOT merged: Dallas Pkwy and Dallas North Tollway are different roads
# (frontage road vs tollway mainlane), and merging them would fabricate intersections.
#
# Run `python check_aliases.py` to look for further aliases: it flags any two street
# names whose crashes sit on top of each other geographically.
STREET_ALIASES = {
    "FM2934": "ELDORADO PKWY",
    "FM3537": "MAIN ST",
    "FM2478": "CUSTER RD",
    "SH289": "PRESTON RD",
}

# --------------------------------------------------------------------- filters
# Crashes that belong to an intersection. NON INTERSECTION crashes are freeway
# mainlane (0 of 12,162 had a cross street); DRIVEWAY ACCESS is a separate problem.
INTERSECTION_TYPES = ["INTERSECTION", "INTERSECTION RELATED"]

# Values that mean "no data" across CRIS text fields.
NULL_VALUES = ["", "NOT REPORTED", "NAN", "NO DATA", "UNKNOWN"]

# ------------------------------------------------------------- analysis windows
# Frisco sunset: ~17:25 in December, ~20:35 in June. Hours 18-19 are therefore dark in
# winter and light in summer, giving the darkness contrast. 17:00 is light in both
# seasons and serves as a comparison hour with no contrast.
CONTRAST_HOURS = [18, 19]
CONTROL_HOUR = 17
EVENING_HOURS = [18, 19, 20, 21]
MIDDAY_HOURS = [10, 11, 12, 13, 14, 15]

WINTER_MONTHS = [11, 12, 1, 2]
SUMMER_MONTHS = [5, 6, 7, 8]

# Minimum crashes in a cell before a comparison is reported.
MIN_CELL = 25
# Minimum dark and daylight crashes at one intersection to enter the stratified test.
MIN_STRATUM = 5

# ------------------------------------------------- before/after signalization
BUFFER_DAYS = 60      # excluded around install: construction and driver adjustment
MIN_YEARS = 1.0       # minimum coverage before and after for a site to be included

# ------------------------------------------------------------------- reporting
SITE_TITLE = "Left-turn crashes after dark"
SITE_SUBTITLE = "Frisco, TX \u00b7 TxDOT CRIS crash records, 2016\u20132026"
REPO_URL = "https://github.com/mbahety/frisco-crash-analysis"
