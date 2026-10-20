"""Shared configuration for the crash analysis.

Settings that are the same for every city live here; settings that differ by city
live in cities/<city>_config.py. Between the two, every tunable parameter is in a
config file. Nothing else in the codebase hard-codes a threshold, a window, or a
field name.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_ROOT = ROOT / "output"      # each city writes to output/<city>/
DOCS_ROOT = ROOT / "docs"          # each city's page goes to docs/<city>/index.html

# ------------------------------------------------------------------- city
# Settings that differ by city are NOT here. They live in cities/<city>_config.py
# and are loaded by src/city.py when a script is run with --city. Those fields are:
#   CRASH_FILE, ANALYSIS_END, STREET_ALIASES, sunrise/sunset times,
#   CONTRAST_HOURS, CONTROL_HOUR, EVENING_HOURS, MIDDAY_HOURS, SITE_SUBTITLE

# ------------------------------------------------------------------- CRIS map
# Confirmed against the Frisco export. CRIS field names vary by export version;
# run `python analyze.py --city <city> --inspect` to print the columns a file has.
COLUMNS = {
    "crash_id": "Crash ID",
    "date": "Crash Date",
    "time": "Crash Time",
    "street": "Street Name",
    "cross_street": "Intersecting Street Name",
    "collision": "Manner of Collision",
    "factors": "Contributing Factors",
    "control": "Traffic Control Type",
    "light": "Light Condition",
    "surface": "Surface Condition",
    "intersection": "Intersection Related",
}

# --------------------------------------------------------------------- filters
# Crashes that belong to an intersection. NON INTERSECTION crashes are freeway
# crashes with no cross street; DRIVEWAY ACCESS crashes are excluded.
INTERSECTION_TYPES = ["INTERSECTION", "INTERSECTION RELATED"]

# Values that mean "no data" across CRIS text fields.
NULL_VALUES = ["", "NOT REPORTED", "NAN", "NO DATA", "UNKNOWN"]

# ------------------------------------------------------------- analysis windows
WINTER_MONTHS = [11, 12, 1, 2]
SUMMER_MONTHS = [5, 6, 7, 8]

# Minimum crashes in a cell before a comparison is reported.
MIN_CELL = 25
# Minimum dark and daylight crashes at one intersection to enter the stratified test.
MIN_STRATUM = 5
# Minimum left-turn crashes per season at one intersection during contrast hours
# for it to appear in the intersection-level seasonal contrast table.
# Lower than MIN_CELL because this is per-intersection in a 2-hour window, not city-wide.
MIN_INTERSECTION_CONTRAST = 3
# Minimum raw count gap (winter_left - summer_left) for an intersection to appear
# in the contrast table. Filters out intersections with no meaningful directional signal.
MIN_INTERSECTION_GAP = 5

# Size of the "largest signalized intersections by total crash count" export
# (top_intersections.csv), also shown as a table on the public report page under
# "Signalized intersections with the most crashes overall".
TOP_N_INTERSECTIONS = 25

# ------------------------------------------------------------------- reporting
SITE_TITLE = "Left-turn crashes after dark"
REPO_URL = "https://github.com/avikabahety/frisco-crash-analysis"
