import streamlit as st

from real_wage_dashboard.corporate_performance_analysis import (
    create_corporate_comparison_dataframe,
    create_corporate_yearly_change_dataframe,
    create_period_comparison_summary,
    create_productivity_compensation_summary,
)
from real_wage_dashboard.corporate_performance_service import (
    load_corporate_performance_dataframe,
)


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    corporate_df = load_corporate_performance_dataframe(app_id=app_id)

    comparison_df = create_corporate_comparison_dataframe(corporate_df)

    summary_df = create_productivity_compensation_summary(comparison_df)

    yearly_change_df = create_corporate_yearly_change_dataframe(corporate_df)

    periods = [
        (2015, 2019),
        (2019, 2020),
        (2020, 2024),
    ]

    for start_year, end_year in periods:
        summary = create_period_comparison_summary(
            corporate_df,
            start_year=start_year,
            end_year=end_year,
        )
        print(summary)


if __name__ == "__main__":
    main()