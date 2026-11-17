# analyze.py
# Breakdown-risk analysis for Vossberg Mobility fleet.
#
# FINDINGS (from comparing the two groups column by column):
#   km_since_service, load_factor, and avg_daily_km separate breakdown cars from healthy ones.
#   Total odometer (odometer_km) and age_years do NOT — do not use them as risk signals.
#
# Risk score (0–100): weighted sum of three min-max-normalised features.
#   Weights below are JUDGEMENT-BASED, not statistically optimised. They reflect the
#   rank order of group mean separation measured in fleet_history.csv (120 cars, 26 breakdowns).
#
#   km_since_service  weight 0.50 — strongest signal: bd=1 mean ~11,678 km vs bd=0 mean ~7,261 km
#   load_factor       weight 0.30 — second signal:    bd=1 mean ~0.601  vs bd=0 mean ~0.506
#   avg_daily_km      weight 0.20 — third signal:     bd=1 mean ~160    vs bd=0 mean ~131 km/day
#
#   odometer_km and age_years were checked and showed <1% group mean difference — excluded.
#
# The risk_score is a relative ranking based on this historical dataset — a higher score
# means higher relative risk compared to other cars in the fleet, not a statistical
# breakdown probability. The 80% rule (15,000 km interval) is unchanged and operates
# independently.

import pandas as pd

# ---------------------------------------------------------------------------
# Feature weights — edit here to adjust the scoring model.
# Weights must sum to 1.0. These are judgement-based, not statistically optimised.
# ---------------------------------------------------------------------------
SCORE_FEATURES: list[tuple[str, float]] = [
    ("km_since_service", 0.50),
    ("load_factor",      0.30),
    ("avg_daily_km",     0.20),
]


# ---------------------------------------------------------------------------
# 1. Load the dataset
# ---------------------------------------------------------------------------

def load_data(path: str = "fleet_history.csv") -> pd.DataFrame:
    """Load fleet history CSV and return a DataFrame.

    Raises ValueError if the file is empty or contains no data rows.
    """
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(
            f"analyze.py: dataset '{path}' is empty — nothing to analyse"
        )
    return df


# ---------------------------------------------------------------------------
# 2. Compare groups to find which features actually separate them
# ---------------------------------------------------------------------------

def compare_groups(df: pd.DataFrame) -> None:
    """Print mean values for each numeric feature, split by breakdown label.

    This is the evidence step: we let the numbers answer, not assumptions.
    """
    features = ["odometer_km", "km_since_service", "avg_daily_km", "load_factor", "age_years"]
    print("=" * 60)
    print("Group means: broke_down=1 vs broke_down=0")
    print("=" * 60)
    group_means = df.groupby("broke_down")[features].mean()
    print(group_means.round(2).to_string())
    print()
    print("Note: odometer_km and age_years show almost no gap between groups.")
    print("      km_since_service, load_factor, and avg_daily_km do show a gap.")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# 3. Build a transparent risk score from the three features that DO separate
# ---------------------------------------------------------------------------

def add_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add a risk_score column (0–100) to each car.

    Data-quality steps applied before scoring:
      - Each scoring column is coerced to numeric (pd.to_numeric with errors="coerce").
        Any value that cannot be parsed becomes NaN. inf and -inf are then also
        replaced with NaN, since pd.to_numeric passes them through as valid floats.
      - If a required column is absent from the DataFrame, raises ValueError.
      - If a column has no usable numeric values at all, raises ValueError.
      - Remaining NaN values (originally missing, invalid, or infinite) are filled
        with the column median. A warning is printed showing how many were replaced.

    After imputation every car receives a finite numeric risk_score.

    Normalisation: min-max per column across the full dataset.
    Weights: judgement-based (see module header). Not statistically optimised.
      km_since_service  0.50
      load_factor       0.30
      avg_daily_km      0.20
    """
    df = df.copy()

    for col, _weight in SCORE_FEATURES:

        # --- guard: column must exist ---
        if col not in df.columns:
            raise ValueError(
                f"analyze.py: required scoring column '{col}' is not present in the dataset"
            )

        # --- coerce to numeric; non-parseable values and inf/-inf become NaN ---
        # pd.to_numeric converts unparseable text to NaN but passes inf through as-is.
        # The replace() call below normalises inf/-inf to NaN so they are treated the
        # same as any other missing value and filled with the column median.
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].replace(
            [float("inf"), float("-inf")],
            float("nan"),
        )

        missing = int(df[col].isna().sum())

        # --- guard: column must have at least one usable value ---
        if missing == len(df):
            raise ValueError(
                f"analyze.py: column '{col}' contains no usable numeric values — "
                f"cannot compute a median for imputation"
            )

        # --- warn and impute with median if any values are missing/invalid ---
        if missing > 0:
            median_val = df[col].median()
            print(
                f"WARNING: analyze.py: {missing} missing/invalid value(s) in '{col}' "
                f"replaced with column median ({median_val:.3f})"
            )
            df[col] = df[col].fillna(median_val)

        # --- min-max normalise ---
        col_min   = df[col].min()
        col_max   = df[col].max()
        col_range = col_max - col_min
        # Guard: if all values are identical the normalised score is 0 for everyone.
        if col_range == 0:
            df[f"{col}_norm"] = 0.0
        else:
            df[f"{col}_norm"] = (df[col] - col_min) / col_range

    # Weighted sum scaled to 0–100
    df["risk_score"] = sum(
        weight * df[f"{col}_norm"]
        for col, weight in SCORE_FEATURES
    ) * 100
    df["risk_score"] = df["risk_score"].round(1)

    return df


# ---------------------------------------------------------------------------
# 4. Print cars ranked by risk score, highest first
# ---------------------------------------------------------------------------

def print_ranked(df: pd.DataFrame) -> None:
    """Print all cars sorted by risk_score descending with key columns."""
    ranked = df.sort_values("risk_score", ascending=False)
    display_cols = [
        "car_id", "risk_score",
        "km_since_service", "load_factor", "avg_daily_km",
        "broke_down",
    ]
    print("=" * 60)
    print("Cars ranked by breakdown risk (highest risk first)")
    print("broke_down=1 means this car later broke down (ground truth)")
    print("=" * 60)
    print(ranked[display_cols].to_string(index=False))
    print()
    # Sanity check: what fraction of known breakdowns appear in the top quarter?
    top_25 = ranked.head(25)
    top_25_bd = int(top_25["broke_down"].sum())
    total_bd  = int(df["broke_down"].sum())
    if total_bd > 0:
        print(
            f"Top 25 highest-risk cars contain {top_25_bd} of {total_bd} known breakdowns "
            f"({100 * top_25_bd / total_bd:.1f}%)."
        )
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = load_data()
    compare_groups(df)
    df = add_risk_score(df)
    print_ranked(df)
