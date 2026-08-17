import pandas as pd


def merge_wage_and_working_hours(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
) -> pd.DataFrame:
    """月次賃金と労働時間を年月でone-to-one結合する。"""

    wage_required = {
        "date",
        "nominal_wage_amount",
    }

    hours_required = {
        "date",
        "working_hours",
    }

    if not wage_required.issubset(wage_df.columns):
        missing = wage_required - set(wage_df.columns)
        raise ValueError(f"賃金データに必要な列がありません: {sorted(missing)}")

    if not hours_required.issubset(working_hours_df.columns):
        missing = hours_required - set(working_hours_df.columns)
        raise ValueError(f"労働時間データに必要な列がありません: {sorted(missing)}")

    wage = wage_df[
        [
            "date",
            "nominal_wage_amount",
        ]
    ].copy()

    hours = working_hours_df[
        [
            "date",
            "working_hours",
        ]
    ].copy()

    result = wage.merge(
        hours,
        on="date",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


def add_approx_hourly_wage(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """月額賃金と総実労働時間から概算時間当たり賃金を算出する。"""

    required_columns = {
        "nominal_wage_amount",
        "working_hours",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    if (result["working_hours"] <= 0).any():
        raise ValueError("労働時間は0より大きい必要があります。")

    result["approx_hourly_wage"] = (
        result["nominal_wage_amount"] / result["working_hours"]
    )

    return result


def create_employment_analysis_dataframe(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
) -> pd.DataFrame:
    """賃金・労働時間・概算時間当たり賃金をまとめたDataFrameを作成する。"""

    result = merge_wage_and_working_hours(
        wage_df,
        working_hours_df,
    )

    result = add_approx_hourly_wage(result)

    return result
