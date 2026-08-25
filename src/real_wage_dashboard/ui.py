import pandas as pd

PERIOD_OPTIONS = {
    "直近1年": 12,
    "直近3年": 36,
    "直近5年": 60,
    "直近10年": 120,
    "直近20年": 240,
    "直近30年": 360,
    "全期間": None,
}


def filter_display_period(
    df: pd.DataFrame,
    period: str,
) -> pd.DataFrame:
    """表示期間に応じて時系列データを切り出す。"""

    months = PERIOD_OPTIONS[period]

    if months is None:
        return df.copy()

    return df.tail(months).copy()
