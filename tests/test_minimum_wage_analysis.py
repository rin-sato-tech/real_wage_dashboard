import pytest

from real_wage_dashboard.minimum_wage_analysis import (
    build_minimum_wage_analysis,
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
