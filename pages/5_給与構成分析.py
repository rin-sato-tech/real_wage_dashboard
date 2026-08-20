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

    chart_df = (
        df[
            [
                "date",
                "total_cash_earnings_yoy_pct",
                "scheduled_earnings_contribution_pt",
                "overtime_earnings_contribution_pt",
                "special_earnings_contribution_pt",
            ]
        ]
        .dropna()
        .copy()
    )

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
                scale=alt.Scale(
                    domain=[
                        "所定内給与",
                        "所定外給与",
                        "特別給与",
                    ],
                    range=[
                        "#4c78a8",
                        "#f58518",
                        "#54a24b",
                    ],
                ),
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
            color="#222222",
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

    return (bars + line + zero_line).properties(
        height=420,
    )


def create_annual_contribution_chart(annual_df: pd.DataFrame) -> alt.LayerChart:
    """年平均現金給与総額前年比と給与3要素の寄与度を表示する。"""

    chart_df = (
        annual_df[annual_df["year"] >= 2015][
            [
                "year",
                "total_yoy_pct",
                "scheduled_earnings_contribution_pt",
                "overtime_earnings_contribution_pt",
                "special_earnings_contribution_pt",
            ]
        ]
        .dropna()
        .copy()
    )

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
                scale=alt.Scale(
                    domain=[
                        "所定内給与",
                        "所定外給与",
                        "特別給与",
                    ],
                    range=[
                        "#4c78a8",
                        "#f58518",
                        "#54a24b",
                    ],
                ),
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
            color="#222222",
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

    return (bars + line + zero_line).properties(
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

        所定内給与・所定外給与・特別給与に分解し、近年の賃金上昇の中身を確認します。
        """
    )

    st.caption("分析条件：調査産業計・事業所規模5人以上・就業形態計")

    st.subheader("分析結果")

    st.markdown(
        """
        **近年の現金給与総額の上昇は、主として所定内給与の増加によって
        構成されています。**

        - 2015～2025年の現金給与総額は **12.72%増加**
        - 所定内給与の寄与は **+8.46pt** と最大
        - 特別給与は **+4.22pt**
        - 所定外給与は **+0.04pt** とほぼ寄与していない
        - 2020年の低下と2022年以降の上昇では、寄与構造が異なる
        """
    )

    st.subheader("考察")

    st.markdown(
        """
        近年の現金給与総額上昇は、残業等の所定外給与の増加を主因とするものではなく、
        **所定内給与の上昇を中心に、特別給与の増加が加わる構造**となっています。

        一方で、特別給与は月ごとの変動が大きく、
        年や月によって給与総額への影響が大きく変わります。

        また、所定内給与が現金給与総額上昇の最大要因であることと、
        給与構成そのものが所定内給与中心へ変化していることは同じ意味ではありません。
        2015年から2025年にかけては、特別給与の構成比も上昇しています。
        """
    )

    st.warning(
        "この分析で分かるのは、"
        "「どの給与項目の変化が現金給与総額の変化を構成したか」です。"
        "所定内給与がなぜ上昇したのか、春闘や人手不足がどの程度影響したのかといった"
        "因果関係までは、この分析だけでは判断できません。"
    )

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

    # -------------------------
    # 2015年と2025年の長期比較
    # -------------------------

    st.divider()

    st.subheader("10年間の賃金上昇を何が構成したか")

    st.caption(
        "各年の12か月平均を比較し、現金給与総額の変化を所定内給与・所定外給与・特別給与に分解します。"
    )

    st.caption(
        "最新の完全な暦年である2025年を終点とし、"
        "中長期的な変化を見るため10年前の2015年と比較します。"
        "この期間にはコロナ前、2020～2021年、2022年以降の賃金上昇局面が含まれます。"
        "なお、2015年自体を経済的な転換点として選んだものではありません。"
    )

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
    # 前年比寄与度
    # -------------------------

    st.divider()

    st.subheader("月次で見る賃金変動の要因")

    st.caption(
        "棒グラフは各給与項目の寄与度、折れ線は現金給与総額の前年同月比を表します。"
    )

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
    # 年次寄与度
    # -------------------------

    st.divider()

    st.subheader("年次で見る賃金変動の要因")

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

    # -------------------------
    # 分析データ
    # -------------------------

    st.divider()

    st.subheader("分析データ")

    table_df = df[
        [
            "date",
            "total_cash_earnings",
            "scheduled_earnings",
            "overtime_earnings",
            "special_earnings",
            "total_cash_earnings_yoy_pct",
            "scheduled_earnings_yoy_pct",
            "overtime_earnings_yoy_pct",
            "special_earnings_yoy_pct",
            "scheduled_earnings_contribution_pt",
            "overtime_earnings_contribution_pt",
            "special_earnings_contribution_pt",
        ]
    ].copy()

    table_df = table_df.sort_values(
        "date",
        ascending=False,
    )

    st.dataframe(
        table_df,
        width="stretch",
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn(
                "年月",
                format="YYYY年MM月",
            ),
            "total_cash_earnings": st.column_config.NumberColumn(
                "現金給与総額",
                format="%,.0f円",
            ),
            "scheduled_earnings": st.column_config.NumberColumn(
                "所定内給与",
                format="%,.0f円",
            ),
            "overtime_earnings": st.column_config.NumberColumn(
                "所定外給与",
                format="%,.0f円",
            ),
            "special_earnings": st.column_config.NumberColumn(
                "特別給与",
                format="%,.0f円",
            ),
            "total_cash_earnings_yoy_pct": st.column_config.NumberColumn(
                "現金給与総額 前年同月比",
                format="%+.2f%%",
            ),
            "scheduled_earnings_yoy_pct": st.column_config.NumberColumn(
                "所定内給与 前年同月比",
                format="%+.2f%%",
            ),
            "overtime_earnings_yoy_pct": st.column_config.NumberColumn(
                "所定外給与 前年同月比",
                format="%+.2f%%",
            ),
            "special_earnings_yoy_pct": st.column_config.NumberColumn(
                "特別給与 前年同月比",
                format="%+.2f%%",
            ),
            "scheduled_earnings_contribution_pt": st.column_config.NumberColumn(
                "所定内給与 寄与度",
                format="%+.2fpt",
            ),
            "overtime_earnings_contribution_pt": st.column_config.NumberColumn(
                "所定外給与 寄与度",
                format="%+.2fpt",
            ),
            "special_earnings_contribution_pt": st.column_config.NumberColumn(
                "特別給与 寄与度",
                format="%+.2fpt",
            ),
        },
    )

    # -------------------------
    # CSV出力
    # -------------------------

    csv_df = df.copy()

    csv_df.insert(
        0,
        "year",
        csv_df["date"].dt.year,
    )

    csv_df.insert(
        1,
        "month",
        csv_df["date"].dt.month,
    )

    csv_df.insert(
        2,
        "industry",
        "調査産業計",
    )

    csv_df.insert(
        3,
        "establishment_size",
        "5人以上",
    )

    csv_df.insert(
        4,
        "employment_type",
        "就業形態計",
    )

    csv_df = csv_df.drop(
        columns="date",
    )

    csv_data = csv_df.to_csv(
        index=False,
    ).encode("utf-8-sig")

    st.download_button(
        label="全期間の給与構成分析データをCSVでダウンロード",
        data=csv_data,
        file_name="wage_composition_analysis.csv",
        mime="text/csv",
    )

    # -------------------------
    # 出典・算出方法
    # -------------------------

    with st.expander("データ出典・算出方法"):
        st.markdown(
            """
            ### データ出典

            - **出典**：厚生労働省「毎月勤労統計調査」
            - **産業**：調査産業計
            - **事業所規模**：5人以上
            - **就業形態**：就業形態計
            - **頻度**：月次

            ### 使用する給与項目

            - 現金給与総額
            - 所定内給与
            - 所定外給与
            - 特別給与

            ### 給与構成

            現金給与総額は、次の恒等式で分解しています。

            ```
            現金給与総額 = 所定内給与 + 所定外給与 + 特別給与
            ```

            ### 寄与度

            各給与項目の前年差を前年の現金給与総額で割ることで、
            現金給与総額の前年同月比に対する寄与度を算出しています。

            3要素の寄与度の合計は、
            現金給与総額の前年同月比と一致します。

            ### 12か月移動平均

            連続した12暦月が存在する場合のみ算出しています。
            """
        )

    st.info(
        "本ページの寄与度分解は給与項目間の恒等関係を用いた機械的な分解です。"
        "各給与項目が変化した経済的・制度的な原因そのものを示すものではありません。"
    )


if __name__ == "__main__":
    main()
