import pandas as pd

from real_wage_dashboard.wage_revision_service import (
    load_wage_revision_amount_rate,
    load_wage_revision_factors,
    load_wage_revision_status,
)


def summarize_revision_trend() -> pd.DataFrame:
    amount_rate = load_wage_revision_amount_rate()

    amount_rate = amount_rate[
        amount_rate["company_size"] == "total"
    ][
        [
            "year",
            "revision_amount_yen",
            "revision_rate_pct",
        ]
    ]

    status = load_wage_revision_status()

    raised = status[
        (status["company_size"] == "total")
        & (status["status"] == "raised")
    ][
        [
            "year",
            "company_share_pct",
        ]
    ].rename(
        columns={
            "company_share_pct": "raised_share_pct",
        }
    )

    result = amount_rate.merge(
        raised,
        on="year",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values("year").reset_index(drop=True)


def summarize_company_size_revision() -> pd.DataFrame:
    amount_rate = load_wage_revision_amount_rate()

    status = load_wage_revision_status()

    raised = status[
        status["status"] == "raised"
    ][
        [
            "year",
            "company_size",
            "company_share_pct",
        ]
    ].rename(
        columns={
            "company_share_pct": "raised_share_pct",
        }
    )

    result = amount_rate.merge(
        raised,
        on=[
            "year",
            "company_size",
        ],
        how="inner",
        validate="one_to_one",
    )

    return result[
        [
            "year",
            "company_size",
            "revision_amount_yen",
            "revision_rate_pct",
            "raised_share_pct",
        ]
    ].sort_values(
        [
            "year",
            "company_size",
        ]
    ).reset_index(drop=True)


def summarize_revision_factors() -> pd.DataFrame:
    factors = load_wage_revision_factors()

    result = factors[
        factors["response_type"] == "most_important"
    ][
        [
            "year",
            "company_size",
            "factor",
            "company_share_pct",
        ]
    ].copy()

    return result.sort_values(
        [
            "year",
            "company_size",
            "factor",
        ]
    ).reset_index(drop=True)


def summarize_factor_changes(
    start_year: int = 2015,
    end_year: int = 2025,
) -> pd.DataFrame:
    factors = summarize_revision_factors()

    start = factors[
        factors["year"] == start_year
    ][
        [
            "company_size",
            "factor",
            "company_share_pct",
        ]
    ].rename(
        columns={
            "company_share_pct": "start_share_pct",
        }
    )

    end = factors[
        factors["year"] == end_year
    ][
        [
            "company_size",
            "factor",
            "company_share_pct",
        ]
    ].rename(
        columns={
            "company_share_pct": "end_share_pct",
        }
    )

    result = start.merge(
        end,
        on=[
            "company_size",
            "factor",
        ],
        how="inner",
        validate="one_to_one",
    )

    result["change_pt"] = (
        result["end_share_pct"]
        - result["start_share_pct"]
    )

    return result.sort_values(
        [
            "company_size",
            "change_pt",
        ],
        ascending=[
            True,
            False,
        ],
        na_position="last",
    ).reset_index(drop=True)
