import pytest

import pandas as pd

from real_wage_dashboard.take_home_service import (
    _create_standard_monthly_brackets,
    load_income_tax_brackets,
    load_pension_standard_monthly_history,
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
