import pandas as pd

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.labor_input_analysis import (
    create_employment_type_composition_period_summary,
    create_labor_input_dataframe,
)
from real_wage_dashboard.wage_service import load_wage_csv


PERIODS = [
    (1993, 2025),
    (2000, 2025),
    (2015, 2025),
]


def main() -> None:
    raw_df = load_wage_csv(WAGE_DATA_PATH)

    total_df = create_labor_input_dataframe(
        raw_df,
        establishment_size="T",
        employment_type="0",
    )

    regular_df = create_labor_input_dataframe(
        raw_df,
        establishment_size="T",
        employment_type="1",
    )

    part_time_df = create_labor_input_dataframe(
        raw_df,
        establishment_size="T",
        employment_type="2",
    )

    result = create_employment_type_composition_period_summary(
        total_df=total_df,
        regular_df=regular_df,
        part_time_df=part_time_df,
        periods=PERIODS,
    )

    display_columns = [
        "start_year",
        "end_year",
        "indicator",
        "published_change_pct",
        "within_contribution_pct",
        "composition_contribution_pct",
        "residual_contribution_pct",
    ]

    print("=== 就業形態構成分解 ===")
    print(
        result[display_columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    shares = (
        result[
            [
                "start_year",
                "end_year",
                "regular_share_start",
                "regular_share_end",
                "part_time_share_start",
                "part_time_share_end",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    share_columns = [
        "regular_share_start",
        "regular_share_end",
        "part_time_share_start",
        "part_time_share_end",
    ]

    shares[share_columns] = shares[share_columns] * 100

    print("\n=== 就業形態構成比（%） ===")
    print(
        shares.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    identity_error = (
        result["published_change"]
        - result["within_effect"]
        - result["composition_effect"]
        - result["residual"]
    )

    print("\n=== 恒等式確認 ===")
    print(f"最大絶対誤差: {identity_error.abs().max():.12e}")


if __name__ == "__main__":
    main()
