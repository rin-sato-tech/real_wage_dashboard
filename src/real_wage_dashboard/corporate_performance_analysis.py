import pandas as pd

from real_wage_dashboard.config import (
    CORPORATE_ANALYSIS_END_YEAR,
    CORPORATE_ANALYSIS_START_YEAR,
)


CORPORATE_COMPARISON_METRICS = [
    "sales",
    "operating_profit",
    "ordinary_profit",
    "value_added",
    "labor_productivity",
    "personnel_expenses",
    "personnel_expenses_per_employee",
    "labor_share",
    "operating_profit_margin",
    "ordinary_profit_margin",
    "value_added_ratio",
]


def create_corporate_comparison_dataframe(
    df: pd.DataFrame,
    start_year: int = CORPORATE_ANALYSIS_START_YEAR,
    end_year: int = CORPORATE_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """開始年度と終了年度の企業パフォーマンス指標を比較する。"""

    required_columns = {
        "fiscal_year",
        *CORPORATE_COMPARISON_METRICS,
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"比較に必要な列がありません: {sorted(missing_columns)}")

    if start_year >= end_year:
        raise ValueError("開始年度は終了年度より前である必要があります。")

    start_rows = df.loc[df["fiscal_year"] == start_year]
    end_rows = df.loc[df["fiscal_year"] == end_year]

    if len(start_rows) != 1:
        raise ValueError(
            f"{start_year}年度のデータが1件ではありません: "
            f"{len(start_rows)}件"
        )

    if len(end_rows) != 1:
        raise ValueError(
            f"{end_year}年度のデータが1件ではありません: "
            f"{len(end_rows)}件"
        )

    start_row = start_rows.iloc[0]
    end_row = end_rows.iloc[0]

    rows = []

    for metric in CORPORATE_COMPARISON_METRICS:
        start_value = start_row[metric]
        end_value = end_row[metric]

        difference = end_value - start_value

        if start_value == 0:
            change_rate = pd.NA
        else:
            change_rate = (
                end_value / start_value - 1
            ) * 100

        rows.append(
            {
                "metric": metric,
                "start_year": start_year,
                "end_year": end_year,
                "start_value": start_value,
                "end_value": end_value,
                "difference": difference,
                "change_rate_pct": change_rate,
            }
        )

    return pd.DataFrame(rows)


def create_productivity_compensation_summary(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """労働生産性と1人当たり人件費の長期変化を比較する。"""

    required_metrics = {
        "labor_productivity",
        "personnel_expenses_per_employee",
        "labor_share",
    }

    available_metrics = set(comparison_df["metric"])

    missing_metrics = required_metrics - available_metrics

    if missing_metrics:
        raise ValueError(f"必要な指標がありません: {sorted(missing_metrics)}")

    indexed = comparison_df.set_index("metric")

    productivity_growth = indexed.loc[
        "labor_productivity",
        "change_rate_pct",
    ]

    compensation_growth = indexed.loc[
        "personnel_expenses_per_employee",
        "change_rate_pct",
    ]

    labor_share_change = indexed.loc[
        "labor_share",
        "difference",
    ]

    return pd.DataFrame(
        [
            {
                "labor_productivity_growth_pct": productivity_growth,
                "personnel_expenses_per_employee_growth_pct": compensation_growth,
                "growth_gap_pct_point": (
                    productivity_growth - compensation_growth
                ),
                "labor_share_change_pct_point": labor_share_change,
            }
        ]
    )


def create_corporate_yearly_change_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """企業パフォーマンス主要指標の前年比・前年差を作成する。"""

    required_columns = {
        "fiscal_year",
        "labor_productivity",
        "personnel_expenses_per_employee",
        "labor_share",
        "operating_profit_margin",
        "ordinary_profit_margin",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"前年比計算に必要な列がありません: {sorted(missing_columns)}")

    result = (
        df.sort_values("fiscal_year")
        .reset_index(drop=True)
        .copy()
    )

    result["labor_productivity_yoy_pct"] = (
        result["labor_productivity"].pct_change(fill_method=None) * 100
    )

    result["personnel_expenses_per_employee_yoy_pct"] = (
        result["personnel_expenses_per_employee"]
        .pct_change(fill_method=None)
        * 100
    )

    result["productivity_compensation_gap_pct_point"] = (
        result["labor_productivity_yoy_pct"]
        - result["personnel_expenses_per_employee_yoy_pct"]
    )

    result["labor_share_change_pct_point"] = (
        result["labor_share"].diff()
    )

    result["operating_profit_margin_change_pct_point"] = (
        result["operating_profit_margin"].diff()
    )

    result["ordinary_profit_margin_change_pct_point"] = (
        result["ordinary_profit_margin"].diff()
    )

    return result


def create_period_comparison_summary(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> dict[str, float]:
    """指定期間の主要指標の変化を要約する。"""

    start_rows = df.loc[df["fiscal_year"] == start_year]
    end_rows = df.loc[df["fiscal_year"] == end_year]

    if len(start_rows) != 1 or len(end_rows) != 1:
        raise ValueError("指定年度のデータが一意に取得できません。")

    start_row = start_rows.iloc[0]
    end_row = end_rows.iloc[0]

    productivity_growth = (
        end_row["labor_productivity"]
        / start_row["labor_productivity"]
        - 1
    ) * 100

    compensation_growth = (
        end_row["personnel_expenses_per_employee"]
        / start_row["personnel_expenses_per_employee"]
        - 1
    ) * 100

    return {
        "start_year": start_year,
        "end_year": end_year,
        "labor_productivity_growth_pct": productivity_growth,
        "personnel_expenses_per_employee_growth_pct": compensation_growth,
        "growth_gap_pct_point": (
            productivity_growth - compensation_growth
        ),
        "labor_share_change_pct_point": (
            end_row["labor_share"] - start_row["labor_share"]
        ),
        "operating_profit_margin_change_pct_point": (
            end_row["operating_profit_margin"]
            - start_row["operating_profit_margin"]
        ),
        "ordinary_profit_margin_change_pct_point": (
            end_row["ordinary_profit_margin"]
            - start_row["ordinary_profit_margin"]
        ),
    }
