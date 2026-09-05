from pathlib import Path

import pandas as pd
import streamlit as st

from real_wage_dashboard.config import CPI_SERIES
from real_wage_dashboard.cpi_service import load_cpi_dataframe
from real_wage_dashboard.real_wage_decomposition_analysis import (
    build_cpi_sensitivity,
    build_real_wage_decomposition_data,
    create_complete_annual_cpi,
    extract_annual_index,
    extract_annual_published_yoy,
    summarize_chained_period_change,
    validate_analysis_results,
)

DATA_DIR = Path("data/raw/real_wage_decomposition")

WAGE_INDEX_PATH = DATA_DIR / "wage_index_total_5plus.xls"
OFFICIAL_REAL_WAGE_INDEX_PATH = DATA_DIR / "official_real_wage_index_5plus.xls"

MAIN_CPI_SERIES = "持家の帰属家賃を除く総合"
SENSITIVITY_CPI_SERIES = "総合"

START_YEAR = 2015
END_YEAR = 2025


def print_main_period(period: pd.DataFrame) -> None:
    columns = [
        "year",
        "nominal_wage_index",
        "published_nominal_yoy_pct",
        "cpi",
        "cpi_yoy_pct",
        "official_real_wage_index",
        "published_real_yoy_pct",
        "wage_price_gap",
        "mechanical_real_yoy_pct",
        "nominal_log_contribution",
        "price_log_contribution",
        "real_log_change",
    ]

    print("=== 2015～2025年：主分析 ===")
    print(
        period[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )


def print_index_validation(period: pd.DataFrame) -> None:
    columns = [
        "year",
        "nominal_wage_index",
        "calculated_nominal_yoy_pct",
        "published_nominal_yoy_pct",
        "calculated_real_wage_index",
        "official_real_wage_index",
        "real_index_difference",
        "calculated_real_yoy_pct",
        "published_real_yoy_pct",
    ]

    print("\n=== 指数・公表前年比の検証 ===")
    print(
        period[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    print(
        "\n実質賃金指数 最大絶対差:",
        f"{period['real_index_difference'].abs().max():.6f}",
    )

    row_2024 = period.loc[period["year"] == 2024]

    if len(row_2024) == 1:
        row = row_2024.iloc[0]

        print("\n=== 2024年の指数断層確認 ===")
        print(
            "名目賃金 指数から単純計算:",
            f"{row['calculated_nominal_yoy_pct']:.3f}%",
        )
        print(
            "名目賃金 公表前年比:",
            f"{row['published_nominal_yoy_pct']:.3f}%",
        )
        print(
            "実質賃金 指数から単純計算:",
            f"{row['calculated_real_yoy_pct']:.3f}%",
        )
        print(
            "実質賃金 公表前年比:",
            f"{row['published_real_yoy_pct']:.3f}%",
        )


def print_chained_summary(summary: pd.Series) -> None:
    print(
        f"\n=== {int(summary['start_year'])}"
        f"→{int(summary['end_year'])}年："
        "公表前年比連鎖による累積変化 ==="
    )

    display = pd.Series(
        {
            "名目賃金累積変化率 (%)": summary["nominal_change_pct"],
            "CPI累積変化率 (%)": summary["cpi_change_pct"],
            "実質賃金機械的累積変化率 (%)": summary["mechanical_real_change_pct"],
            "名目賃金累積対数寄与": summary["nominal_log_contribution"],
            "物価累積対数寄与": summary["price_log_contribution"],
            "実質賃金累積対数変化": summary["real_log_change"],
        }
    )

    print(
        display.to_string(
            float_format=lambda x: f"{x:.3f}",
        )
    )


def print_sensitivity(sensitivity_df: pd.DataFrame) -> None:
    period = sensitivity_df.loc[
        sensitivity_df["year"].between(START_YEAR, END_YEAR)
    ].copy()

    columns = [
        "year",
        "published_nominal_yoy_pct",
        "main_cpi_yoy_pct",
        "sensitivity_cpi_yoy_pct",
        "real_yoy_main_cpi_pct",
        "real_yoy_sensitivity_cpi_pct",
        "real_yoy_sensitivity_gap",
    ]

    print("\n=== CPI系列による感度分析 ===")
    print(
        period[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    wage_index_df = extract_annual_index(WAGE_INDEX_PATH)
    wage_yoy_df = extract_annual_published_yoy(WAGE_INDEX_PATH)

    official_real_index_df = extract_annual_index(OFFICIAL_REAL_WAGE_INDEX_PATH)
    official_real_yoy_df = extract_annual_published_yoy(OFFICIAL_REAL_WAGE_INDEX_PATH)

    main_cpi_monthly_df = load_cpi_dataframe(
        app_id=app_id,
        series_code=CPI_SERIES[MAIN_CPI_SERIES],
    )
    main_cpi_annual_df = create_complete_annual_cpi(main_cpi_monthly_df)

    sensitivity_cpi_monthly_df = load_cpi_dataframe(
        app_id=app_id,
        series_code=CPI_SERIES[SENSITIVITY_CPI_SERIES],
    )
    sensitivity_cpi_annual_df = create_complete_annual_cpi(sensitivity_cpi_monthly_df)

    analysis_df = build_real_wage_decomposition_data(
        wage_index_df=wage_index_df,
        wage_yoy_df=wage_yoy_df,
        official_real_index_df=official_real_index_df,
        official_real_yoy_df=official_real_yoy_df,
        cpi_annual_df=main_cpi_annual_df,
    )

    period = analysis_df.loc[analysis_df["year"].between(START_YEAR, END_YEAR)].copy()

    validate_analysis_results(
        analysis_df=analysis_df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    summary = summarize_chained_period_change(
        df=analysis_df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    sensitivity_df = build_cpi_sensitivity(
        wage_yoy_df=wage_yoy_df,
        main_cpi_df=main_cpi_annual_df,
        sensitivity_cpi_df=sensitivity_cpi_annual_df,
    )

    print_main_period(period)
    print_index_validation(period)
    print_chained_summary(summary)
    print_sensitivity(sensitivity_df)

    print("\n=== 検証結果 ===")
    print("検証: OK")


if __name__ == "__main__":
    main()
