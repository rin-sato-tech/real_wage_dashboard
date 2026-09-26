import pandas as pd
import pytest

from real_wage_dashboard.corporate_profit_allocation_analysis import (
    add_corporate_accounting_metrics,
    add_nonfinancial_disposable_income_identity,
    add_nonfinancial_financial_account_identity,
    add_nonfinancial_primary_income_metrics,
    add_nonfinancial_saving_identity,
    calculate_capital_financial_net_lending_discrepancy,
    calculate_corporate_stock_continuity,
    calculate_cumulative_capital_account,
    calculate_stock_change_reconciliation,
    summarize_corporate_retained_earnings_bridge,
    summarize_cumulative_capital_account,
    summarize_cumulative_financial_components,
    validate_nonfinancial_current_tax_identity,
    validate_nonfinancial_disposable_income_identity,
    validate_nonfinancial_financial_account_identity,
    validate_nonfinancial_primary_income_identity,
    validate_nonfinancial_saving_identity,
)


def create_corporate_accounting_test_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2020, 2021],
            "net_income": [100.0, 120.0],
            "total_dividends": [40.0, 50.0],

            "cash_deposits_begin": [200.0, 230.0],
            "cash_deposits_end": [220.0, 250.0],

            "fixed_assets_begin": [500.0, 540.0],
            "fixed_assets_end": [530.0, 570.0],

            "investment_securities_begin": [100.0, 115.0],
            "investment_securities_end": [110.0, 130.0],

            "short_term_borrowings_begin": [80.0, 85.0],
            "short_term_borrowings_end": [90.0, 95.0],

            "long_term_borrowings_begin": [150.0, 160.0],
            "long_term_borrowings_end": [155.0, 170.0],

            "liabilities_begin": [400.0, 420.0],
            "liabilities_end": [410.0, 440.0],

            "net_assets_begin": [500.0, 535.0],
            "net_assets_end": [530.0, 570.0],

            "retained_earnings_begin": [300.0, 370.0],
            "retained_earnings_end": [360.0, 440.0],
        }
    )


def test_add_corporate_accounting_metrics() -> None:
    df = create_corporate_accounting_test_df()

    result = add_corporate_accounting_metrics(df)

    assert result.loc[0, "profit_after_dividends"] == pytest.approx(
        60.0
    )

    assert result.loc[
        0,
        "calculated_dividend_payout_ratio",
    ] == pytest.approx(40.0)

    assert result.loc[
        0,
        "retained_earnings_change",
    ] == pytest.approx(60.0)

    assert result.loc[
        0,
        "retained_earnings_bridge_residual",
    ] == pytest.approx(0.0)

    # 2021年度
    # 利益剰余金増加 = 440 - 370 = 70
    # 純利益 - 配当 = 120 - 50 = 70
    assert result.loc[
        1,
        "retained_earnings_bridge_residual",
    ] == pytest.approx(0.0)


def test_corporate_accounting_metrics_rejects_missing_columns() -> None:
    df = pd.DataFrame(
        {
            "fiscal_year": [2020],
            "net_income": [100.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        add_corporate_accounting_metrics(df)


def test_calculate_corporate_stock_continuity() -> None:
    df = create_corporate_accounting_test_df()

    result = calculate_corporate_stock_continuity(
        df,
        start_year=2020,
        end_year=2021,
    )

    retained = result.loc[
        result["item"] == "retained_earnings"
    ].iloc[0]

    # 年度内増加
    # 2020: 360 - 300 = 60
    # 2021: 440 - 370 = 70
    # 合計 = 130
    assert retained[
        "cumulative_within_year_change"
    ] == pytest.approx(130.0)

    # 年度間不連続
    # 2021 begin 370 - 2020 end 360 = 10
    assert retained[
        "interyear_discontinuity"
    ] == pytest.approx(10.0)

    # 端点差
    # 440 - 300 = 140
    assert retained[
        "endpoint_change"
    ] == pytest.approx(140.0)

    assert retained[
        "calculated_endpoint_change"
    ] == pytest.approx(140.0)

    assert retained[
        "reconciliation_residual"
    ] == pytest.approx(0.0)


def test_stock_continuity_rejects_missing_year() -> None:
    df = create_corporate_accounting_test_df()

    df.loc[1, "fiscal_year"] = 2022

    with pytest.raises(
        ValueError,
        match="分析対象年度が連続していません",
    ):
        calculate_corporate_stock_continuity(
            df,
            start_year=2020,
            end_year=2022,
        )


def test_retained_earnings_bridge_reconciles() -> None:
    df = create_corporate_accounting_test_df()

    result = summarize_corporate_retained_earnings_bridge(
        df,
        start_year=2020,
        end_year=2021,
    )

    row = result.iloc[0]

    # 純利益累計
    assert row[
        "cumulative_net_income"
    ] == pytest.approx(220.0)

    # 配当累計
    assert row[
        "cumulative_dividends"
    ] == pytest.approx(90.0)

    # 純利益 - 配当
    assert row[
        "cumulative_profit_after_dividends"
    ] == pytest.approx(130.0)

    # このfixtureでは年度内bridge residualは0
    assert row[
        "cumulative_bridge_residual"
    ] == pytest.approx(0.0)

    # 年度間不連続 +10
    assert row[
        "interyear_discontinuity"
    ] == pytest.approx(10.0)

    # 端点差 = 140
    assert row[
        "endpoint_retained_earnings_change"
    ] == pytest.approx(140.0)

    assert row[
        "calculated_endpoint_change"
    ] == pytest.approx(140.0)

    assert row[
        "reconciliation_residual"
    ] == pytest.approx(0.0)


def test_stock_change_reconciliation() -> None:
    balance = pd.DataFrame(
        {
            "calendar_year": [2014, 2024],
            "nonfinancial_assets": [100.0, 160.0],
            "fixed_assets": [80.0, 120.0],
            "inventories": [10.0, 15.0],
            "land": [10.0, 25.0],
            "financial_assets": [200.0, 300.0],
            "shares_assets": [50.0, 90.0],
            "liabilities": [150.0, 250.0],
            "shares_liabilities": [70.0, 120.0],
        }
    )

    years = list(range(2015, 2025))

    other_volume = pd.DataFrame(
        {
            "calendar_year": years,
            "nonfinancial_assets": [1.0] * 10,
            "fixed_assets": [0.5] * 10,
            "inventories": [0.0] * 10,
            "land": [0.5] * 10,
            "financial_assets": [1.0] * 10,
            "shares_assets": [0.0] * 10,
            "liabilities": [2.0] * 10,
            "shares_liabilities": [0.0] * 10,
        }
    )

    revaluation = pd.DataFrame(
        {
            "calendar_year": years,
            "nonfinancial_assets": [2.0] * 10,
            "fixed_assets": [1.0] * 10,
            "inventories": [0.5] * 10,
            "land": [0.5] * 10,
            "financial_assets": [3.0] * 10,
            "shares_assets": [2.0] * 10,
            "liabilities": [4.0] * 10,
            "shares_liabilities": [3.0] * 10,
        }
    )

    result = calculate_stock_change_reconciliation(
        balance_sheet_df=balance,
        other_volume_df=other_volume,
        revaluation_df=revaluation,
        start_year=2014,
        end_year=2024,
    )

    financial_assets = result.loc[
        result["item"] == "financial_assets"
    ].iloc[0]

    # stock change = 300 - 200 = 100
    # other volume = 10
    # revaluation = 30
    # transactions = 60
    assert financial_assets[
        "stock_change"
    ] == pytest.approx(100.0)

    assert financial_assets[
        "other_volume_change"
    ] == pytest.approx(10.0)

    assert financial_assets[
        "revaluation"
    ] == pytest.approx(30.0)

    assert financial_assets[
        "implied_transactions"
    ] == pytest.approx(60.0)

    assert financial_assets[
        "reconciliation_residual"
    ] == pytest.approx(0.0)


def test_nonfinancial_income_identities() -> None:
    primary = pd.DataFrame(
        {
            "fiscal_year": [2020],
            "net_operating_surplus": [100.0],
            "property_income_received": [30.0],
            "property_income_paid": [20.0],
            "net_primary_income_balance": [110.0],

            "interest_paid": [8.0],
            "interest_received": [6.0],
            "dividends_paid": [10.0],
            "dividends_received": [12.0],
            "reinvested_earnings_paid": [2.0],
            "reinvested_earnings_received": [2.0],
        }
    )

    primary_result = (
        add_nonfinancial_primary_income_metrics(
            primary
        )
    )

    validate_nonfinancial_primary_income_identity(
        primary_result
    )

    secondary = pd.DataFrame(
        {
            "fiscal_year": [2020],
            "net_primary_income_balance": [110.0],
            "current_taxes_paid": [20.0],
            "income_taxes_paid": [15.0],
            "other_current_taxes_paid": [5.0],
            "other_social_insurance_nonpension_benefits_paid": [
                2.0
            ],
            "other_current_transfers_paid": [5.0],
            "imputed_employer_social_contributions_received": [
                2.0
            ],
            "other_current_transfers_received": [3.0],
            "net_disposable_income": [88.0],
        }
    )

    secondary_result = (
        add_nonfinancial_disposable_income_identity(
            secondary
        )
    )

    validate_nonfinancial_disposable_income_identity(
        secondary_result
    )

    validate_nonfinancial_current_tax_identity(
        secondary_result
    )

    use_income = pd.DataFrame(
        {
            "fiscal_year": [2020],
            "net_saving": [88.0],
            "gross_saving": [98.0],
            "consumption_fixed_capital": [10.0],
            "net_disposable_income": [88.0],
            "gross_disposable_income": [98.0],
            "consumption_fixed_capital_disposable_income": [
                10.0
            ],
        }
    )

    saving_result = (
        add_nonfinancial_saving_identity(
            use_income
        )
    )

    validate_nonfinancial_saving_identity(
        saving_result
    )


def test_primary_income_identity_rejects_large_residual() -> None:
    df = pd.DataFrame(
        {
            "fiscal_year": [2020],
            "net_operating_surplus": [100.0],
            "property_income_received": [30.0],
            "property_income_paid": [20.0],

            # 正しくは110
            "net_primary_income_balance": [112.0],

            "interest_paid": [8.0],
            "interest_received": [6.0],
            "dividends_paid": [10.0],
            "dividends_received": [12.0],
            "reinvested_earnings_paid": [2.0],
            "reinvested_earnings_received": [2.0],
        }
    )

    result = add_nonfinancial_primary_income_metrics(
        df
    )

    with pytest.raises(ValueError):
        validate_nonfinancial_primary_income_identity(
            result
        )


def create_financial_account_test_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2020, 2021],

            # -----------------
            # 金融資産
            # -----------------
            "monetary_gold_sdr_assets": [0.0, 0.0],
            "cash_deposits_assets": [50.0, 60.0],
            "loans_assets": [10.0, 10.0],
            "debt_securities_assets": [5.0, 5.0],
            "equity_investment_fund_assets": [3.0, 3.0],

            # 140の内数なので合計には入れてはいけない
            "shares_assets": [999.0, 999.0],

            "insurance_pension_guarantee_assets": [2.0, 2.0],
            "financial_derivatives_assets": [0.0, 0.0],
            "other_financial_assets": [30.0, 40.0],

            # 2020 = 100
            # 2021 = 120
            "financial_assets_change": [100.0, 120.0],

            # -----------------
            # 負債
            # -----------------
            "monetary_gold_sdr_liabilities": [0.0, 0.0],
            "cash_deposits_liabilities": [0.0, 0.0],
            "loans_liabilities": [20.0, 25.0],
            "debt_securities_liabilities": [10.0, 10.0],
            "equity_investment_fund_liabilities": [5.0, 5.0],

            # 260の内数
            "shares_liabilities": [999.0, 999.0],

            "insurance_pension_guarantee_liabilities": [
                -2.0,
                -2.0,
            ],
            "financial_derivatives_liabilities": [1.0, 1.0],
            "other_liabilities": [6.0, 11.0],

            # 負債発生
            # 2020 = 40
            # 2021 = 50

            # 資産 - 負債
            "net_lending_financial_account": [60.0, 70.0],

            # 純貸出 + 負債発生 = 資産取得
            "net_lending_plus_liabilities_change": [
                100.0,
                120.0,
            ],
        }
    )


def test_financial_account_identity() -> None:
    df = create_financial_account_test_df()

    result = add_nonfinancial_financial_account_identity(
        df
    )

    # shares_assets / shares_liabilities は
    # 親項目の内数なので二重計上されない
    validate_nonfinancial_financial_account_identity(
        result
    )


def test_financial_account_identity_rejects_mismatch() -> None:
    df = create_financial_account_test_df()

    df.loc[
        0,
        "net_lending_financial_account",
    ] = 65.0

    result = add_nonfinancial_financial_account_identity(
        df
    )

    with pytest.raises(ValueError):
        validate_nonfinancial_financial_account_identity(
            result
        )


def test_capital_financial_discrepancy_is_preserved() -> None:
    capital = pd.DataFrame(
        {
            "fiscal_year": [2020, 2021],
            "gross_fixed_capital_formation": [40.0, 45.0],
            "consumption_fixed_capital": [10.0, 10.0],
            "changes_in_inventories": [5.0, 5.0],
            "net_land_purchases": [2.0, 2.0],
            "net_saving": [50.0, 60.0],
            "capital_transfers_received": [4.0, 3.0],
            "capital_transfers_paid": [1.0, 1.0],

            # 2020:
            # 50 + (4 - 1)
            # - [(40 - 10) + 5 + 2]
            # = 16
            #
            # 2021:
            # 60 + (3 - 1)
            # - [(45 - 10) + 5 + 2]
            # = 20
            "net_lending_capital_account": [16.0, 20.0],
        }
    )

    financial = create_financial_account_test_df()

    result = (
        calculate_capital_financial_net_lending_discrepancy(
            capital,
            financial,
        )
    )

    # 資本勘定と金融勘定は一致を要求しない
    assert result.loc[
        0,
        "capital_financial_discrepancy",
    ] == pytest.approx(-44.0)

    assert result.loc[
        1,
        "capital_financial_discrepancy",
    ] == pytest.approx(-50.0)

    assert result.loc[
        1,
        "cumulative_capital_financial_discrepancy",
    ] == pytest.approx(-94.0)


def test_cumulative_financial_components_reconcile() -> None:
    df = create_financial_account_test_df()

    result = summarize_cumulative_financial_components(
        df,
        start_year=2020,
        end_year=2021,
    )

    # 金融勘定の累積純貸出
    # 60 + 70 = 130
    contribution_sum = result[
        "net_lending_contribution"
    ].sum()

    assert contribution_sum == pytest.approx(
        130.0
    )

    asset_total = result.loc[
        result["side"] == "金融資産",
        "cumulative_amount",
    ].sum()

    liability_total = result.loc[
        result["side"] == "負債",
        "cumulative_amount",
    ].sum()

    assert asset_total == pytest.approx(
        220.0
    )

    assert liability_total == pytest.approx(
        90.0
    )

    assert (
        asset_total - liability_total
    ) == pytest.approx(130.0)


def create_capital_account_test_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2020, 2021, 2022],
            "net_saving": [50.0, 60.0, 70.0],
            "capital_transfers_received": [4.0, 3.0, 5.0],
            "capital_transfers_paid": [1.0, 1.0, 2.0],
            "gross_fixed_capital_formation": [40.0, 45.0, 50.0],
            "consumption_fixed_capital": [10.0, 10.0, 10.0],
            "changes_in_inventories": [5.0, 5.0, 5.0],
            "net_land_purchases": [2.0, 2.0, 2.0],

            # 2020:
            # 50 + 3 - [(40 - 10) + 5 + 2] = 16
            #
            # 2021:
            # 60 + 2 - [(45 - 10) + 5 + 2] = 20
            #
            # 2022:
            # 70 + 3 - [(50 - 10) + 5 + 2] = 26
            "net_lending_capital_account": [
                16.0,
                20.0,
                26.0,
            ],
        }
    )


def test_calculate_cumulative_capital_account() -> None:
    df = create_capital_account_test_df()

    result = calculate_cumulative_capital_account(
        df,
        start_year=2020,
        end_year=2022,
    )

    assert result.loc[
        2,
        "cumulative_net_saving",
    ] == pytest.approx(180.0)

    assert result.loc[
        2,
        "cumulative_net_capital_transfers",
    ] == pytest.approx(8.0)

    # net fixed capital formation:
    # 30 + 35 + 40 = 105
    assert result.loc[
        2,
        "cumulative_net_fixed_capital_formation",
    ] == pytest.approx(105.0)

    # inventories: 15
    assert result.loc[
        2,
        "cumulative_changes_in_inventories",
    ] == pytest.approx(15.0)

    # land: 6
    assert result.loc[
        2,
        "cumulative_net_land_purchases",
    ] == pytest.approx(6.0)

    # net capital formation:
    # 105 + 15 + 6 = 126
    assert result.loc[
        2,
        "cumulative_net_capital_formation",
    ] == pytest.approx(126.0)

    # 16 + 20 + 26 = 62
    assert result.loc[
        2,
        "cumulative_net_lending_capital_account",
    ] == pytest.approx(62.0)


def test_summarize_cumulative_capital_account() -> None:
    df = create_capital_account_test_df()

    summary = summarize_cumulative_capital_account(
        df,
        start_year=2020,
        end_year=2022,
    )

    row = summary.iloc[0]

    assert row[
        "cumulative_net_saving"
    ] == pytest.approx(180.0)

    assert row[
        "cumulative_net_capital_transfers"
    ] == pytest.approx(8.0)

    assert row[
        "cumulative_net_fixed_capital_formation"
    ] == pytest.approx(105.0)

    assert row[
        "cumulative_changes_in_inventories"
    ] == pytest.approx(15.0)

    assert row[
        "cumulative_net_land_purchases"
    ] == pytest.approx(6.0)

    assert row[
        "cumulative_net_capital_formation"
    ] == pytest.approx(126.0)

    assert row[
        "cumulative_net_lending"
    ] == pytest.approx(62.0)

    assert row[
        "cumulative_sources"
    ] == pytest.approx(188.0)

    assert row[
        "capital_formation_share_pct"
    ] == pytest.approx(
        126.0 / 188.0 * 100
    )

    assert row[
        "net_lending_share_pct"
    ] == pytest.approx(
        62.0 / 188.0 * 100
    )

    assert row[
        "identity_residual"
    ] == pytest.approx(0.0)


def test_cumulative_capital_account_rejects_missing_year() -> None:
    df = create_capital_account_test_df()

    df = df[
        df["fiscal_year"] != 2021
    ].reset_index(drop=True)

    with pytest.raises(
        ValueError,
        match="年度",
    ):
        calculate_cumulative_capital_account(
            df,
            start_year=2020,
            end_year=2022,
        )


def test_cumulative_capital_account_rejects_invalid_period() -> None:
    df = create_capital_account_test_df()

    with pytest.raises(ValueError):
        calculate_cumulative_capital_account(
            df,
            start_year=2022,
            end_year=2020,
        )
