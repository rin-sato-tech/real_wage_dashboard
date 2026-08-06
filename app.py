from datetime import datetime

import pandas as pd
import streamlit as st

from real_wage_dashboard.config import (
    CPI_FILTERS,
    CPI_METADATA,
    CPI_STATS_DATA_ID,
)
from real_wage_dashboard.cpi_analysis import add_cpi_changes
from real_wage_dashboard.cpi_service import create_cpi_dataframe
from real_wage_dashboard.estat_client import (
    EStatAPIError,
    get_stats_data,
)


STATS_DATA_ID = "0003427113"

CPI_FILTERS = {
    "cdTab": "1",
    "cdCat01": "0001",
    "cdArea": "00000",
}


st.set_page_config(
    page_title="消費者物価指数分析",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=60 * 60 * 6)
def load_cpi_data(app_id: str) -> tuple[pd.DataFrame, datetime]:
    """e-Stat APIからCPIを取得し、分析用DataFrameを返す。"""

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=CPI_STATS_DATA_ID,
        filters=CPI_FILTERS,
    )

    df = create_cpi_dataframe(response)
    df = add_cpi_changes(df)

    fetched_at = datetime.now().astimezone()

    return df, fetched_at


def main() -> None:
    st.title("消費者物価指数分析")

    st.caption("e-Stat APIから取得した全国・総合の消費者物価指数を表示します。")

    try:
        app_id = st.secrets["ESTAT_APP_ID"]
        df, fetched_at = load_cpi_data(app_id)

    except KeyError:
        st.error(".streamlit/secrets.tomlにESTAT_APP_IDを設定してください。")
        st.stop()

    except EStatAPIError as exc:
        st.error(str(exc))
        st.stop()

    except (TypeError, ValueError) as exc:
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

    st.subheader("最新データ")

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    metric_col1.metric(
        label="消費者物価指数",
        value=f"{latest['index_value']:.1f}",
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

    st.caption(
        f"最新データ：{latest['date'].strftime('%Y年%m月')}　"
        f"API取得日時：{fetched_at.strftime('%Y年%m月%d日 %H:%M')}"
    )

    st.subheader("時系列推移")

    period = st.selectbox(
        "表示期間",
        {
            "直近1年": 12,
            "直近3年": 36,
            "直近5年": 60,
            "直近10年": 120,
            "直近20年": 240,
            "直近30年": 360,
            "全期間": None,
        },
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

    st.markdown("#### 消費者物価指数")

    st.line_chart(
        display_period_df,
        x="date",
        y="index_value",
        x_label="年月",
        y_label="消費者物価指数",
    )

    st.markdown("#### 前年同月比")

    yoy_df = display_period_df.dropna(subset=["yoy_pct"])

    st.line_chart(
        yoy_df,
        x="date",
        y="yoy_pct",
        x_label="年月",
        y_label="前年同月比（%）",
    )

    st.subheader("取得データ")

    display_df = display_period_df[
        [
            "date",
            "index_value",
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

    csv_data = csv_df.to_csv(
        index=False,
    ).encode("utf-8-sig")

    download_col, refresh_col = st.columns([2, 1])

    with download_col:
        st.download_button(
            label="全期間データをCSVでダウンロード",
            data=csv_data,
            file_name="cpi_all_japan.csv",
            mime="text/csv",
        )

    with refresh_col:
        if st.button(
            "データを再取得",
            width="stretch",
        ):
            load_cpi_data.clear()
            st.rerun()

    with st.expander("データ出典・算出方法"):
        st.markdown(
            """
            - **出典**：政府統計の総合窓口 e-Stat
            - **統計**：消費者物価指数
            - **対象地域**：全国
            - **対象系列**：総合
            - **統計表ID**：0003427113
            - **表章項目コード**：1
            - **品目コード**：0001
            - **地域コード**：00000
            - **指数基準**：2020年=100
            """
        )

    st.info(
        "前月比と前年同月比は、取得した消費者物価指数からアプリ内で計算しています。"
        "公表値とは丸め処理などにより、わずかに異なる場合があります。"
    )


if __name__ == "__main__":
    main()
