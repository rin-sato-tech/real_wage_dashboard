from pathlib import Path

import pandas as pd


def load_wage_csv(file_path: str | Path) -> pd.DataFrame:
    """毎月勤労統計の長期時系列CSVを読み込む。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"賃金データが見つかりません: {path}")

    return pd.read_csv(path, encoding="cp932")


def create_wage_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """長期時系列表から現金給与総額の月次実数を抽出する。"""

    required_columns = {
        "年",
        "月",
        "産業分類",
        "規模",
        "就業形態",
        "現金給与総額",
    }

    if not required_columns.issubset(raw_df.columns):
        missing = required_columns - set(raw_df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    industry = raw_df["産業分類"].astype(str).str.strip()

    df = raw_df.loc[
        (industry == "TL")
        & (raw_df["規模"] == "T")
        & (raw_df["就業形態"] == 0)
        & (raw_df["月"] != "CY"),
        [
            "年",
            "月",
            "現金給与総額",
        ],
    ].copy()

    df = df.rename(
        columns={
            "現金給与総額": "nominal_wage_amount",
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

    df["nominal_wage_amount"] = pd.to_numeric(
        df["nominal_wage_amount"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip(),
        errors="coerce",
    )

    df = (
        df.dropna(
            subset=[
                "date",
                "nominal_wage_amount",
            ]
        )
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df[
        [
            "date",
            "nominal_wage_amount",
        ]
    ]
