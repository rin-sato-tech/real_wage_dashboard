"""毎月勤労統計の長期時系列表に共通する月次抽出処理。"""

import pandas as pd


def extract_monthly_labor_series(
    raw_df: pd.DataFrame,
    *,
    item: str,
    value_column: str,
    label: str,
    establishment_size: str,
    employment_type: str,
    industry_code: str,
) -> pd.DataFrame:
    """指定系列を数値化し、有効な月次観測を日付順に返す。

    年平均（CY）と無効な観測を除外し、同じ月の有効な行は末尾を採用する。
    入力は変更しない。領域別の既定条件と列名は呼び出し側で指定する。
    """

    required_columns = {
        "年",
        "月",
        "産業分類",
        "規模",
        "就業形態",
        item,
    }

    if not required_columns.issubset(raw_df.columns):
        missing = required_columns - set(raw_df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    industry = raw_df["産業分類"].astype(str).str.strip()
    size = raw_df["規模"].astype(str).str.strip()
    employment = raw_df["就業形態"].astype(str).str.strip()
    month = raw_df["月"].astype(str).str.strip()

    df = raw_df.loc[
        (industry == industry_code)
        & (size == establishment_size)
        & (employment == employment_type)
        & (month != "CY"),
        [
            "年",
            "月",
            item,
        ],
    ].copy()

    if df.empty:
        raise ValueError(f"選択した条件に該当する{label}データがありません。")

    df = df.rename(columns={item: value_column})

    df["year"] = pd.to_numeric(
        df["年"],
        errors="coerce",
    )

    df["month"] = pd.to_numeric(
        df["月"],
        errors="coerce",
    )

    df["date"] = pd.to_datetime(
        {
            "year": df["year"],
            "month": df["month"],
            "day": 1,
        },
        errors="coerce",
    )

    df[value_column] = pd.to_numeric(
        df[value_column].astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )

    df = (
        df.dropna(
            subset=[
                "date",
                value_column,
            ]
        )
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError(f"選択した条件では有効な{label}データを取得できません。")

    return df[
        [
            "date",
            value_column,
        ]
    ]
