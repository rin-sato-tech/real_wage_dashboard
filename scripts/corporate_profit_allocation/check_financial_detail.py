from __future__ import annotations

import streamlit as st

from real_wage_dashboard.corporate_profit_allocation_service import (
    load_nonfinancial_financial_assets_detail,
    load_nonfinancial_financial_liabilities_detail,
)


START_YEAR = 2015
END_YEAR = 2024


ASSET_OTHER_COMPONENTS = [
    "fiscal_investment_fund_deposits_assets",
    "entrusted_funds_assets",
    "trade_credit_assets",
    "accounts_receivable_assets",
    "direct_investment_assets",
    "foreign_portfolio_investment_assets",
    "other_external_claims_assets",
    "other_assets",
]

LIABILITY_OTHER_COMPONENTS = [
    "fiscal_investment_fund_deposits_liabilities",
    "entrusted_funds_liabilities",
    "trade_credit_liabilities",
    "accounts_payable_liabilities",
    "direct_investment_liabilities",
    "foreign_portfolio_investment_liabilities",
    "other_external_liabilities",
    "other_liabilities_detail",
]


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

    assets = load_nonfinancial_financial_assets_detail(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    liabilities = (
        load_nonfinancial_financial_liabilities_detail(
            app_id=app_id,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    print()
    print("=" * 100)
    print("金融資産取引・大分類累計")
    print("=" * 100)

    asset_major = [
        "cash_deposits_assets",
        "loans_assets",
        "debt_securities_assets",
        "equity_investment_fund_assets",
        "insurance_pension_guarantee_assets",
        "financial_derivatives_assets",
        "other_financial_assets",
        "financial_assets_total",
        "net_lending_financial_detail",
    ]

    for column in asset_major:
        print(
            f"{column}: "
            f"{assets[column].sum() / 1000:.4f}兆円"
        )

    print()
    print("=" * 100)
    print("その他の金融資産・累積内訳")
    print("=" * 100)

    for column in ASSET_OTHER_COMPONENTS:
        print(
            f"{column}: "
            f"{assets[column].sum() / 1000:.4f}兆円"
        )

    asset_other_sum = (
        assets[ASSET_OTHER_COMPONENTS]
        .sum(axis=1)
        .sum()
    )

    published_asset_other = (
        assets["other_financial_assets"].sum()
    )

    print()
    print(
        "内訳合計:",
        asset_other_sum / 1000,
        "兆円",
    )
    print(
        "公表その他金融資産:",
        published_asset_other / 1000,
        "兆円",
    )
    print(
        "残差:",
        asset_other_sum - published_asset_other,
        "10億円",
    )

    print()
    print("=" * 100)
    print("その他の金融負債・累積内訳")
    print("=" * 100)

    for column in LIABILITY_OTHER_COMPONENTS:
        print(
            f"{column}: "
            f"{liabilities[column].sum() / 1000:.4f}兆円"
        )

    liability_other_sum = (
        liabilities[LIABILITY_OTHER_COMPONENTS]
        .sum(axis=1)
        .sum()
    )

    published_liability_other = (
        liabilities[
            "other_financial_liabilities"
        ].sum()
    )

    print()
    print(
        "内訳合計:",
        liability_other_sum / 1000,
        "兆円",
    )
    print(
        "公表その他金融負債:",
        published_liability_other / 1000,
        "兆円",
    )
    print(
        "残差:",
        (
            liability_other_sum
            - published_liability_other
        ),
        "10億円",
    )


if __name__ == "__main__":
    main()
