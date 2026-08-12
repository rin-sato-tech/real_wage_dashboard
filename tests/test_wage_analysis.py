import pandas as pd
import pytest

from real_wage_dashboard.wage_analysis import add_wage_changes


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
