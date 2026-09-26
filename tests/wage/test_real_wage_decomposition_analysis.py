import pandas as pd
import pytest

from real_wage_dashboard.real_wage_decomposition_analysis import (
    build_real_wage_decomposition_data,
    create_complete_annual_cpi,
    summarize_chained_period_change,
)


def test_create_complete_annual_cpi_uses_only_complete_years():
    dates = pd.to_datetime(
        [f"2020-{month:02d}-01" for month in range(1, 13)]
        + [f"2021-{month:02d}-01" for month in range(1, 12)]
    )
    values = [100.0] * 12 + [101.0] * 11

    df = pd.DataFrame(
        {
            "date": dates,
            "index_value": values,
        }
    )

    result = create_complete_annual_cpi(df)

    assert result["year"].tolist() == [2020]
    assert result["cpi"].iloc[0] == pytest.approx(100.0)


def test_summarize_chained_period_change():
    df = pd.DataFrame(
        {
            "year": [2020, 2021, 2022],
            "published_nominal_yoy_pct": [0.0, 10.0, 10.0],
            "cpi_yoy_pct": [0.0, 5.0, 5.0],
        }
    )

    result = summarize_chained_period_change(
        df,
        start_year=2020,
        end_year=2022,
    )

    expected_nominal = 1.10 * 1.10 - 1
    expected_cpi = 1.05 * 1.05 - 1
    expected_real = (1.10 * 1.10) / (1.05 * 1.05) - 1

    assert result["nominal_change_pct"] == pytest.approx(expected_nominal * 100)
    assert result["cpi_change_pct"] == pytest.approx(expected_cpi * 100)
    assert result["mechanical_real_change_pct"] == pytest.approx(expected_real * 100)
    assert result["real_log_change"] == pytest.approx(
        result["nominal_log_contribution"] + result["price_log_contribution"]
    )


def test_summarize_chained_period_change_rejects_missing_year():
    df = pd.DataFrame(
        {
            "year": [2020, 2022],
            "published_nominal_yoy_pct": [0.0, 2.0],
            "cpi_yoy_pct": [0.0, 1.0],
        }
    )

    with pytest.raises(ValueError, match="必要な年が不足"):
        summarize_chained_period_change(
            df,
            start_year=2020,
            end_year=2022,
        )


def test_build_real_wage_decomposition_identity():
    wage_index = pd.DataFrame(
        {
            "year": [2019, 2020, 2021],
            "index_value": [99.0, 100.0, 102.0],
        }
    )

    wage_yoy = pd.DataFrame(
        {
            "year": [2019, 2020, 2021],
            "published_yoy_pct": [0.0, 1.0, 2.0],
        }
    )

    official_real_index = pd.DataFrame(
        {
            "year": [2019, 2020, 2021],
            "index_value": [99.0, 100.0, 101.0],
        }
    )

    official_real_yoy = pd.DataFrame(
        {
            "year": [2019, 2020, 2021],
            "published_yoy_pct": [0.0, 1.0, 1.0],
        }
    )

    cpi = pd.DataFrame(
        {
            "year": [2019, 2020, 2021],
            "cpi": [100.0, 100.0, 101.0],
            "cpi_yoy_pct": [0.0, 0.0, 1.0],
        }
    )

    result = build_real_wage_decomposition_data(
        wage_index_df=wage_index,
        wage_yoy_df=wage_yoy,
        official_real_index_df=official_real_index,
        official_real_yoy_df=official_real_yoy,
        cpi_annual_df=cpi,
    )

    error = (
        (
            result["nominal_log_contribution"]
            + result["price_log_contribution"]
            - result["real_log_change"]
        )
        .abs()
        .max()
    )

    assert error == pytest.approx(0.0)

    row_2021 = result.loc[result["year"] == 2021].iloc[0]
    expected = ((1.02 / 1.01) - 1) * 100

    assert row_2021["mechanical_real_yoy_pct"] == pytest.approx(expected)
