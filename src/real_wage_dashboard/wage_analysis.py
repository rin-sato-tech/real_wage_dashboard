import pandas as pd

from real_wage_dashboard.config import WAGE_MOVING_AVERAGE_WINDOW


def add_wage_changes(df: pd.DataFrame) -> pd.DataFrame:
    """名目賃金の前月比と前年同月比を計算する。"""

    required_columns = {
        "date",
        "nominal_wage_amount",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    result["mom_pct"] = (
        result["nominal_wage_amount"].pct_change(fill_method=None).mul(100)
    )

    result["yoy_pct"] = (
        result["nominal_wage_amount"].pct_change(periods=12, fill_method=None).mul(100)
    )

    return result


def add_moving_average(
    df: pd.DataFrame,
    column: str,
    output_column: str,
    window: int = 12,
) -> pd.DataFrame:
    """連続した暦月のデータに対して移動平均を計算する。"""

    required_columns = {
        "date",
        column,
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    if window <= 0:
        raise ValueError("windowは1以上で指定してください。")

    result = df.sort_values("date").reset_index(drop=True).copy()

    periods = result["date"].dt.to_period("M")

    month_number = periods.dt.year * 12 + periods.dt.month

    moving_average = (
        result[column]
        .rolling(
            window=window,
            min_periods=window,
        )
        .mean()
    )

    continuous = month_number - month_number.shift(window - 1) == window - 1

    result[output_column] = moving_average.where(continuous)

    return result


def add_wage_moving_average(df: pd.DataFrame) -> pd.DataFrame:
    """名目賃金の12か月移動平均を追加する。"""

    return add_moving_average(
        df,
        column="nominal_wage_amount",
        output_column="nominal_wage_ma_12",
        window=WAGE_MOVING_AVERAGE_WINDOW,
    )
