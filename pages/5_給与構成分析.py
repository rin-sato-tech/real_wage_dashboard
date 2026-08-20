import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.wage_composition_analysis import (
    add_annual_wage_contributions,
    add_wage_composition_changes,
    add_wage_composition_contributions,
    add_wage_composition_moving_averages,
    add_wage_composition_shares,
    create_annual_wage_composition_summary,
    create_complete_annual_wage_composition_summary,
    create_long_term_wage_composition_comparison,
    create_wage_composition_dataframe,
)
from real_wage_dashboard.wage_service import load_wage_csv


st.set_page_config(
    page_title="給与構成分析",
    page_icon="🧩",
    layout="wide",
)


@st.cache_data
def load_raw_wage_data() -> pd.DataFrame:
    """毎月勤労統計の元CSVを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)


def create_analysis_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """給与構成分析に必要な指標をまとめて作成する。"""

    df = create_wage_composition_dataframe(
        raw_df,
        establishment_size="T",
        employment_type="0",
    )

    df = add_wage_composition_changes(df)
    df = add_wage_composition_contributions(df)
    df = add_wage_composition_shares(df)
    df = add_wage_composition_moving_averages(df)

    return df


def create_contribution_chart(df: pd.DataFrame) -> alt.LayerChart:
    """現金給与総額前年比と給与3要素の寄与度を表示する。"""

    chart_df = df[
        [
            "date",
            "total_cash_earnings_yoy_pct",
            "scheduled_earnings_contribution_pt",
            "overtime_earnings_contribution_pt",
            "special_earnings_contribution_pt",
        ]
    ].dropna().copy()

    contribution_df = chart_df.melt(
        id_vars="date",
        value_vars=[
            "scheduled_earnings_contribution_pt",
            "overtime_earnings_contribution_pt",
            "special_earnings_contribution_pt",
        ],
        var_name="component",
        value_name="contribution_pt",
    )

    contribution_df["component"] = contribution_df["component"].replace(
        {
            "scheduled_earnings_contribution_pt": "所定内給与",
            "overtime_earnings_contribution_pt": "所定外給与",
            "special_earnings_contribution_pt": "特別給与",
        }
    )

    bars = (
        alt.Chart(contribution_df)
        .mark_bar(opacity=0.8)
        .encode(
            x=alt.X(
                "date:T",
                title="年月",
            ),
            y=alt.Y(
                "contribution_pt:Q",
                title="寄与度（pt）",
            ),
            color=alt.Color(
                "component:N",
                title="給与項目",
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="年月",
                    format="%Y年%m月",
                ),
                alt.Tooltip(
                    "component:N",
                    title="給与項目",
                ),
                alt.Tooltip(
                    "contribution_pt:Q",
                    title="寄与度",
                    format="+.2f",
                ),
            ],
        )
    )

    line = (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "date:T",
                title="年月",
            ),
            y=alt.Y(
                "total_cash_earnings_yoy_pct:Q",
                title="前年同月比（%）",
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="年月",
                    format="%Y年%m月",
                ),
                alt.Tooltip(
                    "total_cash_earnings_yoy_pct:Q",
                    title="現金給与総額前年比",
                    format="+.2f",
                ),
            ],
        )
    )

    zero_line = (
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

    return (
        bars
        + line
        + zero_line
    ).properties(
        height=420,
    )


def create_annual_contribution_chart(annual_df: pd.DataFrame) -> alt.LayerChart:
    """年平均現金給与総額前年比と給与3要素の寄与度を表示する。"""

    chart_df = annual_df[
        annual_df["year"] >= 2015
    ][
        [
            "year",
            "total_yoy_pct",
            "scheduled_earnings_contribution_pt",
            "overtime_earnings_contribution_pt",
            "special_earnings_contribution_pt",
        ]
    ].dropna().copy()

    contribution_df = chart_df.melt(
        id_vars="year",
        value_vars=[
            "scheduled_earnings_contribution_pt",
            "overtime_earnings_contribution_pt",
            "special_earnings_contribution_pt",
        ],
        var_name="component",
        value_name="contribution_pt",
    )

    contribution_df["component"] = contribution_df["component"].replace(
        {
            "scheduled_earnings_contribution_pt": "所定内給与",
            "overtime_earnings_contribution_pt": "所定外給与",
            "special_earnings_contribution_pt": "特別給与",
        }
    )

    bars = (
        alt.Chart(contribution_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "year:O",
                title="年",
            ),
            y=alt.Y(
                "contribution_pt:Q",
                title="寄与度（pt）",
            ),
            color=alt.Color(
                "component:N",
                title="給与項目",
            ),
            tooltip=[
                alt.Tooltip(
                    "year:O",
                    title="年",
                ),
                alt.Tooltip(
                    "component:N",
                    title="給与項目",
                ),
                alt.Tooltip(
                    "contribution_pt:Q",
                    title="寄与度",
                    format="+.2f",
                ),
            ],
        )
    )

    line = (
        alt.Chart(chart_df)
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
                "total_yoy_pct:Q",
                title="前年比（%）",
            ),
            tooltip=[
                alt.Tooltip(
                    "year:O",
                    title="年",
                ),
                alt.Tooltip(
                    "total_yoy_pct:Q",
                    title="現金給与総額前年比",
                    format="+.2f",
                ),
            ],
        )
    )

    zero_line = (
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

    return (
        bars
        + line
        + zero_line
    ).properties(
        height=420,
    )


def main() -> None:
    st.title("給与構成分析")

    st.caption(
        "現金給与総額の変動を、所定内給与・所定外給与・特別給与に分解し、"
        "賃金上昇の中身を確認します。"
    )

    # -------------------------
    # 問い
    # -------------------------

    st.subheader("問い")

    st.markdown(
        """
        **現金給与総額の変動は、何によって生じているのか。**

        - 所定内給与の上昇によるものか
        - 残業等の所定外給与によるものか
        - 賞与等の特別給与によるものか

        を寄与度分解によって確認します。
        """
    )

    st.caption("分析条件：調査産業計・事業所規模5人以上・就業形態計")

    # -------------------------
    # データ生成
    # -------------------------

    try:
        raw_df = load_raw_wage_data()

        df = create_analysis_dataframe(raw_df)

        annual_df = create_complete_annual_wage_composition_summary(df)
        annual_df = add_annual_wage_contributions(annual_df)

        long_term_annual_df = create_annual_wage_composition_summary(
            df,
            years=[2015, 2025],
        )

        long_term_df = create_long_term_wage_composition_comparison(
            long_term_annual_df,
            start_year=2015,
            end_year=2025,
        )

    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    except (KeyError, TypeError, ValueError) as exc:
        st.error(f"給与構成分析データの生成に失敗しました: {exc}")
        st.stop()

    if df.empty:
        st.warning("表示可能な給与構成データがありません。")
        st.stop()

    latest = df.iloc[-1]

    # -------------------------
    # 最新結果
    # -------------------------

    st.subheader("最新結果")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    metric_col1.metric(
        label="現金給与総額",
        value=f"{latest['total_cash_earnings']:,.0f}円",
        delta=(
            f"{latest['total_cash_earnings_yoy_pct']:+.2f}%"
            if pd.notna(latest["total_cash_earnings_yoy_pct"])
            else None
        ),
    )

    metric_col2.metric(
        label="所定内給与の寄与",
        value=(
            f"{latest['scheduled_earnings_contribution_pt']:+.2f}pt"
            if pd.notna(
                latest["scheduled_earnings_contribution_pt"]
            )
            else "算出不可"
        ),
    )

    metric_col3.metric(
        label="所定外給与の寄与",
        value=(
            f"{latest['overtime_earnings_contribution_pt']:+.2f}pt"
            if pd.notna(
                latest["overtime_earnings_contribution_pt"]
            )
            else "算出不可"
        ),
    )

    metric_col4.metric(
        label="特別給与の寄与",
        value=(
            f"{latest['special_earnings_contribution_pt']:+.2f}pt"
            if pd.notna(
                latest["special_earnings_contribution_pt"]
            )
            else "算出不可"
        ),
    )

    st.caption(
        f"最新データ：{latest['date'].strftime('%Y年%m月')}"
    )

    if pd.notna(latest["scheduled_earnings_contribution_pt"]):
        contribution_share = (
            latest["scheduled_earnings_contribution_pt"]
            / latest["total_cash_earnings_yoy_pct"]
            * 100
        )

        st.info(
            f"{latest['date'].strftime('%Y年%m月')}の現金給与総額は"
            f"前年同月比{latest['total_cash_earnings_yoy_pct']:+.2f}%です。"
            f"このうち所定内給与の寄与は"
            f"{latest['scheduled_earnings_contribution_pt']:+.2f}ptで、"
            f"総額の変化の約{contribution_share:.0f}%を占めました。"
        )

    # -------------------------
    # この後グラフを追加
    # -------------------------

    st.divider()

    # -------------------------
    # 給与構成の長期推移
    # -------------------------

    st.divider()

    st.subheader("給与構成の推移")

    st.caption("月ごとの季節変動をならして基調を確認するため、12か月移動平均を表示しています。")

    period_options = {
        "直近5年": 60,
        "直近10年": 120,
        "直近20年": 240,
        "直近30年": 360,
        "全期間": None,
    }

    period = st.selectbox(
        "表示期間",
        options=list(period_options.keys()),
        index=list(period_options.keys()).index("直近10年"),
        key="composition_period",
    )

    period_months = period_options[period]

    if period_months is None:
        display_df = df.copy()
    else:
        display_df = df.tail(period_months).copy()

    # -------------------------
    # 現金給与総額・所定内給与
    # -------------------------

    st.markdown("#### 現金給与総額と所定内給与")

    main_chart_df = display_df[
        [
            "date",
            "total_cash_earnings_ma_12",
            "scheduled_earnings_ma_12",
        ]
    ].copy()

    main_chart_df = main_chart_df.rename(
        columns={
            "total_cash_earnings_ma_12": "現金給与総額",
            "scheduled_earnings_ma_12": "所定内給与",
        }
    )

    st.line_chart(
        main_chart_df,
        x="date",
        y=[
            "現金給与総額",
            "所定内給与",
        ],
        x_label="年月",
        y_label="12か月移動平均（円）",
    )

    st.caption("現金給与総額と、その最大の構成要素である所定内給与の長期的な動きを比較しています。")

    # -------------------------
    # 所定外給与・特別給与
    # -------------------------

    st.markdown("#### 所定外給与と特別給与")

    component_chart_df = display_df[
        [
            "date",
            "overtime_earnings_ma_12",
            "special_earnings_ma_12",
        ]
    ].copy()

    component_chart_df = component_chart_df.rename(
        columns={
            "overtime_earnings_ma_12": "所定外給与",
            "special_earnings_ma_12": "特別給与",
        }
    )

    st.line_chart(
        component_chart_df,
        x="date",
        y=[
            "所定外給与",
            "特別給与",
        ],
        x_label="年月",
        y_label="12か月移動平均（円）",
    )

    st.caption(
        "所定外給与は残業等、特別給与は賞与等を含みます。"
        "所定内給与とは金額規模が大きく異なるため、別グラフに分けて表示しています。"
    )

    # -------------------------
    # 前年比寄与度
    # -------------------------

    st.divider()

    st.subheader("現金給与総額前年比への寄与度")

    st.caption(
        "棒グラフは各給与項目の寄与度、"
        "折れ線は現金給与総額の前年同月比を表します。"
    )

    contribution_chart = create_contribution_chart(display_df)

    st.altair_chart(
        contribution_chart,
        width="stretch",
    )

    st.info(
        "各給与項目の寄与度の合計は、現金給与総額の前年同月比と一致します。"
        "各項目自身の前年比とは異なる指標です。"
    )

    # -------------------------
    # 2015年と2025年の長期比較
    # -------------------------

    st.divider()

    st.subheader("2015年から2025年の長期変化")

    st.caption("各年の12か月平均を比較し、現金給与総額の変化を所定内給与・所定外給与・特別給与に分解します。")

    total_row = long_term_df.loc[
        long_term_df["component"] == "total_cash_earnings"
    ].iloc[0]

    scheduled_row = long_term_df.loc[
        long_term_df["component"] == "scheduled_earnings"
    ].iloc[0]

    overtime_row = long_term_df.loc[
        long_term_df["component"] == "overtime_earnings"
    ].iloc[0]

    special_row = long_term_df.loc[
        long_term_df["component"] == "special_earnings"
    ].iloc[0]

    long_col1, long_col2, long_col3, long_col4 = st.columns(4)

    long_col1.metric(
        label="現金給与総額",
        value=f"{total_row['end_value']:,.0f}円",
        delta=f"{total_row['pct_change']:+.2f}%",
    )

    long_col2.metric(
        label="所定内給与の寄与",
        value=f"{scheduled_row['contribution_pt']:+.2f}pt",
    )

    long_col3.metric(
        label="所定外給与の寄与",
        value=f"{overtime_row['contribution_pt']:+.2f}pt",
    )

    long_col4.metric(
        label="特別給与の寄与",
        value=f"{special_row['contribution_pt']:+.2f}pt",
    )

    long_term_display_df = long_term_df.copy()

    long_term_display_df["component"] = long_term_display_df["component"].replace(
        {
            "total_cash_earnings": "現金給与総額",
            "scheduled_earnings": "所定内給与",
            "overtime_earnings": "所定外給与",
            "special_earnings": "特別給与",
        }
    )

    long_term_display_df = long_term_display_df.rename(
        columns={
            "component": "項目",
            "start_value": "2015年",
            "end_value": "2025年",
            "difference": "差額",
            "pct_change": "変化率",
            "contribution_pt": "寄与度",
        }
    )

    st.dataframe(
        long_term_display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "2015年": st.column_config.NumberColumn(
                "2015年",
                format="%,.0f円",
            ),
            "2025年": st.column_config.NumberColumn(
                "2025年",
                format="%,.0f円",
            ),
            "差額": st.column_config.NumberColumn(
                "差額",
                format="%+,.0f円",
            ),
            "変化率": st.column_config.NumberColumn(
                "変化率",
                format="%+.2f%%",
            ),
            "寄与度": st.column_config.NumberColumn(
                "寄与度",
                format="%+.2fpt",
            ),
        },
    )

    st.info(
        "2015年から2025年にかけて現金給与総額は12.72%増加しました。"
        "このうち所定内給与の寄与が+8.46ptと最大で、"
        "特別給与が+4.22pt、所定外給与は+0.04ptでした。"
        "長期的な賃金上昇は主として所定内給与の増加によって構成されています。"
    )

    # -------------------------
    # 年次寄与度
    # -------------------------

    st.divider()

    st.subheader("年次で見る給与上昇の構成")

    st.caption(
        "各年の年平均現金給与総額の前年比を、"
        "所定内給与・所定外給与・特別給与へ分解しています。"
    )

    annual_chart = create_annual_contribution_chart(annual_df)

    st.altair_chart(
        annual_chart,
        width="stretch",
    )

    st.markdown(
        """
        **確認できる特徴**

        - 2020年は所定外給与と特別給与がマイナス寄与となった
        - 2022年以降は所定内給与が主要なプラス寄与となっている
        - 2024年は所定内給与と特別給与の双方が大きく寄与した
        - 所定外給与の寄与は、近年も相対的に小さい
        """
    )

    st.info(
        "年次で見ると、給与総額の変動要因は時期によって異なります。"
        "2020年の低下は主として所定外給与・特別給与の減少、"
        "2022年以降の上昇は主として所定内給与の増加によって構成されています。"
    )

if __name__ == "__main__":
    main()
