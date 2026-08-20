import pandas as pd
import pytest

from real_wage_dashboard.wage_composition_analysis import (
    add_annual_wage_contributions,
    add_wage_composition_changes,
    add_wage_composition_contributions,
    add_wage_composition_moving_averages,
    add_wage_composition_shares,
    create_annual_wage_composition_summary,
    create_complete_annual_wage_composition_summary,
    create_long_term_wage_composition_comparison,
    create_wage_composition_dataframe,
)


def make_composition_df(periods: int = 13) -> pd.DataFrame:
    """給与構成分析用の簡単なテストデータを作る。"""

    dates = pd.date_range(
        "2024-01-01",
        periods=periods,
        freq="MS",
    )

    scheduled = [800.0] * periods
    overtime = [100.0] * periods
    special = [100.0] * periods

    if periods >= 13:
        scheduled[12] = 880.0
        overtime[12] = 110.0
        special[12] = 110.0

    total = [
        scheduled_value + overtime_value + special_value
        for scheduled_value, overtime_value, special_value in zip(
            scheduled,
            overtime,
            special,
            strict=True,
        )
    ]

    regular = [
        scheduled_value + overtime_value
        for scheduled_value, overtime_value in zip(
            scheduled,
            overtime,
            strict=True,
        )
    ]

    return pd.DataFrame(
        {
            "date": dates,
            "total_cash_earnings": total,
            "regular_earnings": regular,
            "scheduled_earnings": scheduled,
            "overtime_earnings": overtime,
            "special_earnings": special,
        }
    )


def test_create_wage_composition_dataframe_extracts_required_series() -> None:
    raw_df = pd.DataFrame(
        {
            "年": ["2025", "2025"],
            "月": ["1", "CY"],
            "産業分類": ["TL", "TL"],
            "規模": ["T", "T"],
            "就業形態": ["0", "0"],
            "現金給与総額": ["1,000", "12,000"],
            "きまって支給する給与": ["900", "10,800"],
            "所定内給与": ["800", "9,600"],
            "所定外給与": ["100", "1,200"],
            "特別給与": ["100", "1,200"],
        }
    )

    result = create_wage_composition_dataframe(raw_df)

    assert len(result) == 1
    assert result.loc[0, "date"] == pd.Timestamp("2025-01-01")
    assert result.loc[0, "total_cash_earnings"] == 1000
    assert result.loc[0, "regular_earnings"] == 900
    assert result.loc[0, "scheduled_earnings"] == 800
    assert result.loc[0, "overtime_earnings"] == 100
    assert result.loc[0, "special_earnings"] == 100


def test_create_wage_composition_dataframe_raises_when_column_is_missing() -> None:
    raw_df = pd.DataFrame(
        {
            "年": ["2025"],
            "月": ["1"],
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        create_wage_composition_dataframe(raw_df)


def test_create_wage_composition_dataframe_raises_when_date_is_duplicated() -> None:
    raw_df = pd.DataFrame(
        {
            "年": ["2025", "2025"],
            "月": ["1", "1"],
            "産業分類": ["TL", "TL"],
            "規模": ["T", "T"],
            "就業形態": ["0", "0"],
            "現金給与総額": [1000, 1000],
            "きまって支給する給与": [900, 900],
            "所定内給与": [800, 800],
            "所定外給与": [100, 100],
            "特別給与": [100, 100],
        }
    )

    with pytest.raises(
        ValueError,
        match="重複年月",
    ):
        create_wage_composition_dataframe(raw_df)


def test_add_wage_composition_changes_calculates_yoy_diff_and_pct() -> None:
    df = make_composition_df()

    result = add_wage_composition_changes(df)

    assert result.loc[:11, "total_cash_earnings_yoy_pct"].isna().all()

    assert result.loc[
        12,
        "total_cash_earnings_yoy_diff",
    ] == pytest.approx(100.0)

    assert result.loc[
        12,
        "total_cash_earnings_yoy_pct",
    ] == pytest.approx(10.0)

    assert result.loc[
        12,
        "scheduled_earnings_yoy_pct",
    ] == pytest.approx(10.0)


def test_add_wage_composition_changes_requires_continuous_12_months() -> None:
    df = make_composition_df(periods=14)

    df = df.drop(index=5).reset_index(drop=True)

    result = add_wage_composition_changes(df)

    assert pd.isna(
        result.loc[
            result["date"] == pd.Timestamp("2025-02-01"),
            "total_cash_earnings_yoy_pct",
        ].iloc[0]
    )


def test_add_wage_composition_contributions_sum_to_total_yoy() -> None:
    df = make_composition_df()

    result = add_wage_composition_contributions(df)

    assert result.loc[
        12,
        "scheduled_earnings_contribution_pt",
    ] == pytest.approx(8.0)

    assert result.loc[
        12,
        "overtime_earnings_contribution_pt",
    ] == pytest.approx(1.0)

    assert result.loc[
        12,
        "special_earnings_contribution_pt",
    ] == pytest.approx(1.0)

    assert result.loc[
        12,
        "contribution_total_pt",
    ] == pytest.approx(10.0)

    assert result.loc[
        12,
        "total_cash_earnings_yoy_pct",
    ] == pytest.approx(10.0)

    assert result.loc[
        12,
        "contribution_error_pt",
    ] == pytest.approx(0.0)


def test_add_wage_composition_shares_sum_to_100() -> None:
    df = make_composition_df(periods=1)

    result = add_wage_composition_shares(df)

    share_sum = (
        result.loc[0, "scheduled_earnings_share_pct"]
        + result.loc[0, "overtime_earnings_share_pct"]
        + result.loc[0, "special_earnings_share_pct"]
    )

    assert share_sum == pytest.approx(100.0)
    assert result.loc[
        0,
        "scheduled_earnings_share_pct",
    ] == pytest.approx(80.0)


def test_add_wage_composition_moving_averages_starts_after_12_months() -> None:
    df = make_composition_df()

    result = add_wage_composition_moving_averages(df)

    assert result.loc[
        :10,
        "total_cash_earnings_ma_12",
    ].isna().all()

    assert result.loc[
        11,
        "total_cash_earnings_ma_12",
    ] == pytest.approx(1000.0)

    assert result.loc[
        11,
        "scheduled_earnings_ma_12",
    ] == pytest.approx(800.0)


def test_create_annual_wage_composition_summary_calculates_annual_mean() -> None:
    df = make_composition_df(periods=24)

    result = create_annual_wage_composition_summary(
        df,
        years=[2024],
    )

    assert len(result) == 1
    assert result.loc[0, "year"] == 2024
    assert result.loc[
        0,
        "total_cash_earnings",
    ] == pytest.approx(1000.0)

    assert result.loc[
        0,
        "scheduled_share_pct",
    ] == pytest.approx(80.0)


def test_create_annual_wage_composition_summary_raises_for_incomplete_year() -> None:
    df = make_composition_df(periods=11)

    with pytest.raises(
        ValueError,
        match="12か月揃っていません",
    ):
        create_annual_wage_composition_summary(
            df,
            years=[2024],
        )


def test_create_long_term_comparison_decomposes_total_change() -> None:
    annual_df = pd.DataFrame(
        {
            "year": [2015, 2025],
            "total_cash_earnings": [1000.0, 1100.0],
            "scheduled_earnings": [800.0, 880.0],
            "overtime_earnings": [100.0, 110.0],
            "special_earnings": [100.0, 110.0],
        }
    )

    result = create_long_term_wage_composition_comparison(
        annual_df,
        start_year=2015,
        end_year=2025,
    )

    total = result.loc[
        result["component"] == "total_cash_earnings",
        "contribution_pt",
    ].iloc[0]

    components = result.loc[
        result["component"] != "total_cash_earnings",
        "contribution_pt",
    ].sum()

    assert total == pytest.approx(10.0)
    assert components == pytest.approx(10.0)


def test_create_complete_annual_summary_excludes_incomplete_year() -> None:
    df = make_composition_df(periods=13)

    result = create_complete_annual_wage_composition_summary(df)

    assert result["year"].tolist() == [2024]


def test_add_annual_wage_contributions_decomposes_yoy() -> None:
    annual_df = pd.DataFrame(
        {
            "year": [2024, 2025],
            "total_cash_earnings": [1000.0, 1100.0],
            "scheduled_earnings": [800.0, 880.0],
            "overtime_earnings": [100.0, 110.0],
            "special_earnings": [100.0, 110.0],
        }
    )

    result = add_annual_wage_contributions(annual_df)

    assert pd.isna(result.loc[0, "total_yoy_pct"])

    assert result.loc[
        1,
        "total_yoy_pct",
    ] == pytest.approx(10.0)

    assert result.loc[
        1,
        "scheduled_earnings_contribution_pt",
    ] == pytest.approx(8.0)

    assert result.loc[
        1,
        "overtime_earnings_contribution_pt",
    ] == pytest.approx(1.0)

    assert result.loc[
        1,
        "special_earnings_contribution_pt",
    ] == pytest.approx(1.0)

    assert result.loc[
        1,
        "contribution_total_pt",
    ] == pytest.approx(10.0)
