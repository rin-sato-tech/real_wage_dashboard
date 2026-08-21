import pandas as pd


def create_working_hours_dataframe(
    raw_df: pd.DataFrame,
    working_hours_item: str = "総実労働時間",
    establishment_size: str = "T",
    employment_type: str = "1",
    industry_code: str = "TL",
) -> pd.DataFrame:
    """長期時系列表から指定条件の月次労働時間データを抽出する。"""

    required_columns = {
        "年",
        "月",
        "産業分類",
        "規模",
        "就業形態",
        working_hours_item,
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
        ["年", "月", working_hours_item],
    ].copy()

    if df.empty:
        raise ValueError("選択した条件に該当する労働時間データがありません。")

    df = df.rename(
        columns={
            working_hours_item: "working_hours",
        }
    )

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

    df["working_hours"] = pd.to_numeric(
        df["working_hours"].astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )

    df = (
        df.dropna(
            subset=[
                "date",
                "working_hours",
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
        raise ValueError("選択した条件では有効な労働時間データを取得できません。")

    return df[
        [
            "date",
            "working_hours",
        ]
    ]
