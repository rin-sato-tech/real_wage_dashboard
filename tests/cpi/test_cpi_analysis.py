import pandas as pd
import pytest

from real_wage_dashboard.cpi_analysis import add_cpi_changes, prepare_annual_cpi


def test_add_cpi_changes_calculates_mom() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                ]
            ),
            "index_value": [100.0, 102.0],
        }
    )

    result = add_cpi_changes(df)

    assert pd.isna(result.loc[0, "mom_pct"])
    assert result.loc[1, "mom_pct"] == pytest.approx(2.0)


def test_add_cpi_changes_raises_when_column_is_missing() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01"]),
        }
    )

    with pytest.raises(ValueError, match="必要な列がありません"):
        add_cpi_changes(df)


def test_annual_cpi_entry_point_preserves_period_and_legacy_import() -> None:
    from real_wage_dashboard.minimum_wage_analysis import (
        prepare_annual_cpi as legacy_prepare_annual_cpi,
    )

    monthly = pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", periods=36, freq="MS"),
            "index_value": [100.0] * 12 + [110.0] * 12 + [120.0] * 12,
        }
    )
    original = monthly.copy(deep=True)
    expected = pd.DataFrame({"year": [2024, 2025], "cpi": [110.0, 120.0]})
    expected["year"] = expected["year"].astype(monthly["date"].dt.year.dtype)

    result = prepare_annual_cpi(monthly, start_year=2024, end_year=2025)

    pd.testing.assert_frame_equal(result, expected)
    pd.testing.assert_frame_equal(
        result, legacy_prepare_annual_cpi(monthly, 2024, 2025)
    )
    pd.testing.assert_frame_equal(monthly, original)
