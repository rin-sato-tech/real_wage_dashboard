import pandas as pd
import pytest

from real_wage_dashboard.wage_service import create_wage_dataframe


def test_create_wage_dataframe() -> None:
    raw_df = pd.DataFrame(
        {
            "年": [
                2025,
                2025,
                2025,
                2025,
            ],
            "月": [
                "02",
                "01",
                "01",
                "CY",
            ],
            "産業分類": [
                "TL",
                "TL",
                "C",
                "TL",
            ],
            "規模": [
                "T",
                "T",
                "T",
                "T",
            ],
            "就業形態": [
                0,
                0,
                0,
                0,
            ],
            "現金給与総額": [
                "300000",
                "290000",
                "280000",
                "295000",
            ],
        }
    )

    result = create_wage_dataframe(raw_df)

    assert len(result) == 2

    assert result.loc[0, "date"] == pd.Timestamp("2025-01-01")

    assert result.loc[0, "nominal_wage_amount"] == 290000

    assert result.loc[1, "nominal_wage_amount"] == 300000


def test_create_wage_dataframe_raises_when_column_is_missing() -> None:
    raw_df = pd.DataFrame(
        {
            "年": [2025],
            "月": ["01"],
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        create_wage_dataframe(raw_df)
