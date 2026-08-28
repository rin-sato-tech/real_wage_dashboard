import streamlit as st

from real_wage_dashboard.corporate_performance_service import (
    load_corporate_performance_dataframe,
)


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    df = load_corporate_performance_dataframe(
        app_id=app_id,
        start_year=2000,
        end_year=2024,
    )

    print("shape:")
    print(df.shape)

    print("\nyears:")
    print(df["fiscal_year"].tolist())

    print("\nperiod:")
    print(
        df["fiscal_year"].min(),
        "->",
        df["fiscal_year"].max(),
    )

    print("\nmissing values:")
    print(df.isna().sum())

    display_columns = [
        "fiscal_year",
        "labor_productivity",
        "personnel_expenses_per_employee",
        "labor_share",
        "operating_profit_margin",
        "ordinary_profit_margin",
    ]

    print("\ndata:")
    print(df[display_columns].to_string(index=False))


if __name__ == "__main__":
    main()
