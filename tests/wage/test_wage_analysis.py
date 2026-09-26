import pandas as pd
import pytest

from real_wage_dashboard.wage_analysis import (
    add_moving_average,
    add_wage_changes,
    add_wage_moving_average,
)


def test_add_wage_changes_calculates_mom() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                ]
            ),
            "nominal_wage_amount": [
                100000,
                102000,
            ],
        }
    )

    result = add_wage_changes(df)

    assert pd.isna(result.loc[0, "mom_pct"])

    assert result.loc[
        1,
        "mom_pct",
    ] == pytest.approx(2.0)


def test_add_wage_changes_calculates_yoy() -> None:
    dates = pd.date_range(
        "2024-01-01",
        periods=13,
        freq="MS",
    )

    values = [
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
    ]

    df = pd.DataFrame(
        {
            "date": dates,
            "nominal_wage_amount": values,
        }
    )

    result = add_wage_changes(df)

    assert pd.isna(result.loc[11, "yoy_pct"])

    assert result.loc[
        12,
        "yoy_pct",
    ] == pytest.approx(5.0)


def test_add_wage_changes_raises_when_column_is_missing() -> None:
    df = pd.DataFrame({"date": pd.to_datetime(["2025-01-01"])})

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        add_wage_changes(df)


def test_add_wage_moving_average_starts_after_12_months() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=13,
                freq="MS",
            ),
            "nominal_wage_amount": range(100, 113),
        }
    )

    result = add_wage_moving_average(df)

    assert result.loc[:10, "nominal_wage_ma_12"].isna().all()

    assert result.loc[11, "nominal_wage_ma_12"] == pytest.approx(105.5)

    assert result.loc[12, "nominal_wage_ma_12"] == pytest.approx(106.5)


def test_add_wage_moving_average_is_nan_when_month_is_missing() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=13,
                freq="MS",
            ),
            "nominal_wage_amount": range(100, 113),
        }
    )

    df = df.drop(index=5).reset_index(drop=True)

    result = add_wage_moving_average(df)

    assert result["nominal_wage_ma_12"].isna().all()


def test_add_moving_average_uses_specified_column() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
            "value": range(1, 13),
        }
    )

    result = add_moving_average(
        df,
        column="value",
        output_column="value_ma_12",
        window=12,
    )

    assert result.loc[11, "value_ma_12"] == pytest.approx(6.5)


def test_add_moving_average_raises_when_window_is_invalid() -> None:
    df = pd.DataFrame(
        {
            "date": [pd.Timestamp("2025-01-01")],
            "nominal_wage_amount": [100],
        }
    )

    with pytest.raises(
        ValueError,
        match="windowは1以上",
    ):
        add_moving_average(
            df,
            column="nominal_wage_amount",
            output_column="nominal_wage_ma",
            window=0,
        )


def test_add_moving_average_raises_when_column_is_missing() -> None:
    df = pd.DataFrame(
        {
            "date": [pd.Timestamp("2025-01-01")],
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        add_moving_average(
            df,
            column="nominal_wage_amount",
            output_column="nominal_wage_ma_12",
            window=12,
        )


def test_add_wage_changes_uses_monthly_values_not_moving_average() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=13,
                freq="MS",
            ),
            "nominal_wage_amount": [
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
        }
    )

    result = add_wage_changes(df)

    assert result.loc[12, "yoy_pct"] == pytest.approx(10.0)
