from pathlib import Path

import streamlit as st

from check_age_sensitivity import (
    create_annual_wage_dataframe,
)
from real_wage_dashboard.config import (
    CPI_SERIES,
    WAGE_DATA_PATH,
)
from real_wage_dashboard.cpi_analysis import (
    prepare_annual_cpi,
)
from real_wage_dashboard.cpi_service import (
    load_cpi_dataframe,
)
from real_wage_dashboard.take_home_analysis import (
    add_deduction_component_rates,
    add_real_take_home_metrics,
    calculate_take_home_time_series,
    create_burden_three_factor_shapley_decomposition,
    create_deduction_burden_change_summary,
    create_real_take_home_four_factor_shapley_decomposition,
    create_take_home_period_log_decomposition,
)
from real_wage_dashboard.take_home_service import (
    load_take_home_rule_tables,
)
from real_wage_dashboard.wage_service import (
    load_wage_csv,
)


START_YEAR = 1990
END_YEAR = 2025

PERIODS = [
    (1990, 2000),
    (2000, 2010),
    (2010, 2020),
    (2020, 2025),
    (2015, 2025),
    (1990, 2025),
]

OUTPUT_DIR = Path(
    "data/snapshots"
)


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ----------------------------------------
    # 1. 賃金
    # ----------------------------------------

    raw_wage_df = load_wage_csv(
        WAGE_DATA_PATH
    )

    annual_wage_df = (
        create_annual_wage_dataframe(
            raw_wage_df
        )
    )

    # ----------------------------------------
    # 2. CPI
    # ----------------------------------------

    app_id = st.secrets[
        "ESTAT_APP_ID"
    ]

    cpi_df = load_cpi_dataframe(
        app_id=app_id,
        series_code=CPI_SERIES[
            "持家の帰属家賃を除く総合"
        ],
    )

    annual_cpi_df = prepare_annual_cpi(
        cpi_df=cpi_df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    # ----------------------------------------
    # 3. 制度表
    # ----------------------------------------

    rules = (
        load_take_home_rule_tables()
    )

    # ----------------------------------------
    # 4. 主系列
    # ----------------------------------------

    main_series = (
        calculate_take_home_time_series(
            annual_wage_df=annual_wage_df,
            rule_tables=rules,
            start_year=START_YEAR,
            end_year=END_YEAR,
            sex="male",
            age=35,
            timing="income_year",
        )
    )

    main_series = (
        add_real_take_home_metrics(
            take_home_df=main_series,
            annual_cpi_df=annual_cpi_df,
            base_year=START_YEAR,
        )
    )

    main_series = (
        add_deduction_component_rates(
            main_series
        )
    )

    # ----------------------------------------
    # 5. 期間別対数分解
    # ----------------------------------------

    log_decomposition = (
        create_take_home_period_log_decomposition(
            df=main_series,
            periods=PERIODS,
        )
    )

    # ----------------------------------------
    # 6. 控除項目別負担率変化
    # ----------------------------------------

    burden_change = (
        create_deduction_burden_change_summary(
            df=main_series,
            periods=PERIODS,
        )
    )

    # ----------------------------------------
    # 7. W・T・S Shapley
    # ----------------------------------------

    burden_shapley = (
        create_burden_three_factor_shapley_decomposition(
            annual_wage_df=annual_wage_df,
            rule_tables=rules,
            periods=PERIODS,
            sex="male",
        )
    )

    # ----------------------------------------
    # 8. W・T・S・P Shapley
    # ----------------------------------------

    real_shapley = (
        create_real_take_home_four_factor_shapley_decomposition(
            annual_wage_df=annual_wage_df,
            annual_cpi_df=annual_cpi_df,
            rule_tables=rules,
            periods=PERIODS,
            sex="male",
        )
    )

    # ----------------------------------------
    # 9. CSV保存
    # ----------------------------------------

    outputs = {
        "take_home_main_series.csv":
            main_series,
        "take_home_period_log_decomposition.csv":
            log_decomposition,
        "take_home_burden_change_summary.csv":
            burden_change,
        "take_home_burden_shapley_3factor.csv":
            burden_shapley,
        "take_home_real_shapley_4factor.csv":
            real_shapley,
    }

    for filename, df in outputs.items():
        path = (
            OUTPUT_DIR
            / filename
        )

        df.to_csv(
            path,
            index=False,
        )

        print(
            f"saved: {path} "
            f"({len(df)} rows)"
        )

    # ----------------------------------------
    # 10. 回帰確認
    # ----------------------------------------

    selected = main_series.loc[
        main_series["year"].isin(
            [
                1990,
                2015,
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
    ]

    print(
        "\n=== 主系列確認 ==="
    )

    print(
        selected.to_string(
            index=False,
            float_format=lambda x:
                f"{x:,.6f}",
        )
    )

    print(
        "\n=== 1990→2025 "
        "4要因Shapley ==="
    )

    print(
        real_shapley.loc[
            real_shapley[
                "period"
            ] == "1990→2025"
        ].to_string(
            index=False,
            float_format=lambda x:
                f"{x:,.6f}",
        )
    )


if __name__ == "__main__":
    main()
