from __future__ import annotations

import streamlit as st

from real_wage_dashboard.corporate_profit_allocation_analysis import (
    calculate_stock_change_reconciliation,
)
from real_wage_dashboard.corporate_profit_allocation_service import (
    load_nonfinancial_balance_sheet,
    load_nonfinancial_other_volume_changes,
    load_nonfinancial_revaluation,
)


START_YEAR = 2014
END_YEAR = 2024


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

    balance = load_nonfinancial_balance_sheet(
        app_id=app_id,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    other_volume = (
        load_nonfinancial_other_volume_changes(
            app_id=app_id,
            start_year=START_YEAR + 1,
            end_year=END_YEAR,
        )
    )

    revaluation = load_nonfinancial_revaluation(
        app_id=app_id,
        start_year=START_YEAR + 1,
        end_year=END_YEAR,
    )

    result = calculate_stock_change_reconciliation(
        balance_sheet_df=balance,
        other_volume_df=other_volume,
        revaluation_df=revaluation,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    display = result.copy()

    for column in [
        "beginning_stock",
        "ending_stock",
        "stock_change",
        "implied_transactions",
        "other_volume_change",
        "revaluation",
    ]:
        display[column] = (
            display[column] / 1000
        )

    print()
    print("=" * 120)
    print("2014年末→2024年末 ストック変化分解（兆円）")
    print("=" * 120)

    print(
        display.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
