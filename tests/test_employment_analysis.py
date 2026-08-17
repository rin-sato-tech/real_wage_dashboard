import pandas as pd
import pytest

from real_wage_dashboard.employment_analysis import (
    add_approx_hourly_wage,
    create_employment_analysis_dataframe,
    merge_wage_and_working_hours,
)


def create_test_wage_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-02-01",
                    "2020-03-01",
                ]
            ),
            "nominal_wage_amount": [
                320_000.0,
                324_000.0,
                330_000.0,
            ],
        }
    )


def create_test_working_hours_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-02-01",
                    "2020-03-01",
                ]
            ),
            "working_hours": [
                160.0,
                162.0,
                165.0,
            ],
        }
    )


def test_merge_wage_and_working_hours() -> None:
    wage_df = create_test_wage_df()
    working_hours_df = create_test_working_hours_df()

    result = merge_wage_and_working_hours(
        wage_df,
        working_hours_df,
    )

    assert len(result) == 3

    assert result.columns.tolist() == [
        "date",
        "nominal_wage_amount",
        "working_hours",
    ]

    assert result["nominal_wage_amount"].tolist() == [
        320_000.0,
        324_000.0,
        330_000.0,
    ]

    assert result["working_hours"].tolist() == [
        160.0,
        162.0,
        165.0,
    ]


def test_merge_wage_and_working_hours_uses_matching_dates_only() -> None:
    wage_df = create_test_wage_df()

    working_hours_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2020-02-01",
                    "2020-03-01",
                    "2020-04-01",
                ]
            ),
            "working_hours": [
                162.0,
                165.0,
                164.0,
            ],
        }
    )

    result = merge_wage_and_working_hours(
        wage_df,
        working_hours_df,
    )

    assert result["date"].tolist() == [
        pd.Timestamp("2020-02-01"),
        pd.Timestamp("2020-03-01"),
    ]


def test_merge_wage_and_working_hours_returns_sorted_dates() -> None:
    wage_df = create_test_wage_df().iloc[::-1].reset_index(drop=True)
    working_hours_df = create_test_working_hours_df().iloc[::-1].reset_index(drop=True)

    result = merge_wage_and_working_hours(
        wage_df,
        working_hours_df,
    )

    assert result["date"].is_monotonic_increasing


def test_merge_wage_and_working_hours_raises_for_duplicate_wage_dates() -> None:
    wage_df = pd.concat(
        [
            create_test_wage_df(),
            create_test_wage_df().iloc[[0]],
        ],
        ignore_index=True,
    )

    working_hours_df = create_test_working_hours_df()

    with pytest.raises(pd.errors.MergeError):
        merge_wage_and_working_hours(
            wage_df,
            working_hours_df,
        )


def test_merge_wage_and_working_hours_raises_for_duplicate_working_hours_dates() -> (
    None
):
    wage_df = create_test_wage_df()

    working_hours_df = pd.concat(
        [
            create_test_working_hours_df(),
            create_test_working_hours_df().iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(pd.errors.MergeError):
        merge_wage_and_working_hours(
            wage_df,
            working_hours_df,
        )


def test_merge_wage_and_working_hours_raises_when_wage_column_missing() -> None:
    wage_df = create_test_wage_df().drop(columns=["nominal_wage_amount"])

    working_hours_df = create_test_working_hours_df()

    with pytest.raises(
        ValueError,
        match="賃金データに必要な列がありません",
    ):
        merge_wage_and_working_hours(
            wage_df,
            working_hours_df,
        )


def test_merge_wage_and_working_hours_raises_when_working_hours_column_missing() -> (
    None
):
    wage_df = create_test_wage_df()

    working_hours_df = create_test_working_hours_df().drop(columns=["working_hours"])

    with pytest.raises(
        ValueError,
        match="労働時間データに必要な列がありません",
    ):
        merge_wage_and_working_hours(
            wage_df,
            working_hours_df,
        )


def test_add_approx_hourly_wage() -> None:
    df = pd.DataFrame(
        {
            "nominal_wage_amount": [
                320_000.0,
                324_000.0,
            ],
            "working_hours": [
                160.0,
                162.0,
            ],
        }
    )

    result = add_approx_hourly_wage(df)

    assert result["approx_hourly_wage"].tolist() == pytest.approx(
        [
            2000.0,
            2000.0,
        ]
    )


def test_add_approx_hourly_wage_raises_when_working_hours_zero() -> None:
    df = pd.DataFrame(
        {
            "nominal_wage_amount": [
                320_000.0,
            ],
            "working_hours": [
                0.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="労働時間は0より大きい必要があります",
    ):
        add_approx_hourly_wage(df)


def test_add_approx_hourly_wage_raises_when_working_hours_negative() -> None:
    df = pd.DataFrame(
        {
            "nominal_wage_amount": [
                320_000.0,
            ],
            "working_hours": [
                -10.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="労働時間は0より大きい必要があります",
    ):
        add_approx_hourly_wage(df)


def test_add_approx_hourly_wage_raises_when_required_column_missing() -> None:
    df = pd.DataFrame(
        {
            "nominal_wage_amount": [
                320_000.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        add_approx_hourly_wage(df)


def test_create_employment_analysis_dataframe() -> None:
    wage_df = create_test_wage_df()
    working_hours_df = create_test_working_hours_df()

    result = create_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
    )

    assert result.columns.tolist() == [
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
    ]

    assert result["approx_hourly_wage"].tolist() == pytest.approx(
        [
            2000.0,
            2000.0,
            2000.0,
        ]
    )
