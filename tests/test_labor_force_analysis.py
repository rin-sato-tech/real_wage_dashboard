import numpy as np

from real_wage_dashboard.labor_force_analysis import (
    add_centered_composition_effect,
    create_age_hours_decomposition,
    create_age_hours_period_summary,
    create_employment_count_decomposition,
    create_employment_structure_summary,
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
