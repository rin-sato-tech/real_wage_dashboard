import os

import streamlit as st

from real_wage_dashboard.estat_client import get_meta_info


STATS_DATA_ID = "0003427113"


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    data = get_meta_info(
        app_id=app_id,
        stats_data_id=STATS_DATA_ID,
    )

    statistical_data = data["GET_META_INFO"]["METADATA_INF"]

    print("API接続に成功しました。")
    print(
        statistical_data["TABLE_INF"]["TITLE_SPEC"]["TABLE_NAME"]
    )

    class_objects = statistical_data[
        "CLASS_INF"
    ][
        "CLASS_OBJ"
    ]

    for class_object in class_objects:
        print(
            class_object.get("@id"),
            class_object.get("@name"),
        )


if __name__ == "__main__":
    main()