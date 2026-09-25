from __future__ import annotations

import os
import tomllib
from pathlib import Path

from real_wage_dashboard.macro_distribution_analysis import (
    calculate_household_primary_income_components,
    validate_household_primary_income_identity,
)
from real_wage_dashboard.macro_distribution_service import (
    load_household_primary_income,
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
    df = load_household_primary_income(
        app_id=load_app_id(),
    )

    print("=== 取得データ ===")
    print(df.to_string(index=False))

    validate_household_primary_income_identity(df)

    result = calculate_household_primary_income_components(df)

    columns = [
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

    print()
    print("=== 家計第1次所得構成 ===")
    print(
        result[columns].to_string(
            index=False,
        )
    )

    print()
    print(
        "最大恒等式残差:",
        result[
            "primary_income_identity_residual"
        ]
        .abs()
        .max(),
    )

    print(
        "period:",
        result["fiscal_year"].min(),
        "-",
        result["fiscal_year"].max(),
    )


if __name__ == "__main__":
    main()
