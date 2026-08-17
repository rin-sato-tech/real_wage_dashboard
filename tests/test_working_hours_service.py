import pandas as pd
import pytest

from real_wage_dashboard.working_hours_service import (
    create_working_hours_dataframe,
)


def create_test_raw_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "年": [
                2020,
                2020,
                2020,
                2020,
                2020,
                2020,
            ],
            "月": [
                1,
                2,
                1,
                2,
                1,
                2,
            ],
            "産業分類": [
                "TL",
                "TL",
                "TL",
                "TL",
                "TL",
                "TL",
            ],
            "規模": [
                "T",
                "T",
                "T",
                "T",
                "0",
                "0",
            ],
            "就業形態": [
                "1",
                "1",
                "2",
                "2",
                "1",
                "1",
            ],
            "総実労働時間": [
                160.0,
                158.0,
                85.0,
                84.0,
                162.0,
                161.0,
            ],
            "所定内労働時間": [
                150.0,
                149.0,
                82.0,
                81.0,
                151.0,
                150.0,
            ],
            "所定外労働時間": [
                10.0,
                9.0,
                3.0,
                3.0,
                11.0,
                11.0,
            ],
        }
    )


def test_create_working_hours_dataframe_default() -> None:
    raw_df = create_test_raw_df()

    result = create_working_hours_dataframe(raw_df)

    assert len(result) == 2
    assert result["working_hours"].tolist() == [160.0, 158.0]


def test_create_working_hours_dataframe_selects_part_time() -> None:
    raw_df = create_test_raw_df()

    result = create_working_hours_dataframe(
        raw_df,
        employment_type="2",
    )

    assert result["working_hours"].tolist() == [85.0, 84.0]


def test_create_working_hours_dataframe_selects_establishment_size() -> None:
    raw_df = create_test_raw_df()

    result = create_working_hours_dataframe(
        raw_df,
        establishment_size="0",
        employment_type="1",
    )

    assert result["working_hours"].tolist() == [162.0, 161.0]


def test_create_working_hours_dataframe_selects_scheduled_hours() -> None:
    raw_df = create_test_raw_df()

    result = create_working_hours_dataframe(
        raw_df,
        working_hours_item="所定内労働時間",
    )

    assert result["working_hours"].tolist() == [150.0, 149.0]


def test_create_working_hours_dataframe_selects_overtime_hours() -> None:
    raw_df = create_test_raw_df()

    result = create_working_hours_dataframe(
        raw_df,
        working_hours_item="所定外労働時間",
    )

    assert result["working_hours"].tolist() == [10.0, 9.0]


def test_create_working_hours_dataframe_returns_sorted_dates() -> None:
    raw_df = create_test_raw_df().iloc[::-1].reset_index(drop=True)

    result = create_working_hours_dataframe(raw_df)

    assert result["date"].is_monotonic_increasing


def test_create_working_hours_dataframe_raises_when_no_data() -> None:
    raw_df = create_test_raw_df()

    with pytest.raises(
        ValueError,
        match="該当する労働時間データがありません",
    ):
        create_working_hours_dataframe(
            raw_df,
            employment_type="9",
        )


def test_create_working_hours_dataframe_raises_when_item_missing() -> None:
    raw_df = create_test_raw_df()

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        create_working_hours_dataframe(
            raw_df,
            working_hours_item="存在しない労働時間",
        )


def test_create_working_hours_dataframe_raises_when_required_column_missing() -> None:
    raw_df = create_test_raw_df().drop(columns=["産業分類"])

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        create_working_hours_dataframe(raw_df)
