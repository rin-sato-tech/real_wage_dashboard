from __future__ import annotations

import os
import tomllib
from pathlib import Path

from real_wage_dashboard.macro_distribution_analysis import (
    calculate_income_generation_shares,
    validate_income_generation_identity,
)
from real_wage_dashboard.macro_distribution_service import (
    load_income_generation,
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
    df = load_income_generation(
        app_id=load_app_id(),
    )

    # print(df.to_string(index=False))
    # print()
    # print(df.dtypes)
    # print()
    # print(f"rows: {len(df)}")
    # print(
    #     "period:",
    #     df["fiscal_year"].min(),
    #     "-",
    #     df["fiscal_year"].max(),
    # )

    validate_income_generation_identity(df)

    result = calculate_income_generation_shares(df)

    columns = [
        "fiscal_year",
        "employee_compensation_share",
        "gross_operating_surplus_share",
        "gross_mixed_income_share",
        "net_production_tax_share",
        "income_component_share_sum",
        "gdp_identity_residual",
    ]

    print()
    print("=== GDP所得面構成 ===")
    print(
        result[columns].to_string(
            index=False,
        )
    )

    print()
    print(
        "最大恒等式残差:",
        result["gdp_identity_residual"]
        .abs()
        .max(),
    )

if __name__ == "__main__":
    main()
