import streamlit as st

from real_wage_dashboard.config import (
    CORPORATE_INDUSTRY_MAPPING,
    CORPORATE_INDUSTRY_NAMES,
    WAGE_DATA_PATH,
)
from real_wage_dashboard.corporate_performance_analysis import (
    # calculate_corporate_wage_industry_correlations,
    calculate_leave_one_out_correlations,
    merge_corporate_and_wage_industry_comparison,
)
from real_wage_dashboard.corporate_performance_analysis import (
    create_industry_comparison_dataframe as create_corporate_industry_comparison,
)
from real_wage_dashboard.corporate_performance_service import (
    load_corporate_performance_by_industry,
)
from real_wage_dashboard.industry_analysis import (
    create_industry_comparison_dataframe as create_wage_industry_comparison,
)
from real_wage_dashboard.wage_service import load_wage_csv


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    raw_df = load_wage_csv(WAGE_DATA_PATH)

    corporate_dataframes = load_corporate_performance_by_industry(
        app_id=app_id,
    )

    corporate_comparison_df = create_corporate_industry_comparison(
        corporate_dataframes,
        start_year=2015,
        end_year=2024,
    )

    industry_codes = list(CORPORATE_INDUSTRY_MAPPING.keys())

    wage_comparison_df = create_wage_industry_comparison(
        raw_df,
        industry_codes=industry_codes,
        start_year=2015,
        end_year=2024,
    )

    merged_df = merge_corporate_and_wage_industry_comparison(
        corporate_comparison_df,
        wage_comparison_df,
    )

    merged_df["industry_name"] = merged_df["industry"].map(CORPORATE_INDUSTRY_NAMES)

    # display_columns = [
    #     "industry",
    #     "industry_name",
    #     "labor_productivity_growth_pct",
    #     "personnel_expenses_per_employee_growth_pct",
    #     "monthly_wage_change_pct",
    #     "hourly_wage_change_pct",
    #     "total_hours_change_pct",
    #     "labor_share_change_pct_point",
    #     "ordinary_profit_margin_change_pct_point",
    # ]

    # correlations = calculate_corporate_wage_industry_correlations(
    #     merged_df
    # )

    sensitivity_df = calculate_leave_one_out_correlations(merged_df)

    sensitivity_df["industry_name"] = sensitivity_df["excluded_industry"].map(
        CORPORATE_INDUSTRY_NAMES
    )

    print()
    print("leave-one-out correlations:")
    print(
        sensitivity_df[
            [
                "excluded_industry",
                "industry_name",
                "productivity_vs_monthly_wage",
                "productivity_vs_hourly_wage",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
