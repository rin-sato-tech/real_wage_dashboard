import pandas as pd

from real_wage_dashboard.cpi_service import create_cpi_dataframe


def test_create_cpi_dataframe() -> None:
    response = {
        "GET_STATS_DATA": {
            "STATISTICAL_DATA": {
                "CLASS_INF": {
                    "CLASS_OBJ": [
                        {
                            "@id": "time",
                            "CLASS": [
                                {
                                    "@code": "2025000101",
                                    "@name": "2025年1月",
                                },
                                {
                                    "@code": "2025000202",
                                    "@name": "2025年2月",
                                },
                            ],
                        }
                    ]
                },
                "DATA_INF": {
                    "VALUE": [
                        {
                            "@time": "2025000202",
                            "$": "102.0",
                        },
                        {
                            "@time": "2025000101",
                            "$": "100.0",
                        },
                    ]
                },
            }
        }
    }

    result = create_cpi_dataframe(response)

    assert len(result) == 2
    assert result.loc[0, "date"] == pd.Timestamp("2025-01-01")
    assert result.loc[0, "index_value"] == 100.0
    assert result.loc[1, "date"] == pd.Timestamp("2025-02-01")
