import pandas as pd
import pytest

from real_wage_dashboard.corporate_performance_service import (
    add_corporate_derived_metrics,
    create_corporate_performance_dataframe,
    create_corporate_time_codes,
    ensure_list,
)


def test_ensure_list() -> None:
    assert ensure_list(None) == []
    assert ensure_list("value") == ["value"]
    assert ensure_list(["a", "b"]) == ["a", "b"]


def test_create_corporate_time_codes() -> None:
    assert create_corporate_time_codes(
        start_year=2020,
        end_year=2022,
    ) == [
        "20200",
        "20210",
        "20220",
    ]


def test_create_corporate_time_codes_rejects_invalid_period() -> None:
    with pytest.raises(
        ValueError,
        match="開始年度は終了年度以下",
    ):
        create_corporate_time_codes(
            start_year=2022,
            end_year=2020,
        )


def test_create_corporate_performance_dataframe() -> None:
    response = {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "DATA_INF": {
                    "VALUE": [
                        {
                            "@cat01": "073",
                            "@time": "20230",
                            "$": "1000",
                        },
                        {
                            "@cat01": "073",
                            "@time": "20240",
                            "$": "1100",
                        },
                        {
                            "@cat01": "141",
                            "@time": "20230",
                            "$": "700",
                        },
                        {
                            "@cat01": "141",
                            "@time": "20240",
                            "$": "750",
                        },
                    ]
                }
            }
        }
    }

    result = create_corporate_performance_dataframe(response)

    assert result["fiscal_year"].tolist() == [2023, 2024]
    assert result["value_added"].tolist() == [1000, 1100]
    assert result["labor_productivity"].tolist() == [700, 750]


def test_add_corporate_derived_metrics() -> None:
    df = pd.DataFrame(
        {
            "fiscal_year": [2024],
            "executive_salary": [100.0],
            "executive_bonus": [10.0],
            "employee_salary": [500.0],
            "employee_bonus": [50.0],
            "welfare_expenses": [40.0],
            "value_added": [1000.0],
            "average_employees": [100.0],
            "labor_productivity": [1000.0],
        }
    )

    result = add_corporate_derived_metrics(df)

    assert result.loc[0, "personnel_expenses"] == pytest.approx(700.0)

    assert result.loc[0, "labor_share"] == pytest.approx(70.0)

    assert result.loc[
        0,
        "personnel_expenses_per_employee",
    ] == pytest.approx(700.0)

    assert result.loc[
        0,
        "calculated_labor_productivity",
    ] == pytest.approx(1000.0)

    assert result.loc[
        0,
        "labor_productivity_diff",
    ] == pytest.approx(0.0)


@pytest.mark.parametrize(
    "missing_column",
    [
        "executive_salary",
        "executive_bonus",
        "employee_salary",
        "employee_bonus",
        "welfare_expenses",
        "value_added",
        "average_employees",
        "labor_productivity",
    ],
)
def test_add_corporate_derived_metrics_requires_columns(
    missing_column: str,
) -> None:
    df = pd.DataFrame(
        {
            "executive_salary": [100.0],
            "executive_bonus": [10.0],
            "employee_salary": [500.0],
            "employee_bonus": [50.0],
            "welfare_expenses": [40.0],
            "value_added": [1000.0],
            "average_employees": [100.0],
            "labor_productivity": [1000.0],
        }
    ).drop(columns=missing_column)

    with pytest.raises(
        ValueError,
        match="派生指標の計算に必要な列",
    ):
        add_corporate_derived_metrics(df)
