from typing import Any

import streamlit as st

from real_wage_dashboard.config import (
    CPI_BASE_FILTERS,
    CPI_SERIES,
    CPI_STATS_DATA_ID,
)
from real_wage_dashboard.cpi_analysis import add_cpi_changes
from real_wage_dashboard.cpi_service import create_cpi_dataframe
from real_wage_dashboard.estat_client import get_stats_data


def ensure_list(value: Any) -> list[Any]:
    """辞書またはリストを、必ずリストとして返す。"""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    filters = {
        **CPI_BASE_FILTERS,
        "cdCat01": CPI_SERIES["総合"],
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=CPI_STATS_DATA_ID,
        filters=filters,
    )

    statistical_data = response["GET_STATS_DATA"]["STATISTICAL_DATA"]

    values = ensure_list(statistical_data["DATA_INF"]["VALUE"])

    df = create_cpi_dataframe(response)
    df = add_cpi_changes(df)

    print(f"API取得件数: {len(values)}")
    print(f"整形後件数: {len(df)}")

    print("\n先頭10行")
    print(df.head(10).to_string(index=False))

    print("\n末尾10行")
    print(df.tail(10).to_string(index=False))

    print("\nデータ型")
    print(df.dtypes)

    print("\n重複年月")
    print(df["date"].duplicated().sum())

    print("\n期間")
    print(
        df["date"].min(),
        "～",
        df["date"].max(),
    )


if __name__ == "__main__":
    main()
