import pandas as pd
import pytest

from real_wage_dashboard.corporate_performance_analysis import (
    calculate_corporate_wage_industry_correlations,
    calculate_corporate_wage_lag_correlations,
    create_corporate_comparison_dataframe,
    create_period_comparison_summary,
    create_wage_fiscal_year_dataframe,
    merge_corporate_and_wage_industry_comparison,
    merge_corporate_and_wage_time_series,
)


def create_corporate_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fiscal_year": [2020, 2021, 2022],
            "sales": [100.0, 110.0, 120.0],
            "operating_profit": [10.0, 12.0, 15.0],
            "ordinary_profit": [11.0, 13.0, 16.0],
            "value_added": [50.0, 55.0, 60.0],
            "labor_productivity": [100.0, 110.0, 121.0],
            "personnel_expenses": [30.0, 32.0, 34.0],
            "personnel_expenses_per_employee": [
                60.0,
                63.0,
                66.0,
            ],
            "labor_share": [60.0, 58.0, 56.0],
            "operating_profit_margin": [10.0, 10.9, 12.5],
            "ordinary_profit_margin": [11.0, 11.8, 13.3],
            "value_added_ratio": [50.0, 50.0, 50.0],
        }
    )


def test_create_corporate_comparison_dataframe() -> None:
    df = create_corporate_df()

    result = create_corporate_comparison_dataframe(
        df,
        start_year=2020,
        end_year=2022,
    )

    productivity = result.loc[result["metric"] == "labor_productivity"].iloc[0]

    assert productivity["start_value"] == 100.0
    assert productivity["end_value"] == 121.0
    assert productivity["change_rate_pct"] == pytest.approx(21.0)


def test_create_period_comparison_summary() -> None:
    df = create_corporate_df()

    result = create_period_comparison_summary(
        df,
        start_year=2020,
        end_year=2022,
    )

    assert result["labor_productivity_growth_pct"] == pytest.approx(21.0)

    assert result["personnel_expenses_per_employee_growth_pct"] == pytest.approx(10.0)

    assert result["growth_gap_pct_point"] == pytest.approx(11.0)

    assert result["labor_share_change_pct_point"] == pytest.approx(-4.0)


def test_create_wage_fiscal_year_dataframe() -> None:
    dates = pd.date_range(
        "2020-04-01",
        "2022-03-01",
        freq="MS",
    )

    monthly_df = pd.DataFrame(
        {
            "date": dates,
            "monthly_wage": [300000.0] * 12 + [306000.0] * 12,
            "approx_hourly_wage": [2000.0] * 24,
            "total_hours": [150.0] * 24,
        }
    )

    result = create_wage_fiscal_year_dataframe(monthly_df)

    assert result["fiscal_year"].tolist() == [
        2020,
        2021,
    ]

    assert result["month_count"].tolist() == [
        12,
        12,
    ]

    assert result.loc[
        1,
        "monthly_wage_yoy_pct",
    ] == pytest.approx(2.0)

    assert result.loc[
        0,
        "approx_hourly_wage",
    ] == pytest.approx(2000.0)


def test_create_wage_fiscal_year_dataframe_drops_incomplete_year() -> None:
    monthly_df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2020-04-01",
                periods=11,
                freq="MS",
            ),
            "monthly_wage": [300000.0] * 11,
            "approx_hourly_wage": [2000.0] * 11,
            "total_hours": [150.0] * 11,
        }
    )

    result = create_wage_fiscal_year_dataframe(monthly_df)

    assert result.empty


def test_merge_corporate_and_wage_industry_comparison() -> None:
    corporate_df = pd.DataFrame(
        {
            "industry": ["D", "E"],
            "labor_productivity_growth_pct": [10.0, 20.0],
            "personnel_expenses_per_employee_growth_pct": [
                5.0,
                10.0,
            ],
            "growth_gap_pct_point": [5.0, 10.0],
            "labor_share_change_pct_point": [-1.0, -2.0],
            "operating_profit_margin_change_pct_point": [
                0.5,
                1.0,
            ],
            "ordinary_profit_margin_change_pct_point": [
                0.7,
                1.2,
            ],
        }
    )

    wage_df = pd.DataFrame(
        {
            "industry": ["D", "E"],
            "monthly_wage_change_pct": [7.0, 9.0],
            "hourly_wage_change_pct": [10.0, 12.0],
            "total_hours_change_pct": [-3.0, -2.0],
        }
    )

    result = merge_corporate_and_wage_industry_comparison(
        corporate_df,
        wage_df,
    )

    assert result["industry"].tolist() == ["D", "E"]
    assert result["monthly_wage_change_pct"].tolist() == [
        7.0,
        9.0,
    ]


def test_calculate_corporate_wage_industry_correlations() -> None:
    df = pd.DataFrame(
        {
            "labor_productivity_growth_pct": [
                1.0,
                2.0,
                3.0,
            ],
            "personnel_expenses_per_employee_growth_pct": [
                1.0,
                2.0,
                3.0,
            ],
            "labor_share_change_pct_point": [
                3.0,
                2.0,
                1.0,
            ],
            "ordinary_profit_margin_change_pct_point": [
                1.0,
                2.0,
                3.0,
            ],
            "monthly_wage_change_pct": [
                1.0,
                2.0,
                3.0,
            ],
            "hourly_wage_change_pct": [
                3.0,
                2.0,
                1.0,
            ],
        }
    )

    result = calculate_corporate_wage_industry_correlations(df)

    assert result["productivity_vs_monthly_wage"] == pytest.approx(1.0)

    assert result["productivity_vs_hourly_wage"] == pytest.approx(-1.0)


def test_merge_corporate_and_wage_time_series() -> None:
    corporate_df = pd.DataFrame(
        {
            "fiscal_year": [2020, 2021, 2022],
            "labor_productivity": [100.0, 110.0, 121.0],
            "personnel_expenses_per_employee": [
                60.0,
                63.0,
                66.0,
            ],
            "ordinary_profit_margin": [5.0, 6.0, 7.0],
        }
    )

    wage_df = pd.DataFrame(
        {
            "fiscal_year": [2020, 2021, 2022],
            "monthly_wage": [
                300000.0,
                303000.0,
                309060.0,
            ],
            "approx_hourly_wage": [
                2000.0,
                2020.0,
                2060.4,
            ],
            "monthly_wage_yoy_pct": [
                float("nan"),
                1.0,
                2.0,
            ],
            "hourly_wage_yoy_pct": [
                float("nan"),
                1.0,
                2.0,
            ],
        }
    )

    result = merge_corporate_and_wage_time_series(
        corporate_df,
        wage_df,
    )

    assert result.loc[
        1,
        "labor_productivity_yoy_pct",
    ] == pytest.approx(10.0)

    assert result.loc[
        2,
        "ordinary_profit_margin_change_pct_point",
    ] == pytest.approx(1.0)


def test_calculate_corporate_wage_lag_correlations() -> None:
    df = pd.DataFrame(
        {
            "fiscal_year": [
                2020,
                2021,
                2022,
                2023,
            ],
            "labor_productivity_yoy_pct": [
                1.0,
                2.0,
                3.0,
                4.0,
            ],
            "personnel_expenses_per_employee_yoy_pct": [
                1.0,
                2.0,
                3.0,
                4.0,
            ],
            "ordinary_profit_margin_change_pct_point": [
                1.0,
                2.0,
                3.0,
                4.0,
            ],
            "monthly_wage_yoy_pct": [
                1.0,
                2.0,
                3.0,
                4.0,
            ],
            "hourly_wage_yoy_pct": [
                1.0,
                2.0,
                3.0,
                4.0,
            ],
        }
    )

    result = calculate_corporate_wage_lag_correlations(
        df,
        max_lag=2,
    )

    lag_zero = result.loc[
        (result["corporate_metric"] == "labor_productivity_yoy_pct")
        & (result["wage_metric"] == "monthly_wage_yoy_pct")
        & (result["lag_years"] == 0)
    ].iloc[0]

    assert lag_zero["correlation"] == pytest.approx(1.0)

    assert lag_zero["observation_count"] == 4
