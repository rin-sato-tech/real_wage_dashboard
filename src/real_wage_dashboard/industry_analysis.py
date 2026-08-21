import numpy as np
import pandas as pd

from real_wage_dashboard.wage_service import create_wage_dataframe
from real_wage_dashboard.working_hours_service import (
    create_working_hours_dataframe,
)

MAIN_INDUSTRIES = [
    "TL",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
]

INDUSTRY_NAMES = {
    "TL": "調査産業計",
    "C": "鉱業，採石業等",
    "D": "建設業",
    "E": "製造業",
    "F": "電気・ガス業",
    "G": "情報通信業",
    "H": "運輸業，郵便業",
    "I": "卸売業，小売業",
    "J": "金融業，保険業",
    "K": "不動産・物品賃貸業",
    "L": "学術研究等",
    "M": "宿泊・飲食サービス業",
    "N": "生活関連サービス等",
    "O": "教育，学習支援業",
    "P": "医療，福祉",
    "Q": "複合サービス事業",
    "R": "その他のサービス業",
}

def create_industry_monthly_dataframe(
    raw_df: pd.DataFrame,
    industry_code: str,
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """指定産業の賃金・労働時間系列と派生指標を作成する。"""

    wage_df = create_wage_dataframe(
        raw_df,
        wage_item="きまって支給する給与",
        establishment_size=establishment_size,
        employment_type=employment_type,
        industry_code=industry_code,
    ).rename(
        columns={
            "nominal_wage_amount": "monthly_wage",
        }
    )

    total_hours_df = create_working_hours_dataframe(
        raw_df,
        working_hours_item="総実労働時間",
        establishment_size=establishment_size,
        employment_type=employment_type,
        industry_code=industry_code,
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
        industry_code=industry_code,
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
        industry_code=industry_code,
    ).rename(
        columns={
            "working_hours": "overtime_hours",
        }
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
    )

    result["industry"] = industry_code

    result["approx_hourly_wage"] = result["monthly_wage"] / result["total_hours"]

    return result[
        [
            "date",
            "industry",
            "monthly_wage",
            "approx_hourly_wage",
            "total_hours",
            "scheduled_hours",
            "overtime_hours",
        ]
    ]


def create_industry_yearly_dataframe(
    monthly_df: pd.DataFrame,
) -> pd.DataFrame:
    """12か月揃った年について産業別の年平均・加重概算時間当たり賃金を作成する。"""

    required_columns = {
        "date",
        "industry",
        "monthly_wage",
        "total_hours",
        "scheduled_hours",
        "overtime_hours",
    }

    if not required_columns.issubset(monthly_df.columns):
        missing = required_columns - set(monthly_df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    yearly = (
        monthly_df.assign(
            year=monthly_df["date"].dt.year,
        )
        .groupby(
            ["industry", "year"],
            as_index=False,
        )
        .agg(
            monthly_wage=("monthly_wage", "mean"),
            total_hours=("total_hours", "mean"),
            scheduled_hours=("scheduled_hours", "mean"),
            overtime_hours=("overtime_hours", "mean"),
            annual_wage_sum=("monthly_wage", "sum"),
            annual_hours_sum=("total_hours", "sum"),
            month_count=("date", "count"),
        )
    )

    yearly = yearly.loc[yearly["month_count"] == 12].copy()

    yearly["approx_hourly_wage"] = (
        yearly["annual_wage_sum"] / yearly["annual_hours_sum"]
    )

    return yearly[
        [
            "industry",
            "year",
            "monthly_wage",
            "approx_hourly_wage",
            "total_hours",
            "scheduled_hours",
            "overtime_hours",
            "month_count",
        ]
    ]


def create_industry_comparison_dataframe(
    raw_df: pd.DataFrame,
    industry_codes: list[str],
    start_year: int = 2015,
    end_year: int = 2025,
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """産業別に開始年・終了年の年平均と変化率を比較する。"""

    results = []

    for industry_code in industry_codes:
        monthly_df = create_industry_monthly_dataframe(
            raw_df,
            industry_code=industry_code,
            establishment_size=establishment_size,
            employment_type=employment_type,
        )

        yearly_df = create_industry_yearly_dataframe(
            monthly_df,
        )

        start_df = yearly_df.loc[yearly_df["year"] == start_year]

        end_df = yearly_df.loc[yearly_df["year"] == end_year]

        if start_df.empty or end_df.empty:
            continue

        start = start_df.iloc[0]
        end = end_df.iloc[0]

        results.append(
            {
                "industry": industry_code,
                "start_year": start_year,
                "end_year": end_year,
                "start_monthly_wage": start["monthly_wage"],
                "end_monthly_wage": end["monthly_wage"],
                "monthly_wage_change_pct": (
                    end["monthly_wage"] / start["monthly_wage"] - 1
                )
                * 100,
                "start_hourly_wage": start["approx_hourly_wage"],
                "end_hourly_wage": end["approx_hourly_wage"],
                "hourly_wage_change_pct": (
                    end["approx_hourly_wage"] / start["approx_hourly_wage"] - 1
                )
                * 100,
                "start_total_hours": start["total_hours"],
                "end_total_hours": end["total_hours"],
                "total_hours_change_pct": (
                    end["total_hours"] / start["total_hours"] - 1
                )
                * 100,
                "scheduled_hours_change_pct": (
                    end["scheduled_hours"] / start["scheduled_hours"] - 1
                )
                * 100,
                "overtime_hours_change_pct": (
                    end["overtime_hours"] / start["overtime_hours"] - 1
                )
                * 100,
            }
        )

    return pd.DataFrame(results)


def add_industry_wage_decomposition(
    comparison_df: pd.DataFrame,
) -> pd.DataFrame:
    """産業別の月額賃金変化を時間単価と労働時間に対数分解する。"""

    result = comparison_df.copy()

    result["wage_log_change"] = (
        np.log(result["end_monthly_wage"] / result["start_monthly_wage"]) * 100
    )

    result["hourly_wage_log_contribution"] = (
        np.log(result["end_hourly_wage"] / result["start_hourly_wage"]) * 100
    )

    result["total_hours_log_contribution"] = (
        np.log(result["end_total_hours"] / result["start_total_hours"]) * 100
    )

    result["decomposition_error"] = result["wage_log_change"] - (
        result["hourly_wage_log_contribution"] + result["total_hours_log_contribution"]
    )

    return result


def summarize_industry_changes(
    decomposition_df: pd.DataFrame,
) -> dict[str, float]:
    """大分類産業間の変化率分布と全国平均との差を要約する。"""

    industries = decomposition_df.loc[decomposition_df["industry"] != "TL"].copy()

    total_row = decomposition_df.loc[decomposition_df["industry"] == "TL"]

    if total_row.empty:
        raise ValueError("調査産業計（TL）がありません。")

    total_wage_change = total_row.iloc[0]["monthly_wage_change_pct"]

    wage_changes = industries["monthly_wage_change_pct"]
    hourly_changes = industries["hourly_wage_change_pct"]
    hours_changes = industries["total_hours_change_pct"]

    return {
        "industry_count": len(industries),
        "wage_change_mean": wage_changes.mean(),
        "wage_change_median": wage_changes.median(),
        "wage_change_std": wage_changes.std(),
        "wage_change_min": wage_changes.min(),
        "wage_change_q1": wage_changes.quantile(0.25),
        "wage_change_q3": wage_changes.quantile(0.75),
        "wage_change_max": wage_changes.max(),
        "wage_change_iqr": (wage_changes.quantile(0.75) - wage_changes.quantile(0.25)),
        "hourly_change_mean": hourly_changes.mean(),
        "hourly_change_median": hourly_changes.median(),
        "hourly_change_std": hourly_changes.std(),
        "hourly_change_min": hourly_changes.min(),
        "hourly_change_q1": hourly_changes.quantile(0.25),
        "hourly_change_q3": hourly_changes.quantile(0.75),
        "hourly_change_max": hourly_changes.max(),
        "hourly_change_iqr": (
            hourly_changes.quantile(0.75) - hourly_changes.quantile(0.25)
        ),
        "hours_change_mean": hours_changes.mean(),
        "hours_change_median": hours_changes.median(),
        "hours_change_std": hours_changes.std(),
        "hours_change_min": hours_changes.min(),
        "hours_change_q1": hours_changes.quantile(0.25),
        "hours_change_q3": hours_changes.quantile(0.75),
        "hours_change_max": hours_changes.max(),
        "hours_change_iqr": (
            hours_changes.quantile(0.75) - hours_changes.quantile(0.25)
        ),
        "wage_rise_count": int((wage_changes > 0).sum()),
        "wage_rise_share": ((wage_changes > 0).mean() * 100),
        "above_total_count": int((wage_changes > total_wage_change).sum()),
        "above_total_share": ((wage_changes > total_wage_change).mean() * 100),
        "total_wage_change": total_wage_change,
    }


def calculate_industry_correlations(
    decomposition_df: pd.DataFrame,
) -> dict[str, float]:
    """大分類産業について時間単価変化と労働時間変化の相関を算出する。"""

    industries = decomposition_df.loc[decomposition_df["industry"] != "TL"].copy()

    pearson = (
        industries[
            [
                "hourly_wage_log_contribution",
                "total_hours_log_contribution",
            ]
        ]
        .corr(method="pearson")
        .iloc[0, 1]
    )

    spearman = (
        industries[
            [
                "hourly_wage_log_contribution",
                "total_hours_log_contribution",
            ]
        ]
        .corr(method="spearman")
        .iloc[0, 1]
    )

    return {
        "pearson": pearson,
        "spearman": spearman,
    }


def add_industry_quadrant(
    decomposition_df: pd.DataFrame,
) -> pd.DataFrame:
    """時間単価寄与と労働時間寄与の符号から産業を分類する。"""

    result = decomposition_df.copy()

    def classify(row: pd.Series) -> str:
        hourly = row["hourly_wage_log_contribution"]
        hours = row["total_hours_log_contribution"]

        if hourly >= 0 and hours >= 0:
            return "時間単価↑・労働時間↑"
        if hourly >= 0 and hours < 0:
            return "時間単価↑・労働時間↓"
        if hourly < 0 and hours >= 0:
            return "時間単価↓・労働時間↑"
        return "時間単価↓・労働時間↓"

    result["quadrant"] = result.apply(
        classify,
        axis=1,
    )

    return result


def identify_notable_industries(
    decomposition_df: pd.DataFrame,
) -> dict[str, str]:
    """産業別比較から特徴的な産業コードを抽出する。"""

    industries = decomposition_df.loc[decomposition_df["industry"] != "TL"].copy()

    monthly_max = industries.loc[industries["monthly_wage_change_pct"].idxmax()]

    monthly_min = industries.loc[industries["monthly_wage_change_pct"].idxmin()]

    hourly_max = industries.loc[industries["hourly_wage_change_pct"].idxmax()]

    hours_decline_max = industries.loc[industries["total_hours_change_pct"].idxmin()]

    gap = industries["hourly_wage_change_pct"] - industries["monthly_wage_change_pct"]

    monthly_hourly_gap_max = industries.loc[gap.idxmax()]

    return {
        "monthly_wage_growth_max": monthly_max["industry"],
        "monthly_wage_growth_min": monthly_min["industry"],
        "hourly_wage_growth_max": hourly_max["industry"],
        "hours_decline_max": hours_decline_max["industry"],
        "monthly_hourly_gap_max": monthly_hourly_gap_max["industry"],
    }


def create_period_comparison_dataframe(
    raw_df: pd.DataFrame,
    industry_codes: list[str],
    periods: list[tuple[int, int]],
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """複数期間について産業別の賃金・時間変化を比較する。"""

    results = []

    for industry_code in industry_codes:
        monthly_df = create_industry_monthly_dataframe(
            raw_df,
            industry_code=industry_code,
            establishment_size=establishment_size,
            employment_type=employment_type,
        )

        yearly_df = create_industry_yearly_dataframe(monthly_df)

        for start_year, end_year in periods:
            start_df = yearly_df.loc[yearly_df["year"] == start_year]

            end_df = yearly_df.loc[yearly_df["year"] == end_year]

            if start_df.empty or end_df.empty:
                continue

            start = start_df.iloc[0]
            end = end_df.iloc[0]

            results.append(
                {
                    "industry": industry_code,
                    "start_year": start_year,
                    "end_year": end_year,
                    "monthly_wage_change_pct": (
                        end["monthly_wage"] / start["monthly_wage"] - 1
                    )
                    * 100,
                    "hourly_wage_change_pct": (
                        end["approx_hourly_wage"] / start["approx_hourly_wage"] - 1
                    )
                    * 100,
                    "total_hours_change_pct": (
                        end["total_hours"] / start["total_hours"] - 1
                    )
                    * 100,
                }
            )

    return pd.DataFrame(results)
