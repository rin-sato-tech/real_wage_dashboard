from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from real_wage_dashboard.wage_distribution_service import (
    load_wage_distribution_history_by_employment,
)

ESTAT_BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json"
# STATS_DATA_ID = "0003268283" # 2019年までの雇用形態別賃金分布特性値データ
STATS_DATA_ID = "0003446899"

QUANTILE_CODE_MAP = {
    "1280": "p10",
    "1290": "p25",
    "1300": "p50",
    "1310": "p75",
    "1320": "p90",
    "1330": "decile_dispersion",
    "1340": "quartile_dispersion",
}

EMPLOYMENT_CODE_MAP = {
    "02": "regular",
    "03": "nonregular",
}

DATA_DIR = Path("data/raw/wage_distribution/employment")


def get_app_id() -> str:
    app_id = st.secrets["ESTAT_APP_ID"]

    if not app_id:
        raise RuntimeError("ESTAT_APP_ID が設定されていません。")

    return app_id


def get_meta_info(
    app_id: str,
    stats_data_id: str,
) -> dict:
    url = f"{ESTAT_BASE_URL}/getMetaInfo"

    params = {
        "appId": app_id,
        "statsDataId": stats_data_id,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    result = payload["GET_META_INFO"]["RESULT"]

    if result["STATUS"] != 0:
        raise RuntimeError(f"e-Stat API error: {result}")

    return payload


def get_stats_data(
    app_id: str,
    stats_data_id: str,
) -> dict:
    url = f"{ESTAT_BASE_URL}/getStatsData"

    params = {
        "appId": app_id,
        "statsDataId": stats_data_id,
        "cdCat01": "010",
        "cdCat02": "1280,1290,1300,1310,1320,1330,1340",
        "cdCat03": "01",
        "cdCat04": "01",
        "cdCat05": "02,03",
        "cdCat06": "100010",
        "cdCat07": "01",
        "cdTime": "2015000000",
        "limit": 100,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    result = payload["GET_STATS_DATA"]["RESULT"]

    if result["STATUS"] != 0:
        raise RuntimeError(f"e-Stat API error: {result}")

    return payload


def get_employment_distribution_2015_2019(
    app_id: str,
) -> pd.DataFrame:
    url = f"{ESTAT_BASE_URL}/getStatsData"

    params = {
        "appId": app_id,
        "statsDataId": "0003268283",
        "cdCat01": "010",
        "cdCat02": "1280,1290,1300,1310,1320,1330,1340",
        "cdCat03": "01",
        "cdCat04": "01",
        "cdCat05": "02,03",
        "cdCat06": "100010",
        "cdCat07": "01",
        "cdTime": ",".join(
            [
                "2015000000",
                "2016000000",
                "2017000000",
                "2018000000",
                "20190000000",
            ]
        ),
        "limit": 1000,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    result = payload["GET_STATS_DATA"]["RESULT"]

    if result["STATUS"] != 0:
        raise RuntimeError(f"e-Stat API error: {result}")

    values = payload["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

    records: dict[tuple[int, str], dict] = {}

    for value in values:
        year = int(value["@time"][:4])

        employment = EMPLOYMENT_CODE_MAP[value["@cat05"]]

        key = (year, employment)

        if key not in records:
            records[key] = {
                "year": year,
                "employment": employment,
            }

        column = QUANTILE_CODE_MAP[value["@cat02"]]

        records[key][column] = float(value["$"])

    return (
        pd.DataFrame(records.values())
        .sort_values(["employment", "year"])
        .reset_index(drop=True)
    )


def get_employment_distribution_2020_2023(
    app_id: str,
) -> pd.DataFrame:
    url = f"{ESTAT_BASE_URL}/getStatsData"

    params = {
        "appId": app_id,
        "statsDataId": "0003446899",
        "cdCat01": "01",
        "cdCat02": "1280,1290,1300,1310,1320,1330,1340",
        "cdCat03": "01",
        "cdCat04": "01",
        "cdCat05": "02,03",
        "cdCat06": "01",
        "cdCat07": "01",
        "cdCat08": "02",
        "cdTime": ",".join(
            [
                "2020000000",
                "2021000000",
                "2022000000",
                "2023000000",
            ]
        ),
        "limit": 1000,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()

    result = payload["GET_STATS_DATA"]["RESULT"]

    if result["STATUS"] != 0:
        raise RuntimeError(f"e-Stat API error: {result}")

    values = payload["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

    records: dict[tuple[int, str], dict] = {}

    for value in values:
        year = int(value["@time"][:4])
        employment = EMPLOYMENT_CODE_MAP[value["@cat05"]]

        key = (year, employment)

        if key not in records:
            records[key] = {
                "year": year,
                "employment": employment,
            }

        column = QUANTILE_CODE_MAP[value["@cat02"]]

        records[key][column] = float(value["$"])

    return (
        pd.DataFrame(records.values())
        .sort_values(["employment", "year"])
        .reset_index(drop=True)
    )


def main() -> None:
    app_id = get_app_id()

    payload = get_meta_info(
        app_id,
        STATS_DATA_ID,
    )

    class_objects = payload["GET_META_INFO"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]

    # print(
    #     f"=== statsDataId={STATS_DATA_ID} ==="
    # )

    # for class_object in class_objects:
    #     print()
    #     print(
    #         "id:",
    #         class_object.get("@id"),
    #     )
    #     print(
    #         "name:",
    #         class_object.get("@name"),
    #     )

    #     classes = class_object.get(
    #         "CLASS",
    #         [],
    #     )

    #     if isinstance(classes, dict):
    #         classes = [classes]

    #     # cat02 だけ全件表示
    #     if class_object.get("@id") == "cat02":
    #         for item in classes:
    #             print(
    #                 " ",
    #                 item.get("@code"),
    #                 item.get("@name"),
    #             )

    # payload = get_stats_data(
    #     app_id,
    #     STATS_DATA_ID,
    # )

    # values = (
    #     payload["GET_STATS_DATA"]
    #     ["STATISTICAL_DATA"]
    #     ["DATA_INF"]
    #     ["VALUE"]
    # )

    # print()
    # print("=== 2015 雇用形態別 分布特性値 ===")

    # for value in values:
    #     print(value)

    # df = get_employment_distribution_2015_2019(
    #     app_id
    # )

    # print()
    # print("=== 2015-2019 雇用形態別賃金分布 ===")
    # print(df.to_string(index=False))

    for class_object in class_objects:
        if class_object.get("@id") not in {
            "tab",
            "cat01",
            "cat02",
            "cat03",
            "cat04",
            "cat05",
            "cat06",
            "cat07",
            "cat08",
            "time",
        }:
            continue

        # print()
        # print(
        #     "id:",
        #     class_object.get("@id"),
        # )
        # print(
        #     "name:",
        #     class_object.get("@name"),
        # )

        classes = class_object.get(
            "CLASS",
            [],
        )

        if isinstance(classes, dict):
            classes = [classes]

        # for item in classes:
        #     print(
        #         " ",
        #         item.get("@code"),
        #         item.get("@name"),
        #     )

    # df_2020_2023 = (
    #     get_employment_distribution_2020_2023(
    #         app_id
    #     )
    # )

    # print()
    # print("=== 2020-2023 雇用形態別賃金分布 ===")
    # print(df_2020_2023.to_string(index=False))

    employment_history = load_wage_distribution_history_by_employment(
        app_id=app_id,
        excel_data_dir=DATA_DIR,
    )

    print()
    print("=== 2015-2025 雇用形態別賃金分布 ===")
    print(employment_history.to_string(index=False))

    print()
    print("rows:", len(employment_history))

    assert len(employment_history) == 22

    assert employment_history[["year", "employment"]].duplicated().sum() == 0


if __name__ == "__main__":
    main()
