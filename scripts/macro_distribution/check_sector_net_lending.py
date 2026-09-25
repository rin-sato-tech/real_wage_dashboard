from __future__ import annotations

import os
import tomllib
from pathlib import Path

from real_wage_dashboard.macro_distribution_analysis import (
    calculate_capital_financial_discrepancies,
    compare_sector_net_lending_ratios,
    prepare_sector_net_lending_long,
    validate_capital_financial_reconciliation,
    validate_sector_net_lending_balances,
    validate_sector_net_lending_ratios,
)
from real_wage_dashboard.macro_distribution_service import (
    load_income_generation,
    load_sector_net_lending_amount,
    load_sector_net_lending_ratio,
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

    amount = load_sector_net_lending_amount(
        app_id=app_id,
    )

    ratio = load_sector_net_lending_ratio(
        app_id=app_id,
    )

    income_generation = load_income_generation(
        app_id=app_id,
    )

    print("=== 制度部門別純貸出・純借入：金額 ===")
    print(
        amount.to_string(
            index=False,
            float_format=lambda x: f"{x:,.1f}",
        )
    )

    print()
    print("=== 制度部門別純貸出・純借入：GDP比 ===")
    print(
        ratio.to_string(
            index=False,
            float_format=lambda x: f"{x:,.4f}",
        )
    )

    print()
    print("=== 期間 ===")
    print(
        "amount:",
        amount["fiscal_year"].min(),
        "-",
        amount["fiscal_year"].max(),
        "rows:",
        len(amount),
    )
    print(
        "ratio:",
        ratio["fiscal_year"].min(),
        "-",
        ratio["fiscal_year"].max(),
        "rows:",
        len(ratio),
    )

    print()
    print("=== 欠損数：金額 ===")
    print(amount.isna().sum().to_string())

    print()
    print("=== 欠損数：GDP比 ===")
    print(ratio.isna().sum().to_string())

    # 金額からGDP比を再計算し、公表GDP比と照合
    validate_sector_net_lending_ratios(
        amount_df=amount,
        published_ratio_df=ratio,
        income_generation_df=income_generation,
    )

    ratio_comparison = compare_sector_net_lending_ratios(
        amount_df=amount,
        published_ratio_df=ratio,
        income_generation_df=income_generation,
    )

    difference_columns = [
        column
        for column in ratio_comparison.columns
        if column.endswith("_difference")
    ]

    max_ratio_difference = (
        ratio_comparison[difference_columns]
        .abs()
        .max()
        .max()
    )

    print()
    print("=== 金額から再計算したGDP比と公表値の照合 ===")
    print(
        "最大GDP比差:",
        max_ratio_difference,
    )

    # 制度部門間の会計整合性を確認
    validate_sector_net_lending_balances(amount)

    # 資本勘定側と金融勘定側の差を統計上の不突合と照合
    validate_capital_financial_reconciliation(amount)

    discrepancies = calculate_capital_financial_discrepancies(
        amount
    )

    print()
    print("=== 資本勘定・金融勘定の差 ===")

    discrepancy_columns = [
        "fiscal_year",
        "nonfinancial_corporations_difference",
        "financial_corporations_difference",
        "general_government_difference",
        "households_difference",
        "npish_difference",
        "rest_of_world_difference",
        "difference_sum",
        "statistical_discrepancy",
        "discrepancy_reconciliation_residual",
    ]

    print(
        discrepancies[
            discrepancy_columns
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:,.1f}",
        )
    )

    print()
    print(
        "最大資本・金融勘定照合残差:",
        discrepancies[
            "discrepancy_reconciliation_residual"
        ]
        .abs()
        .max(),
    )

    # 分析・可視化用long形式
    long_df = prepare_sector_net_lending_long(
        amount_df=amount,
        ratio_df=ratio,
    )

    print()
    print("=== 制度部門別純貸出：long形式（直近3年度） ===")

    recent_years = sorted(
        long_df["fiscal_year"].unique()
    )[-3:]

    print(
        long_df[
            long_df["fiscal_year"].isin(recent_years)
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:,.4f}",
        )
    )

    print()
    print("long rows:", len(long_df))

    print()
    print("=== 検証結果 ===")
    print("GDP比照合: OK")
    print("制度部門間会計整合性: OK")
    print("資本勘定・金融勘定照合: OK")


if __name__ == "__main__":
    main()
