import numpy as np
import pandas as pd
import pytest

from real_wage_dashboard.config import (
    LFS_WORKING_HOURS_AGE_CODES,
    LFS_WORKING_HOURS_CATEGORY_CODES,
)
from real_wage_dashboard.labor_force_service import (
    _add_harmonized_distribution_metrics,
    _add_harmonized_hours_bands,
    _add_reconstructed_hours_bands,
    _create_lfs_distribution_long_dataframe,
    _pivot_lfs_distribution,
    create_lfs_age_dataframe,
    create_lfs_working_hours_distribution_dataframe,
    create_lfs_working_hours_time_codes,
)


def test_add_reconstructed_hours_bands() -> None:
    df = pd.DataFrame(
        {
            "hours_1_14": [10.0],
            "hours_15_29": [20.0],
            "hours_30_34": [5.0],
            "hours_35_39": [30.0],
            "hours_40_48": [40.0],
            "hours_49_59": [15.0],
            "hours_60_plus": [5.0],
        }
    )

    result = _add_reconstructed_hours_bands(df)

    assert result.loc[0, "hours_1_34_reconstructed"] == pytest.approx(35.0)
    assert result.loc[0, "hours_35_48_reconstructed"] == pytest.approx(70.0)
    assert result.loc[0, "hours_49_plus_reconstructed"] == pytest.approx(20.0)


def test_add_harmonized_hours_bands_prefers_official_values() -> None:
    df = pd.DataFrame(
        {
            "hours_1_34": [100.0, np.nan],
            "hours_35_48": [200.0, np.nan],
            "hours_49_plus": [50.0, np.nan],
            "hours_1_34_reconstructed": [90.0, 110.0],
            "hours_35_48_reconstructed": [190.0, 210.0],
            "hours_49_plus_reconstructed": [40.0, 60.0],
        }
    )

    result = _add_harmonized_hours_bands(df)

    assert result.loc[0, "hours_1_34_harmonized"] == pytest.approx(100.0)
    assert result.loc[0, "hours_35_48_harmonized"] == pytest.approx(200.0)
    assert result.loc[0, "hours_49_plus_harmonized"] == pytest.approx(50.0)

    assert result.loc[1, "hours_1_34_harmonized"] == pytest.approx(110.0)
    assert result.loc[1, "hours_35_48_harmonized"] == pytest.approx(210.0)
    assert result.loc[1, "hours_49_plus_harmonized"] == pytest.approx(60.0)


def test_create_lfs_working_hours_time_codes() -> None:
    assert create_lfs_working_hours_time_codes(
        start_year=2023,
        end_year=2025,
    ) == [
        "2023000000",
        "2024000000",
        "2025000000",
    ]


def test_create_lfs_working_hours_time_codes_rejects_invalid_period() -> None:
    with pytest.raises(
        ValueError,
        match="開始年は終了年以下",
    ):
        create_lfs_working_hours_time_codes(
            start_year=2025,
            end_year=2024,
        )


def test_pivot_lfs_distribution_rejects_duplicates() -> None:
    df = pd.DataFrame(
        {
            "year": [2025, 2025],
            "age_group": ["25～34歳", "25～34歳"],
            "metric": ["persons_at_work", "persons_at_work"],
            "value": [100.0, 110.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="データが重複しています",
    ):
        _pivot_lfs_distribution(df)


def test_create_lfs_working_hours_distribution_dataframe() -> None:
    response = {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "DATA_INF": {
                    "VALUE": [
                        {
                            "@cat02": next(iter(LFS_WORKING_HOURS_AGE_CODES.values())),
                            "@cat04": LFS_WORKING_HOURS_CATEGORY_CODES[
                                "persons_at_work"
                            ],
                            "@time": "2025000000",
                            "$": "100",
                        },
                        {
                            "@cat02": next(iter(LFS_WORKING_HOURS_AGE_CODES.values())),
                            "@cat04": LFS_WORKING_HOURS_CATEGORY_CODES["hours_1_34"],
                            "@time": "2025000000",
                            "$": "30",
                        },
                        {
                            "@cat02": next(iter(LFS_WORKING_HOURS_AGE_CODES.values())),
                            "@cat04": LFS_WORKING_HOURS_CATEGORY_CODES["hours_35_48"],
                            "@time": "2025000000",
                            "$": "50",
                        },
                        {
                            "@cat02": next(iter(LFS_WORKING_HOURS_AGE_CODES.values())),
                            "@cat04": LFS_WORKING_HOURS_CATEGORY_CODES["hours_49_plus"],
                            "@time": "2025000000",
                            "$": "20",
                        },
                    ]
                }
            }
        }
    }

    result = create_lfs_working_hours_distribution_dataframe(response)

    assert len(result) == 1

    row = result.iloc[0]

    assert row["persons_at_work"] == pytest.approx(100.0)
    assert row["hours_1_34_harmonized"] == pytest.approx(30.0)
    assert row["hours_35_48_harmonized"] == pytest.approx(50.0)
    assert row["hours_49_plus_harmonized"] == pytest.approx(20.0)

    assert row["coverage"] == pytest.approx(1.0)
    assert row["unclassified_share"] == pytest.approx(0.0)

    assert row["hours_1_34_harmonized_share"] == pytest.approx(0.30)
    assert row["hours_35_48_harmonized_share"] == pytest.approx(0.50)
    assert row["hours_49_plus_harmonized_share"] == pytest.approx(0.20)


def test_add_harmonized_distribution_metrics_rejects_zero_persons() -> None:
    df = pd.DataFrame(
        {
            "persons_at_work": [0.0],
            "hours_1_34_harmonized": [0.0],
            "hours_35_48_harmonized": [0.0],
            "hours_49_plus_harmonized": [0.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="従業者総数は0より大きい",
    ):
        _add_harmonized_distribution_metrics(df)


def test_create_lfs_distribution_long_dataframe_rejects_invalid_response() -> None:
    response = {}

    with pytest.raises(
        ValueError,
        match="e-StatレスポンスからVALUEを取得できません",
    ):
        _create_lfs_distribution_long_dataframe(response)


def test_create_lfs_distribution_long_dataframe_rejects_invalid_time_code() -> None:
    age_code = next(iter(LFS_WORKING_HOURS_AGE_CODES.values()))

    response = {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "DATA_INF": {
                    "VALUE": [
                        {
                            "@cat02": age_code,
                            "@cat04": LFS_WORKING_HOURS_CATEGORY_CODES[
                                "persons_at_work"
                            ],
                            "@time": "invalid",
                            "$": "100",
                        }
                    ]
                }
            }
        }
    }

    with pytest.raises(
        ValueError,
        match="不正な時間コード",
    ):
        _create_lfs_distribution_long_dataframe(response)


def test_create_lfs_age_dataframe_preserves_missing_hours(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    employment = pd.DataFrame(
        {
            "year": [2011],
            "age_group": ["25～34歳"],
            "employed_persons": [100.0],
            "employment_rate": [80.0],
        }
    )

    hours = pd.DataFrame(
        columns=[
            "year",
            "age_group",
            "average_weekly_hours",
            "aggregate_weekly_hours",
            "implied_persons_at_work",
            "worker_share",
        ]
    )

    monkeypatch.setattr(
        "real_wage_dashboard.labor_force_service.load_lfs_employment_by_age",
        lambda _: employment,
    )

    monkeypatch.setattr(
        "real_wage_dashboard.labor_force_service.load_lfs_hours_by_age",
        lambda _: hours,
    )

    result = create_lfs_age_dataframe(
        "employment.xlsx",
        "hours.csv",
    )

    assert len(result) == 1
    assert pd.isna(result.loc[0, "average_weekly_hours"])
    assert pd.isna(result.loc[0, "aggregate_weekly_hours"])
