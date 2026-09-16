import pandas as pd
import pytest

from real_wage_dashboard.take_home_analysis import (
    _floor_to_thousand_yen,
    _select_assessment_year_rules,
    _select_effective_rules,
    _select_single_assessment_year_rule,
    _select_single_effective_rule,
    calculate_basic_deduction,
    calculate_salary_income,
    calculate_salary_income_deduction,
    calculate_taxable_income,
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
