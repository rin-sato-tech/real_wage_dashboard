import numpy as np
import pandas as pd

from real_wage_dashboard.wage_service import create_wage_dataframe
from real_wage_dashboard.working_days_service import (
    create_working_days_dataframe,
)
from real_wage_dashboard.working_hours_service import (
    create_working_hours_dataframe,
)


def create_labor_input_dataframe(
    raw_df: pd.DataFrame,
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """労働投入分析に必要な基礎系列と派生指標を作成する。"""

    wage_df = create_wage_dataframe(
        raw_df,
        wage_item="きまって支給する給与",
        establishment_size=establishment_size,
        employment_type=employment_type,
    )

    total_hours_df = create_working_hours_dataframe(
        raw_df,
        working_hours_item="総実労働時間",
        establishment_size=establishment_size,
        employment_type=employment_type,
    ).rename(
        columns={
            "working_hours": "total_hours",
        }
    )

    scheduled_hours_df = create_working_hours_dataframe(
        raw_df,
        working_hours_item="所定内労働時間",
        establishment_size=establishment_size,
        employment_type=employment_type,
    ).rename(
        columns={
            "working_hours": "scheduled_hours",
        }
    )

    overtime_hours_df = create_working_hours_dataframe(
        raw_df,
        working_hours_item="所定外労働時間",
        establishment_size=establishment_size,
        employment_type=employment_type,
    ).rename(
        columns={
            "working_hours": "overtime_hours",
        }
    )

    working_days_df = create_working_days_dataframe(
        raw_df,
        establishment_size=establishment_size,
        employment_type=employment_type,
    )

    result = (
        wage_df.merge(
            total_hours_df,
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            scheduled_hours_df,
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            overtime_hours_df,
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            working_days_df,
            on="date",
            how="inner",
            validate="one_to_one",
        )
    )

    result["approx_hourly_wage"] = result["nominal_wage_amount"] / result["total_hours"]

    result["scheduled_hours_per_workday"] = (
        result["scheduled_hours"] / result["working_days"]
    )

    return result


def add_year_over_year_pct(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """12暦月前の値が存在する場合のみ前年比を計算する。"""

    result = df.copy()

    previous = result[["date", *columns]].copy()

    previous["date"] = previous["date"] + pd.DateOffset(years=1)

    previous = previous.rename(
        columns={column: f"{column}_previous_year" for column in columns}
    )

    result = result.merge(
        previous,
        on="date",
        how="left",
        validate="one_to_one",
    )

    for column in columns:
        previous_column = f"{column}_previous_year"

        result[f"{column}_yoy_pct"] = (
            result[column] / result[previous_column] - 1
        ) * 100

        result = result.drop(columns=[previous_column])

    return result


def add_wage_decomposition(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """月額賃金の前年比変化を時間単価と労働時間へ対数分解する。"""

    result = df.copy()

    previous = result[
        [
            "date",
            "nominal_wage_amount",
            "approx_hourly_wage",
            "total_hours",
        ]
    ].copy()

    previous["date"] = previous["date"] + pd.DateOffset(years=1)

    previous = previous.rename(
        columns={
            "nominal_wage_amount": "nominal_wage_amount_previous_year",
            "approx_hourly_wage": "approx_hourly_wage_previous_year",
            "total_hours": "total_hours_previous_year",
        }
    )

    result = result.merge(
        previous,
        on="date",
        how="left",
        validate="one_to_one",
    )

    result["wage_log_change"] = (
        np.log(
            result["nominal_wage_amount"] / result["nominal_wage_amount_previous_year"]
        )
        * 100
    )

    result["hourly_wage_log_contribution"] = (
        np.log(
            result["approx_hourly_wage"] / result["approx_hourly_wage_previous_year"]
        )
        * 100
    )

    result["total_hours_log_contribution"] = (
        np.log(result["total_hours"] / result["total_hours_previous_year"]) * 100
    )

    result = result.drop(
        columns=[
            "nominal_wage_amount_previous_year",
            "approx_hourly_wage_previous_year",
            "total_hours_previous_year",
        ]
    )

    return result


def summarize_long_term_wage_decomposition(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> dict[str, float]:
    """年平均を用いて月額賃金変化を時間単価と労働時間へ分解する。"""

    start_df = df.loc[df["date"].dt.year == start_year]
    end_df = df.loc[df["date"].dt.year == end_year]

    if len(start_df) != 12 or len(end_df) != 12:
        raise ValueError("長期比較には開始年・終了年ともに12か月分のデータが必要です。")

    start_wage = start_df["nominal_wage_amount"].mean()
    end_wage = end_df["nominal_wage_amount"].mean()

    start_hours = start_df["total_hours"].mean()
    end_hours = end_df["total_hours"].mean()

    # 年間の賃金総額 ÷ 年間の総実労働時間
    # 年平均月額賃金 = 加重概算時間当たり賃金 × 年平均労働時間
    # が厳密に成立するようにする。
    start_hourly = start_df["nominal_wage_amount"].sum() / start_df["total_hours"].sum()
    end_hourly = end_df["nominal_wage_amount"].sum() / end_df["total_hours"].sum()

    wage_change_pct = ((end_wage / start_wage) - 1) * 100

    hourly_change_pct = ((end_hourly / start_hourly) - 1) * 100

    hours_change_pct = ((end_hours / start_hours) - 1) * 100

    wage_log_change = np.log(end_wage / start_wage) * 100

    hourly_log_contribution = np.log(end_hourly / start_hourly) * 100

    hours_log_contribution = np.log(end_hours / start_hours) * 100

    return {
        "start_year": start_year,
        "end_year": end_year,
        "start_wage": start_wage,
        "end_wage": end_wage,
        "start_hourly_wage": start_hourly,
        "end_hourly_wage": end_hourly,
        "start_total_hours": start_hours,
        "end_total_hours": end_hours,
        "wage_change_pct": wage_change_pct,
        "hourly_wage_change_pct": hourly_change_pct,
        "total_hours_change_pct": hours_change_pct,
        "wage_log_change": wage_log_change,
        "hourly_wage_log_contribution": hourly_log_contribution,
        "total_hours_log_contribution": hours_log_contribution,
    }


def create_yearly_wage_decomposition(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """年平均を用いて月額賃金の前年比変化を要因分解する。"""

    yearly = (
        df.assign(year=df["date"].dt.year)
        .groupby("year", as_index=False)
        .agg(
            nominal_wage_amount=("nominal_wage_amount", "mean"),
            total_hours=("total_hours", "mean"),
            annual_wage_sum=("nominal_wage_amount", "sum"),
            annual_hours_sum=("total_hours", "sum"),
            month_count=("date", "count"),
        )
    )

    # 12か月揃っている年だけ分析対象とする
    yearly = yearly.loc[yearly["month_count"] == 12].copy()

    yearly["weighted_approx_hourly_wage"] = (
        yearly["annual_wage_sum"] / yearly["annual_hours_sum"]
    )

    yearly["wage_change_pct"] = yearly["nominal_wage_amount"].pct_change() * 100

    yearly["hourly_wage_change_pct"] = (
        yearly["weighted_approx_hourly_wage"].pct_change() * 100
    )

    yearly["total_hours_change_pct"] = yearly["total_hours"].pct_change() * 100

    yearly["wage_log_change"] = (
        np.log(yearly["nominal_wage_amount"] / yearly["nominal_wage_amount"].shift(1))
        * 100
    )

    yearly["hourly_wage_log_contribution"] = (
        np.log(
            yearly["weighted_approx_hourly_wage"]
            / yearly["weighted_approx_hourly_wage"].shift(1)
        )
        * 100
    )

    yearly["total_hours_log_contribution"] = (
        np.log(yearly["total_hours"] / yearly["total_hours"].shift(1)) * 100
    )

    return yearly[
        [
            "year",
            "nominal_wage_amount",
            "weighted_approx_hourly_wage",
            "total_hours",
            "wage_change_pct",
            "hourly_wage_change_pct",
            "total_hours_change_pct",
            "wage_log_change",
            "hourly_wage_log_contribution",
            "total_hours_log_contribution",
        ]
    ]


def add_working_hours_decomposition(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """総実労働時間の前年差・前年比を所定内・所定外労働時間へ分解する。"""

    result = df.copy()

    previous = result[
        [
            "date",
            "total_hours",
            "scheduled_hours",
            "overtime_hours",
        ]
    ].copy()

    previous["date"] = previous["date"] + pd.DateOffset(years=1)

    previous = previous.rename(
        columns={
            "total_hours": "total_hours_previous_year",
            "scheduled_hours": "scheduled_hours_previous_year",
            "overtime_hours": "overtime_hours_previous_year",
        }
    )

    result = result.merge(
        previous,
        on="date",
        how="left",
        validate="one_to_one",
    )

    # 前年差
    result["total_hours_yoy_diff"] = (
        result["total_hours"] - result["total_hours_previous_year"]
    )

    result["scheduled_hours_yoy_diff"] = (
        result["scheduled_hours"] - result["scheduled_hours_previous_year"]
    )

    result["overtime_hours_yoy_diff"] = (
        result["overtime_hours"] - result["overtime_hours_previous_year"]
    )

    # 総実労働時間前年比
    result["total_hours_decomposition_yoy_pct"] = (
        result["total_hours_yoy_diff"] / result["total_hours_previous_year"] * 100
    )

    # 所定内労働時間の寄与度
    result["scheduled_hours_contribution_pct"] = (
        result["scheduled_hours_yoy_diff"] / result["total_hours_previous_year"] * 100
    )

    # 所定外労働時間の寄与度
    result["overtime_hours_contribution_pct"] = (
        result["overtime_hours_yoy_diff"] / result["total_hours_previous_year"] * 100
    )

    result = result.drop(
        columns=[
            "total_hours_previous_year",
            "scheduled_hours_previous_year",
            "overtime_hours_previous_year",
        ]
    )

    return result


def summarize_long_term_working_hours_decomposition(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> dict[str, float]:
    """年平均を用いて総実労働時間の変化を所定内・所定外へ分解する。"""

    start_df = df.loc[df["date"].dt.year == start_year]
    end_df = df.loc[df["date"].dt.year == end_year]

    if len(start_df) != 12 or len(end_df) != 12:
        raise ValueError("長期比較には開始年・終了年ともに12か月分のデータが必要です。")

    start_total = start_df["total_hours"].mean()
    end_total = end_df["total_hours"].mean()

    start_scheduled = start_df["scheduled_hours"].mean()
    end_scheduled = end_df["scheduled_hours"].mean()

    start_overtime = start_df["overtime_hours"].mean()
    end_overtime = end_df["overtime_hours"].mean()

    total_diff = end_total - start_total
    scheduled_diff = end_scheduled - start_scheduled
    overtime_diff = end_overtime - start_overtime

    total_change_pct = total_diff / start_total * 100

    scheduled_contribution_pct = scheduled_diff / start_total * 100

    overtime_contribution_pct = overtime_diff / start_total * 100

    overtime_hours_change_pct = ((end_overtime / start_overtime) - 1) * 100

    return {
        "start_year": start_year,
        "end_year": end_year,
        "start_total_hours": start_total,
        "end_total_hours": end_total,
        "start_scheduled_hours": start_scheduled,
        "end_scheduled_hours": end_scheduled,
        "start_overtime_hours": start_overtime,
        "end_overtime_hours": end_overtime,
        "total_hours_diff": total_diff,
        "scheduled_hours_diff": scheduled_diff,
        "overtime_hours_diff": overtime_diff,
        "total_hours_change_pct": total_change_pct,
        "scheduled_hours_contribution_pct": scheduled_contribution_pct,
        "overtime_hours_contribution_pct": overtime_contribution_pct,
        "overtime_hours_change_pct": overtime_hours_change_pct,
    }


def add_scheduled_hours_decomposition(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """所定内労働時間の前年比変化を出勤日数と1出勤日当たり時間へ分解する。"""

    result = df.copy()

    previous = result[
        [
            "date",
            "scheduled_hours",
            "working_days",
            "scheduled_hours_per_workday",
        ]
    ].copy()

    previous["date"] = previous["date"] + pd.DateOffset(years=1)

    previous = previous.rename(
        columns={
            "scheduled_hours": "scheduled_hours_previous_year",
            "working_days": "working_days_previous_year",
            "scheduled_hours_per_workday": (
                "scheduled_hours_per_workday_previous_year"
            ),
        }
    )

    result = result.merge(
        previous,
        on="date",
        how="left",
        validate="one_to_one",
    )

    result["scheduled_hours_log_change"] = (
        np.log(result["scheduled_hours"] / result["scheduled_hours_previous_year"])
        * 100
    )

    result["working_days_log_contribution"] = (
        np.log(result["working_days"] / result["working_days_previous_year"]) * 100
    )

    result["hours_per_workday_log_contribution"] = (
        np.log(
            result["scheduled_hours_per_workday"]
            / result["scheduled_hours_per_workday_previous_year"]
        )
        * 100
    )

    result = result.drop(
        columns=[
            "scheduled_hours_previous_year",
            "working_days_previous_year",
            "scheduled_hours_per_workday_previous_year",
        ]
    )

    return result


def summarize_long_term_scheduled_hours_decomposition(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> dict[str, float]:
    """年平均を用いて所定内労働時間の変化を出勤日数と1出勤日当たり時間へ分解する。"""

    start_df = df.loc[df["date"].dt.year == start_year]
    end_df = df.loc[df["date"].dt.year == end_year]

    if len(start_df) != 12 or len(end_df) != 12:
        raise ValueError("長期比較には開始年・終了年ともに12か月分のデータが必要です。")

    start_scheduled = start_df["scheduled_hours"].mean()
    end_scheduled = end_df["scheduled_hours"].mean()

    start_days = start_df["working_days"].mean()
    end_days = end_df["working_days"].mean()

    # 完全分解を維持するため、
    # 年平均所定内労働時間 ÷ 年平均出勤日数で算出する
    start_hours_per_workday = start_scheduled / start_days
    end_hours_per_workday = end_scheduled / end_days

    scheduled_change_pct = ((end_scheduled / start_scheduled) - 1) * 100

    working_days_change_pct = ((end_days / start_days) - 1) * 100

    hours_per_workday_change_pct = (
        (end_hours_per_workday / start_hours_per_workday) - 1
    ) * 100

    scheduled_log_change = np.log(end_scheduled / start_scheduled) * 100

    working_days_log_contribution = np.log(end_days / start_days) * 100

    hours_per_workday_log_contribution = (
        np.log(end_hours_per_workday / start_hours_per_workday) * 100
    )

    return {
        "start_year": start_year,
        "end_year": end_year,
        "start_scheduled_hours": start_scheduled,
        "end_scheduled_hours": end_scheduled,
        "start_working_days": start_days,
        "end_working_days": end_days,
        "start_hours_per_workday": start_hours_per_workday,
        "end_hours_per_workday": end_hours_per_workday,
        "scheduled_hours_change_pct": scheduled_change_pct,
        "working_days_change_pct": working_days_change_pct,
        "hours_per_workday_change_pct": hours_per_workday_change_pct,
        "scheduled_hours_log_change": scheduled_log_change,
        "working_days_log_contribution": working_days_log_contribution,
        "hours_per_workday_log_contribution": (hours_per_workday_log_contribution),
    }


def create_yearly_labor_input_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """労働投入分析の主要指標を年次で集計・分解する。"""

    yearly = (
        df.assign(year=df["date"].dt.year)
        .groupby("year", as_index=False)
        .agg(
            nominal_wage_amount=("nominal_wage_amount", "mean"),
            total_hours=("total_hours", "mean"),
            scheduled_hours=("scheduled_hours", "mean"),
            overtime_hours=("overtime_hours", "mean"),
            working_days=("working_days", "mean"),
            annual_wage_sum=("nominal_wage_amount", "sum"),
            annual_total_hours_sum=("total_hours", "sum"),
            month_count=("date", "count"),
        )
    )

    # 12か月揃っている年だけを年次比較に使用
    yearly = yearly.loc[yearly["month_count"] == 12].copy()

    # 年間加重概算時間当たり賃金
    yearly["weighted_approx_hourly_wage"] = (
        yearly["annual_wage_sum"] / yearly["annual_total_hours_sum"]
    )

    # 年平均値同士で完全分解できる1出勤日当たり所定内労働時間
    yearly["scheduled_hours_per_workday"] = (
        yearly["scheduled_hours"] / yearly["working_days"]
    )

    # -------------------------------------------------
    # 月額賃金 = 時間当たり賃金 × 総実労働時間
    # -------------------------------------------------

    yearly["wage_log_change"] = (
        np.log(yearly["nominal_wage_amount"] / yearly["nominal_wage_amount"].shift(1))
        * 100
    )

    yearly["hourly_wage_log_contribution"] = (
        np.log(
            yearly["weighted_approx_hourly_wage"]
            / yearly["weighted_approx_hourly_wage"].shift(1)
        )
        * 100
    )

    yearly["total_hours_log_contribution"] = (
        np.log(yearly["total_hours"] / yearly["total_hours"].shift(1)) * 100
    )

    # -------------------------------------------------
    # 総実労働時間 = 所定内 + 所定外
    # -------------------------------------------------

    yearly["total_hours_diff"] = yearly["total_hours"] - yearly["total_hours"].shift(1)

    yearly["scheduled_hours_diff"] = yearly["scheduled_hours"] - yearly[
        "scheduled_hours"
    ].shift(1)

    yearly["overtime_hours_diff"] = yearly["overtime_hours"] - yearly[
        "overtime_hours"
    ].shift(1)

    yearly["scheduled_hours_contribution_pct"] = (
        yearly["scheduled_hours_diff"] / yearly["total_hours"].shift(1) * 100
    )

    yearly["overtime_hours_contribution_pct"] = (
        yearly["overtime_hours_diff"] / yearly["total_hours"].shift(1) * 100
    )

    # -------------------------------------------------
    # 所定内労働時間 = 出勤日数 × 1出勤日当たり時間
    # -------------------------------------------------

    yearly["scheduled_hours_log_change"] = (
        np.log(yearly["scheduled_hours"] / yearly["scheduled_hours"].shift(1)) * 100
    )

    yearly["working_days_log_contribution"] = (
        np.log(yearly["working_days"] / yearly["working_days"].shift(1)) * 100
    )

    yearly["hours_per_workday_log_contribution"] = (
        np.log(
            yearly["scheduled_hours_per_workday"]
            / yearly["scheduled_hours_per_workday"].shift(1)
        )
        * 100
    )

    return yearly[
        [
            "year",
            "nominal_wage_amount",
            "weighted_approx_hourly_wage",
            "total_hours",
            "scheduled_hours",
            "overtime_hours",
            "working_days",
            "scheduled_hours_per_workday",
            "wage_log_change",
            "hourly_wage_log_contribution",
            "total_hours_log_contribution",
            "total_hours_diff",
            "scheduled_hours_diff",
            "overtime_hours_diff",
            "scheduled_hours_contribution_pct",
            "overtime_hours_contribution_pct",
            "scheduled_hours_log_change",
            "working_days_log_contribution",
            "hours_per_workday_log_contribution",
        ]
    ]
