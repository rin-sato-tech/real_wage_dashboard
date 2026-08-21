import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.labor_input_analysis import (
    add_scheduled_hours_decomposition,
    add_wage_decomposition,
    add_working_hours_decomposition,
    add_year_over_year_pct,
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

st.subheader("2015→2025年の長期比較")

summary_table = pd.DataFrame(
    [
        {
            "階層": "月額賃金",
            "指標": "きまって支給する給与",
            "2015年": f'{wage_summary["start_wage"]:,.0f}円',
            "2025年": f'{wage_summary["end_wage"]:,.0f}円',
            "変化": f'{wage_summary["wage_change_pct"]:+.2f}%',
        },
        {
            "階層": "月額賃金",
            "指標": "年間加重概算時間当たり賃金",
            "2015年": f'{wage_summary["start_hourly_wage"]:,.2f}円/時',
            "2025年": f'{wage_summary["end_hourly_wage"]:,.2f}円/時',
            "変化": f'{wage_summary["hourly_wage_change_pct"]:+.2f}%',
        },
        {
            "階層": "月額賃金",
            "指標": "総実労働時間",
            "2015年": f'{wage_summary["start_total_hours"]:.2f}時間',
            "2025年": f'{wage_summary["end_total_hours"]:.2f}時間',
            "変化": f'{wage_summary["total_hours_change_pct"]:+.2f}%',
        },
        {
            "階層": "総実労働時間",
            "指標": "所定内労働時間",
            "2015年": (
                f'{working_hours_summary["start_scheduled_hours"]:.2f}時間'
            ),
            "2025年": (
                f'{working_hours_summary["end_scheduled_hours"]:.2f}時間'
            ),
            "変化": (
                f'{scheduled_hours_summary["scheduled_hours_change_pct"]:+.2f}%'
            ),
        },
        {
            "階層": "総実労働時間",
            "指標": "所定外労働時間",
            "2015年": (
                f'{working_hours_summary["start_overtime_hours"]:.2f}時間'
            ),
            "2025年": (
                f'{working_hours_summary["end_overtime_hours"]:.2f}時間'
            ),
            "変化": (
                f'{working_hours_summary["overtime_hours_change_pct"]:+.2f}%'
            ),
        },
        {
            "階層": "所定内労働時間",
            "指標": "出勤日数",
            "2015年": (
                f'{scheduled_hours_summary["start_working_days"]:.3f}日'
            ),
            "2025年": (
                f'{scheduled_hours_summary["end_working_days"]:.3f}日'
            ),
            "変化": (
                f'{scheduled_hours_summary["working_days_change_pct"]:+.2f}%'
            ),
        },
        {
            "階層": "所定内労働時間",
            "指標": "1出勤日当たり所定内労働時間",
            "2015年": (
                f'{scheduled_hours_summary["start_hours_per_workday"]:.3f}時間'
            ),
            "2025年": (
                f'{scheduled_hours_summary["end_hours_per_workday"]:.3f}時間'
            ),
            "変化": (
                f'{scheduled_hours_summary["hours_per_workday_change_pct"]:+.2f}%'
            ),
        },
    ]
)

st.dataframe(
    summary_table,
    hide_index=True,
    width="stretch",
)

st.subheader("月額賃金の変化要因")

st.altair_chart(
    create_wage_decomposition_chart(
        wage_summary
    ),
    width="stretch",
)

st.caption("対数変化による機械的な要因分解。各寄与の合計が月額賃金の対数変化に一致します。")

st.markdown(
    f"""
概算時間当たり賃金の寄与は
**{wage_summary["hourly_wage_log_contribution"]:+.2f}**、
総実労働時間の寄与は
**{wage_summary["total_hours_log_contribution"]:+.2f}**でした。

その結果、月額賃金の対数変化は
**{wage_summary["wage_log_change"]:+.2f}**となっています。

概算時間当たり賃金の上昇が月額賃金を押し上げた一方、
総実労働時間の減少がその一部を相殺しています。
"""
)

st.subheader("総実労働時間の年次分解")

st.altair_chart(
    create_working_hours_decomposition_chart(
        yearly_df
    ),
    width="stretch",
)

st.caption(
    "各年の値は前年からの変化です。"
    "所定内労働時間と所定外労働時間の寄与を合計すると、"
    "総実労働時間の前年比変化に一致します。"
)

st.markdown(
    """
2019年は総実労働時間の減少の大部分を所定内労働時間が占めました。

2020年は所定内労働時間に加えて、所定外労働時間のマイナス寄与も大きくなっています。

2021年には所定内・所定外労働時間がともにプラス寄与へ転じました。

2025年は再び総実労働時間が減少し、その中心は所定内労働時間でした。
"""
)

st.subheader("所定内労働時間の変化要因")

st.altair_chart(
    create_scheduled_hours_index_chart(
        yearly_df,
        base_year=ANALYSIS_START_YEAR,
    ),
    width="stretch",
)

st.caption(
    f"{ANALYSIS_START_YEAR}年を100とした指数。"
    "所定内労働時間、出勤日数、"
    "1出勤日当たり所定内労働時間の推移を比較します。"
)

st.markdown(
    """
所定内労働時間と出勤日数は長期的に低下する一方、
1出勤日当たり所定内労働時間はおおむね横ばいで推移しています。

このため、2015年から2025年にかけた所定内労働時間の減少は、
1日に働く時間の短縮よりも、月間の出勤日数減少による影響が大きいと考えられます。
"""
)

general_df = create_labor_input_dataframe(
    raw_df,
    establishment_size="T",
    employment_type="1",
)

part_df = create_labor_input_dataframe(
    raw_df,
    establishment_size="T",
    employment_type="2",
)


def create_employment_type_comparison_table(
    general_df: pd.DataFrame,
    part_df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> pd.DataFrame:
    """一般労働者とパートの長期変化率を比較する。"""

    indicators = {
        "total_hours": "総実労働時間",
        "scheduled_hours": "所定内労働時間",
        "working_days": "出勤日数",
        "scheduled_hours_per_workday": (
            "1出勤日当たり所定内労働時間"
        ),
    }

    rows = []

    for column, label in indicators.items():
        row = {
            "指標": label,
        }

        for df, employment_label in [
            (general_df, "一般労働者"),
            (part_df, "パートタイム労働者"),
        ]:
            start_value = df.loc[
                df["date"].dt.year == start_year,
                column,
            ].mean()

            end_value = df.loc[
                df["date"].dt.year == end_year,
                column,
            ].mean()

            change_pct = (
                (end_value / start_value) - 1
            ) * 100

            row[employment_label] = change_pct

        rows.append(row)

    return pd.DataFrame(rows)


employment_comparison_table = (
    create_employment_type_comparison_table(
        general_df,
        part_df,
        start_year=ANALYSIS_START_YEAR,
        end_year=ANALYSIS_END_YEAR,
    )
)

with st.expander("雇用形態別の補助分析"):
    st.dataframe(
        employment_comparison_table.style.format(
            {
                "一般労働者": "{:+.2f}%",
                "パートタイム労働者": "{:+.2f}%",
            }
        ),
        hide_index=True,
        width="stretch",
    )

    st.markdown(
        """
一般労働者・パートタイム労働者の双方で、
出勤日数と所定内労働時間が減少しています。

一方、1出勤日当たり所定内労働時間は
両雇用形態ともわずかに増加しています。

したがって、就業形態計で確認された出勤日数減少は、
雇用形態構成比の変化だけでは説明できません。
"""
    )

st.subheader("総合的な考察")

st.markdown(
    """
2015年から2025年にかけて、月額のきまって支給する給与は増加しましたが、
その伸びは概算時間当たり賃金の伸びより小さくなっています。

要因分解では、概算時間当たり賃金の上昇が月額賃金を押し上げた一方、
総実労働時間の減少がその一部を相殺していました。

さらに総実労働時間を分解すると、長期的な減少の中心は所定内労働時間でした。
所定内労働時間の減少をさらに分解すると、
1出勤日当たりの労働時間ではなく、主として出勤日数の減少によって説明されます。

一方、2020年には所定外労働時間の減少も大きく、
長期的な傾向とは異なる短期的な変動が確認されました。
"""
)

with st.expander("分析上の注意点"):
    st.markdown(
        """
- **概算時間当たり賃金**は、
  「きまって支給する給与 ÷ 総実労働時間」で算出した派生指標であり、
  公表された時間当たり賃金そのものではありません。

- **1出勤日当たり所定内労働時間**は、
  「所定内労働時間 ÷ 出勤日数」で算出した指標であり、
  契約上の1日の所定労働時間とは異なります。

- 総実労働時間の分解は加法分解、
  月額賃金と所定内労働時間の分解は対数変化による分解です。
  それぞれの寄与を直接同じ尺度として比較することはできません。

- 本分析は恒等式・定義式に基づく機械的な要因分解であり、
  労働時間や出勤日数が変化した因果的な理由までは特定しません。

- 就業形態計の平均値には、一般労働者・パートタイム労働者などの
  構成比変化の影響が含まれる可能性があります。
"""
    )

st.subheader("データダウンロード")

output_df = add_year_over_year_pct(
    labor_df,
    columns=[
        "nominal_wage_amount",
        "approx_hourly_wage",
        "total_hours",
        "scheduled_hours",
        "overtime_hours",
        "working_days",
        "scheduled_hours_per_workday",
    ],
)

output_df = add_wage_decomposition(
    output_df
)

output_df = add_working_hours_decomposition(
    output_df
)

output_df = add_scheduled_hours_decomposition(
    output_df
)

output_df["industry"] = "調査産業計"
output_df["establishment_size"] = "5人以上"
output_df["employment_type"] = "就業形態計"

output_columns = [
    # 分析条件
    "date",
    "industry",
    "establishment_size",
    "employment_type",

    # 基本指標
    "nominal_wage_amount",
    "total_hours",
    "scheduled_hours",
    "overtime_hours",
    "working_days",

    # 派生指標
    "approx_hourly_wage",
    "scheduled_hours_per_workday",

    # 前年比
    "nominal_wage_amount_yoy_pct",
    "approx_hourly_wage_yoy_pct",
    "total_hours_yoy_pct",
    "scheduled_hours_yoy_pct",
    "overtime_hours_yoy_pct",
    "working_days_yoy_pct",
    "scheduled_hours_per_workday_yoy_pct",

    # 月額賃金の要因分解
    "wage_log_change",
    "hourly_wage_log_contribution",
    "total_hours_log_contribution",

    # 総実労働時間の要因分解
    "total_hours_yoy_diff",
    "scheduled_hours_yoy_diff",
    "overtime_hours_yoy_diff",
    "total_hours_decomposition_yoy_pct",
    "scheduled_hours_contribution_pct",
    "overtime_hours_contribution_pct",

    # 所定内労働時間の要因分解
    "scheduled_hours_log_change",
    "working_days_log_contribution",
    "hours_per_workday_log_contribution",
]

output_df = output_df[output_columns]

csv = output_df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="労働投入分析データをCSVでダウンロード",
    data=csv,
    file_name="labor_input_analysis.csv",
    mime="text/csv",
)
