import pandas as pd

from real_wage_dashboard.monthly_labor_service import extract_monthly_labor_series


def create_working_days_dataframe(
    raw_df: pd.DataFrame,
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """長期時系列表から指定条件の月次出勤日数データを抽出する。"""

    return extract_monthly_labor_series(
        raw_df,
        item="出勤日数",
        value_column="working_days",
        label="出勤日数",
        establishment_size=establishment_size,
        employment_type=employment_type,
        industry_code="TL",
    )
