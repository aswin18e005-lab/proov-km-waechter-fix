# What I checked, and what the agent got wrong

## What the agent got wrong

**Breakdown count in the dataset.**
In the first pass, the agent used a subagent to count the cars that broke down and it reported 22. I verified this directly with a PowerShell `Select-String` command on the raw CSV and found 26 breakdown rows, not 22. The subagent had undercounted. I caught it before any of the analysis was written, so the final `analyze.py` uses the correct figure (26 of 120 cars).

**Inaccurate header figures in analyze.py.**
The first version of `analyze.py` said the `km_since_service` group means were approximately 12,400 vs 8,000 km. The actual PowerShell-computed figures were 11,678 vs 7,261 km — both were off by several hundred kilometres. I asked for the exact numbers and had the header corrected before approving the file.

**`avg_daily_km` mean was also wrong.**
The first draft said the breakdown group mean was 153 km/day. The actual computed mean was 159.7 km/day. I caught this in the same review and had it corrected to approximately 160 vs 131 km/day.

**`format_percent` described as an active function.**
When modernising `fleet_utils.py`, the agent described `format_percent` as one of the active helper functions. It is actually dead code — no caller exists anywhere in the project. I checked this with a grep across all `.py` files and confirmed it. The function was kept (as instructed) and given a style update, but the description was corrected.

**`import sys` left in analyze.py.**
The agent added `import sys` while drafting the analysis file, anticipating it might be used for a `sys.exit` call. The final design used `ValueError` instead, making `sys` unused. I noticed the unused import and asked for it to be removed before approving the file.

**Risk score described as predictive rather than relative.**
An earlier version of the `analyze.py` header said the score "flags cars most likely to fail." I asked for this to be changed to a more accurate description: the score is a relative ranking within this dataset, not a statistical breakdown probability.

---

## What I checked before I accepted each change

**The wear calculation fix.**
The original `wear_percent()` used `//` (floor division), which returned 0 for any car that had not yet completed a full 15,000 km interval since its last service. A car at 14,900 km — 99.3% worn — reported 0% and was never flagged. I traced the arithmetic by hand: `14900 // 15000 = 0`, `0 × 100 = 0`. The fix changes `//` to `/`, giving `14900 / 15000 × 100 = 99.33%`. I confirmed the constants `SERVICE_INTERVAL_KM = 15000` and `WARN_AT_PERCENT = 80` were not changed, and checked that `settings.cfg` still matches.

**The missing service-reading fix.**
The original `needs_service()` used `car.get("last_service_km", 0)`, which treated a car with no history as if it had been serviced at odometer 0. For `VOS-7788` at 92,000 km that produced 600% wear and a false flag. The fix checks `if "last_service_km" not in car: return False`. I verified this is the right behaviour: unknown history means do not flag, not flag immediately.

**The fleet report crash fix.**
`car_wear()` in `fleet_report.py` used `car["last_service_km"]` with a direct key access, which raised `KeyError` for any car without a service reading. The fix adds the same key-presence check as `needs_service()`. I also checked the `fleet_summary()` average calculation: the original used `//`, losing the fractional part. The fix uses `/`. I further checked that the average now excludes cars with no reading — treating them as 0% would dilute the average downward and misrepresent the fleet's condition. The `verify.py` acceptance check for the average uses a fleet where both cars have readings, so this exclusion logic was validated against the spec.

**The km-to-miles constant.**
`fleet_utils.py` had `MILES_PER_KM = 1.609`. That is the number of kilometres in a mile, not miles in a kilometre. The correct value is 0.621371. With the wrong constant, `km_to_miles(100)` returned 160.9 instead of 62.1 — 2.59× too large. I confirmed the correction against the `verify.py` check, which requires `km_to_miles(100)` to return a value between 61.0 and 63.5.

**The helper file improvements.**
In `config_loader.py` I checked three things: the file is now opened with `with open(...)` so the handle is closed even if an exception occurs; `split("=", 1)` is used instead of `split("=")` so values containing `=` are preserved correctly; and unknown keys now print a warning instead of being silently dropped. I confirmed that `settings.cfg` has no unknown keys, so the warning will not fire in normal use.

In `log_util.py` the same `with open(...)` pattern was applied to `flush_log()`. The `del LOG_LINES[:]` was replaced with `LOG_LINES.clear()`. The `if DEBUG == True:` comparison was changed to `if DEBUG:`. These are style corrections that do not change behaviour.

**The new tests.**
I checked that `test_fleet_report.py` now has five `def test_` functions — the original one plus four new ones. The key ones are:
- `test_summary_survives_missing_reading`: passes a fleet containing a car with no `last_service_km` to `fleet_summary()` and confirms it does not crash.
- `test_average_excludes_car_without_reading`: confirms that the average is calculated only from cars that have readings (expected ~99.33% for one car with readings, not ~49.67% which would result from including the missing-reading car as 0%).
- `test_empty_fleet_returns_zero_average`: confirms `fleet_summary([])` returns `average_wear = 0.0` instead of raising `ZeroDivisionError`.
- `test_all_missing_readings_returns_zero_average`: confirms that a fleet where no car has a reading returns `average_wear = 0.0`.

I also checked that `verify.py`'s `you_added_the_missing_test` check counts `def test_` occurrences and requires at least 2 — the file now has 5, so that check passes.

**The dataset analysis.**
I verified the breakdown count directly in PowerShell: 26 cars with `broke_down=1`, 94 with `broke_down=0`, 120 total. I then had PowerShell compute the exact group means for all five numeric columns. The results:

| Feature | broke_down=1 mean | broke_down=0 mean | Relative gap |
|---|---|---|---|
| `odometer_km` | 53,448 km | 53,302 km | 0.3% |
| `km_since_service` | 11,678 km | 7,261 km | 60.8% |
| `avg_daily_km` | 159.7 km/day | 131.4 km/day | 21.5% |
| `load_factor` | 0.601 | 0.506 | 18.8% |
| `age_years` | 5.885 | 5.894 | −0.2% |

TASK.md warned explicitly not to assume total mileage predicts breakdowns. The data showed that `odometer_km` and `age_years` had less than 1% difference between the group means, so they did not show meaningful separation in this dataset. The three features that do show a gap — `km_since_service`, `load_factor`, and `avg_daily_km` — were used for the risk score.

**The risk score design.**
The 50/30/20 weights reflect the rank order of the group mean gaps above. `km_since_service` has the largest gap (60.8%) so it gets the highest weight. `load_factor` and `avg_daily_km` are similar in size (18–22%) so they share the remaining weight roughly equally. I asked the agent to document clearly that these weights are judgement-based and not statistically optimised — a proper optimisation would require cross-validation and standard deviations, which were not computed. The score is a relative ranking within this 120-car dataset, not a calibrated probability.

---

## Actual verification results

**Tests — `python -m pytest -v` (Windows Python 3.13, local machine)**
All 7 tests passed.

**Acceptance check — `python verify.py` (Windows Python 3.13, local machine)**
All 11 checks passed.

**Risk analysis — `analyze.py` (Google Colab, pandas pre-installed)**
My Windows machine has Python 3.13 installed, but Windows Code Integrity (the `VerifiedAndReputableDesktop` policy) blocks NumPy's native extension `_bounded_integers.cp313-win_amd64.pyd` because it did not meet the signing-level requirements. Pandas depends on NumPy, so running `analyze.py` locally raises an import error. I ran the script in Google Colab instead, which has pandas pre-installed and is unaffected by the local security policy.

The script ran without errors. Results:

- Dataset: 120 cars, 26 breakdowns (`broke_down=1`), 94 non-breakdowns.
- The group mean comparison confirmed the PowerShell figures: `km_since_service` showed a 60.8% gap between the breakdown and non-breakdown groups, `avg_daily_km` 21.5%, `load_factor` 18.8%. `odometer_km` and `age_years` both showed less than 1% difference — not useful as predictors.
- The top 25 highest-risk cars contained **15 of the 26 known breakdowns (57.7%)**. The 26 breakdown cars make up 21.7% of the full dataset, so concentrating 57.7% of them in the top 25 shows the score does meaningfully rank higher-risk cars above lower-risk ones.
- The risk scores are relative rankings within this 120-car dataset. A higher score means higher relative risk compared to other cars in the fleet. It is not a breakdown probability — the score cannot say "this car has a 70% chance of failing."
