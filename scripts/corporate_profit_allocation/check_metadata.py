from __future__ import annotations

from typing import Any

import streamlit as st

from real_wage_dashboard.estat_client import get_meta_info
from real_wage_dashboard.estat_response import ensure_list

TABLES = {
    "sna_primary_income": "0004049827",
    "sna_secondary_distribution": "0004049828",
    "sna_use_income": "0004049829",
    "sna_capital_account": "0004049767",
    "sna_financial_account": "0004049768",
    "sna_balance_sheet": "0004049867",
    "corporate_statistics": "0003060791",
    # 15番追加
    "sna_financial_assets_detail": "0004050013",
    "sna_financial_liabilities_detail": "0004050014",

    "sna_other_volume_changes": "0004049868",
    "sna_revaluation": "0004049869",
}

KEYWORDS = (
    # SNA 所得
    "営業余剰",
    "財産所得",
    "利子",
    "配当",
    "再投資収益",
    "第１次所得",
    "第1次所得",
    "経常税",
    "可処分所得",
    "貯蓄",
    # 資本勘定
    "固定資本形成",
    "固定資本減耗",
    "在庫",
    "土地",
    "資本移転",
    "純貸出",
    "純借入",
    # 金融資産・負債
    "現金",
    "預金",
    "貸出",
    "借入",
    "債務証券",
    "株式",
    "持分",
    "金融資産",
    "負債",
    "正味資産",
    # 法人企業統計
    "営業利益",
    "経常利益",
    "純利益",
    "配当",
    "利益剰余金",
    "現金",
    "預金",
    "有価証券",
    "固定資産",
    "借入金",
    "社債",
    "純資産",
)

FULL_OUTPUT_TABLES = {
    "sna_secondary_distribution",
    "sna_financial_account",
    "sna_financial_assets_detail",
    "sna_financial_liabilities_detail",

    "sna_balance_sheet",
    "sna_other_volume_changes",
    "sna_revaluation",
}


def get_class_objects(
    response: dict[str, Any],
) -> list[dict[str, Any]]:
    return ensure_list(
        response["GET_META_INFO"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]
    )


def print_metadata(
    table_name: str,
    stats_data_id: str,
    app_id: str,
) -> None:
    print()
    print("=" * 100)
    print(f"{table_name}: {stats_data_id}")
    print("=" * 100)

    response = get_meta_info(
        app_id=app_id,
        stats_data_id=stats_data_id,
    )

    for class_obj in get_class_objects(response):
        class_id = class_obj.get("@id")
        class_name = class_obj.get("@name")

        print()
        print(f"[{class_id}] {class_name}")

        matches = []

        for item in ensure_list(class_obj.get("CLASS")):
            code = item.get("@code")
            name = item.get("@name", "")
            unit = item.get("@unit")

            if (
                table_name not in FULL_OUTPUT_TABLES
                and not any(
                    keyword in name
                    for keyword in KEYWORDS
                )
            ):
                continue

            suffix = (
                f" [{unit}]"
                if unit
                else ""
            )

            print(
                f"  {code}: {name}{suffix}"
            )


def get_app_id() -> str:
    """Streamlit secretsからe-Stat APIのapp IDを取得する。"""

    try:
        return str(st.secrets["ESTAT_APP_ID"])

    except KeyError as exc:
        raise RuntimeError(
            ".streamlit/secrets.tomlに"
            "ESTAT_APP_IDを設定してください。"
        ) from exc


def main() -> None:
    app_id = get_app_id()

    for table_name, stats_data_id in TABLES.items():
        print_metadata(
            table_name=table_name,
            stats_data_id=stats_data_id,
            app_id=app_id,
        )


if __name__ == "__main__":
    main()
