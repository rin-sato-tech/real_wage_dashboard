from __future__ import annotations

import streamlit as st

from real_wage_dashboard.corporate_profit_allocation_analysis import (
    calculate_capital_financial_net_lending_discrepancy,
    calculate_cumulative_financial_account,
    summarize_cumulative_financial_account,
    summarize_cumulative_financial_components,
    validate_nonfinancial_financial_account_identity,
)
from real_wage_dashboard.macro_distribution_service import (
    load_nonfinancial_capital_account,
    load_nonfinancial_financial_account,
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

    financial_df = load_nonfinancial_financial_account(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    validate_nonfinancial_financial_account_identity(
        financial_df
    )

    discrepancy_df = (
        calculate_capital_financial_net_lending_discrepancy(
            capital_df,
            financial_df,
        )
    )

    cumulative_df = (
        calculate_cumulative_financial_account(
            financial_df,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    summary_df = (
        summarize_cumulative_financial_account(
            financial_df,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    print()
    print("=" * 100)
    print("資本勘定・金融勘定の純貸出開差")
    print("=" * 100)

    print(
        discrepancy_df.to_string(
            index=False
        )
    )

    latest = discrepancy_df.iloc[-1]

    # print()
    # print(
    #     "累積・資本勘定純貸出:",
    #     latest["cumulative_capital_net_lending"],
    # )

    # print(
    #     "累積・金融勘定純貸出:",
    #     latest["cumulative_financial_net_lending"],
    # )

    # print(
    #     "累積開差:",
    #     latest[
    #         "cumulative_capital_financial_discrepancy"
    #     ],
    # )

    components_df = (
        summarize_cumulative_financial_components(
            financial_df,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    print()
    print("=" * 100)
    print("2015～2024年度 金融勘定累積内訳")
    print("=" * 100)

    display_df = components_df.copy()

    display_df["cumulative_amount_trillion"] = (
        display_df["cumulative_amount"] / 1000
    )

    display_df["net_lending_contribution_trillion"] = (
        display_df["net_lending_contribution"] / 1000
    )

    print(
        display_df[
            [
                "side",
                "component_name",
                "cumulative_amount_trillion",
                "net_lending_contribution_trillion",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "金融勘定から再構成した累積純貸出:",
        components_df.attrs[
            "calculated_net_lending"
        ]
        / 1000,
        "兆円",
    )

    print(
        "公表累積純貸出:",
        components_df.attrs[
            "published_net_lending"
        ]
        / 1000,
        "兆円",
    )

    print(
        "残差:",
        components_df.attrs[
            "identity_residual"
        ],
        "10億円",
    )

    print()
    print(
        "累積金融資産取得:",
        summary_df.iloc[0][
            "cumulative_financial_assets_change"
        ]
        / 1000,
        "兆円",
    )

    print(
        "累積負債発生:",
        summary_df.iloc[0][
            "cumulative_liabilities_change"
        ]
        / 1000,
        "兆円",
    )

if __name__ == "__main__":
    main()
