import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.industry_analysis import INDUSTRY_NAMES
from real_wage_dashboard.industry_composition_analysis import (
    add_industry_employment_share,
    create_all_industry_employment_monthly_dataframe,
    create_industry_composition_base_dataframe,
    create_industry_composition_decomposition,
    create_industry_employment_yearly_dataframe,
    create_industry_wage_yearly_dataframe,
    create_reconstructed_average_wage_dataframe,
)
from real_wage_dashboard.wage_service import load_wage_csv


st.set_page_config(
    page_title="産業構成効果分析",
    layout="wide",
)

st.title("産業構成効果分析")

st.caption("2015年から2025年の平均賃金変化を、各産業内の賃金変化と産業別雇用シェアの変化に分解します。")

st.subheader("問い")

st.markdown(
    """
    **2015年から2025年にかけての平均賃金上昇は、\
    各産業の中で賃金が上昇した効果と、\
    産業別の雇用シェアが変化した効果にどの程度分けられるか。**
    """
)

st.subheader("分析条件")

st.markdown(
    """
    - **データ**：毎月勤労統計調査
    - **賃金**：きまって支給する給与
    - **事業所規模**：5人以上
    - **就業形態**：就業形態計
    - **産業**：C～Rの主要16産業
    - **主比較期間**：2015年平均 → 2025年平均
    - **雇用ウェイト**：前月末労働者数と本月末労働者数の平均
    """
)

raw_df = load_wage_csv(WAGE_DATA_PATH)

employment_monthly_df = (
    create_all_industry_employment_monthly_dataframe(
        raw_df,
    )
)

employment_yearly_df = (
    create_industry_employment_yearly_dataframe(
        employment_monthly_df,
    )
)

employment_yearly_df = add_industry_employment_share(
    employment_yearly_df,
)

wage_yearly_df = create_industry_wage_yearly_dataframe(
    raw_df,
)

base_df = create_industry_composition_base_dataframe(
    wage_yearly_df,
    employment_yearly_df,
)

reconstructed_df = create_reconstructed_average_wage_dataframe(
    base_df,
)

decomposition_df = create_industry_composition_decomposition(
    base_df,
    start_year=2015,
    end_year=2025,
)

start_wage = reconstructed_df.loc[
    reconstructed_df["year"] == 2015,
    "reconstructed_wage",
].iloc[0]

end_wage = reconstructed_df.loc[
    reconstructed_df["year"] == 2025,
    "reconstructed_wage",
].iloc[0]

within = decomposition_df["within_wage_effect"].sum()
composition = decomposition_df["composition_effect"].sum()
interaction = decomposition_df["interaction_effect"].sum()

total_change = end_wage - start_wage

within_pt = within / start_wage * 100
composition_pt = composition / start_wage * 100
interaction_pt = interaction / start_wage * 100
total_change_pt = total_change / start_wage * 100

st.subheader("分析結果")

st.markdown(
    f"""
    - **平均賃金変化**：{total_change_pt:+.2f}%
    - **産業内賃金効果**：{within_pt:+.2f}pt
    - **産業構成効果**：{composition_pt:+.2f}pt
    - **交差効果**：{interaction_pt:+.2f}pt
    """
)

st.subheader("考察")

st.markdown(
    f"""
    2015年から2025年の平均賃金は **{total_change_pt:+.2f}%** 上昇しました。

    このうち産業内賃金効果は **{within_pt:+.2f}pt** であり、
    平均賃金上昇の大部分は各産業の中で賃金が上昇したことによって説明されます。

    一方、産業構成効果は **{composition_pt:+.2f}pt** で、
    産業構成の変化は平均賃金をわずかに押し下げる方向に作用しました。
    """
)

st.caption(
    "本分析は平均賃金変化を恒等的に分解するものであり、"
    "産業構成変化が賃金変化を因果的に生じさせたことを示すものではありません。"
)

st.divider()