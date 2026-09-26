import pandas as pd
import pytest

from real_wage_dashboard.macro_distribution_service import (
    create_sna_dataframe,
    create_sna_time_codes,
)


def test_create_sna_time_codes() -> None:
    assert create_sna_time_codes(
        start_year=2022,
        end_year=2024,
    ) == [
        "2022100000",
        "2023100000",
        "2024100000",
    ]


def test_create_sna_time_codes_rejects_invalid_period() -> None:
    with pytest.raises(
        ValueError,
        match="開始年度は終了年度以下",
    ):
        create_sna_time_codes(
            start_year=2024,
            end_year=2022,
        )


def test_create_sna_dataframe() -> None:
    response = {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "DATA_INF": {
                    "VALUE": [
                        {
                            "@cat01": "11",
                            "@time": "2023100000",
                            "$": "300000",
                        },
                        {
                            "@cat01": "32",
                            "@time": "2023100000",
                            "$": "600000",
                        },
                        {
                            "@cat01": "11",
                            "@time": "2024100000",
                            "$": "310000",
                        },
                        {
                            "@cat01": "32",
                            "@time": "2024100000",
                            "$": "620000",
                        },
                    ]
                }
            }
        }
    }

    items = {
        "employee_compensation": "11",
        "gross_domestic_product": "32",
    }

    result = create_sna_dataframe(
        response=response,
        items=items,
    )

    expected = pd.DataFrame(
        {
            "fiscal_year": [2023, 2024],
            "employee_compensation": [
                300000,
                310000,
            ],
            "gross_domestic_product": [
                600000,
                620000,
            ],
        }
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
        check_dtype=False,
    )


def test_create_sna_dataframe_ignores_unmapped_items() -> None:
    response = {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "DATA_INF": {
                    "VALUE": [
                        {
                            "@cat01": "11",
                            "@time": "2024100000",
                            "$": "100",
                        },
                        {
                            "@cat01": "999",
                            "@time": "2024100000",
                            "$": "999",
                        },
                    ]
                }
            }
        }
    }

    result = create_sna_dataframe(
        response=response,
        items={"employee_compensation": "11"},
    )

    assert result.columns.tolist() == [
        "fiscal_year",
        "employee_compensation",
    ]

    assert result.loc[
        0,
        "employee_compensation",
    ] == pytest.approx(100.0)


def test_create_sna_dataframe_preserves_missing_values() -> None:
    response = {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "DATA_INF": {
                    "VALUE": [
                        {
                            "@cat01": "11",
                            "@time": "2024100000",
                            "$": "-",
                        }
                    ]
                }
            }
        }
    }

    result = create_sna_dataframe(
        response=response,
        items={"employee_compensation": "11"},
    )

    assert pd.isna(
        result.loc[
            0,
            "employee_compensation",
        ]
    )


def test_create_sna_dataframe_rejects_duplicates() -> None:
    response = {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "DATA_INF": {
                    "VALUE": [
                        {
                            "@cat01": "11",
                            "@time": "2024100000",
                            "$": "100",
                        },
                        {
                            "@cat01": "11",
                            "@time": "2024100000",
                            "$": "101",
                        },
                    ]
                }
            }
        }
    }

    with pytest.raises(
        ValueError,
        match="年度・項目の重複",
    ):
        create_sna_dataframe(
            response=response,
            items={"employee_compensation": "11"},
        )
