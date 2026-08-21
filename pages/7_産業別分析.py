import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.industry_analysis import (
    INDUSTRY_NAMES,
    MAIN_INDUSTRIES,
    add_industry_wage_decomposition,
    create_industry_analysis_discussion,
    create_industry_analysis_results,
    create_industry_comparison_dataframe,
    create_multi_industry_yearly_dataframe,
    identify_notable_industries,
    summarize_industry_changes,
)
from real_wage_dashboard.wage_service import load_wage_csv

ANALYSIS_START_YEAR = 2015
ANALYSIS_END_YEAR = 2025


st.set_page_config(
    page_title="産業別賃金分析",
    page_icon="🏭",
    layout="wide",
)


@st.cache_data
def load_raw_wage_data() -> pd.DataFrame:
    """毎月勤労統計の元CSVを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)


raw_df = load_raw_wage_data()

comparison_df = create_industry_comparison_dataframe(
    raw_df,
    industry_codes=MAIN_INDUSTRIES,
    start_year=ANALYSIS_START_YEAR,
    end_year=ANALYSIS_END_YEAR,
)

decomposition_df = add_industry_wage_decomposition(comparison_df)

summary = summarize_industry_changes(decomposition_df)

notable = identify_notable_industries(decomposition_df)


def create_monthly_wage_change_chart(
    decomposition_df: pd.DataFrame,
) -> alt.Chart:
    """2015→2025年の産業別月額賃金変化率を表示する。"""

    chart_df = decomposition_df.loc[
        decomposition_df["industry"] != "TL",
        [
            "industry",
            "monthly_wage_change_pct",
        ],
    ].copy()

    chart_df["産業"] = chart_df["industry"].map(INDUSTRY_NAMES)

    chart_df = chart_df.sort_values(
        "monthly_wage_change_pct",
        ascending=True,
    )

    total_change = decomposition_df.loc[
        decomposition_df["industry"] == "TL",
        "monthly_wage_change_pct",
    ].iloc[0]

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "monthly_wage_change_pct:Q",
                title="月額賃金変化率（%）",
            ),
            y=alt.Y(
                "産業:N",
                title=None,
                sort=None,
                axis=alt.Axis(
                    labelLimit=240,
                    labelPadding=8,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "産業:N",
                    title="産業",
                ),
                alt.Tooltip(
                    "monthly_wage_change_pct:Q",
                    title="変化率",
                    format="+.2f",
                ),
            ],
        )
    )

    total_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "調査産業計": [total_change],
                }
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
            strokeWidth=2,
        )
        .encode(
            x="調査産業計:Q",
        )
    )

    return (bars + total_line).properties(
        height=500,
    )


def create_hourly_wage_change_chart(
    decomposition_df: pd.DataFrame,
) -> alt.Chart:
    """2015→2025年の産業別1時間あたり賃金変化率を表示する。"""

    chart_df = decomposition_df.loc[
        decomposition_df["industry"] != "TL",
        [
            "industry",
            "hourly_wage_change_pct",
        ],
    ].copy()

    chart_df["産業"] = chart_df["industry"].map(INDUSTRY_NAMES)

    chart_df = chart_df.sort_values(
        "hourly_wage_change_pct",
        ascending=True,
    )

    total_change = decomposition_df.loc[
        decomposition_df["industry"] == "TL",
        "hourly_wage_change_pct",
    ].iloc[0]

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "hourly_wage_change_pct:Q",
                title="1時間あたり賃金変化率（%）",
            ),
            y=alt.Y(
                "産業:N",
                title=None,
                sort=None,
                axis=alt.Axis(
                    labelLimit=240,
                    labelPadding=8,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "産業:N",
                    title="産業",
                ),
                alt.Tooltip(
                    "hourly_wage_change_pct:Q",
                    title="変化率",
                    format="+.2f",
                ),
            ],
        )
    )

    total_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "調査産業計": [total_change],
                }
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
            strokeWidth=2,
        )
        .encode(
            x="調査産業計:Q",
        )
    )

    return (bars + total_line).properties(
        height=500,
    )


def create_total_hours_change_chart(
    decomposition_df: pd.DataFrame,
) -> alt.Chart:
    """2015→2025年の産業別総実労働時間変化率を表示する。"""

    chart_df = decomposition_df.loc[
        decomposition_df["industry"] != "TL",
        [
            "industry",
            "total_hours_change_pct",
        ],
    ].copy()

    chart_df["産業"] = chart_df["industry"].map(INDUSTRY_NAMES)

    chart_df = chart_df.sort_values(
        "total_hours_change_pct",
        ascending=True,
    )

    total_change = decomposition_df.loc[
        decomposition_df["industry"] == "TL",
        "total_hours_change_pct",
    ].iloc[0]

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "total_hours_change_pct:Q",
                title="総実労働時間変化率（%）",
            ),
            y=alt.Y(
                "産業:N",
                title=None,
                sort=None,
                axis=alt.Axis(
                    labelLimit=240,
                    labelPadding=8,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "産業:N",
                    title="産業",
                ),
                alt.Tooltip(
                    "total_hours_change_pct:Q",
                    title="変化率",
                    format="+.2f",
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "基準": [0],
                }
            )
        )
        .mark_rule(
            strokeDash=[4, 4],
        )
        .encode(
            x="基準:Q",
        )
    )

    total_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "調査産業計": [total_change],
                }
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
            strokeWidth=2,
        )
        .encode(
            x="調査産業計:Q",
        )
    )

    return (bars + zero_line + total_line).properties(
        height=500,
    )


def create_industry_decomposition_chart(
    decomposition_df: pd.DataFrame,
) -> alt.Chart:
    """産業別の月額賃金変化を時間単価と労働時間の寄与に分解する。"""

    chart_df = decomposition_df.loc[
        decomposition_df["industry"] != "TL",
        [
            "industry",
            "wage_log_change",
            "hourly_wage_log_contribution",
            "total_hours_log_contribution",
        ],
    ].copy()

    chart_df["産業"] = chart_df["industry"].map(INDUSTRY_NAMES)

    chart_df = chart_df.sort_values(
        "wage_log_change",
        ascending=True,
    )

    long_df = chart_df.melt(
        id_vars=[
            "industry",
            "産業",
            "wage_log_change",
        ],
        value_vars=[
            "hourly_wage_log_contribution",
            "total_hours_log_contribution",
        ],
        var_name="要因",
        value_name="寄与",
    )

    long_df["要因"] = long_df["要因"].replace(
        {
            "hourly_wage_log_contribution": ("1時間あたり賃金（概算）"),
            "total_hours_log_contribution": ("総実労働時間"),
        }
    )

    bars = (
        alt.Chart(long_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "寄与:Q",
                title="月額賃金の対数変化への寄与（pt）",
            ),
            y=alt.Y(
                "産業:N",
                title=None,
                sort=None,
                axis=alt.Axis(
                    labelLimit=240,
                    labelPadding=8,
                ),
            ),
            color=alt.Color(
                "要因:N",
                title="要因",
                scale=alt.Scale(
                    domain=[
                        "1時間あたり賃金（概算）",
                        "総実労働時間",
                    ],
                    range=[
                        "#4c78a8",
                        "#f58518",
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "産業:N",
                    title="産業",
                ),
                alt.Tooltip(
                    "要因:N",
                    title="要因",
                ),
                alt.Tooltip(
                    "寄与:Q",
                    title="寄与",
                    format="+.2f",
                ),
                alt.Tooltip(
                    "wage_log_change:Q",
                    title="月額賃金の対数変化",
                    format="+.2f",
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "基準": [0],
                }
            )
        )
        .mark_rule(
            strokeDash=[4, 4],
        )
        .encode(
            x="基準:Q",
        )
    )

    return (bars + zero_line).properties(
        height=500,
    )


def create_hourly_hours_scatter_chart(
    decomposition_df: pd.DataFrame,
) -> alt.Chart:
    """時間単価寄与と労働時間寄与の関係を産業別に表示する。"""

    chart_df = decomposition_df.loc[
        decomposition_df["industry"] != "TL",
        [
            "industry",
            "hourly_wage_log_contribution",
            "total_hours_log_contribution",
            "wage_log_change",
        ],
    ].copy()

    chart_df["産業"] = chart_df["industry"].map(INDUSTRY_NAMES)

    points = (
        alt.Chart(chart_df)
        .mark_circle(
            size=120,
        )
        .encode(
            x=alt.X(
                "hourly_wage_log_contribution:Q",
                title="1時間あたり賃金の寄与（pt）",
            ),
            y=alt.Y(
                "total_hours_log_contribution:Q",
                title="総実労働時間の寄与（pt）",
            ),
            tooltip=[
                alt.Tooltip(
                    "産業:N",
                    title="産業",
                ),
                alt.Tooltip(
                    "hourly_wage_log_contribution:Q",
                    title="時間単価寄与",
                    format="+.2f",
                ),
                alt.Tooltip(
                    "total_hours_log_contribution:Q",
                    title="労働時間寄与",
                    format="+.2f",
                ),
                alt.Tooltip(
                    "wage_log_change:Q",
                    title="月額賃金の対数変化",
                    format="+.2f",
                ),
            ],
        )
    )

    labels = (
        alt.Chart(chart_df)
        .mark_text(
            dx=8,
            dy=-6,
            fontSize=11,
        )
        .encode(
            x="hourly_wage_log_contribution:Q",
            y="total_hours_log_contribution:Q",
            text="industry:N",
        )
    )

    zero_x = (
        alt.Chart(
            pd.DataFrame(
                {
                    "x": [0],
                }
            )
        )
        .mark_rule(
            strokeDash=[4, 4],
        )
        .encode(
            x="x:Q",
        )
    )

    zero_y = (
        alt.Chart(
            pd.DataFrame(
                {
                    "y": [0],
                }
            )
        )
        .mark_rule(
            strokeDash=[4, 4],
        )
        .encode(
            y="y:Q",
        )
    )

    return (points + labels + zero_x + zero_y).properties(
        height=500,
    )


def create_industry_wage_index_chart(
    yearly_df: pd.DataFrame,
    base_year: int = 2015,
) -> alt.Chart:
    """代表産業の月額賃金を基準年=100で比較する。"""

    chart_df = yearly_df.loc[
        yearly_df["year"].between(base_year, ANALYSIS_END_YEAR),
        [
            "industry",
            "year",
            "monthly_wage",
        ],
    ].copy()

    base_df = chart_df.loc[
        chart_df["year"] == base_year,
        [
            "industry",
            "monthly_wage",
        ],
    ].rename(
        columns={
            "monthly_wage": "base_monthly_wage",
        }
    )

    chart_df = chart_df.merge(
        base_df,
        on="industry",
        how="left",
        validate="many_to_one",
    )

    chart_df["index"] = chart_df["monthly_wage"] / chart_df["base_monthly_wage"] * 100

    chart_df["産業"] = chart_df["industry"].map(INDUSTRY_NAMES)

    lines = (
        alt.Chart(chart_df)
        .mark_line(
            point=True,
            strokeWidth=2,
        )
        .encode(
            x=alt.X(
                "year:O",
                title="年",
            ),
            y=alt.Y(
                "index:Q",
                title=f"月額賃金指数（{base_year}年=100）",
                scale=alt.Scale(
                    zero=False,
                ),
            ),
            color=alt.Color(
                "産業:N",
                title="産業",
            ),
            tooltip=[
                alt.Tooltip(
                    "year:O",
                    title="年",
                ),
                alt.Tooltip(
                    "産業:N",
                    title="産業",
                ),
                alt.Tooltip(
                    "index:Q",
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
        height=450,
    )


def create_industry_hours_index_chart(
    yearly_df: pd.DataFrame,
    base_year: int = 2015,
) -> alt.Chart:
    """代表産業の総実労働時間を基準年=100で比較する。"""

    chart_df = yearly_df.loc[
        yearly_df["year"].between(base_year, ANALYSIS_END_YEAR),
        [
            "industry",
            "year",
            "total_hours",
        ],
    ].copy()

    base_df = chart_df.loc[
        chart_df["year"] == base_year,
        [
            "industry",
            "total_hours",
        ],
    ].rename(
        columns={
            "total_hours": "base_total_hours",
        }
    )

    chart_df = chart_df.merge(
        base_df,
        on="industry",
        how="left",
        validate="many_to_one",
    )

    chart_df["index"] = chart_df["total_hours"] / chart_df["base_total_hours"] * 100

    chart_df["産業"] = chart_df["industry"].map(INDUSTRY_NAMES)

    lines = (
        alt.Chart(chart_df)
        .mark_line(
            point=True,
            strokeWidth=2,
        )
        .encode(
            x=alt.X(
                "year:O",
                title="年",
            ),
            y=alt.Y(
                "index:Q",
                title=f"総実労働時間指数（{base_year}年=100）",
                scale=alt.Scale(
                    zero=False,
                ),
            ),
            color=alt.Color(
                "産業:N",
                title="産業",
            ),
            tooltip=[
                alt.Tooltip(
                    "year:O",
                    title="年",
                ),
                alt.Tooltip(
                    "産業:N",
                    title="産業",
                ),
                alt.Tooltip(
                    "index:Q",
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
        height=450,
    )


st.title("産業別賃金分析")

st.markdown(
    """
    産業ごとの月額賃金の変化を比較し、
    **1時間あたり賃金（概算）と労働時間のどちらが変化を生んだのか**
    を確認します。
    """
)

st.caption(
    "「1時間あたり賃金（概算）」は、"
    "月額のきまって支給する給与を総実労働時間で割って算出した指標です。"
)

st.subheader("問い")

st.markdown(
    f"""
    **{ANALYSIS_START_YEAR}年から{ANALYSIS_END_YEAR}年の賃金上昇は、
    幅広い産業で生じたのか。**

    また、産業ごとの月額賃金の変化は、

    - 1時間あたり賃金（概算）の変化
    - 総実労働時間の変化

    のどちらによって生じたのかを確認します。
    """
)

st.divider()

st.subheader("分析条件")

st.markdown(
    f"""
    - データ：毎月勤労統計調査
    - 産業：産業大分類16産業
    - 比較基準：調査産業計
    - 事業所規模：5人以上
    - 就業形態：就業形態計
    - 比較期間：{ANALYSIS_START_YEAR}年平均 → {ANALYSIS_END_YEAR}年平均
    - 月額賃金：きまって支給する給与
    """
)

results = create_industry_analysis_results(
    summary,
    notable,
)

discussion = create_industry_analysis_discussion(
    notable,
)

st.subheader("分析結果")

for text in results:
    st.markdown(f"- {text}")

st.subheader("考察")

for text in discussion:
    st.markdown(f"- {text}")

st.caption(
    "産業平均には、一般労働者・パートタイム労働者の構成、"
    "年齢、職種、事業所規模などの違いが含まれます。"
    "本分析だけから賃金変化の因果関係を特定することはできません。"
)

st.divider()

st.subheader(f"{ANALYSIS_START_YEAR}→{ANALYSIS_END_YEAR}年の月額賃金変化")

st.markdown(
    """
    産業ごとの「きまって支給する給与」の年平均を比較します。
    破線は調査産業計の変化率です。
    """
)

st.altair_chart(
    create_monthly_wage_change_chart(decomposition_df),
    width="stretch",
)

st.caption(f"破線：調査産業計 {summary['total_wage_change']:+.2f}%")

st.divider()

st.subheader(f"{ANALYSIS_START_YEAR}→{ANALYSIS_END_YEAR}年の1時間あたり賃金変化")

st.markdown(
    """
    月額の「きまって支給する給与」を総実労働時間で割った
    1時間あたり賃金（概算）の変化率を比較します。
    """
)

st.altair_chart(
    create_hourly_wage_change_chart(decomposition_df),
    width="stretch",
)

total_hourly_change = decomposition_df.loc[
    decomposition_df["industry"] == "TL",
    "hourly_wage_change_pct",
].iloc[0]

st.caption(f"破線：調査産業計 {total_hourly_change:+.2f}%")

st.divider()

st.subheader(f"{ANALYSIS_START_YEAR}→{ANALYSIS_END_YEAR}年の総実労働時間変化")

st.markdown(
    """
    月額賃金の変化を解釈するため、
    産業ごとの1人あたり月間総実労働時間の変化率を比較します。
    """
)

st.altair_chart(
    create_total_hours_change_chart(decomposition_df),
    width="stretch",
)

total_hours_change = decomposition_df.loc[
    decomposition_df["industry"] == "TL",
    "total_hours_change_pct",
].iloc[0]

st.caption(f"破線：調査産業計 {total_hours_change:+.2f}%")

st.divider()

st.subheader(f"{ANALYSIS_START_YEAR}→{ANALYSIS_END_YEAR}年の月額賃金の要因分解")

st.markdown(
    """
    月額賃金の変化を、
    **1時間あたり賃金（概算）の変化**と
    **総実労働時間の変化**に対数分解します。

    プラス方向は月額賃金を押し上げる寄与、
    マイナス方向は押し下げる寄与を示します。
    """
)

st.altair_chart(
    create_industry_decomposition_chart(decomposition_df),
    width="stretch",
)

st.caption("対数分解のため、各要因の寄与の合計は月額賃金の対数変化と一致します。")

st.divider()

st.subheader("1時間あたり賃金と労働時間の寄与の関係")

st.markdown(
    """
    各産業について、月額賃金変化への
    1時間あたり賃金の寄与と総実労働時間の寄与を比較します。

    右にあるほど時間単価の押し上げが大きく、
    下にあるほど労働時間による押し下げが大きいことを示します。
    """
)

st.altair_chart(
    create_hourly_hours_scatter_chart(decomposition_df),
    width="stretch",
)

st.caption(
    "16産業では、時間単価の伸びが大きい産業ほど"
    "労働時間の減少も大きい傾向が見られました。"
    "ただし、これは探索的な相関であり因果関係を示すものではありません。"
)

TREND_INDUSTRIES = [
    "TL",
    "C",
    "K",
    "M",
    "N",
    "O",
]

trend_df = create_multi_industry_yearly_dataframe(
    raw_df,
    industry_codes=TREND_INDUSTRIES,
)

st.divider()

st.subheader("代表産業の年次推移")

st.markdown(
    """
    2015年を100として、特徴的な産業の月額賃金の推移を比較します。
    2015→2025年の変化が、どの時期に生じたのかを確認するための補足です。
    """
)

st.altair_chart(
    create_industry_wage_index_chart(trend_df),
    width="stretch",
)

st.altair_chart(
    create_industry_hours_index_chart(trend_df),
    width="stretch",
)

st.caption(
    "2015年=100。M・Nでは2020年に大きく低下した一方、"
    "2015～2019年にもすでに労働時間の減少が見られます。"
    "2020年以降の動きも産業によって異なります。"
)
