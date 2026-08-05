import pandas as pd
import streamlit as st

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
def load_cpi_data(app_id: str) -> pd.DataFrame:
    """e-Stat APIからCPIを取得し、DataFrameとして返す。"""

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=STATS_DATA_ID,
        filters=CPI_FILTERS,
    )

    return create_cpi_dataframe(response)


def main() -> None:
    st.title("消費者物価指数分析")

    st.caption("e-Stat APIから取得した全国・総合の消費者物価指数を表示します。")

    try:
        app_id = st.secrets["ESTAT_APP_ID"]
        df = load_cpi_data(app_id)

    except KeyError:
        st.error(".streamlit/secrets.tomlにESTAT_APP_IDを設定してください。")
        st.stop()

    except EStatAPIError as exc:
        st.error(str(exc))
        st.stop()

    if df.empty:
        st.warning("表示できるCPIデータがありません。")
        st.stop()

    latest = df.iloc[-1]

    st.subheader("最新データ")

    metric_col1, metric_col2 = st.columns(2)

    metric_col1.metric(
        label="最新指数",
        value=f'{latest["index_value"]:.1f}',
    )

    metric_col2.metric(
        label="対象年月",
        value=latest["date"].strftime("%Y年%m月"),
    )

    st.subheader("指数の推移")

    st.line_chart(
        df,
        x="date",
        y="index_value",
        x_label="年月",
        y_label="消費者物価指数",
    )

    st.subheader("取得データ")

    display_df = df[
        [
            "date",
            "time_name",
            "index_value",
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
            "time_name": "e-Stat表記",
            "index_value": st.column_config.NumberColumn(
                "指数",
                format="%.1f",
            ),
        },
    )


if __name__ == "__main__":
    main()