import streamlit as st

from real_wage_dashboard.config import CORPORATE_INDUSTRY_NAMES
from real_wage_dashboard.corporate_performance_analysis import (
    create_industry_comparison_dataframe,
)
from real_wage_dashboard.corporate_performance_service import (
    load_corporate_performance_by_industry,
)


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    dataframes = load_corporate_performance_by_industry(
        app_id=app_id,
    )

    comparison_df = create_industry_comparison_dataframe(
        dataframes,
    )

    comparison_df["industry_name"] = comparison_df["industry"].map(
        CORPORATE_INDUSTRY_NAMES
    )

    display_columns = [
        "industry",
        "industry_name",
        "labor_productivity_growth_pct",
        "personnel_expenses_per_employee_growth_pct",
        "growth_gap_pct_point",
        "labor_share_change_pct_point",
        "operating_profit_margin_change_pct_point",
        "ordinary_profit_margin_change_pct_point",
    ]

    print()
    print("industry comparison:")
    print(
        comparison_df[display_columns]
        .sort_values(
            "labor_productivity_growth_pct",
            ascending=False,
        )
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
