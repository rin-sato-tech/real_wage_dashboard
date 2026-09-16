import pandas as pd

from real_wage_dashboard.take_home_export import (
    create_japanese_tableau_export,
    create_take_home_tableau_export,
)


def test_create_take_home_tableau_export() -> None:
    main = pd.DataFrame(
        {
            "year": [
                1990,
                2025,
            ],
            "gross_salary_yen": [
                3_900_000.0,
                4_200_000.0,
            ],
            "real_take_home_index": [
                100.0,
                81.4,
            ],
        }
    )

    period_log = pd.DataFrame(
        {
            "period": [
                "1990→2025",
            ],
            "start_year": [
                1990,
            ],
            "end_year": [
                2025,
            ],
            "wage_log_contribution_pt": [
                8.0,
            ],
        }
    )

    burden_change = pd.DataFrame(
        {
            "period": [
                "1990→2025",
            ],
            "start_year": [
                1990,
            ],
            "end_year": [
                2025,
            ],
            "total_change_pt": [
                3.78,
            ],
        }
    )

    burden_shapley = pd.DataFrame(
        {
            "period": [
                "1990→2025",
            ],
            "start_year": [
                1990,
            ],
            "end_year": [
                2025,
            ],
            "social_insurance_policy_effect_pt": [
                4.23,
            ],
        }
    )

    real_shapley = pd.DataFrame(
        {
            "period": [
                "1990→2025",
            ],
            "start_year": [
                1990,
            ],
            "end_year": [
                2025,
            ],
            "price_effect_yen": [
                -790_000.0,
            ],
            "price_effect_pct_of_start": [
                -21.68,
            ],
        }
    )

    fixed_policy = pd.DataFrame(
        {
            "year": [
                1990,
                2025,
            ],
            "actual_nominal_take_home_yen": [
                3_270_000.0,
                3_380_000.0,
            ],
            "fixed_1990_nominal_take_home_yen": [
                3_270_000.0,
                3_500_000.0,
            ],
            "actual_real_take_home_yen": [
                3_640_000.0,
                2_960_000.0,
            ],
            "fixed_1990_real_take_home_yen": [
                3_640_000.0,
                3_070_000.0,
            ],
            "actual_total_deductions_yen": [
                670_000.0,
                886_000.0,
            ],
            "fixed_1990_total_deductions_yen": [
                670_000.0,
                766_000.0,
            ],
            "actual_effective_burden_rate": [
                0.17,
                0.208,
            ],
            "fixed_1990_effective_burden_rate": [
                0.17,
                0.180,
            ],
            "actual_income_tax_yen": [
                195_000.0,
                75_000.0,
            ],
            "fixed_1990_income_tax_yen": [
                195_000.0,
                216_000.0,
            ],
            "actual_resident_tax_yen": [
                122_000.0,
                195_000.0,
            ],
            "fixed_1990_resident_tax_yen": [
                122_000.0,
                143_000.0,
            ],
            "actual_pension_yen": [
                206_000.0,
                382_000.0,
            ],
            "fixed_1990_pension_yen": [
                206_000.0,
                240_000.0,
            ],
            "actual_health_insurance_yen": [
                124_000.0,
                209_000.0,
            ],
            "fixed_1990_health_insurance_yen": [
                124_000.0,
                144_000.0,
            ],
            "actual_employment_insurance_yen": [
                22_000.0,
                24_000.0,
            ],
            "fixed_1990_employment_insurance_yen": [
                22_000.0,
                23_000.0,
            ],
            "nominal_take_home_yen_difference_yen": [
                0.0,
                -120_000.0,
            ],
            "real_take_home_difference_yen": [
                0.0,
                -110_000.0,
            ],
            "burden_rate_difference_pt": [
                0.0,
                2.8,
            ],
        }
    )

    robustness = pd.DataFrame(
        {
            "check": [
                "sex",
            ],
            "comparison": [
                "female",
            ],
            "period": [
                "1990→2025",
            ],
            "metric": [
                "real_take_home_change_pct",
            ],
            "value": [
                -18.78,
            ],
            "unit": [
                "pct",
            ],
            "note": [
                "test",
            ],
        }
    )

    result = (
        create_take_home_tableau_export(
            main_series=main,
            period_log_decomposition=(
                period_log
            ),
            burden_change_summary=(
                burden_change
            ),
            burden_shapley=(
                burden_shapley
            ),
            real_shapley=real_shapley,
            fixed_policy_comparison=(
                fixed_policy
            ),
            robustness_summary=(
                robustness
            ),
        )
    )

    assert not result.empty

    assert {
        "annual_main",
        "period_log_decomposition",
        "burden_change",
        "burden_shapley",
        "real_take_home_shapley",
        "fixed_policy_comparison",
        "robustness",
    } == set(
        result[
            "record_type"
        ].unique()
    )

    annual = result.loc[
        (
            result[
                "record_type"
            ] == "annual_main"
        )
        & (
            result[
                "metric"
            ] == "gross_salary_yen"
        )
    ]

    assert len(annual) == 2
    assert set(
        annual["unit"]
    ) == {"yen"}

    assert (
        result["analysis"]
        == "take_home_wage"
    ).all()

    shapley_pct = result.loc[
        (
            result["record_type"]
            == "real_take_home_shapley"
        )
        & (
            result["metric"]
            == "price_effect_pct_of_start"
        )
    ]

    assert len(shapley_pct) == 1
    assert (
        shapley_pct.iloc[0]["unit"]
        == "pct"
    )

    fixed_2025 = result.loc[
        (
            result["record_type"]
            == "fixed_policy_comparison"
        )
        & (
            result["year"]
            == 2025
        )
        & (
            result["comparison"]
            == "actual_minus_fixed_1990"
        )
        & (
            result["metric"]
            == "nominal_take_home_difference_yen"
        )
    ]

    assert len(fixed_2025) == 1
    assert (
        fixed_2025.iloc[0]["value"]
        == -120_000.0
    )


def test_create_japanese_tableau_export_keeps_metric_id():
    source = pd.DataFrame(
        {
            "analysis": [
                "take_home_wage",
            ],
            "record_type": [
                "annual_main",
            ],
            "year": [
                2025,
            ],
            "period": [
                pd.NA,
            ],
            "start_year": [
                pd.NA,
            ],
            "end_year": [
                pd.NA,
            ],
            "metric": [
                "gross_salary_yen",
            ],
            "value": [
                4_267_634.0,
            ],
            "unit": [
                "yen",
            ],
            "check": [
                pd.NA,
            ],
            "comparison": [
                pd.NA,
            ],
            "note": [
                pd.NA,
            ],
            "industry": [
                "調査産業計",
            ],
            "establishment_size": [
                "5人以上",
            ],
            "employment_type": [
                "就業形態計",
            ],
            "model_age": [
                35,
            ],
            "model_sex": [
                "male",
            ],
            "resident_tax_timing": [
                "income_year",
            ],
            "cpi_series": [
                "持家の帰属家賃を除く総合",
            ],
            "base_year": [
                1990,
            ],
        }
    )

    result = (
        create_japanese_tableau_export(
            source
        )
    )

    assert (
        result.iloc[0]["指標ID"]
        == "gross_salary_yen"
    )

    assert (
        result.iloc[0]["指標"]
        == "額面賃金"
    )

    assert (
        result.iloc[0]["分析"]
        == "手取り賃金分析"
    )

    assert (
        result.iloc[0]["レコード種別ID"]
        == "annual_main"
    )

    assert (
        result.iloc[0]["レコード種別"]
        == "年次主系列"
    )

    assert (
        result.iloc[0]["単位ID"]
        == "yen"
    )

    assert (
        result.iloc[0]["単位"]
        == "円"
    )

    assert (
        result.iloc[0]["モデル性別"]
        == "男性"
    )

    assert (
        result.iloc[0]["住民税対応"]
        == "所得年対応"
    )


def test_create_japanese_tableau_export_keeps_unknown_label():
    source = pd.DataFrame(
        {
            "analysis": ["take_home_wage"],
            "record_type": ["unknown_type"],
            "year": [2025],
            "period": [pd.NA],
            "start_year": [pd.NA],
            "end_year": [pd.NA],
            "metric": ["unknown_metric"],
            "value": [1.0],
            "unit": ["unknown_unit"],
            "check": ["unknown_check"],
            "comparison": ["unknown_case"],
            "note": [pd.NA],
            "industry": ["調査産業計"],
            "establishment_size": ["5人以上"],
            "employment_type": ["就業形態計"],
            "model_age": [35],
            "model_sex": ["male"],
            "resident_tax_timing": ["income_year"],
            "cpi_series": ["持家の帰属家賃を除く総合"],
            "base_year": [1990],
        }
    )

    result = (
        create_japanese_tableau_export(
            source
        )
    )

    assert (
        result.iloc[0]["レコード種別"]
        == "unknown_type"
    )

    assert (
        result.iloc[0]["指標"]
        == "unknown_metric"
    )

    assert (
        result.iloc[0]["比較ケース"]
        == "unknown_case"
    )
