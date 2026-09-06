import numpy as np
import pandas as pd
import pytest

from real_wage_dashboard.wage_distribution_analysis import (
    add_real_wage_distribution,
    add_real_wage_distribution_by_group,
    build_gender_wage_ratio,
    build_wage_distribution_analysis,
    build_wage_distribution_analysis_by_sex,
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


def test_add_real_wage_distribution(
    wage_distribution_df: pd.DataFrame,
) -> None:
    cpi_df = pd.DataFrame(
        {
            "year": [2015, 2025],
            "cpi": [97.8, 114.025],
        }
    )

    result = add_real_wage_distribution(
        wage_distribution_df,
        cpi_df,
    )

    base = result[result["year"] == 2015].iloc[0]
    end = result[result["year"] == 2025].iloc[0]

    assert base["real_p10_index"] == pytest.approx(100.0)
    assert base["real_p50_index"] == pytest.approx(100.0)
    assert base["real_p90_index"] == pytest.approx(100.0)

    expected_real_p10_2025 = 199.9 / (114.025 / 100)

    assert end["real_p10"] == pytest.approx(expected_real_p10_2025)


def test_add_real_wage_distribution_rejects_missing_cpi(
    wage_distribution_df: pd.DataFrame,
) -> None:
    cpi_df = pd.DataFrame(
        {
            "year": [2015],
            "cpi": [97.8],
        }
    )

    with pytest.raises(
        ValueError,
        match="CPIが存在しない年",
    ):
        add_real_wage_distribution(
            wage_distribution_df,
            cpi_df,
        )


def test_add_real_wage_distribution_by_group() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2025, 2015, 2025],
            "sex": [
                "male",
                "male",
                "female",
                "female",
            ],
            "p10": [183.2, 214.9, 149.3, 185.5],
            "p25": [225.8, 258.2, 176.9, 215.6],
            "p50": [293.8, 325.8, 218.2, 260.3],
            "p75": [399.4, 433.1, 276.8, 320.8],
            "p90": [534.5, 582.6, 357.4, 405.3],
        }
    )

    cpi_df = pd.DataFrame(
        {
            "year": [2015, 2025],
            "cpi": [97.8, 114.025],
        }
    )

    result = add_real_wage_distribution_by_group(
        df,
        cpi_df,
        group_columns=["sex"],
    )

    base = result[result["year"] == 2015]

    assert np.allclose(
        base["real_p10_index"],
        100.0,
    )

    assert np.allclose(
        base["real_p50_index"],
        100.0,
    )

    assert np.allclose(
        base["real_p90_index"],
        100.0,
    )

    female_2025 = result[(result["year"] == 2025) & (result["sex"] == "female")].iloc[0]

    expected = (185.5 / (114.025 / 100)) / (149.3 / (97.8 / 100)) * 100

    assert female_2025["real_p10_index"] == pytest.approx(expected)


def test_build_wage_distribution_analysis_by_sex() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2025, 2015, 2025],
            "sex": ["male", "male", "female", "female"],
            "p10": [183.2, 214.9, 149.3, 185.5],
            "p25": [225.8, 258.2, 176.9, 215.6],
            "p50": [293.8, 325.8, 218.2, 260.3],
            "p75": [399.4, 433.1, 276.8, 320.8],
            "p90": [534.5, 582.6, 357.4, 405.3],
        }
    )

    result = build_wage_distribution_analysis_by_sex(df)

    base = result[result["year"] == 2015]

    assert np.allclose(base["p10_index"], 100.0)
    assert np.allclose(base["p50_index"], 100.0)
    assert np.allclose(base["p90_index"], 100.0)

    female_2025 = result[(result["year"] == 2025) & (result["sex"] == "female")].iloc[0]

    assert female_2025["p10_index"] == pytest.approx(185.5 / 149.3 * 100)


def test_build_gender_wage_ratio() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2025, 2015, 2025],
            "sex": ["male", "male", "female", "female"],
            "p10": [183.2, 214.9, 149.3, 185.5],
            "p25": [225.8, 258.2, 176.9, 215.6],
            "p50": [293.8, 325.8, 218.2, 260.3],
            "p75": [399.4, 433.1, 276.8, 320.8],
            "p90": [534.5, 582.6, 357.4, 405.3],
        }
    )

    result = build_gender_wage_ratio(df)

    row_2015 = result[result["year"] == 2015].iloc[0]
    row_2025 = result[result["year"] == 2025].iloc[0]

    assert row_2015["female_male_p50_ratio"] == pytest.approx(218.2 / 293.8)

    assert row_2025["female_male_p50_ratio"] == pytest.approx(260.3 / 325.8)


def test_add_real_wage_distribution_by_group_2025_values() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2025, 2015, 2025],
            "sex": ["male", "male", "female", "female"],
            "p10": [183.2, 214.9, 149.3, 185.5],
            "p25": [225.8, 258.2, 176.9, 215.6],
            "p50": [293.8, 325.8, 218.2, 260.3],
            "p75": [399.4, 433.1, 276.8, 320.8],
            "p90": [534.5, 582.6, 357.4, 405.3],
        }
    )

    cpi_df = pd.DataFrame(
        {
            "year": [2015, 2025],
            "cpi": [97.8, 114.025],
        }
    )

    result = add_real_wage_distribution_by_group(
        df,
        cpi_df,
        group_columns=["sex"],
    )

    female_2025 = result[(result["year"] == 2025) & (result["sex"] == "female")].iloc[0]

    male_2025 = result[(result["year"] == 2025) & (result["sex"] == "male")].iloc[0]

    assert female_2025["real_p50_index"] == pytest.approx(
        102.319450,
        abs=1e-6,
    )

    assert male_2025["real_p50_index"] == pytest.approx(
        95.112602,
        abs=1e-6,
    )
