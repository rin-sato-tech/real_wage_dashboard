import altair as alt
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

CPI_COLOR = "#C9793B"
NOMINAL_WAGE_COLOR = "#3F6FA0"
REAL_WAGE_COLOR = "#4F8A6B"
REFERENCE_LINE_COLOR = "#8A8F98"

MONTHLY_STROKE_WIDTH = 1.2
MONTHLY_OPACITY = 0.35

MOVING_AVERAGE_STROKE_WIDTH = 2.8
MOVING_AVERAGE_OPACITY = 1.0

YOY_STROKE_WIDTH = 2.0


def filter_display_period(
    df: pd.DataFrame,
    period: str,
) -> pd.DataFrame:
    """表示期間に応じて時系列データを切り出す。"""

    months = PERIOD_OPTIONS[period]

    if months is None:
        return df.copy()

    return df.tail(months).copy()


def create_time_axis(df: pd.DataFrame, period: str) -> alt.X:
    """表示期間に応じて年月tickを設定した時間軸を返す。"""

    tick_step = {
        "直近1年": 3,
        "直近3年": 6,
        "直近5年": 6,
        "直近10年": 12,
        "直近20年": 24,
        "直近30年": 36,
        "全期間": 60,
    }[period]

    tick_values = df["date"].iloc[::tick_step].dt.to_pydatetime().tolist()

    return alt.X(
        "date:T",
        title="年月",
        axis=alt.Axis(
            values=tick_values,
            format="%Y年%m月",
            labelAngle=0,
            grid=True,
            gridOpacity=0.4,
        ),
    )
