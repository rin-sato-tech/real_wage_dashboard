import streamlit as st

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.corporate_performance_analysis import (
    # calculate_corporate_wage_lag_correlations,
    # calculate_leave_one_year_out_correlations,
    calculate_period_corporate_wage_correlations,
    create_wage_fiscal_year_dataframe,
    merge_corporate_and_wage_time_series,
)
from real_wage_dashboard.corporate_performance_service import (
    load_corporate_performance_dataframe,
)
from real_wage_dashboard.industry_analysis import (
    create_industry_monthly_dataframe,
)
from real_wage_dashboard.wage_service import load_wage_csv


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    raw_df = load_wage_csv(WAGE_DATA_PATH)

    wage_monthly_df = create_industry_monthly_dataframe(
        raw_df,
        industry_code="TL",
    )

    wage_fiscal_df = create_wage_fiscal_year_dataframe(
        wage_monthly_df,
    )

    corporate_df = load_corporate_performance_dataframe(
        app_id=app_id,
        start_year=2000,
        end_year=2024,
    )

    merged_df = merge_corporate_and_wage_time_series(
        corporate_df,
        wage_fiscal_df,
    )

    # display_columns = [
    #     "fiscal_year",
    #     "labor_productivity_yoy_pct",
    #     "personnel_expenses_per_employee_yoy_pct",
    #     "ordinary_profit_margin_change_pct_point",
    #     "monthly_wage_yoy_pct",
    #     "hourly_wage_yoy_pct",
    # ]

    # lag_df = calculate_corporate_wage_lag_correlations(
    #     merged_df,
    #     max_lag=2,
    # )

    # print()
    # print("long-term lag correlations:")
    # print(lag_df.to_string(index=False))

    # sensitivity_df = calculate_leave_one_year_out_correlations(merged_df)

    # print()
    # print("leave-one-year-out correlations:")
    # print(sensitivity_df.to_string(index=False))

    period_df = calculate_period_corporate_wage_correlations(
        merged_df,
        periods=[
            (2000, 2012),
            (2013, 2019),
            (2020, 2024),
        ],
    )

    print()
    print("period correlations:")
    print(period_df.to_string(index=False))


if __name__ == "__main__":
    main()
