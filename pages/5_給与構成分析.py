import pandas as pd
import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.wage_composition_analysis import (
    add_annual_wage_contributions,
    add_wage_composition_changes,
    add_wage_composition_contributions,
    add_wage_composition_moving_averages,
    add_wage_composition_shares,
    create_complete_annual_wage_composition_summary,
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

    st.subheader("給与構成の推移")

    st.caption("次の実装で時系列グラフを追加します。")


if __name__ == "__main__":
    main()
