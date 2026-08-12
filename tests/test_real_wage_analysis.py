import pandas as pd
import pytest

from real_wage_dashboard.real_wage_analysis import (
    add_real_wage_amount,
    add_real_wage_changes,
    add_wage_indices,
    merge_wage_and_cpi,
)


def test_merge_wage_and_cpi() -> None:
    wage_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                ]
            ),
            "nominal_wage_amount": [
                300000,
                310000,
            ],
        }
    )

    cpi_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                ]
            ),
            "index_value": [
                110.0,
                111.0,
            ],
        }
    )

    result = merge_wage_and_cpi(
        wage_df,
        cpi_df,
    )

    assert len(result) == 2


def test_add_real_wage_amount() -> None:
    df = pd.DataFrame(
        {
            "nominal_wage_amount": [
                300000,
            ],
            "index_value": [
                120.0,
            ],
        }
    )

    result = add_real_wage_amount(df)

    assert result.loc[0, "real_wage_amount"] == pytest.approx(250000)


def test_add_wage_indices() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-02-01",
                ]
            ),
            "nominal_wage_amount": [
                100,
                100,
            ],
            "real_wage_amount": [
                100,
                100,
            ],
        }
    )

    result = add_wage_indices(df)

    assert result["nominal_wage_index"].mean() == pytest.approx(100)
    assert result["real_wage_index"].mean() == pytest.approx(100)


def test_add_wage_indices_raises_when_base_year_missing() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01"]),
            "nominal_wage_amount": [
                100,
            ],
            "real_wage_amount": [
                100,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="2020年の基準データがありません",
    ):
        add_wage_indices(df)


def test_add_real_wage_changes_calculates_yoy() -> None:
    dates = pd.date_range(
        "2024-01-01",
        periods=13,
        freq="MS",
    )

    df = pd.DataFrame(
        {
            "date": dates,
            "real_wage_amount": [
                100000,
                100000,
                100000,
                100000,
                100000,
                100000,
                100000,
                100000,
                100000,
                100000,
                100000,
                100000,
                105000,
            ],
            "real_wage_index": [100.0] * 12 + [105.0],
        }
    )

    result = add_real_wage_changes(df)

    assert pd.isna(result.loc[11, "real_wage_yoy_pct"])

    assert result.loc[
        12,
        "real_wage_yoy_pct",
    ] == pytest.approx(5.0)
