import pandas as pd
import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.industry_analysis import (
    INDUSTRY_NAMES,
    MAIN_INDUSTRIES,
    add_industry_wage_decomposition,
    create_industry_comparison_dataframe,
    identify_notable_industries,
    summarize_industry_changes,
)
from real_wage_dashboard.wage_service import load_wage_csv


ANALYSIS_START_YEAR = 2015
ANALYSIS_END_YEAR = 2025


st.set_page_config(
    page_title="産業別賃金分析",
    page_icon="🏭",
    layout="wide",
)


@st.cache_data
def load_raw_wage_data() -> pd.DataFrame:
    """毎月勤労統計の元CSVを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)

raw_df = load_raw_wage_data()

comparison_df = create_industry_comparison_dataframe(
    raw_df,
    industry_codes=MAIN_INDUSTRIES,
    start_year=ANALYSIS_START_YEAR,
    end_year=ANALYSIS_END_YEAR,
)

decomposition_df = add_industry_wage_decomposition(comparison_df)

summary = summarize_industry_changes(decomposition_df)

notable = identify_notable_industries(decomposition_df)

st.title("産業別賃金分析")

st.markdown(
    """
    産業ごとの月額賃金の変化を比較し、
    **1時間あたり賃金（概算）と労働時間のどちらが変化を生んだのか**
    を確認します。
    """
)

st.caption(
    "「1時間あたり賃金（概算）」は、"
    "月額のきまって支給する給与を総実労働時間で割って算出した指標です。"
)

st.subheader("問い")

st.markdown(
    f"""
    **{ANALYSIS_START_YEAR}年から{ANALYSIS_END_YEAR}年の賃金上昇は、
    幅広い産業で生じたのか。**

    また、産業ごとの月額賃金の変化は、

    - 1時間あたり賃金（概算）の変化
    - 総実労働時間の変化

    のどちらによって生じたのかを確認します。
    """
)

st.code(
    """
    産業別の月額賃金変化
    ├─ 1時間あたり賃金（概算）の変化
    └─ 総実労働時間の変化
    """,
    language=None,
)

st.divider()

st.subheader("分析条件")

st.markdown(
    f"""
    - データ：毎月勤労統計調査
    - 産業：産業大分類16産業
    - 比較基準：調査産業計
    - 事業所規模：5人以上
    - 就業形態：就業形態計
    - 比較期間：{ANALYSIS_START_YEAR}年平均 → {ANALYSIS_END_YEAR}年平均
    - 月額賃金：きまって支給する給与
    """
)

st.subheader("分析結果")

st.markdown(
    f"""
    {ANALYSIS_START_YEAR}年から{ANALYSIS_END_YEAR}年にかけて、
    **16産業すべてで月額賃金が上昇**しました。

    産業別の月額賃金上昇率の中央値は
    **{summary["wage_change_median"]:+.2f}%**で、
    調査産業計（{summary["total_wage_change"]:+.2f}%）を上回ったのは
    **{summary["above_total_count"]}産業 / 16産業
    （{summary["above_total_share"]:.1f}%）**でした。

    一方、上昇率は
    **{summary["wage_change_min"]:+.2f}%～
    {summary["wage_change_max"]:+.2f}%**
    と産業による差も確認されました。

    また、**全16産業で1時間あたり賃金（概算）が上昇し、
    総実労働時間は減少**していました。
    つまり、時間単価の上昇が月額賃金を押し上げる一方、
    労働時間の減少がその一部を相殺する構造が共通して見られます。
    """
)

st.subheader("考察")

max_wage_industry = INDUSTRY_NAMES[
    notable["monthly_wage_growth_max"]
]

min_wage_industry = INDUSTRY_NAMES[
    notable["monthly_wage_growth_min"]
]

offset_industry = INDUSTRY_NAMES[
    notable["monthly_hourly_gap_max"]
]

st.markdown(
    f"""
    賃金上昇は一部の産業だけに集中したものではなく、
    **全産業に広がっていました**。

    ただし、その程度は一様ではありません。
    月額賃金の上昇が最も大きかったのは
    **{max_wage_industry}**、
    最も小さかったのは
    **{min_wage_industry}**でした。

    また、**{offset_industry}**では
    1時間あたり賃金の上昇が大きい一方、
    労働時間の減少による押し下げも大きく、
    月額賃金だけを見ると時間単価の上昇が見えにくくなっています。

    このため、産業別の賃金動向を評価する際には、
    月額賃金だけでなく、
    **賃金単価と労働時間を分けて見る必要があります。**
    """
)

st.caption(
    "産業平均には、一般労働者・パートタイム労働者の構成、"
    "年齢、職種、事業所規模などの違いが含まれます。"
    "本分析だけから賃金変化の因果関係を特定することはできません。"
)

st.divider()
