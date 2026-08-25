from pathlib import Path

import pandas as pd

EFFECTIVE_JOB_OPENINGS_SHEET = "第３表ー１（パート含む）"

# Excel上の季節調整値（月次）の列番号
SEASONALLY_ADJUSTED_MONTH_COLUMNS = {
    20: 1,
    21: 2,
    22: 3,
    23: 4,
    24: 5,
    25: 6,
    26: 7,
    27: 8,
    28: 9,
    29: 10,
    30: 11,
    31: 12,
}


def load_effective_job_openings_excel(
    file_path: str | Path,
) -> pd.DataFrame:
    """有効求人倍率の長期時系列Excelを読み込む。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"有効求人倍率データが見つかりません: {path}")

    return pd.read_excel(
        path,
        sheet_name=EFFECTIVE_JOB_OPENINGS_SHEET,
        header=None,
    )


def create_effective_job_openings_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """有効求人倍率の季節調整済み月次系列を作成する。"""

    required_columns = {
        0,
        *SEASONALLY_ADJUSTED_MONTH_COLUMNS.keys(),
    }

    if not required_columns.issubset(raw_df.columns):
        raise ValueError("有効求人倍率データに必要な列がありません。")

    # 西暦列と季節調整済み月次列だけ取得
    df = raw_df.loc[
        :,
        [0, *SEASONALLY_ADJUSTED_MONTH_COLUMNS.keys()],
    ].copy()

    df = df.rename(columns={0: "year"})

    # 「1963年」→ 1963
    df["year"] = df["year"].astype(str).str.replace("年", "", regex=False).str.strip()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    # ヘッダー等を除外
    df = df.dropna(subset=["year"]).copy()

    df["year"] = df["year"].astype(int)

    # 月別列をわかりやすい名前に変更
    rename_columns = {
        column: f"month_{month}"
        for column, month in SEASONALLY_ADJUSTED_MONTH_COLUMNS.items()
    }
    df = df.rename(columns=rename_columns)

    # 横持ち → 縦持ち
    df = df.melt(
        id_vars="year",
        value_vars=[f"month_{month}" for month in range(1, 13)],
        var_name="month",
        value_name="effective_job_openings_ratio",
    )

    df["month"] = df["month"].str.replace("month_", "", regex=False).astype(int)

    df["effective_job_openings_ratio"] = pd.to_numeric(
        df["effective_job_openings_ratio"],
        errors="coerce",
    )

    df["date"] = pd.to_datetime(
        {
            "year": df["year"],
            "month": df["month"],
            "day": 1,
        }
    )

    # 最新年は年途中なので、未公表月のNaNを除外
    df = (
        df.dropna(subset=["effective_job_openings_ratio"])
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
            "effective_job_openings_ratio",
        ]
    ]


def load_unemployment_rate_excel(
    file_path: str | Path,
) -> pd.DataFrame:
    """完全失業率の長期時系列Excelを読み込む。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"完全失業率データが見つかりません: {path}")

    return pd.read_excel(
        path,
        sheet_name="季節調整値",
        header=None,
    )


def create_unemployment_rate_dataframe(
    raw_df: pd.DataFrame,
) -> pd.DataFrame:
    """完全失業率の季節調整済み月次系列を作成する。"""

    required_columns = {0, 1, 19}

    if not required_columns.issubset(raw_df.columns):
        raise ValueError("完全失業率データに必要な列がありません。")

    df = raw_df.loc[:, [0, 1, 19]].copy()

    df = df.rename(
        columns={
            0: "year_raw",
            1: "month_raw",
            19: "unemployment_rate",
        }
    )

    df["month"] = (
        df["month_raw"].astype(str).str.replace("月", "", regex=False).str.strip()
    )

    df["month"] = pd.to_numeric(
        df["month"],
        errors="coerce",
    )

    df["year_numeric"] = pd.to_numeric(
        df["year_raw"],
        errors="coerce",
    )

    # 西暦は2月行に記載されているため、
    # 2月行の西暦を同年1月にも割り当てる
    df["year"] = df["year_numeric"]

    january_mask = df["month"].eq(1)
    next_year = df["year_numeric"].shift(-1)

    df.loc[january_mask, "year"] = next_year.loc[january_mask]

    # 3月以降は直前の年を引き継ぐ
    df["year"] = df["year"].ffill()

    df["unemployment_rate"] = pd.to_numeric(
        df["unemployment_rate"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "year",
            "month",
            "unemployment_rate",
        ]
    ).copy()

    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)

    df["date"] = pd.to_datetime(
        {
            "year": df["year"],
            "month": df["month"],
            "day": 1,
        },
        errors="coerce",
    )

    df = (
        df.dropna(subset=["date"])
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
            "unemployment_rate",
        ]
    ]


NEW_JOB_OPENINGS_SHEET = "第２表ー１（パート含む）"


def load_new_job_openings_excel(
    file_path: str | Path,
) -> pd.DataFrame:
    """新規求人倍率の長期時系列Excelを読み込む。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"新規求人倍率データが見つかりません: {path}")

    return pd.read_excel(
        path,
        sheet_name=NEW_JOB_OPENINGS_SHEET,
        header=None,
    )


def create_new_job_openings_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """新規求人倍率の季節調整済み月次系列を作成する。"""

    required_columns = {
        0,
        *SEASONALLY_ADJUSTED_MONTH_COLUMNS.keys(),
    }

    if not required_columns.issubset(raw_df.columns):
        raise ValueError("新規求人倍率データに必要な列がありません。")

    df = raw_df.loc[
        :,
        [0, *SEASONALLY_ADJUSTED_MONTH_COLUMNS.keys()],
    ].copy()

    df = df.rename(columns={0: "year"})

    df["year"] = df["year"].astype(str).str.replace("年", "", regex=False).str.strip()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)

    rename_columns = {
        column: f"month_{month}"
        for column, month in SEASONALLY_ADJUSTED_MONTH_COLUMNS.items()
    }
    df = df.rename(columns=rename_columns)

    df = df.melt(
        id_vars="year",
        value_vars=[f"month_{month}" for month in range(1, 13)],
        var_name="month",
        value_name="new_job_openings_ratio",
    )

    df["month"] = df["month"].str.replace("month_", "", regex=False).astype(int)

    df["new_job_openings_ratio"] = pd.to_numeric(
        df["new_job_openings_ratio"],
        errors="coerce",
    )

    df["date"] = pd.to_datetime(
        {
            "year": df["year"],
            "month": df["month"],
            "day": 1,
        }
    )

    df = (
        df.dropna(subset=["new_job_openings_ratio"])
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
            "new_job_openings_ratio",
        ]
    ]


def create_labor_market_dataframe(
    effective_job_openings_df: pd.DataFrame,
    unemployment_rate_df: pd.DataFrame,
    new_job_openings_df: pd.DataFrame,
) -> pd.DataFrame:
    """労働需給の月次指標を日付で結合する。"""

    df = (
        effective_job_openings_df.merge(
            unemployment_rate_df,
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            new_job_openings_df,
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df


def load_tankan_employment_di_csv(
    file_path: str | Path,
) -> pd.DataFrame:
    """日銀短観の雇用人員判断DI CSVを読み込む。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"短観CSVが見つかりません: {path}")

    return pd.read_csv(
        path,
        encoding="cp932",
        skiprows=9,
        header=None,
        names=[
            "period",
            "large_enterprise_employment_di",
            "medium_enterprise_employment_di",
            "small_enterprise_employment_di",
        ],
    )


def create_tankan_employment_di_dataframe(
    raw_df: pd.DataFrame,
) -> pd.DataFrame:
    """短観の雇用人員判断DIを分析用に整形する。"""

    df = raw_df.copy()

    di_columns = [
        "large_enterprise_employment_di",
        "medium_enterprise_employment_di",
        "small_enterprise_employment_di",
    ]

    df["date"] = pd.to_datetime(
        df["period"],
        format="%Y/%m",
        errors="coerce",
    )

    for column in di_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = (
        df.dropna(
            subset=[
                "date",
                *di_columns,
            ]
        )
        .drop_duplicates(
            subset="date",
            keep="last",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df[
        [
            "date",
            *di_columns,
        ]
    ]


def add_tankan_tightness_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """短観の雇用人員判断DIを人手不足方向に符号反転する。"""

    result = df.copy()

    result["large_enterprise_tightness"] = -result["large_enterprise_employment_di"]
    result["medium_enterprise_tightness"] = -result["medium_enterprise_employment_di"]
    result["small_enterprise_tightness"] = -result["small_enterprise_employment_di"]

    return result
