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
    calculate_change_rate,
    calculate_yearly_averages,
    calculate_yearly_change_rates,
    compare_employment_change_rates,
    create_employment_analysis_dataframe,
    create_employment_analysis_discussion,
    create_full_employment_analysis_dataframe,
    create_yearly_comparison_summary,
    describe_change_direction,
    merge_employment_analysis_with_cpi,
    merge_wage_and_working_hours,
    summarize_wage_change_decomposition,
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

    total = latest["wage_log_change"]
    hourly = latest["hourly_wage_log_contribution"]
    hours = latest["working_hours_log_contribution"]

    assert total == pytest.approx(hourly + hours)


def test_add_wage_change_decomposition_first_12_months_are_nan() -> None:
    df = create_decomposition_test_df()

    result = add_wage_change_decomposition(df)

    assert result.iloc[:12]["wage_log_change"].isna().all()
    assert result.iloc[:12]["hourly_wage_log_contribution"].isna().all()
    assert result.iloc[:12]["working_hours_log_contribution"].isna().all()


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


def create_full_analysis_test_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    dates = pd.date_range(
        "2020-01-01",
        periods=13,
        freq="MS",
    )

    wage_df = pd.DataFrame(
        {
            "date": dates,
            "nominal_wage_amount": [200_000.0] * 12 + [220_000.0],
        }
    )

    working_hours_df = pd.DataFrame(
        {
            "date": dates,
            "working_hours": [100.0] * 12 + [105.0],
        }
    )

    cpi_df = pd.DataFrame(
        {
            "date": dates,
            "index_value": [100.0] * 12 + [105.0],
        }
    )

    return wage_df, working_hours_df, cpi_df


def test_create_full_employment_analysis_dataframe() -> None:
    wage_df, working_hours_df, cpi_df = create_full_analysis_test_data()

    result = create_full_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
        cpi_df,
    )

    expected_columns = {
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
        "regular_wage_index",
        "working_hours_index",
        "approx_hourly_wage_index",
        "regular_wage_yoy_pct",
        "working_hours_yoy_pct",
        "approx_hourly_wage_yoy_pct",
        "index_value",
        "real_regular_wage",
        "real_approx_hourly_wage",
        "real_regular_wage_index",
        "real_approx_hourly_wage_index",
        "real_regular_wage_yoy_pct",
        "real_approx_hourly_wage_yoy_pct",
        "wage_log_change",
        "hourly_wage_log_contribution",
        "working_hours_log_contribution",
    }

    assert expected_columns.issubset(result.columns)
    assert len(result) == 13


def test_create_full_employment_analysis_dataframe_base_year_indices() -> None:
    wage_df, working_hours_df, cpi_df = create_full_analysis_test_data()

    result = create_full_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
        cpi_df,
    )

    base_df = result[result["date"].dt.year == 2020]

    index_columns = [
        "regular_wage_index",
        "working_hours_index",
        "approx_hourly_wage_index",
        "real_regular_wage_index",
        "real_approx_hourly_wage_index",
    ]

    for column in index_columns:
        assert base_df[column].mean() == pytest.approx(100.0)


def test_create_full_employment_analysis_dataframe_latest_values() -> None:
    wage_df, working_hours_df, cpi_df = create_full_analysis_test_data()

    result = create_full_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
        cpi_df,
    )

    latest = result.iloc[-1]

    assert latest["approx_hourly_wage"] == pytest.approx(220_000.0 / 105.0)

    assert latest["real_regular_wage"] == pytest.approx(220_000.0 / 105.0 * 100)

    assert latest["real_approx_hourly_wage"] == pytest.approx(
        (220_000.0 / 105.0) / 105.0 * 100
    )

    assert latest["regular_wage_yoy_pct"] == pytest.approx(10.0)
    assert latest["working_hours_yoy_pct"] == pytest.approx(5.0)


def test_create_full_employment_analysis_dataframe_decomposition() -> None:
    wage_df, working_hours_df, cpi_df = create_full_analysis_test_data()

    result = create_full_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
        cpi_df,
    )

    latest = result.iloc[-1]

    assert latest["wage_log_change"] == pytest.approx(
        latest["hourly_wage_log_contribution"]
        + latest["working_hours_log_contribution"]
    )


def test_create_full_employment_analysis_dataframe_raises_when_base_year_incomplete() -> (
    None
):
    wage_df, working_hours_df, cpi_df = create_full_analysis_test_data()

    wage_df = wage_df.iloc[:11].copy()
    working_hours_df = working_hours_df.iloc[:11].copy()
    cpi_df = cpi_df.iloc[:11].copy()

    with pytest.raises(
        ValueError,
        match="2020年の基準データが12か月揃っていません",
    ):
        create_full_employment_analysis_dataframe(
            wage_df,
            working_hours_df,
            cpi_df,
        )


def test_calculate_yearly_averages() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
            "nominal_wage_amount": [
                100.0,
                110.0,
                120.0,
                130.0,
                140.0,
                150.0,
                160.0,
                170.0,
                180.0,
                190.0,
                200.0,
                210.0,
            ],
            "working_hours": [
                100.0,
            ]
            * 12,
        }
    )

    result = calculate_yearly_averages(
        df,
        year=2025,
        columns=[
            "nominal_wage_amount",
            "working_hours",
        ],
    )

    assert result["nominal_wage_amount"] == pytest.approx(155.0)
    assert result["working_hours"] == pytest.approx(100.0)


def test_calculate_yearly_averages_raises_when_months_missing() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=11,
                freq="MS",
            ),
            "nominal_wage_amount": [
                100.0,
            ]
            * 11,
        }
    )

    with pytest.raises(
        ValueError,
        match="2025年のデータが12か月揃っていません",
    ):
        calculate_yearly_averages(
            df,
            year=2025,
            columns=["nominal_wage_amount"],
        )


def test_calculate_yearly_averages_raises_when_value_missing() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
            "nominal_wage_amount": [
                100.0,
            ]
            * 11
            + [None],
        }
    )

    with pytest.raises(
        ValueError,
        match="2025年の分析対象データに欠損値があります",
    ):
        calculate_yearly_averages(
            df,
            year=2025,
            columns=["nominal_wage_amount"],
        )


def test_calculate_yearly_averages_raises_when_column_missing() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        calculate_yearly_averages(
            df,
            year=2025,
            columns=["nominal_wage_amount"],
        )


def test_calculate_change_rate() -> None:
    result = calculate_change_rate(
        100.0,
        120.0,
    )

    assert result == pytest.approx(20.0)


def test_calculate_change_rate_returns_negative_value() -> None:
    result = calculate_change_rate(
        100.0,
        90.0,
    )

    assert result == pytest.approx(-10.0)


def test_calculate_change_rate_raises_when_start_value_zero() -> None:
    with pytest.raises(
        ValueError,
        match="開始値は0より大きい必要があります",
    ):
        calculate_change_rate(
            0.0,
            100.0,
        )


def test_calculate_yearly_change_rates() -> None:
    start = {
        "nominal_wage_amount": 200_000.0,
        "working_hours": 100.0,
    }

    end = {
        "nominal_wage_amount": 220_000.0,
        "working_hours": 95.0,
    }

    result = calculate_yearly_change_rates(
        start,
        end,
    )

    assert result["nominal_wage_amount"] == pytest.approx(10.0)
    assert result["working_hours"] == pytest.approx(-5.0)


def test_calculate_yearly_change_rates_raises_when_columns_differ() -> None:
    start = {
        "nominal_wage_amount": 200_000.0,
    }

    end = {
        "working_hours": 100.0,
    }

    with pytest.raises(
        ValueError,
        match="比較する年平均の指標が一致していません",
    ):
        calculate_yearly_change_rates(
            start,
            end,
        )


def test_create_yearly_comparison_summary() -> None:
    general_df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2015-01-01",
                "2025-12-01",
                freq="MS",
            ),
        }
    )

    general_df["nominal_wage_amount"] = general_df["date"].dt.year.map(
        lambda year: 100.0 if year == 2015 else 120.0
    )

    part_df = pd.DataFrame(
        {
            "date": pd.date_range(
                "2015-01-01",
                "2025-12-01",
                freq="MS",
            ),
        }
    )

    part_df["nominal_wage_amount"] = part_df["date"].dt.year.map(
        lambda year: 100.0 if year == 2015 else 130.0
    )

    result = create_yearly_comparison_summary(
        general_df,
        part_df,
        start_year=2015,
        end_year=2025,
        columns=["nominal_wage_amount"],
    )

    assert len(result) == 2

    general_result = result[result["employment_type"] == "一般労働者"].iloc[0]

    part_result = result[result["employment_type"] == "パートタイム労働者"].iloc[0]

    assert general_result["start_value"] == pytest.approx(100.0)
    assert general_result["end_value"] == pytest.approx(120.0)
    assert general_result["change_rate_pct"] == pytest.approx(20.0)

    assert part_result["start_value"] == pytest.approx(100.0)
    assert part_result["end_value"] == pytest.approx(130.0)
    assert part_result["change_rate_pct"] == pytest.approx(30.0)


def test_create_yearly_comparison_summary_handles_multiple_indicators() -> None:
    dates = pd.date_range(
        "2015-01-01",
        "2025-12-01",
        freq="MS",
    )

    general_df = pd.DataFrame(
        {
            "date": dates,
            "nominal_wage_amount": [
                100.0 if date.year == 2015 else 110.0 for date in dates
            ],
            "working_hours": [100.0 if date.year == 2015 else 95.0 for date in dates],
        }
    )

    part_df = pd.DataFrame(
        {
            "date": dates,
            "nominal_wage_amount": [
                100.0 if date.year == 2015 else 120.0 for date in dates
            ],
            "working_hours": [100.0 if date.year == 2015 else 90.0 for date in dates],
        }
    )

    result = create_yearly_comparison_summary(
        general_df,
        part_df,
        start_year=2015,
        end_year=2025,
        columns=[
            "nominal_wage_amount",
            "working_hours",
        ],
    )

    assert len(result) == 4

    assert set(result["indicator"]) == {
        "nominal_wage_amount",
        "working_hours",
    }

    assert set(result["employment_type"]) == {
        "一般労働者",
        "パートタイム労働者",
    }


def test_compare_employment_change_rates() -> None:
    summary_df = pd.DataFrame(
        {
            "employment_type": [
                "一般労働者",
                "パートタイム労働者",
                "一般労働者",
                "パートタイム労働者",
            ],
            "indicator": [
                "nominal_wage_amount",
                "nominal_wage_amount",
                "working_hours",
                "working_hours",
            ],
            "change_rate_pct": [
                10.0,
                20.0,
                -5.0,
                -10.0,
            ],
        }
    )

    result = compare_employment_change_rates(summary_df)

    wage_result = result[result["indicator"] == "nominal_wage_amount"].iloc[0]

    hours_result = result[result["indicator"] == "working_hours"].iloc[0]

    assert wage_result["一般労働者"] == pytest.approx(10.0)
    assert wage_result["パートタイム労働者"] == pytest.approx(20.0)
    assert wage_result["difference_pct_point"] == pytest.approx(10.0)
    assert wage_result["larger_change"] == "パートタイム労働者"

    assert hours_result["difference_pct_point"] == pytest.approx(-5.0)
    assert hours_result["larger_change"] == "一般労働者"


def test_compare_employment_change_rates_returns_same_when_equal() -> None:
    summary_df = pd.DataFrame(
        {
            "employment_type": [
                "一般労働者",
                "パートタイム労働者",
            ],
            "indicator": [
                "nominal_wage_amount",
                "nominal_wage_amount",
            ],
            "change_rate_pct": [
                10.0,
                10.0,
            ],
        }
    )

    result = compare_employment_change_rates(summary_df)

    assert result.iloc[0]["difference_pct_point"] == pytest.approx(0.0)
    assert result.iloc[0]["larger_change"] == "同程度"


def test_compare_employment_change_rates_raises_when_employment_type_missing() -> None:
    summary_df = pd.DataFrame(
        {
            "employment_type": [
                "一般労働者",
            ],
            "indicator": [
                "nominal_wage_amount",
            ],
            "change_rate_pct": [
                10.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="一般労働者とパートタイム労働者の両方のデータが必要です",
    ):
        compare_employment_change_rates(summary_df)


def test_compare_employment_change_rates_raises_when_column_missing() -> None:
    summary_df = pd.DataFrame(
        {
            "indicator": [
                "nominal_wage_amount",
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        compare_employment_change_rates(summary_df)


def test_describe_change_direction() -> None:
    assert describe_change_direction(5.0) == "上昇"
    assert describe_change_direction(-5.0) == "低下"
    assert describe_change_direction(0.05) == "横ばい"


def test_create_employment_analysis_discussion() -> None:
    summary_df = pd.DataFrame(
        {
            "employment_type": [
                "一般労働者",
                "一般労働者",
                "一般労働者",
                "一般労働者",
                "一般労働者",
                "パートタイム労働者",
                "パートタイム労働者",
                "パートタイム労働者",
                "パートタイム労働者",
                "パートタイム労働者",
            ],
            "indicator": [
                "nominal_wage_amount",
                "working_hours",
                "approx_hourly_wage",
                "real_regular_wage",
                "real_approx_hourly_wage",
                "nominal_wage_amount",
                "working_hours",
                "approx_hourly_wage",
                "real_regular_wage",
                "real_approx_hourly_wage",
            ],
            "change_rate_pct": [
                10.0,
                -5.0,
                15.8,
                2.0,
                7.0,
                20.0,
                -10.0,
                33.3,
                5.0,
                15.0,
            ],
        }
    )

    result = create_employment_analysis_discussion(summary_df)

    joined = "\n".join(result)

    assert len(result) == 3

    assert "両就業形態とも、時間当たり賃金が上昇する一方で総実労働時間は減少" in joined

    assert (
        "パートタイム労働者では、一般労働者より時間当たり賃金の伸びが大きく" in joined
    )

    assert "時間当たり賃金の改善ほど月額賃金は伸びていません" in joined

    assert (
        "両就業形態とも名目月額賃金の伸びに比べて実質月額賃金の伸びは小さく" in joined
    )

    assert "物価上昇によって" in joined


def test_summarize_wage_change_decomposition() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-02-01",
                    "2020-03-01",
                    "2020-04-01",
                ]
            ),
            "wage_log_change": [
                2.0,
                3.0,
                1.0,
                4.0,
            ],
            "hourly_wage_log_contribution": [
                3.0,
                4.0,
                2.0,
                5.0,
            ],
            "working_hours_log_contribution": [
                -1.0,
                -1.0,
                -1.0,
                -1.0,
            ],
        }
    )

    result = summarize_wage_change_decomposition(
        df,
        start_year=2020,
        end_year=2020,
    )

    assert result["n_months"] == 4
    assert result["mean_wage_log_change"] == pytest.approx(2.5)
    assert result["mean_hourly_wage_contribution"] == pytest.approx(3.5)
    assert result["mean_working_hours_contribution"] == pytest.approx(-1.0)
    assert result["hourly_positive_share_pct"] == pytest.approx(100.0)
    assert result["hours_negative_share_pct"] == pytest.approx(100.0)
    assert result["hourly_dominant_share_pct"] == pytest.approx(100.0)


def test_summarize_wage_change_decomposition_filters_years() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2019-01-01",
                    "2020-01-01",
                    "2021-01-01",
                ]
            ),
            "wage_log_change": [
                100.0,
                2.0,
                100.0,
            ],
            "hourly_wage_log_contribution": [
                100.0,
                3.0,
                100.0,
            ],
            "working_hours_log_contribution": [
                0.0,
                -1.0,
                0.0,
            ],
        }
    )

    result = summarize_wage_change_decomposition(
        df,
        start_year=2020,
        end_year=2020,
    )

    assert result["n_months"] == 1
    assert result["mean_wage_log_change"] == pytest.approx(2.0)


def test_summarize_wage_change_decomposition_raises_when_no_data() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01"]),
            "wage_log_change": [2.0],
            "hourly_wage_log_contribution": [3.0],
            "working_hours_log_contribution": [-1.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="指定期間に要因分解データがありません",
    ):
        summarize_wage_change_decomposition(
            df,
            start_year=2025,
            end_year=2025,
        )
