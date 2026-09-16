import pandas as pd
import pytest

from real_wage_dashboard.take_home_analysis import (
    _select_assessment_year_rules,
    _select_effective_rules,
    _select_single_assessment_year_rule,
    _select_single_effective_rule,
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
