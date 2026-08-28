import pandas as pd

from real_wage_dashboard.wage_revision_service import (
    _clean_numeric_value,
    _normalize_company_size,
    _parse_japanese_year,
    load_wage_revision_amount_rate,
    load_wage_revision_factors,
    load_wage_revision_status,
)


def test_parse_japanese_year_heisei() -> None:
    year, era = _parse_japanese_year("平成27年", None)

    assert year == 2015
    assert era == "平成"


def test_parse_japanese_year_reiwa_first_year() -> None:
    year, era = _parse_japanese_year("令和元年", "平成")

    assert year == 2019
    assert era == "令和"


def test_parse_japanese_year_continuation() -> None:
    year, era = _parse_japanese_year("　　７", "令和")

    assert year == 2025
    assert era == "令和"


def test_clean_numeric_value_missing() -> None:
    for value in ["…", "・", "･", "-", "－", ""]:
        assert pd.isna(_clean_numeric_value(value))


def test_clean_numeric_value_zero_is_not_missing() -> None:
    assert _clean_numeric_value(0) == 0.0


def test_normalize_company_size() -> None:
    assert _normalize_company_size("企業規模計") == "total"
    assert _normalize_company_size("5,000人以上") == "5000_plus"
    assert _normalize_company_size("1,000～4,999人") == "1000_4999"
    assert _normalize_company_size("300～999人") == "300_999"
    assert _normalize_company_size("100～299人") == "100_299"


def test_load_wage_revision_amount_rate_recent_period() -> None:
    df = load_wage_revision_amount_rate()

    recent_df = df[df["year"].between(2015, 2025)]

    assert recent_df["year"].nunique() == 11
    assert recent_df["company_size"].nunique() == 5
    assert len(recent_df) == 55


def test_load_wage_revision_amount_rate_2025_total() -> None:
    df = load_wage_revision_amount_rate()

    row = df[
        (df["year"] == 2025)
        & (df["company_size"] == "total")
    ].iloc[0]

    assert row["revision_amount_yen"] == 13601.0
    assert row["revision_rate_pct"] == 4.4


def test_load_wage_revision_amount_rate_has_no_duplicates() -> None:
    df = load_wage_revision_amount_rate()

    assert not df.duplicated(
        subset=["year", "company_size"]
    ).any()


def test_load_wage_revision_amount_rate_has_no_future_years() -> None:
    df = load_wage_revision_amount_rate()

    assert df["year"].max() <= 2025


def test_load_wage_revision_status_shape() -> None:
    df = load_wage_revision_status()

    assert len(df) == 275
    assert df["year"].nunique() == 11
    assert df["company_size"].nunique() == 5
    assert df["status"].nunique() == 5


def test_load_wage_revision_status_has_no_duplicates() -> None:
    df = load_wage_revision_status()

    assert not df.duplicated(
        subset=[
            "year",
            "company_size",
            "status",
        ]
    ).any()


def test_load_wage_revision_status_2015_1000_4999() -> None:
    df = load_wage_revision_status()

    row = df[
        (df["year"] == 2015)
        & (df["company_size"] == "1000_4999")
        & (df["status"] == "raised")
    ].iloc[0]

    assert row["company_share_pct"] == 93.9


def test_load_wage_revision_status_2025_total() -> None:
    df = load_wage_revision_status()

    total_2025 = df[
        (df["year"] == 2025)
        & (df["company_size"] == "total")
    ].set_index("status")

    assert total_2025.loc["raised", "company_share_pct"] == 91.5
    assert total_2025.loc["lowered", "company_share_pct"] == 1.1
    assert total_2025.loc["unchanged", "company_share_pct"] == 1.0
    assert total_2025.loc["no_revision", "company_share_pct"] == 2.4
    assert total_2025.loc["undecided", "company_share_pct"] == 3.9


def test_load_wage_revision_status_unchanged_definition() -> None:
    df = load_wage_revision_status()

    before_2025 = df[
        (df["year"] <= 2024)
        & (df["status"] == "unchanged")
    ]

    assert before_2025["company_share_pct"].isna().all()

    after_change = df[
        (df["year"] == 2025)
        & (df["status"] == "unchanged")
    ]

    assert (
        after_change["comparison_note"]
        == "separate category from 2025"
    ).all()


def test_load_wage_revision_status_each_group_has_five_statuses() -> None:
    df = load_wage_revision_status()

    counts = df.groupby(
        ["year", "company_size"]
    ).size()

    assert (counts == 5).all()


def test_load_wage_revision_factors_shape() -> None:
    df = load_wage_revision_factors()

    assert len(df) == 924


def test_load_wage_revision_factors_has_no_duplicates() -> None:
    df = load_wage_revision_factors()

    assert not df.duplicated(
        subset=[
            "year",
            "company_size",
            "response_type",
            "factor",
        ]
    ).any()


def test_load_wage_revision_factors_most_important_structure() -> None:
    df = load_wage_revision_factors()

    most_important = df[
        df["response_type"] == "most_important"
    ]

    assert len(most_important) == 770
    assert most_important["year"].nunique() == 11
    assert most_important["company_size"].nunique() == 5
    assert most_important["factor"].nunique() == 14


def test_load_wage_revision_factors_multiple_structure() -> None:
    df = load_wage_revision_factors()

    multiple = df[
        df["response_type"] == "multiple"
    ]

    assert len(multiple) == 154
    assert multiple["year"].nunique() == 11
    assert set(multiple["company_size"]) == {"100_299"}
    assert multiple["factor"].nunique() == 14


def test_load_wage_revision_factors_2025_total() -> None:
    df = load_wage_revision_factors()

    rows = df[
        (df["year"] == 2025)
        & (df["company_size"] == "total")
        & (df["response_type"] == "most_important")
    ].set_index("factor")

    assert rows.loc[
        "business_performance",
        "company_share_pct",
    ] == 41.7

    assert rows.loc[
        "labor_retention",
        "company_share_pct",
    ] == 17.0

    assert rows.loc[
        "minimum_wage",
        "company_share_pct",
    ] == 3.2


def test_load_wage_revision_factors_new_2025_categories() -> None:
    df = load_wage_revision_factors()

    new_factors = {
        "minimum_wage",
        "government_support",
        "expert_advice",
    }

    before_2025 = df[
        (df["year"] <= 2024)
        & (df["factor"].isin(new_factors))
    ]

    assert before_2025["company_share_pct"].isna().all()

    rows_2025 = df[
        (df["year"] == 2025)
        & (df["factor"].isin(new_factors))
    ]

    assert (
        rows_2025["comparison_note"]
        == "new response category from 2025"
    ).all()