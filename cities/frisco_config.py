"""Frisco, TX. Settings that differ by city; Common settings are in config.py."""

from config import DATA_DIR

# ---------------------------------------------------------------- input files
# TxDOT CRIS export: Query tool -> City = FRISCO -> crash-level Attribute List.
# Large, regenerable, and therefore not committed (see .gitignore).
CRASH_FILE = DATA_DIR / "frisco" / "2016-2026-07-13_cris_list.csv"

# ------------------------------------------------------- reporting completeness
# A crash enters CRIS only after an officer files a CR-3 and TxDOT processes it, so
# the most recent months of any extract are incomplete. An extract
# taken in July 2026 includes a near-complete Jan-Feb (winter) but only a partial,
# under-reported May-Jul (summer). Analysis is therefore
# truncated to complete calendar years. Move this forward when a newer extract is
# pulled; run `python check_completeness.py --city frisco` to see where reporting
# has settled.
ANALYSIS_END = "2025-12-31"

# ---------------------------------------------------------------- street aliases
# Officers record the same physical road under either its route number or its local
# name, so one intersection ends up split across two keys and each half is
# undercounted. For example, these are the same road:
#
#   FM2934  = Eldorado Pkwy      FM3537 = Main St
#   FM2478  = Custer Rd          SH289  = Preston Rd
#
# Source: City of Frisco, Related Agencies / Streets
# (https://www.friscotexas.gov/420/Related-Agencies)
#
# Canonicalised to the LOCAL name: "Eldorado Pkwy & Custer Rd" beats "FM2934 & FM2478".
#
# Deliberately NOT merged: Dallas Pkwy and Dallas North Tollway are different roads
# (frontage road vs tollway mainlane).
#
# Run `python check_aliases.py --city frisco` to look for further aliases: it flags
# any two street names whose crashes sit on top of each other geographically.
# Identification of aliases is a manual process, so check the flagged pairs and add any new ones to this dictionary.
STREET_ALIASES = {
    "FM2934": "ELDORADO PKWY",
    "FM3537": "MAIN ST",
    "FM2478": "CUSTER RD",
    "SH289": "PRESTON RD",
}

# ------------------------------------------------------------- analysis windows
# Frisco sunset: ~17:25 in December, ~20:35 in June. Hours 18-19 (6:00-7:59pm) are
# therefore dark in winter and light in summer, giving the darkness contrast.
#
# Comparison hour: the last full hour that ends before the earliest winter sunset
# (Frisco: earliest sunset ~5:20pm, so 4:00-4:59pm), daylight in both seasons.
# 5:00-5:59pm is not used: sunset falls inside that hour in winter.
CONTRAST_HOURS = [18, 19]
COMPARISON_HOUR = 16
EVENING_HOURS = [18, 19, 20, 21, 22]
MIDDAY_HOURS = [10, 11, 12, 13, 14, 15]

# Frisco sunset and sunrise in decimal hours (17.4 = 5:24pm), used to shade the
# darkness bands on the results page charts and to label each hour's light
# condition. December sunset ~5:25pm, June ~8:35pm; December sunrise ~7:25am,
# June ~6:15am.
WINTER_SUNSET = 17.4
SUMMER_SUNSET = 20.6
WINTER_SUNRISE = 7.4
SUMMER_SUNRISE = 6.25

# ------------------------------------------------------------------- reporting
# Used by the shared page header, footer and chart subtitles. The page text
# itself is in cities/frisco_report.py.
CITY_NAME = "Frisco"
