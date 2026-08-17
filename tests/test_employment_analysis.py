import pandas as pd
import pytest

from real_wage_dashboard.employment_analysis import (
    add_approx_hourly_wage,
    add_base_year_index,
    add_employment_changes,
    add_employment_comparison_indices,
    add_real_employment_analysis,
    add_real_employment_changes,
    add_real_employment_indices,
    add_real_employment_values,
    add_wage_change_decomposition,
    create_employment_analysis_dataframe,
    merge_employment_analysis_with_cpi,
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


def create_base_year_test_df() -> pd.DataFrame:
    dates = pd.date_range(
        "2020-01-01",
        periods=13,
        freq="MS",
    )

    return pd.DataFrame(
        {
            "date": dates,
            "nominal_wage_amount": [
                100.0,
                100.0,
                100.0,
                100.0,
                100.0,
                100.0,
                100.0,
                100.0,
                100.0,
                100.0,
                100.0,
                100.0,
                110.0,
            ],
            "working_hours": [
                160.0,
            ]
            * 12
            + [168.0],
            "approx_hourly_wage": [
                10.0,
            ]
            * 12
            + [11.0],
        }
    )


def test_add_base_year_index() -> None:
    df = create_base_year_test_df()

    result = add_base_year_index(
        df,
        column="nominal_wage_amount",
        output_column="test_index",
    )

    base_df = result[result["date"].dt.year == 2020]

    assert base_df["test_index"].mean() == pytest.approx(100.0)

    assert result.iloc[-1]["test_index"] == pytest.approx(110.0)


def test_add_employment_comparison_indices() -> None:
    df = create_base_year_test_df()

    result = add_employment_comparison_indices(df)

    assert {
        "regular_wage_index",
        "working_hours_index",
        "approx_hourly_wage_index",
    }.issubset(result.columns)

    base_df = result[result["date"].dt.year == 2020]

    assert base_df["regular_wage_index"].mean() == pytest.approx(100.0)
    assert base_df["working_hours_index"].mean() == pytest.approx(100.0)
    assert base_df["approx_hourly_wage_index"].mean() == pytest.approx(100.0)


def test_add_base_year_index_raises_when_base_year_incomplete() -> None:
    df = create_base_year_test_df().iloc[:11].copy()

    with pytest.raises(
        ValueError,
        match="2020年の基準データが12か月揃っていません",
    ):
        add_base_year_index(
            df,
            column="nominal_wage_amount",
            output_column="test_index",
        )


def test_add_base_year_index_raises_when_base_year_missing() -> None:
    df = create_base_year_test_df().copy()

    df["date"] = df["date"] + pd.DateOffset(years=1)

    with pytest.raises(
        ValueError,
        match="2020年の基準データが12か月揃っていません",
    ):
        add_base_year_index(
            df,
            column="nominal_wage_amount",
            output_column="test_index",
        )


def test_add_base_year_index_raises_when_column_missing() -> None:
    df = create_base_year_test_df()

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        add_base_year_index(
            df,
            column="missing_column",
            output_column="test_index",
        )


def create_changes_test_df() -> pd.DataFrame:
    dates = pd.date_range(
        "2020-01-01",
        periods=13,
        freq="MS",
    )

    return pd.DataFrame(
        {
            "date": dates,
            "nominal_wage_amount": [
                100.0,
            ]
            * 12
            + [110.0],
            "working_hours": [
                100.0,
            ]
            * 12
            + [95.0],
            "approx_hourly_wage": [
                100.0,
            ]
            * 12
            + [120.0],
        }
    )


def test_add_employment_changes() -> None:
    df = create_changes_test_df()

    result = add_employment_changes(df)

    latest = result.iloc[-1]

    assert latest["regular_wage_yoy_pct"] == pytest.approx(10.0)
    assert latest["working_hours_yoy_pct"] == pytest.approx(-5.0)
    assert latest["approx_hourly_wage_yoy_pct"] == pytest.approx(20.0)


def test_add_employment_changes_first_12_months_are_nan() -> None:
    df = create_changes_test_df()

    result = add_employment_changes(df)

    assert result.iloc[:12]["regular_wage_yoy_pct"].isna().all()
    assert result.iloc[:12]["working_hours_yoy_pct"].isna().all()
    assert result.iloc[:12]["approx_hourly_wage_yoy_pct"].isna().all()


def test_add_employment_changes_sorts_dates() -> None:
    df = create_changes_test_df().iloc[::-1].reset_index(drop=True)

    result = add_employment_changes(df)

    assert result["date"].is_monotonic_increasing

    latest = result.iloc[-1]

    assert latest["regular_wage_yoy_pct"] == pytest.approx(10.0)


def test_add_employment_changes_raises_when_required_column_missing() -> None:
    df = create_changes_test_df().drop(columns=["working_hours"])

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        add_employment_changes(df)


def create_test_cpi_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-02-01",
                    "2020-03-01",
                ]
            ),
            "index_value": [
                100.0,
                102.0,
                105.0,
            ],
        }
    )


def test_merge_employment_analysis_with_cpi() -> None:
    df = create_employment_analysis_dataframe(
        create_test_wage_df(),
        create_test_working_hours_df(),
    )

    cpi_df = create_test_cpi_df()

    result = merge_employment_analysis_with_cpi(
        df,
        cpi_df,
    )

    assert len(result) == 3

    assert "index_value" in result.columns


def test_merge_employment_analysis_with_cpi_raises_for_duplicate_cpi_dates() -> None:
    df = create_employment_analysis_dataframe(
        create_test_wage_df(),
        create_test_working_hours_df(),
    )

    cpi_df = pd.concat(
        [
            create_test_cpi_df(),
            create_test_cpi_df().iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(pd.errors.MergeError):
        merge_employment_analysis_with_cpi(
            df,
            cpi_df,
        )


def test_add_real_employment_values() -> None:
    df = pd.DataFrame(
        {
            "nominal_wage_amount": [
                300_000.0,
            ],
            "approx_hourly_wage": [
                2000.0,
            ],
            "index_value": [
                120.0,
            ],
        }
    )

    result = add_real_employment_values(df)

    assert result.iloc[0]["real_regular_wage"] == pytest.approx(250_000.0)

    assert result.iloc[0]["real_approx_hourly_wage"] == pytest.approx(1666.6666667)


def test_add_real_employment_values_raises_when_cpi_not_positive() -> None:
    df = pd.DataFrame(
        {
            "nominal_wage_amount": [300_000.0],
            "approx_hourly_wage": [2000.0],
            "index_value": [0.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="CPIには0より大きい値が必要です",
    ):
        add_real_employment_values(df)


def test_add_real_employment_analysis() -> None:
    df = create_employment_analysis_dataframe(
        create_test_wage_df(),
        create_test_working_hours_df(),
    )

    cpi_df = create_test_cpi_df()

    result = add_real_employment_analysis(
        df,
        cpi_df,
    )

    assert {
        "index_value",
        "real_regular_wage",
        "real_approx_hourly_wage",
    }.issubset(result.columns)


def create_real_test_df() -> pd.DataFrame:
    dates = pd.date_range(
        "2020-01-01",
        periods=13,
        freq="MS",
    )

    return pd.DataFrame(
        {
            "date": dates,
            "real_regular_wage": [100.0] * 12 + [110.0],
            "real_approx_hourly_wage": [100.0] * 12 + [105.0],
        }
    )


def test_add_real_employment_indices() -> None:
    df = create_real_test_df()

    result = add_real_employment_indices(df)

    base_df = result[result["date"].dt.year == 2020]

    assert base_df["real_regular_wage_index"].mean() == pytest.approx(100.0)
    assert base_df["real_approx_hourly_wage_index"].mean() == pytest.approx(100.0)

    assert result.iloc[-1]["real_regular_wage_index"] == pytest.approx(110.0)
    assert result.iloc[-1]["real_approx_hourly_wage_index"] == pytest.approx(105.0)


def test_add_real_employment_changes() -> None:
    df = create_real_test_df()

    result = add_real_employment_changes(df)

    latest = result.iloc[-1]

    assert latest["real_regular_wage_yoy_pct"] == pytest.approx(10.0)
    assert latest["real_approx_hourly_wage_yoy_pct"] == pytest.approx(5.0)


def test_add_real_employment_changes_first_12_months_are_nan() -> None:
    df = create_real_test_df()

    result = add_real_employment_changes(df)

    assert result.iloc[:12]["real_regular_wage_yoy_pct"].isna().all()
    assert result.iloc[:12]["real_approx_hourly_wage_yoy_pct"].isna().all()


def create_decomposition_test_df() -> pd.DataFrame:
    dates = pd.date_range(
        "2020-01-01",
        periods=13,
        freq="MS",
    )

    nominal_wage = [200.0] * 12 + [231.0]
    working_hours = [100.0] * 12 + [105.0]

    approx_hourly_wage = [
        wage / hours
        for wage, hours in zip(
            nominal_wage,
            working_hours,
            strict=True,
        )
    ]

    return pd.DataFrame(
        {
            "date": dates,
            "nominal_wage_amount": nominal_wage,
            "working_hours": working_hours,
            "approx_hourly_wage": approx_hourly_wage,
        }
    )


def test_add_wage_change_decomposition() -> None:
    df = create_decomposition_test_df()

    result = add_wage_change_decomposition(df)

    latest = result.iloc[-1]

    total = latest["wage_log_change_pct"]
    hourly = latest["hourly_wage_contribution_pct"]
    hours = latest["working_hours_contribution_pct"]

    assert total == pytest.approx(hourly + hours)


def test_add_wage_change_decomposition_first_12_months_are_nan() -> None:
    df = create_decomposition_test_df()

    result = add_wage_change_decomposition(df)

    assert result.iloc[:12]["wage_log_change_pct"].isna().all()
    assert result.iloc[:12]["hourly_wage_contribution_pct"].isna().all()
    assert result.iloc[:12]["working_hours_contribution_pct"].isna().all()


def test_add_wage_change_decomposition_raises_when_required_column_missing() -> None:
    df = create_decomposition_test_df().drop(columns=["working_hours"])

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        add_wage_change_decomposition(df)


def test_add_wage_change_decomposition_raises_when_value_not_positive() -> None:
    df = create_decomposition_test_df()

    df.loc[0, "working_hours"] = 0.0

    with pytest.raises(
        ValueError,
        match="0より大きい賃金・労働時間データが必要",
    ):
        add_wage_change_decomposition(df)
