import pandas as pd

from real_wage_dashboard.wage_analysis import add_moving_average

WAGE_COMPONENT_COLUMNS = {
    "現金給与総額": "total_cash_earnings",
    "きまって支給する給与": "regular_earnings",
    "所定内給与": "scheduled_earnings",
    "所定外給与": "overtime_earnings",
    "特別給与": "special_earnings",
}


def create_wage_composition_dataframe(
    raw_df: pd.DataFrame,
    establishment_size: str = "T",
    employment_type: str = "0",
) -> pd.DataFrame:
    """毎月勤労統計から給与構成分析用の月次DataFrameを作成する。"""

    required_columns = {
        "年",
        "月",
        "産業分類",
        "規模",
        "就業形態",
        *WAGE_COMPONENT_COLUMNS.keys(),
    }

    if not required_columns.issubset(raw_df.columns):
        missing = required_columns - set(raw_df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    industry = raw_df["産業分類"].astype(str).str.strip()
    size = raw_df["規模"].astype(str).str.strip()
    employment = raw_df["就業形態"].astype(str).str.strip()
    month = raw_df["月"].astype(str).str.strip()

    df = raw_df.loc[
        (industry == "TL")
        & (size == establishment_size)
        & (employment == employment_type)
        & (month != "CY"),
        [
            "年",
            "月",
            *WAGE_COMPONENT_COLUMNS.keys(),
        ],
    ].copy()

    if df.empty:
        raise ValueError("選択した条件に該当する給与構成データがありません。")

    # 年月
    df["year"] = pd.to_numeric(
        df["年"],
        errors="coerce",
    )

    df["month_num"] = pd.to_numeric(
        df["月"],
        errors="coerce",
    )

    df["date"] = pd.to_datetime(
        {
            "year": df["year"],
            "month": df["month_num"],
            "day": 1,
        },
        errors="coerce",
    )

    # 給与系列
    df = df.rename(columns=WAGE_COMPONENT_COLUMNS)

    wage_columns = list(WAGE_COMPONENT_COLUMNS.values())

    for column in wage_columns:
        df[column] = pd.to_numeric(
            df[column].astype(str).str.replace(",", "", regex=False).str.strip(),
            errors="coerce",
        )

    # 日付または給与系列のどれかが欠損している行は分析対象外
    df = df.dropna(
        subset=[
            "date",
            *wage_columns,
        ]
    )

    if df.empty:
        raise ValueError("選択した条件では有効な給与構成データを取得できません。")

    # 同一年月が複数存在する場合は、黙って削除せず異常として扱う
    if df["date"].duplicated().any():
        raise ValueError("給与構成データに重複年月があります。")

    df = df.sort_values("date").reset_index(drop=True)

    return df[
        [
            "date",
            "total_cash_earnings",
            "regular_earnings",
            "scheduled_earnings",
            "overtime_earnings",
            "special_earnings",
        ]
    ]


def add_wage_composition_changes(df: pd.DataFrame) -> pd.DataFrame:
    """給与構成各系列の前年差・前年同月比を追加する。"""

    wage_columns = [
        "total_cash_earnings",
        "regular_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    ]

    required_columns = {
        "date",
        *wage_columns,
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    periods = result["date"].dt.to_period("M")
    month_number = periods.dt.year * 12 + periods.dt.month

    # 12行前が実際に12か月前か確認
    continuous_12m = month_number - month_number.shift(12) == 12

    for column in wage_columns:
        previous = result[column].shift(12)

        yoy_diff = result[column] - previous

        yoy_pct = (result[column] / previous - 1).mul(100)

        result[f"{column}_yoy_diff"] = yoy_diff.where(continuous_12m)

        result[f"{column}_yoy_pct"] = yoy_pct.where(continuous_12m)

    return result


def add_wage_composition_contributions(df: pd.DataFrame) -> pd.DataFrame:
    """現金給与総額の前年同月比に対する各給与項目の寄与度を追加する。"""

    required_columns = {
        "date",
        "total_cash_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    periods = result["date"].dt.to_period("M")
    month_number = periods.dt.year * 12 + periods.dt.month

    continuous_12m = month_number - month_number.shift(12) == 12

    previous_total = result["total_cash_earnings"].shift(12)

    if (previous_total.dropna() <= 0).any():
        raise ValueError("前年の現金給与総額は0より大きい必要があります。")

    components = [
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    ]

    contribution_columns = []

    for column in components:
        previous = result[column].shift(12)

        contribution_column = f"{column}_contribution_pt"

        result[contribution_column] = (
            (result[column] - previous) / previous_total * 100
        ).where(continuous_12m)

        contribution_columns.append(contribution_column)

    result["contribution_total_pt"] = result[contribution_columns].sum(
        axis=1, min_count=len(contribution_columns)
    )

    result["total_cash_earnings_yoy_pct"] = (
        (result["total_cash_earnings"] / previous_total - 1) * 100
    ).where(continuous_12m)

    result["contribution_error_pt"] = (
        result["total_cash_earnings_yoy_pct"] - result["contribution_total_pt"]
    )

    return result


def add_wage_composition_shares(df: pd.DataFrame) -> pd.DataFrame:
    """現金給与総額に占める各給与項目の構成比を追加する。"""

    required_columns = {
        "total_cash_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    if (result["total_cash_earnings"] <= 0).any():
        raise ValueError("現金給与総額は0より大きい必要があります。")

    result["scheduled_earnings_share_pct"] = (
        result["scheduled_earnings"] / result["total_cash_earnings"] * 100
    )

    result["overtime_earnings_share_pct"] = (
        result["overtime_earnings"] / result["total_cash_earnings"] * 100
    )

    result["special_earnings_share_pct"] = (
        result["special_earnings"] / result["total_cash_earnings"] * 100
    )

    return result


def add_wage_composition_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """給与構成各系列の12か月移動平均を追加する。"""

    columns = [
        "total_cash_earnings",
        "regular_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    ]

    result = df.copy()

    for column in columns:
        result = add_moving_average(
            result,
            column=column,
            output_column=f"{column}_ma_12",
            window=12,
        )

    return result


def create_annual_wage_composition_summary(
    df: pd.DataFrame,
    years: list[int],
) -> pd.DataFrame:
    """指定年について12か月平均の給与構成サマリーを作成する。"""

    required_columns = {
        "date",
        "total_cash_earnings",
        "regular_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result_rows = []

    for year in years:
        year_df = df[df["date"].dt.year == year].copy()

        months = year_df["date"].dt.to_period("M").nunique()

        if months != 12:
            raise ValueError(f"{year}年のデータが12か月揃っていません。")

        row = {
            "year": year,
            "total_cash_earnings": year_df["total_cash_earnings"].mean(),
            "regular_earnings": year_df["regular_earnings"].mean(),
            "scheduled_earnings": year_df["scheduled_earnings"].mean(),
            "overtime_earnings": year_df["overtime_earnings"].mean(),
            "special_earnings": year_df["special_earnings"].mean(),
        }

        result_rows.append(row)

    result = pd.DataFrame(result_rows)

    result["scheduled_share_pct"] = (
        result["scheduled_earnings"] / result["total_cash_earnings"] * 100
    )

    result["overtime_share_pct"] = (
        result["overtime_earnings"] / result["total_cash_earnings"] * 100
    )

    result["special_share_pct"] = (
        result["special_earnings"] / result["total_cash_earnings"] * 100
    )

    return result


def create_long_term_wage_composition_comparison(
    annual_df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """2時点の年平均給与を比較し、現金給与総額の変化を寄与度分解する。"""

    required_columns = {
        "year",
        "total_cash_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    }

    if not required_columns.issubset(annual_df.columns):
        missing = required_columns - set(annual_df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    start = annual_df.loc[annual_df["year"] == start_year]
    end = annual_df.loc[annual_df["year"] == end_year]

    if len(start) != 1 or len(end) != 1:
        raise ValueError("比較対象年のデータを一意に取得できません。")

    start = start.iloc[0]
    end = end.iloc[0]

    start_total = start["total_cash_earnings"]

    components = [
        "total_cash_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    ]

    rows = []

    for column in components:
        start_value = start[column]
        end_value = end[column]

        diff = end_value - start_value
        pct_change = (end_value / start_value - 1) * 100

        row = {
            "component": column,
            "start_value": start_value,
            "end_value": end_value,
            "difference": diff,
            "pct_change": pct_change,
        }

        if column != "total_cash_earnings":
            row["contribution_pt"] = diff / start_total * 100
        else:
            row["contribution_pt"] = pct_change

        rows.append(row)

    return pd.DataFrame(rows)


def create_complete_annual_wage_composition_summary(df: pd.DataFrame) -> pd.DataFrame:
    """12か月揃っている年について給与構成年平均を作成する。"""

    required_columns = {
        "date",
        "total_cash_earnings",
        "regular_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()
    result["year"] = result["date"].dt.year
    result["month"] = result["date"].dt.month

    complete_years = (
        result.groupby("year")["month"].nunique().loc[lambda x: x == 12].index
    )

    result = result[result["year"].isin(complete_years)]

    annual = (
        result.groupby("year", as_index=False)[
            [
                "total_cash_earnings",
                "regular_earnings",
                "scheduled_earnings",
                "overtime_earnings",
                "special_earnings",
            ]
        ]
        .mean()
        .sort_values("year")
        .reset_index(drop=True)
    )

    return annual


def add_annual_wage_contributions(annual_df: pd.DataFrame) -> pd.DataFrame:
    """年平均現金給与総額の前年比を給与3要素へ分解する。"""

    required_columns = {
        "year",
        "total_cash_earnings",
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    }

    if not required_columns.issubset(annual_df.columns):
        missing = required_columns - set(annual_df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = annual_df.sort_values("year").reset_index(drop=True).copy()

    previous_total = result["total_cash_earnings"].shift(1)
    previous_year = result["year"].shift(1)

    continuous_year = result["year"] - previous_year == 1

    result["total_yoy_pct"] = (
        (result["total_cash_earnings"] / previous_total - 1) * 100
    ).where(continuous_year)

    for column in [
        "scheduled_earnings",
        "overtime_earnings",
        "special_earnings",
    ]:
        result[f"{column}_contribution_pt"] = (
            (result[column] - result[column].shift(1)) / previous_total * 100
        ).where(continuous_year)

    result["contribution_total_pt"] = result[
        [
            "scheduled_earnings_contribution_pt",
            "overtime_earnings_contribution_pt",
            "special_earnings_contribution_pt",
        ]
    ].sum(axis=1, min_count=3)

    return result
