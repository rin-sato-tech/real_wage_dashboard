import pandas as pd

from real_wage_dashboard.time_series import add_moving_average


def add_cpi_changes(df: pd.DataFrame) -> pd.DataFrame:
    """CPI指数から前月比と前年同月比を計算する。"""

    required_columns = {"date", "index_value"}

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    result["mom_pct"] = result["index_value"].pct_change(fill_method=None).mul(100)

    result["yoy_pct"] = (
        result["index_value"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    return result


def add_cpi_moving_average(df: pd.DataFrame) -> pd.DataFrame:
    """CPI指数の12か月移動平均を追加する。"""

    return add_moving_average(
        df,
        column="index_value",
        output_column="index_value_ma_12",
        window=12,
    )
