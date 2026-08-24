import pandas as pd

from real_wage_dashboard.labor_market_service import (
    add_tankan_tightness_columns,
    create_effective_job_openings_dataframe,
    create_labor_market_dataframe,
    create_new_job_openings_dataframe,
    create_tankan_employment_di_dataframe,
    create_unemployment_rate_dataframe,
)


def test_create_effective_job_openings_dataframe():
    raw_df = pd.DataFrame(
        {
            0: ["2025年"],
            20: [1.20],
            21: [1.21],
            22: [1.22],
            23: [1.23],
            24: [1.24],
            25: [1.25],
            26: [1.26],
            27: [1.27],
            28: [1.28],
            29: [1.29],
            30: [1.30],
            31: [1.31],
        }
    )

    result = create_effective_job_openings_dataframe(raw_df)

    assert len(result) == 12
    assert result.iloc[0]["date"] == pd.Timestamp("2025-01-01")
    assert result.iloc[0]["effective_job_openings_ratio"] == 1.20
    assert result.iloc[-1]["date"] == pd.Timestamp("2025-12-01")
    assert result.iloc[-1]["effective_job_openings_ratio"] == 1.31


def test_create_new_job_openings_dataframe():
    raw_df = pd.DataFrame(
        {
            0: ["2025年"],
            20: [2.00],
            21: [2.01],
            22: [2.02],
            23: [2.03],
            24: [2.04],
            25: [2.05],
            26: [2.06],
            27: [2.07],
            28: [2.08],
            29: [2.09],
            30: [2.10],
            31: [2.11],
        }
    )

    result = create_new_job_openings_dataframe(raw_df)

    assert len(result) == 12
    assert result.iloc[0]["date"] == pd.Timestamp("2025-01-01")
    assert result.iloc[0]["new_job_openings_ratio"] == 2.00
    assert result.iloc[-1]["date"] == pd.Timestamp("2025-12-01")
    assert result.iloc[-1]["new_job_openings_ratio"] == 2.11


def test_create_unemployment_rate_dataframe():
    raw_df = pd.DataFrame(
        {
            0: ["令和7年", 2025, None],
            1: ["1月", "2月", "3月"],
            19: [2.5, 2.4, 2.6],
        }
    )

    result = create_unemployment_rate_dataframe(raw_df)

    assert len(result) == 3

    assert result.iloc[0]["date"] == pd.Timestamp("2025-01-01")
    assert result.iloc[0]["unemployment_rate"] == 2.5

    assert result.iloc[1]["date"] == pd.Timestamp("2025-02-01")
    assert result.iloc[1]["unemployment_rate"] == 2.4

    assert result.iloc[2]["date"] == pd.Timestamp("2025-03-01")
    assert result.iloc[2]["unemployment_rate"] == 2.6


def test_create_labor_market_dataframe():
    effective_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                ]
            ),
            "effective_job_openings_ratio": [1.2, 1.3],
        }
    )

    unemployment_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                ]
            ),
            "unemployment_rate": [2.5, 2.4],
        }
    )

    new_jobs_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-02-01",
                ]
            ),
            "new_job_openings_ratio": [2.1, 2.2],
        }
    )

    result = create_labor_market_dataframe(
        effective_df,
        unemployment_df,
        new_jobs_df,
    )

    assert len(result) == 2
    assert list(result.columns) == [
        "date",
        "effective_job_openings_ratio",
        "unemployment_rate",
        "new_job_openings_ratio",
    ]


def test_create_tankan_employment_di_dataframe():
    raw_df = pd.DataFrame(
        {
            "period": [
                "2025/03",
                "2025/06",
            ],
            "large_enterprise_employment_di": [-25, -28],
            "medium_enterprise_employment_di": [-35, -37],
            "small_enterprise_employment_di": [-38, -40],
        }
    )

    result = create_tankan_employment_di_dataframe(raw_df)

    assert len(result) == 2
    assert result.iloc[0]["date"] == pd.Timestamp("2025-03-01")
    assert result.iloc[1]["date"] == pd.Timestamp("2025-06-01")


def test_add_tankan_tightness_columns():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-03-01",
                ]
            ),
            "large_enterprise_employment_di": [-28],
            "medium_enterprise_employment_di": [-37],
            "small_enterprise_employment_di": [-40],
        }
    )

    result = add_tankan_tightness_columns(df)

    assert result.iloc[0]["large_enterprise_tightness"] == 28
    assert result.iloc[0]["medium_enterprise_tightness"] == 37
    assert result.iloc[0]["small_enterprise_tightness"] == 40
