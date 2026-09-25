from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from real_wage_dashboard.config import (
    SNA_HOUSEHOLD_PRIMARY_INCOME_STATS_DATA_ID,
    SNA_HOUSEHOLD_SECONDARY_DISTRIBUTION_STATS_DATA_ID,
    SNA_HOUSEHOLD_USE_INCOME_STATS_DATA_ID,
    SNA_INCOME_GENERATION_STATS_DATA_ID,
    SNA_NONFINANCIAL_CAPITAL_ACCOUNT_STATS_DATA_ID,
    SNA_NONFINANCIAL_FINANCIAL_ACCOUNT_STATS_DATA_ID,
    SNA_SECTOR_NET_LENDING_AMOUNT_STATS_DATA_ID,
    SNA_SECTOR_NET_LENDING_RATIO_STATS_DATA_ID,
)
from real_wage_dashboard.estat_client import get_meta_info
from real_wage_dashboard.estat_response import ensure_list


ROOT_DIR = Path(__file__).resolve().parents[2]
SECRETS_PATH = ROOT_DIR / ".streamlit" / "secrets.toml"


TABLES = {
    "所得の発生勘定": SNA_INCOME_GENERATION_STATS_DATA_ID,
    "家計・第1次所得の配分勘定": SNA_HOUSEHOLD_PRIMARY_INCOME_STATS_DATA_ID,
    "家計・所得の第2次分配勘定": (
        SNA_HOUSEHOLD_SECONDARY_DISTRIBUTION_STATS_DATA_ID
    ),
    "家計・可処分所得の使用勘定": SNA_HOUSEHOLD_USE_INCOME_STATS_DATA_ID,
    "非金融法人企業・資本勘定": SNA_NONFINANCIAL_CAPITAL_ACCOUNT_STATS_DATA_ID,
    "非金融法人企業・金融勘定": (
        SNA_NONFINANCIAL_FINANCIAL_ACCOUNT_STATS_DATA_ID
    ),
    "制度部門別純貸出・純借入（金額）": (
        SNA_SECTOR_NET_LENDING_AMOUNT_STATS_DATA_ID
    ),
    "制度部門別純貸出・純借入（GDP比）": (
        SNA_SECTOR_NET_LENDING_RATIO_STATS_DATA_ID
    ),
}


def load_estat_app_id() -> str:
    """環境変数またはStreamlit secretsからe-Stat API IDを取得する。"""
    env_app_id = os.getenv("ESTAT_APP_ID")

    if env_app_id:
        return env_app_id

    if not SECRETS_PATH.exists():
        raise FileNotFoundError(
            "ESTAT_APP_IDが環境変数にも"
            ".streamlit/secrets.tomlにも設定されていません。"
        )

    with SECRETS_PATH.open("rb") as file:
        secrets = tomllib.load(file)

    try:
        return str(secrets["ESTAT_APP_ID"])
    except KeyError as exc:
        raise KeyError(
            ".streamlit/secrets.tomlにESTAT_APP_IDがありません。"
        ) from exc


def print_class_object(class_obj: dict[str, Any]) -> None:
    """1つの分類軸とコード一覧を表示する。"""
    class_id = class_obj.get("@id")
    class_name = class_obj.get("@name")

    print(f"\n  [{class_id}] {class_name}")

    for item in ensure_list(class_obj.get("CLASS")):
        code = item.get("@code")
        name = item.get("@name")
        unit = item.get("@unit")
        level = item.get("@level")

        extras = []

        if level is not None:
            extras.append(f"level={level}")

        if unit is not None:
            extras.append(f"unit={unit}")

        suffix = f" ({', '.join(extras)})" if extras else ""

        print(f"    {code}: {name}{suffix}")


def print_table_metadata(
    app_id: str,
    table_name: str,
    stats_data_id: str,
) -> None:
    """指定統計表の分類軸・コードを表示する。"""
    print("\n" + "=" * 100)
    print(f"{table_name}")
    print(f"statsDataId: {stats_data_id}")
    print("=" * 100)

    response = get_meta_info(
        app_id=app_id,
        stats_data_id=stats_data_id,
    )

    metadata = response["GET_META_INFO"]["METADATA_INF"]

    table_inf = metadata.get("TABLE_INF", {})

    print(f"表題: {table_inf.get('TITLE')}")
    print(f"政府統計名: {table_inf.get('STAT_NAME')}")

    class_inf = metadata["CLASS_INF"]

    for class_obj in ensure_list(class_inf.get("CLASS_OBJ")):
        print_class_object(class_obj)


def main() -> None:
    app_id = load_estat_app_id()

    for table_name, stats_data_id in TABLES.items():
        print_table_metadata(
            app_id=app_id,
            table_name=table_name,
            stats_data_id=stats_data_id,
        )


if __name__ == "__main__":
    main()
