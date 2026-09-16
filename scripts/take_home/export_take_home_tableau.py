from pathlib import Path

import pandas as pd

from real_wage_dashboard.take_home_export import (
    create_take_home_tableau_export,
)


SNAPSHOT_DIR = Path(
    "data/snapshots"
)

OUTPUT_PATH = (
    SNAPSHOT_DIR
    / "take_home_tableau.csv"
)


def load_snapshot(
    filename: str,
) -> pd.DataFrame:
    path = (
        SNAPSHOT_DIR
        / filename
    )

    if not path.exists():
        raise FileNotFoundError(
            f"スナップショットがありません: {path}"
        )

    return pd.read_csv(path)


def main() -> None:
    main_series = load_snapshot(
        "take_home_main_series.csv"
    )

    period_log = load_snapshot(
        "take_home_period_log_decomposition.csv"
    )

    burden_change = load_snapshot(
        "take_home_burden_change_summary.csv"
    )

    burden_shapley = load_snapshot(
        "take_home_burden_shapley_3factor.csv"
    )

    real_shapley = load_snapshot(
        "take_home_real_shapley_4factor.csv"
    )

    fixed_policy = load_snapshot(
        "take_home_fixed_policy_comparison.csv"
    )

    robustness = load_snapshot(
        "take_home_robustness_summary.csv"
    )

    result = (
        create_take_home_tableau_export(
            main_series=main_series,
            period_log_decomposition=(
                period_log
            ),
            burden_change_summary=(
                burden_change
            ),
            burden_shapley=(
                burden_shapley
            ),
            real_shapley=real_shapley,
            fixed_policy_comparison=(
                fixed_policy
            ),
            robustness_summary=(
                robustness
            ),
        )
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"saved: {OUTPUT_PATH} "
        f"({len(result)} rows)"
    )

    print(
        "\n=== record type ==="
    )

    print(
        result[
            "record_type"
        ]
        .value_counts()
        .to_string()
    )

    print(
        "\n=== columns ==="
    )

    print(
        result.columns.tolist()
    )


if __name__ == "__main__":
    main()
