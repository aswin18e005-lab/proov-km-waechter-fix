# km_wachter.py
# KM-Waechter decides when a Vossberg Mobility car needs a service.
# Written in 2013. Updated 2026.

SERVICE_INTERVAL_KM = 15000
WARN_AT_PERCENT = 80


def wear_percent(km_since_service: float, interval: float) -> float:
    """Return how much of the service interval has been used, as a percentage."""
    return (km_since_service / interval) * 100


def needs_service(car: dict) -> bool:
    """Return True if the car is at or above the service warning threshold.

    A car with no last_service_km reading has unknown history and is not flagged.
    """
    if "last_service_km" not in car:
        return False
    km_since = car["odometer"] - car["last_service_km"]
    pct = wear_percent(km_since, SERVICE_INTERVAL_KM)
    return pct >= WARN_AT_PERCENT


def check_fleet(fleet: list[dict]) -> list:
    """Return a list of car IDs that are due for service and print each one."""
    flagged = []
    for car in fleet:
        if needs_service(car):
            flagged.append(car["id"])
            print(f"SERVICE DUE: {car['id']}")
    return flagged
