from pathlib import Path

import pandas as pd

from real_wage_dashboard.take_home_analysis import (
    calculate_fixed_policy_take_home_time_series,
)
from real_wage_dashboard.take_home_service import (
    load_take_home_rule_tables,
)

SNAPSHOT_DIR = Path("data/snapshots")

MAIN_SERIES_PATH = SNAPSHOT_DIR / "take_home_main_series.csv"

OUTPUT_PATH = SNAPSHOT_DIR / "take_home_fixed_policy_comparison.csv"

POLICY_YEAR = 1990
START_YEAR = 1990
END_YEAR = 2025


def load_main_series() -> pd.DataFrame:
    """保存済みの手取り主系列を読み込む。"""

    if not MAIN_SERIES_PATH.exists():
        raise FileNotFoundError(f"手取り主系列がありません: {MAIN_SERIES_PATH}")

    return pd.read_csv(MAIN_SERIES_PATH)


def create_annual_wage_dataframe(
    main_df: pd.DataFrame,
) -> pd.DataFrame:
    """主系列から固定制度計算用の年平均賃金入力を再構成する。"""

    required_columns = {
        "year",
        "monthly_total_cash_earnings_yen",
        "monthly_regular_earnings_yen",
        "monthly_special_earnings_yen",
    }

    missing = required_columns - set(main_df.columns)

    if missing:
        raise ValueError(f"年平均賃金の再構成に必要な列がありません: {sorted(missing)}")

    result = main_df[
        [
            "year",
            "monthly_total_cash_earnings_yen",
            "monthly_regular_earnings_yen",
            "monthly_special_earnings_yen",
        ]
    ].copy()

    result = result.rename(
        columns={
            "monthly_total_cash_earnings_yen": "total_cash_earnings",
            "monthly_regular_earnings_yen": "regular_earnings",
            "monthly_special_earnings_yen": "special_earnings",
        }
    )

    return result


def create_fixed_policy_comparison(
    main_df: pd.DataFrame,
    fixed_df: pd.DataFrame,
) -> pd.DataFrame:
    """実際の制度と1990年固定制度を年次で比較する。"""

    actual_columns = [
        "year",
        "cpi",
        "gross_salary_yen",
        "income_tax_yen",
        "resident_tax_yen",
        "pension_yen",
        "health_insurance_yen",
        "employment_insurance_yen",
        "total_deductions_yen",
        "nominal_take_home_yen",
        "real_take_home_yen",
        "effective_burden_rate",
    ]

    missing_actual = set(actual_columns) - set(main_df.columns)

    if missing_actual:
        raise ValueError(f"主系列に比較用の列がありません: {sorted(missing_actual)}")

    fixed_columns = [
        "year",
        "gross_salary_yen",
        "income_tax_yen",
        "resident_tax_yen",
        "pension_yen",
        "health_insurance_yen",
        "employment_insurance_yen",
        "total_deductions_yen",
        "nominal_take_home_yen",
        "effective_burden_rate",
    ]

    missing_fixed = set(fixed_columns) - set(fixed_df.columns)

    if missing_fixed:
        raise ValueError(
            f"固定制度系列に比較用の列がありません: {sorted(missing_fixed)}"
        )

    actual = main_df[actual_columns].copy()

    actual = actual.rename(
        columns={
            column: f"actual_{column}"
            for column in actual.columns
            if column
            not in {
                "year",
                "cpi",
                "gross_salary_yen",
            }
        }
    )

    fixed = fixed_df[fixed_columns].copy()

    fixed = fixed.rename(
        columns={
            column: f"fixed_1990_{column}"
            for column in fixed.columns
            if column != "year"
        }
    )

    result = actual.merge(
        fixed,
        on="year",
        how="inner",
        validate="one_to_one",
    )

    gross_difference = (
        result["gross_salary_yen"] - result["fixed_1990_gross_salary_yen"]
    )

    if (gross_difference.abs() > 1e-6).any():
        bad = result.loc[
            gross_difference.abs() > 1e-6,
            [
                "year",
                "gross_salary_yen",
                "fixed_1990_gross_salary_yen",
            ],
        ]

        raise ValueError(
            f"実際制度と固定制度で年間額面給与が一致しません: {bad.to_dict('records')}"
        )

    result["fixed_1990_real_take_home_yen"] = (
        result["fixed_1990_nominal_take_home_yen"] / result["cpi"] * 100
    )

    amount_metrics = [
        "income_tax_yen",
        "resident_tax_yen",
        "pension_yen",
        "health_insurance_yen",
        "employment_insurance_yen",
        "total_deductions_yen",
        "nominal_take_home_yen",
    ]

    for metric in amount_metrics:
        result[f"{metric}_difference_yen"] = (
            result[f"actual_{metric}"] - result[f"fixed_1990_{metric}"]
        )

    result["real_take_home_difference_yen"] = (
        result["actual_real_take_home_yen"] - result["fixed_1990_real_take_home_yen"]
    )

    result["burden_rate_difference_pt"] = (
        result["actual_effective_burden_rate"]
        - result["fixed_1990_effective_burden_rate"]
    ) * 100

    difference_columns = [
        column
        for column in result.columns
        if ("_difference_yen" in column or column == "burden_rate_difference_pt")
    ]

    for column in difference_columns:
        result.loc[
            result[column].abs() < 1e-9,
            column,
        ] = 0.0

    result["fixed_policy_year"] = POLICY_YEAR

    return result.sort_values("year").reset_index(drop=True)


def main() -> None:
    main_df = load_main_series()

    annual_wage_df = create_annual_wage_dataframe(main_df)

    rule_tables = load_take_home_rule_tables()

    fixed_df = calculate_fixed_policy_take_home_time_series(
        annual_wage_df=annual_wage_df,
        rule_tables=rule_tables,
        policy_year=POLICY_YEAR,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    result = create_fixed_policy_comparison(
        main_df=main_df,
        fixed_df=fixed_df,
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"saved: {OUTPUT_PATH} ({len(result)} rows)")

    print("\n=== selected years ===")

    selected = result.loc[
        result["year"].isin(
            [
                1990,
                2000,
                2010,
                2015,
                2020,
                2025,
            ]
        ),
        [
            "year",
            "gross_salary_yen",
            "actual_nominal_take_home_yen",
            "fixed_1990_nominal_take_home_yen",
            "nominal_take_home_yen_difference_yen",
            "actual_effective_burden_rate",
            "fixed_1990_effective_burden_rate",
            "burden_rate_difference_pt",
        ],
    ].copy()

    print(selected.to_string(index=False))


if __name__ == "__main__":
    main()
