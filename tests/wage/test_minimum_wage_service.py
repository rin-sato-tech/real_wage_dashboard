import pandas as pd
import pytest

from real_wage_dashboard.minimum_wage_service import (
    load_minimum_wage_data,
)


def test_load_minimum_wage_data_shape() -> None:
    df = load_minimum_wage_data()

    assert len(df) == 11
    assert df["year"].nunique() == 11
    assert df["year"].min() == 2015
    assert df["year"].max() == 2025


def test_load_minimum_wage_data_columns() -> None:
    df = load_minimum_wage_data()

    assert list(df.columns) == [
        "year",
        "minimum_wage",
        "minimum_wage_yoy",
    ]


def test_load_minimum_wage_data_has_no_duplicates() -> None:
    df = load_minimum_wage_data()

    assert not df["year"].duplicated().any()


def test_load_minimum_wage_data_has_no_missing_wages() -> None:
    df = load_minimum_wage_data()

    assert not df["minimum_wage"].isna().any()


def test_load_minimum_wage_data_is_monotonic() -> None:
    df = load_minimum_wage_data()

    assert df["minimum_wage"].is_monotonic_increasing


def test_load_minimum_wage_data_known_values() -> None:
    df = load_minimum_wage_data().set_index("year")

    assert df.loc[2015, "minimum_wage"] == 798
    assert df.loc[2019, "minimum_wage"] == 901
    assert df.loc[2020, "minimum_wage"] == 902
    assert df.loc[2025, "minimum_wage"] == 1121


def test_load_minimum_wage_data_yoy() -> None:
    df = load_minimum_wage_data().set_index("year")

    assert pd.isna(df.loc[2015, "minimum_wage_yoy"])

    assert df.loc[2020, "minimum_wage_yoy"] == pytest.approx(902 / 901 - 1)
    assert df.loc[2025, "minimum_wage_yoy"] == pytest.approx(1121 / 1055 - 1)
