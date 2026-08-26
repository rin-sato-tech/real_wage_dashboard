import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import (
    WAGE_DATA_PATH,
    WAGE_DEFAULT_EMPLOYMENT_TYPE,
    WAGE_DEFAULT_ESTABLISHMENT_SIZE,
    WAGE_DEFAULT_ITEM,
    WAGE_DEFAULT_SHOW_MOVING_AVERAGE,
    WAGE_EMPLOYMENT_TYPES,
    WAGE_ESTABLISHMENT_SIZES,
    WAGE_ITEMS,
    WAGE_METADATA,
)
from real_wage_dashboard.ui import (
    MONTHLY_OPACITY,
    MONTHLY_STROKE_WIDTH,
    MOVING_AVERAGE_OPACITY,
    MOVING_AVERAGE_STROKE_WIDTH,
    NOMINAL_WAGE_COLOR,
    PERIOD_OPTIONS,
    REFERENCE_LINE_COLOR,
    YOY_STROKE_WIDTH,
    create_time_axis,
    filter_display_period,
)
from real_wage_dashboard.wage_analysis import (
    add_wage_changes,
    add_wage_moving_average,
)
from real_wage_dashboard.wage_service import (
    create_wage_dataframe,
    load_wage_csv,
)

st.set_page_config(
    page_title="名目賃金分析",
    page_icon="💴",
    layout="wide",
)


@st.cache_data
def load_raw_wage_data() -> pd.DataFrame:
    """毎月勤労統計の元CSVを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)


def main() -> None:
    st.title("名目賃金分析")

    st.caption(
        "毎月勤労統計から名目賃金の推移を確認します。"
        "物価変動を考慮する前の、実際に支払われた賃金額の変化を見ます。"
    )

    # -------------------------
    # 元データ読み込み
    # -------------------------

    try:
        raw_df = load_raw_wage_data()

    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    except (KeyError, TypeError, ValueError) as exc:
        st.error(f"賃金データの読み込みに失敗しました: {exc}")
        st.stop()

    # -------------------------
    # 分析条件
    # -------------------------

    st.subheader("分析条件")

    condition_col1, condition_col2, condition_col3 = st.columns(3)

    with condition_col1:
        wage_item = st.selectbox(
            "賃金項目",
            list(WAGE_ITEMS.keys()),
            index=list(WAGE_ITEMS.keys()).index(WAGE_DEFAULT_ITEM),
        )

    with condition_col2:
        employment_type = st.selectbox(
            "就業形態",
            list(WAGE_EMPLOYMENT_TYPES.keys()),
            index=list(WAGE_EMPLOYMENT_TYPES.keys()).index(
                WAGE_DEFAULT_EMPLOYMENT_TYPE
            ),
        )

    with condition_col3:
        establishment_size = st.selectbox(
            "事業所規模",
            list(WAGE_ESTABLISHMENT_SIZES.keys()),
            index=list(WAGE_ESTABLISHMENT_SIZES.keys()).index(
                WAGE_DEFAULT_ESTABLISHMENT_SIZE
            ),
        )

    show_moving_average = st.toggle(
        "12か月移動平均を表示",
        value=WAGE_DEFAULT_SHOW_MOVING_AVERAGE,
    )

    # -------------------------
    # 条件抽出・分析
    # -------------------------

    try:
        df = create_wage_dataframe(
            raw_df,
            wage_item=WAGE_ITEMS[wage_item],
            establishment_size=WAGE_ESTABLISHMENT_SIZES[establishment_size],
            employment_type=WAGE_EMPLOYMENT_TYPES[employment_type],
        )

        df = add_wage_changes(df)
        df = add_wage_moving_average(df)

    except (KeyError, TypeError, ValueError) as exc:
        st.error(f"選択した条件の賃金データを作成できませんでした: {exc}")
        st.stop()

    if df.empty:
        st.warning("表示可能な名目賃金データがありません。")
        st.stop()

    latest = df.iloc[-1]

    # -------------------------
    # 主要結果
    # -------------------------

    st.subheader("主要結果")

    metric_col1, metric_col2 = st.columns(2)

    metric_col1.metric(
        label=wage_item,
        value=f"{latest['nominal_wage_amount']:,.0f}円",
    )

    metric_col2.metric(
        label="前年同月比",
        value=(
            f"{latest['yoy_pct']:+.1f}%" if pd.notna(latest["yoy_pct"]) else "算出不可"
        ),
    )

    st.caption(f"最新データ：{latest['date'].strftime('%Y年%m月')}")

    # -------------------------
    # 時系列推移
    # -------------------------

    st.subheader("時系列推移")

    period_options = list(PERIOD_OPTIONS.keys())

    period = st.selectbox(
        "表示期間",
        period_options,
        index=period_options.index("直近10年"),
    )

    display_period_df = filter_display_period(df, period)

    # -------------------------
    # 名目賃金
    # -------------------------

    st.markdown(f"#### {wage_item}")

    st.caption("月次：薄い線　／　12か月移動平均：濃い線")

    wage_min = (
        display_period_df[
            [
                "nominal_wage_amount",
                "nominal_wage_ma_12",
            ]
        ]
        .min()
        .min()
    )

    wage_max = (
        display_period_df[
            [
                "nominal_wage_amount",
                "nominal_wage_ma_12",
            ]
        ]
        .max()
        .max()
    )

    wage_chart_df = display_period_df[
        [
            "date",
            "nominal_wage_amount",
            "nominal_wage_ma_12",
        ]
    ].copy()

    wage_chart_df = wage_chart_df.rename(
        columns={
            "nominal_wage_amount": "月次",
            "nominal_wage_ma_12": "12か月移動平均",
        }
    )

    wage_chart_columns = ["月次"]

    if show_moving_average:
        wage_chart_columns.append("12か月移動平均")

    wage_chart_long_df = wage_chart_df.melt(
        id_vars="date",
        value_vars=wage_chart_columns,
        var_name="系列",
        value_name="賃金額",
    )

    wage_min = wage_chart_long_df["賃金額"].min()
    wage_max = wage_chart_long_df["賃金額"].max()

    wage_padding = max(
        (wage_max - wage_min) * 0.1,
        1000,
    )

    monthly_chart = (
        alt.Chart(display_period_df)
        .mark_line(
            color=NOMINAL_WAGE_COLOR,
            strokeWidth=MONTHLY_STROKE_WIDTH,
            opacity=MONTHLY_OPACITY,
        )
        .encode(
            x=create_time_axis(display_period_df, period),
            y=alt.Y(
                "nominal_wage_amount:Q",
                title=f"{wage_item}（円）",
                scale=alt.Scale(
                    domain=[
                        wage_min - wage_padding,
                        wage_max + wage_padding,
                    ],
                    zero=False,
                ),
                axis=alt.Axis(
                    grid=True,
                    gridOpacity=0.6,
                ),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="年月", format="%Y年%m月"),
                alt.Tooltip("nominal_wage_amount:Q", title="月次", format=".1f"),
            ],
        )
        .properties(height=400)
    )

    moving_average_chart = (
        alt.Chart(display_period_df)
        .mark_line(
            color=NOMINAL_WAGE_COLOR,
            strokeWidth=MOVING_AVERAGE_STROKE_WIDTH,
            opacity=MOVING_AVERAGE_OPACITY,
        )
        .encode(
            x=create_time_axis(display_period_df, period),
            y=alt.Y(
                "nominal_wage_ma_12:Q",
                title=f"{wage_item}（円）",
                scale=alt.Scale(
                    domain=[
                        wage_min - wage_padding,
                        wage_max + wage_padding,
                    ],
                    zero=False,
                ),
                axis=alt.Axis(
                    grid=True,
                    gridOpacity=0.6,
                ),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="年月", format="%Y年%m月"),
                alt.Tooltip(
                    "nominal_wage_ma_12:Q",
                    title="12か月移動平均",
                    format=".1f",
                ),
            ],
        )
        .properties(height=400)
    )

    if show_moving_average:
        chart = monthly_chart + moving_average_chart
    else:
        chart = monthly_chart

    st.altair_chart(
        chart,
        width="stretch",
    )

    # -------------------------
    # 前年同月比
    # -------------------------

    st.markdown("#### 前年同月比")

    yoy_df = display_period_df.dropna(subset=["yoy_pct"])

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(
            color=REFERENCE_LINE_COLOR,
            strokeDash=[5, 5],
            strokeWidth=1,
        )
        .encode(
            y="y:Q",
        )
    )

    yoy_chart = (
        alt.Chart(yoy_df)
        .mark_line(
            color=NOMINAL_WAGE_COLOR,
            strokeWidth=YOY_STROKE_WIDTH,
        )
        .encode(
            x=create_time_axis(display_period_df, period),
            y=alt.Y(
                "yoy_pct:Q",
                title="前年同月比（%）",
                axis=alt.Axis(
                    grid=True,
                    gridOpacity=0.6,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="年月",
                    format="%Y年%m月",
                ),
                alt.Tooltip(
                    "yoy_pct:Q",
                    title="前年同月比",
                    format="+.1f",
                ),
            ],
        )
        .properties(height=400)
    )

    st.altair_chart(
        zero_line + yoy_chart,
        width="stretch",
    )

    # -------------------------
    # データ一覧
    # -------------------------

    st.subheader("取得データ")

    display_df = display_period_df[
        [
            "date",
            "nominal_wage_amount",
            "nominal_wage_ma_12",
            "mom_pct",
            "yoy_pct",
        ]
    ].copy()

    display_df = display_df.sort_values("date", ascending=False)

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn(
                "年月",
                format="YYYY年MM月",
            ),
            "nominal_wage_amount": st.column_config.NumberColumn(
                "月次",
                format="%,.0f円",
            ),
            "nominal_wage_ma_12": st.column_config.NumberColumn(
                "12か月移動平均",
                format="%,.0f円",
            ),
            "mom_pct": st.column_config.NumberColumn(
                "前月比",
                format="%.1f%%",
            ),
            "yoy_pct": st.column_config.NumberColumn(
                "前年同月比",
                format="%.1f%%",
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
        "wage_item",
        wage_item,
    )

    csv_df.insert(
        3,
        "employment_type",
        employment_type,
    )

    csv_df.insert(
        4,
        "establishment_size",
        establishment_size,
    )

    csv_df = csv_df.drop(columns="date")

    csv_data = csv_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="選択条件の全期間データをCSVでダウンロード",
        data=csv_data,
        file_name="nominal_wage.csv",
        mime="text/csv",
    )

    # -------------------------
    # 出典
    # -------------------------

    with st.expander("データ出典・算出方法"):
        st.markdown(
            f"""
            - **出典**：{WAGE_METADATA["source"]}
            - **統計**：{WAGE_METADATA["statistics_name"]}
            - **賃金項目**：{wage_item}
            - **産業**：{WAGE_METADATA["industry"]}
            - **事業所規模**：{establishment_size}
            - **就業形態**：{employment_type}
            - **単位**：{WAGE_METADATA["unit"]}
            - **12か月移動平均**：月次値からアプリ内で算出
            """
        )

    st.info(
        "前月比・前年同月比・12か月移動平均は、選択した月次賃金データからアプリ内で算出しています。"
        "12か月移動平均は12か月連続したデータがある場合のみ算出します。"
    )


if __name__ == "__main__":
    main()
