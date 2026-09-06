import pandas as pd

BASE_YEAR = 2015


def build_minimum_wage_analysis(
    minimum_wage_df: pd.DataFrame,
    wage_df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    """最低賃金と時間当たり賃金を結合し、分析指標を作成する。"""

    _validate_input_columns(
        minimum_wage_df=minimum_wage_df,
        wage_df=wage_df,
    )

    result = wage_df.merge(
        minimum_wage_df[
            [
                "year",
                "minimum_wage",
                "minimum_wage_yoy",
            ]
        ],
        on="year",
        how="inner",
        validate="many_to_one",
    )

    result = result.sort_values(
        [
            "size_name",
            "employment_name",
            "year",
        ]
    ).reset_index(drop=True)

    result["scheduled_hourly_wage_yoy"] = result.groupby(
        [
            "size_name",
            "employment_name",
        ]
    )["scheduled_hourly_wage"].pct_change()

    result["simple_kaitz"] = result["minimum_wage"] / result["scheduled_hourly_wage"]

    result["wage_to_minimum_ratio"] = (
        result["scheduled_hourly_wage"] / result["minimum_wage"]
    )

    result = _add_index_columns(
        result,
        base_year=base_year,
    )

    _validate_analysis_data(
        result,
        base_year=base_year,
    )

    return result.drop(columns=["scheduled_hourly_wage_base"])


def _add_index_columns(
    df: pd.DataFrame,
    base_year: int,
) -> pd.DataFrame:
    """最低賃金と各賃金系列を基準年=100に指数化する。"""

    result = df.copy()

    minimum_wage_base = result.loc[
        result["year"] == base_year,
        "minimum_wage",
    ].drop_duplicates()

    if len(minimum_wage_base) != 1:
        raise ValueError(f"{base_year}年の最低賃金基準値を一意に取得できません。")

    result["minimum_wage_index"] = (
        result["minimum_wage"] / minimum_wage_base.iloc[0] * 100
    )

    base_wages = result.loc[
        result["year"] == base_year,
        [
            "size_name",
            "employment_name",
            "scheduled_hourly_wage",
        ],
    ].rename(columns={"scheduled_hourly_wage": "scheduled_hourly_wage_base"})

    if base_wages.duplicated(
        subset=[
            "size_name",
            "employment_name",
        ]
    ).any():
        raise ValueError(f"{base_year}年の賃金基準値が重複しています。")

    result = result.merge(
        base_wages,
        on=[
            "size_name",
            "employment_name",
        ],
        how="left",
        validate="many_to_one",
    )

    result["wage_index"] = (
        result["scheduled_hourly_wage"] / result["scheduled_hourly_wage_base"] * 100
    )

    return result


def _validate_input_columns(
    minimum_wage_df: pd.DataFrame,
    wage_df: pd.DataFrame,
) -> None:
    """入力DataFrameに必要な列が存在することを確認する。"""

    required_minimum_wage_columns = {
        "year",
        "minimum_wage",
        "minimum_wage_yoy",
    }

    required_wage_columns = {
        "year",
        "size_name",
        "employment_name",
        "scheduled_hourly_wage",
    }

    missing_minimum_wage = required_minimum_wage_columns - set(minimum_wage_df.columns)

    if missing_minimum_wage:
        raise ValueError(
            f"最低賃金データに必要な列がありません: {sorted(missing_minimum_wage)}"
        )

    missing_wage = required_wage_columns - set(wage_df.columns)

    if missing_wage:
        raise ValueError(f"賃金データに必要な列がありません: {sorted(missing_wage)}")


def _validate_analysis_data(
    df: pd.DataFrame,
    base_year: int,
) -> None:
    """分析用DataFrameの完全性を検証する。"""

    if df.empty:
        raise ValueError("最低賃金分析データが空です。")

    duplicate_columns = [
        "year",
        "size_name",
        "employment_name",
    ]

    if df.duplicated(subset=duplicate_columns).any():
        raise ValueError("年・事業所規模・就業形態の組み合わせが重複しています。")

    required_value_columns = [
        "minimum_wage",
        "scheduled_hourly_wage",
        "simple_kaitz",
        "wage_to_minimum_ratio",
        "minimum_wage_index",
        "wage_index",
    ]

    if df[required_value_columns].isna().any().any():
        raise ValueError("最低賃金分析の主要指標に欠損があります。")

    if (df[required_value_columns] <= 0).any().any():
        raise ValueError("最低賃金分析の主要指標に0以下の値があります。")

    base_rows = df[df["year"] == base_year]

    if base_rows.empty:
        raise ValueError(f"{base_year}年の基準データがありません。")

    minimum_index_error = (base_rows["minimum_wage_index"] - 100).abs().max()

    wage_index_error = (base_rows["wage_index"] - 100).abs().max()

    if minimum_index_error > 1e-10:
        raise ValueError("最低賃金指数の基準年が100になっていません。")

    if wage_index_error > 1e-10:
        raise ValueError("賃金指数の基準年が100になっていません。")

    ratio_error = (df["simple_kaitz"] * df["wage_to_minimum_ratio"] - 1).abs().max()

    if ratio_error > 1e-10:
        raise ValueError(
            "簡易Kaitz指数と賃金/最低賃金比の"
            f"逆数関係が成立しません。最大誤差={ratio_error:.12f}"
        )
