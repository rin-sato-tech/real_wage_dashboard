import numpy as np
import pandas as pd
import pytest

from real_wage_dashboard.labor_force_analysis import (
    add_centered_composition_effect,
    create_age_hours_decomposition,
    create_age_hours_period_summary,
    create_employment_count_decomposition,
    create_employment_structure_summary,
    create_total_labor_input_decomposition,
    create_total_labor_input_period_summary,
    create_total_labor_input_trend,
    create_working_hours_distribution_change,
    create_working_hours_distribution_period_summary,
    summarize_age_hours_decomposition,
    summarize_total_labor_input_decomposition,
)
from real_wage_dashboard.labor_force_service import (
    create_lfs_age_dataframe,
)

EMPLOYMENT_PATH = "data/raw/labor_input/lfs_employment_by_age_annual.xlsx"

HOURS_PATH = "data/raw/labor_input/lfs_hours_by_age_annual.csv"


def load_lfs_age_df():
    return create_lfs_age_dataframe(
        EMPLOYMENT_PATH,
        HOURS_PATH,
    )


def test_age_hours_decomposition_identity() -> None:
    df = load_lfs_age_df()

    decomposition = create_age_hours_decomposition(
        df,
        start_year=2000,
        end_year=2025,
    )

    summary = summarize_age_hours_decomposition(decomposition)

    assert np.isclose(
        summary["total_change_hours"],
        (summary["within_effect_hours"] + summary["composition_effect_hours"]),
        atol=1e-10,
    )

    assert abs(summary["decomposition_error"]) < 1e-10


def test_age_hours_decomposition_2000_2025() -> None:
    df = load_lfs_age_df()

    decomposition = create_age_hours_decomposition(
        df,
        start_year=2000,
        end_year=2025,
    )

    summary = summarize_age_hours_decomposition(decomposition)

    assert np.isclose(
        summary["start_average_weekly_hours"],
        42.7341,
        atol=1e-3,
    )

    assert np.isclose(
        summary["end_average_weekly_hours"],
        35.8730,
        atol=1e-3,
    )

    assert np.isclose(
        summary["within_effect_hours"],
        -6.2737,
        atol=1e-3,
    )

    assert np.isclose(
        summary["composition_effect_hours"],
        -0.5875,
        atol=1e-3,
    )


def test_centered_composition_effect_identity() -> None:
    df = load_lfs_age_df()

    decomposition = create_age_hours_decomposition(
        df,
        start_year=2000,
        end_year=2025,
    )

    centered = add_centered_composition_effect(decomposition)

    assert np.isclose(
        centered["centered_composition_effect"].sum(),
        decomposition["composition_effect"].sum(),
        atol=1e-10,
    )


def test_age_hours_period_summary() -> None:
    df = load_lfs_age_df()

    periods = [
        (2000, 2010),
        (2012, 2019),
        (2012, 2025),
        (2015, 2025),
        (2020, 2025),
    ]

    result = create_age_hours_period_summary(
        df,
        periods,
    )

    assert len(result) == 5

    error = (
        result["total_change_hours"]
        - result["within_effect_hours"]
        - result["composition_effect_hours"]
    )

    assert error.abs().max() < 1e-10


def test_employment_count_decomposition_identity() -> None:
    df = load_lfs_age_df()

    structure = create_employment_structure_summary(
        df,
        start_year=2015,
        end_year=2025,
    )

    result = create_employment_count_decomposition(structure)

    assert result["decomposition_error"].abs().max() < 1e-10


def test_create_working_hours_distribution_change() -> None:
    df = pd.DataFrame(
        {
            "year": [
                2015,
                2025,
            ],
            "age_group": [
                "15歳以上",
                "15歳以上",
            ],
            "persons_at_work": [
                1000.0,
                1100.0,
            ],
            "hours_1_34_harmonized": [
                300.0,
                396.0,
            ],
            "hours_35_48_harmonized": [
                500.0,
                539.0,
            ],
            "hours_49_plus_harmonized": [
                190.0,
                154.0,
            ],
            "hours_1_34_harmonized_share": [
                0.30,
                0.36,
            ],
            "hours_35_48_harmonized_share": [
                0.50,
                0.49,
            ],
            "hours_49_plus_harmonized_share": [
                0.19,
                0.14,
            ],
            "unclassified_share": [
                0.01,
                0.01,
            ],
        }
    )

    result = create_working_hours_distribution_change(
        df,
        start_year=2015,
        end_year=2025,
    )

    row = result.iloc[0]

    assert row["hours_1_34_share_change_pt"] == pytest.approx(6.0)
    assert row["hours_35_48_share_change_pt"] == pytest.approx(-1.0)
    assert row["hours_49_plus_share_change_pt"] == pytest.approx(-5.0)

    assert row["persons_at_work_change"] == pytest.approx(100.0)
    assert row["hours_1_34_workers_change"] == pytest.approx(96.0)
    assert row["hours_35_48_workers_change"] == pytest.approx(39.0)
    assert row["hours_49_plus_workers_change"] == pytest.approx(-36.0)


def test_create_working_hours_distribution_period_summary() -> None:
    df = pd.DataFrame(
        {
            "year": [
                2000,
                2010,
                2020,
            ],
            "age_group": [
                "15歳以上",
                "15歳以上",
                "15歳以上",
            ],
            "persons_at_work": [
                1000.0,
                1050.0,
                1100.0,
            ],
            "hours_1_34_harmonized": [
                200.0,
                262.5,
                330.0,
            ],
            "hours_35_48_harmonized": [
                500.0,
                504.0,
                528.0,
            ],
            "hours_49_plus_harmonized": [
                290.0,
                273.0,
                231.0,
            ],
            "hours_1_34_harmonized_share": [
                0.20,
                0.25,
                0.30,
            ],
            "hours_35_48_harmonized_share": [
                0.50,
                0.48,
                0.48,
            ],
            "hours_49_plus_harmonized_share": [
                0.29,
                0.26,
                0.21,
            ],
            "unclassified_share": [
                0.01,
                0.01,
                0.01,
            ],
        }
    )

    result = create_working_hours_distribution_period_summary(
        df,
        periods=[
            (2000, 2010),
            (2010, 2020),
        ],
    )

    assert len(result) == 2

    first = result.iloc[0]
    assert first["hours_1_34_change_pt"] == pytest.approx(5.0)
    assert first["hours_35_48_change_pt"] == pytest.approx(-2.0)
    assert first["hours_49_plus_change_pt"] == pytest.approx(-3.0)

    second = result.iloc[1]
    assert second["hours_1_34_change_pt"] == pytest.approx(5.0)
    assert second["hours_35_48_change_pt"] == pytest.approx(0.0)
    assert second["hours_49_plus_change_pt"] == pytest.approx(-5.0)


def test_create_total_labor_input_decomposition() -> None:
    df = pd.DataFrame(
        {
            "year": [
                2015,
                2015,
                2025,
                2025,
            ],
            "age_group": [
                "25～34歳",
                "35～44歳",
                "25～34歳",
                "35～44歳",
            ],
            "average_weekly_hours": [
                40.0,
                42.0,
                38.0,
                39.0,
            ],
            "implied_persons_at_work": [
                100.0,
                200.0,
                110.0,
                180.0,
            ],
            "aggregate_weekly_hours": [
                4000.0,
                8400.0,
                4180.0,
                7020.0,
            ],
        }
    )

    result = create_total_labor_input_decomposition(
        df,
        start_year=2015,
        end_year=2025,
    )

    assert len(result) == 2

    row = result.loc[result["age_group"] == "25～34歳"].iloc[0]

    assert row["aggregate_weekly_hours_change"] == pytest.approx(180.0)

    assert row["persons_effect"] == pytest.approx(390.0)

    assert row["hours_effect"] == pytest.approx(-210.0)

    assert row["decomposition_error"] == pytest.approx(0.0)


def test_summarize_total_labor_input_decomposition() -> None:
    df = pd.DataFrame(
        {
            "year": [
                2015,
                2015,
                2025,
                2025,
            ],
            "age_group": [
                "25～34歳",
                "35～44歳",
                "25～34歳",
                "35～44歳",
            ],
            "average_weekly_hours": [
                40.0,
                42.0,
                38.0,
                39.0,
            ],
            "implied_persons_at_work": [
                100.0,
                200.0,
                110.0,
                180.0,
            ],
            "aggregate_weekly_hours": [
                4000.0,
                8400.0,
                4180.0,
                7020.0,
            ],
        }
    )

    decomposition = create_total_labor_input_decomposition(
        df,
        start_year=2015,
        end_year=2025,
    )

    summary = summarize_total_labor_input_decomposition(decomposition)

    assert summary["start_total_weekly_hours"] == pytest.approx(12400.0)

    assert summary["end_total_weekly_hours"] == pytest.approx(11200.0)

    assert summary["total_change_weekly_hours"] == pytest.approx(-1200.0)

    assert summary["persons_effect_weekly_hours"] == pytest.approx(-399.7701149425287)

    assert summary["within_age_hours_effect_weekly_hours"] == pytest.approx(
        -779.8850574712644
    )

    assert summary["age_composition_effect_weekly_hours"] == pytest.approx(
        -20.344827586206897
    )

    assert summary["average_hours_effect_weekly_hours"] == pytest.approx(
        -800.2298850574713
    )

    assert (
        summary["persons_effect_weekly_hours"]
        + summary["within_age_hours_effect_weekly_hours"]
        + summary["age_composition_effect_weekly_hours"]
    ) == pytest.approx(-1200.0)

    assert summary["decomposition_error"] == pytest.approx(0.0)


def test_create_total_labor_input_period_summary() -> None:
    df = load_lfs_age_df()

    result = create_total_labor_input_period_summary(
        df,
        periods=[
            (2015, 2025),
            (2000, 2025),
        ],
    )

    assert len(result) == 2

    recent = result.loc[
        (result["start_year"] == 2015)
        & (result["end_year"] == 2025)
    ].iloc[0]

    assert recent[
        "total_change_weekly_hours"
    ] == pytest.approx(-4985.0)

    assert recent[
        "persons_effect_weekly_hours"
    ] == pytest.approx(
        15255.471935,
        abs=1e-6,
    )

    assert recent[
        "within_age_hours_effect_weekly_hours"
    ] == pytest.approx(
        -18064.934705,
        abs=1e-6,
    )

    assert recent[
        "age_composition_effect_weekly_hours"
    ] == pytest.approx(
        -2175.537231,
        abs=1e-6,
    )

    assert (
        recent["persons_effect_weekly_hours"]
        + recent["within_age_hours_effect_weekly_hours"]
        + recent["age_composition_effect_weekly_hours"]
    ) == pytest.approx(
        recent["total_change_weekly_hours"],
        abs=1e-6,
    )


def test_create_total_labor_input_trend() -> None:
    df = load_lfs_age_df()

    result = create_total_labor_input_trend(df)

    row_2000 = result.loc[
        result["year"] == 2000
    ].iloc[0]

    assert row_2000[
        "total_weekly_hours"
    ] == pytest.approx(270293.0)

    assert row_2000[
        "average_weekly_hours"
    ] == pytest.approx(
        42.734140,
        abs=1e-6,
    )

    row_2011 = result.loc[
        result["year"] == 2011
    ].iloc[0]

    assert pd.isna(
        row_2011["total_weekly_hours"]
    )
    assert pd.isna(
        row_2011["total_persons_at_work"]
    )
    assert pd.isna(
        row_2011["average_weekly_hours"]
    )

    row_2025 = result.loc[
        result["year"] == 2025
    ].iloc[0]

    assert row_2025[
        "total_weekly_hours"
    ] == pytest.approx(236287.0)

    assert row_2025[
        "average_weekly_hours"
    ] == pytest.approx(
        35.873024,
        abs=1e-6,
    )
