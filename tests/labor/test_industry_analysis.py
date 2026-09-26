import pandas as pd
import pytest

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.industry_analysis import (
    MAIN_INDUSTRIES,
    add_industry_wage_decomposition,
    create_industry_analysis_discussion,
    create_industry_analysis_results,
    create_industry_comparison_dataframe,
    create_industry_monthly_dataframe,
    create_industry_yearly_dataframe,
    identify_notable_industries,
    summarize_industry_changes,
)
from real_wage_dashboard.wage_service import load_wage_csv


def load_raw_wage_df() -> pd.DataFrame:
    """毎月勤労統計の元データを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)


def test_create_industry_monthly_dataframe_has_expected_columns() -> None:
    result = create_industry_monthly_dataframe(
        load_raw_wage_df(),
        industry_code="E",
    )

    assert list(result.columns) == [
        "date",
        "industry",
        "monthly_wage",
        "approx_hourly_wage",
        "total_hours",
        "scheduled_hours",
        "overtime_hours",
    ]

    assert not result.empty
    assert result["industry"].eq("E").all()


def test_total_hours_equals_scheduled_plus_overtime() -> None:
    result = create_industry_monthly_dataframe(
        load_raw_wage_df(),
        industry_code="E",
    )

    error = (
        result["total_hours"] - result["scheduled_hours"] - result["overtime_hours"]
    ).abs()

    assert error.max() < 1e-10


def test_create_industry_yearly_dataframe_keeps_complete_years() -> None:
    monthly = create_industry_monthly_dataframe(
        load_raw_wage_df(),
        industry_code="E",
    )

    yearly = create_industry_yearly_dataframe(monthly)

    assert yearly["month_count"].eq(12).all()
    assert 2025 in yearly["year"].to_list()

    # 2026年は現データでは1～5月のみ
    assert 2026 not in yearly["year"].to_list()


def test_yearly_wage_identity() -> None:
    monthly = create_industry_monthly_dataframe(
        load_raw_wage_df(),
        industry_code="E",
    )

    yearly = create_industry_yearly_dataframe(monthly)

    reconstructed = yearly["approx_hourly_wage"] * yearly["total_hours"]

    error = (yearly["monthly_wage"] - reconstructed).abs()

    assert error.max() < 1e-8


def test_main_industries_have_2015_2025_comparison() -> None:
    result = create_industry_comparison_dataframe(
        load_raw_wage_df(),
        industry_codes=MAIN_INDUSTRIES,
        start_year=2015,
        end_year=2025,
    )

    assert set(result["industry"]) == set(MAIN_INDUSTRIES)
    assert len(result) == len(MAIN_INDUSTRIES)


def test_industry_wage_decomposition_identity() -> None:
    comparison = create_industry_comparison_dataframe(
        load_raw_wage_df(),
        industry_codes=MAIN_INDUSTRIES,
        start_year=2015,
        end_year=2025,
    )

    result = add_industry_wage_decomposition(comparison)

    assert result["decomposition_error"].abs().max() < 1e-10


def test_industry_summary() -> None:
    comparison = create_industry_comparison_dataframe(
        load_raw_wage_df(),
        industry_codes=MAIN_INDUSTRIES,
    )

    decomposition = add_industry_wage_decomposition(comparison)

    summary = summarize_industry_changes(decomposition)

    assert summary["industry_count"] == 16
    assert summary["wage_rise_count"] == 16
    assert summary["wage_rise_share"] == pytest.approx(100.0)
    assert summary["above_total_count"] == 9


def test_identify_notable_industries() -> None:
    comparison = create_industry_comparison_dataframe(
        load_raw_wage_df(),
        industry_codes=MAIN_INDUSTRIES,
    )

    decomposition = add_industry_wage_decomposition(comparison)

    result = identify_notable_industries(decomposition)

    assert result == {
        "monthly_wage_growth_max": "C",
        "monthly_wage_growth_min": "O",
        "hourly_wage_growth_max": "C",
        "hours_decline_max": "M",
        "monthly_hourly_gap_max": "M",
    }


def test_industry_analysis_texts() -> None:
    comparison = create_industry_comparison_dataframe(
        load_raw_wage_df(),
        industry_codes=MAIN_INDUSTRIES,
    )

    decomposition = add_industry_wage_decomposition(comparison)

    summary = summarize_industry_changes(decomposition)

    notable = identify_notable_industries(decomposition)

    results = create_industry_analysis_results(
        summary,
        notable,
    )

    discussion = create_industry_analysis_discussion(
        notable,
    )

    assert len(results) > 0
    assert len(discussion) > 0

    assert any("16産業すべて" in text for text in results)

    assert any("2020年" in text for text in discussion)
