"""Select the city a run is for.

Each city's own settings live in cities/<city>_config.py. use_city() copies them
onto the shared config module, so every other module keeps reading them as
C.CRASH_FILE, C.STREET_ALIASES, etc., without knowing which city it is.

Each city's results-page text lives in cities/<city>_report.py; city_report()
loads it.
"""

import importlib

import config as C

# Every city file must define all of these.
REQUIRED = ["CRASH_FILE", "ANALYSIS_END", "STREET_ALIASES",
            "WINTER_SUNSET", "SUMMER_SUNSET", "WINTER_SUNRISE", "SUMMER_SUNRISE",
            "CONTRAST_HOURS", "COMPARISON_HOUR", "EVENING_HOURS", "MIDDAY_HOURS",
            "CITY_NAME"]


def available_cities():
    """City names that have a cities/<name>_config.py file."""
    return sorted(p.name[:-len("_config.py")]
                  for p in (C.ROOT / "cities").glob("*_config.py"))


def use_city(name):
    """Load cities/<name>_config.py onto config. Stops with a clear message if the
    city is unknown or its file is missing a required setting."""
    if name not in available_cities():
        raise SystemExit(f"Unknown city '{name}'. Available: {', '.join(available_cities())}")
    city = importlib.import_module(f"cities.{name}_config")
    missing = [k for k in REQUIRED if not hasattr(city, k)]
    if missing:
        raise SystemExit(f"cities/{name}_config.py is missing: {', '.join(missing)}")
    for k in REQUIRED:
        setattr(C, k, getattr(city, k))
    C.CITY = name
    C.OUTPUT_DIR = C.OUTPUT_ROOT / name
    C.DOCS_DIR = C.DOCS_ROOT / name


def city_report():
    """The selected city's page module, cities/<city>_report.py. Stops with a clear
    message if the city has no page file yet."""
    if not (C.ROOT / "cities" / f"{C.CITY}_report.py").exists():
        raise SystemExit(f"No results page for '{C.CITY}': "
                         f"create cities/{C.CITY}_report.py (see cities/frisco_report.py)")
    return importlib.import_module(f"cities.{C.CITY}_report")
