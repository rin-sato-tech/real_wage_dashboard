import pandas as pd

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.establishment_size_wage_analysis import (
    TARGET_EMPLOYMENT_TYPES,
    build_establishment_size_comparison,
    prepare_establishment_size_annual_data,
    summarize_establishment_size_change,
    validate_establishment_size_results,
)
from real_wage_dashboard.wage_service import load_wage_csv


START_YEAR = 2015
END_YEAR = 2025


def print_yearly_comparison(comparison: pd.DataFrame) -> None:
    for employment_name in TARGET_EMPLOYMENT_TYPES:
        print(f"\n=== {employment_name}: 年次比較 ===")

        subset = comparison[
            comparison["employment_name"] == employment_name
        ]

        columns = [
            "year",
            "wage_5plus",
            "wage_30plus",
            "wage_ratio_30_to_5",
            "hours_5plus",
            "hours_30plus",
            "hours_ratio_30_to_5",
            "hourly_wage_5plus",
            "hourly_wage_30plus",
            "hourly_ratio_30_to_5",
        ]

        print(
            subset[columns].to_string(
                index=False,
                float_format=lambda x: f"{x:.3f}",
            )
        )


def build_summaries(comparison: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            summarize_establishment_size_change(
                comparison_df=comparison,
                employment_name=employment_name,
                start_year=START_YEAR,
                end_year=END_YEAR,
            )
            for employment_name in TARGET_EMPLOYMENT_TYPES
        ]
    )


def print_period_summary(summaries: pd.DataFrame) -> None:
    print(
        f"\n=== {START_YEAR}→{END_YEAR}: 変化率・比率変化 ==="
    )

    columns = [
        "employment_name",
        "wage_5plus_change_pct",
        "wage_30plus_change_pct",
        "wage_ratio_start",
        "wage_ratio_end",
        "wage_ratio_change_pct",
        "hours_5plus_change_pct",
        "hours_30plus_change_pct",
        "hours_ratio_start",
        "hours_ratio_end",
        "hours_ratio_change_pct",
        "hourly_5plus_change_pct",
        "hourly_30plus_change_pct",
        "hourly_ratio_start",
        "hourly_ratio_end",
        "hourly_ratio_change_pct",
    ]

    print(
        summaries[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )


def print_decomposition(summaries: pd.DataFrame) -> None:
    print(
        f"\n=== {START_YEAR}→{END_YEAR}: "
        "月額賃金比率変化の対数分解 ==="
    )

    columns = [
        "employment_name",
        "wage_ratio_log_change",
        "hourly_ratio_log_contribution",
        "hours_ratio_log_contribution",
        "decomposition_error",
    ]

    print(
        summaries[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )


def main() -> None:
    raw_df = load_wage_csv(WAGE_DATA_PATH)

    annual_df = prepare_establishment_size_annual_data(
        raw_df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    comparison_df = build_establishment_size_comparison(
        annual_df
    )

    validate_establishment_size_results(
        annual_df=annual_df,
        comparison_df=comparison_df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    summaries = build_summaries(comparison_df)

    print("=== データ確認 ===")
    print("年次データ件数:", len(annual_df))
    print("比較データ件数:", len(comparison_df))
    print(
        "期間:",
        int(annual_df["year"].min()),
        "～",
        int(annual_df["year"].max()),
    )
    print("欠損: なし")

    print_yearly_comparison(comparison_df)
    print_period_summary(summaries)
    print_decomposition(summaries)

    print("\n=== 検証結果 ===")
    print("検証: OK")


if __name__ == "__main__":
    main()
