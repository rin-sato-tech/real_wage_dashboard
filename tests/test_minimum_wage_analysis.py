import pandas as pd
import pytest

from real_wage_dashboard.minimum_wage_analysis import (
    add_real_minimum_wage,
    build_minimum_wage_analysis,
    prepare_annual_cpi,
    prepare_minimum_wage_wage_data,
)
from real_wage_dashboard.minimum_wage_service import (
    load_minimum_wage_data,
)
from real_wage_dashboard.wage_service import load_wage_csv

WAGE_DATA_PATH = "data/raw/hon-maikin-k-jissu.csv"


def _load_analysis_df():
    minimum_wage_df = load_minimum_wage_data()

    raw_wage_df = load_wage_csv(
        file_path=WAGE_DATA_PATH,
    )

    wage_df = prepare_minimum_wage_wage_data(
        raw_wage_df,
        start_year=2015,
        end_year=2025,
    )

    return build_minimum_wage_analysis(
        minimum_wage_df,
        wage_df,
    )


def test_minimum_wage_analysis_shape() -> None:
    df = _load_analysis_df()

    assert len(df) == 66
    assert df["year"].nunique() == 11
    assert df["size_name"].nunique() == 2
    assert df["employment_name"].nunique() == 3


def test_minimum_wage_analysis_has_no_duplicates() -> None:
    df = _load_analysis_df()

    assert not df.duplicated(
        subset=[
            "year",
            "size_name",
            "employment_name",
        ]
    ).any()


def test_minimum_wage_analysis_has_no_missing_main_values() -> None:
    df = _load_analysis_df()

    columns = [
        "minimum_wage",
        "scheduled_hourly_wage",
        "simple_kaitz",
        "wage_to_minimum_ratio",
        "minimum_wage_index",
        "wage_index",
    ]

    assert not df[columns].isna().any().any()


def test_minimum_wage_analysis_base_year_indexes() -> None:
    df = _load_analysis_df()

    base = df[df["year"] == 2015]

    assert base["minimum_wage_index"].tolist() == pytest.approx([100.0] * len(base))
    assert base["wage_index"].tolist() == pytest.approx([100.0] * len(base))


def test_minimum_wage_analysis_ratio_identity() -> None:
    df = _load_analysis_df()

    identity = df["simple_kaitz"] * df["wage_to_minimum_ratio"]

    assert identity.tolist() == pytest.approx([1.0] * len(identity))


def test_minimum_wage_analysis_2025_5plus_part() -> None:
    df = _load_analysis_df()

    row = df[
        (df["year"] == 2025)
        & (df["size_name"] == "5人以上")
        & (df["employment_name"] == "パートタイム労働者")
    ].iloc[0]

    assert row["minimum_wage"] == 1121
    assert row["scheduled_hourly_wage"] == pytest.approx(
        1394.153646,
        rel=1e-6,
    )
    assert row["simple_kaitz"] == pytest.approx(
        0.804072,
        rel=1e-6,
    )
    assert row["minimum_wage_index"] == pytest.approx(
        140.476190,
        rel=1e-6,
    )
    assert row["wage_index"] == pytest.approx(
        130.373982,
        rel=1e-6,
    )


def test_minimum_wage_analysis_2025_general_worker() -> None:
    df = _load_analysis_df()

    row = df[
        (df["year"] == 2025)
        & (df["size_name"] == "5人以上")
        & (df["employment_name"] == "一般労働者")
    ].iloc[0]

    assert row["simple_kaitz"] == pytest.approx(
        0.484753,
        rel=1e-6,
    )
    assert row["wage_index"] == pytest.approx(
        116.544830,
        rel=1e-6,
    )


def test_part_time_wage_growth_exceeds_general_worker() -> None:
    df = _load_analysis_df()

    rows_2025 = df[(df["year"] == 2025) & (df["size_name"] == "5人以上")].set_index(
        "employment_name"
    )

    assert (
        rows_2025.loc[
            "パートタイム労働者",
            "wage_index",
        ]
        > rows_2025.loc[
            "一般労働者",
            "wage_index",
        ]
    )


def test_minimum_wage_index_exceeds_all_wage_indexes_in_2025() -> None:
    df = _load_analysis_df()

    rows_2025 = df[df["year"] == 2025]

    assert (rows_2025["minimum_wage_index"] > rows_2025["wage_index"]).all()


def test_prepare_annual_cpi() -> None:
    dates = pd.date_range(
        "2015-01-01",
        "2016-12-01",
        freq="MS",
    )

    cpi_df = pd.DataFrame(
        {
            "date": dates,
            "index_value": ([100.0] * 12 + [102.0] * 12),
        }
    )

    result = prepare_annual_cpi(
        cpi_df,
        start_year=2015,
        end_year=2016,
    )

    assert result["year"].tolist() == [
        2015,
        2016,
    ]

    assert result["cpi"].tolist() == pytest.approx(
        [
            100.0,
            102.0,
        ]
    )


def test_prepare_annual_cpi_rejects_incomplete_year() -> None:
    cpi_df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2015-01-01",
                periods=11,
                freq="MS",
            ),
            "index_value": [100.0] * 11,
        }
    )

    with pytest.raises(
        ValueError,
        match="12か月揃っていない",
    ):
        prepare_annual_cpi(
            cpi_df,
            start_year=2015,
            end_year=2015,
        )


def test_add_real_minimum_wage() -> None:
    analysis_df = pd.DataFrame(
        {
            "year": [
                2015,
                2016,
            ],
            "minimum_wage": [
                800,
                840,
            ],
            "minimum_wage_index": [
                100.0,
                105.0,
            ],
        }
    )

    annual_cpi_df = pd.DataFrame(
        {
            "year": [
                2015,
                2016,
            ],
            "cpi": [
                100.0,
                102.0,
            ],
        }
    )

    result = add_real_minimum_wage(
        analysis_df,
        annual_cpi_df,
        base_year=2015,
    )

    assert result["real_minimum_wage"].tolist() == pytest.approx(
        [
            800.0,
            840 / 1.02,
        ]
    )

    assert result["real_minimum_wage_index"].tolist() == pytest.approx(
        [
            100.0,
            (840 / 1.02) / 800 * 100,
        ]
    )


def test_real_minimum_wage_index_2025() -> None:
    analysis_df = _load_analysis_df()

    annual_cpi_df = pd.DataFrame(
        {
            "year": list(range(2015, 2026)),
            "cpi": [
                97.800000,
                97.708333,
                98.308333,
                99.483333,
                100.041667,
                100.000000,
                99.691667,
                102.650000,
                106.583333,
                109.975000,
                114.025000,
            ],
        }
    )

    result = add_real_minimum_wage(
        analysis_df,
        annual_cpi_df,
    )

    rows_2025 = result[result["year"] == 2025]

    assert rows_2025["real_minimum_wage_index"].tolist() == pytest.approx(
        [120.487362] * len(rows_2025),
        rel=1e-6,
    )
