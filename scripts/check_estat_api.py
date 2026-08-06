import streamlit as st

from real_wage_dashboard.estat_client import get_meta_info

STATS_DATA_ID = "0003427113"


def ensure_list(value: object) -> list:
    """辞書またはリストを、必ずリストとして返す。"""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def print_classes(
    class_object: dict,
    limit: int = 20,
) -> None:
    """分類項目と分類コードを表示する。"""
    class_id = class_object.get("@id", "不明")
    class_name = class_object.get("@name", "名称なし")

    print()
    print("=" * 60)
    print(f"分類ID: {class_id}")
    print(f"分類名: {class_name}")
    print("=" * 60)

    classes = ensure_list(class_object.get("CLASS"))

    for item in classes[:limit]:
        print(
            f"コード={item.get('@code')}  "
            f"名称={item.get('@name')}  "
            f"レベル={item.get('@level')}"
        )

    if len(classes) > limit:
        print(f"... 残り {len(classes) - limit} 件")


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    response = get_meta_info(
        app_id=app_id,
        stats_data_id=STATS_DATA_ID,
    )

    metadata = response["GET_META_INFO"]["METADATA_INF"]

    table_info = metadata["TABLE_INF"]

    print("API接続に成功しました。")
    print(f"統計表ID: {table_info.get('@id')}")
    print(f"統計表名: {table_info.get('STAT_NAME')}")
    print(f"表題: {table_info.get('TITLE')}")

    class_objects = ensure_list(metadata["CLASS_INF"]["CLASS_OBJ"])

    for class_object in class_objects:
        print_classes(class_object)


if __name__ == "__main__":
    main()
