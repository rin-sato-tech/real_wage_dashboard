import pandas as pd
import pytest

from real_wage_dashboard.macro_distribution_analysis import (
    add_household_disposable_income_identity,
    add_household_primary_income_identity,
    add_household_saving_identity,
    add_income_generation_identity,
    add_nonfinancial_capital_account_identity,
    calculate_household_primary_income_components,
    calculate_household_redistribution_components,
    calculate_household_saving_metrics,
    calculate_income_generation_shares,
    calculate_sector_net_lending_ratios,
    decompose_net_lending_change,
    prepare_sector_net_lending_long,
    validate_household_disposable_income_identity,
    validate_household_primary_income_identity,
    validate_household_saving_identity,
    validate_income_generation_identity,
    validate_published_saving_rate,
)


def make_income_generation_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2024],
            "employee_compensation": [314065.9],
            "gross_domestic_product": [635981.5],
            "gross_operating_surplus": [259437.5],
            "gross_mixed_income": [13463.0],
            "taxes_on_production_and_imports": [56081.9],
            "subsidies": [7066.7],
        }
    )


def test_add_income_generation_identity() -> None:
    df = make_income_generation_df()

    result = add_income_generation_identity(df)

    assert result.loc[
        0,
        "net_taxes_on_production_and_imports",
    ] == pytest.approx(49015.2)

    assert result.loc[
        0,
        "calculated_gdp",
    ] == pytest.approx(635981.6)

    assert result.loc[
        0,
        "gdp_identity_residual",
    ] == pytest.approx(0.1)


def test_validate_income_generation_identity() -> None:
    df = make_income_generation_df()

    validate_income_generation_identity(
        df,
        tolerance=0.2,
    )


def test_validate_income_generation_identity_rejects_large_error() -> None:
    df = make_income_generation_df()

    df.loc[
        0,
        "employee_compensation",
    ] += 100.0

    with pytest.raises(
        ValueError,
        match="GDP所得面恒等式",
    ):
        validate_income_generation_identity(
            df,
            tolerance=0.2,
        )


def test_calculate_income_generation_shares() -> None:
    df = make_income_generation_df()

    result = calculate_income_generation_shares(df)

    assert result.loc[
        0,
        "employee_compensation_share",
    ] == pytest.approx(
        314065.9 / 635981.5 * 100
    )

    assert result.loc[
        0,
        "gross_operating_surplus_share",
    ] == pytest.approx(
        259437.5 / 635981.5 * 100
    )

    assert result.loc[
        0,
        "gross_mixed_income_share",
    ] == pytest.approx(
        13463.0 / 635981.5 * 100
    )

    assert result.loc[
        0,
        "net_production_tax_share",
    ] == pytest.approx(
        (56081.9 - 7066.7)
        / 635981.5
        * 100
    )

    assert result.loc[
        0,
        "income_component_share_sum",
    ] == pytest.approx(
        100.0,
        abs=0.001,
    )


def test_calculate_income_generation_shares_rejects_nonpositive_gdp() -> None:
    df = make_income_generation_df()

    df.loc[
        0,
        "gross_domestic_product",
    ] = 0.0

    with pytest.raises(
        ValueError,
        match="GDPは正",
    ):
        calculate_income_generation_shares(df)


def test_income_generation_requires_columns() -> None:
    df = make_income_generation_df().drop(
        columns="gross_mixed_income"
    )

    with pytest.raises(
        ValueError,
        match="必要な列",
    ):
        calculate_income_generation_shares(df)


def make_household_primary_income_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2024],
            "net_primary_income_balance": [400.0],
            "net_operating_surplus_mixed_income": [50.0],
            "employee_compensation_received": [300.0],
            "property_income_received": [80.0],
            "property_income_paid": [30.0],
        }
    )


def test_add_household_primary_income_identity() -> None:
    df = make_household_primary_income_df()

    result = add_household_primary_income_identity(df)

    assert result.loc[
        0,
        "net_property_income",
    ] == pytest.approx(50.0)

    assert result.loc[
        0,
        "calculated_net_primary_income",
    ] == pytest.approx(400.0)

    assert result.loc[
        0,
        "primary_income_identity_residual",
    ] == pytest.approx(0.0)


def test_validate_household_primary_income_identity() -> None:
    df = make_household_primary_income_df()

    validate_household_primary_income_identity(df)


def test_validate_household_primary_income_identity_rejects_error() -> None:
    df = make_household_primary_income_df()

    df.loc[
        0,
        "property_income_received",
    ] += 10.0

    with pytest.raises(
        ValueError,
        match="家計第1次所得恒等式",
    ):
        validate_household_primary_income_identity(df)


def test_calculate_household_primary_income_components() -> None:
    df = make_household_primary_income_df()

    result = calculate_household_primary_income_components(df)

    assert result.loc[
        0,
        "employee_compensation_ratio",
    ] == pytest.approx(75.0)

    assert result.loc[
        0,
        "operating_mixed_income_ratio",
    ] == pytest.approx(12.5)

    assert result.loc[
        0,
        "net_property_income_ratio",
    ] == pytest.approx(12.5)

    assert result.loc[
        0,
        "primary_income_component_ratio_sum",
    ] == pytest.approx(100.0)


def test_household_primary_income_requires_columns() -> None:
    df = make_household_primary_income_df().drop(
        columns="property_income_paid"
    )

    with pytest.raises(
        ValueError,
        match="家計第1次所得分析に必要な列",
    ):
        calculate_household_primary_income_components(df)


def make_household_secondary_distribution_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2024],
            "net_primary_income_balance": [400.0],
            "current_taxes_paid": [40.0],
            "net_social_contributions_paid": [80.0],
            "other_current_transfers_paid": [10.0],
            "social_benefits_received": [100.0],
            "other_current_transfers_received": [5.0],
            "net_disposable_income": [375.0],
        }
    )


def test_add_household_disposable_income_identity() -> None:
    df = make_household_secondary_distribution_df()

    result = add_household_disposable_income_identity(df)

    assert result.loc[
        0,
        "net_other_current_transfers",
    ] == pytest.approx(-5.0)

    assert result.loc[
        0,
        "calculated_net_disposable_income",
    ] == pytest.approx(375.0)

    assert result.loc[
        0,
        "disposable_income_identity_residual",
    ] == pytest.approx(0.0)


def test_validate_household_disposable_income_identity() -> None:
    df = make_household_secondary_distribution_df()

    validate_household_disposable_income_identity(df)


def test_validate_household_disposable_income_identity_rejects_error() -> None:
    df = make_household_secondary_distribution_df()

    df.loc[
        0,
        "net_disposable_income",
    ] += 10.0

    with pytest.raises(
        ValueError,
        match="家計可処分所得恒等式",
    ):
        validate_household_disposable_income_identity(df)


def test_calculate_household_redistribution_components() -> None:
    df = make_household_secondary_distribution_df()

    result = calculate_household_redistribution_components(df)

    assert result.loc[
        0,
        "current_taxes_ratio",
    ] == pytest.approx(10.0)

    assert result.loc[
        0,
        "net_social_contributions_ratio",
    ] == pytest.approx(20.0)

    assert result.loc[
        0,
        "social_benefits_ratio",
    ] == pytest.approx(25.0)

    assert result.loc[
        0,
        "net_other_current_transfers_ratio",
    ] == pytest.approx(-1.25)

    assert result.loc[
        0,
        "disposable_income_to_primary_income_ratio",
    ] == pytest.approx(93.75)

    assert result.loc[
        0,
        "net_redistribution",
    ] == pytest.approx(-25.0)

    assert result.loc[
        0,
        "net_redistribution_ratio",
    ] == pytest.approx(-6.25)


def test_household_secondary_distribution_requires_columns() -> None:
    df = make_household_secondary_distribution_df().drop(
        columns="social_benefits_received"
    )

    with pytest.raises(
        ValueError,
        match="家計第2次所得分配分析に必要な列",
    ):
        calculate_household_redistribution_components(df)


def make_household_use_income_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2024],
            "household_final_consumption": [330.0],
            "net_saving": [40.0],
            "net_disposable_income": [360.0],
            "pension_entitlement_adjustment": [10.0],
            "published_saving_rate": [10.8],
        }
    )


def test_add_household_saving_identity() -> None:
    df = make_household_use_income_df()

    result = add_household_saving_identity(df)

    assert result.loc[
        0,
        "adjusted_disposable_income",
    ] == pytest.approx(370.0)

    assert result.loc[
        0,
        "calculated_net_saving",
    ] == pytest.approx(40.0)

    assert result.loc[
        0,
        "saving_identity_residual",
    ] == pytest.approx(0.0)


def test_validate_household_saving_identity() -> None:
    df = make_household_use_income_df()

    validate_household_saving_identity(df)


def test_validate_household_saving_identity_rejects_error() -> None:
    df = make_household_use_income_df()

    df.loc[
        0,
        "net_saving",
    ] += 10.0

    with pytest.raises(
        ValueError,
        match="家計純貯蓄恒等式",
    ):
        validate_household_saving_identity(df)


def test_calculate_household_saving_metrics() -> None:
    df = make_household_use_income_df()

    result = calculate_household_saving_metrics(df)

    expected_rate = 40.0 / 370.0 * 100

    assert result.loc[
        0,
        "calculated_saving_rate",
    ] == pytest.approx(expected_rate)

    assert result.loc[
        0,
        "saving_rate_difference",
    ] == pytest.approx(
        expected_rate - 10.8
    )

    assert result.loc[
        0,
        "consumption_ratio",
    ] == pytest.approx(
        330.0 / 370.0 * 100
    )

    assert result.loc[
        0,
        "saving_consumption_ratio_sum",
    ] == pytest.approx(100.0)


def test_household_use_income_requires_columns() -> None:
    df = make_household_use_income_df().drop(
        columns="pension_entitlement_adjustment"
    )

    with pytest.raises(
        ValueError,
        match="家計所得使用分析に必要な列",
    ):
        calculate_household_saving_metrics(df)


def test_validate_published_saving_rate() -> None:
    df = make_household_use_income_df()

    validate_published_saving_rate(
        df,
        tolerance=0.1,
    )


def test_prepare_sector_net_lending_long() -> None:
    amount_df = pd.DataFrame(
        {
            "fiscal_year": [2024],
            "capital_nonfinancial_corporations": [10.0],
            "financial_nonfinancial_corporations": [8.0],
            "capital_financial_corporations": [2.0],
            "financial_financial_corporations": [1.0],
            "capital_general_government": [-5.0],
            "financial_general_government": [-4.0],
            "capital_households": [3.0],
            "financial_households": [2.0],
            "capital_npish": [0.0],
            "financial_npish": [0.0],
            "capital_rest_of_world": [-10.0],
            "financial_rest_of_world": [-7.0],
            "statistical_discrepancy": [0.0],
        }
    )

    ratio_df = amount_df.copy()

    result = prepare_sector_net_lending_long(
        amount_df,
        ratio_df,
    )

    assert len(result) == 6

    row = result[
        result["sector"]
        == "nonfinancial_corporations"
    ].iloc[0]

    assert row["capital_net_lending"] == pytest.approx(
        10.0
    )

    assert row[
        "capital_financial_difference"
    ] == pytest.approx(2.0)


def test_calculate_sector_net_lending_ratios_uses_expenditure_side_gdp() -> None:
    amount_df = pd.DataFrame(
        {
            "fiscal_year": [2024],
            "capital_nonfinancial_corporations": [22.0],
            "capital_financial_corporations": [0.0],
            "capital_general_government": [0.0],
            "capital_households": [0.0],
            "capital_npish": [0.0],
            "capital_rest_of_world": [0.0],
            "statistical_discrepancy": [10.0],
            "financial_nonfinancial_corporations": [0.0],
            "financial_financial_corporations": [0.0],
            "financial_general_government": [0.0],
            "financial_households": [0.0],
            "financial_npish": [0.0],
            "financial_rest_of_world": [0.0],
        }
    )

    income_generation_df = pd.DataFrame(
        {
            "fiscal_year": [2024],
            "gross_domestic_product": [1000.0],
        }
    )

    result = calculate_sector_net_lending_ratios(
        amount_df=amount_df,
        income_generation_df=income_generation_df,
    )

    assert result.loc[
        0,
        "expenditure_side_gdp",
    ] == pytest.approx(1010.0)

    assert result.loc[
        0,
        "capital_nonfinancial_corporations",
    ] == pytest.approx(
        22.0 / 1010.0 * 100
    )


def make_nonfinancial_capital_account_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2024],
            "gross_fixed_capital_formation": [100.0],
            "consumption_fixed_capital": [60.0],
            "changes_in_inventories": [5.0],
            "net_land_purchases": [-2.0],
            "net_lending_capital_account": [30.0],
            "net_saving": [70.0],
            "capital_transfers_received": [10.0],
            "capital_transfers_paid": [7.0],
        }
    )


def test_add_nonfinancial_capital_account_identity() -> None:
    df = make_nonfinancial_capital_account_df()

    result = add_nonfinancial_capital_account_identity(df)

    assert result.loc[
        0,
        "net_fixed_capital_formation",
    ] == pytest.approx(40.0)

    assert result.loc[
        0,
        "net_capital_formation",
    ] == pytest.approx(43.0)

    assert result.loc[
        0,
        "net_capital_transfers",
    ] == pytest.approx(3.0)

    assert result.loc[
        0,
        "calculated_net_lending",
    ] == pytest.approx(30.0)

    assert result.loc[
        0,
        "net_lending_identity_residual",
    ] == pytest.approx(0.0)


def test_decompose_net_lending_change() -> None:
    df = pd.DataFrame(
        {
            "fiscal_year": [2015, 2024],
            "net_saving_ratio": [8.0, 7.0],
            "net_capital_transfers_ratio": [0.0, 0.2],
            "net_capital_formation_ratio": [2.0, 5.0],
            "net_lending_capital_account_ratio": [6.0, 2.2],
        }
    )

    result = decompose_net_lending_change(
        df,
        start_year=2015,
        end_year=2024,
    )

    assert result["contribution_pt"].sum() == pytest.approx(
        -3.8
    )

    assert result["actual_change_pt"].iloc[0] == pytest.approx(
        -3.8
    )

    assert result["decomposition_residual"].iloc[0] == pytest.approx(
        0.0
    )
