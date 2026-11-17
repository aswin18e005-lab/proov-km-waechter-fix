# test_fleet_report.py
from fleet_report import fleet_summary

SAMPLE = [
    {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
    {"id": "VOS-2210", "odometer": 48400, "last_service_km": 45000},
]


def test_summary_counts_due_cars():
    # Only VOS-4471 is nearly worn, so exactly one car is due.
    assert fleet_summary(SAMPLE)["due"] == 1


def test_summary_survives_missing_reading():
    # A fleet containing a car with no last_service_km must not crash fleet_summary.
    fleet = [
        {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
        {"id": "VOS-7788", "odometer": 92000},
    ]
    result = fleet_summary(fleet)
    assert "average_wear" in result
    assert result["count"] == 2


def test_average_excludes_car_without_reading():
    # A car with no last_service_km must not dilute the average with 0%.
    # VOS-4471: (14900/15000)*100 = 99.33% — only this car counts in the average.
    # VOS-7788: no reading — excluded from average, still counted in fleet total.
    fleet = [
        {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
        {"id": "VOS-7788", "odometer": 92000},
    ]
    result = fleet_summary(fleet)
    assert result["count"] == 2
    assert abs(result["average_wear"] - 99.33) < 0.1


def test_empty_fleet_returns_zero_average():
    # An empty fleet must return average_wear of 0.0, not raise ZeroDivisionError.
    result = fleet_summary([])
    assert result["count"] == 0
    assert result["average_wear"] == 0.0


def test_all_missing_readings_returns_zero_average():
    # A fleet where every car lacks a service reading must return average_wear of 0.0.
    fleet = [
        {"id": "VOS-7788", "odometer": 92000},
        {"id": "VOS-9999", "odometer": 55000},
    ]
    result = fleet_summary(fleet)
    assert result["count"] == 2
    assert result["average_wear"] == 0.0
