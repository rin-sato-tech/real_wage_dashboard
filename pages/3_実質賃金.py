import pandas as pd
import streamlit as st

from real_wage_dashboard.config import (
    CPI_BASE_FILTERS,
    CPI_DEFAULT_SERIES,
    CPI_METADATA,
    CPI_SERIES,
    CPI_STATS_DATA_ID,
    WAGE_BASE_YEAR,
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
from real_wage_dashboard.cpi_service import create_cpi_dataframe
from real_wage_dashboard.estat_client import (
    EStatAPIError,
    get_stats_data,
)
from real_wage_dashboard.real_wage_analysis import (
    add_real_wage_changes,
    create_real_wage_dataframe,
)
from real_wage_dashboard.wage_analysis import add_wage_moving_average
from real_wage_dashboard.wage_service import (
    create_wage_dataframe,
    load_wage_csv,
)

st.set_page_config(
    page_title="実質賃金分析",
    page_icon="📈",
    layout="wide",
)


@st.cache_data
def load_raw_wage_data() -> pd.DataFrame:
    """毎月勤労統計の元CSVを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)


@st.cache_data(ttl=60 * 60 * 6)
def load_cpi_data(
    app_id: str,
    series_code: str,
) -> pd.DataFrame:
    """指定系列のCPIデータを取得する。"""

    filters = {
        **CPI_BASE_FILTERS,
        "cdCat01": series_code,
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=CPI_STATS_DATA_ID,
        filters=filters,
    )

    return create_cpi_dataframe(response)


def main() -> None:
    st.title("実質賃金分析")

    st.caption(
        "毎月勤労統計調査の現金給与総額を消費者物価指数で実質化し、"
        "名目賃金と購買力の変化を比較します。"
    )

    # -------------------------
    # 分析条件
    # -------------------------

    st.subheader("分析条件")

    condition_col1, condition_col2 = st.columns(2)

    with condition_col1:
        wage_item = st.selectbox(
            "賃金項目",
            list(WAGE_ITEMS.keys()),
            index=list(WAGE_ITEMS.keys()).index(WAGE_DEFAULT_ITEM),
        )

    with condition_col2:
        selected_series = st.selectbox(
            "実質化に使用する消費者物価指数",
            list(CPI_SERIES.keys()),
            index=list(CPI_SERIES.keys()).index(CPI_DEFAULT_SERIES),
        )

    condition_col3, condition_col4 = st.columns(2)

    with condition_col3:
        employment_type = st.selectbox(
            "就業形態",
            list(WAGE_EMPLOYMENT_TYPES.keys()),
            index=list(WAGE_EMPLOYMENT_TYPES.keys()).index(
                WAGE_DEFAULT_EMPLOYMENT_TYPE
            ),
        )

    with condition_col4:
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

    selected_series_code = CPI_SERIES[selected_series]

    # -------------------------
    # データ取得
    # -------------------------

    try:
        app_id = st.secrets["ESTAT_APP_ID"]

    except KeyError:
        st.error(".streamlit/secrets.tomlにESTAT_APP_IDを設定してください。")
        st.stop()

    try:
        raw_wage_df = load_raw_wage_data()

        cpi_df = load_cpi_data(
            app_id,
            selected_series_code,
        )

        wage_df = create_wage_dataframe(
            raw_wage_df,
            wage_item=WAGE_ITEMS[wage_item],
            establishment_size=(WAGE_ESTABLISHMENT_SIZES[establishment_size]),
            employment_type=(WAGE_EMPLOYMENT_TYPES[employment_type]),
        )

        # CSV出力用に名目賃金MAも作っておく
        wage_df = add_wage_moving_average(wage_df)

        df = create_real_wage_dataframe(
            wage_df,
            cpi_df,
            base_year=WAGE_BASE_YEAR,
        )

        df = add_real_wage_changes(df)

    except EStatAPIError as exc:
        st.error(str(exc))
        st.stop()

    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    except (
        KeyError,
        TypeError,
        ValueError,
        pd.errors.MergeError,
    ) as exc:
        st.error(f"実質賃金データの生成に失敗しました: {exc}")
        st.stop()

    if df.empty:
        st.warning("表示可能な実質賃金データがありません。")
        st.stop()

    latest = df.iloc[-1]

    # -------------------------
    # 最新データ
    # -------------------------

    st.subheader("最新データ")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        label=wage_item,
        value=f"{latest['nominal_wage_amount']:,.0f}円",
    )

    col2.metric(
        label=selected_series,
        value=f"{latest['index_value']:.1f}",
    )

    col3.metric(
        label="実質賃金",
        value=(f"{latest['real_wage_amount']:,.0f}円"),
    )

    col4.metric(
        label="実質賃金 前年同月比",
        value=(
            f"{latest['real_wage_yoy_pct']:+.1f}%"
            if pd.notna(latest["real_wage_yoy_pct"])
            else "算出不可"
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
        display_df = df.copy()

    else:
        display_df = df.tail(period_months).copy()

    # -------------------------
    # 名目賃金指数とCPI
    # -------------------------

    st.markdown("#### 名目賃金と物価の比較")

    comparison_df = display_df[
        [
            "date",
            "nominal_wage_index",
            "index_value",
        ]
    ].rename(
        columns={
            "nominal_wage_index": ("名目賃金指数"),
            "index_value": ("消費者物価指数"),
        }
    )

    st.line_chart(
        comparison_df,
        x="date",
        y=[
            "名目賃金指数",
            "消費者物価指数",
        ],
        x_label="年月",
        y_label="指数",
    )

    st.caption("2020年平均=100として、名目賃金の伸びと物価の伸びを比較しています。")

    # -------------------------
    # 実質賃金指数
    # -------------------------

    st.markdown("#### 実質賃金指数")

    real_wage_index_chart_df = display_df[
        [
            "date",
            "real_wage_index",
            "real_wage_index_ma_12",
        ]
    ].copy()

    real_wage_index_chart_df = real_wage_index_chart_df.rename(
        columns={
            "real_wage_index": "月次",
            "real_wage_index_ma_12": "12か月移動平均",
        }
    )

    real_wage_index_chart_columns = ["月次"]

    if show_moving_average:
        real_wage_index_chart_columns.append("12か月移動平均")

    st.line_chart(
        real_wage_index_chart_df,
        x="date",
        y=real_wage_index_chart_columns,
        x_label="年月",
        y_label="実質賃金指数（2020年平均=100）",
    )

    # -------------------------
    # 実質賃金前年同月比
    # -------------------------

    st.markdown("#### 実質賃金 前年同月比")

    yoy_df = display_df.dropna(subset=["real_wage_yoy_pct"])

    st.line_chart(
        yoy_df,
        x="date",
        y="real_wage_yoy_pct",
        x_label="年月",
        y_label="前年同月比（%）",
    )

    # -------------------------
    # データ一覧
    # -------------------------

    st.subheader("分析データ")

    table_df = display_df[
        [
            "date",
            "nominal_wage_amount",
            "nominal_wage_ma_12",
            "index_value",
            "real_wage_amount",
            "real_wage_ma_12",
            "nominal_wage_index",
            "real_wage_index",
            "real_wage_index_ma_12",
            "real_wage_yoy_pct",
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
            "nominal_wage_amount": (
                st.column_config.NumberColumn(
                    "名目賃金",
                    format="%,.0f円",
                )
            ),
            "nominal_wage_ma_12": (
                st.column_config.NumberColumn(
                    "名目賃金 12か月移動平均",
                    format="%,.0f円",
                )
            ),
            "index_value": (
                st.column_config.NumberColumn(
                    selected_series,
                    format="%.1f",
                )
            ),
            "real_wage_amount": (
                st.column_config.NumberColumn(
                    "実質賃金",
                    format="%,.0f円",
                )
            ),
            "real_wage_ma_12": (
                st.column_config.NumberColumn(
                    "実質賃金 12か月移動平均",
                    format="%,.0f円",
                )
            ),
            "nominal_wage_index": (
                st.column_config.NumberColumn(
                    "名目賃金指数",
                    format="%.1f",
                )
            ),
            "real_wage_index": (
                st.column_config.NumberColumn(
                    "実質賃金指数",
                    format="%.1f",
                )
            ),
            "real_wage_index_ma_12": (
                st.column_config.NumberColumn(
                    "実質賃金指数 12か月移動平均",
                    format="%.1f",
                )
            ),
            "real_wage_yoy_pct": (
                st.column_config.NumberColumn(
                    "実質賃金 前年同月比",
                    format="%.1f%%",
                )
            ),
        },
    )

    # -------------------------
    # CSV
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

    csv_df.insert(
        5,
        "cpi_series",
        selected_series,
    )

    csv_df = csv_df.drop(columns="date")

    csv_data = csv_df.to_csv(index=False).encode("utf-8-sig")

    download_col, refresh_col = st.columns([2, 1])

    with download_col:
        st.download_button(
            label=("全期間データをCSVでダウンロード"),
            data=csv_data,
            file_name="real_wage.csv",
            mime="text/csv",
        )

    with refresh_col:
        if st.button(
            "データを再取得",
            width="stretch",
        ):
            load_raw_wage_data.clear()
            load_cpi_data.clear()
            st.rerun()

    # -------------------------
    # 出典・計算方法
    # -------------------------

    with st.expander("データ出典・算出方法"):
        st.markdown(
            f"""
            ### 名目賃金

            - **出典**：{WAGE_METADATA["source"]}
            - **統計**：{WAGE_METADATA["statistics_name"]}
            - **賃金項目**：{wage_item}
            - **産業**：調査産業計
            - **事業所規模**：{establishment_size}
            - **就業形態**：{employment_type}

            ### 消費者物価指数

            - **出典**：{CPI_METADATA["source"]}
            - **統計**：{CPI_METADATA["statistics_name"]}
            - **対象系列**：{selected_series}
            - **品目コード**：{selected_series_code}
            - **指数基準**：{CPI_METADATA["base_year"]}

            ### 算出方法

            **実質賃金額 = 名目賃金 ÷ CPI × 100**

            名目賃金指数および実質賃金指数は、
            **2020年平均=100**としてアプリ内で指数化しています。

            実質賃金の12か月移動平均は、
            各月の実質賃金を算出した後、その連続12か月平均を計算しています。
            """
        )

    st.info(
        "このページの実質賃金は、選択した毎月勤労統計の賃金データを、"
        "選択した消費者物価指数で調整してアプリ内で算出したものです。"
        "公表されている実質賃金指数とは、算出条件などにより一致しない場合があります。"
    )


if __name__ == "__main__":
    main()
