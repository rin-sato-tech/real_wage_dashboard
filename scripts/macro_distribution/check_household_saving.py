from __future__ import annotations

import os
import tomllib
from pathlib import Path

from real_wage_dashboard.macro_distribution_analysis import (
    calculate_household_saving_metrics,
    validate_household_saving_identity,
)
from real_wage_dashboard.macro_distribution_service import (
    load_household_use_income,
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
    df = load_household_use_income(
        app_id=load_app_id(),
    )

    validate_household_saving_identity(df)

    result = calculate_household_saving_metrics(df)

    columns = [
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

    print("=== 家計可処分所得・消費・貯蓄 ===")
    print(
        result[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:,.6f}",
        )
    )

    print()
    print(
        "最大恒等式残差:",
        result["saving_identity_residual"].abs().max(),
    )

    print(
        "最大貯蓄率差:",
        result["saving_rate_difference"].abs().max(),
    )

    print(
        "period:",
        result["fiscal_year"].min(),
        "-",
        result["fiscal_year"].max(),
    )


if __name__ == "__main__":
    main()
