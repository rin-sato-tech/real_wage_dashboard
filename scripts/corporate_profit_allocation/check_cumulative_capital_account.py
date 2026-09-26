from __future__ import annotations

import streamlit as st

from real_wage_dashboard.corporate_profit_allocation_analysis import (
    calculate_cumulative_capital_account,
    summarize_cumulative_capital_account,
)
from real_wage_dashboard.macro_distribution_analysis import (
    validate_nonfinancial_capital_account_identity,
)
from real_wage_dashboard.macro_distribution_service import (
    load_nonfinancial_capital_account,
)


START_YEAR = 2015
END_YEAR = 2024


def get_app_id() -> str:
    try:
        return str(
            st.secrets["ESTAT_APP_ID"]
        )

    except KeyError as exc:
        raise RuntimeError(
            ".streamlit/secrets.tomlに"
            "ESTAT_APP_IDを設定してください。"
        ) from exc


def main() -> None:
    app_id = get_app_id()

    capital_df = load_nonfinancial_capital_account(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    validate_nonfinancial_capital_account_identity(
        capital_df
    )

    cumulative_df = (
        calculate_cumulative_capital_account(
            capital_df,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    summary_df = (
        summarize_cumulative_capital_account(
            capital_df,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    print()
    print("=" * 100)
    print("年次・累積資本勘定")
    print("=" * 100)

    columns = [
        "fiscal_year",
        "net_saving",
        "net_capital_formation",
        "net_lending_capital_account",
        "cumulative_net_saving",
        "cumulative_net_capital_formation",
        "cumulative_net_lending_capital_account",
    ]

    print(
        cumulative_df[
            columns
        ].to_string(
            index=False
        )
    )

    print()
    print("=" * 100)
    print("2015～2024年度 累積要約")
    print("=" * 100)

    print(
        summary_df.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
