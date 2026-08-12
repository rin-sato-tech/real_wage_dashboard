import pandas as pd


def add_wage_changes(df: pd.DataFrame) -> pd.DataFrame:
    """現金給与総額の前月比と前年同月比を計算する。"""

    required_columns = {
        "date",
        "nominal_wage_amount",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    result["mom_pct"] = result["nominal_wage_amount"].pct_change().mul(100)

    result["yoy_pct"] = result["nominal_wage_amount"].pct_change(periods=12).mul(100)

    return result
