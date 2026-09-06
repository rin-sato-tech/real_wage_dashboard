from __future__ import annotations

import pandas as pd

BASE_YEAR = 2015

QUANTILE_COLUMNS = [
    "p10",
    "p25",
    "p50",
    "p75",
    "p90",
]


def validate_wage_distribution_data(
    df: pd.DataFrame,
) -> None:
    required_columns = {
        "year",
        *QUANTILE_COLUMNS,
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"必要な列がありません: {sorted(missing_columns)}")

    if df.empty:
        raise ValueError("賃金分布データが空です。")

    if df["year"].duplicated().any():
        raise ValueError("year が重複しています。")

    if df[QUANTILE_COLUMNS].isna().any().any():
        raise ValueError("分位値に欠損があります。")

    if (df[QUANTILE_COLUMNS] <= 0).any().any():
        raise ValueError("分位値には正の値が必要です。")

    ordered = (
        (df["p10"] <= df["p25"])
        & (df["p25"] <= df["p50"])
        & (df["p50"] <= df["p75"])
        & (df["p75"] <= df["p90"])
    )

    if not ordered.all():
        raise ValueError("P10 <= P25 <= P50 <= P75 <= P90 を満たさない年があります。")


def build_wage_distribution_analysis(
    df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    validate_wage_distribution_data(df)

    result = df.copy().sort_values("year").reset_index(drop=True)

    base_rows = result[result["year"] == base_year]

    if len(base_rows) != 1:
        raise ValueError(f"基準年 {base_year} が一意に存在しません。")

    base_row = base_rows.iloc[0]

    for column in QUANTILE_COLUMNS:
        result[f"{column}_index"] = result[column] / base_row[column] * 100

    result["p90_p10"] = result["p90"] / result["p10"]
    result["p90_p50"] = result["p90"] / result["p50"]
    result["p50_p10"] = result["p50"] / result["p10"]

    return result


def summarize_wage_distribution_change(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> pd.DataFrame:
    validate_wage_distribution_data(df)

    start_rows = df[df["year"] == start_year]
    end_rows = df[df["year"] == end_year]

    if len(start_rows) != 1:
        raise ValueError(f"開始年 {start_year} が一意に存在しません。")

    if len(end_rows) != 1:
        raise ValueError(f"終了年 {end_year} が一意に存在しません。")

    start_row = start_rows.iloc[0]
    end_row = end_rows.iloc[0]

    rows = []

    for column in QUANTILE_COLUMNS:
        start_value = float(start_row[column])
        end_value = float(end_row[column])

        rows.append(
            {
                "quantile": column.upper(),
                "start_year": start_year,
                "end_year": end_year,
                "start_value": start_value,
                "end_value": end_value,
                "change_rate": (end_value / start_value - 1),
            }
        )

    return pd.DataFrame(rows)
