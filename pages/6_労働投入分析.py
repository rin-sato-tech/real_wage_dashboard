import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.labor_input_analysis import (
    create_labor_input_dataframe,
    create_yearly_labor_input_summary,
    summarize_long_term_scheduled_hours_decomposition,
    summarize_long_term_wage_decomposition,
    summarize_long_term_working_hours_decomposition,
)
from real_wage_dashboard.wage_service import load_wage_csv

ANALYSIS_START_YEAR = 2015
ANALYSIS_END_YEAR = 2025

st.set_page_config(
    page_title="労働投入分析",
    page_icon="⏱️",
    layout="wide",
)

@st.cache_data
def load_raw_wage_data() -> pd.DataFrame:
    """毎月勤労統計の元CSVを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)


def create_wage_decomposition_chart(summary: dict[str, float]) -> alt.Chart:
    """2015→2025年の月額賃金変化要因を表示する。"""

    chart_df = pd.DataFrame(
        {
            "要因": [
                "概算時間当たり賃金",
                "総実労働時間",
            ],
            "寄与": [
                summary["hourly_wage_log_contribution"],
                summary["total_hours_log_contribution"],
            ],
        }
    )

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "寄与:Q",
                title="月額賃金の対数変化への寄与",
            ),
            y=alt.Y(
                "要因:N",
                title=None,
                sort=None,
            ),
            color=alt.condition(
                alt.datum.寄与 >= 0,
                alt.value("#4c78a8"),
                alt.value("#f58518"),
            ),
            tooltip=[
                alt.Tooltip(
                    "要因:N",
                    title="要因",
                ),
                alt.Tooltip(
                    "寄与:Q",
                    title="寄与",
                    format="+.2f",
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(pd.DataFrame({"x": [0]}))
        .mark_rule(
            color="#666666",
            strokeDash=[4, 4],
        )
        .encode(
            x="x:Q",
        )
    )

    return (bars + zero_line).properties(
        height=220,
    )


def create_working_hours_decomposition_chart(yearly_df: pd.DataFrame) -> alt.Chart:
    """総実労働時間前年比を所定内・所定外寄与へ分解する。"""

    chart_df = yearly_df.loc[
        yearly_df["year"].between(2015, 2025),
        [
            "year",
            "scheduled_hours_contribution_pct",
            "overtime_hours_contribution_pct",
        ],
    ].copy()

    chart_df = chart_df.melt(
        id_vars="year",
        value_vars=[
            "scheduled_hours_contribution_pct",
            "overtime_hours_contribution_pct",
        ],
        var_name="要因",
        value_name="寄与度",
    )

    chart_df["要因"] = chart_df["要因"].replace(
        {
            "scheduled_hours_contribution_pct": "所定内労働時間",
            "overtime_hours_contribution_pct": "所定外労働時間",
        }
    )

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "year:O",
                title="年",
            ),
            y=alt.Y(
                "寄与度:Q",
                title="総実労働時間前年比への寄与（pt）",
            ),
            color=alt.Color(
                "要因:N",
                title="要因",
                scale=alt.Scale(
                    domain=[
                        "所定内労働時間",
                        "所定外労働時間",
                    ],
                    range=[
                        "#4c78a8",
                        "#f58518",
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "year:O",
                    title="年",
                ),
                alt.Tooltip(
                    "要因:N",
                    title="要因",
                ),
                alt.Tooltip(
                    "寄与度:Q",
                    title="寄与",
                    format="+.2f",
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(
            color="#666666",
            strokeDash=[4, 4],
        )
        .encode(
            y="y:Q",
        )
    )

    return (bars + zero_line).properties(
        height=400,
    )


def create_scheduled_hours_index_chart(
    yearly_df: pd.DataFrame,
    base_year: int = 2015,
) -> alt.Chart:
    """所定内労働時間関連指標を基準年=100で比較する。"""

    chart_df = yearly_df.loc[
        yearly_df["year"].between(base_year, 2025),
        [
            "year",
            "scheduled_hours",
            "working_days",
            "scheduled_hours_per_workday",
        ],
    ].copy()

    base = chart_df.loc[
        chart_df["year"] == base_year
    ]

    if len(base) != 1:
        raise ValueError(
            f"{base_year}年の基準値を一意に取得できません。"
        )

    for column in [
        "scheduled_hours",
        "working_days",
        "scheduled_hours_per_workday",
    ]:
        base_value = base.iloc[0][column]

        chart_df[f"{column}_index"] = (
            chart_df[column]
            / base_value
            * 100
        )

    long_df = chart_df.melt(
        id_vars="year",
        value_vars=[
            "scheduled_hours_index",
            "working_days_index",
            "scheduled_hours_per_workday_index",
        ],
        var_name="指標",
        value_name="指数",
    )

    long_df["指標"] = long_df["指標"].replace(
        {
            "scheduled_hours_index": "所定内労働時間",
            "working_days_index": "出勤日数",
            "scheduled_hours_per_workday_index":
                "1出勤日当たり所定内労働時間",
        }
    )

    y_min = long_df["指数"].min()
    y_max = long_df["指数"].max()

    padding = max(
        (y_max - y_min) * 0.1,
        1,
    )

    lines = (
        alt.Chart(long_df)
        .mark_line(
            strokeWidth=2.5,
            point=True,
        )
        .encode(
            x=alt.X(
                "year:O",
                title="年",
            ),
            y=alt.Y(
                "指数:Q",
                title=f"指数（{base_year}年=100）",
                scale=alt.Scale(
                    domain=[
                        y_min - padding,
                        y_max + padding,
                    ],
                    zero=False,
                ),
            ),
            color=alt.Color(
                "指標:N",
                title="指標",
            ),
            tooltip=[
                alt.Tooltip(
                    "year:O",
                    title="年",
                ),
                alt.Tooltip(
                    "指標:N",
                    title="指標",
                ),
                alt.Tooltip(
                    "指数:Q",
                    title="指数",
                    format=".1f",
                ),
            ],
        )
    )

    baseline = (
        alt.Chart(
            pd.DataFrame(
                {
                    "y": [100],
                }
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
        )
        .encode(
            y="y:Q",
        )
    )

    return (lines + baseline).properties(
        height=400,
    )


st.title("労働投入分析")

st.markdown(
    """
月額賃金の変化を、概算時間当たり賃金と労働時間に分解し、
さらに労働時間の変化を所定内・所定外労働時間、
出勤日数へ段階的に分解します。
"""
)

raw_df = load_raw_wage_data()

labor_df = create_labor_input_dataframe(
    raw_df,
    establishment_size="T",
    employment_type="0",
)

yearly_df = create_yearly_labor_input_summary(labor_df)

wage_summary = summarize_long_term_wage_decomposition(
    labor_df,
    start_year=ANALYSIS_START_YEAR,
    end_year=ANALYSIS_END_YEAR,
)

working_hours_summary = (
    summarize_long_term_working_hours_decomposition(
        labor_df,
        start_year=ANALYSIS_START_YEAR,
        end_year=ANALYSIS_END_YEAR,
    )
)

scheduled_hours_summary = (
    summarize_long_term_scheduled_hours_decomposition(
        labor_df,
        start_year=ANALYSIS_START_YEAR,
        end_year=ANALYSIS_END_YEAR,
    )
)

st.subheader("分析条件")

st.markdown(
    f"""
- 産業：調査産業計
- 事業所規模：5人以上
- 就業形態：就業形態計
- 長期比較：{ANALYSIS_START_YEAR}年平均 → {ANALYSIS_END_YEAR}年平均
"""
)

st.subheader("分析結果")

st.markdown(
    f"""
**{ANALYSIS_START_YEAR}年から{ANALYSIS_END_YEAR}年にかけて、
月額のきまって支給する給与は
{wage_summary["wage_change_pct"]:+.2f}%増加しました。**

一方、年間加重概算時間当たり賃金は
{wage_summary["hourly_wage_change_pct"]:+.2f}%、
総実労働時間は
{wage_summary["total_hours_change_pct"]:+.2f}%となりました。

月額賃金の上昇は概算時間当たり賃金の上昇によって押し上げられた一方、
労働時間の減少がその一部を相殺しています。

さらに労働時間の減少を分解すると、
主な要因は所定内労働時間、とりわけ**出勤日数の減少**でした。
"""
)