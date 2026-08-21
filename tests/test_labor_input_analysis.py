import numpy as np
import pandas as pd
import pytest

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.labor_input_analysis import (
    add_scheduled_hours_decomposition,
    add_wage_decomposition,
    add_working_hours_decomposition,
    create_labor_input_dataframe,
    summarize_long_term_scheduled_hours_decomposition,
    summarize_long_term_wage_decomposition,
    summarize_long_term_working_hours_decomposition,
)
from real_wage_dashboard.wage_service import load_wage_csv
from real_wage_dashboard.working_days_service import create_working_days_dataframe


def load_analysis_df() -> pd.DataFrame:
    raw_df = load_wage_csv(WAGE_DATA_PATH)

    return create_labor_input_dataframe(
        raw_df,
        establishment_size="T",
        employment_type="0",
    )


def test_create_labor_input_dataframe() -> None:
    df = load_analysis_df()

    assert len(df) == 437
    assert df["date"].min() == pd.Timestamp("1990-01-01")
    assert df["date"].max() == pd.Timestamp("2026-05-01")

    required_columns = {
        "date",
        "nominal_wage_amount",
        "total_hours",
        "scheduled_hours",
        "overtime_hours",
        "working_days",
        "approx_hourly_wage",
        "scheduled_hours_per_workday",
    }

    assert required_columns.issubset(df.columns)
    assert df[list(required_columns)].isna().sum().sum() == 0


def test_wage_decomposition_identity() -> None:
    df = add_wage_decomposition(load_analysis_df())

    error = (
        df["wage_log_change"]
        - df["hourly_wage_log_contribution"]
        - df["total_hours_log_contribution"]
    )

    assert error.dropna().abs().max() < 1e-10


def test_working_hours_decomposition_identity() -> None:
    df = add_working_hours_decomposition(load_analysis_df())

    diff_error = (
        df["total_hours_yoy_diff"]
        - df["scheduled_hours_yoy_diff"]
        - df["overtime_hours_yoy_diff"]
    )

    contribution_error = (
        df["total_hours_decomposition_yoy_pct"]
        - df["scheduled_hours_contribution_pct"]
        - df["overtime_hours_contribution_pct"]
    )

    assert diff_error.dropna().abs().max() < 1e-10
    assert contribution_error.dropna().abs().max() < 1e-10


def test_scheduled_hours_decomposition_identity() -> None:
    df = add_scheduled_hours_decomposition(load_analysis_df())

    error = (
        df["scheduled_hours_log_change"]
        - df["working_days_log_contribution"]
        - df["hours_per_workday_log_contribution"]
    )

    assert error.dropna().abs().max() < 1e-10


def test_long_term_summaries() -> None:
    df = load_analysis_df()

    wage = summarize_long_term_wage_decomposition(df)
    hours = summarize_long_term_working_hours_decomposition(df)
    scheduled = summarize_long_term_scheduled_hours_decomposition(df)

    assert np.isclose(
        wage["wage_log_change"],
        (wage["hourly_wage_log_contribution"] + wage["total_hours_log_contribution"]),
        atol=1e-10,
    )

    assert np.isclose(
        hours["total_hours_change_pct"],
        (
            hours["scheduled_hours_contribution_pct"]
            + hours["overtime_hours_contribution_pct"]
        ),
        atol=1e-10,
    )

    assert np.isclose(
        scheduled["scheduled_hours_log_change"],
        (
            scheduled["working_days_log_contribution"]
            + scheduled["hours_per_workday_log_contribution"]
        ),
        atol=1e-10,
    )


def test_long_term_summary_requires_full_year() -> None:
    df = load_analysis_df()

    incomplete_df = df.loc[df["date"] != pd.Timestamp("2015-01-01")].copy()

    with pytest.raises(ValueError):
        summarize_long_term_wage_decomposition(
            incomplete_df,
            start_year=2015,
            end_year=2025,
        )

    with pytest.raises(ValueError):
        summarize_long_term_working_hours_decomposition(
            incomplete_df,
            start_year=2015,
            end_year=2025,
        )

    with pytest.raises(ValueError):
        summarize_long_term_scheduled_hours_decomposition(
            incomplete_df,
            start_year=2015,
            end_year=2025,
        )


def test_create_working_days_dataframe_requires_columns() -> None:
    raw_df = pd.DataFrame(
        {
            "年": [2025],
            "月": [1],
            "産業分類": ["TL"],
            "規模": ["T"],
            "就業形態": ["0"],
            # 出勤日数がない
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        create_working_days_dataframe(raw_df)


def test_create_working_days_dataframe_raises_for_no_matching_data() -> None:
    raw_df = load_wage_csv(WAGE_DATA_PATH)

    with pytest.raises(
        ValueError,
        match="該当する出勤日数データがありません",
    ):
        create_working_days_dataframe(
            raw_df,
            establishment_size="INVALID",
            employment_type="0",
        )
