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
from real_wage_dashboard.cpi_analysis import add_cpi_changes
from real_wage_dashboard.cpi_service import load_cpi_dataframe
from real_wage_dashboard.estat_client import EStatAPIError
from real_wage_dashboard.ui import (
    PERIOD_OPTIONS,
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

    fetched_at = datetime.now().astimezone()

    return df, fetched_at


def main() -> None:
    st.title("消費者物価指数分析")

    st.caption(
        "賃金の実質化に用いる消費者物価指数について、水準と前年比の推移を確認します。"
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

    index_min = display_period_df["index_value"].min()
    index_max = display_period_df["index_value"].max()

    index_padding = max(
        (index_max - index_min) * 0.1,
        1.0,
    )

    index_chart = (
        alt.Chart(display_period_df)
        .mark_line()
        .encode(
            x=alt.X(
                "date:T",
                title="年月",
            ),
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
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="年月",
                    format="%Y年%m月",
                ),
                alt.Tooltip(
                    "index_value:Q",
                    title=selected_series,
                    format=".1f",
                ),
            ],
        )
        .properties(height=400)
    )

    st.altair_chart(
        index_chart,
        width="stretch",
    )

    st.markdown("#### 前年同月比")

    yoy_df = display_period_df.dropna(subset=["yoy_pct"])

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(strokeDash=[4, 4])
        .encode(
            y="y:Q",
        )
    )

    yoy_chart = (
        alt.Chart(yoy_df)
        .mark_line()
        .encode(
            x=alt.X(
                "date:T",
                title="年月",
            ),
            y=alt.Y(
                "yoy_pct:Q",
                title="前年同月比（%）",
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

    download_col, refresh_col = st.columns([2, 1])

    with download_col:
        st.download_button(
            label="全期間データをCSVでダウンロード",
            data=csv_data,
            file_name=CPI_FILE_NAMES[selected_series],
            mime="text/csv",
        )

    with refresh_col:
        if st.button(
            "データを再取得",
            width="stretch",
        ):
            load_cpi_data.clear()
            st.rerun()

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
