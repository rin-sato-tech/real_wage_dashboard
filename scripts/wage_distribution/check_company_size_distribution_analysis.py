from __future__ import annotations

from pathlib import Path

import streamlit as st

from real_wage_dashboard.cpi_analysis import prepare_annual_cpi
from real_wage_dashboard.cpi_service import load_cpi_dataframe
from real_wage_dashboard.wage_distribution_analysis import (
    BASE_YEAR,
    add_real_wage_distribution_by_group,
    build_wage_distribution_analysis_by_company_size,
)
from real_wage_dashboard.wage_distribution_service import (
    load_wage_distribution_history_by_company_size,
)

DATA_DIR = Path("data/raw/wage_distribution")


def get_app_id() -> str:
    app_id = st.secrets["ESTAT_APP_ID"]

    if not app_id:
        raise RuntimeError("ESTAT_APP_ID が設定されていません。")

    return app_id


def main() -> None:
    app_id = get_app_id()

    history = load_wage_distribution_history_by_company_size(
        DATA_DIR,
        start_year=2015,
        end_year=2025,
    )

    analysis = build_wage_distribution_analysis_by_company_size(
        history,
        base_year=BASE_YEAR,
    )

    print()
    print("=== 企業規模別 分位指数・格差 ===")

    print(
        analysis[
            [
                "year",
                "company_size",
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

    cpi_df = load_cpi_dataframe(
        app_id=app_id,
        series_code="0163",
    )

    annual_cpi = prepare_annual_cpi(cpi_df)

    annual_cpi = annual_cpi[
        annual_cpi["year"].between(
            2015,
            2025,
        )
    ].copy()

    real_analysis = add_real_wage_distribution_by_group(
        analysis,
        annual_cpi,
        group_columns=["company_size"],
        base_year=BASE_YEAR,
    )

    print()
    print("=== 企業規模別 実質分位指数 ===")

    print(
        real_analysis[
            [
                "year",
                "company_size",
                "real_p10_index",
                "real_p25_index",
                "real_p50_index",
                "real_p75_index",
                "real_p90_index",
            ]
        ].to_string(index=False)
    )

    print()
    print("=== 2025 企業規模別 実質分位指数 ===")

    print(
        real_analysis[real_analysis["year"] == 2025][
            [
                "company_size",
                "real_p10_index",
                "real_p25_index",
                "real_p50_index",
                "real_p75_index",
                "real_p90_index",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
