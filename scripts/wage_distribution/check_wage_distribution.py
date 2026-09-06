from pathlib import Path

import streamlit as st

from real_wage_dashboard.cpi_service import load_cpi_dataframe
from real_wage_dashboard.minimum_wage_analysis import prepare_annual_cpi
from real_wage_dashboard.wage_distribution_analysis import (
    add_real_wage_distribution,
    build_wage_distribution_analysis,
    summarize_wage_distribution_change,
)
from real_wage_dashboard.wage_distribution_service import (
    load_wage_distribution_history,
)

DATA_DIR = Path("data/raw/wage_distribution")

START_YEAR = 2015
END_YEAR = 2025
BASE_YEAR = 2015

CPI_SERIES_CODE = "0163"


def main() -> None:
    # 1. 賃金分布データ読み込み
    distribution_df = load_wage_distribution_history(
        data_dir=DATA_DIR,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    print("=== 賃金分布 元データ ===")
    print(distribution_df.to_string(index=False))
    print()

    # 2. 名目分布分析
    analysis = build_wage_distribution_analysis(
        distribution_df,
        base_year=BASE_YEAR,
    )

    print("=== 名目賃金分布分析 ===")
    print(
        analysis[
            [
                "year",
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
    print()

    # 3. 2015→2025変化率
    summary = summarize_wage_distribution_change(
        distribution_df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    print("=== 2015→2025 分位別変化 ===")
    print(summary.to_string(index=False))
    print()

    # 4. CPI取得
    #
    # ESTAT_APP_ID は既存実装と同様、
    # .streamlit/secrets.toml 等から取得する想定。

    app_id = st.secrets["ESTAT_APP_ID"]

    cpi_raw = load_cpi_dataframe(
        app_id=app_id,
        series_code=CPI_SERIES_CODE,
    )

    annual_cpi = prepare_annual_cpi(
        cpi_raw,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    print("=== 年平均CPI ===")
    print(annual_cpi.to_string(index=False))
    print()

    # 5. 実質分位賃金
    real_analysis = add_real_wage_distribution(
        analysis,
        annual_cpi,
        base_year=BASE_YEAR,
    )

    print("=== 名目・実質 分位指数 ===")
    print(
        real_analysis[
            [
                "year",
                "cpi",
                "p10_index",
                "real_p10_index",
                "p25_index",
                "real_p25_index",
                "p50_index",
                "real_p50_index",
                "p75_index",
                "real_p75_index",
                "p90_index",
                "real_p90_index",
            ]
        ].to_string(index=False)
    )
    print()

    # 6. 2025年だけ確認
    end = real_analysis[real_analysis["year"] == END_YEAR].iloc[0]

    print(f"=== {END_YEAR}年 主要結果 ===")
    print(f"P10: 名目指数={end['p10_index']:.2f}, 実質指数={end['real_p10_index']:.2f}")
    print(f"P25: 名目指数={end['p25_index']:.2f}, 実質指数={end['real_p25_index']:.2f}")
    print(f"P50: 名目指数={end['p50_index']:.2f}, 実質指数={end['real_p50_index']:.2f}")
    print(f"P75: 名目指数={end['p75_index']:.2f}, 実質指数={end['real_p75_index']:.2f}")
    print(f"P90: 名目指数={end['p90_index']:.2f}, 実質指数={end['real_p90_index']:.2f}")

    print()
    print(
        f"P90/P10: "
        f"{analysis.loc[analysis['year'] == START_YEAR, 'p90_p10'].iloc[0]:.3f}"
        f" → {end['p90_p10']:.3f}"
    )
    print(
        f"P50/P10: "
        f"{analysis.loc[analysis['year'] == START_YEAR, 'p50_p10'].iloc[0]:.3f}"
        f" → {end['p50_p10']:.3f}"
    )


if __name__ == "__main__":
    main()
