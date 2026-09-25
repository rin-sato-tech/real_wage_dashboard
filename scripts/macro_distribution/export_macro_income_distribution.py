from __future__ import annotations

import os
import tomllib
from pathlib import Path

import pandas as pd

from real_wage_dashboard.macro_distribution_analysis import (
    calculate_household_primary_income_components,
    calculate_household_redistribution_components,
    calculate_household_saving_metrics,
    calculate_income_generation_shares,
    calculate_nonfinancial_capital_account_metrics,
    decompose_net_lending_change,
    prepare_sector_net_lending_long,
    validate_capital_financial_reconciliation,
    validate_household_disposable_income_identity,
    validate_household_primary_income_identity,
    validate_household_saving_identity,
    validate_income_generation_identity,
    validate_nonfinancial_capital_account_identity,
    validate_nonfinancial_net_lending_crosscheck,
    validate_sector_net_lending_balances,
    validate_sector_net_lending_ratios,
)
from real_wage_dashboard.macro_distribution_service import (
    load_household_primary_income,
    load_household_secondary_distribution,
    load_household_use_income,
    load_income_generation,
    load_nonfinancial_capital_account,
    load_sector_net_lending_amount,
    load_sector_net_lending_ratio,
)


ROOT_DIR = Path(__file__).resolve().parents[2]

SECRETS_PATH = (
    ROOT_DIR
    / ".streamlit"
    / "secrets.toml"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "outputs"
    / "analysis"
    / "macro_income_distribution"
)


def load_app_id() -> str:
    """環境変数またはStreamlit secretsからe-Stat API IDを取得する。"""
    app_id = os.getenv("ESTAT_APP_ID")

    if app_id:
        return app_id

    with SECRETS_PATH.open("rb") as file:
        secrets = tomllib.load(file)

    return str(secrets["ESTAT_APP_ID"])


def save_csv(
    df: pd.DataFrame,
    filename: str,
) -> None:
    """分析結果をCSVで保存する。"""
    output_path = OUTPUT_DIR / filename

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"saved: {output_path.relative_to(ROOT_DIR)} "
        f"({len(df)} rows)"
    )


def main() -> None:
    app_id = load_app_id()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ==========================================
    # 1. データ取得
    # ==========================================

    income_generation = load_income_generation(
        app_id=app_id,
    )

    household_primary = load_household_primary_income(
        app_id=app_id,
    )

    household_secondary = (
        load_household_secondary_distribution(
            app_id=app_id,
        )
    )

    household_use = load_household_use_income(
        app_id=app_id,
    )

    sector_amount = load_sector_net_lending_amount(
        app_id=app_id,
    )

    sector_ratio = load_sector_net_lending_ratio(
        app_id=app_id,
    )

    nonfinancial_capital = (
        load_nonfinancial_capital_account(
            app_id=app_id,
        )
    )

    # ==========================================
    # 2. 会計・クロスチェック
    # ==========================================

    validate_income_generation_identity(
        income_generation
    )

    validate_household_primary_income_identity(
        household_primary
    )

    validate_household_disposable_income_identity(
        household_secondary
    )

    validate_household_saving_identity(
        household_use
    )

    validate_sector_net_lending_ratios(
        amount_df=sector_amount,
        published_ratio_df=sector_ratio,
        income_generation_df=income_generation,
    )

    validate_sector_net_lending_balances(
        sector_amount
    )

    validate_capital_financial_reconciliation(
        sector_amount
    )

    validate_nonfinancial_capital_account_identity(
        nonfinancial_capital
    )

    validate_nonfinancial_net_lending_crosscheck(
        capital_account_df=nonfinancial_capital,
        sector_net_lending_df=sector_amount,
    )

    # ==========================================
    # 3. GDP所得面構成
    # ==========================================

    income_generation_result = (
        calculate_income_generation_shares(
            income_generation
        )
    )

    income_generation_columns = [
        "fiscal_year",
        "employee_compensation",
        "gross_operating_surplus",
        "gross_mixed_income",
        "net_taxes_on_production_and_imports",
        "gross_domestic_product",
        "employee_compensation_share",
        "gross_operating_surplus_share",
        "gross_mixed_income_share",
        "net_production_tax_share",
        "income_component_share_sum",
        "gdp_identity_residual",
    ]

    save_csv(
        income_generation_result[
            income_generation_columns
        ],
        "01_income_generation.csv",
    )

    # ==========================================
    # 4. 家計第1次所得
    # ==========================================

    household_primary_result = (
        calculate_household_primary_income_components(
            household_primary
        )
    )

    household_primary_columns = [
        "fiscal_year",
        "net_primary_income_balance",
        "employee_compensation_received",
        "net_operating_surplus_mixed_income",
        "property_income_received",
        "property_income_paid",
        "net_property_income",
        "employee_compensation_ratio",
        "operating_mixed_income_ratio",
        "net_property_income_ratio",
        "primary_income_component_ratio_sum",
        "primary_income_identity_residual",
    ]

    save_csv(
        household_primary_result[
            household_primary_columns
        ],
        "02_household_primary_income.csv",
    )

    # ==========================================
    # 5. 第1次所得 → 可処分所得
    # ==========================================

    household_redistribution_result = (
        calculate_household_redistribution_components(
            household_secondary
        )
    )

    household_redistribution_columns = [
        "fiscal_year",
        "net_primary_income_balance",
        "current_taxes_paid",
        "net_social_contributions_paid",
        "social_benefits_received",
        "net_other_current_transfers",
        "net_disposable_income",
        "current_taxes_ratio",
        "net_social_contributions_ratio",
        "social_benefits_ratio",
        "net_other_current_transfers_ratio",
        "disposable_income_to_primary_income_ratio",
        "net_redistribution",
        "net_redistribution_ratio",
        "disposable_income_identity_residual",
    ]

    save_csv(
        household_redistribution_result[
            household_redistribution_columns
        ],
        "03_household_redistribution.csv",
    )

    # ==========================================
    # 6. 可処分所得 → 消費・貯蓄
    # ==========================================

    household_saving_result = (
        calculate_household_saving_metrics(
            household_use
        )
    )

    household_saving_columns = [
        "fiscal_year",
        "net_disposable_income",
        "pension_entitlement_adjustment",
        "adjusted_disposable_income",
        "household_final_consumption",
        "net_saving",
        "published_saving_rate",
        "calculated_saving_rate",
        "saving_rate_difference",
        "consumption_ratio",
        "saving_consumption_ratio_sum",
        "saving_identity_residual",
    ]

    save_csv(
        household_saving_result[
            household_saving_columns
        ],
        "04_household_saving.csv",
    )

    # ==========================================
    # 7. 制度部門別純貸出・純借入
    # ==========================================

    sector_long = prepare_sector_net_lending_long(
        amount_df=sector_amount,
        ratio_df=sector_ratio,
    )

    save_csv(
        sector_long,
        "05_sector_net_lending_long.csv",
    )

    # 公表値そのものもwide形式で残しておく
    save_csv(
        sector_amount,
        "05_sector_net_lending_amount_wide.csv",
    )

    save_csv(
        sector_ratio,
        "05_sector_net_lending_ratio_wide.csv",
    )

    # ==========================================
    # 8. 非金融法人企業・資本勘定
    # ==========================================

    nonfinancial_result = (
        calculate_nonfinancial_capital_account_metrics(
            df=nonfinancial_capital,
            income_generation_df=income_generation,
            statistical_discrepancy_df=sector_amount,
        )
    )

    nonfinancial_columns = [
        "fiscal_year",
        "net_saving",
        "net_capital_transfers",
        "net_fixed_capital_formation",
        "changes_in_inventories",
        "net_land_purchases",
        "net_capital_formation",
        "net_lending_capital_account",
        "net_saving_ratio",
        "net_capital_transfers_ratio",
        "net_fixed_capital_formation_ratio",
        "changes_in_inventories_ratio",
        "net_land_purchases_ratio",
        "net_capital_formation_ratio",
        "net_lending_capital_account_ratio",
        "net_lending_identity_residual",
    ]

    save_csv(
        nonfinancial_result[
            nonfinancial_columns
        ],
        "06_nonfinancial_capital_account.csv",
    )

    # ==========================================
    # 9. 純貸出変化の期間別分解
    # ==========================================

    periods = [
        (2015, 2019),
        (2019, 2020),
        (2020, 2024),
        (2015, 2024),
    ]

    decomposition_frames = []

    for start_year, end_year in periods:
        decomposition = decompose_net_lending_change(
            nonfinancial_result,
            start_year=start_year,
            end_year=end_year,
        )

        decomposition_frames.append(
            decomposition
        )

    decomposition_result = pd.concat(
        decomposition_frames,
        ignore_index=True,
    )

    save_csv(
        decomposition_result,
        "07_nonfinancial_net_lending_decomposition.csv",
    )

    # ==========================================
    # 10. 完了
    # ==========================================

    print()
    print("=== export completed ===")
    print(
        OUTPUT_DIR.relative_to(ROOT_DIR)
    )


if __name__ == "__main__":
    main()
