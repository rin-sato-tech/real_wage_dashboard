from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import (
    CPI_BASE_FILTERS,
    CPI_FILE_NAMES,
    CPI_METADATA,
    CPI_SERIES,
    CPI_STATS_DATA_ID,
)
from real_wage_dashboard.cpi_analysis import (
    add_cpi_changes,
    add_cpi_moving_average,
)
from real_wage_dashboard.cpi_service import load_cpi_dataframe
from real_wage_dashboard.estat_client import EStatAPIError
from real_wage_dashboard.ui import (
    CPI_COLOR,
    MONTHLY_OPACITY,
    MONTHLY_STROKE_WIDTH,
    MOVING_AVERAGE_OPACITY,
    MOVING_AVERAGE_STROKE_WIDTH,
    PERIOD_OPTIONS,
    REFERENCE_LINE_COLOR,
    YOY_STROKE_WIDTH,
    create_time_axis,
    filter_display_period,
)

st.set_page_config(
    page_title="消費者物価指数分析",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=60 * 60 * 6)
def load_cpi_data(app_id: str, series_code: str) -> tuple[pd.DataFrame, datetime]:
    """選択されたCPIをe-Stat APIから取得し、分析用DataFrameを返す。"""

    df = load_cpi_dataframe(app_id, series_code)
    df = add_cpi_changes(df)
    df = add_cpi_moving_average(df)

    fetched_at = datetime.now().astimezone()

    return df, fetched_at


def main() -> None:
    st.title("消費者物価指数分析")

    st.caption(
        "消費者物価指数の推移を確認します。"
        "物価上昇が賃金の購買力に与える影響を見るための基礎となるページです。"
    )

    # -------------------------
    # 分析条件
    # -------------------------

    st.subheader("分析条件")

    selected_series = st.selectbox(
        "表示する系列",
        options=list(CPI_SERIES.keys()),
    )

    selected_series_code = CPI_SERIES[selected_series]

    show_moving_average = st.toggle(
        "12か月移動平均を表示",
        value=True,
    )

    # -------------------------
    # データ取得
    # -------------------------

    try:
        app_id = st.secrets["ESTAT_APP_ID"]

    except KeyError:
        st.error(".streamlit/secrets.tomlにESTAT_APP_IDを設定してください。")
        st.stop()

    try:
        df, fetched_at = load_cpi_data(app_id, selected_series_code)

    except EStatAPIError as exc:
        st.error(str(exc))
        st.stop()

    except (KeyError, TypeError, ValueError) as exc:
        st.error(f"取得データの変換または計算に失敗しました: {exc}")
        st.stop()

    if df.empty:
        st.warning("表示可能なCPIデータがありません。")
        st.stop()

    if len(df) < 2:
        st.warning("前月比を計算するためのデータ件数が不足しています。")

    if len(df) < 13:
        st.warning("前年同月比を計算するためのデータ件数が不足しています。")

    latest = df.iloc[-1]

    # -------------------------
    # 主要結果
    # -------------------------

    st.subheader("主要結果")

    metric_col1, metric_col2 = st.columns(2)

    metric_col1.metric(
        label=selected_series,
        value=f"{latest['index_value']:.1f}",
    )

    metric_col2.metric(
        label="前年同月比",
        value=(
            f"{latest['yoy_pct']:+.1f}%" if pd.notna(latest["yoy_pct"]) else "算出不可"
        ),
    )

    st.caption(
        f"最新データ：{latest['date'].strftime('%Y年%m月')}　"
        f"API取得日時：{fetched_at.strftime('%Y年%m月%d日 %H:%M')}"
    )

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

    st.markdown(f"#### {selected_series}")

    st.caption("月次：薄い線　／　12か月移動平均：濃い線")

    index_chart_df = display_period_df[
        [
            "date",
            "index_value",
            "index_value_ma_12",
        ]
    ].rename(
        columns={
            "index_value": "月次",
            "index_value_ma_12": "12か月移動平均",
        }
    )

    index_columns = ["月次"]

    if show_moving_average:
        index_columns.append("12か月移動平均")

    index_long_df = index_chart_df.melt(
        id_vars="date",
        value_vars=index_columns,
        var_name="系列",
        value_name="指数",
    )

    index_min = index_long_df["指数"].min()
    index_max = index_long_df["指数"].max()

    index_padding = max(
        (index_max - index_min) * 0.1,
        1.0,
    )

    monthly_chart = (
        alt.Chart(display_period_df)
        .mark_line(
            color=CPI_COLOR,
            strokeWidth=MONTHLY_STROKE_WIDTH,
            opacity=MONTHLY_OPACITY,
        )
        .encode(
            x=create_time_axis(display_period_df, period),
            y=alt.Y(
                "index_value:Q",
                title=selected_series,
                scale=alt.Scale(
                    domain=[
                        index_min - index_padding,
                        index_max + index_padding,
                    ],
                    zero=False,
                ),
                axis=alt.Axis(
                    grid=True,
                    gridOpacity=0.6,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="年月",
                    format="%Y年%m月"
                ),
                alt.Tooltip(
                    "index_value:Q",
                    title="月次",
                    format=".1f"
                ),
            ],
        )
    )

    moving_average_chart = (
        alt.Chart(display_period_df)
        .mark_line(
            color=CPI_COLOR,
            strokeWidth=MOVING_AVERAGE_STROKE_WIDTH,
            opacity=MOVING_AVERAGE_OPACITY,
        )
        .encode(
            x=create_time_axis(display_period_df, period),
            y=alt.Y(
                "index_value_ma_12:Q",
                title=selected_series,
                scale=alt.Scale(
                    domain=[
                        index_min - index_padding,
                        index_max + index_padding,
                    ],
                    zero=False,
                ),
                axis=alt.Axis(
                    grid=True,
                    gridOpacity=0.6,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="年月",
                    format="%Y年%m月"
                ),
                alt.Tooltip(
                    "index_value_ma_12:Q",
                    title="12か月移動平均",
                    format=".1f",
                ),
            ],
        )
    )

    if show_moving_average:
        chart = monthly_chart + moving_average_chart
    else:
        chart = monthly_chart

    st.altair_chart(
        chart,
        width="stretch",
    )

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
            color=CPI_COLOR,
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
            "index_value",
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
            "index_value": st.column_config.NumberColumn(
                "指数",
                format="%.1f",
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

    csv_df = df[
        [
            "date",
            "index_value",
            "mom_pct",
            "yoy_pct",
        ]
    ].copy()

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

    csv_df = csv_df.drop(columns="date")

    csv_df = csv_df.rename(
        columns={
            "year": "年",
            "month": "月",
            "index_value": "消費者物価指数",
            "mom_pct": "前月比(%)",
            "yoy_pct": "前年同月比(%)",
        }
    )

    csv_data = csv_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="全期間データをCSVでダウンロード",
        data=csv_data,
        file_name=CPI_FILE_NAMES[selected_series],
        mime="text/csv",
    )

    # -------------------------
    # 出典・算出方法
    # -------------------------

    with st.expander("データ出典・算出方法"):
        st.markdown(
            f"""
            - **出典**：{CPI_METADATA["source"]}
            - **統計**：{CPI_METADATA["statistics_name"]}
            - **対象地域**：{CPI_METADATA["area_name"]}
            - **対象系列**：{selected_series}
            - **統計表ID**：{CPI_STATS_DATA_ID}
            - **表章項目コード**：{CPI_BASE_FILTERS["cdTab"]}
            - **品目コード**：{selected_series_code}
            - **地域コード**：{CPI_BASE_FILTERS["cdArea"]}
            - **指数基準**：{CPI_METADATA["base_year"]}
            """
        )

    st.info(
        "前月比と前年同月比は、取得した消費者物価指数からアプリ内で計算しています。"
        "公表値とは丸め処理などにより、わずかに異なる場合があります。"
    )


if __name__ == "__main__":
    main()
