import pandas as pd
import pytest

from real_wage_dashboard.take_home_analysis import (
    _floor_to_hundred_yen,
    _floor_to_thousand_yen,
    _get_fiscal_year,
    _select_assessment_year_rules,
    _select_effective_rules,
    _select_health_insurance_rate_rule,
    _select_pension_rate_rule,
    _select_single_assessment_year_rule,
    _select_single_effective_rule,
    _select_standard_monthly_remuneration_rule,
    calculate_annual_employment_insurance,
    calculate_annual_health_bonus_contribution,
    calculate_annual_pension_bonus_contribution,
    calculate_annual_pension_contribution,
    calculate_annual_regular_health_insurance_contribution,
    calculate_annual_regular_pension_contribution,
    calculate_base_income_tax,
    calculate_basic_deduction,
    calculate_employment_insurance,
    calculate_health_bonus_base,
    calculate_health_bonus_contribution,
    calculate_income_tax_after_adjustments,
    calculate_monthly_health_insurance_contribution,
    calculate_monthly_pension_contribution,
    calculate_pension_bonus_base,
    calculate_pension_bonus_contribution,
    calculate_reconstruction_special_income_tax,
    calculate_salary_income,
    calculate_salary_income_deduction,
    calculate_standard_monthly_remuneration,
    calculate_taxable_income,
    calculate_total_income_tax,
    create_semiannual_bonus_payments,
)


def test_select_effective_rules():
    df = pd.DataFrame(
        {
            "effective_from": [
                "2000-01-01",
                "2010-01-01",
            ],
            "effective_to": [
                "2009-12-31",
                None,
            ],
            "rate": [
                0.10,
                0.20,
            ],
        }
    )

    result = _select_effective_rules(
        df,
        "2015-01-01",
    )

    assert len(result) == 1
    assert result.loc[0, "rate"] == 0.20


def test_select_effective_rules_includes_boundary_dates():
    df = pd.DataFrame(
        {
            "effective_from": ["2000-01-01"],
            "effective_to": ["2009-12-31"],
            "rate": [0.10],
        }
    )

    start = _select_effective_rules(
        df,
        "2000-01-01",
    )

    end = _select_effective_rules(
        df,
        "2009-12-31",
    )

    assert len(start) == 1
    assert len(end) == 1


def test_select_effective_rules_accepts_open_ended_rule():
    df = pd.DataFrame(
        {
            "effective_from": ["2017-09-01"],
            "effective_to": [None],
            "rate": [0.183],
        }
    )

    result = _select_effective_rules(
        df,
        "2025-01-01",
    )

    assert len(result) == 1
    assert result.loc[0, "rate"] == 0.183


def test_select_effective_rules_rejects_invalid_start_date():
    df = pd.DataFrame(
        {
            "effective_from": ["invalid"],
            "effective_to": [None],
        }
    )

    with pytest.raises(
        ValueError,
        match="effective_from に不正な日付があります",
    ):
        _select_effective_rules(
            df,
            "2025-01-01",
        )


def test_select_assessment_year_rules():
    df = pd.DataFrame(
        {
            "assessment_year_from": [
                1999,
                2007,
            ],
            "assessment_year_to": [
                2006,
                None,
            ],
            "rate": [
                0.13,
                0.10,
            ],
        }
    )

    result = _select_assessment_year_rules(
        df,
        assessment_year=2025,
    )

    assert len(result) == 1
    assert result.loc[0, "rate"] == 0.10


def test_select_assessment_year_rules_includes_boundaries():
    df = pd.DataFrame(
        {
            "assessment_year_from": [1999],
            "assessment_year_to": [2006],
            "rate": [0.13],
        }
    )

    start = _select_assessment_year_rules(
        df,
        assessment_year=1999,
    )

    end = _select_assessment_year_rules(
        df,
        assessment_year=2006,
    )

    assert len(start) == 1
    assert len(end) == 1


def test_select_single_effective_rule_with_filter():
    df = pd.DataFrame(
        {
            "effective_from": [
                "2017-09-01",
                "2017-09-01",
            ],
            "effective_to": [
                None,
                None,
            ],
            "insured_category": [
                "general",
                "other",
            ],
            "rate": [
                0.183,
                0.15,
            ],
        }
    )

    result = _select_single_effective_rule(
        df,
        target_date="2025-01-01",
        filters={
            "insured_category": "general",
        },
    )

    assert result["rate"] == 0.183


def test_select_single_effective_rule_rejects_multiple_rows():
    df = pd.DataFrame(
        {
            "effective_from": [
                "2017-09-01",
                "2017-09-01",
            ],
            "effective_to": [
                None,
                None,
            ],
            "rate": [
                0.183,
                0.184,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="制度ルールを一意に取得できません",
    ):
        _select_single_effective_rule(
            df,
            target_date="2025-01-01",
        )


def test_select_single_assessment_year_rule_with_filter():
    df = pd.DataFrame(
        {
            "assessment_year_from": [
                2024,
                2024,
            ],
            "assessment_year_to": [
                None,
                None,
            ],
            "municipality_band": [
                "standard",
                "other",
            ],
            "municipal_yen": [
                3000,
                4000,
            ],
        }
    )

    result = _select_single_assessment_year_rule(
        df,
        assessment_year=2025,
        filters={
            "municipality_band": "standard",
        },
    )

    assert result["municipal_yen"] == 3000


def _create_salary_income_deduction_rules() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "deduction_type": [
                "salary_income",
                "salary_income",
                "salary_income",
                "salary_income",
                "salary_income",
                "salary_income",
            ],
            "effective_from": [
                "2017-01-01",
                "2017-01-01",
                "2020-01-01",
                "2020-01-01",
                "2025-01-01",
                "2025-01-01",
            ],
            "effective_to": [
                "2019-12-31",
                "2019-12-31",
                "2024-12-31",
                "2024-12-31",
                None,
                None,
            ],
            "bracket_order": [
                1,
                4,
                1,
                4,
                1,
                3,
            ],
            "basis": [
                "gross_salary",
                "gross_salary",
                "gross_salary",
                "gross_salary",
                "gross_salary",
                "gross_salary",
            ],
            "lower_bound_yen": [
                0,
                3_600_001,
                0,
                3_600_001,
                0,
                3_600_001,
            ],
            "upper_bound_yen": [
                1_625_000,
                6_600_000,
                1_625_000,
                6_600_000,
                1_900_000,
                6_600_000,
            ],
            "rate": [
                None,
                0.20,
                None,
                0.20,
                None,
                0.20,
            ],
            "add_yen": [
                None,
                540_000,
                None,
                440_000,
                None,
                440_000,
            ],
            "fixed_yen": [
                650_000,
                None,
                550_000,
                None,
                650_000,
                None,
            ],
            "source_key": ["test"] * 6,
        }
    )


def test_calculate_salary_income_deduction_fixed_amount():
    rules = _create_salary_income_deduction_rules()

    result = calculate_salary_income_deduction(
        gross_salary_yen=1_000_000,
        target_date="2020-06-01",
        deduction_rules=rules,
    )

    assert result == 550_000


def test_calculate_salary_income_deduction_does_not_exceed_salary():
    rules = _create_salary_income_deduction_rules()

    result = calculate_salary_income_deduction(
        gross_salary_yen=300_000,
        target_date="2020-06-01",
        deduction_rules=rules,
    )

    assert result == 300_000


def test_calculate_salary_income_deduction_2019():
    rules = _create_salary_income_deduction_rules()

    result = calculate_salary_income_deduction(
        gross_salary_yen=4_000_000,
        target_date="2019-06-01",
        deduction_rules=rules,
    )

    assert result == 1_340_000


def test_calculate_salary_income_deduction_2020():
    rules = _create_salary_income_deduction_rules()

    result = calculate_salary_income_deduction(
        gross_salary_yen=4_000_000,
        target_date="2020-06-01",
        deduction_rules=rules,
    )

    assert result == 1_240_000


def test_calculate_salary_income_deduction_2025():
    rules = _create_salary_income_deduction_rules()

    result = calculate_salary_income_deduction(
        gross_salary_yen=4_000_000,
        target_date="2025-06-01",
        deduction_rules=rules,
    )

    assert result == 1_240_000


def test_calculate_salary_income():
    rules = _create_salary_income_deduction_rules()

    result = calculate_salary_income(
        gross_salary_yen=4_000_000,
        target_date="2020-06-01",
        deduction_rules=rules,
    )

    assert result == 2_760_000


def test_calculate_salary_income_deduction_rejects_negative_salary():
    rules = _create_salary_income_deduction_rules()

    with pytest.raises(
        ValueError,
        match="給与収入は0以上",
    ):
        calculate_salary_income_deduction(
            gross_salary_yen=-1,
            target_date="2020-06-01",
            deduction_rules=rules,
        )


def test_calculate_salary_income_deduction_rejects_missing_rule():
    rules = _create_salary_income_deduction_rules()

    with pytest.raises(
        ValueError,
        match="有効な給与所得控除ルールがありません",
    ):
        calculate_salary_income_deduction(
            gross_salary_yen=1_000_000,
            target_date="2010-01-01",
            deduction_rules=rules,
        )


def _create_basic_deduction_rules() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "deduction_type": [
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
                "basic",
            ],
            "effective_from": [
                "1995-01-01",
                "2020-01-01",
                "2020-01-01",
                "2020-01-01",
                "2020-01-01",
                "2025-01-01",
                "2025-01-01",
                "2025-01-01",
                "2025-01-01",
                "2025-01-01",
                "2025-01-01",
                "2025-01-01",
                "2025-01-01",
                "2025-01-01",
            ],
            "effective_to": [
                "2019-12-31",
                "2024-12-31",
                "2024-12-31",
                "2024-12-31",
                "2024-12-31",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            "bracket_order": [
                1,
                1,
                2,
                3,
                4,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
            ],
            "basis": ["total_income"] * 14,
            "lower_bound_yen": [
                0,
                0,
                24_000_001,
                24_500_001,
                25_000_001,
                0,
                1_320_001,
                3_360_001,
                4_890_001,
                6_550_001,
                23_500_001,
                24_000_001,
                24_500_001,
                25_000_001,
            ],
            "upper_bound_yen": [
                None,
                24_000_000,
                24_500_000,
                25_000_000,
                None,
                1_320_000,
                3_360_000,
                4_890_000,
                6_550_000,
                23_500_000,
                24_000_000,
                24_500_000,
                25_000_000,
                None,
            ],
            "fixed_yen": [
                380_000,
                480_000,
                320_000,
                160_000,
                0,
                950_000,
                880_000,
                680_000,
                630_000,
                580_000,
                480_000,
                320_000,
                160_000,
                0,
            ],
            "source_key": ["test"] * 14,
        }
    )


def test_calculate_basic_deduction_2019():
    rules = _create_basic_deduction_rules()

    result = calculate_basic_deduction(
        total_income_yen=3_000_000,
        target_date="2019-06-01",
        deduction_rules=rules,
    )

    assert result == 380_000


def test_calculate_basic_deduction_2020():
    rules = _create_basic_deduction_rules()

    result = calculate_basic_deduction(
        total_income_yen=3_000_000,
        target_date="2020-06-01",
        deduction_rules=rules,
    )

    assert result == 480_000


def test_calculate_basic_deduction_2020_high_income():
    rules = _create_basic_deduction_rules()

    result = calculate_basic_deduction(
        total_income_yen=24_300_000,
        target_date="2020-06-01",
        deduction_rules=rules,
    )

    assert result == 320_000


def test_calculate_basic_deduction_2020_over_limit():
    rules = _create_basic_deduction_rules()

    result = calculate_basic_deduction(
        total_income_yen=26_000_000,
        target_date="2020-06-01",
        deduction_rules=rules,
    )

    assert result == 0


def test_calculate_basic_deduction_2025_standard_worker():
    rules = _create_basic_deduction_rules()

    result = calculate_basic_deduction(
        total_income_yen=2_800_000,
        target_date="2025-06-01",
        deduction_rules=rules,
    )

    assert result == 880_000


def test_calculate_basic_deduction_2025_low_income():
    rules = _create_basic_deduction_rules()

    result = calculate_basic_deduction(
        total_income_yen=1_000_000,
        target_date="2025-06-01",
        deduction_rules=rules,
    )

    assert result == 950_000


def test_calculate_basic_deduction_2025_boundary():
    rules = _create_basic_deduction_rules()

    lower_band = calculate_basic_deduction(
        total_income_yen=1_320_000,
        target_date="2025-06-01",
        deduction_rules=rules,
    )

    upper_band = calculate_basic_deduction(
        total_income_yen=1_320_001,
        target_date="2025-06-01",
        deduction_rules=rules,
    )

    assert lower_band == 950_000
    assert upper_band == 880_000


def test_calculate_basic_deduction_2025_middle_income():
    rules = _create_basic_deduction_rules()

    result = calculate_basic_deduction(
        total_income_yen=4_000_000,
        target_date="2025-06-01",
        deduction_rules=rules,
    )

    assert result == 680_000


def test_calculate_basic_deduction_rejects_negative_income():
    rules = _create_basic_deduction_rules()

    with pytest.raises(
        ValueError,
        match="合計所得金額は0以上",
    ):
        calculate_basic_deduction(
            total_income_yen=-1,
            target_date="2025-06-01",
            deduction_rules=rules,
        )


def test_calculate_basic_deduction_rejects_missing_rule():
    rules = _create_basic_deduction_rules()

    with pytest.raises(
        ValueError,
        match="有効な基礎控除ルールがありません",
    ):
        calculate_basic_deduction(
            total_income_yen=3_000_000,
            target_date="1990-01-01",
            deduction_rules=rules,
        )


def test_floor_to_thousand_yen():
    result = _floor_to_thousand_yen(
        1_234_567,
    )

    assert result == 1_234_000


def test_floor_to_thousand_yen_exact():
    result = _floor_to_thousand_yen(
        1_234_000,
    )

    assert result == 1_234_000


def test_floor_to_thousand_yen_below_thousand():
    result = _floor_to_thousand_yen(
        999,
    )

    assert result == 0


def test_floor_to_thousand_yen_rejects_negative():
    with pytest.raises(
        ValueError,
        match="切り捨て対象金額は0以上",
    ):
        _floor_to_thousand_yen(
            -1,
        )


def test_calculate_taxable_income():
    result = calculate_taxable_income(
        salary_income_yen=2_760_000,
        basic_deduction_yen=480_000,
        social_insurance_deduction_yen=600_123,
    )

    assert result == 1_679_000


def test_calculate_taxable_income_floor_at_zero():
    result = calculate_taxable_income(
        salary_income_yen=500_000,
        basic_deduction_yen=950_000,
        social_insurance_deduction_yen=100_000,
    )

    assert result == 0


def test_calculate_taxable_income_with_other_deductions():
    result = calculate_taxable_income(
        salary_income_yen=3_000_000,
        basic_deduction_yen=480_000,
        social_insurance_deduction_yen=500_000,
        other_income_deductions_yen=100_500,
    )

    assert result == 1_919_000


@pytest.mark.parametrize(
    (
        "salary_income_yen",
        "basic_deduction_yen",
        "social_insurance_deduction_yen",
        "other_income_deductions_yen",
        "message",
    ),
    [
        (
            -1,
            0,
            0,
            0,
            "給与所得は0以上",
        ),
        (
            0,
            -1,
            0,
            0,
            "基礎控除は0以上",
        ),
        (
            0,
            0,
            -1,
            0,
            "社会保険料控除は0以上",
        ),
        (
            0,
            0,
            0,
            -1,
            "その他所得控除は0以上",
        ),
    ],
)
def test_calculate_taxable_income_rejects_negative_values(
    salary_income_yen,
    basic_deduction_yen,
    social_insurance_deduction_yen,
    other_income_deductions_yen,
    message,
):
    with pytest.raises(
        ValueError,
        match=message,
    ):
        calculate_taxable_income(
            salary_income_yen=salary_income_yen,
            basic_deduction_yen=basic_deduction_yen,
            social_insurance_deduction_yen=(
                social_insurance_deduction_yen
            ),
            other_income_deductions_yen=(
                other_income_deductions_yen
            ),
        )


def _create_income_tax_brackets() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "1999-01-01",
                "1999-01-01",
                "1999-01-01",
                "1999-01-01",
                "2015-01-01",
                "2015-01-01",
                "2015-01-01",
                "2015-01-01",
                "2015-01-01",
                "2015-01-01",
                "2015-01-01",
            ],
            "effective_to": [
                "2006-12-31",
                "2006-12-31",
                "2006-12-31",
                "2006-12-31",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            "bracket_order": [
                1,
                2,
                3,
                4,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
            ],
            "lower_bound_yen": [
                0,
                3_300_000,
                9_000_000,
                18_000_000,
                0,
                1_950_000,
                3_300_000,
                6_950_000,
                9_000_000,
                18_000_000,
                40_000_000,
            ],
            "upper_bound_yen": [
                3_300_000,
                9_000_000,
                18_000_000,
                None,
                1_950_000,
                3_300_000,
                6_950_000,
                9_000_000,
                18_000_000,
                40_000_000,
                None,
            ],
            "marginal_rate": [
                0.10,
                0.20,
                0.30,
                0.37,
                0.05,
                0.10,
                0.20,
                0.23,
                0.33,
                0.40,
                0.45,
            ],
            "quick_deduction_yen": [
                0,
                330_000,
                1_230_000,
                2_490_000,
                0,
                97_500,
                427_500,
                636_000,
                1_536_000,
                2_796_000,
                4_796_000,
            ],
            "source_key": ["test"] * 11,
        }
    )


def test_calculate_base_income_tax_2025():
    rules = _create_income_tax_brackets()

    result = calculate_base_income_tax(
        taxable_income_yen=5_000_000,
        target_date="2025-06-01",
        tax_brackets=rules,
    )

    assert result == 572_500


def test_calculate_base_income_tax_floors_taxable_income():
    rules = _create_income_tax_brackets()

    result = calculate_base_income_tax(
        taxable_income_yen=5_000_999,
        target_date="2025-06-01",
        tax_brackets=rules,
    )

    assert result == 572_500


def test_calculate_base_income_tax_bracket_boundary():
    rules = _create_income_tax_brackets()

    below = calculate_base_income_tax(
        taxable_income_yen=1_949_000,
        target_date="2025-06-01",
        tax_brackets=rules,
    )

    boundary = calculate_base_income_tax(
        taxable_income_yen=1_950_000,
        target_date="2025-06-01",
        tax_brackets=rules,
    )

    assert below == 97_450
    assert boundary == 97_500


def test_calculate_base_income_tax_top_bracket_boundary():
    rules = _create_income_tax_brackets()

    result = calculate_base_income_tax(
        taxable_income_yen=40_000_000,
        target_date="2025-06-01",
        tax_brackets=rules,
    )

    assert result == 13_204_000


def test_calculate_base_income_tax_2000():
    rules = _create_income_tax_brackets()

    result = calculate_base_income_tax(
        taxable_income_yen=5_000_000,
        target_date="2000-06-01",
        tax_brackets=rules,
    )

    assert result == 670_000


def test_calculate_base_income_tax_zero_income():
    rules = _create_income_tax_brackets()

    result = calculate_base_income_tax(
        taxable_income_yen=0,
        target_date="2025-06-01",
        tax_brackets=rules,
    )

    assert result == 0


def test_calculate_base_income_tax_rejects_negative_income():
    rules = _create_income_tax_brackets()

    with pytest.raises(
        ValueError,
        match="課税所得は0以上",
    ):
        calculate_base_income_tax(
            taxable_income_yen=-1,
            target_date="2025-06-01",
            tax_brackets=rules,
        )


def test_calculate_base_income_tax_rejects_missing_period():
    rules = _create_income_tax_brackets()

    with pytest.raises(
        ValueError,
        match="有効な所得税率ルールがありません",
    ):
        calculate_base_income_tax(
            taxable_income_yen=1_000_000,
            target_date="1990-01-01",
            tax_brackets=rules,
        )


def test_calculate_base_income_tax_rejects_unmatched_bracket():
    rules = _create_income_tax_brackets()

    rules = rules.loc[
        ~(
            (rules["effective_from"] == "2015-01-01")
            & (rules["bracket_order"] == 3)
        )
    ].copy()

    with pytest.raises(
        ValueError,
        match="所得税率ルールを一意に取得できません",
    ):
        calculate_base_income_tax(
            taxable_income_yen=5_000_000,
            target_date="2025-06-01",
            tax_brackets=rules,
        )


def _create_income_tax_adjustment_rules() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "policy_id": [
                "special_reduction_1994",
                "special_reduction_1995",
                "special_reduction_1996",
                "special_reduction_1998",
                "proportional_reduction_1999_2005",
                "proportional_reduction_2006",
                "reconstruction_surtax_2013",
                "fixed_reduction_2024",
            ],
            "effective_from": [
                "1994-01-01",
                "1995-01-01",
                "1996-01-01",
                "1998-01-01",
                "1999-01-01",
                "2006-01-01",
                "2013-01-01",
                "2024-01-01",
            ],
            "effective_to": [
                "1994-12-31",
                "1995-12-31",
                "1996-12-31",
                "1998-12-31",
                "2005-12-31",
                "2006-12-31",
                None,
                "2024-12-31",
            ],
            "operation": [
                "subtract_rate",
                "subtract_rate",
                "subtract_rate",
                "subtract_fixed",
                "subtract_rate",
                "subtract_rate",
                "add_rate",
                "subtract_fixed",
            ],
            "base": [
                "income_tax",
                "income_tax",
                "income_tax",
                "income_tax",
                "income_tax",
                "income_tax",
                "post_credit_income_tax",
                "income_tax",
            ],
            "rate": [
                0.20,
                0.15,
                0.15,
                None,
                0.20,
                0.10,
                0.021,
                None,
            ],
            "fixed_taxpayer_yen": [
                None,
                None,
                None,
                38_000,
                None,
                None,
                None,
                30_000,
            ],
            "fixed_dependent_yen": [
                None,
                None,
                None,
                19_000,
                None,
                None,
                None,
                30_000,
            ],
            "cap_yen": [
                2_000_000,
                50_000,
                50_000,
                None,
                250_000,
                125_000,
                None,
                None,
            ],
            "total_income_limit_yen": [
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                18_050_000,
            ],
            "policy_class": [
                "temporary",
                "temporary",
                "temporary",
                "temporary",
                "multi_year_general",
                "multi_year_general",
                "surtax",
                "temporary",
            ],
            "apply_order": [
                100,
                100,
                100,
                100,
                100,
                100,
                200,
                100,
            ],
            "source_key": ["test"] * 8,
        }
    )


def test_calculate_income_tax_after_adjustments_1994():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="1994-06-01",
        adjustment_rules=rules,
    )

    assert result == 80_000


def test_calculate_income_tax_after_adjustments_1995_cap():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=1_000_000,
        total_income_yen=5_000_000,
        target_date="1995-06-01",
        adjustment_rules=rules,
    )

    assert result == 950_000


def test_calculate_income_tax_after_adjustments_1998():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="1998-06-01",
        adjustment_rules=rules,
    )

    assert result == 62_000


def test_calculate_income_tax_after_adjustments_1998_with_dependents():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="1998-06-01",
        adjustment_rules=rules,
        dependent_count=2,
    )

    assert result == 24_000


def test_calculate_income_tax_after_adjustments_1999():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="1999-06-01",
        adjustment_rules=rules,
    )

    assert result == 80_000


def test_calculate_income_tax_after_adjustments_2006():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="2006-06-01",
        adjustment_rules=rules,
    )

    assert result == 90_000


def test_calculate_income_tax_after_adjustments_2007():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="2007-06-01",
        adjustment_rules=rules,
    )

    assert result == 100_000


def test_calculate_income_tax_after_adjustments_2024():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="2024-06-01",
        adjustment_rules=rules,
    )

    assert result == 70_000


def test_calculate_income_tax_after_adjustments_2024_with_dependents():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="2024-06-01",
        adjustment_rules=rules,
        dependent_count=2,
    )

    assert result == 10_000


def test_calculate_income_tax_after_adjustments_2024_income_limit():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=18_050_001,
        target_date="2024-06-01",
        adjustment_rules=rules,
    )

    assert result == 100_000


def test_calculate_income_tax_after_adjustments_floor_at_zero():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=20_000,
        total_income_yen=3_000_000,
        target_date="2024-06-01",
        adjustment_rules=rules,
    )

    assert result == 0


def test_calculate_income_tax_structural_policy_excludes_2024_reduction():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="2024-06-01",
        adjustment_rules=rules,
        policy_mode="structural_policy",
    )

    assert result == 100_000


def test_calculate_income_tax_structural_policy_keeps_1999_reduction():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_income_tax_after_adjustments(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="1999-06-01",
        adjustment_rules=rules,
        policy_mode="structural_policy",
    )

    assert result == 80_000


def test_calculate_reconstruction_special_income_tax():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_reconstruction_special_income_tax(
        income_tax_after_adjustments_yen=176_500,
        target_date="2025-06-01",
        adjustment_rules=rules,
    )

    assert result == 3_706


def test_calculate_reconstruction_special_income_tax_before_2013():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_reconstruction_special_income_tax(
        income_tax_after_adjustments_yen=100_000,
        target_date="2012-06-01",
        adjustment_rules=rules,
    )

    assert result == 0


def test_calculate_total_income_tax_2024():
    rules = _create_income_tax_adjustment_rules()

    result = calculate_total_income_tax(
        base_income_tax_yen=100_000,
        total_income_yen=3_000_000,
        target_date="2024-06-01",
        adjustment_rules=rules,
    )

    assert result == 71_400


def _create_employment_insurance_rates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "2017-04-01",
                "2022-10-01",
                "2023-04-01",
                "2025-04-01",
                "2017-04-01",
            ],
            "effective_to": [
                "2022-09-30",
                "2023-03-31",
                "2025-03-31",
                None,
                None,
            ],
            "business_type": [
                "general",
                "general",
                "general",
                "general",
                "construction",
            ],
            "employee_rate": [
                0.0030,
                0.0050,
                0.0060,
                0.0055,
                0.0040,
            ],
            "source_key": [
                "test",
                "test",
                "test",
                "test",
                "test",
            ],
        }
    )


def test_calculate_employment_insurance():
    rates = _create_employment_insurance_rates()

    result = calculate_employment_insurance(
        wage_yen=300_000,
        target_date="2024-06-01",
        employment_insurance_rates=rates,
    )

    assert result == 1_800


def test_calculate_employment_insurance_2022_rate_change():
    rates = _create_employment_insurance_rates()

    september = calculate_employment_insurance(
        wage_yen=300_000,
        target_date="2022-09-30",
        employment_insurance_rates=rates,
    )

    october = calculate_employment_insurance(
        wage_yen=300_000,
        target_date="2022-10-01",
        employment_insurance_rates=rates,
    )

    assert september == 900
    assert october == 1_500


def test_calculate_employment_insurance_2025_rate_change():
    rates = _create_employment_insurance_rates()

    march = calculate_employment_insurance(
        wage_yen=300_000,
        target_date="2025-03-31",
        employment_insurance_rates=rates,
    )

    april = calculate_employment_insurance(
        wage_yen=300_000,
        target_date="2025-04-01",
        employment_insurance_rates=rates,
    )

    assert march == 1_800
    assert april == 1_650


def test_calculate_employment_insurance_business_type():
    rates = _create_employment_insurance_rates()

    result = calculate_employment_insurance(
        wage_yen=300_000,
        target_date="2020-06-01",
        employment_insurance_rates=rates,
        business_type="construction",
    )

    assert result == 1_200


def test_calculate_employment_insurance_zero_wage():
    rates = _create_employment_insurance_rates()

    result = calculate_employment_insurance(
        wage_yen=0,
        target_date="2024-06-01",
        employment_insurance_rates=rates,
    )

    assert result == 0


def test_calculate_employment_insurance_rejects_negative_wage():
    rates = _create_employment_insurance_rates()

    with pytest.raises(
        ValueError,
        match="対象賃金は0以上",
    ):
        calculate_employment_insurance(
            wage_yen=-1,
            target_date="2024-06-01",
            employment_insurance_rates=rates,
        )


def test_calculate_annual_employment_insurance_2025():
    rates = _create_employment_insurance_rates()

    monthly_wages = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
            "cash_earnings_yen": [
                300_000,
            ] * 12,
        }
    )

    result = calculate_annual_employment_insurance(
        monthly_wages=monthly_wages,
        employment_insurance_rates=rates,
    )

    expected = (
        300_000 * 0.0060 * 3
        + 300_000 * 0.0055 * 9
    )

    assert result == expected


def test_calculate_annual_employment_insurance_rejects_missing_columns():
    rates = _create_employment_insurance_rates()

    monthly_wages = pd.DataFrame(
        {
            "date": ["2025-01-01"],
        }
    )

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        calculate_annual_employment_insurance(
            monthly_wages=monthly_wages,
            employment_insurance_rates=rates,
        )


def test_calculate_annual_employment_insurance_rejects_empty_data():
    rates = _create_employment_insurance_rates()

    monthly_wages = pd.DataFrame(
        columns=[
            "date",
            "cash_earnings_yen",
        ]
    )

    with pytest.raises(
        ValueError,
        match="月次賃金データが空です",
    ):
        calculate_annual_employment_insurance(
            monthly_wages=monthly_wages,
            employment_insurance_rates=rates,
        )


def _create_standard_monthly_rules() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "2000-10-01",
                "2000-10-01",
                "2000-10-01",
                "2016-10-01",
                "2016-10-01",
                "2016-10-01",
                "2020-09-01",
                "2020-09-01",
                "2020-09-01",
            ],
            "effective_to": [
                "2016-09-30",
                "2016-09-30",
                "2016-09-30",
                "2020-08-31",
                "2020-08-31",
                "2020-08-31",
                None,
                None,
                None,
            ],
            "grade": [
                1,
                2,
                3,
                1,
                2,
                3,
                30,
                31,
                32,
            ],
            "standard_monthly_yen": [
                98_000,
                104_000,
                110_000,
                88_000,
                98_000,
                104_000,
                590_000,
                620_000,
                650_000,
            ],
            "remuneration_lower_yen": [
                None,
                101_000,
                107_000,
                None,
                93_000,
                101_000,
                575_000,
                605_000,
                635_000,
            ],
            "remuneration_upper_yen": [
                101_000,
                107_000,
                None,
                93_000,
                101_000,
                None,
                605_000,
                635_000,
                None,
            ],
        }
    )


def test_calculate_standard_monthly_remuneration():
    rules = _create_standard_monthly_rules()

    result = calculate_standard_monthly_remuneration(
        remuneration_yen=97_000,
        target_date="2018-06-01",
        standard_monthly_rules=rules,
    )

    assert result == 98_000


def test_calculate_standard_monthly_remuneration_2016_boundary():
    rules = _create_standard_monthly_rules()

    below = calculate_standard_monthly_remuneration(
        remuneration_yen=92_999,
        target_date="2018-06-01",
        standard_monthly_rules=rules,
    )

    boundary = calculate_standard_monthly_remuneration(
        remuneration_yen=93_000,
        target_date="2018-06-01",
        standard_monthly_rules=rules,
    )

    assert below == 88_000
    assert boundary == 98_000


def test_calculate_standard_monthly_remuneration_second_boundary():
    rules = _create_standard_monthly_rules()

    below = calculate_standard_monthly_remuneration(
        remuneration_yen=100_999,
        target_date="2018-06-01",
        standard_monthly_rules=rules,
    )

    boundary = calculate_standard_monthly_remuneration(
        remuneration_yen=101_000,
        target_date="2018-06-01",
        standard_monthly_rules=rules,
    )

    assert below == 98_000
    assert boundary == 104_000


def test_calculate_standard_monthly_remuneration_below_bottom():
    rules = _create_standard_monthly_rules()

    result = calculate_standard_monthly_remuneration(
        remuneration_yen=50_000,
        target_date="2018-06-01",
        standard_monthly_rules=rules,
    )

    assert result == 88_000


def test_calculate_standard_monthly_remuneration_above_top():
    rules = _create_standard_monthly_rules()

    result = calculate_standard_monthly_remuneration(
        remuneration_yen=800_000,
        target_date="2025-06-01",
        standard_monthly_rules=rules,
    )

    assert result == 650_000


def test_calculate_standard_monthly_remuneration_2020_top_boundary():
    rules = _create_standard_monthly_rules()

    below = calculate_standard_monthly_remuneration(
        remuneration_yen=634_999,
        target_date="2025-06-01",
        standard_monthly_rules=rules,
    )

    boundary = calculate_standard_monthly_remuneration(
        remuneration_yen=635_000,
        target_date="2025-06-01",
        standard_monthly_rules=rules,
    )

    assert below == 620_000
    assert boundary == 650_000


def test_standard_monthly_remuneration_changes_by_period():
    rules = _create_standard_monthly_rules()

    before = calculate_standard_monthly_remuneration(
        remuneration_yen=90_000,
        target_date="2015-06-01",
        standard_monthly_rules=rules,
    )

    after = calculate_standard_monthly_remuneration(
        remuneration_yen=90_000,
        target_date="2018-06-01",
        standard_monthly_rules=rules,
    )

    assert before == 98_000
    assert after == 88_000


def test_calculate_standard_monthly_remuneration_rejects_negative():
    rules = _create_standard_monthly_rules()

    with pytest.raises(
        ValueError,
        match="報酬月額は0以上",
    ):
        calculate_standard_monthly_remuneration(
            remuneration_yen=-1,
            target_date="2025-06-01",
            standard_monthly_rules=rules,
        )


def test_calculate_standard_monthly_remuneration_rejects_missing_period():
    rules = _create_standard_monthly_rules()

    with pytest.raises(
        ValueError,
        match="有効な標準報酬月額ルールがありません",
    ):
        calculate_standard_monthly_remuneration(
            remuneration_yen=300_000,
            target_date="1990-01-01",
            standard_monthly_rules=rules,
        )


def _create_pension_rates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "1990-01-01",
                "1990-01-01",
                "1994-01-01",
                "2015-09-01",
                "2016-09-01",
                "2017-09-01",
            ],
            "effective_to": [
                "1990-12-31",
                "1990-12-31",
                "1994-10-31",
                "2016-08-31",
                "2017-08-31",
                None,
            ],
            "insured_category": [
                "general_male",
                "general_female",
                "general",
                "general",
                "general",
                "general",
            ],
            "regular_total_rate": [
                0.1430,
                0.1380,
                0.1450,
                0.17828,
                0.18182,
                0.18300,
            ],
            "bonus_total_rate": [
                0,
                0,
                0,
                0.17828,
                0.18182,
                0.18300,
            ],
            "employee_share": [
                0.5,
                0.5,
                0.5,
                0.5,
                0.5,
                0.5,
            ],
            "source_key": [
                "test",
                "test",
                "test",
                "test",
                "test",
                "test",
            ],
        }
    )


def _create_pension_standard_monthly_rules() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "1989-12-01",
                "1989-12-01",
                "1989-12-01",
                "2016-10-01",
                "2016-10-01",
                "2016-10-01",
                "2020-09-01",
                "2020-09-01",
                "2020-09-01",
            ],
            "effective_to": [
                "1994-10-31",
                "1994-10-31",
                "1994-10-31",
                "2020-08-31",
                "2020-08-31",
                "2020-08-31",
                None,
                None,
                None,
            ],
            "grade": [
                1,
                2,
                3,
                1,
                2,
                3,
                1,
                2,
                3,
            ],
            "standard_monthly_yen": [
                200_000,
                220_000,
                240_000,
                200_000,
                220_000,
                240_000,
                200_000,
                220_000,
                240_000,
            ],
            "remuneration_lower_yen": [
                None,
                210_000,
                230_000,
                None,
                210_000,
                230_000,
                None,
                210_000,
                230_000,
            ],
            "remuneration_upper_yen": [
                210_000,
                230_000,
                None,
                210_000,
                230_000,
                None,
                210_000,
                230_000,
                None,
            ],
        }
    )


def test_calculate_monthly_pension_contribution():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    rates = _create_pension_rates()

    result = calculate_monthly_pension_contribution(
        remuneration_yen=205_000,
        target_date="2025-06-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
    )

    assert result == 18_300


def test_monthly_pension_uses_standard_monthly_remuneration():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    rates = _create_pension_rates()

    result = calculate_monthly_pension_contribution(
        remuneration_yen=209_999,
        target_date="2025-06-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
    )

    expected = (
        200_000
        * 0.183
        * 0.5
    )

    assert result == expected


def test_monthly_pension_standard_monthly_boundary():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    rates = _create_pension_rates()

    below = calculate_monthly_pension_contribution(
        remuneration_yen=209_999,
        target_date="2025-06-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
    )

    boundary = calculate_monthly_pension_contribution(
        remuneration_yen=210_000,
        target_date="2025-06-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
    )

    assert below == 18_300
    assert boundary == 20_130


def test_monthly_pension_1990_sex_difference():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    rates = _create_pension_rates()

    male = calculate_monthly_pension_contribution(
        remuneration_yen=205_000,
        target_date="1990-06-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
        sex="male",
    )

    female = calculate_monthly_pension_contribution(
        remuneration_yen=205_000,
        target_date="1990-06-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
        sex="female",
    )

    assert male == 14_300
    assert female == 13_800


def test_pension_rate_uses_general_after_sex_rates_end():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    rates = _create_pension_rates()

    male = calculate_monthly_pension_contribution(
        remuneration_yen=205_000,
        target_date="1994-06-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
        sex="male",
    )

    female = calculate_monthly_pension_contribution(
        remuneration_yen=205_000,
        target_date="1994-06-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
        sex="female",
    )

    assert male == female
    assert male == 14_500


def test_monthly_pension_2017_rate_change():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    rates = _create_pension_rates()

    august = calculate_monthly_pension_contribution(
        remuneration_yen=205_000,
        target_date="2017-08-31",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
    )

    september = calculate_monthly_pension_contribution(
        remuneration_yen=205_000,
        target_date="2017-09-01",
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
    )

    assert august == 18_182
    assert september == 18_300


def test_calculate_annual_regular_pension_contribution():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    rates = _create_pension_rates()

    monthly = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
            "regular_pay_yen": [
                205_000,
            ] * 12,
        }
    )

    result = (
        calculate_annual_regular_pension_contribution(
            monthly_remuneration=monthly,
            standard_monthly_rules=standard_rules,
            pension_rates=rates,
        )
    )

    assert result == 18_300 * 12
    assert result == 219_600


def test_annual_regular_pension_handles_rate_change():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    rates = _create_pension_rates()

    monthly = pd.DataFrame(
        {
            "date": pd.date_range(
                "2017-01-01",
                periods=12,
                freq="MS",
            ),
            "regular_pay_yen": [
                205_000,
            ] * 12,
        }
    )

    result = (
        calculate_annual_regular_pension_contribution(
            monthly_remuneration=monthly,
            standard_monthly_rules=standard_rules,
            pension_rates=rates,
        )
    )

    expected = (
        18_182 * 8
        + 18_300 * 4
    )

    assert result == expected


def test_select_pension_rate_rejects_invalid_sex():
    rates = _create_pension_rates()

    with pytest.raises(
        ValueError,
        match="sex は male または female",
    ):
        _select_pension_rate_rule(
            target_date="1990-06-01",
            pension_rates=rates,
            sex="other",
        )


def _create_pension_bonus_rates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "1994-11-01",
                "1995-04-01",
                "2003-04-01",
                "2017-09-01",
            ],
            "effective_to": [
                "1995-03-31",
                "2003-03-31",
                "2017-08-31",
                None,
            ],
            "insured_category": [
                "general",
                "general",
                "general",
                "general",
            ],
            "regular_total_rate": [
                0.1650,
                0.1735,
                0.1358,
                0.1830,
            ],
            "bonus_total_rate": [
                0.0,
                0.0100,
                0.1358,
                0.1830,
            ],
            "employee_share": [
                0.5,
                0.5,
                0.5,
                0.5,
            ],
            "source_key": [
                "test",
                "test",
                "test",
                "test",
            ],
        }
    )


def _create_pension_bonus_rules() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scheme": [
                "pension",
                "pension",
            ],
            "effective_from": [
                "1995-04-01",
                "2003-04-01",
            ],
            "effective_to": [
                "2003-03-31",
                None,
            ],
            "cap_type": [
                "none",
                "per_month",
            ],
            "cap_yen": [
                None,
                1_500_000,
            ],
            "rounding_unit_yen": [
                100,
                1_000,
            ],
            "source_key": [
                "test",
                "test",
            ],
        }
    )


def test_calculate_pension_bonus_base_special_premium():
    rules = _create_pension_bonus_rules()

    result = calculate_pension_bonus_base(
        bonus_yen=500_099,
        target_date="2000-06-01",
        bonus_rules=rules,
    )

    assert result == 500_000


def test_calculate_pension_bonus_base_after_2003():
    rules = _create_pension_bonus_rules()

    result = calculate_pension_bonus_base(
        bonus_yen=500_999,
        target_date="2025-06-01",
        bonus_rules=rules,
    )

    assert result == 500_000


def test_calculate_pension_bonus_base_cap():
    rules = _create_pension_bonus_rules()

    result = calculate_pension_bonus_base(
        bonus_yen=2_000_000,
        target_date="2025-06-01",
        bonus_rules=rules,
    )

    assert result == 1_500_000


def test_calculate_pension_bonus_contribution_before_1995():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    result = calculate_pension_bonus_contribution(
        bonus_yen=500_000,
        target_date="1995-03-01",
        pension_rates=rates,
        bonus_rules=rules,
    )

    assert result == 0


def test_calculate_pension_bonus_contribution_special_premium():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    result = calculate_pension_bonus_contribution(
        bonus_yen=500_099,
        target_date="2000-06-01",
        pension_rates=rates,
        bonus_rules=rules,
    )

    assert result == 2_500


def test_calculate_pension_bonus_contribution_after_2003():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    result = calculate_pension_bonus_contribution(
        bonus_yen=500_999,
        target_date="2003-06-01",
        pension_rates=rates,
        bonus_rules=rules,
    )

    assert result == 33_950


def test_calculate_pension_bonus_contribution_current():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    result = calculate_pension_bonus_contribution(
        bonus_yen=500_000,
        target_date="2025-06-01",
        pension_rates=rates,
        bonus_rules=rules,
    )

    assert result == 45_750


def test_calculate_pension_bonus_contribution_uses_cap():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    result = calculate_pension_bonus_contribution(
        bonus_yen=2_000_000,
        target_date="2025-06-01",
        pension_rates=rates,
        bonus_rules=rules,
    )

    assert result == 137_250


def test_calculate_annual_pension_bonus_contribution():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    bonuses = pd.DataFrame(
        {
            "date": [
                "2025-06-01",
                "2025-12-01",
            ],
            "bonus_yen": [
                500_000,
                500_000,
            ],
        }
    )

    result = (
        calculate_annual_pension_bonus_contribution(
            bonus_payments=bonuses,
            pension_rates=rates,
            bonus_rules=rules,
        )
    )

    assert result == 45_750 * 2
    assert result == 91_500


def test_annual_pension_bonus_groups_same_month_before_cap():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    bonuses = pd.DataFrame(
        {
            "date": [
                "2025-06-01",
                "2025-06-20",
            ],
            "bonus_yen": [
                1_000_000,
                800_000,
            ],
        }
    )

    result = (
        calculate_annual_pension_bonus_contribution(
            bonus_payments=bonuses,
            pension_rates=rates,
            bonus_rules=rules,
        )
    )

    expected = (
        1_500_000
        * 0.183
        * 0.5
    )

    assert result == 137_250
    assert result == expected


def test_annual_pension_bonus_accepts_empty_data():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    bonuses = pd.DataFrame(
        columns=[
            "date",
            "bonus_yen",
        ]
    )

    result = (
        calculate_annual_pension_bonus_contribution(
            bonus_payments=bonuses,
            pension_rates=rates,
            bonus_rules=rules,
        )
    )

    assert result == 0


def test_annual_pension_bonus_before_total_remuneration():
    rates = _create_pension_bonus_rates()
    rules = _create_pension_bonus_rules()

    bonuses = pd.DataFrame(
        {
            "date": [
                "2000-06-01",
                "2000-12-01",
            ],
            "bonus_yen": [
                500_099,
                500_099,
            ],
        }
    )

    result = (
        calculate_annual_pension_bonus_contribution(
            bonus_payments=bonuses,
            pension_rates=rates,
            bonus_rules=rules,
        )
    )

    assert result == 5_000


def test_create_semiannual_bonus_payments():
    result = create_semiannual_bonus_payments(
        year=2025,
        annual_bonus_yen=1_000_000,
    )

    assert len(result) == 2

    assert result["bonus_yen"].tolist() == [
        500_000,
        500_000,
    ]

    assert result["date"].tolist() == [
        pd.Timestamp("2025-06-01"),
        pd.Timestamp("2025-12-01"),
    ]


def test_create_semiannual_bonus_payments_preserves_total():
    result = create_semiannual_bonus_payments(
        year=2025,
        annual_bonus_yen=1_000_001,
    )

    assert result["bonus_yen"].sum() == 1_000_001


def test_calculate_annual_pension_contribution():
    standard_rules = (
        _create_pension_standard_monthly_rules()
    )

    pension_rates = _create_pension_rates()
    bonus_rates = _create_pension_bonus_rates()

    rates = pd.concat(
        [
            pension_rates,
            bonus_rates,
        ],
        ignore_index=True,
    ).drop_duplicates()

    bonus_rules = _create_pension_bonus_rules()

    monthly = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
            "regular_pay_yen": [
                205_000,
            ] * 12,
        }
    )

    bonuses = pd.DataFrame(
        {
            "date": [
                "2025-06-01",
                "2025-12-01",
            ],
            "bonus_yen": [
                500_000,
                500_000,
            ],
        }
    )

    result = calculate_annual_pension_contribution(
        monthly_remuneration=monthly,
        bonus_payments=bonuses,
        standard_monthly_rules=standard_rules,
        pension_rates=rates,
        bonus_rules=bonus_rules,
    )

    assert result[
        "regular_pension_yen"
    ] == 219_600

    assert result[
        "bonus_pension_yen"
    ] == 91_500

    assert result[
        "total_pension_yen"
    ] == 311_100


def _create_health_insurance_rates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "1990-01-01",
                "1992-04-01",
                "1997-09-01",
                "2003-04-01",
                "2010-03-01",
                "2011-03-01",
                "2012-03-01",
            ],
            "effective_to": [
                "1992-03-31",
                "1997-08-31",
                "2003-03-31",
                "2010-02-28",
                "2011-02-28",
                "2012-02-29",
                None,
            ],
            "regular_total_rate": [
                0.0840,
                0.0820,
                0.0850,
                0.0820,
                0.0934,
                0.0950,
                0.1000,
            ],
            "bonus_employee_rate": [
                0.003,
                0.003,
                0.003,
                None,
                None,
                None,
                None,
            ],
            "employee_share": [
                0.5,
                0.5,
                0.5,
                0.5,
                0.5,
                0.5,
                0.5,
            ],
            "source_key": [
                "test",
                "test",
                "test",
                "test",
                "test",
                "test",
                "test",
            ],
        }
    )


def _create_health_standard_monthly_rules() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "1984-10-01",
                "1984-10-01",
                "1984-10-01",
                "1992-10-01",
                "1992-10-01",
                "1992-10-01",
                "2007-04-01",
                "2007-04-01",
                "2007-04-01",
            ],
            "effective_to": [
                "1992-09-30",
                "1992-09-30",
                "1992-09-30",
                "2007-03-31",
                "2007-03-31",
                "2007-03-31",
                None,
                None,
                None,
            ],
            "grade": [
                1,
                2,
                3,
                1,
                2,
                3,
                1,
                2,
                3,
            ],
            "standard_monthly_yen": [
                200_000,
                220_000,
                240_000,
                200_000,
                220_000,
                240_000,
                200_000,
                220_000,
                240_000,
            ],
            "remuneration_lower_yen": [
                None,
                210_000,
                230_000,
                None,
                210_000,
                230_000,
                None,
                210_000,
                230_000,
            ],
            "remuneration_upper_yen": [
                210_000,
                230_000,
                None,
                210_000,
                230_000,
                None,
                210_000,
                230_000,
                None,
            ],
        }
    )


def test_calculate_monthly_health_insurance_contribution():
    standard_rules = (
        _create_health_standard_monthly_rules()
    )
    rates = _create_health_insurance_rates()

    result = (
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=205_000,
            target_date="2025-06-01",
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    assert result == 10_000


def test_monthly_health_insurance_1990():
    standard_rules = (
        _create_health_standard_monthly_rules()
    )
    rates = _create_health_insurance_rates()

    result = (
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=205_000,
            target_date="1990-06-01",
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    assert result == 8_400


def test_monthly_health_insurance_1997_rate_change():
    standard_rules = (
        _create_health_standard_monthly_rules()
    )
    rates = _create_health_insurance_rates()

    august = (
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=205_000,
            target_date="1997-08-31",
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    september = (
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=205_000,
            target_date="1997-09-01",
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    assert august == 8_200
    assert september == 8_500


def test_monthly_health_insurance_2010_rate_change():
    standard_rules = (
        _create_health_standard_monthly_rules()
    )
    rates = _create_health_insurance_rates()

    february = (
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=205_000,
            target_date="2010-02-28",
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    march = (
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=205_000,
            target_date="2010-03-01",
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    assert february == 8_200
    assert march == 9_340


def test_monthly_health_insurance_uses_standard_remuneration():
    standard_rules = (
        _create_health_standard_monthly_rules()
    )
    rates = _create_health_insurance_rates()

    below = (
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=209_999,
            target_date="2025-06-01",
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    boundary = (
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=210_000,
            target_date="2025-06-01",
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    assert below == 10_000
    assert boundary == 11_000


def test_calculate_annual_regular_health_insurance_contribution():
    standard_rules = (
        _create_health_standard_monthly_rules()
    )
    rates = _create_health_insurance_rates()

    monthly = pd.DataFrame(
        {
            "date": pd.date_range(
                "2025-01-01",
                periods=12,
                freq="MS",
            ),
            "regular_pay_yen": [
                205_000,
            ] * 12,
        }
    )

    result = (
        calculate_annual_regular_health_insurance_contribution(
            monthly_remuneration=monthly,
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    assert result == 120_000


def test_annual_health_insurance_handles_rate_change():
    standard_rules = (
        _create_health_standard_monthly_rules()
    )
    rates = _create_health_insurance_rates()

    monthly = pd.DataFrame(
        {
            "date": pd.date_range(
                "1997-01-01",
                periods=12,
                freq="MS",
            ),
            "regular_pay_yen": [
                205_000,
            ] * 12,
        }
    )

    result = (
        calculate_annual_regular_health_insurance_contribution(
            monthly_remuneration=monthly,
            standard_monthly_rules=standard_rules,
            health_insurance_rates=rates,
        )
    )

    expected = (
        8_200 * 8
        + 8_500 * 4
    )

    assert result == expected
    assert result == 99_600


def _create_health_bonus_rules() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scheme": [
                "health",
                "health",
                "health",
                "health",
            ],
            "effective_from": [
                "1990-01-01",
                "2003-04-01",
                "2007-04-01",
                "2016-04-01",
            ],
            "effective_to": [
                "2003-03-31",
                "2007-03-31",
                "2016-03-31",
                None,
            ],
            "cap_type": [
                "none",
                "per_payment",
                "fiscal_year",
                "fiscal_year",
            ],
            "cap_yen": [
                None,
                2_000_000,
                5_400_000,
                5_730_000,
            ],
            "rounding_unit_yen": [
                100,
                1_000,
                1_000,
                1_000,
            ],
            "source_key": [
                "test",
                "test",
                "test",
                "test",
            ],
        }
    )


def test_health_bonus_contribution_before_total_remuneration():
    rates = _create_health_insurance_rates()
    rules = _create_health_bonus_rules()

    result = calculate_health_bonus_contribution(
        bonus_yen=500_099,
        target_date="1990-06-01",
        health_insurance_rates=rates,
        bonus_rules=rules,
    )

    assert result == 1_500


def test_health_bonus_contribution_after_2003():
    rates = _create_health_insurance_rates()
    rules = _create_health_bonus_rules()

    result = calculate_health_bonus_contribution(
        bonus_yen=500_999,
        target_date="2003-06-01",
        health_insurance_rates=rates,
        bonus_rules=rules,
    )

    assert result == 20_500


def test_health_bonus_2003_per_payment_cap():
    rates = _create_health_insurance_rates()
    rules = _create_health_bonus_rules()

    result = calculate_health_bonus_contribution(
        bonus_yen=2_500_000,
        target_date="2005-06-01",
        health_insurance_rates=rates,
        bonus_rules=rules,
    )

    assert result == 82_000


def test_annual_health_bonus_uses_5400000_cap():
    rates = _create_health_insurance_rates()
    rules = _create_health_bonus_rules()

    bonuses = pd.DataFrame(
        {
            "date": [
                "2015-06-01",
                "2015-12-01",
            ],
            "bonus_yen": [
                3_000_000,
                3_000_000,
            ],
        }
    )

    result = calculate_annual_health_bonus_contribution(
        bonus_payments=bonuses,
        health_insurance_rates=rates,
        bonus_rules=rules,
    )

    assert result == 270_000


def test_annual_health_bonus_uses_5730000_cap():
    rates = _create_health_insurance_rates()
    rules = _create_health_bonus_rules()

    bonuses = pd.DataFrame(
        {
            "date": [
                "2025-06-01",
                "2025-12-01",
            ],
            "bonus_yen": [
                3_000_000,
                3_000_000,
            ],
        }
    )

    result = calculate_annual_health_bonus_contribution(
        bonus_payments=bonuses,
        health_insurance_rates=rates,
        bonus_rules=rules,
    )

    assert result == 286_500


def test_health_bonus_cap_resets_in_april():
    rates = _create_health_insurance_rates()
    rules = _create_health_bonus_rules()

    bonuses = pd.DataFrame(
        {
            "date": [
                "2025-03-01",
                "2025-04-01",
            ],
            "bonus_yen": [
                4_000_000,
                4_000_000,
            ],
        }
    )

    result = calculate_annual_health_bonus_contribution(
        bonus_payments=bonuses,
        health_insurance_rates=rates,
        bonus_rules=rules,
    )

    assert result == 400_000


def test_get_fiscal_year():
    assert _get_fiscal_year("2025-03-31") == 2024
    assert _get_fiscal_year("2025-04-01") == 2025
