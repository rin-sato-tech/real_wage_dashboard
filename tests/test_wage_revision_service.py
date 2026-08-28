import pandas as pd

from real_wage_dashboard.wage_revision_service import (
    _clean_numeric_value,
    _normalize_company_size,
    _parse_japanese_year,
    load_wage_revision_amount_rate,
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
