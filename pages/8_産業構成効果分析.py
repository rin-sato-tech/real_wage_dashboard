import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.industry_analysis import INDUSTRY_NAMES
from real_wage_dashboard.industry_composition_analysis import (
    add_industry_employment_share,
    create_all_industry_employment_monthly_dataframe,
    create_industry_composition_analysis_discussion,
    create_industry_composition_analysis_results,
    create_industry_composition_base_dataframe,
    create_industry_composition_decomposition,
    create_industry_employment_yearly_dataframe,
    create_industry_monthly_dataframe,
    create_industry_wage_yearly_dataframe,
    create_industry_yearly_dataframe,
    create_reconstructed_average_wage_dataframe,
)
from real_wage_dashboard.wage_service import load_wage_csv

st.set_page_config(
    page_title="産業構成効果分析",
    layout="wide",
)

st.title("産業構成効果分析")

st.caption(
    "2015年から2025年の平均賃金変化を、各産業内の賃金変化と産業別雇用シェアの変化に分解します。"
)

st.subheader("問い")

st.markdown(
    """
    **2015年から2025年にかけての平均賃金上昇は、何によって生じたのか。**

    平均賃金は、各産業の賃金が上昇するだけでなく、賃金水準の異なる産業の雇用シェアが変化することでも動きます。

    そこで、平均賃金の変化を

    - 各産業の中で賃金が変化した効果
    - 産業別の雇用シェアが変化した効果

    に分けることで、平均賃金の上昇が「各産業で賃金が上がったため」なのか、「雇用される産業の構成が変わったため」なのかを切り分けます。
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

st.caption(
    "本分析は就業形態計を用いているため、産業内賃金効果には、"
    "一般労働者・パートタイム労働者それぞれの賃金変化だけでなく、"
    "産業内部の就業形態構成の変化も含まれます。"
)

raw_df = load_wage_csv(WAGE_DATA_PATH)

employment_monthly_df = create_all_industry_employment_monthly_dataframe(
    raw_df,
)

employment_yearly_df = create_industry_employment_yearly_dataframe(
    employment_monthly_df,
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

analysis_results = create_industry_composition_analysis_results(
    decomposition_df,
    reconstructed_df,
)

analysis_discussion = create_industry_composition_analysis_discussion(
    decomposition_df,
)

st.subheader("分析結果")

for result in analysis_results:
    st.markdown(f"- {result}")

st.subheader("考察")

for discussion in analysis_discussion:
    st.markdown(f"- {discussion}")

st.caption(
    "本分析は平均賃金変化を恒等的に分解するものであり、"
    "産業構成変化が賃金変化を因果的に生じさせたことを示すものではありません。"
)

st.divider()

st.subheader("平均賃金変化の要因分解")

st.info(
    """
    平均賃金の変化を、次の3つの効果に分けます。

    - **産業内賃金効果**：各産業の雇用シェアが変わらなかったと仮定したときの、産業内の賃金変化による効果
    - **産業構成効果**：各産業の賃金が変わらなかったと仮定したときの、雇用シェア変化による効果
    - **交差効果**：賃金と雇用シェアが同時に変化したことで生じる残りの効果
    """
)

decomposition_summary = pd.DataFrame(
    {
        "factor": [
            "産業内賃金効果",
            "産業構成効果",
            "交差効果",
        ],
        "effect_yen": [
            within,
            composition,
            interaction,
        ],
    }
)

decomposition_chart = (
    alt.Chart(decomposition_summary)
    .mark_bar()
    .encode(
        x=alt.X(
            "effect_yen:Q",
            title="平均賃金への寄与（円）",
        ),
        y=alt.Y(
            "factor:N",
            title=None,
            sort=[
                "産業内賃金効果",
                "産業構成効果",
                "交差効果",
            ],
        ),
        tooltip=[
            alt.Tooltip(
                "factor:N",
                title="要因",
            ),
            alt.Tooltip(
                "effect_yen:Q",
                title="寄与",
                format="+,.0f",
            ),
        ],
    )
    .properties(
        height=220,
    )
)

decomposition_zero_line = alt.Chart({"values": [{"x": 0}]}).mark_rule().encode(x="x:Q")

st.altair_chart(
    decomposition_chart + decomposition_zero_line,
    width="stretch",
)

st.caption(
    f"2015→2025の平均賃金変化は {total_change:+,.0f}円（{total_change_pt:+.2f}%）。"
    f"内訳は、産業内賃金効果 {within:+,.0f}円（{within_pt:+.2f}pt）、"
    f"産業構成効果 {composition:+,.0f}円（{composition_pt:+.2f}pt）、"
    f"交差効果 {interaction:+,.0f}円（{interaction_pt:+.2f}pt）です。"
)

st.divider()

share_target = employment_yearly_df[
    employment_yearly_df["year"].isin([2015, 2025])
].copy()

share_comparison = (
    share_target.pivot(
        index="industry",
        columns="year",
        values="employment_share",
    )
    .rename(
        columns={
            2015: "share_2015",
            2025: "share_2025",
        }
    )
    .reset_index()
)

share_comparison["share_change_pt"] = (
    share_comparison["share_2025"] - share_comparison["share_2015"]
) * 100

share_comparison["industry_name"] = share_comparison["industry"].map(INDUSTRY_NAMES)

share_comparison = share_comparison.sort_values(
    "share_change_pt",
    ascending=True,
)

st.subheader("産業別の雇用シェア変化")

share_chart = (
    alt.Chart(share_comparison)
    .mark_bar()
    .encode(
        x=alt.X(
            "share_change_pt:Q",
            title="雇用シェア変化（pt）",
        ),
        y=alt.Y(
            "industry_name:N",
            title=None,
            sort=None,
            axis=alt.Axis(
                labelLimit=240,
                labelPadding=8,
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "industry_name:N",
                title="産業",
            ),
            alt.Tooltip(
                "share_2015:Q",
                title="2015年シェア",
                format=".2%",
            ),
            alt.Tooltip(
                "share_2025:Q",
                title="2025年シェア",
                format=".2%",
            ),
            alt.Tooltip(
                "share_change_pt:Q",
                title="変化",
                format="+.2f",
            ),
        ],
    )
    .properties(
        height=520,
    )
)

zero_line = alt.Chart({"values": [{"x": 0}]}).mark_rule().encode(x="x:Q")

st.altair_chart(
    share_chart + zero_line,
    width="stretch",
)

st.caption(
    "2015年から2025年にかけて、医療・福祉やその他のサービス業では"
    "雇用シェアが上昇する一方、製造業、運輸業・郵便業、建設業では低下しました。"
)

st.divider()

st.subheader("産業別の構成寄与")

composition_industry_df = decomposition_df.copy()

composition_industry_df["industry_name"] = composition_industry_df["industry"].map(
    INDUSTRY_NAMES
)

composition_industry_df = composition_industry_df.sort_values(
    "centered_composition_effect_pt",
    ascending=True,
)

composition_industry_chart = (
    alt.Chart(composition_industry_df)
    .mark_bar()
    .encode(
        x=alt.X(
            "centered_composition_effect_pt:Q",
            title="産業構成効果への寄与（pt）",
        ),
        y=alt.Y(
            "industry_name:N",
            title=None,
            sort=None,
            axis=alt.Axis(
                labelLimit=240,
                labelPadding=8,
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "industry_name:N",
                title="産業",
            ),
            alt.Tooltip(
                "start_wage:Q",
                title="2015年賃金",
                format=",.0f",
            ),
            alt.Tooltip(
                "share_change:Q",
                title="雇用シェア変化",
                format="+.3%",
            ),
            alt.Tooltip(
                "composition_pattern:N",
                title="構成",
            ),
            alt.Tooltip(
                "centered_composition_effect_pt:Q",
                title="構成寄与",
                format="+.3f",
            ),
        ],
    )
    .properties(
        height=520,
    )
)

composition_zero_line = alt.Chart({"values": [{"x": 0}]}).mark_rule().encode(x="x:Q")

st.altair_chart(
    composition_industry_chart + composition_zero_line,
    width="stretch",
)

st.caption(
    "2015年の全体平均賃金を基準にした産業別の構成寄与です。"
    "平均以上の賃金水準でシェアが上昇した産業、または"
    "平均未満の賃金水準でシェアが低下した産業はプラス方向に寄与します。"
)

tl_monthly_df = create_industry_monthly_dataframe(
    raw_df,
    industry_code="TL",
)

tl_yearly_df = create_industry_yearly_dataframe(
    tl_monthly_df,
)

comparison_yearly_df = reconstructed_df.merge(
    tl_yearly_df[
        [
            "year",
            "monthly_wage",
        ]
    ].rename(
        columns={
            "monthly_wage": "tl_monthly_wage",
        }
    ),
    on="year",
    how="inner",
    validate="one_to_one",
)

comparison_yearly_df = comparison_yearly_df[comparison_yearly_df["year"] >= 2010].copy()

comparison_chart_df = comparison_yearly_df[
    [
        "year",
        "reconstructed_wage",
        "tl_monthly_wage",
    ]
].melt(
    id_vars="year",
    var_name="series",
    value_name="monthly_wage",
)

comparison_chart_df["series_name"] = comparison_chart_df["series"].map(
    {
        "reconstructed_wage": "主要16産業の再構築平均",
        "tl_monthly_wage": "調査産業計（TL）",
    }
)

st.divider()

st.subheader("雇用シェア変化と産業構成寄与")

scatter_df = decomposition_df.copy()

scatter_df["industry_name"] = scatter_df["industry"].map(
    INDUSTRY_NAMES
)

scatter_df["share_change_pt"] = (
    scatter_df["share_change"] * 100
)

scatter_chart = (
    alt.Chart(scatter_df)
    .mark_circle(size=100)
    .encode(
        x=alt.X(
            "share_change_pt:Q",
            title="雇用シェア変化（pt）",
        ),
        y=alt.Y(
            "centered_composition_effect_pt:Q",
            title="産業構成寄与（pt）",
        ),
        tooltip=[
            alt.Tooltip(
                "industry_name:N",
                title="産業",
            ),
            alt.Tooltip(
                "share_change_pt:Q",
                title="シェア変化",
                format="+.2f",
            ),
            alt.Tooltip(
                "start_wage:Q",
                title="2015年賃金",
                format=",.0f",
            ),
            alt.Tooltip(
                "centered_composition_effect_pt:Q",
                title="構成寄与",
                format="+.3f",
            ),
        ],
    )
)

zero_x = alt.Chart(
    pd.DataFrame({"x": [0]})
).mark_rule().encode(
    x="x:Q"
)

zero_y = alt.Chart(
    pd.DataFrame({"y": [0]})
).mark_rule().encode(
    y="y:Q"
)

labels = (
    alt.Chart(scatter_df)
    .mark_text(
        align="left",
        dx=6,
        dy=-6,
    )
    .encode(
        x="share_change_pt:Q",
        y="centered_composition_effect_pt:Q",
        text="industry:N",
    )
)

st.altair_chart(
    scatter_chart + labels + zero_x + zero_y,
    width="stretch",
)

st.divider()

st.subheader("再構築平均賃金と調査産業計")

st.write(
    "妥当性確認：16産業の雇用シェアから再構築した平均賃金は、"
    "調査産業計との差が2015年で約2.8円、2025年で約4.8円であり、"
    "ほぼ一致しました。"
)

st.divider()

st.subheader("時期別にみた要因分解")

periods = [
    (2015, 2019),
    (2019, 2020),
    (2020, 2025),
]

period_rows = []

for start_year, end_year in periods:
    period_df = create_industry_composition_decomposition(
        base_df,
        start_year=start_year,
        end_year=end_year,
    )

    start_average_wage = (period_df["start_wage"] * period_df["start_share"]).sum()

    within_period = period_df["within_wage_effect"].sum()
    composition_period = period_df["composition_effect"].sum()
    interaction_period = period_df["interaction_effect"].sum()

    total_period = within_period + composition_period + interaction_period

    period_rows.append(
        {
            "期間": f"{start_year}→{end_year}",
            "平均賃金変化（%）": total_period / start_average_wage * 100,
            "産業内賃金効果（pt）": within_period / start_average_wage * 100,
            "産業構成効果（pt）": composition_period / start_average_wage * 100,
            "交差効果（pt）": interaction_period / start_average_wage * 100,
        }
    )

period_summary_df = pd.DataFrame(period_rows)

st.dataframe(
    period_summary_df.style.format(
        {
            "平均賃金変化（%）": "{:+.2f}",
            "産業内賃金効果（pt）": "{:+.2f}",
            "産業構成効果（pt）": "{:+.2f}",
            "交差効果（pt）": "{:+.2f}",
        }
    ),
    width="stretch",
    hide_index=True,
)

st.markdown(
    """
    - **2015→2019**：産業構成効果はマイナスで、平均賃金上昇を抑える方向に作用しました。
    - **2019→2020**：産業構成効果はほぼゼロで、平均賃金低下のほとんどは産業内賃金効果によるものでした。
    - **2020→2025**：産業構成効果はプラスに転じ、平均賃金をわずかに押し上げました。
    """
)

st.caption(
    "2015→2025全体で産業構成効果が小さいのは、"
    "産業構成がほとんど変化しなかったためではなく、"
    "前半の押し下げと後半の押し上げが相殺されたためです。"
)

st.markdown(
    """
    **2015→2025全体の産業構成効果は -0.21pt でした。**

    ただし、これは10年間を通じて産業構成効果が常に小さかったことを意味しません。

    - 2015→2019：**-0.50pt**
    - 2019→2020：**-0.01pt**
    - 2020→2025：**+0.29pt**

    前半の押し下げと後半の押し上げが一部相殺された結果、
    10年間全体では -0.21pt にとどまりました。
    """
)