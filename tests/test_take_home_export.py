import pandas as pd

from real_wage_dashboard.take_home_export import (
    create_take_home_tableau_export,
)


def test_create_take_home_tableau_export() -> None:
    main = pd.DataFrame(
        {
            "year": [
                1990,
                2025,
            ],
            "gross_salary_yen": [
                3_900_000.0,
                4_200_000.0,
            ],
            "real_take_home_index": [
                100.0,
                81.4,
            ],
        }
    )

    period_log = pd.DataFrame(
        {
            "period": [
                "1990→2025",
            ],
            "start_year": [
                1990,
            ],
            "end_year": [
                2025,
            ],
            "wage_log_contribution_pt": [
                8.0,
            ],
        }
    )

    burden_change = pd.DataFrame(
        {
            "period": [
                "1990→2025",
            ],
            "start_year": [
                1990,
            ],
            "end_year": [
                2025,
            ],
            "total_change_pt": [
                3.78,
            ],
        }
    )

    burden_shapley = pd.DataFrame(
        {
            "period": [
                "1990→2025",
            ],
            "start_year": [
                1990,
            ],
            "end_year": [
                2025,
            ],
            "social_insurance_policy_effect_pt": [
                4.23,
            ],
        }
    )

    real_shapley = pd.DataFrame(
        {
            "period": [
                "1990→2025",
            ],
            "start_year": [
                1990,
            ],
            "end_year": [
                2025,
            ],
            "price_effect_yen": [
                -790_000.0,
            ],
            "price_effect_pct_of_start": [
                -21.68,
            ],
        }
    )

    robustness = pd.DataFrame(
        {
            "check": [
                "sex",
            ],
            "comparison": [
                "female",
            ],
            "period": [
                "1990→2025",
            ],
            "metric": [
                "real_take_home_change_pct",
            ],
            "value": [
                -18.78,
            ],
            "unit": [
                "pct",
            ],
            "note": [
                "test",
            ],
        }
    )

    result = (
        create_take_home_tableau_export(
            main_series=main,
            period_log_decomposition=(
                period_log
            ),
            burden_change_summary=(
                burden_change
            ),
            burden_shapley=(
                burden_shapley
            ),
            real_shapley=real_shapley,
            robustness_summary=(
                robustness
            ),
        )
    )

    assert not result.empty

    assert {
        "annual_main",
        "period_log_decomposition",
        "burden_change",
        "burden_shapley",
        "real_take_home_shapley",
        "robustness",
    } == set(
        result[
            "record_type"
        ].unique()
    )

    annual = result.loc[
        (
            result[
                "record_type"
            ] == "annual_main"
        )
        & (
            result[
                "metric"
            ] == "gross_salary_yen"
        )
    ]

    assert len(annual) == 2
    assert set(
        annual["unit"]
    ) == {"yen"}

    assert (
        result["analysis"]
        == "take_home_wage"
    ).all()

    shapley_pct = result.loc[
        (
            result["record_type"]
            == "real_take_home_shapley"
        )
        & (
            result["metric"]
            == "price_effect_pct_of_start"
        )
    ]

    assert len(shapley_pct) == 1
    assert (
        shapley_pct.iloc[0]["unit"]
        == "pct"
    )
