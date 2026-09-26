from __future__ import annotations

import streamlit as st

from real_wage_dashboard.corporate_profit_allocation_analysis import (
    add_corporate_accounting_metrics,
    calculate_corporate_stock_continuity,
    summarize_corporate_retained_earnings_bridge,
)
from real_wage_dashboard.corporate_profit_allocation_service import (
    load_corporate_profit_allocation,
)


START_YEAR = 2015
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
    df = load_corporate_profit_allocation(
        app_id=get_app_id(),
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    result = add_corporate_accounting_metrics(
        df
    )

    # -------------------------
    # 年次結果
    # -------------------------

    # print()
    # print("=" * 120)
    # print("法人企業統計・利益配分")
    # print("=" * 120)

    display_columns = [
        "fiscal_year",
        "net_income",
        "total_dividends",
        "profit_after_dividends",
        "calculated_dividend_payout_ratio",
        "retained_earnings_change",
        "cash_deposits_change",
        "fixed_assets_change",
        "investment_securities_change",
        "short_term_borrowings_change",
        "long_term_borrowings_change",
    ]

    # 公表配当性向が取得できた場合のみ表示
    if "published_dividend_payout_ratio" in result.columns:
        payout_index = display_columns.index(
            "calculated_dividend_payout_ratio"
        ) + 1

        display_columns.insert(
            payout_index,
            "published_dividend_payout_ratio",
        )

    # 公表値との差を計算している場合のみ表示
    if "dividend_payout_ratio_difference" in result.columns:
        difference_index = display_columns.index(
            "calculated_dividend_payout_ratio"
        ) + 1

        if "published_dividend_payout_ratio" in display_columns:
            difference_index += 1

        display_columns.insert(
            difference_index,
            "dividend_payout_ratio_difference",
        )

    # print(
    #     result[
    #         display_columns
    #     ].to_string(
    #         index=False
    #     )
    # )

    # -------------------------
    # 累積利益フロー
    # -------------------------

    # print()
    # print("=" * 120)
    # print(
    #     f"{START_YEAR}～{END_YEAR}年度 累積利益フロー"
    # )
    # print("=" * 120)

    cumulative_net_income = (
        result["net_income"].sum()
    )

    cumulative_dividends = (
        result["total_dividends"].sum()
    )

    cumulative_profit_after_dividends = (
        result["profit_after_dividends"].sum()
    )

    # print(
    #     "当期純利益累計:",
    #     cumulative_net_income / 1_000_000,
    #     "兆円",
    # )

    # print(
    #     "配当金累計:",
    #     cumulative_dividends / 1_000_000,
    #     "兆円",
    # )

    # print(
    #     "純利益－配当累計:",
    #     cumulative_profit_after_dividends / 1_000_000,
    #     "兆円",
    # )

    if cumulative_net_income != 0:
        cumulative_payout_ratio = (
            cumulative_dividends
            / cumulative_net_income
            * 100
        )

        # print(
        #     "期間累積配当性向:",
        #     cumulative_payout_ratio,
        #     "%",
        # )

    # -------------------------
    # BS変化
    # -------------------------

    # print()
    # print("=" * 120)
    # print(
    #     f"{START_YEAR}～{END_YEAR}年度 BS項目変化累計"
    # )
    # print("=" * 120)

    stock_change_columns = [
        "retained_earnings_change",
        "cash_deposits_change",
        "fixed_assets_change",
        "investment_securities_change",
        "short_term_borrowings_change",
        "long_term_borrowings_change",
        "liabilities_change",
        "net_assets_change",
    ]

    # for column in stock_change_columns:
    #     print(
    #         f"{column}: "
    #         f"{result[column].sum() / 1_000_000:.4f}兆円"
    #     )

    continuity_df = calculate_corporate_stock_continuity(
        df,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    # print()
    # print("=" * 120)
    # print(
    #     f"{START_YEAR}～{END_YEAR}年度 "
    #     "BSストック接続"
    # )
    # print("=" * 120)

    display = continuity_df.copy()

    amount_columns = [
        "start_stock",
        "end_stock",
        "endpoint_change",
        "cumulative_within_year_change",
        "interyear_discontinuity",
        "calculated_endpoint_change",
    ]

    for column in amount_columns:
        display[column] = (
            display[column] / 1_000_000
        )

    # print(
    #     display.to_string(
    #         index=False
    #     )
    # )

    # print()
    # print("=" * 120)
    # print("利益剰余金ブリッジ")
    # print("=" * 120)

    # print(
    #     result[
    #         [
    #             "fiscal_year",
    #             "net_income",
    #             "total_dividends",
    #             "profit_after_dividends",
    #             "retained_earnings_change",
    #             "retained_earnings_bridge_residual",
    #         ]
    #     ].to_string(
    #         index=False
    #     )
    # )

    # print()
    # print(
    #     "純利益－配当累計:",
    #     result["profit_after_dividends"].sum()
    #     / 1_000_000,
    #     "兆円",
    # )

    # print(
    #     "利益剰余金年度内増加累計:",
    #     result["retained_earnings_change"].sum()
    #     / 1_000_000,
    #     "兆円",
    # )

    # print(
    #     "橋渡し残差累計:",
    #     result[
    #         "retained_earnings_bridge_residual"
    #     ].sum()
    #     / 1_000_000,
    #     "兆円",
    # )

    bridge_summary = (
        summarize_corporate_retained_earnings_bridge(
            df,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    )

    print()
    print("=" * 120)
    print("利益剰余金・長期ブリッジ")
    print("=" * 120)

    display_bridge = bridge_summary.copy()

    amount_columns = [
        "cumulative_net_income",
        "cumulative_dividends",
        "cumulative_profit_after_dividends",
        "cumulative_bridge_residual",
        "cumulative_within_year_retained_earnings_change",
        "interyear_discontinuity",
        "endpoint_retained_earnings_change",
        "calculated_endpoint_change",
    ]

    for column in amount_columns:
        display_bridge[column] = (
            display_bridge[column]
            / 1_000_000
        )

    print(
        display_bridge.to_string(
            index=False
        )
    )

if __name__ == "__main__":
    main()
