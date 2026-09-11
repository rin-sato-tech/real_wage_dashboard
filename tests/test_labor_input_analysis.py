import numpy as np
import pandas as pd
import pytest

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.labor_input_analysis import (
    add_scheduled_hours_decomposition,
    add_wage_decomposition,
    add_working_hours_decomposition,
    create_labor_input_dataframe,
    create_rolling_labor_input_decomposition,
    create_working_hours_index_comparison,
    create_yearly_labor_input_summary,
    create_yearly_weighted_means,
    summarize_long_term_scheduled_hours_decomposition,
    summarize_long_term_wage_decomposition,
    summarize_long_term_working_hours_decomposition,
    weighted_mean,
)
from real_wage_dashboard.labor_input_index_service import (
    create_official_working_hours_index_dataframe,
)
from real_wage_dashboard.wage_service import load_wage_csv
from real_wage_dashboard.working_days_service import create_working_days_dataframe

TOTAL_HOURS_INDEX_PATH = "data/raw/labor_input/total_hours_index_5plus.xls"
SCHEDULED_HOURS_INDEX_PATH = "data/raw/labor_input/scheduled_hours_index_5plus.xls"
OVERTIME_HOURS_INDEX_PATH = "data/raw/labor_input/overtime_hours_index_5plus.xls"


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
        "previous_month_workers",
        "end_month_workers",
        "worker_weight",
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


def test_worker_weight_is_average_of_month_end_workers() -> None:
    df = load_analysis_df()

    expected = (df["previous_month_workers"] + df["end_month_workers"]) / 2

    assert np.allclose(
        df["worker_weight"],
        expected,
        atol=1e-10,
    )


def test_weighted_mean() -> None:
    df = pd.DataFrame(
        {
            "value": [10.0, 20.0],
            "worker_weight": [1.0, 3.0],
        }
    )

    result = weighted_mean(df, "value")

    assert np.isclose(result, 17.5)


def test_create_yearly_weighted_means_uses_worker_weights() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
            "value": [10.0] * 6 + [20.0] * 6,
            "worker_weight": [1.0] * 6 + [3.0] * 6,
        }
    )

    result = create_yearly_weighted_means(
        df,
        columns=["value"],
    )

    assert len(result) == 1
    assert np.isclose(result.loc[0, "value"], 17.5)


def test_yearly_labor_input_summary_uses_weighted_annual_values() -> None:
    df = load_analysis_df()

    yearly = create_yearly_labor_input_summary(df)

    row_2015 = yearly.loc[yearly["year"] == 2015].iloc[0]
    row_2025 = yearly.loc[yearly["year"] == 2025].iloc[0]

    assert np.isclose(
        row_2015["nominal_wage_amount"],
        260576.643006,
        atol=1e-3,
    )
    assert np.isclose(
        row_2025["nominal_wage_amount"],
        287426.954126,
        atol=1e-3,
    )

    assert np.isclose(
        row_2015["total_hours"],
        144.436968,
        atol=1e-5,
    )
    assert np.isclose(
        row_2025["total_hours"],
        135.067115,
        atol=1e-5,
    )


def test_yearly_labor_input_summary_identities() -> None:
    df = load_analysis_df()

    yearly = create_yearly_labor_input_summary(df)

    hours_error = (
        yearly["total_hours"] - yearly["scheduled_hours"] - yearly["overtime_hours"]
    )

    wage_error = (
        yearly["wage_log_change"]
        - yearly["hourly_wage_log_contribution"]
        - yearly["total_hours_log_contribution"]
    )

    scheduled_error = (
        yearly["scheduled_hours_log_change"]
        - yearly["working_days_log_contribution"]
        - yearly["hours_per_workday_log_contribution"]
    )

    assert hours_error.abs().max() < 1e-10
    assert wage_error.dropna().abs().max() < 1e-10
    assert scheduled_error.dropna().abs().max() < 1e-10


def test_rolling_labor_input_decomposition_identities() -> None:
    df = load_analysis_df()
    yearly = create_yearly_labor_input_summary(df)

    rolling = create_rolling_labor_input_decomposition(
        yearly,
        window_years=10,
    )

    assert rolling["start_year"].min() == 1990
    assert rolling["end_year"].max() == 2025
    assert len(rolling) == 26

    wage_error = (
        rolling["wage_log_change"]
        - rolling["hourly_wage_log_contribution"]
        - rolling["total_hours_log_contribution"]
    )

    hours_error = (
        rolling["total_hours_change_pct"]
        - rolling["scheduled_hours_contribution_pct"]
        - rolling["overtime_hours_contribution_pct"]
    )

    scheduled_error = (
        rolling["scheduled_hours_log_change"]
        - rolling["working_days_log_contribution"]
        - rolling["hours_per_workday_log_contribution"]
    )

    assert wage_error.abs().max() < 1e-10
    assert hours_error.abs().max() < 1e-10
    assert scheduled_error.abs().max() < 1e-10


def test_working_hours_index_comparison_base_year() -> None:
    yearly = create_yearly_labor_input_summary(load_analysis_df())

    official = create_official_working_hours_index_dataframe(
        TOTAL_HOURS_INDEX_PATH,
        SCHEDULED_HOURS_INDEX_PATH,
        OVERTIME_HOURS_INDEX_PATH,
    )

    comparison = create_working_hours_index_comparison(
        yearly,
        official,
        base_year=2020,
    )

    base = comparison.loc[comparison["year"] == 2020].iloc[0]

    assert np.isclose(
        base["calculated_total_hours_index"],
        100,
    )
    assert np.isclose(
        base["calculated_scheduled_hours_index"],
        100,
    )
    assert np.isclose(
        base["calculated_overtime_hours_index"],
        100,
    )

    assert comparison.loc[comparison["year"].between(1990, 2025)].shape[0] == 36
