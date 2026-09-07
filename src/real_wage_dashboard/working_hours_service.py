import pandas as pd

from real_wage_dashboard.monthly_labor_service import extract_monthly_labor_series


def create_working_hours_dataframe(
    raw_df: pd.DataFrame,
    working_hours_item: str = "総実労働時間",
    establishment_size: str = "T",
    employment_type: str = "1",
    industry_code: str = "TL",
) -> pd.DataFrame:
    """長期時系列表から指定条件の月次労働時間データを抽出する。"""

    return extract_monthly_labor_series(
        raw_df,
        item=working_hours_item,
        value_column="working_hours",
        label="労働時間",
        establishment_size=establishment_size,
        employment_type=employment_type,
        industry_code=industry_code,
    )
