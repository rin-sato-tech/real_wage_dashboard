from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.take_home_export import (
    create_japanese_tableau_export,
    create_take_home_tableau_export,
)
from real_wage_dashboard.take_home_scenario import (
    calculate_take_home_scenario,
)
from real_wage_dashboard.take_home_service import (
    load_take_home_rule_tables,
)

SNAPSHOT_PATH = Path("data/snapshots/take_home_main_series.csv")

START_YEAR = 1990
END_YEAR = 2025


st.set_page_config(
    page_title="手取り賃金分析",
    page_icon="💴",
    layout="wide",
)


@st.cache_data
def load_take_home_data() -> pd.DataFrame:
    """保存済みの手取り主系列を読み込む。"""

    if not SNAPSHOT_PATH.exists():
        raise FileNotFoundError(
            f"手取り分析のスナップショットがありません: {SNAPSHOT_PATH}"
        )

    df = pd.read_csv(SNAPSHOT_PATH)

    required_columns = {
        "year",
        "gross_salary_yen",
        "nominal_take_home_yen",
        "real_gross_salary_yen",
        "real_take_home_yen",
        "gross_salary_index",
        "nominal_take_home_index",
        "real_gross_salary_index",
        "real_take_home_index",
        "effective_burden_rate",
        "income_tax_rate",
        "resident_tax_rate",
        "pension_rate_effective",
        "health_insurance_rate_effective",
        "employment_insurance_rate_effective",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"手取り主系列に必要な列がありません: {sorted(missing)}")

    df["year"] = pd.to_numeric(
        df["year"],
        errors="raise",
    ).astype(int)

    return df.sort_values("year").reset_index(drop=True)


@st.cache_data
def load_snapshot(
    filename: str,
) -> pd.DataFrame:
    """data/snapshots 配下のCSVを読み込む。"""

    path = Path("data/snapshots") / filename

    if not path.exists():
        raise FileNotFoundError(f"分析結果がありません: {path}")

    return pd.read_csv(path)


def get_year_row(
    df: pd.DataFrame,
    year: int,
) -> pd.Series:
    """指定年の行を一意に取得する。"""

    selected = df.loc[df["year"] == year]

    if len(selected) != 1:
        raise ValueError(f"{year}年のデータを一意に取得できません。")

    return selected.iloc[0]


def calculate_change_pct(
    start_value: float,
    end_value: float,
) -> float:
    """開始値から終了値への変化率を計算する。"""

    if start_value == 0:
        raise ValueError("変化率の開始値は0以外である必要があります。")

    return (end_value / start_value - 1) * 100


@st.cache_resource
def load_rule_tables():
    """税・社会保険制度表を読み込む。"""

    return load_take_home_rule_tables()


def create_reference_wage_df(
    main_df: pd.DataFrame,
) -> pd.DataFrame:
    """主系列からシナリオ計算用の年平均賃金を再構成する。"""

    required_columns = {
        "year",
        "monthly_total_cash_earnings_yen",
        "monthly_regular_earnings_yen",
        "monthly_special_earnings_yen",
    }

    missing = (
        required_columns
        - set(main_df.columns)
    )

    if missing:
        raise ValueError(
            "シナリオ計算に必要な賃金列がありません: "
            f"{sorted(missing)}"
        )

    return (
        main_df[
            [
                "year",
                "monthly_total_cash_earnings_yen",
                "monthly_regular_earnings_yen",
                "monthly_special_earnings_yen",
            ]
        ]
        .rename(
            columns={
                "monthly_total_cash_earnings_yen":
                    "total_cash_earnings",
                "monthly_regular_earnings_yen":
                    "regular_earnings",
                "monthly_special_earnings_yen":
                    "special_earnings",
            }
        )
        .copy()
    )


def create_index_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """1990年=100の4系列を比較する。"""

    chart_df = df[
        [
            "year",
            "gross_salary_index",
            "nominal_take_home_index",
            "real_gross_salary_index",
            "real_take_home_index",
        ]
    ].melt(
        id_vars="year",
        var_name="metric",
        value_name="index",
    )

    labels = {
        "gross_salary_index": "名目額面賃金",
        "nominal_take_home_index": "名目手取り",
        "real_gross_salary_index": "実質額面賃金",
        "real_take_home_index": "実質手取り",
    }

    chart_df["metric"] = chart_df["metric"].map(labels)

    lines = (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "year:Q",
                title="年",
                axis=alt.Axis(
                    format="d",
                ),
            ),
            y=alt.Y(
                "index:Q",
                title=(f"指数（{START_YEAR}年=100）"),
                scale=alt.Scale(
                    zero=False,
                ),
            ),
            color=alt.Color(
                "metric:N",
                title="指標",
                sort=[
                    "名目額面賃金",
                    "名目手取り",
                    "実質額面賃金",
                    "実質手取り",
                ],
            ),
            tooltip=[
                alt.Tooltip(
                    "year:Q",
                    title="年",
                    format="d",
                ),
                alt.Tooltip(
                    "metric:N",
                    title="指標",
                ),
                alt.Tooltip(
                    "index:Q",
                    title="指数",
                    format=".1f",
                ),
            ],
        )
    )

    base_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "index": [
                        100.0,
                    ]
                }
            )
        )
        .mark_rule(
            strokeDash=[
                5,
                5,
            ],
        )
        .encode(
            y="index:Q",
        )
    )

    return (
        (lines + base_line)
        .properties(
            height=430,
        )
        .interactive()
    )


def create_burden_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """税・社会保険料の実効負担率を積み上げ表示する。"""

    component_labels = {
        "income_tax_rate": "所得税",
        "resident_tax_rate": "住民税",
        "pension_rate_effective": "厚生年金",
        "health_insurance_rate_effective": "健康保険",
        "employment_insurance_rate_effective": "雇用保険",
    }

    chart_df = df[
        [
            "year",
            *component_labels.keys(),
        ]
    ].copy()

    for column in component_labels.keys():
        chart_df[column] = chart_df[column] * 100

    long_df = chart_df.melt(
        id_vars="year",
        var_name="component",
        value_name="burden_pct",
    )

    long_df["component"] = long_df["component"].map(component_labels)

    total_df = df[
        [
            "year",
            "effective_burden_rate",
        ]
    ].copy()

    total_df["total_burden_pct"] = total_df["effective_burden_rate"] * 100

    area = (
        alt.Chart(long_df)
        .mark_area(
            opacity=0.8,
        )
        .encode(
            x=alt.X(
                "year:Q",
                title="年",
                axis=alt.Axis(
                    format="d",
                ),
            ),
            y=alt.Y(
                "burden_pct:Q",
                title=("額面賃金に対する負担率（%）"),
                stack="zero",
            ),
            color=alt.Color(
                "component:N",
                title="負担項目",
                sort=[
                    "所得税",
                    "住民税",
                    "厚生年金",
                    "健康保険",
                    "雇用保険",
                ],
            ),
            tooltip=[
                alt.Tooltip(
                    "year:Q",
                    title="年",
                    format="d",
                ),
                alt.Tooltip(
                    "component:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "burden_pct:Q",
                    title="負担率",
                    format=".2f",
                ),
            ],
        )
    )

    total_line = (
        alt.Chart(total_df)
        .mark_line(
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "year:Q",
                axis=alt.Axis(
                    format="d",
                ),
            ),
            y=alt.Y(
                "total_burden_pct:Q",
            ),
            tooltip=[
                alt.Tooltip(
                    "year:Q",
                    title="年",
                    format="d",
                ),
                alt.Tooltip(
                    "total_burden_pct:Q",
                    title="合計負担率",
                    format=".2f",
                ),
            ],
        )
    )

    return (
        (area + total_line)
        .properties(
            height=430,
        )
        .interactive()
    )


def create_hundred_yen_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """額面100円あたりの手取り・負担内訳を表示する。"""

    selected_years = [
        1990,
        2000,
        2010,
        2015,
        2020,
        2025,
    ]

    component_labels = {
        "income_tax_yen": "所得税",
        "resident_tax_yen": "住民税",
        "pension_yen": "厚生年金",
        "health_insurance_yen": "健康保険",
        "employment_insurance_yen": "雇用保険",
        "nominal_take_home_yen": "手取り",
    }

    selected = df.loc[df["year"].isin(selected_years)].copy()

    rows = []

    for _, row in selected.iterrows():
        gross = float(row["gross_salary_yen"])

        for column, label in component_labels.items():
            rows.append(
                {
                    "year": str(int(row["year"])),
                    "component": label,
                    "yen_per_100": (float(row[column]) / gross * 100),
                }
            )

    chart_df = pd.DataFrame(rows)

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "year:N",
                title="年",
                sort=[str(year) for year in selected_years],
            ),
            y=alt.Y(
                "yen_per_100:Q",
                title="額面100円あたり（円）",
                stack="zero",
            ),
            color=alt.Color(
                "component:N",
                title="配分",
                sort=[
                    "手取り",
                    "所得税",
                    "住民税",
                    "厚生年金",
                    "健康保険",
                    "雇用保険",
                ],
            ),
            tooltip=[
                alt.Tooltip(
                    "year:N",
                    title="年",
                ),
                alt.Tooltip(
                    "component:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "yen_per_100:Q",
                    title="額面100円あたり",
                    format=".2f",
                ),
            ],
        )
        .properties(
            height=430,
        )
    )


def create_period_decomposition_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """実質手取りの期間別対数分解を表示する。"""

    factor_labels = {
        "wage_log_contribution_pt": "額面賃金",
        "burden_log_contribution_pt": "負担率",
        "price_log_contribution_pt": "物価",
    }

    chart_df = df[
        [
            "period",
            *factor_labels.keys(),
        ]
    ].melt(
        id_vars="period",
        var_name="factor",
        value_name="contribution",
    )

    chart_df["factor"] = chart_df["factor"].map(factor_labels)

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "period:N",
                title="期間",
                sort=None,
            ),
            y=alt.Y(
                "contribution:Q",
                title="対数変化への寄与（pt）",
            ),
            color=alt.Color(
                "factor:N",
                title="要因",
            ),
            tooltip=[
                alt.Tooltip(
                    "period:N",
                    title="期間",
                ),
                alt.Tooltip(
                    "factor:N",
                    title="要因",
                ),
                alt.Tooltip(
                    "contribution:Q",
                    title="寄与",
                    format="+.2f",
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "y": [0.0],
                }
            )
        )
        .mark_rule(
            strokeDash=[4, 4],
        )
        .encode(
            y="y:Q",
        )
    )

    return (bars + zero_line).properties(
        height=430,
    )


def create_real_shapley_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """実質手取り変化の4要因Shapley分解を表示する。"""

    factor_labels = {
        "wage_effect_pct_of_start": "額面賃金",
        "tax_policy_effect_pct_of_start": "税制度",
        "social_insurance_policy_effect_pct_of_start": "社会保険制度",
        "price_effect_pct_of_start": "物価",
    }

    chart_df = df[
        [
            "period",
            *factor_labels.keys(),
        ]
    ].melt(
        id_vars="period",
        var_name="factor",
        value_name="effect_pct",
    )

    chart_df["factor"] = chart_df["factor"].map(factor_labels)

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "period:N",
                title="期間",
                sort=None,
            ),
            y=alt.Y(
                "effect_pct:Q",
                title="開始年実質手取り比（%）",
            ),
            color=alt.Color(
                "factor:N",
                title="要因",
            ),
            tooltip=[
                alt.Tooltip(
                    "period:N",
                    title="期間",
                ),
                alt.Tooltip(
                    "factor:N",
                    title="要因",
                ),
                alt.Tooltip(
                    "effect_pct:Q",
                    title="寄与",
                    format="+.2f",
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "y": [0.0],
                }
            )
        )
        .mark_rule(
            strokeDash=[4, 4],
        )
        .encode(
            y="y:Q",
        )
    )

    return (bars + zero_line).properties(
        height=430,
    )


def create_fixed_policy_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """実際制度と1990年固定制度の名目手取りを比較する。"""

    chart_df = df[
        [
            "year",
            "actual_nominal_take_home_yen",
            "fixed_1990_nominal_take_home_yen",
        ]
    ].copy()

    chart_df["actual_nominal_take_home_man_yen"] = (
        chart_df["actual_nominal_take_home_yen"] / 10_000
    )

    chart_df["fixed_1990_nominal_take_home_man_yen"] = (
        chart_df["fixed_1990_nominal_take_home_yen"] / 10_000
    )

    chart_df = chart_df[
        [
            "year",
            "actual_nominal_take_home_man_yen",
            "fixed_1990_nominal_take_home_man_yen",
        ]
    ].melt(
        id_vars="year",
        var_name="scenario",
        value_name="take_home_man_yen",
    )

    chart_df["scenario"] = chart_df["scenario"].replace(
        {
            "actual_nominal_take_home_man_yen": "実際の制度",
            "fixed_1990_nominal_take_home_man_yen": "1990年制度固定",
        }
    )

    return (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "year:Q",
                title="年",
                axis=alt.Axis(
                    format="d",
                ),
            ),
            y=alt.Y(
                "take_home_man_yen:Q",
                title="年間名目手取り（万円）",
                scale=alt.Scale(
                    zero=False,
                ),
            ),
            color=alt.Color(
                "scenario:N",
                title="制度",
                sort=[
                    "実際の制度",
                    "1990年制度固定",
                ],
            ),
            tooltip=[
                alt.Tooltip(
                    "year:Q",
                    title="年",
                    format="d",
                ),
                alt.Tooltip(
                    "scenario:N",
                    title="制度",
                ),
                alt.Tooltip(
                    "take_home_man_yen:Q",
                    title="名目手取り（万円）",
                    format=".1f",
                ),
            ],
        )
        .properties(
            height=430,
        )
        .interactive()
    )


def create_scenario_allocation_chart(
    scenario: pd.Series,
) -> alt.Chart:
    """指定シナリオの額面100円あたり配分を表示する。"""

    gross = float(
        scenario["gross_salary_yen"]
    )

    components = {
        "手取り":
            float(
                scenario[
                    "nominal_take_home_yen"
                ]
            ),
        "所得税":
            float(
                scenario[
                    "income_tax_yen"
                ]
            ),
        "住民税":
            float(
                scenario[
                    "resident_tax_yen"
                ]
            ),
        "厚生年金":
            float(
                scenario[
                    "pension_yen"
                ]
            ),
        "健康保険":
            float(
                scenario[
                    "health_insurance_yen"
                ]
            ),
        "介護保険":
            float(
                scenario[
                    "long_term_care_yen"
                ]
            ),
        "雇用保険":
            float(
                scenario[
                    "employment_insurance_yen"
                ]
            ),
    }

    chart_df = pd.DataFrame(
        {
            "component":
                list(
                    components.keys()
                ),
            "yen_per_100": [
                value
                / gross
                * 100
                for value
                in components.values()
            ],
            "group": [
                "配分"
            ] * len(
                components
            ),
        }
    )

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "yen_per_100:Q",
                title="額面100円あたり（円）",
                stack="zero",
            ),
            y=alt.Y(
                "group:N",
                title=None,
                axis=None,
            ),
            color=alt.Color(
                "component:N",
                title="配分",
            ),
            tooltip=[
                alt.Tooltip(
                    "component:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "yen_per_100:Q",
                    title="100円あたり",
                    format=".2f",
                ),
            ],
        )
        .properties(
            height=100,
        )
    )


# ============================================
# データ読み込み
# ============================================

try:
    main_df = load_take_home_data()

    start = get_year_row(
        main_df,
        START_YEAR,
    )

    end = get_year_row(
        main_df,
        END_YEAR,
    )

except (
    FileNotFoundError,
    ValueError,
) as exc:
    st.error(str(exc))
    st.stop()


try:
    period_log_df = load_snapshot("take_home_period_log_decomposition.csv")

    burden_change_df = load_snapshot("take_home_burden_change_summary.csv")

    burden_shapley_df = load_snapshot("take_home_burden_shapley_3factor.csv")

    real_shapley_df = load_snapshot("take_home_real_shapley_4factor.csv")

    fixed_policy_df = load_snapshot("take_home_fixed_policy_comparison.csv")

    robustness_df = load_snapshot("take_home_robustness_summary.csv")

except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()


try:
    reference_wage_df = (
        create_reference_wage_df(
            main_df
        )
    )

    rule_tables = (
        load_rule_tables()
    )

except ValueError as exc:
    st.error(
        str(exc)
    )
    st.stop()


# ============================================
# ヘッダー
# ============================================

st.title("💴 手取り賃金・実質手取り賃金分析")

st.caption("1990～2025年｜35歳男性・単身・扶養なしの標準労働者モデル")

st.info(
    "毎月勤労統計の平均賃金水準に、"
    "各年の所得税・住民税・社会保険制度を"
    "適用した標準労働者モデルです。"
    "日本の労働者の平均的な実手取り額を"
    "直接推計したものではありません。"
)


# ============================================
# 手取りシミュレーター
# ============================================

st.header(
    "手取りシミュレーター"
)

st.caption(
    "対象年・年齢・年収を変更して、"
    "その条件での税・社会保険料と"
    "名目手取りを試算できます。"
)

sim_col1, sim_col2, sim_col3 = (
    st.columns(3)
)

with sim_col1:
    scenario_year = st.selectbox(
        "対象年",
        options=list(
            range(
                START_YEAR,
                END_YEAR + 1,
            )
        ),
        index=(
            END_YEAR
            - START_YEAR
        ),
    )

with sim_col2:
    scenario_age = st.slider(
        "年齢",
        min_value=20,
        max_value=64,
        value=35,
        step=1,
    )

with sim_col3:
    scenario_salary_man = (
        st.number_input(
            "年収（万円）",
            min_value=200,
            max_value=1_500,
            value=500,
            step=10,
        )
    )

scenario_salary_yen = (
    float(
        scenario_salary_man
    )
    * 10_000
)

try:
    scenario = (
        calculate_take_home_scenario(
            reference_wage_df=(
                reference_wage_df
            ),
            rule_tables=rule_tables,
            year=int(
                scenario_year
            ),
            annual_salary_yen=(
                scenario_salary_yen
            ),
            age=int(
                scenario_age
            ),
            sex="male",
        )
    )

except ValueError as exc:
    st.error(
        str(exc)
    )
    st.stop()

result_col1, result_col2, result_col3, result_col4 = (
    st.columns(4)
)

with result_col1:
    st.metric(
        "額面年収",
        (
            f"{scenario['gross_salary_yen'] / 10_000:,.1f}"
            "万円"
        ),
    )

with result_col2:
    st.metric(
        "名目手取り",
        (
            f"{scenario['nominal_take_home_yen'] / 10_000:,.1f}"
            "万円"
        ),
    )

with result_col3:
    st.metric(
        "実効負担率",
        (
            f"{scenario['effective_burden_rate'] * 100:.2f}%"
        ),
    )

with result_col4:
    st.metric(
        "手取り率",
        (
            f"{scenario['take_home_rate'] * 100:.2f}%"
        ),
    )

st.altair_chart(
    create_scenario_allocation_chart(
        scenario
    ),
    width="stretch",
)

with st.expander(
    "税・社会保険料の内訳を見る"
):
    scenario_detail = pd.DataFrame(
        {
            "項目": [
                "所得税",
                "住民税",
                "厚生年金",
                "健康保険",
                "介護保険",
                "雇用保険",
                "控除総額",
                "名目手取り",
            ],
            "年間金額（円）": [
                scenario[
                    "income_tax_yen"
                ],
                scenario[
                    "resident_tax_yen"
                ],
                scenario[
                    "pension_yen"
                ],
                scenario[
                    "health_insurance_yen"
                ],
                scenario[
                    "long_term_care_yen"
                ],
                scenario[
                    "employment_insurance_yen"
                ],
                scenario[
                    "total_deductions_yen"
                ],
                scenario[
                    "nominal_take_home_yen"
                ],
            ],
        }
    )

    st.dataframe(
        scenario_detail,
        width="stretch",
        hide_index=True,
        column_config={
            "年間金額（円）":
                st.column_config.NumberColumn(
                    format="%,.0f",
                ),
        },
    )

monthly_regular = float(
    scenario[
        "monthly_regular_earnings_yen"
    ]
)

annual_bonus = (
    float(
        scenario[
            "monthly_special_earnings_yen"
        ]
    )
    * 12
)

st.caption(
    f"{scenario_year}年の毎月勤労統計における"
    "月例賃金・特別給与の構成比を維持して試算。"
    f"設定上の月例賃金は約"
    f"{monthly_regular / 10_000:,.1f}万円/月、"
    f"年間賞与相当額は約"
    f"{annual_bonus / 10_000:,.1f}万円です。"
)

if 40 <= scenario_age <= 64:
    st.caption(
        "40～64歳のため、"
        "介護保険第2号被保険者として"
        "介護保険料を含めています。"
    )

st.warning(
    "このシミュレーターは単身・扶養なし・給与所得のみ等の"
    "標準化した条件による概算です。"
    "実際の手取り額は勤務先、加入する健康保険、"
    "各種控除、自治体等によって異なります。"
)

st.divider()


# ============================================
# KPI
# ============================================

gross_change = calculate_change_pct(
    start["gross_salary_yen"],
    end["gross_salary_yen"],
)

nominal_take_home_change = calculate_change_pct(
    start["nominal_take_home_yen"],
    end["nominal_take_home_yen"],
)

real_take_home_change = calculate_change_pct(
    start["real_take_home_yen"],
    end["real_take_home_yen"],
)

burden_change_pt = (end["effective_burden_rate"] - start["effective_burden_rate"]) * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="2025年 額面賃金",
        value=(f"{end['gross_salary_yen'] / 10_000:,.1f}万円"),
        delta=(f"{gross_change:+.2f}% （1990年比）"),
    )

with col2:
    st.metric(
        label="2025年 名目手取り",
        value=(f"{end['nominal_take_home_yen'] / 10_000:,.1f}万円"),
        delta=(f"{nominal_take_home_change:+.2f}% （1990年比）"),
    )

with col3:
    st.metric(
        label="2025年 実質手取り",
        value=(f"{end['real_take_home_yen'] / 10_000:,.1f}万円"),
        delta=(f"{real_take_home_change:+.2f}% （1990年比）"),
    )

with col4:
    st.metric(
        label="2025年 実効負担率",
        value=(f"{end['effective_burden_rate'] * 100:.2f}%"),
        delta=(f"{burden_change_pt:+.2f}pt （1990年比）"),
        delta_color="inverse",
    )


st.divider()


# ============================================
# 1. 長期推移
# ============================================

st.header("1. 額面賃金と手取りの長期推移")

st.altair_chart(
    create_index_chart(main_df),
    width="stretch",
)

st.caption(
    "1990年=100。実質額面賃金・実質手取りは「持家の帰属家賃を除く総合」CPIで物価調整。"
)

with st.expander("主要年の数値を見る"):
    selected = main_df.loc[
        main_df["year"].isin(
            [
                1990,
                2000,
                2010,
                2015,
                2020,
                2025,
            ]
        ),
        [
            "year",
            "gross_salary_yen",
            "nominal_take_home_yen",
            "real_take_home_yen",
            "effective_burden_rate",
        ],
    ].copy()

    selected["effective_burden_rate"] *= 100

    selected = selected.rename(
        columns={
            "year": "年",
            "gross_salary_yen": "額面賃金（円）",
            "nominal_take_home_yen": "名目手取り（円）",
            "real_take_home_yen": "実質手取り（円）",
            "effective_burden_rate": "実効負担率（%）",
        }
    )

    st.dataframe(
        selected,
        width="stretch",
        hide_index=True,
        column_config={
            "年": st.column_config.NumberColumn(
                format="%d",
            ),
            "額面賃金（円）": st.column_config.NumberColumn(
                format="%,.0f",
            ),
            "名目手取り（円）": st.column_config.NumberColumn(
                format="%,.0f",
            ),
            "実質手取り（円）": st.column_config.NumberColumn(
                format="%,.0f",
            ),
            "実効負担率（%）": st.column_config.NumberColumn(
                format="%.2f",
            ),
        },
    )


# ============================================
# 2. 負担構造
# ============================================

st.header("2. 税・社会保険料の負担構造")

st.altair_chart(
    create_burden_chart(main_df),
    width="stretch",
)

st.caption(
    "各項目の年間本人負担額を"
    "年間額面給与で除した実効負担率。"
    "積み上げ面が項目別負担、"
    "折れ線が合計実効負担率を示します。"
)

st.info(
    "1990→2025年では合計負担率は"
    f"{start['effective_burden_rate'] * 100:.2f}%から"
    f"{end['effective_burden_rate'] * 100:.2f}%へ"
    f"{burden_change_pt:+.2f}ポイント変化しました。"
    "長期的な上昇の中心は厚生年金・健康保険です。"
)

st.divider()


# ============================================
# 3. 額面100円の配分
# ============================================

st.header("3. 額面100円の配分")

st.altair_chart(
    create_hundred_yen_chart(main_df),
    width="stretch",
)

st.caption(
    "年間額面給与100円のうち、"
    "所得税・住民税・社会保険料として"
    "何円が控除され、何円が手取りとして"
    "残るかを示します。"
)


# ============================================
# 4. 期間別対数分解
# ============================================

st.header("4. 実質手取り変化の期間別分解")

st.altair_chart(
    create_period_decomposition_chart(period_log_df),
    width="stretch",
)

st.caption(
    "実質手取りの変化を、"
    "額面賃金・手取り率（負担率）・物価の"
    "3要因へ恒等的に分解しています。"
)

with st.expander("期間別の数値を見る"):
    st.dataframe(
        period_log_df,
        width="stretch",
        hide_index=True,
    )


# ============================================
# 5. Shapley分解
# ============================================

st.header("5. 実質手取りの4要因Shapley分解")

st.altair_chart(
    create_real_shapley_chart(real_shapley_df),
    width="stretch",
)

st.caption(
    "額面賃金・税制度・社会保険制度・物価の"
    "変更順序による交互作用を、"
    "Shapley値によって各要因へ配分しています。"
)

long_term = real_shapley_df.loc[real_shapley_df["period"] == "1990→2025"]

if len(long_term) == 1:
    row = long_term.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "額面賃金要因",
        (f"{row['wage_effect_pct_of_start']:+.2f}%"),
    )

    col2.metric(
        "税制度要因",
        (f"{row['tax_policy_effect_pct_of_start']:+.2f}%"),
    )

    col3.metric(
        "社会保険制度要因",
        (f"{row['social_insurance_policy_effect_pct_of_start']:+.2f}%"),
        delta_color="inverse",
    )

    col4.metric(
        "物価要因",
        (f"{row['price_effect_pct_of_start']:+.2f}%"),
        delta_color="inverse",
    )

    st.info(
        "1990→2025年では、"
        "実質手取りを最も大きく押し下げたのは"
        "物価要因です。社会保険制度も"
        "押下げ方向に寄与する一方、"
        "額面賃金と税制度は押上げ方向に"
        "寄与しています。"
    )


st.header("6. 1990年制度を固定した場合との比較")

st.altair_chart(
    create_fixed_policy_chart(fixed_policy_df),
    width="stretch",
)

fixed_2025 = fixed_policy_df.loc[fixed_policy_df["year"] == 2025]

if len(fixed_2025) == 1:
    row = fixed_2025.iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "実際の2025年手取り",
        (f"{row['actual_nominal_take_home_yen'] / 10_000:,.1f}万円"),
    )

    col2.metric(
        "1990年制度固定",
        (f"{row['fixed_1990_nominal_take_home_yen'] / 10_000:,.1f}万円"),
    )

    col3.metric(
        "実際－固定制度",
        (f"{row['nominal_take_home_yen_difference_yen'] / 10_000:+,.1f}万円"),
        delta_color="inverse",
    )

    st.info(
        "2025年の賃金水準に1990年の税・社会保険制度を"
        "名目額のまま固定して適用すると、"
        f"名目手取りは約"
        f"{abs(row['nominal_take_home_yen_difference_yen']) / 10_000:,.1f}"
        "万円多くなります。"
        f"実際の制度との差は負担率で"
        f"{row['burden_rate_difference_pt']:+.2f}ポイントです。"
    )

st.caption(
    "1990年制度固定系列では、各年の賃金水準は実績値を使用し、"
    "税率・控除・社会保険料率・標準報酬月額表などを"
    "1990年の名目制度に固定しています。"
    "実際に1990年制度が維持された場合の経済全体を予測する"
    "因果的な反実仮想ではありません。"
)

with st.expander("主要年の固定制度比較を見る"):
    selected_fixed = fixed_policy_df.loc[
        fixed_policy_df["year"].isin(
            [
                1990,
                2000,
                2010,
                2015,
                2020,
                2025,
            ]
        ),
        [
            "year",
            "actual_nominal_take_home_yen",
            "fixed_1990_nominal_take_home_yen",
            "nominal_take_home_yen_difference_yen",
            "actual_effective_burden_rate",
            "fixed_1990_effective_burden_rate",
            "burden_rate_difference_pt",
        ],
    ].copy()

    selected_fixed["actual_effective_burden_rate"] *= 100

    selected_fixed["fixed_1990_effective_burden_rate"] *= 100

    selected_fixed = selected_fixed.rename(
        columns={
            "year": "年",
            "actual_nominal_take_home_yen": "実際の手取り（円）",
            "fixed_1990_nominal_take_home_yen": "1990年制度固定（円）",
            "nominal_take_home_yen_difference_yen": "手取り差（円）",
            "actual_effective_burden_rate": "実際の負担率（%）",
            "fixed_1990_effective_burden_rate": "固定制度負担率（%）",
            "burden_rate_difference_pt": "負担率差（pt）",
        }
    )

    st.dataframe(
        selected_fixed,
        width="stretch",
        hide_index=True,
    )


# ============================================
# 7. 頑健性確認
# ============================================

st.header("7. 頑健性確認")

robustness_display = robustness_df.copy()

robustness_display = robustness_display.rename(
    columns={
        "check": "確認項目",
        "comparison": "ケース",
        "period": "期間",
        "metric": "指標",
        "value": "値",
        "unit": "単位",
        "note": "備考",
    }
)

st.dataframe(
    robustness_display,
    width="stretch",
    hide_index=True,
)

st.caption(
    "住民税の時間対応、男女差、"
    "介護保険、一時的減税、"
    "賃金系列の選択を変更した場合の"
    "主要な感応度分析結果です。"
)


# ============================================
# 8. Tableau出力
# ============================================

st.header("8. Tableau用データ")

tableau_df = create_take_home_tableau_export(
    main_series=main_df,
    period_log_decomposition=(period_log_df),
    burden_change_summary=(burden_change_df),
    burden_shapley=(burden_shapley_df),
    real_shapley=(real_shapley_df),
    fixed_policy_comparison=(fixed_policy_df),
    robustness_summary=(robustness_df),
)

tableau_output_df = create_japanese_tableau_export(tableau_df)

csv_bytes = tableau_output_df.to_csv(
    index=False,
).encode("utf-8-sig")

st.download_button(
    label=("Tableau用CSVをダウンロード"),
    data=csv_bytes,
    file_name=("take_home_tableau.csv"),
    mime="text/csv",
    width="stretch",
)

st.caption(
    "Tableauでは「レコード種別」と「指標」を"
    "主要なディメンションとして利用するlong形式です。"
    "対応する英語ID列も保持しています。"
)

with st.expander("Tableau用CSVの構造を見る"):
    st.dataframe(
        tableau_output_df.head(50),
        width="stretch",
        hide_index=True,
    )

    st.markdown(
        """
        - `annual_main`：1990～2025年の年次主系列
        - `period_log_decomposition`：実質手取りの対数分解
        - `burden_change`：期間別の実効負担率変化
        - `burden_shapley`：負担率の3要因Shapley分解
        - `real_take_home_shapley`：実質手取りの4要因Shapley分解
        - `robustness`：感応度・頑健性確認
        """
    )
