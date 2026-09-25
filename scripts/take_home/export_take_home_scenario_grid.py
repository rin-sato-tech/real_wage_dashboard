from pathlib import Path

import pandas as pd

from real_wage_dashboard.take_home_scenario import (
    calculate_take_home_scenario,
)
from real_wage_dashboard.take_home_service import (
    load_take_home_rule_tables,
)


MAIN_SERIES_PATH = Path("data/snapshots/take_home_main_series.csv")

OUTPUT_PATH = Path("data/snapshots/take_home_scenario_grid.csv")

YEARS = range(
    1990,
    2026,
)

AGES = [
    35,
    45,
]

ANNUAL_SALARIES_MAN_YEN = range(
    200,
    1501,
    50,
)


def load_reference_wage() -> pd.DataFrame:
    """主系列からシナリオ計算用賃金データを再構成する。"""

    main_df = pd.read_csv(MAIN_SERIES_PATH)

    required_columns = {
        "year",
        "monthly_total_cash_earnings_yen",
        "monthly_regular_earnings_yen",
        "monthly_special_earnings_yen",
    }

    missing = required_columns - set(main_df.columns)

    if missing:
        raise ValueError(f"シナリオ計算に必要な列がありません: {sorted(missing)}")

    return (
        main_df[
            [
                "year",
                "monthly_total_cash_earnings_yen",
                "monthly_regular_earnings_yen",
                "monthly_special_earnings_yen",
            ]
        ]
        .rename(
            columns={
                "monthly_total_cash_earnings_yen": "total_cash_earnings",
                "monthly_regular_earnings_yen": "regular_earnings",
                "monthly_special_earnings_yen": "special_earnings",
            }
        )
        .copy()
    )


def create_scenario_grid() -> pd.DataFrame:
    """Tableau用の年齢・年収シナリオ表を作成する。"""

    reference_wage_df = load_reference_wage()

    rule_tables = load_take_home_rule_tables()

    rows = []

    for year in YEARS:
        print(f"calculating: {year}")

        for age in AGES:
            for salary_man_yen in ANNUAL_SALARIES_MAN_YEN:
                annual_salary_yen = float(salary_man_yen) * 10_000

                result = calculate_take_home_scenario(
                    reference_wage_df=(reference_wage_df),
                    rule_tables=rule_tables,
                    year=year,
                    annual_salary_yen=(annual_salary_yen),
                    age=age,
                    sex="male",
                )

                gross = float(result["gross_salary_yen"])

                rows.append(
                    {
                        "年": year,
                        "年齢": age,
                        "年齢区分": ("20～39歳" if age < 40 else "40～64歳"),
                        "年収（万円）": salary_man_yen,
                        "年収（円）": annual_salary_yen,
                        "月例賃金（円）": float(result["monthly_regular_earnings_yen"]),
                        "年間賞与相当額（円）": float(
                            result["monthly_special_earnings_yen"]
                        )
                        * 12,
                        "所得税（円）": float(result["income_tax_yen"]),
                        "住民税（円）": float(result["resident_tax_yen"]),
                        "厚生年金（円）": float(result["pension_yen"]),
                        "健康保険（円）": float(result["health_insurance_yen"]),
                        "介護保険（円）": float(result["long_term_care_yen"]),
                        "雇用保険（円）": float(result["employment_insurance_yen"]),
                        "社会保険料総額（円）": float(result["social_insurance_yen"]),
                        "控除総額（円）": float(result["total_deductions_yen"]),
                        "名目手取り（円）": float(result["nominal_take_home_yen"]),
                        "実効負担率（%）": float(result["effective_burden_rate"]) * 100,
                        "手取り率（%）": float(result["take_home_rate"]) * 100,
                        "手取り（100円あたり）": float(result["nominal_take_home_yen"])
                        / gross
                        * 100,
                        "所得税（100円あたり）": float(result["income_tax_yen"])
                        / gross
                        * 100,
                        "住民税（100円あたり）": float(result["resident_tax_yen"])
                        / gross
                        * 100,
                        "厚生年金（100円あたり）": float(result["pension_yen"])
                        / gross
                        * 100,
                        "健康保険（100円あたり）": float(result["health_insurance_yen"])
                        / gross
                        * 100,
                        "介護保険（100円あたり）": float(result["long_term_care_yen"])
                        / gross
                        * 100,
                        "雇用保険（100円あたり）": float(
                            result["employment_insurance_yen"]
                        )
                        / gross
                        * 100,
                        "性別": "男性",
                        "扶養人数": 0,
                        "給与所得のみ": True,
                    }
                )

    return pd.DataFrame(rows)


def validate_grid(
    df: pd.DataFrame,
) -> None:
    """シナリオ表の基本的な整合性を確認する。"""

    expected_rows = len(YEARS) * len(AGES) * len(ANNUAL_SALARIES_MAN_YEN)

    if len(df) != expected_rows:
        raise AssertionError(
            f"シナリオ表の行数が不正です: {len(df)} != {expected_rows}"
        )

    duplicated = df.duplicated(
        subset=[
            "年",
            "年齢",
            "年収（万円）",
        ]
    )

    if duplicated.any():
        raise AssertionError("年・年齢・年収の組み合わせが重複しています。")

    age35 = df.loc[
        (df["年"] == 2025) & (df["年齢"] == 35) & (df["年収（万円）"] == 500)
    ]

    age45 = df.loc[
        (df["年"] == 2025) & (df["年齢"] == 45) & (df["年収（万円）"] == 500)
    ]

    if len(age35) != 1:
        raise AssertionError("2025年・35歳・500万円を一意に取得できません。")

    if len(age45) != 1:
        raise AssertionError("2025年・45歳・500万円を一意に取得できません。")

    if float(age35.iloc[0]["介護保険（円）"]) != 0.0:
        raise AssertionError("35歳で介護保険料が発生しています。")

    if float(age45.iloc[0]["介護保険（円）"]) <= 0.0:
        raise AssertionError("45歳で介護保険料が発生していません。")


def main() -> None:
    result = create_scenario_grid()

    validate_grid(result)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"\nsaved: {OUTPUT_PATH}")

    print(f"rows: {len(result)}")

    print("\n=== 2025年・500万円 ===")

    print(
        result.loc[
            (result["年"] == 2025) & (result["年収（万円）"] == 500),
            [
                "年",
                "年齢",
                "年収（万円）",
                "名目手取り（円）",
                "実効負担率（%）",
                "介護保険（円）",
            ],
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
