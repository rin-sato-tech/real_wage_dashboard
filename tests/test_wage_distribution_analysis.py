import pandas as pd
import pytest

from real_wage_dashboard.wage_distribution_analysis import (
    build_wage_distribution_analysis,
    summarize_wage_distribution_change,
    validate_wage_distribution_data,
)


@pytest.fixture
def wage_distribution_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2015, 2025],
            "p10": [166.0, 199.9],
            "p25": [204.1, 238.2],
            "p50": [263.4, 296.6],
            "p75": [359.3, 389.8],
            "p90": [487.9, 527.3],
            "decile_dispersion": [0.61, 0.55],
            "quartile_dispersion": [0.29, 0.26],
        }
    )


def test_build_wage_distribution_analysis(
    wage_distribution_df: pd.DataFrame,
) -> None:
    result = build_wage_distribution_analysis(wage_distribution_df)

    base = result[result["year"] == 2015].iloc[0]
    end = result[result["year"] == 2025].iloc[0]

    for column in [
        "p10_index",
        "p25_index",
        "p50_index",
        "p75_index",
        "p90_index",
    ]:
        assert base[column] == pytest.approx(100.0)

    assert end["p90_p10"] == pytest.approx(527.3 / 199.9)
    assert end["p90_p50"] == pytest.approx(527.3 / 296.6)
    assert end["p50_p10"] == pytest.approx(296.6 / 199.9)


def test_summarize_wage_distribution_change(
    wage_distribution_df: pd.DataFrame,
) -> None:
    result = summarize_wage_distribution_change(wage_distribution_df)

    assert result["quantile"].tolist() == [
        "P10",
        "P25",
        "P50",
        "P75",
        "P90",
    ]

    p10 = result[result["quantile"] == "P10"].iloc[0]
    p90 = result[result["quantile"] == "P90"].iloc[0]

    assert p10["change_rate"] == pytest.approx(199.9 / 166.0 - 1)
    assert p90["change_rate"] == pytest.approx(527.3 / 487.9 - 1)


def test_validation_rejects_invalid_quantile_order() -> None:
    df = pd.DataFrame(
        {
            "year": [2015],
            "p10": [200.0],
            "p25": [190.0],
            "p50": [250.0],
            "p75": [300.0],
            "p90": [400.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="P10 <= P25 <= P50 <= P75 <= P90",
    ):
        validate_wage_distribution_data(df)


def test_validation_rejects_duplicate_year() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2015],
            "p10": [166.0, 166.0],
            "p25": [204.1, 204.1],
            "p50": [263.4, 263.4],
            "p75": [359.3, 359.3],
            "p90": [487.9, 487.9],
        }
    )

    with pytest.raises(
        ValueError,
        match="year が重複",
    ):
        validate_wage_distribution_data(df)
