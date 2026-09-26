from __future__ import annotations

from unittest.mock import Mock

import pytest

import pandas as pd

import real_wage_dashboard.corporate_profit_allocation_service as service


def create_estat_response(
    values: list[dict[str, str]],
) -> dict:
    """テスト用の最小e-Statレスポンスを作成する。"""

    return {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "DATA_INF": {
                    "VALUE": values,
                }
            }
        }
    }


def test_load_nonfinancial_primary_income(
    monkeypatch,
) -> None:
    mock_loader = Mock(
        return_value=pd.DataFrame(
            {
                "fiscal_year": [2020],
                "net_operating_surplus": [100.0],
            }
        )
    )

    monkeypatch.setattr(
        service,
        "load_sna_table",
        mock_loader,
    )

    result = service.load_nonfinancial_primary_income(
        app_id="test-app-id",
        start_year=2020,
        end_year=2021,
    )

    assert result["fiscal_year"].tolist() == [2020]

    kwargs = mock_loader.call_args.kwargs

    assert kwargs["app_id"] == "test-app-id"
    assert (
        kwargs["stats_data_id"]
        == service.SNA_NONFINANCIAL_PRIMARY_INCOME_STATS_DATA_ID
    )
    assert (
        kwargs["items"]
        == service.SNA_NONFINANCIAL_PRIMARY_INCOME_ITEMS
    )
    assert kwargs["start_year"] == 2020
    assert kwargs["end_year"] == 2021


def test_load_nonfinancial_secondary_distribution(
    monkeypatch,
) -> None:
    mock_loader = Mock(
        return_value=pd.DataFrame(
            {
                "fiscal_year": [2020],
                "net_disposable_income": [80.0],
            }
        )
    )

    monkeypatch.setattr(
        service,
        "load_sna_table",
        mock_loader,
    )

    service.load_nonfinancial_secondary_distribution(
        app_id="test-app-id",
        start_year=2020,
        end_year=2021,
    )

    kwargs = mock_loader.call_args.kwargs

    assert (
        kwargs["stats_data_id"]
        == service.SNA_NONFINANCIAL_SECONDARY_DISTRIBUTION_STATS_DATA_ID
    )
    assert (
        kwargs["items"]
        == service.SNA_NONFINANCIAL_SECONDARY_DISTRIBUTION_ITEMS
    )


def test_load_nonfinancial_use_income(
    monkeypatch,
) -> None:
    mock_loader = Mock(
        return_value=pd.DataFrame(
            {
                "fiscal_year": [2020],
                "net_saving": [80.0],
            }
        )
    )

    monkeypatch.setattr(
        service,
        "load_sna_table",
        mock_loader,
    )

    service.load_nonfinancial_use_income(
        app_id="test-app-id",
        start_year=2020,
        end_year=2021,
    )

    kwargs = mock_loader.call_args.kwargs

    assert (
        kwargs["stats_data_id"]
        == service.SNA_NONFINANCIAL_USE_INCOME_STATS_DATA_ID
    )
    assert (
        kwargs["items"]
        == service.SNA_NONFINANCIAL_USE_INCOME_ITEMS
    )


def test_load_sna_financial_detail_table_filters_sector_and_period(
    monkeypatch,
) -> None:
    response = create_estat_response([])

    mock_get_stats_data = Mock(
        return_value=response
    )

    parsed = pd.DataFrame(
        {
            "fiscal_year": [
                2014,
                2015,
                2016,
                2017,
            ],
            "cash_deposits_assets": [
                1.0,
                2.0,
                3.0,
                4.0,
            ],
        }
    )

    mock_create_dataframe = Mock(
        return_value=parsed
    )

    monkeypatch.setattr(
        service,
        "get_stats_data",
        mock_get_stats_data,
    )

    monkeypatch.setattr(
        service,
        "create_sna_dataframe",
        mock_create_dataframe,
    )

    items = {
        "cash_deposits_assets": "140",
        "other_financial_assets": "620",
    }

    result = service.load_sna_financial_detail_table(
        app_id="test-app-id",
        stats_data_id="test-table",
        items=items,
        start_year=2015,
        end_year=2016,
    )

    assert result["fiscal_year"].tolist() == [
        2015,
        2016,
    ]

    api_kwargs = (
        mock_get_stats_data.call_args.kwargs
    )

    assert api_kwargs["app_id"] == "test-app-id"
    assert (
        api_kwargs["stats_data_id"]
        == "test-table"
    )

    filters = api_kwargs["filters"]

    assert filters["cdTab"] == "11"
    assert filters["cdCat01"] == "140,620"
    assert (
        filters["cdCat02"]
        == service.SNA_NONFINANCIAL_CORPORATIONS_SECTOR_CODE
    )

    # この表では特殊なtime codeがあるため
    # API段階でcdTimeを指定していないことを確認
    assert "cdTime" not in filters


def test_financial_detail_wrappers_use_correct_tables(
    monkeypatch,
) -> None:
    mock_loader = Mock(
        return_value=pd.DataFrame(
            {
                "fiscal_year": [2020],
            }
        )
    )

    monkeypatch.setattr(
        service,
        "load_sna_financial_detail_table",
        mock_loader,
    )

    service.load_nonfinancial_financial_assets_detail(
        app_id="test-app-id",
        start_year=2020,
        end_year=2021,
    )

    asset_kwargs = (
        mock_loader.call_args.kwargs
    )

    assert (
        asset_kwargs["stats_data_id"]
        == service.SNA_FINANCIAL_ASSETS_DETAIL_STATS_DATA_ID
    )

    assert (
        asset_kwargs["items"]
        == service.SNA_FINANCIAL_ASSETS_DETAIL_ITEMS
    )

    mock_loader.reset_mock()

    service.load_nonfinancial_financial_liabilities_detail(
        app_id="test-app-id",
        start_year=2020,
        end_year=2021,
    )

    liability_kwargs = (
        mock_loader.call_args.kwargs
    )

    assert (
        liability_kwargs["stats_data_id"]
        == service.SNA_FINANCIAL_LIABILITIES_DETAIL_STATS_DATA_ID
    )

    assert (
        liability_kwargs["items"]
        == service.SNA_FINANCIAL_LIABILITIES_DETAIL_ITEMS
    )


def test_load_sna_calendar_table_filters_calendar_year(
    monkeypatch,
) -> None:
    response = create_estat_response([])

    monkeypatch.setattr(
        service,
        "get_stats_data",
        Mock(return_value=response),
    )

    parsed = pd.DataFrame(
        {
            "fiscal_year": [
                2013,
                2014,
                2015,
                2016,
            ],
            "financial_assets": [
                100.0,
                110.0,
                120.0,
                130.0,
            ],
        }
    )

    monkeypatch.setattr(
        service,
        "create_sna_dataframe",
        Mock(return_value=parsed),
    )

    result = service.load_sna_calendar_table(
        app_id="test-app-id",
        stats_data_id="test-table",
        items={
            "financial_assets": "450",
        },
        start_year=2014,
        end_year=2015,
    )

    assert result[
        "calendar_year"
    ].tolist() == [
        2014,
        2015,
    ]

    assert "fiscal_year" not in result.columns


def test_calendar_table_rejects_invalid_period() -> None:
    with pytest.raises(ValueError):
        service.load_sna_calendar_table(
            app_id="test-app-id",
            stats_data_id="test-table",
            items={
                "financial_assets": "450",
            },
            start_year=2024,
            end_year=2014,
        )


def test_load_corporate_profit_allocation_uses_all_industries_all_sizes(
    monkeypatch,
) -> None:
    response = create_estat_response([])

    mock_get_stats_data = Mock(
        return_value=response
    )

    mock_create_dataframe = Mock(
        return_value=pd.DataFrame(
            {
                "fiscal_year": [2020],
                "net_income": [100.0],
            }
        )
    )

    monkeypatch.setattr(
        service,
        "get_stats_data",
        mock_get_stats_data,
    )

    monkeypatch.setattr(
        service,
        "create_corporate_profit_allocation_dataframe",
        mock_create_dataframe,
    )

    result = service.load_corporate_profit_allocation(
        app_id="test-app-id",
        start_year=2020,
        end_year=2021,
    )

    assert result["fiscal_year"].tolist() == [2020]

    kwargs = (
        mock_get_stats_data.call_args.kwargs
    )

    assert kwargs["app_id"] == "test-app-id"
    assert (
        kwargs["stats_data_id"]
        == service.CORPORATE_STATS_DATA_ID
    )

    filters = kwargs["filters"]

    assert (
        filters["cdCat02"]
        == service.CORPORATE_INDUSTRIES[
            "全産業（除く金融保険業）"
        ]
    )

    assert (
        filters["cdCat03"]
        == service.CORPORATE_CAPITAL_CLASSES[
            "全規模"
        ]
    )

    assert filters["cdTime"] == "20200,20210"
