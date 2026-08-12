import pandas as pd
import streamlit as st

from real_wage_dashboard.config import (
    WAGE_DATA_PATH,
    WAGE_METADATA,
)
from real_wage_dashboard.wage_analysis import add_wage_changes
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
def load_wage_data() -> pd.DataFrame:
    """毎月勤労統計CSVを読み込み、分析用DataFrameを返す。"""

    raw_df = load_wage_csv(WAGE_DATA_PATH)
    df = create_wage_dataframe(raw_df)
    df = add_wage_changes(df)

    return df


def main() -> None:
    st.title("名目賃金分析")

    st.caption("毎月勤労統計調査の現金給与総額から、名目賃金の推移を表示します。")

    try:
        df = load_wage_data()

    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    except (KeyError, TypeError, ValueError) as exc:
        st.error(f"賃金データの読み込みまたは変換に失敗しました: {exc}")
        st.stop()

    if df.empty:
        st.warning("表示可能な名目賃金データがありません。")
        st.stop()

    if len(df) < 2:
        st.warning("前月比を計算するためのデータ件数が不足しています。")

    if len(df) < 13:
        st.warning("前年同月比を計算するためのデータ件数が不足しています。")

    latest = df.iloc[-1]

    # -------------------------
    # 最新データ
    # -------------------------

    st.subheader("最新データ")

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    metric_col1.metric(
        label="現金給与総額",
        value=f"{latest['nominal_wage_amount']:,.0f}円",
    )

    metric_col2.metric(
        label="前月比",
        value=(
            f"{latest['mom_pct']:+.1f}%"
            if pd.notna(latest["mom_pct"])
            else "算出不可"
        ),
    )

    metric_col3.metric(
        label="前年同月比",
        value=(
            f"{latest['yoy_pct']:+.1f}%"
            if pd.notna(latest["yoy_pct"])
            else "算出不可"
        ),
    )

    st.caption(f"最新データ：{latest['date'].strftime('%Y年%m月')}")

    # -------------------------
    # 表示期間
    # -------------------------

    st.subheader("時系列推移")

    period = st.selectbox(
        "表示期間",
        [
            "直近1年",
            "直近3年",
            "直近5年",
            "直近10年",
            "直近20年",
            "直近30年",
            "全期間",
        ],
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
    # 現金給与総額
    # -------------------------

    st.markdown("#### 現金給与総額")

    st.line_chart(
        display_period_df,
        x="date",
        y="nominal_wage_amount",
        x_label="年月",
        y_label="現金給与総額（円）",
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
                    "現金給与総額",
                    format="%,.0f円",
                )
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

    csv_df = csv_df.drop(
        columns="date",
    )

    csv_df = csv_df.rename(
        columns={
            "year": "年",
            "month": "月",
            "nominal_wage_amount": "現金給与総額",
            "mom_pct": "前月比(%)",
            "yoy_pct": "前年同月比(%)",
        }
    )

    csv_data = (
        csv_df.to_csv(index=False)
        .encode("utf-8-sig")
    )

    download_col, refresh_col = st.columns(
        [2, 1]
    )

    with download_col:
        st.download_button(
            label="全期間データをCSVでダウンロード",
            data=csv_data,
            file_name="nominal_wage.csv",
            mime="text/csv",
        )

    with refresh_col:
        if st.button(
            "データを再読み込み",
            width="stretch",
        ):
            load_wage_data.clear()
            st.rerun()

    # -------------------------
    # 出典
    # -------------------------

    with st.expander(
        "データ出典・算出方法"
    ):
        st.markdown(
            f"""
            - **出典**：{WAGE_METADATA["source"]}
            - **統計**：{WAGE_METADATA["statistics_name"]}
            - **項目**：{WAGE_METADATA["item_name"]}
            - **産業**：{WAGE_METADATA["industry"]}
            - **事業所規模**：{WAGE_METADATA["establishment_size"]}
            - **就業形態**：{WAGE_METADATA["employment_type"]}
            - **単位**：{WAGE_METADATA["unit"]}
            """
        )

    st.info(
        "前月比と前年同月比は、現金給与総額からアプリ内で計算しています。"
        "現金給与総額は賞与などの影響を受けるため、月ごとの変動が大きくなる場合があります。"
    )


if __name__ == "__main__":
    main()
