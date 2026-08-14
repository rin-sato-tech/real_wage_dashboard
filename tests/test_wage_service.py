import pandas as pd
import pytest

from real_wage_dashboard.wage_service import create_wage_dataframe


def create_test_raw_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "年": [
                2025,
                2025,
                2025,
                2025,
                2025,
                2025,
                2025,
                2025,
            ],
            "月": [
                "01",
                "02",
                "01",
                "01",
                "01",
                "01",
                "01",
                "CY",
            ],
            "産業分類": [
                "TL",
                "TL",
                "TL",
                "TL",
                "TL",
                "TL",
                "C",
                "TL",
            ],
            "規模": [
                "T",
                "T",
                "0",
                "T",
                "0",
                "T",
                "T",
                "T",
            ],
            "就業形態": [
                0,
                0,
                0,
                1,
                1,
                2,
                0,
                0,
            ],
            "現金給与総額": [
                "290000",
                "300000",
                "310000",
                "320000",
                "330000",
                "180000",
                "280000",
                "295000",
            ],
            "きまって支給する給与": [
                "250000",
                "255000",
                "260000",
                "270000",
                "275000",
                "170000",
                "240000",
                "252000",
            ],
        }
    )


def test_create_wage_dataframe_uses_v1_defaults() -> None:
    raw_df = create_test_raw_df()

    result = create_wage_dataframe(raw_df)

    assert len(result) == 2

    assert result.loc[0, "date"] == pd.Timestamp("2025-01-01")
    assert result.loc[0, "nominal_wage_amount"] == 290000

    assert result.loc[1, "date"] == pd.Timestamp("2025-02-01")
    assert result.loc[1, "nominal_wage_amount"] == 300000


def test_create_wage_dataframe_selects_regular_wage_item() -> None:
    raw_df = create_test_raw_df()

    result = create_wage_dataframe(
        raw_df,
        wage_item="きまって支給する給与",
        establishment_size="T",
        employment_type="0",
    )

    assert len(result) == 2

    assert result.loc[0, "nominal_wage_amount"] == 250000
    assert result.loc[1, "nominal_wage_amount"] == 255000


def test_create_wage_dataframe_selects_establishment_size() -> None:
    raw_df = create_test_raw_df()

    result = create_wage_dataframe(
        raw_df,
        wage_item="現金給与総額",
        establishment_size="0",
        employment_type="0",
    )

    assert len(result) == 1

    assert result.loc[0, "date"] == pd.Timestamp("2025-01-01")
    assert result.loc[0, "nominal_wage_amount"] == 310000


def test_create_wage_dataframe_selects_employment_type() -> None:
    raw_df = create_test_raw_df()

    result = create_wage_dataframe(
        raw_df,
        wage_item="現金給与総額",
        establishment_size="T",
        employment_type="1",
    )

    assert len(result) == 1
    assert result.loc[0, "nominal_wage_amount"] == 320000


def test_create_wage_dataframe_selects_part_time_workers() -> None:
    raw_df = create_test_raw_df()

    result = create_wage_dataframe(
        raw_df,
        wage_item="現金給与総額",
        establishment_size="T",
        employment_type="2",
    )

    assert len(result) == 1
    assert result.loc[0, "nominal_wage_amount"] == 180000


def test_create_wage_dataframe_default_matches_explicit_v1_conditions() -> None:
    raw_df = create_test_raw_df()

    default_result = create_wage_dataframe(raw_df)

    explicit_result = create_wage_dataframe(
        raw_df,
        wage_item="現金給与総額",
        establishment_size="T",
        employment_type="0",
    )

    pd.testing.assert_frame_equal(
        default_result,
        explicit_result,
    )


def test_create_wage_dataframe_raises_when_condition_has_no_data() -> None:
    raw_df = create_test_raw_df()

    with pytest.raises(
        ValueError,
        match="選択した条件に該当する賃金データがありません",
    ):
        create_wage_dataframe(
            raw_df,
            wage_item="現金給与総額",
            establishment_size="XXX",
            employment_type="0",
        )


def test_create_wage_dataframe_raises_when_wage_item_is_missing() -> None:
    raw_df = create_test_raw_df()

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        create_wage_dataframe(
            raw_df,
            wage_item="存在しない給与",
        )


def test_create_wage_dataframe_raises_when_required_column_is_missing() -> None:
    raw_df = pd.DataFrame(
        {
            "年": [2025],
            "月": ["01"],
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        create_wage_dataframe(raw_df)
