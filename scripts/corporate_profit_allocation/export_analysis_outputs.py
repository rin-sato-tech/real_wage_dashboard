from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from real_wage_dashboard.corporate_profit_allocation_analysis import (
    add_corporate_accounting_metrics,
    add_nonfinancial_disposable_income_identity,
    add_nonfinancial_primary_income_metrics,
    add_nonfinancial_saving_identity,
    calculate_capital_financial_net_lending_discrepancy,
    calculate_corporate_stock_continuity,
    calculate_cumulative_capital_account,
    calculate_stock_change_reconciliation,
    summarize_corporate_retained_earnings_bridge,
    summarize_cumulative_capital_account,
    summarize_cumulative_financial_components,
)
from real_wage_dashboard.corporate_profit_allocation_service import (
    load_corporate_profit_allocation,
    load_nonfinancial_balance_sheet,
    load_nonfinancial_financial_assets_detail,
    load_nonfinancial_financial_liabilities_detail,
    load_nonfinancial_other_volume_changes,
    load_nonfinancial_primary_income,
    load_nonfinancial_revaluation,
    load_nonfinancial_secondary_distribution,
    load_nonfinancial_use_income,
)
from real_wage_dashboard.macro_distribution_service import (
    load_nonfinancial_capital_account,
    load_nonfinancial_financial_account,
)


START_YEAR = 2015
END_YEAR = 2024

STOCK_START_YEAR = 2014
STOCK_END_YEAR = 2024

OUTPUT_DIR = Path(
    "outputs/analysis/corporate_profit_allocation"
)


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


def save_csv(
    df: pd.DataFrame,
    filename: str,
) -> None:
    path = OUTPUT_DIR / filename

    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"saved: {path} "
        f"({len(df)} rows)"
    )


def create_income_chain(
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    use_income: pd.DataFrame,
) -> pd.DataFrame:
    """所得形成から純貯蓄までの主要系列を1表にまとめる。"""

    primary_metrics = (
        add_nonfinancial_primary_income_metrics(
            primary
        )
    )

    secondary_metrics = (
        add_nonfinancial_disposable_income_identity(
            secondary
        )
    )

    saving_metrics = (
        add_nonfinancial_saving_identity(
            use_income
        )
    )

    result = primary_metrics[
        [
            "fiscal_year",
            "net_operating_surplus",
            "property_income_received",
            "property_income_paid",
            "net_property_income",
            "interest_received",
            "interest_paid",
            "net_interest_income",
            "dividends_received",
            "dividends_paid",
            "net_dividend_income",
            "reinvested_earnings_received",
            "reinvested_earnings_paid",
            "net_reinvested_earnings_income",
            "net_primary_income_balance",
        ]
    ].copy()

    result = result.merge(
        secondary_metrics[
            [
                "fiscal_year",
                "current_taxes_paid",
                "income_taxes_paid",
                "other_current_taxes_paid",
                "other_social_insurance_nonpension_benefits_paid",
                "other_current_transfers_paid",
                "imputed_employer_social_contributions_received",
                "other_current_transfers_received",
                "net_disposable_income",
            ]
        ],
        on="fiscal_year",
        how="inner",
    )

    result = result.merge(
        saving_metrics[
            [
                "fiscal_year",
                "net_saving",
                "gross_saving",
            ]
        ],
        on="fiscal_year",
        how="inner",
    )

    return result


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    app_id = get_app_id()

    # =========================================================
    # 1. 所得形成 → 純貯蓄
    # =========================================================

    primary = load_nonfinancial_primary_income(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    secondary = (
        load_nonfinancial_secondary_distribution(
            app_id=app_id,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    use_income = load_nonfinancial_use_income(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    income_chain = create_income_chain(
        primary,
        secondary,
        use_income,
    )

    save_csv(
        income_chain,
        "01_income_chain.csv",
    )

    # =========================================================
    # 2. 資本勘定
    # =========================================================

    capital_account = (
        load_nonfinancial_capital_account(
            app_id=app_id,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    cumulative_capital = (
        calculate_cumulative_capital_account(
            capital_account,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    save_csv(
        cumulative_capital,
        "02_capital_account_cumulative.csv",
    )

    capital_summary = (
        summarize_cumulative_capital_account(
            capital_account,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    save_csv(
        capital_summary,
        "02b_capital_account_summary.csv",
    )

    # =========================================================
    # 3. 資本勘定 vs 金融勘定
    # =========================================================

    financial_account = (
        load_nonfinancial_financial_account(
            app_id=app_id,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    discrepancy = (
        calculate_capital_financial_net_lending_discrepancy(
            capital_account,
            financial_account,
        )
    )

    save_csv(
        discrepancy,
        "03_capital_financial_discrepancy.csv",
    )

    # =========================================================
    # 4. 金融勘定累積内訳
    # =========================================================

    financial_components = (
        summarize_cumulative_financial_components(
            financial_account,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    save_csv(
        financial_components,
        "04_financial_account_components.csv",
    )

    # =========================================================
    # 5・6. 詳細金融取引
    # =========================================================

    financial_assets_detail = (
        load_nonfinancial_financial_assets_detail(
            app_id=app_id,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    financial_liabilities_detail = (
        load_nonfinancial_financial_liabilities_detail(
            app_id=app_id,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    save_csv(
        financial_assets_detail,
        "05_financial_detail_assets.csv",
    )

    save_csv(
        financial_liabilities_detail,
        "06_financial_detail_liabilities.csv",
    )

    # =========================================================
    # 7. ストック変化分解
    # =========================================================

    balance_sheet = (
        load_nonfinancial_balance_sheet(
            app_id=app_id,
            start_year=STOCK_START_YEAR,
            end_year=STOCK_END_YEAR,
        )
    )

    other_volume = (
        load_nonfinancial_other_volume_changes(
            app_id=app_id,
            start_year=STOCK_START_YEAR + 1,
            end_year=STOCK_END_YEAR,
        )
    )

    revaluation = (
        load_nonfinancial_revaluation(
            app_id=app_id,
            start_year=STOCK_START_YEAR + 1,
            end_year=STOCK_END_YEAR,
        )
    )

    stock_reconciliation = (
        calculate_stock_change_reconciliation(
            balance_sheet_df=balance_sheet,
            other_volume_df=other_volume,
            revaluation_df=revaluation,
            start_year=STOCK_START_YEAR,
            end_year=STOCK_END_YEAR,
        )
    )

    save_csv(
        stock_reconciliation,
        "07_stock_reconciliation.csv",
    )

    # =========================================================
    # 8. 法人企業統計
    # =========================================================

    corporate = (
        load_corporate_profit_allocation(
            app_id=app_id,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    corporate_metrics = (
        add_corporate_accounting_metrics(
            corporate
        )
    )

    save_csv(
        corporate_metrics,
        "08_corporate_accounting.csv",
    )

    # =========================================================
    # 9. 法人企業統計 BS接続
    # =========================================================

    corporate_continuity = (
        calculate_corporate_stock_continuity(
            corporate,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    save_csv(
        corporate_continuity,
        "09_corporate_stock_continuity.csv",
    )

    # =========================================================
    # 10. 利益剰余金ブリッジ
    # =========================================================

    retained_earnings_bridge = (
        summarize_corporate_retained_earnings_bridge(
            corporate,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    save_csv(
        retained_earnings_bridge,
        "10_retained_earnings_bridge.csv",
    )

    print()
    print("=" * 80)
    print("企業利益配分分析の出力が完了しました。")
    print(f"output: {OUTPUT_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()