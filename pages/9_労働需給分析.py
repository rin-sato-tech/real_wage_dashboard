import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.labor_market_analysis import (
    add_labor_market_regime,
    calculate_lag_correlations,
    calculate_regime_correlations,
)
from real_wage_dashboard.labor_market_service import (
    create_effective_job_openings_dataframe,
    create_labor_market_dataframe,
    create_new_job_openings_dataframe,
    create_unemployment_rate_dataframe,
    load_effective_job_openings_excel,
    load_new_job_openings_excel,
    load_unemployment_rate_excel,
)
from real_wage_dashboard.wage_service import (
    create_wage_dataframe,
    load_wage_csv,
)
from real_wage_dashboard.labor_market_analysis import (
    add_labor_market_regime,
    calculate_lag_correlations,
    calculate_quarterly_lag_correlations,
    calculate_regime_correlations,
    create_quarterly_wage_dataframe,
)

from real_wage_dashboard.labor_market_service import (
    add_tankan_tightness_columns,
    create_effective_job_openings_dataframe,
    create_labor_market_dataframe,
    create_new_job_openings_dataframe,
    create_tankan_employment_di_dataframe,
    create_unemployment_rate_dataframe,
    load_effective_job_openings_excel,
    load_new_job_openings_excel,
    load_tankan_employment_di_csv,
    load_unemployment_rate_excel,
)

st.set_page_config(
    page_title="労働需給分析",
    layout="wide",
)

st.title("労働需給と賃金分析")

st.caption("労働市場の逼迫と所定内給与の伸び率にどのような関係があるかを分析します。")

st.subheader("問い")

st.markdown(
    """
    **労働需給が逼迫した後、所定内給与の伸び率は高まるのか。**

    有効求人倍率、完全失業率、新規求人倍率を使って、労働市場の逼迫度と所定内給与前年比の関係を確認します。
    あわせて、労働需給指標が賃金上昇率に先行するか、またその関係が時期によって変化するかを分析します。
    """
)

st.subheader("分析条件")

st.markdown(
    """
    - **賃金データ**：毎月勤労統計調査
    - **賃金指標**：所定内給与前年比
    - **事業所規模**：5人以上
    - **就業形態**：就業形態計
    - **産業**：調査産業計
    - **労働需給指標**：有効求人倍率、完全失業率、新規求人倍率
    - **主分析期間**：2000年1月～2025年12月
    - **求人倍率・失業率**：季節調整値
    """
)

st.caption(
    "完全失業率は分析時に符号を反転し、"
    "すべての指標で値が大きいほど労働需給が逼迫する方向に統一します。"
)

with st.expander("用語・グラフの見方"):
    st.markdown(
        """
        #### 所定内給与

        基本給など、所定の労働時間に対して支払われる給与です。
        残業代や賞与の影響を受けにくいため、継続的な賃金水準の変化を見るために使用します。

        **所定内給与前年比**は、前年の同じ月と比べて所定内給与が何％増減したかを表します。

        ---

        #### 有効求人倍率

        求職者1人に対して、何件の求人があるかを表す指標です。

        - 1倍より高い：求職者より求人が多い
        - 値が高くなる：企業側の人材需要が相対的に強い
        - この分析では、値が高いほど「労働需給が逼迫している」と考えます

        **分かること**：
        求人と求職者のバランスからみた労働市場の需給状況。

        ---

        #### 新規求人倍率

        新しく受け付けられた求人と、新しく仕事を探し始めた求職者のバランスを表す指標です。
        有効求人倍率よりも、新しい求人の動きを反映するため、比較的短期的な労働需要を見る指標として利用します。

        **分かること**：
        最近の企業の採用需要が強まっているか、弱まっているか。

        ---

        #### 完全失業率

        労働力人口のうち、仕事がなく求職活動をしている人の割合です。

        通常は低いほど労働市場が逼迫していると考えられます。
        このページでは他の指標と方向を揃えるため、分析上は符号を反転しています。

        **分かること**：
        求職側からみた労働市場全体の余裕・逼迫状況。

        ---

        #### 相関係数

        2つの値がどの程度一緒に動くかを、-1～1の範囲で表した値です。

        - 1に近い：同じ方向に動きやすい
        - 0に近い：直線的な関係が弱い
        - -1に近い：反対方向に動きやすい

        **注意**：
        相関が高くても、一方がもう一方の原因だとは限りません。

        ---

        #### ラグ相関

        同じ月同士ではなく、「過去の労働需給」と「現在の賃金上昇率」を比較した相関です。
        例えば6か月ラグなら、**6か月前の労働需給指標 × 当月の所定内給与前年比**を比較します。

        **分かること**：
        労働需給の変化が賃金より先に動いているように見えるか。

        ただし、最大相関となるラグが
        そのまま企業の賃金決定に必要な時間を意味するわけではありません。

        ---

        #### 短観・雇用人員判断DI

        日本銀行の短観で、企業に従業員が「過剰」か「不足」かを尋ねた結果から作られる指標です。
        元のDIは「過剰 − 不足」なので、マイナスになるほど人手不足が強いことを意味します。

        このページでは符号を反転し、
        **値が大きいほど企業の人手不足感が強い**方向に統一しています。

        **分かること**：
        求人・失業統計とは別に、企業自身がどの程度人手不足を感じているか。
        """
    )

# ----------------------------
# データ読み込み
# ----------------------------

effective_raw_df = load_effective_job_openings_excel(
    "data/raw/labor_market/effective_job_openings_ratio.xlsx"
)
effective_df = create_effective_job_openings_dataframe(
    effective_raw_df
)

unemployment_raw_df = load_unemployment_rate_excel(
    "data/raw/labor_market/unemployment_rate.xlsx"
)
unemployment_df = create_unemployment_rate_dataframe(
    unemployment_raw_df
)

new_jobs_raw_df = load_new_job_openings_excel(
    "data/raw/labor_market/new_job_openings_ratio.xlsx"
)
new_jobs_df = create_new_job_openings_dataframe(
    new_jobs_raw_df
)

labor_market_df = create_labor_market_dataframe(
    effective_df,
    unemployment_df,
    new_jobs_df,
)


# ----------------------------
# 所定内給与前年比
# ----------------------------

raw_wage_df = load_wage_csv(
    WAGE_DATA_PATH
)

wage_df = create_wage_dataframe(
    raw_wage_df,
    wage_item="所定内給与",
    establishment_size="T",
    employment_type="0",
    industry_code="TL",
)

wage_df = wage_df.rename(
    columns={
        "nominal_wage_amount": "scheduled_cash_earnings",
    }
)

wage_df["scheduled_cash_earnings_yoy"] = (
    wage_df["scheduled_cash_earnings"]
    / wage_df["scheduled_cash_earnings"].shift(12)
    - 1
) * 100


# ----------------------------
# 分析用データ
# ----------------------------

full_analysis_df = (
    labor_market_df
    .merge(
        wage_df[
            [
                "date",
                "scheduled_cash_earnings",
                "scheduled_cash_earnings_yoy",
            ]
        ],
        on="date",
        how="inner",
        validate="one_to_one",
    )
    .sort_values("date")
    .reset_index(drop=True)
)

full_analysis_df["labor_market_tightness_effective_jobs"] = (
    full_analysis_df["effective_job_openings_ratio"]
)

full_analysis_df["labor_market_tightness_unemployment"] = (
    -full_analysis_df["unemployment_rate"]
)

full_analysis_df["labor_market_tightness_new_jobs"] = (
    full_analysis_df["new_job_openings_ratio"]
)

full_analysis_df = add_labor_market_regime(
    full_analysis_df
)

analysis_df = full_analysis_df.loc[
    full_analysis_df["date"].between(
        "2000-01-01",
        "2025-12-01",
    )
].copy()


# ----------------------------
# 基本集計
# ----------------------------

labor_market_columns = {
    "有効求人倍率": "labor_market_tightness_effective_jobs",
    "完全失業率": "labor_market_tightness_unemployment",
    "新規求人倍率": "labor_market_tightness_new_jobs",
}

correlation_rows = []

for indicator_name, column_name in labor_market_columns.items():
    correlation_rows.append(
        {
            "indicator": indicator_name,
            "correlation": analysis_df[column_name].corr(
                analysis_df["scheduled_cash_earnings_yoy"]
            ),
        }
    )

correlation_df = pd.DataFrame(
    correlation_rows
)

regime_correlation_df = calculate_regime_correlations(
    analysis_df,
    labor_market_columns,
)

effective_lag_df = calculate_lag_correlations(
    analysis_df,
    "labor_market_tightness_effective_jobs",
)

unemployment_lag_df = calculate_lag_correlations(
    analysis_df,
    "labor_market_tightness_unemployment",
)

new_jobs_lag_df = calculate_lag_correlations(
    analysis_df,
    "labor_market_tightness_new_jobs",
)


# ----------------------------
# 冒頭結果
# ----------------------------

st.subheader("主な結果")

st.markdown(
    """
    - 2000～2025年では、3つの労働需給指標すべてで所定内給与前年比との正の関連が確認されました。
    - ただし関係の強さは時期によって異なり、2013～2019年では比較的明確でした。
    - 2022年以降は求人倍率と賃金上昇率の同時点の関係が弱まり、過去とは異なる動きがみられます。
    - ラグ相関から固定的な「賃金反応期間」を特定することはできません。
    - 短観でも、企業の人手不足感が強いほど所定内給与前年比が高い傾向が確認されました。
    """
)

st.subheader("考察")

st.markdown(
    """
    労働需給の逼迫と所定内給与の上昇には関連がみられますが、その強さや時間差は経済局面によって変化しています。
    特に2022年以降の賃金上昇は、労働需給だけでは説明しにくく、物価上昇や賃金改定行動など他の要因も考慮する必要があります。
    """
)

st.warning(
    "本分析は時系列の相関分析であり、"
    "労働需給の逼迫が賃金上昇を直接引き起こしたことを示すものではありません。"
)

st.divider()

st.subheader("労働需給と所定内給与前年比の長期推移")

indicator_options = {
    "有効求人倍率": "labor_market_tightness_effective_jobs",
    "完全失業率（逼迫方向）": "labor_market_tightness_unemployment",
    "新規求人倍率": "labor_market_tightness_new_jobs",
}

selected_indicator = st.selectbox(
    "表示する労働需給指標",
    options=list(indicator_options.keys()),
)

selected_column = indicator_options[selected_indicator]

chart_df = analysis_df[
    [
        "date",
        selected_column,
        "scheduled_cash_earnings_yoy",
    ]
].copy()

labor_market_chart = (
    alt.Chart(chart_df)
    .mark_line(
        color="#2F6B9A",
        strokeWidth=2,
    )
    .encode(
        x=alt.X(
            "date:T",
            title=None,
        ),
        y=alt.Y(
            f"{selected_column}:Q",
            title=selected_indicator,
        ),
        tooltip=[
            alt.Tooltip(
                "date:T",
                title="年月",
                format="%Y-%m",
            ),
            alt.Tooltip(
                f"{selected_column}:Q",
                title=selected_indicator,
                format=".2f",
            ),
        ],
    )
)

wage_chart = (
    alt.Chart(chart_df)
    .mark_line(
        color="#C65D4B",
        strokeWidth=2,
    )
    .encode(
        x=alt.X(
            "date:T",
            title=None,
        ),
        y=alt.Y(
            "scheduled_cash_earnings_yoy:Q",
            title="所定内給与前年比（%）",
        ),
        tooltip=[
            alt.Tooltip(
                "date:T",
                title="年月",
                format="%Y-%m",
            ),
            alt.Tooltip(
                "scheduled_cash_earnings_yoy:Q",
                title="所定内給与前年比",
                format=".2f",
            ),
        ],
    )
)

combined_chart = alt.layer(
    labor_market_chart,
    wage_chart,
).resolve_scale(
    y="independent",
).properties(
    height=420,
)

st.caption(f"青：{selected_indicator}　／　赤：所定内給与前年比")

st.altair_chart(
    combined_chart,
    width="stretch",
)

st.caption(
    "労働需給指標と所定内給与前年比は単位・尺度が異なるため、"
    "左右で独立した縦軸を使用しています。"
)

if selected_indicator == "有効求人倍率":
    st.markdown(
        """
        有効求人倍率が高いほど、求職者に対して求人が多く、労働需給が逼迫していると解釈します。
        """
    )

elif selected_indicator == "完全失業率（逼迫方向）":
    st.markdown(
        """
        完全失業率は符号を反転して表示しています。
        そのため、値が高いほど失業率が低く、労働需給が逼迫している状態を表します。
        """
    )

else:
    st.markdown(
        """
        新規求人倍率は新しく出された求人と新規求職者の関係を表し、
        有効求人倍率より短期的な求人動向を反映します。
        """
    )

st.divider()

st.subheader("労働需給と所定内給与前年比の関係")

scatter_df = analysis_df[
    [
        selected_column,
        "scheduled_cash_earnings_yoy",
    ]
].dropna()

selected_correlation = scatter_df[
    selected_column
].corr(
    scatter_df["scheduled_cash_earnings_yoy"]
)

scatter_chart = (
    alt.Chart(scatter_df)
    .mark_circle(
        size=55,
        opacity=0.6,
    )
    .encode(
        x=alt.X(
            f"{selected_column}:Q",
            title=selected_indicator,
        ),
        y=alt.Y(
            "scheduled_cash_earnings_yoy:Q",
            title="所定内給与前年比（%）",
        ),
        tooltip=[
            alt.Tooltip(
                f"{selected_column}:Q",
                title=selected_indicator,
                format=".2f",
            ),
            alt.Tooltip(
                "scheduled_cash_earnings_yoy:Q",
                title="所定内給与前年比",
                format=".2f",
            ),
        ],
    )
    .properties(
        height=380,
    )
)

regression_line = (
    scatter_chart
    .transform_regression(
        selected_column,
        "scheduled_cash_earnings_yoy",
    )
    .mark_line()
)

st.altair_chart(
    scatter_chart + regression_line,
    width="stretch",
)

st.metric(
    "同時点相関",
    f"{selected_correlation:.3f}",
)

st.caption(
    "各点は1か月の観測値です。回帰線は変数間の線形な関係を視覚的に示すためのもので、"
    "因果関係を示すものではありません。"
)

st.divider()

st.subheader("同時点相関")

display_correlation_df = correlation_df.copy()
display_correlation_df["correlation"] = (
    display_correlation_df["correlation"]
    .round(3)
)

st.dataframe(
    display_correlation_df,
    width="stretch",
    hide_index=True,
)

st.divider()

st.subheader("労働需給指標のラグ相関")

lag_comparison_df = pd.concat(
    [
        effective_lag_df.assign(
            indicator="有効求人倍率"
        ),
        unemployment_lag_df.assign(
            indicator="完全失業率"
        ),
        new_jobs_lag_df.assign(
            indicator="新規求人倍率"
        ),
    ],
    ignore_index=True,
)

lag_chart = (
    alt.Chart(lag_comparison_df)
    .mark_line(
        point=True,
    )
    .encode(
        x=alt.X(
            "lag_months:Q",
            title="労働需給指標の先行ラグ（月）",
            scale=alt.Scale(
                domain=[0, 12],
            ),
        ),
        y=alt.Y(
            "correlation:Q",
            title="所定内給与前年比との相関係数",
        ),
        color=alt.Color(
            "indicator:N",
            title="労働需給指標",
        ),
        tooltip=[
            alt.Tooltip(
                "indicator:N",
                title="指標",
            ),
            alt.Tooltip(
                "lag_months:Q",
                title="先行ラグ",
                format=".0f",
            ),
            alt.Tooltip(
                "correlation:Q",
                title="相関係数",
                format=".3f",
            ),
            alt.Tooltip(
                "observation_count:Q",
                title="観測数",
                format=".0f",
            ),
        ],
    )
    .properties(
        height=400,
    )
)

st.altair_chart(
    lag_chart,
    width="stretch",
)

st.caption(
    "ラグ0は同時点、ラグ6は6か月前の労働需給指標と"
    "当月の所定内給与前年比との相関を表します。"
)

max_lag_rows = []

for indicator_name, lag_df in [
    (
        "有効求人倍率",
        effective_lag_df,
    ),
    (
        "完全失業率",
        unemployment_lag_df,
    ),
    (
        "新規求人倍率",
        new_jobs_lag_df,
    ),
]:
    max_row = lag_df.loc[
        lag_df["correlation"].idxmax()
    ]

    max_lag_rows.append(
        {
            "indicator": indicator_name,
            "max_correlation": max_row[
                "correlation"
            ],
            "lag_months": int(
                max_row["lag_months"]
            ),
        }
    )

max_lag_df = pd.DataFrame(max_lag_rows)

display_max_lag_df = max_lag_df.copy()

display_max_lag_df["max_correlation"] = (
    display_max_lag_df["max_correlation"]
    .round(3)
)

display_max_lag_df = display_max_lag_df.rename(
    columns={
        "indicator": "指標",
        "max_correlation": "最大相関",
        "lag_months": "最大ラグ（月）",
    }
)

st.dataframe(
    display_max_lag_df,
    width="stretch",
    hide_index=True,
)

st.markdown(
    """
    **読み取り**

    - 有効求人倍率は1年前後、新規求人倍率は半年～1年前後で相関がやや高くなります。
    - 完全失業率は比較的短いラグで相関が高くなります。
    - ただし、同時点から最大相関までの差は大きくありません。
    - 最大ラグは局面やデータ変換によって変化するため、「この月数後に賃金が上がる」とは解釈できません。
    """
)

st.warning(
    "最大相関ラグは参考値です。近接するラグでも相関は大きく変わらず、"
    "局面やデータ変換によって最大値の位置も変化します。"
)

st.divider()

st.subheader("局面別にみた労働需給と賃金の関係")

regime_display_df = regime_correlation_df.copy()

regime_display_df["correlation"] = (
    regime_display_df["correlation"]
    .round(3)
)

regime_order = [
    "2000年代～震災後",
    "雇用改善期",
    "コロナ期",
    "物価上昇・賃上げ期",
]

regime_display_df["regime"] = pd.Categorical(
    regime_display_df["regime"],
    categories=regime_order,
    ordered=True,
)

regime_display_df = regime_display_df.sort_values(
    [
        "regime",
        "indicator",
    ]
)

regime_chart = (
    alt.Chart(regime_display_df)
    .mark_bar()
    .encode(
        x=alt.X(
            "regime:N",
            title=None,
            sort=regime_order,
            axis=alt.Axis(
                labelAngle=0,
            ),
        ),
        y=alt.Y(
            "correlation:Q",
            title="所定内給与前年比との相関係数",
        ),
        xOffset=alt.XOffset(
            "indicator:N",
        ),
        color=alt.Color(
            "indicator:N",
            title="労働需給指標",
        ),
        tooltip=[
            alt.Tooltip(
                "regime:N",
                title="局面",
            ),
            alt.Tooltip(
                "indicator:N",
                title="指標",
            ),
            alt.Tooltip(
                "correlation:Q",
                title="相関係数",
                format=".3f",
            ),
            alt.Tooltip(
                "observation_count:Q",
                title="観測数",
                format=".0f",
            ),
        ],
    )
    .properties(
        height=400,
    )
)

zero_line = (
    alt.Chart(
        {
            "values": [
                {
                    "y": 0,
                }
            ]
        }
    )
    .mark_rule()
    .encode(
        y="y:Q",
    )
)

st.altair_chart(
    regime_chart + zero_line,
    width="stretch",
)
regime_table_df = (
    regime_display_df[
        [
            "regime",
            "indicator",
            "correlation",
            "observation_count",
        ]
    ]
    .rename(
        columns={
            "regime": "局面",
            "indicator": "指標",
            "correlation": "相関係数",
            "observation_count": "観測数",
        }
    )
)

with st.expander("局面別の相関係数を表で確認"):
    st.dataframe(
        regime_table_df,
        width="stretch",
        hide_index=True,
    )

st.markdown(
    """
    **読み取り**

    - **2000年代～震災後**：3指標とも相関は弱く、労働需給と賃金上昇率の関係は明確ではありません。
    - **雇用改善期**：3指標すべてで0.5前後の正の相関があり、比較的明確な関係が確認されます。
    - **コロナ期**：正の相関はみられるものの、24か月と観測数が少なく、特殊な経済ショックを含むため参考値です。
    - **物価上昇・賃上げ期**：有効求人倍率・新規求人倍率では同時点相関が負となり、過去とは異なる動きがみられます。
    """
)

st.caption(
    "局面区分は経済状況の違いを比較するための分析上の区分です。"
    "特定の政策や出来事だけで局面の特徴を説明するものではありません。"
)

# ----------------------------
# 短観
# ----------------------------

raw_tankan_df = load_tankan_employment_di_csv(
    "data/raw/labor_market/tankan_employment_di.csv"
)

tankan_df = create_tankan_employment_di_dataframe(
    raw_tankan_df
)

tankan_df = add_tankan_tightness_columns(
    tankan_df
)

quarterly_wage_df = create_quarterly_wage_dataframe(
    analysis_df
)

tankan_analysis_df = tankan_df.loc[
    tankan_df["date"].between(
        "2000-03-01",
        "2025-12-01",
    )
].copy()

tankan_wage_df = (
    tankan_analysis_df
    .merge(
        quarterly_wage_df,
        on="date",
        how="inner",
        validate="one_to_one",
    )
    .sort_values("date")
    .reset_index(drop=True)
)

tankan_columns = {
    "大企業": "large_enterprise_tightness",
    "中堅企業": "medium_enterprise_tightness",
    "中小企業": "small_enterprise_tightness",
}

tankan_lag_frames = []

for enterprise_size, column_name in tankan_columns.items():
    lag_df = calculate_quarterly_lag_correlations(
        tankan_wage_df,
        column_name,
    )

    lag_df["enterprise_size"] = enterprise_size

    tankan_lag_frames.append(
        lag_df
    )

tankan_lag_df = pd.concat(
    tankan_lag_frames,
    ignore_index=True,
)

st.divider()

st.subheader("企業の人手不足感と賃金")

st.markdown(
    """
    日本銀行「短観」の雇用人員判断DIを使って、
    企業が感じている人手不足感と所定内給与前年比の関係を確認します。

    雇用人員判断DIは「過剰－不足」で公表されるため、
    ここでは符号を反転し、**値が大きいほど人手不足感が強い**
    方向に統一しています。
    """
)

tankan_correlation_rows = []

for enterprise_size, column_name in tankan_columns.items():
    correlation = tankan_wage_df[
        column_name
    ].corr(
        tankan_wage_df[
            "scheduled_cash_earnings_yoy"
        ]
    )

    tankan_correlation_rows.append(
        {
            "企業規模": enterprise_size,
            "同時点相関": correlation,
        }
    )

tankan_correlation_df = pd.DataFrame(
    tankan_correlation_rows
)

tankan_correlation_df["同時点相関"] = (
    tankan_correlation_df["同時点相関"]
    .round(3)
)

st.dataframe(
    tankan_correlation_df,
    width="stretch",
    hide_index=True,
)

tankan_lag_chart = (
    alt.Chart(tankan_lag_df)
    .mark_line(
        point=True,
    )
    .encode(
        x=alt.X(
            "lag_quarters:Q",
            title="短観の先行ラグ（四半期）",
            scale=alt.Scale(
                domain=[0, 4],
            ),
        ),
        y=alt.Y(
            "correlation:Q",
            title="所定内給与前年比との相関係数",
        ),
        color=alt.Color(
            "enterprise_size:N",
            title="企業規模",
        ),
        tooltip=[
            alt.Tooltip(
                "enterprise_size:N",
                title="企業規模",
            ),
            alt.Tooltip(
                "lag_quarters:Q",
                title="先行ラグ",
                format=".0f",
            ),
            alt.Tooltip(
                "lag_months:Q",
                title="換算月数",
                format=".0f",
            ),
            alt.Tooltip(
                "correlation:Q",
                title="相関係数",
                format=".3f",
            ),
        ],
    )
    .properties(
        height=400,
    )
)

st.altair_chart(
    tankan_lag_chart,
    width="stretch",
)

tankan_max_rows = []

for enterprise_size in tankan_columns:
    target_df = tankan_lag_df[
        tankan_lag_df["enterprise_size"]
        == enterprise_size
    ]

    max_row = target_df.loc[
        target_df["correlation"].idxmax()
    ]

    tankan_max_rows.append(
        {
            "企業規模": enterprise_size,
            "最大相関": max_row["correlation"],
            "最大ラグ（四半期）": int(
                max_row["lag_quarters"]
            ),
            "最大ラグ（月）": int(
                max_row["lag_months"]
            ),
        }
    )

tankan_max_df = pd.DataFrame(
    tankan_max_rows
)

tankan_max_df["最大相関"] = (
    tankan_max_df["最大相関"]
    .round(3)
)

st.dataframe(
    tankan_max_df,
    width="stretch",
    hide_index=True,
)
st.markdown(
    """
    **読み取り**

    - 大企業・中堅企業・中小企業のすべてで、企業の人手不足感と所定内給与前年比に正の相関があります。
    - 3系列とも1四半期（3か月）先行時に相関が最大になります。
    - ただし、同時点から2四半期先行までの相関差は小さく、
      3か月というラグだけが特別に強いわけではありません。
    - 企業の人手不足感と賃金上昇率は、比較的近い時期に連動していると解釈できます。
    """
)

st.caption(
    "短観は四半期統計のため、毎月勤労統計の所定内給与前年比を"
    "四半期平均に変換して比較しています。"
)

st.divider()

st.subheader("分析データ")

display_df = analysis_df[
    [
        "date",
        "scheduled_cash_earnings",
        "scheduled_cash_earnings_yoy",
        "effective_job_openings_ratio",
        "unemployment_rate",
        "new_job_openings_ratio",
    ]
].copy()

display_df = display_df.rename(
    columns={
        "date": "年月",
        "scheduled_cash_earnings": "所定内給与",
        "scheduled_cash_earnings_yoy": "所定内給与前年比",
        "effective_job_openings_ratio": "有効求人倍率",
        "unemployment_rate": "完全失業率",
        "new_job_openings_ratio": "新規求人倍率",
    }
)

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
)

csv_data = display_df.to_csv(
    index=False,
).encode("utf-8-sig")

st.download_button(
    label="分析データをCSVでダウンロード",
    data=csv_data,
    file_name="labor_market_analysis.csv",
    mime="text/csv",
)
