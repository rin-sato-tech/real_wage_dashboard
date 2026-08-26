import pandas as pd

from real_wage_dashboard.config import (
    WAGE_BASE_YEAR,
    WAGE_MOVING_AVERAGE_WINDOW,
)
from real_wage_dashboard.time_series import add_moving_average


def merge_wage_and_cpi(
    wage_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """名目賃金とCPIを年月で内部結合する。"""

    wage_required = {
        "date",
        "nominal_wage_amount",
    }

    cpi_required = {
        "date",
        "index_value",
    }

    if not wage_required.issubset(wage_df.columns):
        missing = wage_required - set(wage_df.columns)
        raise ValueError(f"名目賃金データに必要な列がありません: {sorted(missing)}")

    if not cpi_required.issubset(cpi_df.columns):
        missing = cpi_required - set(cpi_df.columns)
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing)}")

    wage_columns = [
        "date",
        "nominal_wage_amount",
    ]

    if "nominal_wage_ma_12" in wage_df.columns:
        wage_columns.append("nominal_wage_ma_12")

    wage = wage_df[wage_columns].copy()

    cpi = cpi_df[
        [
            "date",
            "index_value",
        ]
    ].copy()

    result = wage.merge(
        cpi,
        on="date",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


def add_real_wage_amount(df: pd.DataFrame) -> pd.DataFrame:
    """CPIで実質化した賃金額を計算する。"""

    required_columns = {
        "nominal_wage_amount",
        "index_value",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    if (result["index_value"] <= 0).any():
        raise ValueError("CPIには0より大きい値が必要です。")

    result["real_wage_amount"] = (
        result["nominal_wage_amount"] / result["index_value"] * 100
    )

    return result


def add_wage_indices(
    df: pd.DataFrame,
    base_year: int = WAGE_BASE_YEAR,
) -> pd.DataFrame:
    """名目賃金と実質賃金を基準年平均=100に指数化する。"""

    required_columns = {
        "date",
        "nominal_wage_amount",
        "real_wage_amount",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    base_df = result[result["date"].dt.year == base_year].copy()

    base_months = base_df["date"].dt.to_period("M").drop_duplicates()

    if len(base_months) != 12:
        raise ValueError(f"{base_year}年の基準データが12か月揃っていません。")

    nominal_base = base_df["nominal_wage_amount"].mean()

    real_base = base_df["real_wage_amount"].mean()

    if nominal_base <= 0 or real_base <= 0:
        raise ValueError("基準年平均は0より大きい必要があります。")

    result["nominal_wage_index"] = result["nominal_wage_amount"] / nominal_base * 100

    result["real_wage_index"] = result["real_wage_amount"] / real_base * 100

    return result


def add_real_wage_moving_average(df: pd.DataFrame) -> pd.DataFrame:
    """実質賃金額の12か月移動平均を追加する。"""

    return add_moving_average(
        df,
        column="real_wage_amount",
        output_column="real_wage_ma_12",
        window=WAGE_MOVING_AVERAGE_WINDOW,
    )


def add_real_wage_index_moving_average(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """実質賃金指数の12か月移動平均を追加する。"""

    return add_moving_average(
        df,
        column="real_wage_index",
        output_column="real_wage_index_ma_12",
        window=WAGE_MOVING_AVERAGE_WINDOW,
    )


def create_real_wage_dataframe(
    wage_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    base_year: int = WAGE_BASE_YEAR,
) -> pd.DataFrame:
    """名目賃金とCPIを結合し、実質賃金を計算する。"""

    result = merge_wage_and_cpi(
        wage_df,
        cpi_df,
    )

    result = add_real_wage_amount(result)

    result = add_wage_indices(
        result,
        base_year=base_year,
    )

    result = add_real_wage_moving_average(result)

    result = add_real_wage_index_moving_average(result)

    return result


def add_real_wage_changes(df: pd.DataFrame) -> pd.DataFrame:
    """実質賃金の前月比と前年同月比を計算する。"""

    required_columns = {
        "date",
        "real_wage_amount",
        "real_wage_index",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    result["real_wage_mom_pct"] = (
        result["real_wage_amount"].pct_change(fill_method=None).mul(100)
    )

    result["real_wage_yoy_pct"] = (
        result["real_wage_amount"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    return result
