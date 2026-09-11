import numpy as np
import pandas as pd
import pytest

from real_wage_dashboard.labor_force_analysis import (
    add_centered_composition_effect,
    create_age_hours_decomposition,
    create_age_hours_period_summary,
    create_employment_count_decomposition,
    create_employment_structure_summary,
    create_working_hours_distribution_change,
    create_working_hours_distribution_period_summary,
    summarize_age_hours_decomposition,
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
