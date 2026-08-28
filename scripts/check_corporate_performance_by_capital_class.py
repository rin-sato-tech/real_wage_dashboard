import streamlit as st

from real_wage_dashboard.config import CORPORATE_CAPITAL_CLASSES
from real_wage_dashboard.corporate_performance_analysis import (
    # create_capital_class_comparison_dataframe,
    create_period_comparison_summary,
)
from real_wage_dashboard.corporate_performance_service import (
    load_corporate_performance_dataframe,
)


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    target_capital_classes = {
        "大企業": CORPORATE_CAPITAL_CLASSES["大企業"],
        "中堅企業": CORPORATE_CAPITAL_CLASSES["中堅企業"],
        "中小企業": CORPORATE_CAPITAL_CLASSES["中小企業"],
    }

    dataframes = {}

    for capital_class, code in target_capital_classes.items():
        print(f"loading: {capital_class}")

        dataframes[capital_class] = load_corporate_performance_dataframe(
            app_id=app_id,
            capital_class_code=code,
        )

    # comparison_df = create_capital_class_comparison_dataframe(
    #     dataframes,
    # )

    periods = [
        (2015, 2019),
        (2019, 2020),
        (2020, 2024),
    ]

    print()
    print("capital class period comparison:")

    for capital_class, df in dataframes.items():
        print()
        print(f"[{capital_class}]")

        for start_year, end_year in periods:
            summary = create_period_comparison_summary(
                df,
                start_year=start_year,
                end_year=end_year,
            )

            print(
                f"{start_year} -> {end_year}: "
                f"productivity={summary['labor_productivity_growth_pct']:.2f}%, "
                f"personnel_per_employee="
                f"{summary['personnel_expenses_per_employee_growth_pct']:.2f}%, "
                f"gap={summary['growth_gap_pct_point']:.2f}pt, "
                f"labor_share="
                f"{summary['labor_share_change_pct_point']:.2f}pt, "
                f"operating_margin="
                f"{summary['operating_profit_margin_change_pct_point']:.2f}pt, "
                f"ordinary_margin="
                f"{summary['ordinary_profit_margin_change_pct_point']:.2f}pt"
            )


if __name__ == "__main__":
    main()
