import pandas as pd


def add_monthly_changes(
    df: pd.DataFrame,
    column: str,
    mom_column: str = "mom_pct",
    yoy_column: str = "yoy_pct",
) -> pd.DataFrame:
    """月次系列の前月比・前年同月比（%）を追加する。

    日付で並べ替えた前行・12行前との比較を行い、欠損は補完しない。
    月の連続性は呼び出し側の入力条件とし、暦月への再配置は行わない。
    """
    required_columns = {"date", column}

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()
    result[mom_column] = result[column].pct_change(fill_method=None).mul(100)
    result[yoy_column] = (
        result[column].pct_change(periods=12, fill_method=None).mul(100)
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
