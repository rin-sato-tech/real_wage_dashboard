import altair as alt
import pandas as pd
import pytest

from real_wage_dashboard.corporate_profit_allocation_ui import (
    create_capital_allocation_chart,
    create_financial_account_components_chart,
    create_retained_earnings_bridge_chart,
    create_stock_reconciliation_chart,
    prepare_capital_allocation_data,
    prepare_financial_asset_detail_data,
)


def test_prepare_capital_allocation_data_includes_sources_and_uses():
    df = pd.DataFrame(
        {
            "cumulative_net_saving": [
                330946.2,
            ],
            "cumulative_net_capital_transfers": [
                35065.3,
            ],
            "cumulative_net_capital_formation": [
                112863.9,
            ],
            "cumulative_net_lending": [
                253147.6,
            ],
        }
    )

    result = (
        prepare_capital_allocation_data(
            df
        )
    )

    assert result[
        "side"
    ].tolist() == [
        "資金源",
        "資金源",
        "資金使途",
        "資金使途",
    ]

    assert result[
        "component"
    ].tolist() == [
        "純貯蓄",
        "純資本移転",
        "純資本形成",
        "純貸出",
    ]

    assert (
        result.loc[
            result["side"]
            == "資金源",
            "value_trillion",
        ].sum()
        == pytest.approx(
            366.0115
        )
    )

    assert (
        result.loc[
            result["side"]
            == "資金使途",
            "value_trillion",
        ].sum()
        == pytest.approx(
            366.0115
        )
    )


def test_create_capital_allocation_chart_returns_chart():
    df = pd.DataFrame(
        {
            "cumulative_net_saving": [
                330946.2,
            ],
            "cumulative_net_capital_transfers": [
                35065.3,
            ],
            "cumulative_net_capital_formation": [
                112863.9,
            ],
            "cumulative_net_lending": [
                253147.6,
            ],
        }
    )

    assert isinstance(
        create_capital_allocation_chart(
            df
        ),
        alt.Chart,
    )


def test_create_financial_account_components_chart_rejects_unknown_side():
    df = pd.DataFrame(
        {
            "side": [
                "金融資産",
            ],
            "component_name": [
                "現金・預金",
            ],
            "cumulative_amount": [
                1000.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="未対応の区分",
    ):
        create_financial_account_components_chart(
            df,
            "不明",
        )


def test_prepare_financial_asset_detail_data_sums_period():
    columns = {
        "fiscal_year": [
            2023,
            2024,
        ],
    }

    detail_columns = [
        "cash_deposits_assets",
        "loans_assets",
        "debt_securities_assets",
        "equity_investment_fund_assets",
        "insurance_pension_guarantee_assets",
        "financial_derivatives_assets",
        "fiscal_investment_fund_deposits_assets",
        "entrusted_funds_assets",
        "trade_credit_assets",
        "accounts_receivable_assets",
        "direct_investment_assets",
        "foreign_portfolio_investment_assets",
        "other_external_claims_assets",
        "other_assets",
    ]

    for column in detail_columns:
        columns[column] = [
            1000.0,
            2000.0,
        ]

    result = (
        prepare_financial_asset_detail_data(
            pd.DataFrame(
                columns
            )
        )
    )

    cash = result.loc[
        result["component"]
        == "現金・預金"
    ].iloc[0]

    direct = result.loc[
        result["component"]
        == "直接投資"
    ].iloc[0]

    assert (
        cash["value_trillion"]
        == pytest.approx(
            3.0
        )
    )

    assert (
        direct["value_trillion"]
        == pytest.approx(
            3.0
        )
    )


def test_create_stock_reconciliation_chart_rejects_missing_item():
    df = pd.DataFrame(
        {
            "item": [
                "financial_assets",
            ],
            "implied_transactions": [
                100.0,
            ],
            "other_volume_change": [
                10.0,
            ],
            "revaluation": [
                20.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="一意に取得できません",
    ):
        create_stock_reconciliation_chart(
            df,
            "unknown",
        )


def test_create_retained_earnings_bridge_chart_requires_one_row():
    df = pd.DataFrame(
        {
            "cumulative_profit_after_dividends": [
                100.0,
                200.0,
            ],
            "cumulative_bridge_residual": [
                10.0,
                20.0,
            ],
            "interyear_discontinuity": [
                -5.0,
                -6.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="1行",
    ):
        create_retained_earnings_bridge_chart(
            df
        )
