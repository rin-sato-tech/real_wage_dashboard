import pandas as pd
import pytest

from real_wage_dashboard.macro_distribution_ui import (
    create_household_primary_income_chart,
    create_income_generation_chart,
    create_net_lending_decomposition_chart,
    create_nonfinancial_capital_account_chart,
    prepare_sector_net_lending_chart_data,
)


def test_prepare_sector_net_lending_chart_data_ratio():
    amount_df = pd.DataFrame(
        {
            "fiscal_year": [2023, 2024],
            "capital_nonfinancial_corporations": [
                12000.0,
                14000.0,
            ],
            "capital_households": [
                8000.0,
                13000.0,
            ],
        }
    )

    ratio_df = pd.DataFrame(
        {
            "fiscal_year": [2023, 2024],
            "capital_nonfinancial_corporations": [
                1.9,
                2.2,
            ],
            "capital_households": [
                1.3,
                2.0,
            ],
        }
    )

    result = prepare_sector_net_lending_chart_data(
        amount_df=amount_df,
        ratio_df=ratio_df,
        selected_sectors=[
            "非金融法人企業",
            "家計",
        ],
        display_mode="GDP比",
    )

    assert len(result) == 4

    corporate = result.loc[
        (result["fiscal_year"] == 2024)
        & (result["sector"] == "非金融法人企業")
    ].iloc[0]

    household = result.loc[
        (result["fiscal_year"] == 2024)
        & (result["sector"] == "家計")
    ].iloc[0]

    assert corporate["value"] == pytest.approx(2.2)
    assert household["value"] == pytest.approx(2.0)


def test_prepare_sector_net_lending_chart_data_amount_converts_to_trillion():
    amount_df = pd.DataFrame(
        {
            "fiscal_year": [2024],
            "capital_nonfinancial_corporations": [
                13856.2,
            ],
        }
    )

    ratio_df = pd.DataFrame(
        {
            "fiscal_year": [2024],
            "capital_nonfinancial_corporations": [
                2.156893,
            ],
        }
    )

    result = prepare_sector_net_lending_chart_data(
        amount_df=amount_df,
        ratio_df=ratio_df,
        selected_sectors=[
            "非金融法人企業",
        ],
        display_mode="名目額",
    )

    assert len(result) == 1

    assert result.iloc[0]["value"] == pytest.approx(
        13.8562
    )


def test_prepare_sector_net_lending_chart_data_uses_selected_sector_only():
    amount_df = pd.DataFrame(
        {
            "fiscal_year": [2024],
            "capital_nonfinancial_corporations": [
                13856.2,
            ],
            "capital_households": [
                12900.0,
            ],
        }
    )

    ratio_df = pd.DataFrame(
        {
            "fiscal_year": [2024],
            "capital_nonfinancial_corporations": [
                2.156893,
            ],
            "capital_households": [
                2.0,
            ],
        }
    )

    result = prepare_sector_net_lending_chart_data(
        amount_df=amount_df,
        ratio_df=ratio_df,
        selected_sectors=[
            "家計",
        ],
        display_mode="GDP比",
    )

    assert result["sector"].unique().tolist() == [
        "家計"
    ]


def test_create_income_generation_chart_rejects_unknown_mode():
    df = pd.DataFrame(
        {
            "fiscal_year": [2024],
        }
    )

    with pytest.raises(
        ValueError,
        match="未対応の表示モード",
    ):
        create_income_generation_chart(
            df,
            "不明",
        )


def test_create_household_primary_income_chart_rejects_unknown_mode():
    df = pd.DataFrame(
        {
            "fiscal_year": [2024],
        }
    )

    with pytest.raises(
        ValueError,
        match="未対応の表示モード",
    ):
        create_household_primary_income_chart(
            df,
            "不明",
        )


def test_create_nonfinancial_capital_account_chart_rejects_unknown_mode():
    df = pd.DataFrame(
        {
            "fiscal_year": [2024],
        }
    )

    with pytest.raises(
        ValueError,
        match="未対応の表示モード",
    ):
        create_nonfinancial_capital_account_chart(
            df,
            "不明",
        )


def test_create_net_lending_decomposition_chart_rejects_missing_period():
    df = pd.DataFrame(
        {
            "start_year": [2015],
            "end_year": [2024],
            "component": [
                "net_saving",
            ],
            "contribution_pt": [
                -4.04,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="分解結果がありません",
    ):
        create_net_lending_decomposition_chart(
            df,
            start_year=2010,
            end_year=2015,
        )


def test_create_net_lending_decomposition_chart_rejects_unknown_component():
    df = pd.DataFrame(
        {
            "start_year": [2015],
            "end_year": [2024],
            "component": [
                "unknown_component",
            ],
            "contribution_pt": [
                1.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="未定義の分解要因",
    ):
        create_net_lending_decomposition_chart(
            df,
            start_year=2015,
            end_year=2024,
        )


def test_create_net_lending_decomposition_chart_returns_altair_chart():
    df = pd.DataFrame(
        {
            "start_year": [
                2015,
                2015,
                2015,
            ],
            "end_year": [
                2024,
                2024,
                2024,
            ],
            "component": [
                "net_saving",
                "net_capital_transfers",
                "net_capital_formation",
            ],
            "contribution_pt": [
                -4.041071,
                0.111807,
                -0.527803,
            ],
        }
    )

    chart = create_net_lending_decomposition_chart(
        df,
        start_year=2015,
        end_year=2024,
    )

    spec = chart.to_dict()

    assert spec
    assert "layer" in spec
