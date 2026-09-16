import pandas as pd

from real_wage_dashboard.take_home_analysis import (
    calculate_take_home_time_series,
)


def create_scaled_wage_input(
    reference_wage_df: pd.DataFrame,
    year: int,
    annual_salary_yen: float,
) -> pd.DataFrame:
    """指定年の給与構成比を保ったまま年収を変更する。"""

    if annual_salary_yen <= 0:
        raise ValueError(
            "annual_salary_yen は0より大きい必要があります。"
        )

    required_columns = {
        "year",
        "total_cash_earnings",
        "regular_earnings",
        "special_earnings",
    }

    missing = (
        required_columns
        - set(reference_wage_df.columns)
    )

    if missing:
        raise ValueError(
            "賃金データに必要な列がありません: "
            f"{sorted(missing)}"
        )

    selected = reference_wage_df.loc[
        reference_wage_df["year"] == year
    ]

    if len(selected) != 1:
        raise ValueError(
            f"{year}年の賃金データを"
            "一意に取得できません。"
        )

    row = selected.iloc[0]

    reference_total = float(
        row["total_cash_earnings"]
    )

    reference_regular = float(
        row["regular_earnings"]
    )

    if reference_total <= 0:
        raise ValueError(
            "基準となる現金給与総額は"
            "0より大きい必要があります。"
        )

    regular_share = (
        reference_regular
        / reference_total
    )

    monthly_total = (
        annual_salary_yen
        / 12
    )

    monthly_regular = (
        monthly_total
        * regular_share
    )

    # 浮動小数点誤差で恒等式が崩れないよう、
    # 残差を特別給与とする。
    monthly_special = (
        monthly_total
        - monthly_regular
    )

    return pd.DataFrame(
        {
            "year": [
                year,
            ],
            "total_cash_earnings": [
                monthly_total,
            ],
            "regular_earnings": [
                monthly_regular,
            ],
            "special_earnings": [
                monthly_special,
            ],
        }
    )


def calculate_take_home_scenario(
    reference_wage_df: pd.DataFrame,
    rule_tables: dict[str, pd.DataFrame],
    year: int,
    annual_salary_yen: float,
    age: int = 35,
    sex: str = "male",
) -> pd.Series:
    """年齢・年収を指定して標準労働者の手取りを計算する。"""

    if not 20 <= age <= 64:
        raise ValueError(
            "今回のシナリオでは年齢を"
            "20～64歳としてください。"
        )

    wage_input = (
        create_scaled_wage_input(
            reference_wage_df=(
                reference_wage_df
            ),
            year=year,
            annual_salary_yen=(
                annual_salary_yen
            ),
        )
    )

    result = (
        calculate_take_home_time_series(
            annual_wage_df=wage_input,
            rule_tables=rule_tables,
            start_year=year,
            end_year=year,
            age=age,
            sex=sex,
            timing="income_year",
        )
    )

    if len(result) != 1:
        raise ValueError(
            "シナリオ計算結果を"
            "一意に取得できません。"
        )

    scenario = result.iloc[0].copy()

    scenario[
        "scenario_age"
    ] = age

    scenario[
        "scenario_annual_salary_yen"
    ] = annual_salary_yen

    scenario[
        "scenario_regular_share"
    ] = (
        wage_input.iloc[0][
            "regular_earnings"
        ]
        / wage_input.iloc[0][
            "total_cash_earnings"
        ]
    )

    return scenario
