from typing import Any

import pandas as pd


def ensure_list(value: Any) -> list[Any]:
    """値を必ずリストとして返す。"""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def create_time_mapping(response: dict[str, Any]) -> dict[str, str]:
    """時間コードと時間名称の対応表を作成する。"""

    class_objects = response["GET_STATS_DATA"]["STATISTICAL_DATA"]["CLASS_INF"][
        "CLASS_OBJ"
    ]

    for class_object in ensure_list(class_objects):
        if class_object.get("@id") != "time":
            continue

        time_classes = ensure_list(class_object.get("CLASS"))

        return {item["@code"]: item["@name"] for item in time_classes}

    return {}


def create_cpi_dataframe(response: dict[str, Any]) -> pd.DataFrame:
    """e-Stat APIレスポンスからCPIのDataFrameを作成する。"""

    values = response["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

    time_mapping = create_time_mapping(response)

    rows = []

    for item in ensure_list(values):
        time_code = item.get("@time")

        rows.append(
            {
                "time_code": time_code,
                "time_name": time_mapping.get(time_code),
                "index_value": item.get("$"),
            }
        )

    df = pd.DataFrame(rows)

    df["index_value"] = pd.to_numeric(
        df["index_value"],
        errors="coerce",
    )

    df["date"] = pd.to_datetime(
        df["time_name"],
        format="%Y年%m月",
        errors="coerce",
    )

    df = (
        df.dropna(subset=["date", "index_value"])
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df
