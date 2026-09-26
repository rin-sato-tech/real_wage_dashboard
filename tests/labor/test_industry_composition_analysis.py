import pandas as pd
import pytest

from real_wage_dashboard.config import WAGE_DATA_PATH
from real_wage_dashboard.industry_composition_analysis import (
    COMPOSITION_INDUSTRIES,
    add_industry_employment_share,
    create_all_industry_employment_monthly_dataframe,
    create_employment_type_composition_summary,
    create_industry_composition_analysis_discussion,
    create_industry_composition_analysis_results,
    create_industry_composition_base_dataframe,
    create_industry_composition_decomposition,
    create_industry_employment_monthly_dataframe,
    create_industry_employment_yearly_dataframe,
    create_industry_wage_yearly_dataframe,
    create_reconstructed_average_wage_dataframe,
    identify_composition_notable_industries,
)
from real_wage_dashboard.wage_service import load_wage_csv


def load_raw_wage_df() -> pd.DataFrame:
    """毎月勤労統計の元データを読み込む。"""

    return load_wage_csv(WAGE_DATA_PATH)


def create_base_dataframe() -> pd.DataFrame:
    """産業構成効果分析用の年次ベースDataFrameを作成する。"""

    raw_df = load_raw_wage_df()

    employment_monthly = create_all_industry_employment_monthly_dataframe(
        raw_df,
    )

    employment_yearly = create_industry_employment_yearly_dataframe(
        employment_monthly,
    )

    employment_yearly = add_industry_employment_share(
        employment_yearly,
    )

    wage_yearly = create_industry_wage_yearly_dataframe(
        raw_df,
    )

    return create_industry_composition_base_dataframe(
        wage_yearly,
        employment_yearly,
    )


def test_create_industry_employment_monthly_dataframe() -> None:
    result = create_industry_employment_monthly_dataframe(
        load_raw_wage_df(),
        industry_code="E",
    )

    assert list(result.columns) == [
        "date",
        "industry",
        "previous_month_end_employment",
        "current_month_end_employment",
        "monthly_employment",
    ]

    assert not result.empty
    assert result["industry"].eq("E").all()
    assert result.isna().sum().sum() == 0
    assert (result["monthly_employment"] > 0).all()


def test_monthly_employment_is_average_of_month_end_counts() -> None:
    result = create_industry_employment_monthly_dataframe(
        load_raw_wage_df(),
        industry_code="E",
    )

    expected = (
        result["previous_month_end_employment"] + result["current_month_end_employment"]
    ) / 2

    assert (result["monthly_employment"] - expected).abs().max() < 1e-10


def test_all_composition_industries_are_included() -> None:
    result = create_all_industry_employment_monthly_dataframe(
        load_raw_wage_df(),
    )

    assert set(result["industry"]) == set(COMPOSITION_INDUSTRIES)
    assert result["industry"].nunique() == 16


def test_employment_yearly_keeps_complete_years() -> None:
    monthly = create_all_industry_employment_monthly_dataframe(
        load_raw_wage_df(),
    )

    yearly = create_industry_employment_yearly_dataframe(
        monthly,
    )

    assert yearly["month_count"].eq(12).all()

    target = yearly[yearly["year"].isin([2015, 2025])]

    assert target.groupby("year")["industry"].nunique().to_dict() == {
        2015: 16,
        2025: 16,
    }


def test_employment_share_sums_to_one() -> None:
    monthly = create_all_industry_employment_monthly_dataframe(
        load_raw_wage_df(),
    )

    yearly = create_industry_employment_yearly_dataframe(
        monthly,
    )

    result = add_industry_employment_share(
        yearly,
    )

    target = result[result["year"].isin([2015, 2025])]

    share_sum = target.groupby("year")["employment_share"].sum()

    assert share_sum.loc[2015] == pytest.approx(1.0)
    assert share_sum.loc[2025] == pytest.approx(1.0)


def test_composition_base_dataframe_has_no_missing_values() -> None:
    result = create_base_dataframe()

    target = result[result["year"].isin([2015, 2025])]

    assert target.groupby("year")["industry"].nunique().to_dict() == {
        2015: 16,
        2025: 16,
    }

    assert (
        target[
            [
                "monthly_wage",
                "annual_employment",
                "employment_share",
            ]
        ]
        .isna()
        .sum()
        .sum()
        == 0
    )

    assert (
        target.duplicated(
            subset=[
                "industry",
                "year",
            ]
        ).sum()
        == 0
    )


def test_reconstructed_wage_matches_total_industry() -> None:
    base_df = create_base_dataframe()

    reconstructed = create_reconstructed_average_wage_dataframe(
        base_df,
    )

    wage_2015 = reconstructed.loc[
        reconstructed["year"] == 2015,
        "reconstructed_wage",
    ].iloc[0]

    wage_2025 = reconstructed.loc[
        reconstructed["year"] == 2025,
        "reconstructed_wage",
    ].iloc[0]

    assert wage_2015 == pytest.approx(
        260577.829012,
        abs=0.01,
    )

    assert wage_2025 == pytest.approx(
        287413.112992,
        abs=0.01,
    )


def test_composition_decomposition_identity() -> None:
    base_df = create_base_dataframe()

    reconstructed = create_reconstructed_average_wage_dataframe(
        base_df,
    )

    decomposition = create_industry_composition_decomposition(
        base_df,
        start_year=2015,
        end_year=2025,
    )

    decomposed_change = (
        decomposition["within_wage_effect"].sum()
        + decomposition["composition_effect"].sum()
        + decomposition["interaction_effect"].sum()
    )

    start_wage = reconstructed.loc[
        reconstructed["year"] == 2015,
        "reconstructed_wage",
    ].iloc[0]

    end_wage = reconstructed.loc[
        reconstructed["year"] == 2025,
        "reconstructed_wage",
    ].iloc[0]

    actual_change = end_wage - start_wage

    assert decomposed_change == pytest.approx(
        actual_change,
        abs=1e-8,
    )


def test_centered_composition_effect_has_same_total() -> None:
    decomposition = create_industry_composition_decomposition(
        create_base_dataframe(),
        start_year=2015,
        end_year=2025,
    )

    original = decomposition["composition_effect"].sum()

    centered = decomposition["centered_composition_effect"].sum()

    assert centered == pytest.approx(
        original,
        abs=1e-8,
    )


def test_identify_composition_notable_industries() -> None:
    decomposition = create_industry_composition_decomposition(
        create_base_dataframe(),
        start_year=2015,
        end_year=2025,
    )

    result = identify_composition_notable_industries(
        decomposition,
    )

    assert result == {
        "share_increase_max": "P",
        "share_decrease_max": "E",
        "within_effect_max": "E",
        "composition_effect_max": "G",
        "composition_effect_min": "E",
        "total_contribution_max": "P",
        "total_contribution_min": "H",
    }


def test_industry_composition_analysis_texts() -> None:
    base_df = create_base_dataframe()

    reconstructed = create_reconstructed_average_wage_dataframe(
        base_df,
    )

    decomposition = create_industry_composition_decomposition(
        base_df,
        start_year=2015,
        end_year=2025,
    )

    results = create_industry_composition_analysis_results(
        decomposition,
        reconstructed,
    )

    discussion = create_industry_composition_analysis_discussion(
        decomposition,
    )

    assert len(results) > 0
    assert len(discussion) > 0

    assert any("産業内賃金効果" in text for text in results)

    assert any("2015→2019" in text for text in discussion)


def test_create_employment_type_composition_summary() -> None:
    raw_df = load_raw_wage_df()

    comparison_industries = [
        industry for industry in COMPOSITION_INDUSTRIES if industry != "C"
    ]

    result = create_employment_type_composition_summary(
        raw_df,
        industry_codes=comparison_industries,
        start_year=2015,
        end_year=2025,
    )

    assert result["employment_type"].to_list() == [
        "就業形態計",
        "一般労働者",
        "パートタイム労働者",
    ]

    assert result["industry_count"].eq(15).all()

    actual = result.set_index("employment_type")

    assert actual.loc[
        "就業形態計",
        "composition_effect_pt",
    ] == pytest.approx(-0.212, abs=0.001)

    assert actual.loc[
        "一般労働者",
        "composition_effect_pt",
    ] == pytest.approx(-0.082, abs=0.001)

    assert actual.loc[
        "パートタイム労働者",
        "composition_effect_pt",
    ] == pytest.approx(0.377, abs=0.001)

    assert actual.loc[
        "パートタイム労働者",
        "within_effect_pt",
    ] == pytest.approx(15.070, abs=0.001)
