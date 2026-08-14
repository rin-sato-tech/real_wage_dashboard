import pandas as pd
import pytest

from real_wage_dashboard.real_wage_analysis import (
    add_real_wage_amount,
    add_real_wage_changes,
    add_real_wage_moving_average,
    add_wage_indices,
    create_real_wage_dataframe,
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


def test_merge_wage_and_cpi_raises_when_wage_dates_are_duplicated() -> None:
    wage_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-01-01",
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
            "date": pd.to_datetime(["2025-01-01"]),
            "index_value": [110.0],
        }
    )

    with pytest.raises(
        pd.errors.MergeError,
    ):
        merge_wage_and_cpi(
            wage_df,
            cpi_df,
        )


def test_merge_wage_and_cpi_raises_when_cpi_dates_are_duplicated() -> None:
    wage_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01"]),
            "nominal_wage_amount": [300000],
        }
    )

    cpi_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-01-01",
                ]
            ),
            "index_value": [
                110.0,
                111.0,
            ],
        }
    )

    with pytest.raises(
        pd.errors.MergeError,
    ):
        merge_wage_and_cpi(
            wage_df,
            cpi_df,
        )


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


def test_add_real_wage_amount_raises_when_cpi_is_zero() -> None:
    df = pd.DataFrame(
        {
            "nominal_wage_amount": [300000],
            "index_value": [0.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="CPIには0より大きい値が必要です",
    ):
        add_real_wage_amount(df)


def test_add_real_wage_moving_average_starts_after_12_months() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=13,
                freq="MS",
            ),
            "real_wage_amount": range(100, 113),
        }
    )

    result = add_real_wage_moving_average(df)

    assert result.loc[:10, "real_wage_ma_12"].isna().all()

    assert result.loc[
        11,
        "real_wage_ma_12",
    ] == pytest.approx(105.5)

    assert result.loc[
        12,
        "real_wage_ma_12",
    ] == pytest.approx(106.5)


def test_add_real_wage_moving_average_is_nan_when_month_is_missing() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=13,
                freq="MS",
            ),
            "real_wage_amount": range(100, 113),
        }
    )

    df = df.drop(index=5).reset_index(drop=True)

    result = add_real_wage_moving_average(df)

    assert result["real_wage_ma_12"].isna().all()


def test_real_wage_moving_average_is_calculated_after_deflation() -> None:
    dates = pd.date_range(
        "2020-01-01",
        periods=12,
        freq="MS",
    )

    wage_df = pd.DataFrame(
        {
            "date": dates,
            "nominal_wage_amount": [100.0] * 12,
        }
    )

    cpi_values = [
        100.0,
        101.0,
        102.0,
        103.0,
        104.0,
        105.0,
        106.0,
        107.0,
        108.0,
        109.0,
        110.0,
        111.0,
    ]

    cpi_df = pd.DataFrame(
        {
            "date": dates,
            "index_value": cpi_values,
        }
    )

    result = create_real_wage_dataframe(
        wage_df,
        cpi_df,
    )

    expected = sum(100.0 / cpi * 100 for cpi in cpi_values) / 12

    assert result.loc[
        11,
        "real_wage_ma_12",
    ] == pytest.approx(expected)


def test_add_wage_indices() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2020-01-01",
                periods=12,
                freq="MS",
            ),
            "nominal_wage_amount": [100] * 12,
            "real_wage_amount": [100] * 12,
        }
    )

    result = add_wage_indices(df)

    assert result["nominal_wage_index"].eq(100).all()
    assert result["real_wage_index"].eq(100).all()


def test_add_wage_indices_raises_when_base_year_missing() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01"]),
            "nominal_wage_amount": [100],
            "real_wage_amount": [100],
        }
    )

    with pytest.raises(
        ValueError,
        match="2020年の基準データが12か月揃っていません",
    ):
        add_wage_indices(df)


def test_add_wage_indices_raises_when_base_year_is_incomplete() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2020-01-01",
                periods=11,
                freq="MS",
            ),
            "nominal_wage_amount": [100] * 11,
            "real_wage_amount": [100] * 11,
        }
    )

    with pytest.raises(
        ValueError,
        match="2020年の基準データが12か月揃っていません",
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


def test_add_real_wage_changes_uses_monthly_real_wage() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=13,
                freq="MS",
            ),
            "real_wage_amount": [
                100,
                100,
                100,
                100,
                100,
                100,
                100,
                100,
                100,
                100,
                100,
                100,
                110,
            ],
            "real_wage_index": [100.0] * 12 + [110.0],
        }
    )

    result = add_real_wage_changes(df)

    assert result.loc[
        12,
        "real_wage_yoy_pct",
    ] == pytest.approx(10.0)
