import streamlit as st

from real_wage_dashboard.cpi_service import create_cpi_dataframe
from real_wage_dashboard.estat_client import get_stats_data


STATS_DATA_ID = "0003427113"


def ensure_list(value: object) -> list:
    """辞書またはリストを、必ずリストとして返す。"""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=STATS_DATA_ID,
        filters={
            "cdTab": "1",
            "cdCat01": "0001",
            "cdArea": "00000",
        },
    )

    statistical_data = response[
        "GET_STATS_DATA"
    ][
        "STATISTICAL_DATA"
    ]

    values = ensure_list(
        statistical_data["DATA_INF"]["VALUE"]
    )

    print(f"取得件数: {len(values)}")

    df = create_cpi_dataframe(response)

    print(df.head())
    print()
    print(df.tail())
    print()
    print(df.dtypes)


if __name__ == "__main__":
    main()