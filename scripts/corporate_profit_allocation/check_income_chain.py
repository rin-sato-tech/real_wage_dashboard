from __future__ import annotations

import pandas as pd
import streamlit as st

from real_wage_dashboard.corporate_profit_allocation_analysis import (
    add_nonfinancial_disposable_income_identity,
    add_nonfinancial_primary_income_metrics,
    add_nonfinancial_saving_identity,
    validate_nonfinancial_current_tax_identity,
    validate_nonfinancial_disposable_income_identity,
    validate_nonfinancial_primary_income_identity,
    validate_nonfinancial_saving_identity,
)
from real_wage_dashboard.corporate_profit_allocation_service import (
    load_nonfinancial_primary_income,
    load_nonfinancial_secondary_distribution,
    load_nonfinancial_use_income,
)


START_YEAR = 2015
END_YEAR = 2024


def get_app_id() -> str:
    try:
        return str(st.secrets["ESTAT_APP_ID"])

    except KeyError as exc:
        raise RuntimeError(
            ".streamlit/secrets.tomlに"
            "ESTAT_APP_IDを設定してください。"
        ) from exc


def print_selected_years(
    title: str,
    df: pd.DataFrame,
) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    selected = df[
        df["fiscal_year"].isin(
            [
                2015,
                2019,
                2020,
                2024,
            ]
        )
    ]

    print(
        selected.to_string(
            index=False,
        )
    )


def main() -> None:
    app_id = get_app_id()

    primary_df = load_nonfinancial_primary_income(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    secondary_df = load_nonfinancial_secondary_distribution(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    use_income_df = load_nonfinancial_use_income(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    # print_selected_years(
    #     "第1次所得の配分勘定",
    #     primary_df,
    # )

    # print_selected_years(
    #     "所得の第2次分配勘定",
    #     secondary_df,
    # )

    # print_selected_years(
    #     "可処分所得の使用勘定",
    #     use_income_df,
    # )

    primary_result = add_nonfinancial_primary_income_metrics(
        primary_df
    )

    secondary_result = add_nonfinancial_disposable_income_identity(
        secondary_df
    )

    saving_result = add_nonfinancial_saving_identity(
        use_income_df
    )

    validate_nonfinancial_primary_income_identity(
        primary_df
    )

    validate_nonfinancial_disposable_income_identity(
        secondary_df
    )

    validate_nonfinancial_current_tax_identity(
        secondary_df
    )

    validate_nonfinancial_saving_identity(
        use_income_df
    )

    print()
    print("=" * 100)
    print("恒等式検証")
    print("=" * 100)

    print(
        "第1次所得 最大残差:",
        primary_result[
            "primary_income_identity_residual"
        ].abs().max(),
    )

    print(
        "可処分所得 最大残差:",
        secondary_result[
            "disposable_income_identity_residual"
        ].abs().max(),
    )

    print(
        "経常税 最大残差:",
        secondary_result[
            "current_tax_identity_residual"
        ].abs().max(),
    )

    print(
        "純貯蓄 最大残差:",
        saving_result[
            "net_saving_identity_residual"
        ].abs().max(),
    )

    print()
    print("すべての恒等式検証を通過しました。")


if __name__ == "__main__":
    main()
