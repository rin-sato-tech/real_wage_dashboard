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

    st.caption("毎月勤労統計調査から、選択した条件の名目賃金推移を表示します。")

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
            establishment_size=(WAGE_ESTABLISHMENT_SIZES[establishment_size]),
            employment_type=(WAGE_EMPLOYMENT_TYPES[employment_type]),
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
    # 最新データ
    # -------------------------

    st.subheader("最新データ")

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    metric_col1.metric(
        label=wage_item,
        value=f"{latest['nominal_wage_amount']:,.0f}円",
    )

    metric_col2.metric(
        label="前月比",
        value=(
            f"{latest['mom_pct']:+.1f}%" if pd.notna(latest["mom_pct"]) else "算出不可"
        ),
    )

    metric_col3.metric(
        label="前年同月比",
        value=(
            f"{latest['yoy_pct']:+.1f}%" if pd.notna(latest["yoy_pct"]) else "算出不可"
        ),
    )

    st.caption(f"最新データ：{latest['date'].strftime('%Y年%m月')}")

    # -------------------------
    # 表示期間
    # -------------------------

    st.subheader("時系列推移")

    period_options = [
        "直近1年",
        "直近3年",
        "直近5年",
        "直近10年",
        "直近20年",
        "直近30年",
        "全期間",
    ]

    period = st.selectbox(
        "表示期間",
        period_options,
        index=period_options.index("直近10年"),
    )

    period_months = {
        "直近1年": 12,
        "直近3年": 36,
        "直近5年": 60,
        "直近10年": 120,
        "直近20年": 240,
        "直近30年": 360,
        "全期間": None,
    }[period]

    if period_months is None:
        display_period_df = df.copy()
    else:
        display_period_df = df.tail(period_months).copy()

    # -------------------------
    # 名目賃金
    # -------------------------

    st.markdown(f"#### {wage_item}")

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

    chart_columns = ["月次"]

    if show_moving_average:
        chart_columns.append("12か月移動平均")

    st.line_chart(
        wage_chart_df,
        x="date",
        y=chart_columns,
        x_label="年月",
        y_label=f"{wage_item}（円）",
    )

    # -------------------------
    # 前年同月比
    # -------------------------

    st.markdown("#### 前年同月比")

    yoy_df = display_period_df.dropna(subset=["yoy_pct"])

    st.line_chart(
        yoy_df,
        x="date",
        y="yoy_pct",
        x_label="年月",
        y_label="前年同月比（%）",
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

    display_df = display_df.sort_values(
        "date",
        ascending=False,
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn(
                "年月",
                format="YYYY年MM月",
            ),
            "nominal_wage_amount": (
                st.column_config.NumberColumn(
                    "月次",
                    format="%,.0f円",
                )
            ),
            "nominal_wage_ma_12": (
                st.column_config.NumberColumn(
                    "12か月移動平均",
                    format="%,.0f円",
                )
            ),
            "mom_pct": (
                st.column_config.NumberColumn(
                    "前月比",
                    format="%.1f%%",
                )
            ),
            "yoy_pct": (
                st.column_config.NumberColumn(
                    "前年同月比",
                    format="%.1f%%",
                )
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

    csv_df = csv_df.drop(
        columns="date",
    )

    csv_data = csv_df.to_csv(index=False).encode("utf-8-sig")

    download_col, refresh_col = st.columns([2, 1])

    with download_col:
        st.download_button(
            label="選択条件の全期間データをCSVでダウンロード",
            data=csv_data,
            file_name="nominal_wage.csv",
            mime="text/csv",
        )

    with refresh_col:
        if st.button(
            "データを再読み込み",
            width="stretch",
        ):
            load_raw_wage_data.clear()
            st.rerun()

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
        "前月比・前年同月比・12か月移動平均は、"
        "選択した月次賃金データからアプリ内で算出しています。"
        "12か月移動平均は12か月連続したデータがある場合のみ算出します。"
    )


if __name__ == "__main__":
    main()
