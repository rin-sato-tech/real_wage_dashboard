import altair as alt
import pandas as pd
import streamlit as st

from real_wage_dashboard.config import (
    CPI_BASE_FILTERS,
    CPI_DEFAULT_SERIES,
    CPI_SERIES,
    CPI_STATS_DATA_ID,
    WAGE_BASE_YEAR,
    WAGE_DATA_PATH,
    WAGE_DEFAULT_ESTABLISHMENT_SIZE,
    WAGE_ESTABLISHMENT_SIZES,
)
from real_wage_dashboard.cpi_service import create_cpi_dataframe
from real_wage_dashboard.employment_analysis import (
    create_full_employment_analysis_dataframe,
    create_yearly_comparison_summary,
)
from real_wage_dashboard.estat_client import (
    EStatAPIError,
    get_stats_data,
)
from real_wage_dashboard.wage_service import (
    create_wage_dataframe,
    load_wage_csv,
)
from real_wage_dashboard.working_hours_service import (
    create_working_hours_dataframe,
)

ANALYSIS_START_YEAR = 2015
ANALYSIS_END_YEAR = 2025

ANALYSIS_INDICATORS = [
    "nominal_wage_amount",
    "working_hours",
    "approx_hourly_wage",
    "real_regular_wage",
    "real_approx_hourly_wage",
]

ANALYSIS_INDICATOR_LABELS = {
    "nominal_wage_amount": "月額賃金",
    "working_hours": "総実労働時間",
    "approx_hourly_wage": "概算時間当たり賃金",
    "real_regular_wage": "実質月額賃金",
    "real_approx_hourly_wage": "実質概算時間当たり賃金",
}

st.set_page_config(
    page_title="雇用形態比較",
    page_icon="👥",
    layout="wide",
)


@st.cache_data
def load_raw_wage_data() -> pd.DataFrame:
    """毎月勤労統計の元CSVを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)


@st.cache_data(ttl=60 * 60 * 6)
def load_cpi_data(
    app_id: str,
    series_code: str,
) -> pd.DataFrame:
    """指定系列のCPIデータを取得する。"""

    filters = {
        **CPI_BASE_FILTERS,
        "cdCat01": series_code,
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=CPI_STATS_DATA_ID,
        filters=filters,
    )

    return create_cpi_dataframe(response)


def create_analysis_dataframe(
    raw_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    establishment_size: str,
    employment_type: str,
) -> pd.DataFrame:
    """指定した就業形態の分析DataFrameを作成する。"""

    wage_df = create_wage_dataframe(
        raw_df,
        wage_item="きまって支給する給与",
        establishment_size=establishment_size,
        employment_type=employment_type,
    )

    working_hours_df = create_working_hours_dataframe(
        raw_df,
        working_hours_item="総実労働時間",
        establishment_size=establishment_size,
        employment_type=employment_type,
    )

    return create_full_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
        cpi_df,
        base_year=WAGE_BASE_YEAR,
    )


def create_comparison_chart_dataframe(
    general_df: pd.DataFrame,
    part_df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """一般労働者とパートの指定指標を横持ちで結合する。"""

    general = general_df[
        [
            "date",
            column,
        ]
    ].rename(
        columns={
            column: "一般労働者",
        }
    )

    part = part_df[
        [
            "date",
            column,
        ]
    ].rename(
        columns={
            column: "パートタイム労働者",
        }
    )

    return general.merge(
        part,
        on="date",
        how="inner",
        validate="one_to_one",
    )


def create_comparison_output_dataframe(
    general_df: pd.DataFrame,
    part_df: pd.DataFrame,
) -> pd.DataFrame:
    """一般労働者とパートの分析結果を縦結合する。"""

    general = general_df.copy()
    general["employment_type"] = "一般労働者"

    part = part_df.copy()
    part["employment_type"] = "パートタイム労働者"

    result = pd.concat(
        [
            general,
            part,
        ],
        ignore_index=True,
    )

    return result.sort_values(
        [
            "date",
            "employment_type",
        ]
    ).reset_index(drop=True)


def create_index_chart(
    df: pd.DataFrame,
    title: str,
    y_title: str,
) -> alt.Chart:
    """雇用形態比較用の指数折れ線グラフを作成する。"""

    long_df = df.melt(
        id_vars="date",
        value_vars=[
            "一般労働者",
            "パートタイム労働者",
        ],
        var_name="就業形態",
        value_name="指数",
    )

    y_min = long_df["指数"].min()
    y_max = long_df["指数"].max()

    padding = max(
        (y_max - y_min) * 0.1,
        2,
    )

    chart = (
        alt.Chart(long_df)
        .mark_line(
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "date:T",
                title="年月",
            ),
            y=alt.Y(
                "指数:Q",
                title=y_title,
                scale=alt.Scale(
                    domain=[
                        y_min - padding,
                        y_max + padding,
                    ],
                    zero=False,
                ),
            ),
            color=alt.Color(
                "就業形態:N",
                title="就業形態",
                scale=alt.Scale(
                    domain=[
                        "一般労働者",
                        "パートタイム労働者",
                    ],
                    range=[
                        "#1f77b4",
                        "#e45756",
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="年月",
                    format="%Y年%m月",
                ),
                alt.Tooltip(
                    "就業形態:N",
                    title="就業形態",
                ),
                alt.Tooltip(
                    "指数:Q",
                    title="指数",
                    format=".1f",
                ),
            ],
        )
        .properties(
            title=title,
            height=400,
        )
        .interactive()
    )

    baseline = (
        alt.Chart(
            pd.DataFrame(
                {
                    "y": [100],
                }
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
        )
        .encode(
            y="y:Q",
        )
    )

    return chart + baseline


def create_decomposition_chart(
    df: pd.DataFrame,
    title: str,
) -> alt.LayerChart:
    """月額賃金変化の要因分解を棒グラフと折れ線で表示する。"""

    chart_df = df[
        [
            "date",
            "wage_log_change",
            "hourly_wage_log_contribution",
            "working_hours_log_contribution",
        ]
    ].dropna()

    contribution_df = chart_df.melt(
        id_vars="date",
        value_vars=[
            "hourly_wage_log_contribution",
            "working_hours_log_contribution",
        ],
        var_name="要因",
        value_name="寄与",
    )

    contribution_df["要因"] = contribution_df["要因"].replace(
        {
            "hourly_wage_log_contribution": "時間当たり賃金要因",
            "working_hours_log_contribution": "労働時間要因",
        }
    )

    base = alt.Chart(chart_df).encode(
        x=alt.X(
            "date:T",
            title="年月",
        )
    )

    bars = (
        alt.Chart(contribution_df)
        .mark_bar(opacity=0.75)
        .encode(
            x=alt.X(
                "date:T",
                title="年月",
            ),
            y=alt.Y(
                "寄与:Q",
                title="前年同月からの対数変化（×100）",
            ),
            color=alt.Color(
                "要因:N",
                title="要因",
                scale=alt.Scale(
                    domain=[
                        "時間当たり賃金要因",
                        "労働時間要因",
                    ],
                    range=[
                        "#4c78a8",
                        "#f58518",
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="年月",
                    format="%Y年%m月",
                ),
                alt.Tooltip(
                    "要因:N",
                    title="要因",
                ),
                alt.Tooltip(
                    "寄与:Q",
                    title="寄与",
                    format="+.2f",
                ),
            ],
        )
    )

    line = base.mark_line(
        strokeWidth=2.5,
        color="#222222",
    ).encode(
        y=alt.Y(
            "wage_log_change:Q",
            title="前年同月からの対数変化（×100）",
        ),
        tooltip=[
            alt.Tooltip(
                "date:T",
                title="年月",
                format="%Y年%m月",
            ),
            alt.Tooltip(
                "wage_log_change:Q",
                title="月額賃金の対数変化",
                format="+.2f",
            ),
        ],
    )

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(
            color="#666666",
            strokeDash=[4, 4],
        )
        .encode(
            y="y:Q",
        )
    )

    return (bars + line + zero_line).properties(
        title=title,
        height=400,
    )


def create_change_summary_display(
    comparison_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態別の変化率を指標ごとに横並びにする。"""

    change_df = comparison_summary_df[
        [
            "indicator",
            "employment_type",
            "change_rate_pct",
        ]
    ].copy()

    result = change_df.pivot(
        index="indicator",
        columns="employment_type",
        values="change_rate_pct",
    ).reset_index()

    result["指標"] = result["indicator"].map(ANALYSIS_INDICATOR_LABELS)

    result["差（pt）"] = result["パートタイム労働者"] - result["一般労働者"]

    return result[
        [
            "指標",
            "一般労働者",
            "パートタイム労働者",
            "差（pt）",
        ]
    ]


def main() -> None:
    st.title("一般労働者・パートタイム労働者の比較")

    st.caption(
        "一般労働者とパートタイム労働者について、"
        "月額賃金・労働時間・概算時間当たり賃金・実質購買力の推移を比較します。"
    )

    # -------------------------
    # 分析条件
    # -------------------------

    st.subheader("分析条件")

    condition_col1, condition_col2 = st.columns(2)

    with condition_col1:
        establishment_size = st.selectbox(
            "事業所規模",
            list(WAGE_ESTABLISHMENT_SIZES.keys()),
            index=list(WAGE_ESTABLISHMENT_SIZES.keys()).index(
                WAGE_DEFAULT_ESTABLISHMENT_SIZE
            ),
        )

    with condition_col2:
        selected_series = st.selectbox(
            "実質化に使用する消費者物価指数",
            list(CPI_SERIES.keys()),
            index=list(CPI_SERIES.keys()).index(CPI_DEFAULT_SERIES),
        )

    st.caption(
        "賃金項目：きまって支給する給与 ／ 労働時間：総実労働時間 ／ 産業：調査産業計"
    )

    selected_size_code = WAGE_ESTABLISHMENT_SIZES[establishment_size]
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
        raw_df = load_raw_wage_data()

        cpi_df = load_cpi_data(
            app_id,
            selected_series_code,
        )

        general_df = create_analysis_dataframe(
            raw_df,
            cpi_df,
            establishment_size=selected_size_code,
            employment_type="1",
        )

        part_df = create_analysis_dataframe(
            raw_df,
            cpi_df,
            establishment_size=selected_size_code,
            employment_type="2",
        )

    except EStatAPIError as exc:
        st.error(str(exc))
        st.stop()

    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()

    # -------------------------
    # 生成確認
    # -------------------------

    latest_general = general_df.iloc[-1]
    latest_part = part_df.iloc[-1]

    st.subheader("最新データ")

    general_col, part_col = st.columns(2)

    with general_col:
        st.markdown("#### 一般労働者")

        metric_col1, metric_col2, metric_col3 = st.columns(3)

        metric_col1.metric(
            "月額賃金",
            f"{latest_general['nominal_wage_amount']:,.0f}円",
            f"{latest_general['regular_wage_yoy_pct']:+.1f}%",
        )

        metric_col2.metric(
            "総実労働時間",
            f"{latest_general['working_hours']:.1f}時間",
            f"{latest_general['working_hours_yoy_pct']:+.1f}%",
        )

        metric_col3.metric(
            "概算時間当たり賃金",
            f"{latest_general['approx_hourly_wage']:,.0f}円",
            f"{latest_general['approx_hourly_wage_yoy_pct']:+.1f}%",
        )

    with part_col:
        st.markdown("#### パートタイム労働者")

        metric_col1, metric_col2, metric_col3 = st.columns(3)

        metric_col1.metric(
            "月額賃金",
            f"{latest_part['nominal_wage_amount']:,.0f}円",
            f"{latest_part['regular_wage_yoy_pct']:+.1f}%",
        )

        metric_col2.metric(
            "総実労働時間",
            f"{latest_part['working_hours']:.1f}時間",
            f"{latest_part['working_hours_yoy_pct']:+.1f}%",
        )

        metric_col3.metric(
            "概算時間当たり賃金",
            f"{latest_part['approx_hourly_wage']:,.0f}円",
            f"{latest_part['approx_hourly_wage_yoy_pct']:+.1f}%",
        )

    st.caption(
        f"最新データ：{latest_general['date'].strftime('%Y年%m月')} "
        "（各指標の下段は前年同月比）"
    )

    st.caption(
        f"データ期間："
        f"{general_df['date'].min().strftime('%Y年%m月')} ～ "
        f"{general_df['date'].max().strftime('%Y年%m月')}"
    )

    st.subheader("2015年から2025年の変化")

    try:
        comparison_summary_df = create_yearly_comparison_summary(
            general_df,
            part_df,
            start_year=ANALYSIS_START_YEAR,
            end_year=ANALYSIS_END_YEAR,
            columns=ANALYSIS_INDICATORS,
        )

    except ValueError as exc:
        st.warning(f"年平均による比較結果を作成できませんでした：{exc}")

    else:
        change_summary_df = create_change_summary_display(comparison_summary_df)

        st.markdown("#### 変化率の比較")

        st.dataframe(
            change_summary_df,
            width="stretch",
            hide_index=True,
            column_config={
                "一般労働者": st.column_config.NumberColumn(
                    "一般労働者",
                    format="%+.1f%%",
                ),
                "パートタイム労働者": st.column_config.NumberColumn(
                    "パートタイム労働者",
                    format="%+.1f%%",
                ),
                "差（pt）": st.column_config.NumberColumn(
                    "パート - 一般",
                    format="%+.1f",
                ),
            },
        )

        st.caption(
            "「パート - 一般」は2015年平均から2025年平均までの変化率の差（%ポイント）です。"
            "賃金額そのものの差を示すものではありません。"
        )

        st.markdown("#### 年平均の詳細")

        analysis_display_df = comparison_summary_df.copy()

        analysis_display_df["指標"] = analysis_display_df["indicator"].map(
            ANALYSIS_INDICATOR_LABELS
        )

        analysis_display_df["就業形態"] = analysis_display_df["employment_type"]

        analysis_display_df["2015年平均"] = analysis_display_df["start_value"]

        analysis_display_df["2025年平均"] = analysis_display_df["end_value"]

        analysis_display_df["変化率"] = analysis_display_df["change_rate_pct"]

        analysis_display_df = analysis_display_df[
            [
                "指標",
                "就業形態",
                "2015年平均",
                "2025年平均",
                "変化率",
            ]
        ]

        st.dataframe(
            analysis_display_df,
            width="stretch",
            hide_index=True,
            column_config={
                "2015年平均": st.column_config.NumberColumn(
                    format="%.1f",
                ),
                "2025年平均": st.column_config.NumberColumn(
                    format="%.1f",
                ),
                "変化率": st.column_config.NumberColumn(
                    format="%+.1f%%",
                ),
            },
        )

        st.caption(
            f"{ANALYSIS_START_YEAR}年と{ANALYSIS_END_YEAR}年について、"
            "各12か月の平均値を比較しています。"
            f"事業所規模：{establishment_size} ／ "
            f"CPI：{selected_series}"
        )

    st.subheader("時系列推移")

    period_options = [
        "直近5年",
        "直近10年",
        "直近20年",
        "全期間",
    ]

    period = st.selectbox(
        "表示期間",
        period_options,
        index=period_options.index("直近10年"),
    )

    period_months = {
        "直近5年": 60,
        "直近10年": 120,
        "直近20年": 240,
        "全期間": None,
    }[period]

    def filter_display_period(
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        if period_months is None:
            return df.copy()

        return df.tail(period_months).copy()

    general_display_df = filter_display_period(general_df)
    part_display_df = filter_display_period(part_df)

    st.markdown("## 1. 何が起きたか")

    st.caption(
        "2020年平均を100として、月額賃金・労働時間・概算時間当たり賃金の変化を比較します。"
    )

    regular_wage_chart_df = create_comparison_chart_dataframe(
        general_display_df,
        part_display_df,
        "regular_wage_index",
    )

    st.altair_chart(
        create_index_chart(
            regular_wage_chart_df,
            title="月額賃金指数",
            y_title="指数（2020年平均=100）",
        ),
        width="stretch",
    )

    st.info(
        """
    **読み方：** 各就業形態の「きまって支給する給与」が、
    2020年平均からどの程度変化したかを示します。100を上回れば2020年平均より高い水準です。

    **分かること：** 一般労働者とパートタイム労働者で、
    月額賃金の伸び方がどのように異なるかを比較できます。

    **分からないこと：** 両者はそれぞれ個別に2020年平均=100としているため、
    指数の高さから実際の賃金額の大小や賃金格差を比較することはできません。
    """
    )

    working_hours_chart_df = create_comparison_chart_dataframe(
        general_display_df,
        part_display_df,
        "working_hours_index",
    )

    st.altair_chart(
        create_index_chart(
            working_hours_chart_df,
            title="総実労働時間指数",
            y_title="指数（2020年平均=100）",
        ),
        width="stretch",
    )

    st.info(
        """
    **読み方：** 月間の総実労働時間が、
    各就業形態の2020年平均からどの程度変化したかを示します。

    **分かること：** 月額賃金の変化が、労働時間の増減から
    どの程度影響を受けている可能性があるかを考える手掛かりになります。

    **分からないこと：** 労働時間が変化した理由や、
    本人の希望による変化か企業側の要因による変化かまでは判断できません。
    """
    )

    hourly_wage_chart_df = create_comparison_chart_dataframe(
        general_display_df,
        part_display_df,
        "approx_hourly_wage_index",
    )

    st.altair_chart(
        create_index_chart(
            hourly_wage_chart_df,
            title="概算時間当たり賃金指数",
            y_title="指数（2020年平均=100）",
        ),
        width="stretch",
    )

    st.info(
        """
    **読み方：** 「きまって支給する給与 ÷ 総実労働時間」で算出した
    概算時間当たり賃金の変化を示します。

    **分かること：** 労働時間の長短の影響をある程度取り除き、
    1時間当たりの賃金水準がどのように変化したかを比較できます。

    **分からないこと：** この値は公表された公式の時給ではありません。
    また、各就業形態の実際の時間当たり賃金額の差を指数から判断することもできません。
    """
    )

    st.markdown("## 2. 物価を考えるとどうか")
    st.caption("名目賃金を消費者物価指数で実質化し、購買力の変化を比較します。")

    real_regular_wage_chart_df = create_comparison_chart_dataframe(
        general_display_df,
        part_display_df,
        "real_regular_wage_index",
    )

    st.altair_chart(
        create_index_chart(
            real_regular_wage_chart_df,
            title="実質月額賃金指数",
            y_title="指数（2020年平均=100）",
        ),
        width="stretch",
    )

    st.info(
        """
    **読み方：** 月額の「きまって支給する給与」を選択したCPIで実質化し、
    2020年平均=100として購買力の変化を示します。

    **分かること：** 名目賃金の上昇が物価上昇を上回っているかを確認できます。
    名目賃金が増えていても、物価上昇の方が大きければ実質指数は低下します。

    **分からないこと：** 本アプリで算出した実質値であり、
    公式に公表される実質賃金指数と同一ではありません。
    """
    )

    real_hourly_wage_chart_df = create_comparison_chart_dataframe(
        general_display_df,
        part_display_df,
        "real_approx_hourly_wage_index",
    )

    st.altair_chart(
        create_index_chart(
            real_hourly_wage_chart_df,
            title="実質概算時間当たり賃金指数",
            y_title="指数（2020年平均=100）",
        ),
        width="stretch",
    )

    st.info(
        """
    **読み方：** 概算時間当たり賃金を選択したCPIで実質化し、
    1時間当たりの賃金の購買力を2020年平均=100として示します。

    **分かること：** 1時間働くことで得られる実質的な購買力が
    どのように変化したかを確認できます。実質月額賃金と比較すると、
    労働時間の変化が月額の購買力に与える影響も考察できます。

    **分からないこと：** 「概算時間当たり賃金」を基にした本アプリ独自の指標であり、
    公式な実質時給を示すものではありません。
    """
    )

    st.markdown("## 3. なぜそうなったか")

    st.caption(
        "月額賃金の前年同月変化を、概算時間当たり賃金の変化と労働時間の変化に分解します。"
    )

    st.altair_chart(
        create_decomposition_chart(
            general_display_df,
            "一般労働者：月額賃金変化の要因分解",
        ),
        width="stretch",
    )

    st.altair_chart(
        create_decomposition_chart(
            part_display_df,
            "パートタイム労働者：月額賃金変化の要因分解",
        ),
        width="stretch",
    )

    st.info(
        """
    **読み方：** 月額賃金の前年同月からの変化を、
    「時間当たり賃金要因」と「労働時間要因」に分解しています。
    棒がプラスなら月額賃金を押し上げる方向、
    マイナスなら押し下げる方向です。黒線は両要因を合わせた月額賃金の対数変化です。

    **分かること：** 月額賃金が増減した背景について、
    時間当たり賃金の変化と労働時間の変化のどちらが寄与したかを確認できます。

    **分からないこと：** 労働時間や時間当たり賃金が変化した原因そのものは、
    この分解だけでは判断できません。また、値は通常の前年比（%）ではなく
    前年同月からの対数変化を100倍したものです。
    """
    )

    comparison_output_df = create_comparison_output_dataframe(
        general_df,
        part_df,
    )

    st.subheader("分析データ")

    display_columns = [
        "date",
        "employment_type",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
        "real_regular_wage",
        "real_approx_hourly_wage",
        "regular_wage_index",
        "working_hours_index",
        "approx_hourly_wage_index",
        "real_regular_wage_index",
        "real_approx_hourly_wage_index",
        "regular_wage_yoy_pct",
        "working_hours_yoy_pct",
        "approx_hourly_wage_yoy_pct",
        "real_regular_wage_yoy_pct",
        "real_approx_hourly_wage_yoy_pct",
        "wage_log_change",
        "hourly_wage_log_contribution",
        "working_hours_log_contribution",
    ]

    display_df = comparison_output_df[display_columns].copy()

    display_df = display_df.sort_values(
        [
            "date",
            "employment_type",
        ],
        ascending=[
            False,
            True,
        ],
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )

    csv_data = (
        comparison_output_df[display_columns]
        .to_csv(
            index=False,
        )
        .encode("utf-8-sig")
    )

    st.download_button(
        label="CSVをダウンロード",
        data=csv_data,
        file_name="employment_comparison.csv",
        mime="text/csv",
    )

    st.subheader("注意事項")

    st.markdown(
        """
    - **概算時間当たり賃金**は、公表されている公式の時給ではありません。
    本アプリでは「きまって支給する給与 ÷ 総実労働時間」で算出しています。
    - **実質月額賃金・実質概算時間当たり賃金**は、
    選択した消費者物価指数を用いて本アプリ側で実質化した値です。
    公式に公表されている実質賃金指数とは定義・計算方法が異なる場合があります。
    - 各指数は、**一般労働者とパートタイム労働者について、それぞれ個別に
    2020年平均=100として指数化**しています。
    したがって、指数の水準から両者の絶対的な賃金格差を比較することはできません。
    - 要因分解では、月額賃金を
    「概算時間当たり賃金 × 総実労働時間」とみなし、
    前年同月からの**対数変化**を時間当たり賃金要因と労働時間要因に分解しています。
    - 要因分解の値は通常の前年比（%）とは異なります。
    対数変化を100倍した値として表示しています。
    """
    )

    st.subheader("データ出典")

    st.markdown(
        f"""
    - 賃金・労働時間：政府統計の総合窓口 e-Stat
    「毎月勤労統計調査」
    - 産業：調査産業計
    - 賃金項目：きまって支給する給与
    - 労働時間：総実労働時間
    - 事業所規模：{establishment_size}
    - 消費者物価指数：{selected_series}
    """
    )


if __name__ == "__main__":
    main()
