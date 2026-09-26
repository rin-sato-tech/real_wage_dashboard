from __future__ import annotations

from typing import Any

import pandas as pd

from real_wage_dashboard.config import (
    CORPORATE_ANALYSIS_END_YEAR,
    CORPORATE_ANALYSIS_START_YEAR,
    CORPORATE_CAPITAL_CLASSES,
    CORPORATE_INDUSTRIES,
    CORPORATE_PROFIT_ALLOCATION_ITEMS,
    CORPORATE_STATS_DATA_ID,
    SNA_ANALYSIS_END_YEAR,
    SNA_ANALYSIS_START_YEAR,
    SNA_FINANCIAL_ASSETS_DETAIL_ITEMS,
    SNA_FINANCIAL_ASSETS_DETAIL_STATS_DATA_ID,
    SNA_FINANCIAL_LIABILITIES_DETAIL_ITEMS,
    SNA_FINANCIAL_LIABILITIES_DETAIL_STATS_DATA_ID,
    SNA_NONFINANCIAL_BALANCE_SHEET_ITEMS,
    SNA_NONFINANCIAL_BALANCE_SHEET_STATS_DATA_ID,
    SNA_NONFINANCIAL_CORPORATIONS_SECTOR_CODE,
    SNA_NONFINANCIAL_OTHER_VOLUME_CHANGES_ITEMS,
    SNA_NONFINANCIAL_OTHER_VOLUME_CHANGES_STATS_DATA_ID,
    SNA_NONFINANCIAL_PRIMARY_INCOME_ITEMS,
    SNA_NONFINANCIAL_PRIMARY_INCOME_STATS_DATA_ID,
    SNA_NONFINANCIAL_REVALUATION_ITEMS,
    SNA_NONFINANCIAL_REVALUATION_STATS_DATA_ID,
    SNA_NONFINANCIAL_SECONDARY_DISTRIBUTION_ITEMS,
    SNA_NONFINANCIAL_SECONDARY_DISTRIBUTION_STATS_DATA_ID,
    SNA_NONFINANCIAL_USE_INCOME_ITEMS,
    SNA_NONFINANCIAL_USE_INCOME_STATS_DATA_ID,
)
from real_wage_dashboard.estat_client import get_stats_data
from real_wage_dashboard.estat_response import ensure_list
from real_wage_dashboard.macro_distribution_service import (
    create_sna_dataframe,
    load_sna_table,
)


def load_nonfinancial_primary_income(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """非金融法人企業の第1次所得の配分勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_NONFINANCIAL_PRIMARY_INCOME_STATS_DATA_ID,
        items=SNA_NONFINANCIAL_PRIMARY_INCOME_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_nonfinancial_secondary_distribution(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """非金融法人企業の所得の第2次分配勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_NONFINANCIAL_SECONDARY_DISTRIBUTION_STATS_DATA_ID,
        items=SNA_NONFINANCIAL_SECONDARY_DISTRIBUTION_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_nonfinancial_use_income(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """非金融法人企業の可処分所得の使用勘定を取得する。"""

    return load_sna_table(
        app_id=app_id,
        stats_data_id=SNA_NONFINANCIAL_USE_INCOME_STATS_DATA_ID,
        items=SNA_NONFINANCIAL_USE_INCOME_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_sna_financial_detail_table(
    app_id: str,
    stats_data_id: str,
    items: dict[str, str],
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """制度部門別の詳細金融取引表を取得する。"""

    if start_year > end_year:
        raise ValueError(
            "開始年度は終了年度以下である必要があります。"
        )

    filters = {
        "cdTab": "11",
        "cdCat01": ",".join(items.values()),
        "cdCat02": SNA_NONFINANCIAL_CORPORATIONS_SECTOR_CODE,
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=stats_data_id,
        filters=filters,
    )

    result = create_sna_dataframe(
        response=response,
        items=items,
    )

    if result.empty:
        return result

    return (
        result[
            result["fiscal_year"].between(
                start_year,
                end_year,
            )
        ]
        .reset_index(drop=True)
    )


def load_nonfinancial_financial_assets_detail(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """非金融法人企業の詳細金融資産取引を取得する。"""

    return load_sna_financial_detail_table(
        app_id=app_id,
        stats_data_id=(
            SNA_FINANCIAL_ASSETS_DETAIL_STATS_DATA_ID
        ),
        items=SNA_FINANCIAL_ASSETS_DETAIL_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_nonfinancial_financial_liabilities_detail(
    app_id: str,
    start_year: int = SNA_ANALYSIS_START_YEAR,
    end_year: int = SNA_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """非金融法人企業の詳細負債取引を取得する。"""

    return load_sna_financial_detail_table(
        app_id=app_id,
        stats_data_id=(
            SNA_FINANCIAL_LIABILITIES_DETAIL_STATS_DATA_ID
        ),
        items=SNA_FINANCIAL_LIABILITIES_DETAIL_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_sna_calendar_table(
    app_id: str,
    stats_data_id: str,
    items: dict[str, str],
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """SNAストック編の暦年・暦年末系列を取得する。"""

    if start_year > end_year:
        raise ValueError(
            "開始年は終了年以下である必要があります。"
        )

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=stats_data_id,
        filters={
            "cdTab": "11",
            "cdCat01": ",".join(items.values()),
        },
    )

    result = create_sna_dataframe(
        response=response,
        items=items,
    )

    if result.empty:
        return result

    result = result.rename(
        columns={
            "fiscal_year": "calendar_year",
        }
    )

    return (
        result[
            result["calendar_year"].between(
                start_year,
                end_year,
            )
        ]
        .sort_values("calendar_year")
        .reset_index(drop=True)
    )


def load_nonfinancial_balance_sheet(
    app_id: str,
    start_year: int = 1994,
    end_year: int = 2024,
) -> pd.DataFrame:
    """非金融法人企業の期末貸借対照表を取得する。"""

    return load_sna_calendar_table(
        app_id=app_id,
        stats_data_id=SNA_NONFINANCIAL_BALANCE_SHEET_STATS_DATA_ID,
        items=SNA_NONFINANCIAL_BALANCE_SHEET_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_nonfinancial_other_volume_changes(
    app_id: str,
    start_year: int = 1994,
    end_year: int = 2024,
) -> pd.DataFrame:
    """非金融法人企業のその他の資産量変動勘定を取得する。"""

    return load_sna_calendar_table(
        app_id=app_id,
        stats_data_id=(
            SNA_NONFINANCIAL_OTHER_VOLUME_CHANGES_STATS_DATA_ID
        ),
        items=SNA_NONFINANCIAL_OTHER_VOLUME_CHANGES_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def load_nonfinancial_revaluation(
    app_id: str,
    start_year: int = 1994,
    end_year: int = 2024,
) -> pd.DataFrame:
    """非金融法人企業の再評価勘定を取得する。"""

    return load_sna_calendar_table(
        app_id=app_id,
        stats_data_id=SNA_NONFINANCIAL_REVALUATION_STATS_DATA_ID,
        items=SNA_NONFINANCIAL_REVALUATION_ITEMS,
        start_year=start_year,
        end_year=end_year,
    )


def create_corporate_profit_allocation_dataframe(
    response: dict[str, Any],
) -> pd.DataFrame:
    """法人企業統計から企業利益配分分析用DataFrameを作成する。"""

    values = (
        response["GET_STATS_DATA"]
        ["STATISTICAL_DATA"]
        ["DATA_INF"]
        ["VALUE"]
    )

    item_mapping = {
        code: column
        for column, code
        in CORPORATE_PROFIT_ALLOCATION_ITEMS.items()
    }

    rows = []

    for value in ensure_list(values):
        item_code = value.get("@cat01")
        column = item_mapping.get(item_code)

        if column is None:
            continue

        time_code = value.get("@time")

        if not time_code or len(time_code) < 4:
            continue

        rows.append(
            {
                "fiscal_year": int(time_code[:4]),
                "item": column,
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

        raise ValueError(
            "法人企業統計に年度・項目の重複があります: "
            f"{duplicates}"
        )

    return (
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


def load_corporate_profit_allocation(
    app_id: str,
    start_year: int = CORPORATE_ANALYSIS_START_YEAR,
    end_year: int = CORPORATE_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """法人企業統計の利益配分・主要BS項目を取得する。"""

    item_codes = ",".join(
        CORPORATE_PROFIT_ALLOCATION_ITEMS.values()
    )

    time_codes = ",".join(
        f"{year}0"
        for year in range(
            start_year,
            end_year + 1,
        )
    )

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=CORPORATE_STATS_DATA_ID,
        filters={
            "cdCat01": item_codes,
            "cdCat02": (
                CORPORATE_INDUSTRIES[
                    "全産業（除く金融保険業）"
                ]
            ),
            "cdCat03": (
                CORPORATE_CAPITAL_CLASSES["全規模"]
            ),
            "cdTime": time_codes,
        },
    )

    return create_corporate_profit_allocation_dataframe(
        response
    )
