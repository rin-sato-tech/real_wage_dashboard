import streamlit as st

from real_wage_dashboard.config import CORPORATE_STATS_DATA_ID
from real_wage_dashboard.estat_client import get_meta_info

TARGET_ITEMS = [
    "売上高",
    "営業利益",
    "経常利益",
    "役員給与",
    "役員賞与",
    "従業員給与",
    "従業員賞与",
    "福利厚生費",
    "期中平均従業員数",
    "付加価値",
    "従業員一人当付加価値",
    "付加価値率",
    "売上高営業利益率",
    "売上高経常利益率",
]

TARGET_INDUSTRIES = [
    "鉱業、採石業、砂利採取業",
    "建設業",
    "製造業",
    "情報通信業",
    "運輸業、郵便業(集約)",
    "卸売業・小売業(集約)",
    "不動産業、物品賃貸業(集約)",
    "学術研究、専門・技術サービス業(集約)",
    "宿泊業、飲食サービス業(集約)",
    "生活関連サービス業、娯楽業(集約)",
    "教育、学習支援業",
    "医療、福祉業",
]

TARGET_YEARS = {
    "2015年度",
    "2024年度",
}


def main() -> None:
    app_id = st.secrets["ESTAT_APP_ID"]

    data = get_meta_info(
        app_id=app_id,
        stats_data_id=CORPORATE_STATS_DATA_ID,
    )

    class_objects = data["GET_META_INFO"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]

    for class_object in class_objects:
        class_id = class_object["@id"]
        class_name = class_object["@name"]

        classes = class_object["CLASS"]

        if isinstance(classes, dict):
            classes = [classes]

        print("=" * 80)
        print("id:", class_id)
        print("name:", class_name)

        if class_id == "cat01":
            for item in classes:
                name = item.get("@name", "")

                if any(target in name for target in TARGET_ITEMS):
                    print(
                        item.get("@code"),
                        name,
                        item.get("@unit"),
                    )

        elif class_id == "cat02":
            for item in classes:
                name = item.get("@name", "")

                if name in TARGET_INDUSTRIES:
                    print(
                        item.get("@code"),
                        name,
                    )

        elif class_id == "cat03":
            for item in classes:
                if item.get("@code") in {"26", "25", "24", "22"}:
                    print(
                        item.get("@code"),
                        item.get("@name"),
                    )

        elif class_id == "time":
            for item in classes:
                if item.get("@name") in TARGET_YEARS:
                    print(
                        item.get("@code"),
                        item.get("@name"),
                    )


if __name__ == "__main__":
    main()
