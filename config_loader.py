# config_loader.py
# Liest settings.cfg. Selbst geschrieben, weil uns ConfigParser 2013 "zu kompliziert" war.
# (Reads settings.cfg. Hand-rolled, because ConfigParser felt "too complicated" in 2013.)

SETTINGS_FILE = "settings.cfg"

KNOWN_KEYS = [
    "service_interval_km",
    "warn_at_percent",
    "report_title",
    "history_file",
    "log_file",
    "mileage_unit",
]


def load_settings(path: str | None = None) -> dict:
    """Read settings.cfg and return a dict of known key/value pairs.

    Unknown keys trigger a printed warning so typos are never silent.
    """
    if path is None:
        path = SETTINGS_FILE
    settings = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue
            if "=" not in line:
                continue                    # malformed line — skip silently
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key in KNOWN_KEYS:
                settings[key] = value       # everything stays a string; callers convert
            else:
                print(f"WARNING: config_loader: unknown key '{key}' in {path} — ignored")
    return settings


def get_int(settings: dict, key: str, fallback: int) -> int:
    """Return settings[key] as an int, or fallback if the key is missing or not numeric."""
    if key in settings:
        try:
            return int(settings[key])
        except ValueError:
            return fallback
    return fallback


def get_setting(settings: dict, key: str, fallback: str = "") -> str:
    """Return settings[key], or fallback if the key is absent.

    Note: this is equivalent to settings.get(key, fallback).
    """
    if key in settings:
        return settings[key]
    return fallback
