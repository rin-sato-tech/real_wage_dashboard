import pandas as pd
import pytest

from real_wage_dashboard.take_home_scenario import (
    create_scaled_wage_input,
)


def test_create_scaled_wage_input_preserves_salary_total():
    reference = pd.DataFrame(
        {
            "year": [2025],
            "total_cash_earnings": [
                355_636.1666666667,
            ],
            "regular_earnings": [
                330_000.0,
            ],
            "special_earnings": [
                25_636.1666666667,
            ],
        }
    )

    result = create_scaled_wage_input(
        reference_wage_df=reference,
        year=2025,
        annual_salary_yen=5_000_000.0,
    )

    assert len(result) == 1

    row = result.iloc[0]

    assert row["total_cash_earnings"] * 12 == pytest.approx(5_000_000.0)

    assert row["regular_earnings"] + row["special_earnings"] == pytest.approx(
        row["total_cash_earnings"]
    )


def test_create_scaled_wage_input_preserves_regular_share():
    reference = pd.DataFrame(
        {
            "year": [2025],
            "total_cash_earnings": [
                400_000.0,
            ],
            "regular_earnings": [
                320_000.0,
            ],
            "special_earnings": [
                80_000.0,
            ],
        }
    )

    result = create_scaled_wage_input(
        reference_wage_df=reference,
        year=2025,
        annual_salary_yen=6_000_000.0,
    )

    row = result.iloc[0]

    original_share = 320_000.0 / 400_000.0

    result_share = row["regular_earnings"] / row["total_cash_earnings"]

    assert result_share == pytest.approx(original_share)


def test_create_scaled_wage_input_rejects_missing_year():
    reference = pd.DataFrame(
        {
            "year": [2024],
            "total_cash_earnings": [
                400_000.0,
            ],
            "regular_earnings": [
                320_000.0,
            ],
            "special_earnings": [
                80_000.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="2025年の賃金データ",
    ):
        create_scaled_wage_input(
            reference_wage_df=reference,
            year=2025,
            annual_salary_yen=5_000_000.0,
        )


def test_create_scaled_wage_input_rejects_nonpositive_salary():
    reference = pd.DataFrame(
        {
            "year": [2025],
            "total_cash_earnings": [
                400_000.0,
            ],
            "regular_earnings": [
                320_000.0,
            ],
            "special_earnings": [
                80_000.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="0より大きい",
    ):
        create_scaled_wage_input(
            reference_wage_df=reference,
            year=2025,
            annual_salary_yen=0,
        )
