from __future__ import annotations

from typing import Any

import pandas as pd

from real_wage_dashboard.config import (
    SNA_ANALYSIS_END_YEAR,
    SNA_ANALYSIS_START_YEAR,
    SNA_HOUSEHOLD_PRIMARY_INCOME_ITEMS,
    SNA_HOUSEHOLD_PRIMARY_INCOME_STATS_DATA_ID,
    SNA_HOUSEHOLD_SECONDARY_DISTRIBUTION_ITEMS,
    SNA_HOUSEHOLD_SECONDARY_DISTRIBUTION_STATS_DATA_ID,
    SNA_HOUSEHOLD_USE_INCOME_ITEMS,
    SNA_HOUSEHOLD_USE_INCOME_STATS_DATA_ID,
    SNA_INCOME_GENERATION_ITEMS,
    SNA_INCOME_GENERATION_STATS_DATA_ID,
    SNA_NONFINANCIAL_CAPITAL_ACCOUNT_ITEMS,
    SNA_NONFINANCIAL_CAPITAL_ACCOUNT_STATS_DATA_ID,
    SNA_NONFINANCIAL_FINANCIAL_ACCOUNT_ITEMS,
    SNA_NONFINANCIAL_FINANCIAL_ACCOUNT_STATS_DATA_ID,
    SNA_SECTOR_NET_LENDING_AMOUNT_STATS_DATA_ID,
    SNA_SECTOR_NET_LENDING_ITEMS,
    SNA_SECTOR_NET_LENDING_RATIO_STATS_DATA_ID,
)
from real_wage_dashboard.estat_client import get_stats_data
from real_wage_dashboard.estat_response import ensure_list


def create_sna_time_codes(
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> list[str]:
    """SNA年度系列のe-Stat時間コードを作成する。"""
    if start_year > end_year:
        raise ValueError("開始年度は終了年度以下である必要があります。")

    return [f"{year}100000" for year in range(start_year, end_year + 1)]


def create_sna_item_code_mapping(
    items: dict[str, str],
) -> dict[str, str]:
    """e-Stat項目コードから分析用列名への対応表を作成する。"""
    return {code: column_name for column_name, code in items.items()}


def create_sna_dataframe(
    response: dict[str, Any],
    items: dict[str, str],
) -> pd.DataFrame:
    """SNAのe-Statレスポンスを年度×項目のDataFrameへ変換する。"""

    values = response["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

    item_mapping = create_sna_item_code_mapping(items)

    rows: list[dict[str, Any]] = []

    for value in ensure_list(values):
        item_code = value.get("@cat01")
        column_name = item_mapping.get(item_code)

        if column_name is None:
            continue

        time_code = value.get("@time")

        if not time_code or len(time_code) < 4:
            continue

        rows.append(
            {
                "time_code": time_code,
                "fiscal_year": int(time_code[:4]),
                "item": column_name,
                "value": value.get("$"),
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    duplicate_mask = df.duplicated(
        subset=["fiscal_year", "item"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = (
            df.loc[
                duplicate_mask,
                ["fiscal_year", "item"],
            ]
            .drop_duplicates()
            .to_dict("records")
        )

        raise ValueError(f"SNAデータに年度・項目の重複があります: {duplicates}")

    result = (
        df.pivot(
            index="fiscal_year",
            columns="item",
            values="value",
        )
        .reset_index()
        .rename_axis(columns=None)
        .sort_values("fiscal_year")
        .reset_index(drop=True)
    )

    return result


def load_sna_table(
    app_id: str,
    stats_data_id: str,
    items: dict[str, str],
    tab_code: str = "11",
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """指定したSNA年度表を取得し分析用DataFrameとして返す。"""

    item_codes = ",".join(items.values())

    time_codes = ",".join(
        create_sna_time_codes(
            start_year=start_year,
            end_year=end_year,
        )
    )

    filters = {
        "cdTab": tab_code,
        "cdCat01": item_codes,
        "cdTime": time_codes,
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=stats_data_id,
        filters=filters,
    )

    return create_sna_dataframe(
        response=response,
        items=items,
    )


def load_income_generation(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """一国経済・所得の発生勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_INCOME_GENERATION_STATS_DATA_ID,
        items=SNA_INCOME_GENERATION_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_household_primary_income(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """家計・第1次所得の配分勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_HOUSEHOLD_PRIMARY_INCOME_STATS_DATA_ID,
        items=SNA_HOUSEHOLD_PRIMARY_INCOME_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_household_secondary_distribution(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """家計・所得の第2次分配勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_HOUSEHOLD_SECONDARY_DISTRIBUTION_STATS_DATA_ID,
        items=SNA_HOUSEHOLD_SECONDARY_DISTRIBUTION_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_household_use_income(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """家計・可処分所得の使用勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_HOUSEHOLD_USE_INCOME_STATS_DATA_ID,
        items=SNA_HOUSEHOLD_USE_INCOME_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_nonfinancial_capital_account(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """非金融法人企業・資本勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_NONFINANCIAL_CAPITAL_ACCOUNT_STATS_DATA_ID,
        items=SNA_NONFINANCIAL_CAPITAL_ACCOUNT_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_nonfinancial_financial_account(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """非金融法人企業・金融勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_NONFINANCIAL_FINANCIAL_ACCOUNT_STATS_DATA_ID,
        items=SNA_NONFINANCIAL_FINANCIAL_ACCOUNT_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_sector_net_lending_amount(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """制度部門別純貸出・純借入の金額系列を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_SECTOR_NET_LENDING_AMOUNT_STATS_DATA_ID,
        items=SNA_SECTOR_NET_LENDING_ITEMS,
        tab_code="11",
        start_year=start_year,
        end_year=end_year,
    )


def load_sector_net_lending_ratio(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """制度部門別純貸出・純借入のGDP比系列を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_SECTOR_NET_LENDING_RATIO_STATS_DATA_ID,
        items=SNA_SECTOR_NET_LENDING_ITEMS,
        tab_code="30",
        start_year=start_year,
        end_year=end_year,
    )
