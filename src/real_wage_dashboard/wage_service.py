from pathlib import Path

import pandas as pd

from real_wage_dashboard.monthly_labor_service import extract_monthly_labor_series


def load_wage_csv(file_path: str | Path) -> pd.DataFrame:
    """毎月勤労統計の長期時系列CSVを読み込む。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"賃金データが見つかりません: {path}")

    return pd.read_csv(
        path,
        encoding="cp932",
        dtype={
            "月": str,
        },
    )


def create_wage_dataframe(
    raw_df: pd.DataFrame,
    wage_item: str = "現金給与総額",
    establishment_size: str = "T",
    employment_type: str = "0",
    industry_code: str = "TL",
) -> pd.DataFrame:
    """長期時系列表から指定条件の月次賃金データを抽出する。"""

    return extract_monthly_labor_series(
        raw_df,
        item=wage_item,
        value_column="nominal_wage_amount",
        label="賃金",
        establishment_size=establishment_size,
        employment_type=employment_type,
        industry_code=industry_code,
    )
