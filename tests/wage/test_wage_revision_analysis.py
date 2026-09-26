import pytest

from real_wage_dashboard.wage_revision_analysis import (
    summarize_company_size_revision,
    summarize_factor_changes,
    summarize_revision_factors,
    summarize_revision_trend,
)


def test_summarize_revision_trend_shape() -> None:
    df = summarize_revision_trend()

    assert len(df) == 11
    assert list(df["year"]) == list(range(2015, 2026))


def test_summarize_revision_trend_2025() -> None:
    df = summarize_revision_trend()

    row = df[df["year"] == 2025].iloc[0]

    assert row["revision_amount_yen"] == 13601.0
    assert row["revision_rate_pct"] == 4.4
    assert row["raised_share_pct"] == 91.5


def test_summarize_revision_trend_2021() -> None:
    df = summarize_revision_trend()

    row = df[df["year"] == 2021].iloc[0]

    assert row["revision_amount_yen"] == 4694.0
    assert row["revision_rate_pct"] == 1.6
    assert row["raised_share_pct"] == 80.7


def test_summarize_company_size_revision_shape() -> None:
    df = summarize_company_size_revision()

    assert len(df) == 55

    counts = df.groupby(["year", "company_size"]).size()

    assert (counts == 1).all()


def test_summarize_company_size_revision_2025() -> None:
    df = summarize_company_size_revision()

    rows = df[df["year"] == 2025].set_index("company_size")

    assert (
        rows.loc[
            "5000_plus",
            "revision_rate_pct",
        ]
        == 5.1
    )

    assert (
        rows.loc[
            "100_299",
            "revision_rate_pct",
        ]
        == 3.6
    )

    assert (
        rows.loc[
            "5000_plus",
            "raised_share_pct",
        ]
        == 98.9
    )

    assert (
        rows.loc[
            "100_299",
            "raised_share_pct",
        ]
        == 89.7
    )


def test_summarize_revision_factors_structure() -> None:
    df = summarize_revision_factors()

    assert len(df) == 770

    assert set(df["company_size"].unique()) == {
        "total",
        "5000_plus",
        "1000_4999",
        "300_999",
        "100_299",
    }

    assert df["factor"].nunique() == 14


def test_summarize_revision_factors_2025_total() -> None:
    df = summarize_revision_factors()

    rows = df[(df["year"] == 2025) & (df["company_size"] == "total")].set_index(
        "factor"
    )

    assert (
        rows.loc[
            "business_performance",
            "company_share_pct",
        ]
        == 41.7
    )

    assert (
        rows.loc[
            "labor_retention",
            "company_share_pct",
        ]
        == 17.0
    )

    assert (
        rows.loc[
            "market_rate",
            "company_share_pct",
        ]
        == 7.7
    )


def test_summarize_factor_changes_total() -> None:
    df = summarize_factor_changes()

    rows = df[df["company_size"] == "total"].set_index("factor")

    assert rows.loc[
        "business_performance",
        "change_pt",
    ] == pytest.approx(-10.9)

    assert rows.loc[
        "labor_retention",
        "change_pt",
    ] == pytest.approx(10.2)

    assert rows.loc[
        "employment_maintenance",
        "change_pt",
    ] == pytest.approx(6.9)

    assert rows.loc[
        "market_rate",
        "change_pt",
    ] == pytest.approx(4.1)


def test_summarize_factor_changes_new_categories_are_missing() -> None:
    df = summarize_factor_changes()

    new_categories = df[
        (df["company_size"] == "total")
        & (
            df["factor"].isin(
                [
                    "minimum_wage",
                    "government_support",
                    "expert_advice",
                ]
            )
        )
    ]

    assert new_categories["change_pt"].isna().all()


def test_summarize_factor_changes_company_size_difference() -> None:
    df = summarize_factor_changes()

    business = df[df["factor"] == "business_performance"].set_index("company_size")

    assert business.loc[
        "5000_plus",
        "change_pt",
    ] == pytest.approx(-19.3)

    assert business.loc[
        "100_299",
        "change_pt",
    ] == pytest.approx(-8.7)

    retention = df[df["factor"] == "labor_retention"].set_index("company_size")

    assert retention.loc[
        "1000_4999",
        "change_pt",
    ] == pytest.approx(13.2)

    assert retention.loc[
        "100_299",
        "change_pt",
    ] == pytest.approx(10.7)
