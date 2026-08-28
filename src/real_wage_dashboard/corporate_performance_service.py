from typing import Any

import pandas as pd

from real_wage_dashboard.config import (
    CORPORATE_ANALYSIS_END_YEAR,
    CORPORATE_ANALYSIS_START_YEAR,
    CORPORATE_CAPITAL_CLASSES,
    CORPORATE_INDUSTRIES,
    CORPORATE_ITEMS,
    CORPORATE_STATS_DATA_ID,
)
from real_wage_dashboard.estat_client import get_stats_data


def ensure_list(value: Any) -> list[Any]:
    """値を必ずリストとして返す。"""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def create_corporate_time_codes(
    start_year: int = CORPORATE_ANALYSIS_START_YEAR,
    end_year: int = CORPORATE_ANALYSIS_END_YEAR,
) -> list[str]:
    """分析対象年度のe-Stat時間コードを作成する。"""
    if start_year > end_year:
        raise ValueError("開始年度は終了年度以下である必要があります。")

    return [f"{year}0" for year in range(start_year, end_year + 1)]


def create_item_code_mapping() -> dict[str, str]:
    """e-Statの調査項目コードから分析用列名への対応表を作成する。"""
    return {code: column_name for column_name, code in CORPORATE_ITEMS.items()}


def create_corporate_performance_dataframe(response: dict[str, Any]) -> pd.DataFrame:
    """e-Stat APIレスポンスから法人企業統計の分析用DataFrameを作成する。"""

    values = response["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]

    item_mapping = create_item_code_mapping()

    rows = []

    for item in ensure_list(values):
        item_code = item.get("@cat01")
        column_name = item_mapping.get(item_code)

        if column_name is None:
            continue

        time_code = item.get("@time")

        rows.append(
            {
                "time_code": time_code,
                "fiscal_year": (int(time_code[:4]) if time_code else None),
                "item": column_name,
                "value": item.get("$"),
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame()

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "fiscal_year",
            "item",
            "value",
        ]
    ).copy()

    df["fiscal_year"] = df["fiscal_year"].astype(int)

    df = (
        df.pivot_table(
            index="fiscal_year",
            columns="item",
            values="value",
            aggfunc="last",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    df = df.sort_values("fiscal_year").reset_index(drop=True)

    return df


def add_corporate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """人件費・労働分配率などの派生指標を追加する。"""

    required_columns = {
        "executive_salary",
        "executive_bonus",
        "employee_salary",
        "employee_bonus",
        "welfare_expenses",
        "value_added",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"派生指標の計算に必要な列がありません: {sorted(missing_columns)}"
        )

    result = df.copy()

    result["personnel_expenses"] = (
        result["executive_salary"]
        + result["executive_bonus"]
        + result["employee_salary"]
        + result["employee_bonus"]
        + result["welfare_expenses"]
    )

    result["labor_share"] = result["personnel_expenses"] / result["value_added"] * 100

    result["personnel_expenses_per_employee"] = (
        result["personnel_expenses"] / result["average_employees"] * 100
    )

    result["calculated_labor_productivity"] = (
        result["value_added"] / result["average_employees"] * 100
    )

    result["labor_productivity_diff"] = (
        result["calculated_labor_productivity"] - result["labor_productivity"]
    )

    return result


def load_corporate_performance_dataframe(
    app_id: str,
    industry_code: str = CORPORATE_INDUSTRIES["全産業（除く金融保険業）"],
    capital_class_code: str = CORPORATE_CAPITAL_CLASSES["全規模"],
    start_year: int = CORPORATE_ANALYSIS_START_YEAR,
    end_year: int = CORPORATE_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """法人企業統計を取得し、分析用DataFrameとして返す。"""

    item_codes = ",".join(CORPORATE_ITEMS.values())
    time_codes = ",".join(
        create_corporate_time_codes(
            start_year=start_year,
            end_year=end_year,
        )
    )

    filters = {
        "cdCat01": item_codes,
        "cdCat02": industry_code,
        "cdCat03": capital_class_code,
        "cdTime": time_codes,
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=CORPORATE_STATS_DATA_ID,
        filters=filters,
    )

    df = create_corporate_performance_dataframe(response)

    return add_corporate_derived_metrics(df)
