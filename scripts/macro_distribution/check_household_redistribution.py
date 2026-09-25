from __future__ import annotations

import os
import tomllib
from pathlib import Path

from real_wage_dashboard.macro_distribution_analysis import (
    calculate_household_redistribution_components,
    validate_household_disposable_income_identity,
)
from real_wage_dashboard.macro_distribution_service import (
    load_household_secondary_distribution,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
SECRETS_PATH = ROOT_DIR / ".streamlit" / "secrets.toml"


def load_app_id() -> str:
    app_id = os.getenv("ESTAT_APP_ID")

    if app_id:
        return app_id

    with SECRETS_PATH.open("rb") as file:
        secrets = tomllib.load(file)

    return str(secrets["ESTAT_APP_ID"])


def main() -> None:
    df = load_household_secondary_distribution(
        app_id=load_app_id(),
    )

    validate_household_disposable_income_identity(df)

    result = calculate_household_redistribution_components(df)

    columns = [
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
        "net_redistribution_ratio",
        "disposable_income_identity_residual",
    ]

    print("=== 第1次所得から可処分所得への再分配 ===")
    print(
        result[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:,.6f}",
        )
    )

    print()
    print(
        "最大恒等式残差:",
        result["disposable_income_identity_residual"].abs().max(),
    )

    print(
        "period:",
        result["fiscal_year"].min(),
        "-",
        result["fiscal_year"].max(),
    )


if __name__ == "__main__":
    main()
