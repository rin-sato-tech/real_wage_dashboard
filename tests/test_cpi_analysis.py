import pandas as pd
import pytest

from real_wage_dashboard.cpi_analysis import add_cpi_changes


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
