from __future__ import annotations

import os
import tomllib
from pathlib import Path

from real_wage_dashboard.macro_distribution_analysis import (
    calculate_nonfinancial_capital_account_metrics,
    decompose_net_lending_change,
    validate_nonfinancial_capital_account_identity,
    validate_nonfinancial_net_lending_crosscheck,
)
from real_wage_dashboard.macro_distribution_service import (
    load_income_generation,
    load_nonfinancial_capital_account,
    load_sector_net_lending_amount,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
SECRETS_PATH = ROOT_DIR / ".streamlit" / "secrets.toml"


def load_app_id() -> str:
    """環境変数またはStreamlit secretsからe-Stat API IDを取得する。"""
    app_id = os.getenv("ESTAT_APP_ID")

    if app_id:
        return app_id

    with SECRETS_PATH.open("rb") as file:
        secrets = tomllib.load(file)

    return str(secrets["ESTAT_APP_ID"])


def main() -> None:
    app_id = load_app_id()

    # 非金融法人企業の資本勘定
    capital_account = load_nonfinancial_capital_account(
        app_id=app_id,
    )

    # 所得発生勘定
    # 支出側GDPの再構成に使用する。
    income_generation = load_income_generation(
        app_id=app_id,
    )

    # 制度部門別純貸出・純借入
    # 統計上の不突合とクロスチェックに使用する。
    sector_net_lending = load_sector_net_lending_amount(
        app_id=app_id,
    )

    # --------------------------------------------------
    # 1. 非金融法人企業の資本勘定恒等式
    # --------------------------------------------------

    validate_nonfinancial_capital_account_identity(capital_account)

    # 個別資本勘定の純貸出と、
    # 制度部門別純貸出表の非金融法人企業を照合する。
    validate_nonfinancial_net_lending_crosscheck(
        capital_account_df=capital_account,
        sector_net_lending_df=sector_net_lending,
    )

    # --------------------------------------------------
    # 2. GDP比などを計算
    # --------------------------------------------------

    result = calculate_nonfinancial_capital_account_metrics(
        df=capital_account,
        income_generation_df=income_generation,
        statistical_discrepancy_df=sector_net_lending,
    )

    columns = [
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

    print("=== 非金融法人企業・資本勘定 ===")
    print(
        result[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:,.6f}",
        )
    )

    print()
    print(
        "最大恒等式残差:",
        result["net_lending_identity_residual"].abs().max(),
    )

    # --------------------------------------------------
    # 3. 純貸出GDP比変化の期間別分解
    # --------------------------------------------------

    periods = [
        (2015, 2019),
        (2019, 2020),
        (2020, 2024),
        (2015, 2024),
    ]

    print()
    print("=== 純貸出GDP比変化の期間別分解 ===")

    for start_year, end_year in periods:
        decomposition = decompose_net_lending_change(
            result,
            start_year=start_year,
            end_year=end_year,
        )

        print()
        print(f"--- {start_year} → {end_year} ---")

        print(
            decomposition.to_string(
                index=False,
                float_format=lambda x: f"{x:,.6f}",
            )
        )

    # --------------------------------------------------
    # 4. 検証結果
    # --------------------------------------------------

    print()
    print("=== 検証結果 ===")
    print("資本勘定恒等式: OK")
    print("制度部門表との純貸出照合: OK")


if __name__ == "__main__":
    main()
