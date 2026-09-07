import pandas as pd

from real_wage_dashboard.config import WAGE_MOVING_AVERAGE_WINDOW
from real_wage_dashboard.time_series import add_monthly_changes, add_moving_average


def add_wage_changes(df: pd.DataFrame) -> pd.DataFrame:
    """名目賃金の前月比と前年同月比を計算する。"""

    return add_monthly_changes(df, column="nominal_wage_amount")


def add_wage_moving_average(df: pd.DataFrame) -> pd.DataFrame:
    """名目賃金の12か月移動平均を追加する。"""

    return add_moving_average(
        df,
        column="nominal_wage_amount",
        output_column="nominal_wage_ma_12",
        window=WAGE_MOVING_AVERAGE_WINDOW,
    )
