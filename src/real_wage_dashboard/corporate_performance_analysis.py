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
            f"{start_year}年度のデータが1件ではありません: {len(start_rows)}件"
        )

    if len(end_rows) != 1:
        raise ValueError(
            f"{end_year}年度のデータが1件ではありません: {len(end_rows)}件"
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
            change_rate = (end_value / start_value - 1) * 100

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


def create_productivity_compensation_summary(
    comparison_df: pd.DataFrame,
) -> pd.DataFrame:
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
                "growth_gap_pct_point": (productivity_growth - compensation_growth),
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

    result = df.sort_values("fiscal_year").reset_index(drop=True).copy()

    result["labor_productivity_yoy_pct"] = (
        result["labor_productivity"].pct_change(fill_method=None) * 100
    )

    result["personnel_expenses_per_employee_yoy_pct"] = (
        result["personnel_expenses_per_employee"].pct_change(fill_method=None) * 100
    )

    result["productivity_compensation_gap_pct_point"] = (
        result["labor_productivity_yoy_pct"]
        - result["personnel_expenses_per_employee_yoy_pct"]
    )

    result["labor_share_change_pct_point"] = result["labor_share"].diff()

    result["operating_profit_margin_change_pct_point"] = result[
        "operating_profit_margin"
    ].diff()

    result["ordinary_profit_margin_change_pct_point"] = result[
        "ordinary_profit_margin"
    ].diff()

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
        end_row["labor_productivity"] / start_row["labor_productivity"] - 1
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
        "growth_gap_pct_point": (productivity_growth - compensation_growth),
        "labor_share_change_pct_point": (
            end_row["labor_share"] - start_row["labor_share"]
        ),
        "operating_profit_margin_change_pct_point": (
            end_row["operating_profit_margin"] - start_row["operating_profit_margin"]
        ),
        "ordinary_profit_margin_change_pct_point": (
            end_row["ordinary_profit_margin"] - start_row["ordinary_profit_margin"]
        ),
    }


def create_capital_class_comparison_dataframe(
    dataframes: dict[str, pd.DataFrame],
    start_year: int = CORPORATE_ANALYSIS_START_YEAR,
    end_year: int = CORPORATE_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """企業規模別に開始年度と終了年度の主要指標を比較する。"""

    rows = []

    for capital_class, df in dataframes.items():
        comparison_df = create_corporate_comparison_dataframe(
            df,
            start_year=start_year,
            end_year=end_year,
        )

        indexed = comparison_df.set_index("metric")

        rows.append(
            {
                "capital_class": capital_class,
                "start_year": start_year,
                "end_year": end_year,
                "labor_productivity_start": indexed.loc[
                    "labor_productivity",
                    "start_value",
                ],
                "labor_productivity_end": indexed.loc[
                    "labor_productivity",
                    "end_value",
                ],
                "labor_productivity_growth_pct": indexed.loc[
                    "labor_productivity",
                    "change_rate_pct",
                ],
                "personnel_expenses_per_employee_start": indexed.loc[
                    "personnel_expenses_per_employee",
                    "start_value",
                ],
                "personnel_expenses_per_employee_end": indexed.loc[
                    "personnel_expenses_per_employee",
                    "end_value",
                ],
                "personnel_expenses_per_employee_growth_pct": indexed.loc[
                    "personnel_expenses_per_employee",
                    "change_rate_pct",
                ],
                "growth_gap_pct_point": (
                    indexed.loc[
                        "labor_productivity",
                        "change_rate_pct",
                    ]
                    - indexed.loc[
                        "personnel_expenses_per_employee",
                        "change_rate_pct",
                    ]
                ),
                "labor_share_start": indexed.loc[
                    "labor_share",
                    "start_value",
                ],
                "labor_share_end": indexed.loc[
                    "labor_share",
                    "end_value",
                ],
                "labor_share_change_pct_point": indexed.loc[
                    "labor_share",
                    "difference",
                ],
                "operating_profit_margin_start": indexed.loc[
                    "operating_profit_margin",
                    "start_value",
                ],
                "operating_profit_margin_end": indexed.loc[
                    "operating_profit_margin",
                    "end_value",
                ],
                "operating_profit_margin_change_pct_point": indexed.loc[
                    "operating_profit_margin",
                    "difference",
                ],
                "ordinary_profit_margin_start": indexed.loc[
                    "ordinary_profit_margin",
                    "start_value",
                ],
                "ordinary_profit_margin_end": indexed.loc[
                    "ordinary_profit_margin",
                    "end_value",
                ],
                "ordinary_profit_margin_change_pct_point": indexed.loc[
                    "ordinary_profit_margin",
                    "difference",
                ],
            }
        )

    return pd.DataFrame(rows)


def create_industry_comparison_dataframe(
    dataframes: dict[str, pd.DataFrame],
    start_year: int = CORPORATE_ANALYSIS_START_YEAR,
    end_year: int = CORPORATE_ANALYSIS_END_YEAR,
) -> pd.DataFrame:
    """産業別に開始年度と終了年度の主要指標を比較する。"""

    rows = []

    for industry_code, df in dataframes.items():
        comparison_df = create_corporate_comparison_dataframe(
            df,
            start_year=start_year,
            end_year=end_year,
        )

        indexed = comparison_df.set_index("metric")

        rows.append(
            {
                "industry": industry_code,
                "start_year": start_year,
                "end_year": end_year,
                "labor_productivity_start": indexed.loc[
                    "labor_productivity",
                    "start_value",
                ],
                "labor_productivity_end": indexed.loc[
                    "labor_productivity",
                    "end_value",
                ],
                "labor_productivity_growth_pct": indexed.loc[
                    "labor_productivity",
                    "change_rate_pct",
                ],
                "personnel_expenses_per_employee_start": indexed.loc[
                    "personnel_expenses_per_employee",
                    "start_value",
                ],
                "personnel_expenses_per_employee_end": indexed.loc[
                    "personnel_expenses_per_employee",
                    "end_value",
                ],
                "personnel_expenses_per_employee_growth_pct": indexed.loc[
                    "personnel_expenses_per_employee",
                    "change_rate_pct",
                ],
                "growth_gap_pct_point": (
                    indexed.loc[
                        "labor_productivity",
                        "change_rate_pct",
                    ]
                    - indexed.loc[
                        "personnel_expenses_per_employee",
                        "change_rate_pct",
                    ]
                ),
                "labor_share_start": indexed.loc[
                    "labor_share",
                    "start_value",
                ],
                "labor_share_end": indexed.loc[
                    "labor_share",
                    "end_value",
                ],
                "labor_share_change_pct_point": indexed.loc[
                    "labor_share",
                    "difference",
                ],
                "operating_profit_margin_start": indexed.loc[
                    "operating_profit_margin",
                    "start_value",
                ],
                "operating_profit_margin_end": indexed.loc[
                    "operating_profit_margin",
                    "end_value",
                ],
                "operating_profit_margin_change_pct_point": indexed.loc[
                    "operating_profit_margin",
                    "difference",
                ],
                "ordinary_profit_margin_start": indexed.loc[
                    "ordinary_profit_margin",
                    "start_value",
                ],
                "ordinary_profit_margin_end": indexed.loc[
                    "ordinary_profit_margin",
                    "end_value",
                ],
                "ordinary_profit_margin_change_pct_point": indexed.loc[
                    "ordinary_profit_margin",
                    "difference",
                ],
            }
        )

    return pd.DataFrame(rows)


def merge_corporate_and_wage_industry_comparison(
    corporate_df: pd.DataFrame,
    wage_df: pd.DataFrame,
) -> pd.DataFrame:
    """法人企業統計と毎月勤労統計の産業別比較結果を結合する。"""

    required_corporate_columns = {
        "industry",
        "labor_productivity_growth_pct",
        "personnel_expenses_per_employee_growth_pct",
        "growth_gap_pct_point",
        "labor_share_change_pct_point",
        "operating_profit_margin_change_pct_point",
        "ordinary_profit_margin_change_pct_point",
    }

    required_wage_columns = {
        "industry",
        "monthly_wage_change_pct",
        "hourly_wage_change_pct",
        "total_hours_change_pct",
    }

    missing_corporate = required_corporate_columns - set(corporate_df.columns)

    if missing_corporate:
        raise ValueError(
            f"法人企業統計側に必要な列がありません: {sorted(missing_corporate)}"
        )

    missing_wage = required_wage_columns - set(wage_df.columns)

    if missing_wage:
        raise ValueError(f"毎勤側に必要な列がありません: {sorted(missing_wage)}")

    result = corporate_df.merge(
        wage_df[
            [
                "industry",
                "monthly_wage_change_pct",
                "hourly_wage_change_pct",
                "total_hours_change_pct",
            ]
        ],
        on="industry",
        how="inner",
        validate="one_to_one",
    )

    return result


def calculate_corporate_wage_industry_correlations(
    df: pd.DataFrame,
) -> dict[str, float]:
    """産業横断で企業業績指標と賃金変化率の相関を算出する。"""

    required_columns = {
        "labor_productivity_growth_pct",
        "personnel_expenses_per_employee_growth_pct",
        "labor_share_change_pct_point",
        "ordinary_profit_margin_change_pct_point",
        "monthly_wage_change_pct",
        "hourly_wage_change_pct",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"相関計算に必要な列がありません: {sorted(missing_columns)}")

    return {
        "productivity_vs_monthly_wage": df["labor_productivity_growth_pct"].corr(
            df["monthly_wage_change_pct"]
        ),
        "productivity_vs_hourly_wage": df["labor_productivity_growth_pct"].corr(
            df["hourly_wage_change_pct"]
        ),
        "personnel_expenses_vs_monthly_wage": df[
            "personnel_expenses_per_employee_growth_pct"
        ].corr(df["monthly_wage_change_pct"]),
        "personnel_expenses_vs_hourly_wage": df[
            "personnel_expenses_per_employee_growth_pct"
        ].corr(df["hourly_wage_change_pct"]),
        "ordinary_profit_margin_vs_monthly_wage": df[
            "ordinary_profit_margin_change_pct_point"
        ].corr(df["monthly_wage_change_pct"]),
        "ordinary_profit_margin_vs_hourly_wage": df[
            "ordinary_profit_margin_change_pct_point"
        ].corr(df["hourly_wage_change_pct"]),
        "labor_share_vs_monthly_wage": df["labor_share_change_pct_point"].corr(
            df["monthly_wage_change_pct"]
        ),
        "labor_share_vs_hourly_wage": df["labor_share_change_pct_point"].corr(
            df["hourly_wage_change_pct"]
        ),
    }


def calculate_leave_one_out_correlations(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """1産業ずつ除外した場合の相関係数を算出する。"""

    required_columns = {
        "industry",
        "labor_productivity_growth_pct",
        "monthly_wage_change_pct",
        "hourly_wage_change_pct",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"感応度分析に必要な列がありません: {sorted(missing_columns)}")

    rows = []

    for industry in df["industry"]:
        subset = df.loc[df["industry"] != industry]

        rows.append(
            {
                "excluded_industry": industry,
                "observation_count": len(subset),
                "productivity_vs_monthly_wage": subset[
                    "labor_productivity_growth_pct"
                ].corr(subset["monthly_wage_change_pct"]),
                "productivity_vs_hourly_wage": subset[
                    "labor_productivity_growth_pct"
                ].corr(subset["hourly_wage_change_pct"]),
            }
        )

    return pd.DataFrame(rows)
