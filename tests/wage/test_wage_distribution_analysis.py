import numpy as np
import pandas as pd
import pytest

from real_wage_dashboard.wage_distribution_analysis import (
    add_real_wage_distribution,
    add_real_wage_distribution_by_group,
    build_gender_wage_ratio,
    build_wage_distribution_analysis,
    build_wage_distribution_analysis_by_company_size,
    build_wage_distribution_analysis_by_employment,
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


def test_build_wage_distribution_analysis_by_employment() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2025, 2015, 2025],
            "employment": [
                "regular",
                "regular",
                "nonregular",
                "nonregular",
            ],
            "p10": [181.7, 216.1, 136.0, 169.0],
            "p25": [219.5, 254.6, 155.3, 188.9],
            "p50": [280.1, 313.3, 183.6, 218.7],
            "p75": [377.9, 409.1, 227.1, 261.8],
            "p90": [508.1, 550.3, 290.6, 326.5],
            "decile_dispersion": [0.58, 0.53, 0.42, 0.36],
            "quartile_dispersion": [0.28, 0.25, 0.20, 0.17],
        }
    )

    result = build_wage_distribution_analysis_by_employment(
        df,
        base_year=2015,
    )

    base = result[result["year"] == 2015]

    assert np.allclose(base["p10_index"], 100.0)
    assert np.allclose(base["p50_index"], 100.0)
    assert np.allclose(base["p90_index"], 100.0)

    regular_2025 = result[
        (result["year"] == 2025) & (result["employment"] == "regular")
    ].iloc[0]

    assert regular_2025["p10_index"] == pytest.approx(216.1 / 181.7 * 100)

    assert regular_2025["p90_p10"] == pytest.approx(550.3 / 216.1)


def test_add_real_wage_distribution_by_employment() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2025, 2015, 2025],
            "employment": [
                "regular",
                "regular",
                "nonregular",
                "nonregular",
            ],
            "p10": [181.7, 216.1, 136.0, 169.0],
            "p25": [219.5, 254.6, 155.3, 188.9],
            "p50": [280.1, 313.3, 183.6, 218.7],
            "p75": [377.9, 409.1, 227.1, 261.8],
            "p90": [508.1, 550.3, 290.6, 326.5],
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
        group_columns=["employment"],
        base_year=2015,
    )

    regular_2025 = result[
        (result["year"] == 2025) & (result["employment"] == "regular")
    ].iloc[0]

    nonregular_2025 = result[
        (result["year"] == 2025) & (result["employment"] == "nonregular")
    ].iloc[0]

    assert regular_2025["real_p50_index"] == pytest.approx(
        95.936984,
        abs=1e-6,
    )

    assert nonregular_2025["real_p50_index"] == pytest.approx(
        102.167997,
        abs=1e-6,
    )


def test_build_wage_distribution_analysis_by_company_size() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2025, 2015, 2025, 2015, 2025],
            "company_size": [
                "large",
                "large",
                "medium",
                "medium",
                "small",
                "small",
            ],
            "p10": [180.5, 211.1, 164.6, 198.3, 157.4, 192.2],
            "p25": [226.5, 255.5, 200.5, 234.7, 189.9, 226.7],
            "p50": [305.3, 328.6, 254.8, 288.4, 240.1, 278.5],
            "p75": [431.3, 450.1, 337.9, 372.3, 310.7, 350.5],
            "p90": [587.8, 632.0, 452.6, 494.8, 398.4, 444.7],
            "decile_dispersion": [0.67, 0.64, 0.57, 0.51, 0.50, 0.45],
            "quartile_dispersion": [0.34, 0.30, 0.27, 0.24, 0.25, 0.22],
        }
    )

    result = build_wage_distribution_analysis_by_company_size(
        df,
        base_year=2015,
    )

    base = result[result["year"] == 2015]

    assert np.allclose(base["p10_index"], 100.0)
    assert np.allclose(base["p50_index"], 100.0)
    assert np.allclose(base["p90_index"], 100.0)

    small_2025 = result[
        (result["year"] == 2025) & (result["company_size"] == "small")
    ].iloc[0]

    assert small_2025["p10_index"] == pytest.approx(192.2 / 157.4 * 100)

    assert small_2025["p90_p10"] == pytest.approx(444.7 / 192.2)


def test_add_real_wage_distribution_by_company_size() -> None:
    df = pd.DataFrame(
        {
            "year": [2015, 2025, 2015, 2025, 2015, 2025],
            "company_size": [
                "large",
                "large",
                "medium",
                "medium",
                "small",
                "small",
            ],
            "p10": [180.5, 211.1, 164.6, 198.3, 157.4, 192.2],
            "p25": [226.5, 255.5, 200.5, 234.7, 189.9, 226.7],
            "p50": [305.3, 328.6, 254.8, 288.4, 240.1, 278.5],
            "p75": [431.3, 450.1, 337.9, 372.3, 310.7, 350.5],
            "p90": [587.8, 632.0, 452.6, 494.8, 398.4, 444.7],
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
        group_columns=["company_size"],
        base_year=2015,
    )

    large_2025 = result[
        (result["year"] == 2025) & (result["company_size"] == "large")
    ].iloc[0]

    small_2025 = result[
        (result["year"] == 2025) & (result["company_size"] == "small")
    ].iloc[0]

    assert large_2025["real_p50_index"] == pytest.approx(
        92.316542,
        abs=1e-6,
    )

    assert small_2025["real_p50_index"] == pytest.approx(
        99.488255,
        abs=1e-6,
    )
