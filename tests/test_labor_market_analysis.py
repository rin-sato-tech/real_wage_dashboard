import pandas as pd

from real_wage_dashboard.labor_market_analysis import (
    add_labor_market_regime,
    add_labor_market_tightness_columns,
    calculate_correlations,
    calculate_lag_correlations,
    calculate_regime_lag_correlations,
)


def test_calculate_lag_correlations_is_independent_of_input_order():
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2020-01-01",
                periods=6,
                freq="MS",
            ),
            "labor": [1, 2, 3, 4, 5, 6],
            "wage": [2, 4, 6, 8, 10, 12],
        }
    )

    normal = calculate_lag_correlations(
        df,
        labor_market_column="labor",
        wage_column="wage",
        max_lag=2,
    )

    reversed_result = calculate_lag_correlations(
        df.sort_values("date", ascending=False),
        labor_market_column="labor",
        wage_column="wage",
        max_lag=2,
    )

    pd.testing.assert_frame_equal(
        normal,
        reversed_result,
    )


def test_regime_lag_uses_data_before_analysis_start():
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "1999-01-01",
                "2000-12-01",
                freq="MS",
            ),
            "labor": list(range(24)),
            "wage": list(range(24)),
        }
    )

    df = add_labor_market_regime(df)

    result = calculate_regime_lag_correlations(
        df,
        labor_market_columns={
            "test": "labor",
        },
        wage_column="wage",
        max_lag=12,
        analysis_start="2000-01-01",
        analysis_end="2000-12-01",
    )

    target = result[
        (result["regime"] == "2000年代～震災後") & (result["lag_months"] == 12)
    ].iloc[0]

    assert target["observation_count"] == 12


def test_add_labor_market_tightness_columns():
    df = pd.DataFrame(
        {
            "effective_job_openings_ratio": [1.2],
            "unemployment_rate": [2.5],
            "new_job_openings_ratio": [2.0],
        }
    )

    result = add_labor_market_tightness_columns(df)

    assert (
        result.loc[
            0,
            "labor_market_tightness_effective_jobs",
        ]
        == 1.2
    )

    assert (
        result.loc[
            0,
            "labor_market_tightness_unemployment",
        ]
        == -2.5
    )

    assert (
        result.loc[
            0,
            "labor_market_tightness_new_jobs",
        ]
        == 2.0
    )


def test_calculate_correlations():
    df = pd.DataFrame(
        {
            "indicator_a": [1.0, 2.0, 3.0],
            "indicator_b": [3.0, 2.0, 1.0],
            "scheduled_cash_earnings_yoy": [
                1.0,
                2.0,
                3.0,
            ],
        }
    )

    result = calculate_correlations(
        df,
        {
            "A": "indicator_a",
            "B": "indicator_b",
        },
    )

    result = result.set_index("indicator")

    assert result.loc["A", "correlation"] == 1.0
    assert result.loc["B", "correlation"] == -1.0
    assert result.loc["A", "observation_count"] == 3
