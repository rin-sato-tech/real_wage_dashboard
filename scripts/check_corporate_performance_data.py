import streamlit as st

from real_wage_dashboard.corporate_performance_service import (
    load_corporate_performance_dataframe,
)


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    df = load_corporate_performance_dataframe(app_id=app_id)

    print()
    print("labor productivity validation:")
    print(
        df[
            [
                "fiscal_year",
                "labor_productivity",
                "calculated_labor_productivity",
                "labor_productivity_diff",
            ]
        ].to_string(index=False)
    )

    print()
    print("personnel expenses per employee:")
    print(
        df[
            [
                "fiscal_year",
                "personnel_expenses_per_employee",
                "labor_share",
            ]
        ].to_string(index=False)
    )

if __name__ == "__main__":
    main()
