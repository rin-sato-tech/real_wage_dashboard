import pandas as pd
import pytest

from real_wage_dashboard.take_home_analysis import (
    _select_assessment_year_rules,
    _select_effective_rules,
    _select_single_assessment_year_rule,
    _select_single_effective_rule,
    calculate_salary_income,
    calculate_salary_income_deduction,
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
