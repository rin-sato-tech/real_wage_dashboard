import numpy as np
import pandas as pd

from real_wage_dashboard.monthly_labor_service import extract_monthly_labor_series
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

    previous_workers_df = extract_monthly_labor_series(
        raw_df,
        item="前月末労働者数",
        value_column="previous_month_workers",
        label="前月末労働者数",
        establishment_size=establishment_size,
        employment_type=employment_type,
        industry_code="TL",
    )

    end_workers_df = extract_monthly_labor_series(
        raw_df,
        item="本月末労働者数",
        value_column="end_month_workers",
        label="本月末労働者数",
        establishment_size=establishment_size,
        employment_type=employment_type,
        industry_code="TL",
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
        .merge(
            previous_workers_df,
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            end_workers_df,
            on="date",
            how="inner",
            validate="one_to_one",
        )
    )

    result["worker_weight"] = (
        result["previous_month_workers"] + result["end_month_workers"]
    ) / 2

    result["approx_hourly_wage"] = result["nominal_wage_amount"] / result["total_hours"]

    result["scheduled_hours_per_workday"] = (
        result["scheduled_hours"] / result["working_days"]
    )

    return result


def weighted_mean(
    df: pd.DataFrame,
    value_column: str,
    weight_column: str = "worker_weight",
) -> float:
    """月次値を平均労働者数で加重平均する。"""

    values = df[value_column]
    weights = df[weight_column]

    if values.isna().any() or weights.isna().any():
        raise ValueError("加重平均の対象に欠損値があります。")

    if (weights <= 0).any():
        raise ValueError("加重平均の重みは正である必要があります。")

    return float(np.average(values, weights=weights))


def create_yearly_weighted_means(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """12か月揃った年について平均労働者数加重の年平均を作成する。"""

    data = df.copy()
    data["year"] = data["date"].dt.year

    records: list[dict[str, float | int]] = []

    for year, group in data.groupby("year", sort=True):
        if len(group) != 12:
            continue

        record: dict[str, float | int] = {
            "year": int(year),
        }

        for column in columns:
            record[column] = weighted_mean(group, column)

        records.append(record)

    return pd.DataFrame(records)


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

    # start_wage = start_df["nominal_wage_amount"].mean()
    # end_wage = end_df["nominal_wage_amount"].mean()

    # start_hours = start_df["total_hours"].mean()
    # end_hours = end_df["total_hours"].mean()

    # 年間の賃金総額 ÷ 年間の総実労働時間
    # 年平均月額賃金 = 加重概算時間当たり賃金 × 年平均労働時間
    # が厳密に成立するようにする。
    # start_hourly = start_df["nominal_wage_amount"].sum() / start_df["total_hours"].sum()
    # end_hourly = end_df["nominal_wage_amount"].sum() / end_df["total_hours"].sum()

    start_wage = weighted_mean(start_df, "nominal_wage_amount")
    end_wage = weighted_mean(end_df, "nominal_wage_amount")

    start_hours = weighted_mean(start_df, "total_hours")
    end_hours = weighted_mean(end_df, "total_hours")

    # 年平均月額給与 = 年平均概算時間当たり給与 × 年平均労働時間
    # が厳密に成立するようにする。
    start_hourly = start_wage / start_hours
    end_hourly = end_wage / end_hours

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


def create_yearly_wage_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    """年平均を用いて月額賃金の前年比変化を要因分解する。"""

    yearly = create_yearly_weighted_means(
        df,
        columns=[
            "nominal_wage_amount",
            "total_hours",
        ],
    )

    yearly["weighted_approx_hourly_wage"] = (
        yearly["nominal_wage_amount"] / yearly["total_hours"]
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

    start_total = weighted_mean(start_df, "total_hours")
    end_total = weighted_mean(end_df, "total_hours")

    start_scheduled = weighted_mean(start_df, "scheduled_hours")
    end_scheduled = weighted_mean(end_df, "scheduled_hours")

    start_overtime = weighted_mean(start_df, "overtime_hours")
    end_overtime = weighted_mean(end_df, "overtime_hours")

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

    start_scheduled = weighted_mean(start_df, "scheduled_hours")
    end_scheduled = weighted_mean(end_df, "scheduled_hours")

    start_days = weighted_mean(start_df, "working_days")
    end_days = weighted_mean(end_df, "working_days")

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


def create_yearly_labor_input_summary(df: pd.DataFrame) -> pd.DataFrame:
    """労働投入分析の主要指標を年次で集計・分解する。"""

    yearly = create_yearly_weighted_means(
        df,
        columns=[
            "nominal_wage_amount",
            "total_hours",
            "scheduled_hours",
            "overtime_hours",
            "working_days",
        ],
    )

    yearly["weighted_approx_hourly_wage"] = (
        yearly["nominal_wage_amount"] / yearly["total_hours"]
    )

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


def create_rolling_labor_input_decomposition(
    yearly_df: pd.DataFrame,
    window_years: int = 10,
) -> pd.DataFrame:
    """年次系列からローリング長期分解を作成する。"""

    if window_years <= 0:
        raise ValueError("window_years は正の整数である必要があります。")

    data = yearly_df.sort_values("year").reset_index(drop=True)

    records: list[dict[str, float | int]] = []

    indexed = data.set_index("year")

    for start_year in indexed.index:
        end_year = start_year + window_years

        if end_year not in indexed.index:
            continue

        start = indexed.loc[start_year]
        end = indexed.loc[end_year]

        # 月額給与
        wage_log_change = (
            np.log(end["nominal_wage_amount"] / start["nominal_wage_amount"]) * 100
        )

        hourly_wage_log_contribution = (
            np.log(
                end["weighted_approx_hourly_wage"]
                / start["weighted_approx_hourly_wage"]
            )
            * 100
        )

        total_hours_log_contribution = (
            np.log(end["total_hours"] / start["total_hours"]) * 100
        )

        # 総実労働時間
        total_hours_diff = end["total_hours"] - start["total_hours"]

        scheduled_hours_diff = end["scheduled_hours"] - start["scheduled_hours"]

        overtime_hours_diff = end["overtime_hours"] - start["overtime_hours"]

        total_hours_change_pct = total_hours_diff / start["total_hours"] * 100

        scheduled_hours_contribution_pct = (
            scheduled_hours_diff / start["total_hours"] * 100
        )

        overtime_hours_contribution_pct = (
            overtime_hours_diff / start["total_hours"] * 100
        )

        # 所定内労働時間
        scheduled_hours_log_change = (
            np.log(end["scheduled_hours"] / start["scheduled_hours"]) * 100
        )

        working_days_log_contribution = (
            np.log(end["working_days"] / start["working_days"]) * 100
        )

        hours_per_workday_log_contribution = (
            np.log(
                end["scheduled_hours_per_workday"]
                / start["scheduled_hours_per_workday"]
            )
            * 100
        )

        records.append(
            {
                "start_year": int(start_year),
                "end_year": int(end_year),
                "wage_log_change": wage_log_change,
                "hourly_wage_log_contribution": (hourly_wage_log_contribution),
                "total_hours_log_contribution": (total_hours_log_contribution),
                "total_hours_change_pct": (total_hours_change_pct),
                "scheduled_hours_contribution_pct": (scheduled_hours_contribution_pct),
                "overtime_hours_contribution_pct": (overtime_hours_contribution_pct),
                "scheduled_hours_log_change": (scheduled_hours_log_change),
                "working_days_log_contribution": (working_days_log_contribution),
                "hours_per_workday_log_contribution": (
                    hours_per_workday_log_contribution
                ),
            }
        )

    return pd.DataFrame(records)


def create_working_hours_index_comparison(
    yearly_df: pd.DataFrame,
    official_df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """実数から再構築した指数と公式労働時間指数を比較する。"""

    result = yearly_df[
        [
            "year",
            "total_hours",
            "scheduled_hours",
            "overtime_hours",
        ]
    ].copy()

    base = result.loc[result["year"] == base_year]

    if len(base) != 1:
        raise ValueError(f"{base_year}年の基準値を一意に取得できません。")

    for source, target in [
        (
            "total_hours",
            "calculated_total_hours_index",
        ),
        (
            "scheduled_hours",
            "calculated_scheduled_hours_index",
        ),
        (
            "overtime_hours",
            "calculated_overtime_hours_index",
        ),
    ]:
        result[target] = result[source] / base.iloc[0][source] * 100

    result = result.merge(
        official_df,
        on="year",
        how="inner",
        validate="one_to_one",
    )

    for name in [
        "total_hours",
        "scheduled_hours",
        "overtime_hours",
    ]:
        result[f"{name}_index_diff"] = (
            result[f"calculated_{name}_index"] - result[f"official_{name}_index"]
        )

    return result


def _summarize_annual_labor_input_level(
    df: pd.DataFrame,
    year: int,
    columns: list[str],
) -> dict[str, float]:
    """指定年の労働投入指標と年間労働者ウェイト合計を返す。"""

    year_df = df.loc[df["date"].dt.year == year]

    if len(year_df) != 12:
        raise ValueError(f"{year}年の年平均計算には12か月分のデータが必要です。")

    worker_exposure = float(year_df["worker_weight"].sum())

    if worker_exposure <= 0:
        raise ValueError("年間労働者ウェイト合計は正である必要があります。")

    result = {
        "worker_exposure": worker_exposure,
    }

    for column in columns:
        result[column] = weighted_mean(year_df, column)

    return result


def create_employment_type_composition_decomposition(
    total_df: pd.DataFrame,
    regular_df: pd.DataFrame,
    part_time_df: pd.DataFrame,
    start_year: int,
    end_year: int,
    metrics: dict[str, str] | None = None,
) -> pd.DataFrame:
    """就業形態計の水準変化を就業形態内効果と構成効果へ分解する。

    一般労働者・パートタイム労働者の年平均水準と年間労働者
    ウェイトから構成比を求め、対称分解する。

    再構成残差は、公表された就業形態計の変化と、
    一般・パートから再構成した変化との差を表す。
    """

    if start_year >= end_year:
        raise ValueError("start_year は end_year より前である必要があります。")

    if metrics is None:
        metrics = {
            "nominal_wage_amount": "きまって支給する給与",
            "total_hours": "総実労働時間",
            "scheduled_hours": "所定内労働時間",
            "overtime_hours": "所定外労働時間",
            "working_days": "出勤日数",
        }

    columns = list(metrics)

    total_start = _summarize_annual_labor_input_level(
        total_df,
        start_year,
        columns,
    )
    total_end = _summarize_annual_labor_input_level(
        total_df,
        end_year,
        columns,
    )

    group_dfs = {
        "regular": regular_df,
        "part_time": part_time_df,
    }

    group_start = {
        name: _summarize_annual_labor_input_level(
            df,
            start_year,
            columns,
        )
        for name, df in group_dfs.items()
    }

    group_end = {
        name: _summarize_annual_labor_input_level(
            df,
            end_year,
            columns,
        )
        for name, df in group_dfs.items()
    }

    start_exposure = sum(values["worker_exposure"] for values in group_start.values())
    end_exposure = sum(values["worker_exposure"] for values in group_end.values())

    start_shares = {
        name: values["worker_exposure"] / start_exposure
        for name, values in group_start.items()
    }

    end_shares = {
        name: values["worker_exposure"] / end_exposure
        for name, values in group_end.items()
    }

    records = []

    for column, label in metrics.items():
        published_start = total_start[column]
        published_end = total_end[column]
        published_change = published_end - published_start

        reconstructed_start = sum(
            start_shares[name] * group_start[name][column] for name in group_dfs
        )

        reconstructed_end = sum(
            end_shares[name] * group_end[name][column] for name in group_dfs
        )

        within_effect = sum(
            ((start_shares[name] + end_shares[name]) / 2)
            * (group_end[name][column] - group_start[name][column])
            for name in group_dfs
        )

        composition_effect = sum(
            ((group_start[name][column] + group_end[name][column]) / 2)
            * (end_shares[name] - start_shares[name])
            for name in group_dfs
        )

        reconstructed_change = reconstructed_end - reconstructed_start

        residual = published_change - reconstructed_change

        records.append(
            {
                "start_year": start_year,
                "end_year": end_year,
                "indicator": label,
                "column": column,
                "published_start": published_start,
                "published_end": published_end,
                "published_change": published_change,
                "published_change_pct": (published_change / published_start * 100),
                "reconstructed_start": reconstructed_start,
                "reconstructed_end": reconstructed_end,
                "within_effect": within_effect,
                "composition_effect": composition_effect,
                "residual": residual,
                "within_contribution_pct": (within_effect / published_start * 100),
                "composition_contribution_pct": (
                    composition_effect / published_start * 100
                ),
                "residual_contribution_pct": (residual / published_start * 100),
                "regular_share_start": (start_shares["regular"]),
                "regular_share_end": (end_shares["regular"]),
                "part_time_share_start": (start_shares["part_time"]),
                "part_time_share_end": (end_shares["part_time"]),
            }
        )

    return pd.DataFrame(records)


def create_employment_type_composition_period_summary(
    total_df: pd.DataFrame,
    regular_df: pd.DataFrame,
    part_time_df: pd.DataFrame,
    periods: list[tuple[int, int]],
    metrics: dict[str, str] | None = None,
) -> pd.DataFrame:
    """複数期間について就業形態構成分解をまとめて返す。"""

    results = [
        create_employment_type_composition_decomposition(
            total_df=total_df,
            regular_df=regular_df,
            part_time_df=part_time_df,
            start_year=start_year,
            end_year=end_year,
            metrics=metrics,
        )
        for start_year, end_year in periods
    ]

    if not results:
        return pd.DataFrame()

    return pd.concat(
        results,
        ignore_index=True,
    )
