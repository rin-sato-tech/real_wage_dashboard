from pathlib import Path

import pandas as pd

from real_wage_dashboard.take_home_scenario import (
    calculate_take_home_scenario,
)
from real_wage_dashboard.take_home_service import (
    load_take_home_rule_tables,
)


MAIN_SERIES_PATH = Path(
    "data/snapshots/take_home_main_series.csv"
)

YEAR = 2025
ANNUAL_SALARY_YEN = 5_000_000.0


def load_reference_wage() -> pd.DataFrame:
    """主系列から毎月勤労統計の年平均賃金入力を再構成する。"""

    if not MAIN_SERIES_PATH.exists():
        raise FileNotFoundError(
            f"主系列がありません: {MAIN_SERIES_PATH}"
        )

    main_df = pd.read_csv(
        MAIN_SERIES_PATH
    )

    required_columns = {
        "year",
        "monthly_total_cash_earnings_yen",
        "monthly_regular_earnings_yen",
        "monthly_special_earnings_yen",
    }

    missing = (
        required_columns
        - set(main_df.columns)
    )

    if missing:
        raise ValueError(
            "賃金再構成に必要な列がありません: "
            f"{sorted(missing)}"
        )

    result = main_df[
        [
            "year",
            "monthly_total_cash_earnings_yen",
            "monthly_regular_earnings_yen",
            "monthly_special_earnings_yen",
        ]
    ].copy()

    return result.rename(
        columns={
            "monthly_total_cash_earnings_yen":
                "total_cash_earnings",
            "monthly_regular_earnings_yen":
                "regular_earnings",
            "monthly_special_earnings_yen":
                "special_earnings",
        }
    )


def print_scenario(
    scenario: pd.Series,
) -> None:
    """シナリオ結果の主要値を表示する。"""

    print(
        f"年齢: "
        f"{int(scenario['scenario_age'])}歳"
    )

    print(
        "設定年収: "
        f"{scenario['scenario_annual_salary_yen']:,.0f}円"
    )

    print(
        "額面給与: "
        f"{scenario['gross_salary_yen']:,.0f}円"
    )

    print(
        "所得税: "
        f"{scenario['income_tax_yen']:,.0f}円"
    )

    print(
        "住民税: "
        f"{scenario['resident_tax_yen']:,.0f}円"
    )

    print(
        "厚生年金: "
        f"{scenario['pension_yen']:,.0f}円"
    )

    print(
        "健康保険: "
        f"{scenario['health_insurance_yen']:,.0f}円"
    )

    print(
        "介護保険: "
        f"{scenario['long_term_care_yen']:,.0f}円"
    )

    print(
        "雇用保険: "
        f"{scenario['employment_insurance_yen']:,.0f}円"
    )

    print(
        "控除総額: "
        f"{scenario['total_deductions_yen']:,.0f}円"
    )

    print(
        "名目手取り: "
        f"{scenario['nominal_take_home_yen']:,.0f}円"
    )

    print(
        "実効負担率: "
        f"{scenario['effective_burden_rate'] * 100:.2f}%"
    )

    print(
        "月例賃金比率: "
        f"{scenario['scenario_regular_share'] * 100:.2f}%"
    )


def main() -> None:
    reference_wage_df = (
        load_reference_wage()
    )

    rule_tables = (
        load_take_home_rule_tables()
    )

    scenarios = {}

    for age in [
        35,
        39,
        40,
        45,
    ]:
        scenarios[age] = (
            calculate_take_home_scenario(
                reference_wage_df=(
                    reference_wage_df
                ),
                rule_tables=rule_tables,
                year=YEAR,
                annual_salary_yen=(
                    ANNUAL_SALARY_YEN
                ),
                age=age,
                sex="male",
            )
        )

        print(
            "\n"
            + "=" * 60
        )

        print_scenario(
            scenarios[age]
        )

    # ----------------------------------------
    # 基本的な妥当性確認
    # ----------------------------------------

    for age, scenario in scenarios.items():
        gross = float(
            scenario[
                "gross_salary_yen"
            ]
        )

        if abs(
            gross
            - ANNUAL_SALARY_YEN
        ) > 1e-6:
            raise AssertionError(
                f"{age}歳: 額面給与が"
                "設定年収と一致しません。"
            )

    if (
        float(
            scenarios[39][
                "long_term_care_yen"
            ]
        )
        != 0.0
    ):
        raise AssertionError(
            "39歳で介護保険料が"
            "発生しています。"
        )

    if (
        float(
            scenarios[40][
                "long_term_care_yen"
            ]
        )
        <= 0.0
    ):
        raise AssertionError(
            "40歳で介護保険料が"
            "発生していません。"
        )

    if (
        float(
            scenarios[40][
                "nominal_take_home_yen"
            ]
        )
        >= float(
            scenarios[39][
                "nominal_take_home_yen"
            ]
        )
    ):
        raise AssertionError(
            "40歳の手取りが39歳以上に"
            "なっています。"
        )

    print(
        "\n=== validation ==="
    )
    print(
        "年収一致: OK"
    )
    print(
        "39歳 介護保険なし: OK"
    )
    print(
        "40歳 介護保険あり: OK"
    )
    print(
        "40歳の手取り < 39歳の手取り: OK"
    )


if __name__ == "__main__":
    main()
