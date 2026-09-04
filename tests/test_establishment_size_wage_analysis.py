import pandas as pd
import pytest

from real_wage_dashboard.establishment_size_wage_analysis import (
    build_establishment_size_comparison,
    prepare_establishment_size_annual_data,
    summarize_establishment_size_change,
    validate_establishment_size_results,
)


def make_sample_raw_data() -> pd.DataFrame:
    rows = []

    for year in [2020, 2021]:
        for size_code, wage_multiplier, hours_multiplier in [
            ("T", 1.0, 1.0),
            ("0", 1.1, 1.05),
        ]:
            for employment_code in ["0", "1", "2"]:
                wage = 100_000 * wage_multiplier
                hours = 100 * hours_multiplier

                if year == 2021:
                    wage *= 1.10
                    if size_code == "0":
                        wage *= 1.02

                rows.append(
                    {
                        "産業分類": "TL  ",
                        "規模": size_code,
                        "就業形態": employment_code,
                        "月": "CY",
                        "年": year,
                        "現金給与総額": wage,
                        "総実労働時間": hours,
                    }
                )

    return pd.DataFrame(rows)


def test_prepare_establishment_size_annual_data():
    raw = make_sample_raw_data()

    result = prepare_establishment_size_annual_data(
        raw,
        start_year=2020,
        end_year=2021,
    )

    assert len(result) == 12
    assert set(result["size_name"]) == {"5人以上", "30人以上"}
    assert set(result["employment_name"]) == {
        "就業形態計",
        "一般労働者",
        "パートタイム労働者",
    }
    assert result["hourly_wage"].notna().all()


def test_build_establishment_size_comparison_identity():
    raw = make_sample_raw_data()
    annual = prepare_establishment_size_annual_data(
        raw,
        start_year=2020,
        end_year=2021,
    )

    result = build_establishment_size_comparison(annual)

    error = (
        result["hourly_ratio_30_to_5"]
        * result["hours_ratio_30_to_5"]
        - result["wage_ratio_30_to_5"]
    ).abs().max()

    assert error == pytest.approx(0.0)


def test_summarize_establishment_size_change_decomposition():
    raw = make_sample_raw_data()
    annual = prepare_establishment_size_annual_data(
        raw,
        start_year=2020,
        end_year=2021,
    )
    comparison = build_establishment_size_comparison(annual)

    summary = summarize_establishment_size_change(
        comparison,
        employment_name="就業形態計",
        start_year=2020,
        end_year=2021,
    )

    assert summary["decomposition_error"] == pytest.approx(0.0)
    assert summary["wage_ratio_log_change"] == pytest.approx(
        summary["hourly_ratio_log_contribution"]
        + summary["hours_ratio_log_contribution"]
    )


def test_validate_establishment_size_results():
    raw = make_sample_raw_data()
    annual = prepare_establishment_size_annual_data(
        raw,
        start_year=2020,
        end_year=2021,
    )
    comparison = build_establishment_size_comparison(annual)

    validate_establishment_size_results(
        annual,
        comparison,
        start_year=2020,
        end_year=2021,
    )
