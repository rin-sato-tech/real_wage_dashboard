from __future__ import annotations

from pathlib import Path

import streamlit as st

from real_wage_dashboard.config import CPI_SERIES
from real_wage_dashboard.cpi_analysis import prepare_annual_cpi
from real_wage_dashboard.cpi_service import load_cpi_dataframe
from real_wage_dashboard.wage_distribution_analysis import (
    BASE_YEAR,
    add_real_wage_distribution_by_group,
    build_wage_distribution_analysis_by_employment,
)
from real_wage_dashboard.wage_distribution_service import (
    load_wage_distribution_history_by_employment,
)

DATA_DIR = Path("data/raw/wage_distribution/employment")

MAIN_CPI_SERIES = "持家の帰属家賃を除く総合"
SENSITIVITY_CPI_SERIES = "総合"


def get_app_id() -> str:
    app_id = st.secrets["ESTAT_APP_ID"]

    if not app_id:
        raise RuntimeError("ESTAT_APP_ID が設定されていません。")

    return app_id


def main() -> None:
    app_id = get_app_id()

    # --------------------------------------------------
    # 1. 雇用形態別賃金分布 2015-2025
    # --------------------------------------------------

    employment_history = load_wage_distribution_history_by_employment(
        app_id=app_id,
        excel_data_dir=DATA_DIR,
    )

    print()
    print("=== 雇用形態別 賃金分布 ===")

    print(employment_history.to_string(index=False))

    print()
    print(
        "rows:",
        len(employment_history),
    )

    # --------------------------------------------------
    # 2. 名目分位指数・格差
    # --------------------------------------------------

    employment_analysis = build_wage_distribution_analysis_by_employment(
        employment_history,
        base_year=BASE_YEAR,
    )

    print()
    print("=== 雇用形態別 分位指数・格差 ===")

    print(
        employment_analysis[
            [
                "year",
                "employment",
                "p10_index",
                "p25_index",
                "p50_index",
                "p75_index",
                "p90_index",
                "p90_p10",
                "p90_p50",
                "p50_p10",
                "decile_dispersion",
                "quartile_dispersion",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------
    # 3. CPI取得・年次化
    # --------------------------------------------------

    cpi_df = load_cpi_dataframe(
        app_id=app_id,
        series_code=CPI_SERIES[MAIN_CPI_SERIES],
    )

    annual_cpi = prepare_annual_cpi(cpi_df)

    annual_cpi = annual_cpi[
        annual_cpi["year"].between(
            2015,
            2025,
        )
    ].copy()

    print()
    print("=== 年次CPI ===")

    print(
        annual_cpi[
            [
                "year",
                "cpi",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------
    # 4. 雇用形態別 実質分位指数
    # --------------------------------------------------

    employment_real_analysis = add_real_wage_distribution_by_group(
        employment_analysis,
        annual_cpi,
        group_columns=[
            "employment",
        ],
        base_year=BASE_YEAR,
    )

    print()
    print("=== 雇用形態別 実質分位指数 ===")

    print(
        employment_real_analysis[
            [
                "year",
                "employment",
                "real_p10_index",
                "real_p25_index",
                "real_p50_index",
                "real_p75_index",
                "real_p90_index",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------
    # 5. 2015 -> 2025 の変化
    # --------------------------------------------------

    print()
    print("=== 2015 -> 2025 名目変化率 ===")

    for employment in [
        "regular",
        "nonregular",
    ]:
        group = employment_analysis[employment_analysis["employment"] == employment]

        start = group[group["year"] == 2015].iloc[0]

        end = group[group["year"] == 2025].iloc[0]

        print()
        print(f"[{employment}]")

        for column in [
            "p10",
            "p25",
            "p50",
            "p75",
            "p90",
        ]:
            change = (end[column] / start[column] - 1) * 100

            print(f"{column}: {change:.2f}%")

    # --------------------------------------------------
    # 6. 2025年 実質指数
    # --------------------------------------------------

    print()
    print("=== 2025 雇用形態別 実質分位指数 ===")

    result_2025 = employment_real_analysis[employment_real_analysis["year"] == 2025][
        [
            "employment",
            "real_p10_index",
            "real_p25_index",
            "real_p50_index",
            "real_p75_index",
            "real_p90_index",
        ]
    ]

    print(result_2025.to_string(index=False))


if __name__ == "__main__":
    main()
