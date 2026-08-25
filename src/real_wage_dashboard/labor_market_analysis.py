import pandas as pd


def calculate_lag_correlations(
    df: pd.DataFrame,
    labor_market_column: str,
    wage_column: str = "scheduled_cash_earnings_yoy",
    max_lag: int = 12,
) -> pd.DataFrame:
    """労働需給指標の先行ラグと賃金前年比の相関を計算する。"""

    sorted_df = df.sort_values("date").reset_index(drop=True).copy()

    results = []

    for lag in range(max_lag + 1):
        lagged_labor_market = sorted_df[labor_market_column].shift(lag)

        valid_df = pd.DataFrame(
            {
                "labor_market": lagged_labor_market,
                "wage": sorted_df[wage_column],
            }
        ).dropna()

        correlation = valid_df["labor_market"].corr(valid_df["wage"])

        results.append(
            {
                "lag_months": lag,
                "correlation": correlation,
                "observation_count": len(valid_df),
            }
        )

    return pd.DataFrame(results)


def add_labor_market_regime(df: pd.DataFrame) -> pd.DataFrame:
    """分析期間に局面区分を付与する。"""

    result = df.copy()

    result["regime"] = pd.NA

    result.loc[
        result["date"].between("2000-01-01", "2012-12-01"),
        "regime",
    ] = "2000年代～震災後"

    result.loc[
        result["date"].between("2013-01-01", "2019-12-01"),
        "regime",
    ] = "雇用改善期"

    result.loc[
        result["date"].between("2020-01-01", "2021-12-01"),
        "regime",
    ] = "コロナ期"

    result.loc[
        result["date"].between("2022-01-01", "2025-12-01"),
        "regime",
    ] = "物価上昇・賃上げ期"

    return result


def calculate_regime_correlations(
    df: pd.DataFrame,
    labor_market_columns: dict[str, str],
    wage_column: str = "scheduled_cash_earnings_yoy",
) -> pd.DataFrame:
    """局面別に労働需給指標と賃金前年比の相関を計算する。"""

    results = []

    for regime, regime_df in df.groupby("regime", sort=False):
        for indicator_name, column_name in labor_market_columns.items():
            valid_df = regime_df[[column_name, wage_column]].dropna()

            correlation = valid_df[column_name].corr(valid_df[wage_column])

            results.append(
                {
                    "regime": regime,
                    "indicator": indicator_name,
                    "correlation": correlation,
                    "observation_count": len(valid_df),
                }
            )

    return pd.DataFrame(results)


def calculate_regime_lag_correlations(
    df: pd.DataFrame,
    labor_market_columns: dict[str, str],
    wage_column: str = "scheduled_cash_earnings_yoy",
    max_lag: int = 12,
    analysis_start: str = "2000-01-01",
    analysis_end: str = "2025-12-01",
) -> pd.DataFrame:
    """局面別に労働需給指標の先行ラグと賃金前年比の相関を計算する。

    ラグは分析期間以前のデータも含めて作成し、
    相関計算時に分析対象期間へ絞り込む。
    """

    sorted_df = df.sort_values("date").reset_index(drop=True).copy()

    results = []

    for indicator_name, column_name in labor_market_columns.items():
        for lag in range(max_lag + 1):
            lagged_column = f"_lag_{lag}"

            sorted_df[lagged_column] = sorted_df[column_name].shift(lag)

            analysis_df = sorted_df.loc[
                sorted_df["date"].between(
                    analysis_start,
                    analysis_end,
                )
            ]

            for regime, regime_df in analysis_df.groupby(
                "regime",
                sort=False,
            ):
                valid_df = regime_df[[lagged_column, wage_column]].dropna()

                correlation = valid_df[lagged_column].corr(valid_df[wage_column])

                results.append(
                    {
                        "regime": regime,
                        "indicator": indicator_name,
                        "lag_months": lag,
                        "correlation": correlation,
                        "observation_count": len(valid_df),
                    }
                )

            sorted_df.drop(
                columns=lagged_column,
                inplace=True,
            )

    return pd.DataFrame(results)


def create_quarterly_wage_dataframe(
    df: pd.DataFrame,
    wage_column: str = "scheduled_cash_earnings_yoy",
) -> pd.DataFrame:
    """月次の賃金前年比を四半期平均に変換する。"""

    result = df[
        [
            "date",
            wage_column,
        ]
    ].copy()

    result["quarter"] = result["date"].dt.to_period("Q")

    quarterly_df = result.groupby("quarter", as_index=False)[wage_column].mean()

    quarterly_df["date"] = (
        quarterly_df["quarter"].dt.end_time.dt.to_period("M").dt.to_timestamp()
    )

    return quarterly_df[
        [
            "date",
            wage_column,
        ]
    ]


def calculate_quarterly_lag_correlations(
    df: pd.DataFrame,
    labor_market_column: str,
    wage_column: str = "scheduled_cash_earnings_yoy",
    max_lag: int = 4,
) -> pd.DataFrame:
    """四半期データの先行ラグと賃金前年比の相関を計算する。"""

    sorted_df = df.sort_values("date").reset_index(drop=True).copy()

    results = []

    for lag in range(max_lag + 1):
        lagged_labor_market = sorted_df[labor_market_column].shift(lag)

        valid_df = pd.DataFrame(
            {
                "labor_market": lagged_labor_market,
                "wage": sorted_df[wage_column],
            }
        ).dropna()

        correlation = valid_df["labor_market"].corr(valid_df["wage"])

        results.append(
            {
                "lag_quarters": lag,
                "lag_months": lag * 3,
                "correlation": correlation,
                "observation_count": len(valid_df),
            }
        )

    return pd.DataFrame(results)

def add_labor_market_tightness_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """労働需給指標を、値が大きいほど逼迫する方向に統一する。"""

    result = df.copy()

    result["labor_market_tightness_effective_jobs"] = result[
        "effective_job_openings_ratio"
    ]

    result["labor_market_tightness_unemployment"] = -result[
        "unemployment_rate"
    ]

    result["labor_market_tightness_new_jobs"] = result[
        "new_job_openings_ratio"
    ]

    return result


def calculate_correlations(
    df: pd.DataFrame,
    labor_market_columns: dict[str, str],
    wage_column: str = "scheduled_cash_earnings_yoy",
) -> pd.DataFrame:
    """労働需給指標と賃金前年比の同時点相関を計算する。"""

    results = []

    for indicator_name, column_name in labor_market_columns.items():
        valid_df = df[
            [
                column_name,
                wage_column,
            ]
        ].dropna()

        correlation = valid_df[
            column_name
        ].corr(
            valid_df[wage_column]
        )

        results.append(
            {
                "indicator": indicator_name,
                "correlation": correlation,
                "observation_count": len(valid_df),
            }
        )

    return pd.DataFrame(results)
