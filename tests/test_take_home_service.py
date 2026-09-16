import pytest

import pandas as pd

from real_wage_dashboard.take_home_service import (
    _create_standard_monthly_brackets,
    _validate_health_standard_monthly_history,
    load_health_standard_monthly_history,
    load_income_tax_brackets,
    load_long_term_care_insurance_rates,
    load_pension_standard_monthly_history,
    load_take_home_rule_tables,
)


def test_load_income_tax_brackets(tmp_path):
    path = tmp_path / "income_tax_brackets.csv"

    pd.DataFrame(
        {
            "effective_from": ["2007-01-01"],
            "effective_to": [""],
            "bracket_order": [1],
            "lower_bound_yen": [0],
            "upper_bound_yen": [1_950_000],
            "marginal_rate": [0.05],
            "quick_deduction_yen": [0],
            "source_key": ["test"],
        }
    ).to_csv(path, index=False)

    result = load_income_tax_brackets(path)

    assert len(result) == 1
    assert result.loc[0, "marginal_rate"] == 0.05
    assert pd.api.types.is_datetime64_any_dtype(
        result["effective_from"]
    )


def test_load_income_tax_brackets_rejects_missing_columns(
    tmp_path,
):
    path = tmp_path / "income_tax_brackets.csv"

    pd.DataFrame(
        {
            "effective_from": ["2007-01-01"],
        }
    ).to_csv(path, index=False)

    with pytest.raises(
        ValueError,
        match="必要な列がありません",
    ):
        load_income_tax_brackets(path)


def test_create_standard_monthly_brackets():
    result = _create_standard_monthly_brackets(
        standard_monthly_values=[
            88_000,
            98_000,
            104_000,
        ],
        effective_from=pd.Timestamp(
            "2016-10-01"
        ),
        effective_to=pd.Timestamp(
            "2020-08-31"
        ),
    )

    assert result["grade"].tolist() == [
        1,
        2,
        3,
    ]

    assert result[
        "standard_monthly_yen"
    ].tolist() == [
        88_000,
        98_000,
        104_000,
    ]

    assert pd.isna(
        result.loc[
            0,
            "remuneration_lower_yen",
        ]
    )

    assert (
        result.loc[
            0,
            "remuneration_upper_yen",
        ]
        == 93_000
    )

    assert (
        result.loc[
            1,
            "remuneration_lower_yen",
        ]
        == 93_000
    )

    assert (
        result.loc[
            1,
            "remuneration_upper_yen",
        ]
        == 101_000
    )


def test_create_standard_monthly_brackets_top_grade():
    result = _create_standard_monthly_brackets(
        standard_monthly_values=[
            590_000,
            620_000,
            650_000,
        ],
        effective_from=pd.Timestamp(
            "2020-09-01"
        ),
        effective_to=pd.NaT,
    )

    assert (
        result.loc[
            1,
            "remuneration_lower_yen",
        ]
        == 605_000
    )

    assert (
        result.loc[
            1,
            "remuneration_upper_yen",
        ]
        == 635_000
    )

    assert (
        result.loc[
            2,
            "remuneration_lower_yen",
        ]
        == 635_000
    )

    assert pd.isna(
        result.loc[
            2,
            "remuneration_upper_yen",
        ]
    )


def test_create_standard_monthly_brackets_rejects_duplicates():
    with pytest.raises(
        ValueError,
        match="標準報酬月額に重複があります",
    ):
        _create_standard_monthly_brackets(
            standard_monthly_values=[
                98_000,
                98_000,
            ],
            effective_from=pd.Timestamp(
                "2000-10-01"
            ),
            effective_to=pd.Timestamp(
                "2016-09-30"
            ),
        )


def test_load_pension_standard_monthly_history(
    tmp_path,
):
    path = (
        tmp_path
        / "pension_standard_monthly_history.xlsx"
    )

    raw = pd.DataFrame(
        index=range(10),
        columns=range(18),
    )

    raw.iloc[6, 10] = 92
    raw.iloc[7, 10] = 98
    raw.iloc[8, 10] = 104

    raw.iloc[6, 11] = 92
    raw.iloc[7, 11] = 98
    raw.iloc[8, 11] = 104

    raw.iloc[6, 12] = 98
    raw.iloc[7, 12] = 104
    raw.iloc[8, 12] = 110

    raw.iloc[6, 13] = 88
    raw.iloc[7, 13] = 98
    raw.iloc[8, 13] = 104

    raw.iloc[6, 14] = 88
    raw.iloc[7, 14] = 98
    raw.iloc[8, 14] = 104

    with pd.ExcelWriter(path) as writer:
        raw.to_excel(
            writer,
            sheet_name=(
                "厚生年金保険　標準報酬月額等級の変遷"
            ),
            header=False,
            index=False,
        )

    result = (
        load_pension_standard_monthly_history(
            path
        )
    )

    assert set(
        result["effective_from"]
    ) == {
        pd.Timestamp("1989-12-01"),
        pd.Timestamp("1994-11-01"),
        pd.Timestamp("2000-10-01"),
        pd.Timestamp("2016-10-01"),
        pd.Timestamp("2020-09-01"),
    }


def test_load_pension_standard_monthly_history_2016_boundary(
    tmp_path,
):
    path = (
        tmp_path
        / "pension_standard_monthly_history.xlsx"
    )

    raw = pd.DataFrame(
        index=range(10),
        columns=range(18),
    )

    for column in [
        10,
        11,
        12,
        13,
        14,
    ]:
        raw.iloc[6, column] = 88
        raw.iloc[7, column] = 98
        raw.iloc[8, column] = 104

    with pd.ExcelWriter(path) as writer:
        raw.to_excel(
            writer,
            sheet_name=(
                "厚生年金保険　標準報酬月額等級の変遷"
            ),
            header=False,
            index=False,
        )

    result = (
        load_pension_standard_monthly_history(
            path
        )
    )

    period = result.loc[
        result["effective_from"]
        == pd.Timestamp("2016-10-01")
    ].reset_index(drop=True)

    assert (
        period.loc[
            0,
            "standard_monthly_yen",
        ]
        == 88_000
    )

    assert (
        period.loc[
            0,
            "remuneration_upper_yen",
        ]
        == 93_000
    )


def _create_health_standard_monthly_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "effective_from": [
                "2007-04-01",
                "2007-04-01",
                "2007-04-01",
            ],
            "effective_to": [
                "2016-03-31",
                "2016-03-31",
                "2016-03-31",
            ],
            "grade": [
                1,
                2,
                3,
            ],
            "standard_monthly_yen": [
                58_000,
                68_000,
                78_000,
            ],
            "remuneration_lower_yen": [
                None,
                63_000,
                73_000,
            ],
            "remuneration_upper_yen": [
                63_000,
                73_000,
                None,
            ],
            "source_key": [
                "test",
                "test",
                "test",
            ],
            "notes": [
                "test",
                "test",
                "test",
            ],
        }
    )


def test_validate_health_standard_monthly_history():
    df = _create_health_standard_monthly_data()

    _validate_health_standard_monthly_history(
        df
    )


def test_validate_health_standard_monthly_history_rejects_gap():
    df = _create_health_standard_monthly_data()

    df.loc[
        1,
        "remuneration_lower_yen",
    ] = 64_000

    with pytest.raises(
        ValueError,
        match="等級境界が連続していません",
    ):
        _validate_health_standard_monthly_history(
            df
        )


def test_validate_health_standard_monthly_history_rejects_duplicate_grade():
    df = _create_health_standard_monthly_data()

    df.loc[
        1,
        "grade",
    ] = 1

    with pytest.raises(
        ValueError,
        match="等級が重複しています",
    ):
        _validate_health_standard_monthly_history(
            df
        )


def test_load_health_standard_monthly_history(
    tmp_path,
):
    path = (
        tmp_path
        / "health_standard_monthly_history.csv"
    )

    df = _create_health_standard_monthly_data()

    df.to_csv(
        path,
        index=False,
    )

    result = (
        load_health_standard_monthly_history(
            path
        )
    )

    assert len(result) == 3

    assert (
        result.loc[
            0,
            "standard_monthly_yen",
        ]
        == 58_000
    )

    assert (
        result.loc[
            1,
            "remuneration_lower_yen",
        ]
        == 63_000
    )

    assert pd.api.types.is_datetime64_any_dtype(
        result["effective_from"]
    )


def test_real_health_standard_monthly_history():
    result = (
        load_health_standard_monthly_history()
    )

    summary = (
        result.groupby(
            "effective_from"
        )
        .agg(
            grades=(
                "grade",
                "count",
            ),
            minimum=(
                "standard_monthly_yen",
                "min",
            ),
            maximum=(
                "standard_monthly_yen",
                "max",
            ),
        )
    )

    expected = {
        pd.Timestamp("1984-10-01"): (
            39,
            68_000,
            710_000,
        ),
        pd.Timestamp("1992-10-01"): (
            42,
            80_000,
            980_000,
        ),
        pd.Timestamp("1994-11-01"): (
            40,
            92_000,
            980_000,
        ),
        pd.Timestamp("2001-01-01"): (
            39,
            98_000,
            980_000,
        ),
        pd.Timestamp("2007-04-01"): (
            47,
            58_000,
            1_210_000,
        ),
        pd.Timestamp("2016-04-01"): (
            50,
            58_000,
            1_390_000,
        ),
    }

    for effective_from, (
        grades,
        minimum,
        maximum,
    ) in expected.items():
        row = summary.loc[
            effective_from
        ]

        assert row["grades"] == grades
        assert row["minimum"] == minimum
        assert row["maximum"] == maximum

    period_2007 = result.loc[
        result["effective_from"]
        == pd.Timestamp("2007-04-01")
    ]

    grade_44_2007 = period_2007.loc[
        period_2007["grade"] == 44
    ].iloc[0]

    assert (
        grade_44_2007["standard_monthly_yen"]
        == 1_030_000
    )
    assert (
        grade_44_2007["remuneration_lower_yen"]
        == 1_005_000
    )
    assert (
        grade_44_2007["remuneration_upper_yen"]
        == 1_055_000
    )

    grade_47_2007 = period_2007.loc[
        period_2007["grade"] == 47
    ].iloc[0]

    assert (
        grade_47_2007["standard_monthly_yen"]
        == 1_210_000
    )
    assert (
        grade_47_2007["remuneration_lower_yen"]
        == 1_175_000
    )
    assert pd.isna(
        grade_47_2007[
            "remuneration_upper_yen"
        ]
    )

    period_2016 = result.loc[
        result["effective_from"]
        == pd.Timestamp("2016-04-01")
    ]

    grade_47_2016 = period_2016.loc[
        period_2016["grade"] == 47
    ].iloc[0]

    assert (
        grade_47_2016["remuneration_lower_yen"]
        == 1_175_000
    )
    assert (
        grade_47_2016["remuneration_upper_yen"]
        == 1_235_000
    )

    grade_48_2016 = period_2016.loc[
        period_2016["grade"] == 48
    ].iloc[0]

    assert (
        grade_48_2016["standard_monthly_yen"]
        == 1_270_000
    )
    assert (
        grade_48_2016["remuneration_lower_yen"]
        == 1_235_000
    )
    assert (
        grade_48_2016["remuneration_upper_yen"]
        == 1_295_000
    )

    grade_50_2016 = period_2016.loc[
        period_2016["grade"] == 50
    ].iloc[0]

    assert (
        grade_50_2016["standard_monthly_yen"]
        == 1_390_000
    )
    assert (
        grade_50_2016["remuneration_lower_yen"]
        == 1_355_000
    )
    assert pd.isna(
        grade_50_2016[
            "remuneration_upper_yen"
        ]
    )


def test_load_long_term_care_insurance_rates(
    tmp_path,
):
    path = (
        tmp_path
        / "long_term_care_insurance_rates.csv"
    )

    pd.DataFrame(
        {
            "effective_from": [
                "2024-03-01",
                "2025-03-01",
            ],
            "effective_to": [
                "2025-02-28",
                "2026-02-28",
            ],
            "total_rate": [
                0.0160,
                0.0159,
            ],
            "employee_share": [
                0.5,
                0.5,
            ],
        }
    ).to_csv(
        path,
        index=False,
    )

    result = (
        load_long_term_care_insurance_rates(
            path
        )
    )

    assert len(result) == 2

    assert result.loc[
        0,
        "total_rate",
    ] == pytest.approx(
        0.0160
    )

    assert result.loc[
        1,
        "total_rate",
    ] == pytest.approx(
        0.0159
    )

    assert pd.api.types.is_datetime64_any_dtype(
        result["effective_from"]
    )

    assert pd.api.types.is_datetime64_any_dtype(
        result["effective_to"]
    )


def test_real_long_term_care_insurance_rates():
    result = (
        load_long_term_care_insurance_rates()
    )

    assert not result.empty

    assert (
        result["effective_from"].min()
        == pd.Timestamp("2000-04-01")
    )

    assert (
        result["total_rate"] > 0
    ).all()

    assert (
        result["employee_share"]
        == 0.5
    ).all()

    rate_2025 = result.loc[
        (
            result["effective_from"]
            <= pd.Timestamp("2025-03-01")
        )
        & (
            result["effective_to"]
            >= pd.Timestamp("2025-03-01")
        )
    ]

    assert len(rate_2025) == 1

    assert rate_2025.iloc[
        0
    ]["total_rate"] == pytest.approx(
        0.0159
    )


def test_take_home_rule_tables_include_long_term_care():
    rules = load_take_home_rule_tables()

    assert (
        "long_term_care_insurance_rates"
        in rules
    )

    assert not rules[
        "long_term_care_insurance_rates"
    ].empty
