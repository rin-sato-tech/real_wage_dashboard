import altair as alt
import pandas as pd
import streamlit as st
import hashlib
import io
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

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
    summarize_wage_change_decomposition,
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
    "nominal_wage_amount": "名目月額賃金",
    "working_hours": "総実労働時間",
    "approx_hourly_wage": "時間当たり賃金",
    "real_regular_wage": "実質月額賃金",
    "real_approx_hourly_wage": "実質時間当たり賃金",
}

ANALYSIS_INDICATOR_UNITS = {
    "nominal_wage_amount": "円",
    "working_hours": "時間",
    "approx_hourly_wage": "円/時間",
    "real_regular_wage": "円（2020年価格換算）",
    "real_approx_hourly_wage": "円/時間（2020年価格換算）",
}

TABLEAU_EXPORT_COLUMNS = [
    # 分析条件
    "date",
    "employment_type",
    "establishment_size",
    "cpi_series",
    "wage_item",
    "working_hours_item",
    "industry",
    # 基本指標
    "nominal_wage_amount",
    "working_hours",
    "approx_hourly_wage",
    # 実質指標
    "real_regular_wage",
    "real_approx_hourly_wage",
    # 指数
    "regular_wage_index",
    "working_hours_index",
    "approx_hourly_wage_index",
    "real_regular_wage_index",
    "real_approx_hourly_wage_index",
    # 前年同月比
    "regular_wage_yoy_pct",
    "working_hours_yoy_pct",
    "approx_hourly_wage_yoy_pct",
    "real_regular_wage_yoy_pct",
    "real_approx_hourly_wage_yoy_pct",
    # 要因分解
    "wage_log_change",
    "hourly_wage_log_contribution",
    "working_hours_log_contribution",
]

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
        ["date", column,]
    ].rename(
        columns={column: "一般労働者"}
    )

    part = part_df[
        ["date", column,]
    ].rename(
        columns={column: "パートタイム労働者"}
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
    establishment_size: str,
    cpi_series: str,
) -> pd.DataFrame:
    """一般労働者とパートの分析結果を選択条件付きで縦結合する。"""

    general = general_df.copy()
    general["employment_type"] = "一般労働者"

    part = part_df.copy()
    part["employment_type"] = "パートタイム労働者"

    result = pd.concat(
        [general, part],
        ignore_index=True,
    )

    result["establishment_size"] = establishment_size
    result["cpi_series"] = cpi_series
    result["wage_item"] = "きまって支給する給与"
    result["working_hours_item"] = "総実労働時間"
    result["industry"] = "調査産業計"

    return result.sort_values(
        ["date", "employment_type"]
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

    result = (
        change_df.pivot(
            index="indicator",
            columns="employment_type",
            values="change_rate_pct",
        )
        .reindex(ANALYSIS_INDICATORS)
        .reset_index()
    )

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


def get_change_rate(
    comparison_summary_df: pd.DataFrame,
    employment_type: str,
    indicator: str,
) -> float:
    """指定した就業形態・指標の変化率を取得する。"""

    matched = comparison_summary_df[
        (comparison_summary_df["employment_type"] == employment_type)
        & (comparison_summary_df["indicator"] == indicator)
    ]

    if len(matched) != 1:
        raise ValueError(
            f"比較結果を一意に取得できません: {employment_type}, {indicator}"
        )

    return float(matched.iloc[0]["change_rate_pct"])


def create_tableau_export_dataframe(
    raw_df: pd.DataFrame,
    cpi_dataframes: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Tableau用に全事業所規模・全CPI系列の分析結果を結合する。"""

    results = []

    for establishment_size, establishment_size_code in WAGE_ESTABLISHMENT_SIZES.items():
        for cpi_series, cpi_df in cpi_dataframes.items():
            general_df = create_analysis_dataframe(
                raw_df,
                cpi_df,
                establishment_size=establishment_size_code,
                employment_type="1",
            )

            part_df = create_analysis_dataframe(
                raw_df,
                cpi_df,
                establishment_size=establishment_size_code,
                employment_type="2",
            )

            comparison_df = create_comparison_output_dataframe(
                general_df,
                part_df,
                establishment_size=establishment_size,
                cpi_series=cpi_series,
            )

            results.append(comparison_df)

    if not results:
        raise ValueError("Tableau用データを生成できませんでした。")

    result = (
        pd.concat(
            results,
            ignore_index=True,
        )
        .sort_values(
            [
                "date",
                "establishment_size",
                "cpi_series",
                "employment_type",
            ]
        )
        .reset_index(drop=True)
    )

    missing_columns = set(TABLEAU_EXPORT_COLUMNS) - set(result.columns)

    if missing_columns:
        raise ValueError(
            f"Tableau出力に必要な列がありません: {sorted(missing_columns)}"
        )

    return result[TABLEAU_EXPORT_COLUMNS]


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

    st.caption(
        f"データ期間："
        f"{general_df['date'].min().strftime('%Y年%m月')} ～ "
        f"{general_df['date'].max().strftime('%Y年%m月')}"
    )

    st.subheader(
        f"主要結果：{ANALYSIS_START_YEAR}年から"
        f"{ANALYSIS_END_YEAR}年の変化"
    )

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
        st.stop()

    else:
        change_summary_df = create_change_summary_display(comparison_summary_df)

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
                    "パート－一般（ポイント）",
                    format="%+.1f",
                ),
            },
        )

        st.caption(
            f"{ANALYSIS_START_YEAR}年平均から"
            f"{ANALYSIS_END_YEAR}年平均までの変化率。"
            "「パート－一般」は変化率の差（%ポイント）であり、"
            "賃金額そのものの差ではありません。"
        )

        analysis_display_df = comparison_summary_df.copy()

        analysis_display_df["指標"] = analysis_display_df["indicator"].map(
            ANALYSIS_INDICATOR_LABELS
        )

        analysis_display_df["単位"] = analysis_display_df["indicator"].map(
            ANALYSIS_INDICATOR_UNITS
        )

        analysis_display_df["就業形態"] = analysis_display_df["employment_type"]

        analysis_display_df[f"{ANALYSIS_START_YEAR}年平均"] = analysis_display_df[
            "start_value"
        ]

        analysis_display_df[f"{ANALYSIS_END_YEAR}年平均"] = analysis_display_df[
            "end_value"
        ]

        analysis_display_df["変化率"] = analysis_display_df["change_rate_pct"]

        analysis_display_df = analysis_display_df[
            [
                "指標",
                "就業形態",
                "単位",
                f"{ANALYSIS_START_YEAR}年平均",
                f"{ANALYSIS_END_YEAR}年平均",
                "変化率",
            ]
        ]

        with st.expander(
            f"{ANALYSIS_START_YEAR}年・"
            f"{ANALYSIS_END_YEAR}年の年平均を確認",
            expanded=False,
        ):
            st.dataframe(
                analysis_display_df,
                width="stretch",
                hide_index=True,
                column_config={
                    f"{ANALYSIS_START_YEAR}年平均": st.column_config.NumberColumn(
                        format="%.1f",
                    ),
                    f"{ANALYSIS_END_YEAR}年平均": st.column_config.NumberColumn(
                        format="%.1f",
                    ),
                    "変化率": st.column_config.NumberColumn(
                        format="%+.1f%%",
                    ),
                },
            )

            st.caption(
                "実質値は選択中のCPI系列を用いて実質化しています。"
                "「2020年価格換算」はCPIの2020年基準に対応した表記です。"
            )

        st.markdown("#### 結果の要点")

        if (
            establishment_size == "5人以上"
            and selected_series == "総合"
            and ANALYSIS_START_YEAR == 2015
            and ANALYSIS_END_YEAR == 2025
        ):
            st.caption(
                "考察更新日：2026年9月11日 ｜ "
                "対象：5人以上・調査産業計・CPI総合"
            )

            st.markdown(
                "- **実質月額賃金**：2015→2025年では、"
                "一般で2.9%低下、パートで1.4%上昇。\n"
                "- **実質時間当たり賃金**：同期間では、"
                "一般で2.0%、パートで14.2%上昇。\n"
                "- **比較期間による違い**：一般の実質時間当たり賃金は、"
                "2019→2025年では約1.0%低下。"
                "改善の評価は開始年によって異なる。"
            )

            with st.expander("考察の詳細", expanded=False):
                st.markdown(
                    "一般・パートともに、2015年から2025年にかけて"
                    "名目月額賃金と時間当たり賃金が上昇し、"
                    "総実労働時間は減少した。"
                    "ただし、2020年から2025年の労働時間の変化は"
                    "両者とも小幅であり、一様に減少し続けたとは言えない。\n\n"
                    "物価を考慮すると、月額と時間当たりでは"
                    "改善の程度が異なる。特に一般では、"
                    "比較開始年によって実質時間当たり賃金の"
                    "増減方向も変わる。\n\n"
                    "集計順序を変えた比較では、対象6項目の変化率の差は"
                    "すべて0.01パーセントポイント未満だった。"
                    "この確認は公式の労働者数加重平均との比較ではない。\n\n"
                    "これらは集団平均の変化であり、"
                    "個人の賃上げや勤務時間の短縮を示すものではない。"
                    "時間当たり賃金は給与と実労働時間の比率であり、"
                    "契約上の時給とは異なる。"
                    "賃金や労働時間が変化した原因も、この比較だけでは特定できない。"
                )
        else:
            st.caption(
                "現在の選択条件に対応する固定考察は未掲載です。"
                "比較表と各タブで結果を確認してください。"
            )

        st.divider()

        tab_trends, tab_validation, tab_data = st.tabs(
            [
                "時系列・月次分解",
                "期間別比較・検証",
                "データ・保存",
            ]
        )

        with tab_validation:
            # 集計順序による変化率の違いを確認する。
            sensitivity_rows = []

            for employment_type, analysis_df in [
                ("一般労働者", general_df),
                ("パートタイム労働者", part_df),
            ]:
                alternative_values = {}

                for year in [ANALYSIS_START_YEAR, ANALYSIS_END_YEAR]:
                    annual_df = analysis_df.loc[
                        analysis_df["date"].dt.year == year
                    ]

                    # 賃金・時間等の12か月確認は、
                    # 上で実行した年次比較関数で実施済み。
                    cpi = annual_df["index_value"]
                    if (
                        cpi.isna().any()
                        or not cpi.between(0, float("inf"), inclusive="neither").all()
                    ):
                        raise ValueError(
                            f"{employment_type}・{year}年のCPIが不正です。"
                        )

                    mean_wage = annual_df["nominal_wage_amount"].mean()
                    mean_hours = annual_df["working_hours"].mean()
                    mean_cpi = cpi.mean()

                    alternative_values[year] = {
                        "approx_hourly_wage": mean_wage / mean_hours,
                        "real_regular_wage": mean_wage / mean_cpi * 100,
                        "real_approx_hourly_wage": (
                            mean_wage / mean_hours / mean_cpi * 100
                        ),
                    }

                for indicator, label in [
                    ("approx_hourly_wage", "時間当たり賃金"),
                    ("real_regular_wage", "実質月額賃金"),
                    ("real_approx_hourly_wage", "実質時間当たり賃金"),
                ]:
                    start_value = alternative_values[ANALYSIS_START_YEAR][indicator]
                    end_value = alternative_values[ANALYSIS_END_YEAR][indicator]
                    alternative_rate = (end_value / start_value - 1) * 100

                    current_rate = get_change_rate(
                        comparison_summary_df,
                        employment_type,
                        indicator,
                    )

                    sensitivity_rows.append(
                        {
                            "就業形態": employment_type,
                            "指標": label,
                            "現在の方法（%）": current_rate,
                            "年平均から計算（%）": alternative_rate,
                            "差（ポイント）": alternative_rate - current_rate,
                        }
                    )

            with st.expander("集計方法による結果の違いを確認", expanded=False):
                st.dataframe(
                    pd.DataFrame(sensitivity_rows),
                    hide_index=True,
                    column_config={
                        column: st.column_config.NumberColumn(format="%+.3f")
                        for column in [
                            "現在の方法（%）",
                            "年平均から計算（%）",
                            "差（ポイント）",
                        ]
                    },
                )
                st.caption(
                    "2015年平均から2025年平均への変化率を比較しています。"
                    "差は「年平均から計算－現在の方法」です。"
                    "公式の労働者数加重平均との比較ではありません。"
                )

    with tab_validation:
        st.subheader("期間別の変化")

        comparison_periods = [
            (2015, 2019),
            (2019, 2020),
            (2020, 2025),
            (2019, 2025),
        ]

        period_results = []

        try:
            for start_year, end_year in comparison_periods:
                result = create_yearly_comparison_summary(
                    general_df,
                    part_df,
                    start_year=start_year,
                    end_year=end_year,
                    columns=ANALYSIS_INDICATORS,
                )

                # 年率換算には、正の開始値・終了値を使用する。
                if (
                    result[["start_value", "end_value"]] <= 0
                ).any().any():
                    raise ValueError(
                        f"{start_year}→{end_year}年の"
                        "年率換算には正の開始値・終了値が必要です。"
                    )

                years = end_year - start_year
                result["annualized_change_pct"] = (
                    (
                        result["end_value"]
                        / result["start_value"]
                    ) ** (1 / years)
                    - 1
                ) * 100

                result["period"] = f"{start_year}→{end_year}"
                period_results.append(result)

            period_comparison_df = pd.concat(
                period_results,
                ignore_index=True,
            )

        except ValueError as exc:
            st.error(f"期間別比較を作成できませんでした：{exc}")
            st.stop()

        period_labels = {
            "nominal_wage_amount": "名目月額賃金",
            "working_hours": "総実労働時間",
            "approx_hourly_wage": "時間当たり賃金",
            "real_regular_wage": "実質月額賃金",
            "real_approx_hourly_wage": "実質時間当たり賃金",
        }

        for employment_type in [
            "一般労働者",
            "パートタイム労働者",
        ]:
            selected = period_comparison_df.loc[
                period_comparison_df["employment_type"]
                == employment_type
            ]

            st.markdown(f"#### {employment_type}")

            for value_column, title in [
                ("change_rate_pct", "期間全体の変化率（%）"),
                ("annualized_change_pct", "年率換算（%／年）"),
            ]:
                table = selected.pivot(
                    index="indicator",
                    columns="period",
                    values=value_column,
                ).reindex(
                    index=ANALYSIS_INDICATORS,
                    columns=[
                        f"{start}→{end}"
                        for start, end in comparison_periods
                    ],
                )

                table.index = table.index.map(period_labels)
                table.index.name = "指標"

                st.caption(title)
                st.dataframe(table.style.format("{:+.2f}"))

        st.caption(
            "各年12か月の月次値を単純平均して比較しています。"
            "年率換算は（終了値÷開始値）"
            "の経過年数乗根から1を引いて算出した値です。"
            "各年の実際の変化率の平均ではありません。"
            "2019→2025年は他の期間と重なる補足比較です。"
        )

        st.download_button(
            "期間別比較のCSVをダウンロード",
            data=period_comparison_df.to_csv(
                index=False,
                float_format="%.17g",
            ).encode("utf-8-sig"),
            file_name="employment_period_comparison.csv",
            mime="text/csv",
        )

    with tab_trends:
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

        def filter_display_period(df: pd.DataFrame) -> pd.DataFrame:
            if period_months is None:
                return df.copy()

            return df.tail(period_months).copy()

        general_display_df = filter_display_period(general_df)
        part_display_df = filter_display_period(part_df)

        st.markdown("## 1. 何が起きたか")

        st.caption(
            "2020年平均を100として、月額賃金・労働時間・概算時間当たり賃金の変化を比較します。"
        )

        # 月額賃金指数
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
        st.caption(
            "指数は各就業形態の2020年平均＝100。"
            "指数の高さから一般・パートの賃金額の差は比較できません。"
        )

        # 総実労働時間指数
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
        st.caption(
            "平均労働時間の変化を示します。"
            "個人の勤務時間の変化や、減少の原因は特定できません。"
        )

        # 時間当たり賃金指数
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
        st.caption(
            "きまって支給する給与÷総実労働時間で算出した概算値です。"
            "契約上の時給とは異なります。"
        )

        st.markdown("## 2. 物価を考えるとどうか")
        st.caption("名目賃金を消費者物価指数で実質化し、購買力の変化を比較します。")

        # 実質月額賃金指数
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
        st.caption(
            "選択したCPIで実質化した値です。公式の実質賃金指数とは区別します。"
        )

        # 実質時間当たり賃金指数
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
        st.caption("時間当たり賃金を選択したCPIで実質化した値です。")

        st.markdown("## 3. 月額賃金の変化を分解")

        st.caption(
            "月額賃金の前年同月変化を、概算時間当たり賃金の変化と労働時間の変化に分解します。"
        )

        # 各就業形態で、まず分解可能な月を確認する。
        general_available = summarize_wage_change_decomposition(
            general_df,
            start_year=ANALYSIS_START_YEAR,
            end_year=ANALYSIS_END_YEAR,
        )
        part_available = summarize_wage_change_decomposition(
            part_df,
            start_year=ANALYSIS_START_YEAR,
            end_year=ANALYSIS_END_YEAR,
        )

        common_months = sorted(
            set(general_available["valid_months"])
            & set(part_available["valid_months"])
        )

        if not common_months:
            st.warning("一般・パートに共通する分解可能な月がありません。")
            st.stop()

        # 共通月だけを使い、比較用の要約を作成する。
        general_decomposition_summary = summarize_wage_change_decomposition(
            general_df,
            start_year=ANALYSIS_START_YEAR,
            end_year=ANALYSIS_END_YEAR,
            target_months=common_months,
        )
        part_decomposition_summary = summarize_wage_change_decomposition(
            part_df,
            start_year=ANALYSIS_START_YEAR,
            end_year=ANALYSIS_END_YEAR,
            target_months=common_months,
        )

        n_expected = general_decomposition_summary["n_expected_months"]
        excluded_months = general_decomposition_summary["excluded_months"]

        st.caption(
            f"期間要約の対象：一般・パート共通の{len(common_months)}か月"
            f"／対象期間の{n_expected}か月。"
            "各値は前年同月との対数変化に基づきます。"
        )

        if excluded_months:
            with st.expander("期間要約から除外した月"):
                st.write("、".join(excluded_months))

        st.altair_chart(
            create_decomposition_chart(
                general_display_df,
                "一般労働者：月額賃金変化の要因分解",
            ),
            width="stretch",
        )

        st.info(
            f"""
        **一般労働者：{ANALYSIS_START_YEAR}〜{ANALYSIS_END_YEAR}年の傾向**

        - 時間当たり賃金要因の平均：\
        **{general_decomposition_summary["mean_hourly_wage_contribution"]:+.2f}**
        - 労働時間要因の平均：\
        **{general_decomposition_summary["mean_working_hours_contribution"]:+.2f}**
        - 時間当たり賃金要因がプラスだった月：\
        **{general_decomposition_summary["hourly_positive_share_pct"]:.1f}%**
        - 労働時間要因がマイナスだった月：\
        **{general_decomposition_summary["hours_negative_share_pct"]:.1f}%**
        - 時間当たり賃金要因の絶対値が大きかった月：\
        **{general_decomposition_summary["hourly_dominant_share_pct"]:.1f}%**

        期間中の前年同月変化を平均した記述統計です。
        原因そのものを示すものではありません。
        """
        )

        st.altair_chart(
            create_decomposition_chart(
                part_display_df,
                "パートタイム労働者：月額賃金変化の要因分解",
            ),
            width="stretch",
        )

        st.info(
            f"""
        **パートタイム労働者：{ANALYSIS_START_YEAR}〜{ANALYSIS_END_YEAR}年の傾向**

        - 時間当たり賃金要因の平均：\
        **{part_decomposition_summary["mean_hourly_wage_contribution"]:+.2f}**
        - 労働時間要因の平均：\
        **{part_decomposition_summary["mean_working_hours_contribution"]:+.2f}**
        - 時間当たり賃金要因がプラスだった月：\
        **{part_decomposition_summary["hourly_positive_share_pct"]:.1f}%**
        - 労働時間要因がマイナスだった月：\
        **{part_decomposition_summary["hours_negative_share_pct"]:.1f}%**
        - 時間当たり賃金要因の絶対値が大きかった月：\
        **{part_decomposition_summary["hourly_dominant_share_pct"]:.1f}%**

        期間中の前年同月変化を平均した記述統計です。
        原因そのものを示すものではありません。
        """
        )

        general_hourly_dominant = general_decomposition_summary["hourly_dominant_share_pct"]
        part_hourly_dominant = part_decomposition_summary["hourly_dominant_share_pct"]

        st.markdown("#### 要因分解から見た違い")

        if part_hourly_dominant > general_hourly_dominant + 0.1:
            st.write(
                "パートタイム労働者では、一般労働者よりも"
                "時間当たり賃金要因の変動幅が労働時間要因を上回る月の割合が高く、"
                "月額賃金の変化が時間当たり賃金の変化により強く結び付いていた"
                "期間が多かったことが確認できます。"
            )
        elif general_hourly_dominant > part_hourly_dominant + 0.1:
            st.write(
                "一般労働者では、パートタイム労働者よりも"
                "時間当たり賃金要因の変動幅が労働時間要因を上回る月の割合が高く、"
                "月額賃金の変化が時間当たり賃金の変化により強く結び付いていた"
                "期間が多かったことが確認できます。"
            )
        else:
            st.write(
                "時間当たり賃金要因が労働時間要因を上回る月の割合は、"
                "一般労働者とパートタイム労働者でおおむね同程度でした。"
            )

        st.caption(
            "棒は前年同月からの月額賃金変化を、"
            "時間当たり賃金要因と労働時間要因に分解したものです。"
            "値は通常の前年比ではなく、対数変化を100倍した値です。"
        )

    with tab_data:
        comparison_output_df = create_comparison_output_dataframe(
            general_df,
            part_df,
            establishment_size=establishment_size,
            cpi_series=selected_series,
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

        export_columns = [
            "date",
            "employment_type",
            "establishment_size",
            "cpi_series",
            "wage_item",
            "working_hours_item",
            "industry",
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

        csv_data = (
            comparison_output_df[export_columns]
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

        st.markdown("#### Tableau用データ")

        st.caption(
            "事業所規模・CPI系列・雇用形態の全条件を含むCSVを生成します。"
            "Tableau側で各条件をフィルターして分析できます。"
        )

        if st.button("Tableau用CSVを生成"):
            try:
                cpi_dataframes = {
                    series_name: load_cpi_data(
                        app_id,
                        series_code,
                    )
                    for series_name, series_code in CPI_SERIES.items()
                }

                tableau_df = create_tableau_export_dataframe(
                    raw_df,
                    cpi_dataframes,
                )

                st.session_state["tableau_export_csv"] = tableau_df.to_csv(
                    index=False
                ).encode("utf-8-sig")

                st.session_state["tableau_export_rows"] = len(tableau_df)

            except (EStatAPIError, ValueError) as exc:
                st.error(str(exc))

        if "tableau_export_csv" in st.session_state:
            st.download_button(
                label="Tableau用CSVをダウンロード",
                data=st.session_state["tableau_export_csv"],
                file_name="employment_comparison_tableau.csv",
                mime="text/csv",
            )

            st.caption(
                f"{st.session_state['tableau_export_rows']:,}行のデータを生成しました。"
            )

    with st.expander("分析方法・注意事項・出典", expanded=False):
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

    with tab_data:
        st.subheader("再計算記録の保存")

        st.caption(
            "今回の計算に使用したデータ、丸め前の結果、保存済みのコードをZIPで保存します。"
        )

        # ダウンロード操作による不要な再実行を避ける。
        @st.fragment
        def render_snapshot_download():
            if st.button("再計算記録のZIPを作成"):
                captured_at = datetime.now(timezone.utc)
                timestamp = captured_at.strftime("%Y%m%dT%H%M%SZ")
                project_root = Path(__file__).resolve().parents[1]

                files = {}

                def add_dataframe(name, frame):
                    files[name] = frame.to_csv(
                        index=False,
                        float_format="%.17g",
                    ).encode("utf-8-sig")

                # ディスク上のCSVではなく、実際に計算へ渡した
                # 読込済みDataFrameを保存する。
                add_dataframe("inputs/raw_wage_loaded.csv", raw_df)
                add_dataframe("inputs/cpi_used.csv", cpi_df)

                add_dataframe("outputs/general_monthly.csv", general_df)
                add_dataframe("outputs/part_monthly.csv", part_df)
                add_dataframe(
                    "outputs/yearly_comparison.csv",
                    comparison_summary_df,
                )
                add_dataframe(
                    "outputs/aggregation_sensitivity.csv",
                    pd.DataFrame(sensitivity_rows),
                )

                # 保存済みのソースと依存関係を収録する。
                source_paths = sorted(
                    (project_root / "src").rglob("*.py")
                )
                source_paths.append(Path(__file__).resolve())

                for filename in ["pyproject.toml", "uv.lock"]:
                    path = project_root / filename
                    if path.exists():
                        source_paths.append(path)

                for path in source_paths:
                    relative = path.relative_to(project_root).as_posix()
                    files[f"code/{relative}"] = path.read_bytes()

                metadata = {
                    "snapshot_created_at_utc": captured_at.isoformat(),
                    "analysis_conditions": {
                        "industry": "調査産業計",
                        "establishment_size": establishment_size,
                        "establishment_size_code": selected_size_code,
                        "employment_types": {
                            "1": "一般労働者",
                            "2": "パートタイム労働者",
                        },
                        "wage_item": "きまって支給する給与",
                        "working_hours_item": "総実労働時間",
                        "start_year": ANALYSIS_START_YEAR,
                        "end_year": ANALYSIS_END_YEAR,
                        "index_base_year": WAGE_BASE_YEAR,
                        "annual_aggregation": "monthly_arithmetic_mean",
                    },
                    "cpi": {
                        "series": selected_series,
                        "stats_data_id": CPI_STATS_DATA_ID,
                        "filters": {
                            **CPI_BASE_FILTERS,
                            "cdCat01": selected_series_code,
                        },
                        "retrieved_at": None,
                        "note": (
                            "取得日時は未記録。保存日時とは区別する。"
                            "実際に使用した整形済み月次データを収録。"
                        ),
                    },
                    "wage_input": {
                        "configured_path": str(WAGE_DATA_PATH),
                        "retrieved_at": None,
                        "note": (
                            "原本CSVのバイト列ではなく、"
                            "実際に使用した読込済みDataFrameを収録。"
                        ),
                    },
                    "runtime": {
                        "python": platform.python_version(),
                        "packages": {
                            name: version(name)
                            for name in [
                                "pandas",
                                "numpy",
                                "streamlit",
                                "altair",
                                "requests",
                            ]
                        },
                    },
                    "source_note": (
                        "ZIP作成時の保存済みソースを収録。"
                        "編集内容を保存し、アプリを再起動してから作成する。"
                    ),
                    "files": {
                        name: {
                            "sha256": hashlib.sha256(data).hexdigest(),
                            "bytes": len(data),
                        }
                        for name, data in files.items()
                    },
                }

                files["metadata.json"] = json.dumps(
                    metadata,
                    ensure_ascii=False,
                    indent=2,
                ).encode("utf-8")

                buffer = io.BytesIO()
                with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
                    for name, data in files.items():
                        archive.writestr(name, data)

                st.download_button(
                    "再計算記録のZIPをダウンロード",
                    data=buffer.getvalue(),
                    file_name=f"employment_snapshot_{timestamp}.zip",
                    mime="application/zip",
                    on_click="ignore",
                )

        render_snapshot_download()

if __name__ == "__main__":
    main()
