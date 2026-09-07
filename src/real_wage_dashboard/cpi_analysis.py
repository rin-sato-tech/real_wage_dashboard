import pandas as pd

from real_wage_dashboard.time_series import add_monthly_changes, add_moving_average


def add_cpi_changes(df: pd.DataFrame) -> pd.DataFrame:
    """CPI指数から前月比と前年同月比を計算する。"""

    return add_monthly_changes(df, column="index_value")


def add_cpi_moving_average(df: pd.DataFrame) -> pd.DataFrame:
    """CPI指数の12か月移動平均を追加する。"""

    return add_moving_average(
        df,
        column="index_value",
        output_column="index_value_ma_12",
        window=12,
    )


def prepare_annual_cpi(
    cpi_df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> pd.DataFrame:
    """月次CPIから年平均CPIを作成する。"""

    required_columns = {
        "date",
        "index_value",
    }

    missing = required_columns - set(cpi_df.columns)

    if missing:
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing)}")

    work = cpi_df.copy()

    work["year"] = work["date"].dt.year

    work = work.loc[
        work["year"].between(
            start_year,
            end_year,
        )
    ].copy()

    annual = (
        work.groupby(
            "year",
            as_index=False,
        )
        .agg(
            cpi=("index_value", "mean"),
            month_count=("index_value", "count"),
        )
        .sort_values("year")
        .reset_index(drop=True)
    )

    incomplete = annual.loc[annual["month_count"] != 12]

    if not incomplete.empty:
        raise ValueError(
            "12か月揃っていないCPI年次データがあります: "
            f"{incomplete[['year', 'month_count']].to_dict('records')}"
        )

    return annual[
        [
            "year",
            "cpi",
        ]
    ]
