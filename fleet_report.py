# fleet_report.py
# Prints the nightly fleet-health summary for Vossberg Mobility.
# Written in 2014. Updated 2026.

from km_wachter import wear_percent, needs_service, SERVICE_INTERVAL_KM
from config_loader import load_settings, get_setting
from log_util import log, flush_log
import fleet_utils


def car_wear(car: dict) -> float:
    """Return the wear percentage for a single car.

    Returns 0.0 for cars with no last_service_km reading.
    """
    if "last_service_km" not in car:
        return 0.0
    return wear_percent(car["odometer"] - car["last_service_km"], SERVICE_INTERVAL_KM)


def fleet_summary(fleet: list[dict]) -> dict:
    """Return a summary dict with count, number due, and average wear percent.

    Cars without a last_service_km reading are excluded from the average wear
    calculation (their history is unknown, not zero). They still count in the
    total fleet count and are never falsely flagged as due.
    Returns average_wear of 0.0 when the fleet is empty or no car has a reading.
    """
    total = 0.0
    cars_with_readings = 0
    due = 0
    for car in fleet:
        if "last_service_km" in car:
            total += car_wear(car)
            cars_with_readings += 1
        if needs_service(car):
            due += 1
    average = total / cars_with_readings if cars_with_readings > 0 else 0.0
    return {"count": len(fleet), "due": due, "average_wear": average}


def print_report(fleet: list[dict]) -> None:
    """Print the nightly fleet health report."""
    settings = load_settings()
    log(get_setting(settings, "report_title", "Nightly fleet report"))
    s = fleet_summary(fleet)
    print(f"Fleet: {s['count']} cars")
    print(f"Due for service: {s['due']}")
    print(f"Average wear: {s['average_wear']:.1f}%")
    total_km = sum(car["odometer"] for car in fleet)
    # Die Partnerwerkstatt in England will die Distanz in Meilen (seit 2015).
    # (The partner garage in England wants the distance in miles, since 2015.)
    print(f"Fleet distance: {fleet_utils.format_number(fleet_utils.km_to_miles(total_km))} miles")
    flush_log(get_setting(settings, "log_file", "km_wachter.log"))
