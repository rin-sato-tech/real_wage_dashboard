import numpy as np
import pandas as pd


def merge_wage_and_working_hours(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
) -> pd.DataFrame:
    """月次賃金と労働時間を年月でone-to-one結合する。"""

    wage_required = {
        "date",
        "nominal_wage_amount",
    }

    hours_required = {
        "date",
        "working_hours",
    }

    if not wage_required.issubset(wage_df.columns):
        missing = wage_required - set(wage_df.columns)
        raise ValueError(f"賃金データに必要な列がありません: {sorted(missing)}")

    if not hours_required.issubset(working_hours_df.columns):
        missing = hours_required - set(working_hours_df.columns)
        raise ValueError(f"労働時間データに必要な列がありません: {sorted(missing)}")

    wage = wage_df[
        [
            "date",
            "nominal_wage_amount",
        ]
    ].copy()

    hours = working_hours_df[
        [
            "date",
            "working_hours",
        ]
    ].copy()

    result = wage.merge(
        hours,
        on="date",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


def add_approx_hourly_wage(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """月額賃金と総実労働時間から概算時間当たり賃金を算出する。"""

    required_columns = {
        "nominal_wage_amount",
        "working_hours",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    if (result["working_hours"] <= 0).any():
        raise ValueError("労働時間は0より大きい必要があります。")

    result["approx_hourly_wage"] = (
        result["nominal_wage_amount"] / result["working_hours"]
    )

    return result


def create_employment_analysis_dataframe(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
) -> pd.DataFrame:
    """賃金・労働時間・概算時間当たり賃金をまとめたDataFrameを作成する。"""

    result = merge_wage_and_working_hours(
        wage_df,
        working_hours_df,
    )

    result = add_approx_hourly_wage(result)

    return result


def add_base_year_index(
    df: pd.DataFrame,
    column: str,
    output_column: str,
    base_year: int = 2020,
) -> pd.DataFrame:
    """指定列を基準年平均=100として指数化する。"""

    required_columns = {
        "date",
        column,
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    base_df = result[result["date"].dt.year == base_year].copy()

    base_months = base_df["date"].dt.to_period("M").drop_duplicates()

    if len(base_months) != 12:
        raise ValueError(f"{base_year}年の基準データが12か月揃っていません。")

    base_value = base_df[column].mean()

    if pd.isna(base_value) or base_value <= 0:
        raise ValueError("基準年平均は0より大きい必要があります。")

    result[output_column] = result[column] / base_value * 100

    return result


def add_employment_comparison_indices(
    df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """雇用形態比較で使用する2020年基準指数を追加する。"""

    index_columns = {
        "nominal_wage_amount": "regular_wage_index",
        "working_hours": "working_hours_index",
        "approx_hourly_wage": "approx_hourly_wage_index",
    }

    result = df.copy()

    for column, output_column in index_columns.items():
        result = add_base_year_index(
            result,
            column=column,
            output_column=output_column,
            base_year=base_year,
        )

    return result


def add_employment_changes(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態比較で使用する主要指標の前年同月比を追加する。"""

    required_columns = {
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    result["regular_wage_yoy_pct"] = (
        result["nominal_wage_amount"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    result["working_hours_yoy_pct"] = (
        result["working_hours"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    result["approx_hourly_wage_yoy_pct"] = (
        result["approx_hourly_wage"]
        .pct_change(
            periods=12,
            fill_method=None,
        )
        .mul(100)
    )

    return result


def merge_employment_analysis_with_cpi(
    df: pd.DataFrame,
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態比較データとCPIを年月でone-to-one結合する。"""

    analysis_required = {
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
    }

    cpi_required = {
        "date",
        "index_value",
    }

    if not analysis_required.issubset(df.columns):
        missing = analysis_required - set(df.columns)
        raise ValueError(f"雇用形態比較データに必要な列がありません: {sorted(missing)}")

    if not cpi_required.issubset(cpi_df.columns):
        missing = cpi_required - set(cpi_df.columns)
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing)}")

    analysis = df.copy()

    cpi = cpi_df[
        [
            "date",
            "index_value",
        ]
    ].copy()

    result = analysis.merge(
        cpi,
        on="date",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


def add_real_employment_values(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """CPIで実質月額賃金と実質概算時間当たり賃金を算出する。"""

    required_columns = {
        "nominal_wage_amount",
        "approx_hourly_wage",
        "index_value",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    if (result["index_value"] <= 0).any():
        raise ValueError("CPIには0より大きい値が必要です。")

    result["real_regular_wage"] = (
        result["nominal_wage_amount"] / result["index_value"] * 100
    )

    result["real_approx_hourly_wage"] = (
        result["approx_hourly_wage"] / result["index_value"] * 100
    )

    return result


def add_real_employment_analysis(
    df: pd.DataFrame,
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態比較データにCPIと実質値を追加する。"""

    result = merge_employment_analysis_with_cpi(
        df,
        cpi_df,
    )

    result = add_real_employment_values(result)

    return result


def add_real_employment_indices(
    df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """実質賃金系の2020年基準指数を追加する。"""

    result = df.copy()

    result = add_base_year_index(
        result,
        column="real_regular_wage",
        output_column="real_regular_wage_index",
        base_year=base_year,
    )

    result = add_base_year_index(
        result,
        column="real_approx_hourly_wage",
        output_column="real_approx_hourly_wage_index",
        base_year=base_year,
    )

    return result


def add_real_employment_changes(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """実質賃金系の前年同月比を追加する。"""

    required_columns = {
        "date",
        "real_regular_wage",
        "real_approx_hourly_wage",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    result["real_regular_wage_yoy_pct"] = (
        result["real_regular_wage"].pct_change(periods=12, fill_method=None).mul(100)
    )

    result["real_approx_hourly_wage_yoy_pct"] = (
        result["real_approx_hourly_wage"]
        .pct_change(periods=12, fill_method=None)
        .mul(100)
    )

    return result


def add_wage_change_decomposition(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """月額賃金の前年同月変化を時間当たり賃金要因と労働時間要因に分解する。"""

    required_columns = {
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    if (
        (result["nominal_wage_amount"] <= 0).any()
        or (result["working_hours"] <= 0).any()
        or (result["approx_hourly_wage"] <= 0).any()
    ):
        raise ValueError("要因分解には0より大きい賃金・労働時間データが必要です。")

    result["wage_log_change"] = (
        np.log(result["nominal_wage_amount"])
        - np.log(result["nominal_wage_amount"].shift(12))
    ) * 100

    result["hourly_wage_log_contribution"] = (
        np.log(result["approx_hourly_wage"])
        - np.log(result["approx_hourly_wage"].shift(12))
    ) * 100

    result["working_hours_log_contribution"] = (
        np.log(result["working_hours"]) - np.log(result["working_hours"].shift(12))
    ) * 100

    return result


def create_full_employment_analysis_dataframe(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """雇用形態比較に必要な分析列をまとめて作成する。"""

    result = create_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
    )

    result = add_employment_comparison_indices(
        result,
        base_year=base_year,
    )

    result = add_employment_changes(result)

    result = add_real_employment_analysis(
        result,
        cpi_df,
    )

    result = add_real_employment_indices(
        result,
        base_year=base_year,
    )

    result = add_real_employment_changes(result)

    result = add_wage_change_decomposition(result)

    return result


def calculate_yearly_averages(
    df: pd.DataFrame,
    year: int,
    columns: list[str],
) -> dict[str, float]:
    """指定年の12か月平均を算出する。"""

    required_columns = {
        "date",
        *columns,
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    year_df = df[df["date"].dt.year == year].copy()

    months = year_df["date"].dt.to_period("M")

    if len(year_df) != 12 or months.nunique() != 12:
        raise ValueError(f"{year}年のデータが12か月揃っていません。")

    if year_df[columns].isna().any().any():
        raise ValueError(f"{year}年の分析対象データに欠損値があります。")

    return {column: float(year_df[column].mean()) for column in columns}


def calculate_change_rate(
    start_value: float,
    end_value: float,
) -> float:
    """開始値から終了値までの変化率（%）を算出する。"""

    if start_value <= 0:
        raise ValueError("開始値は0より大きい必要があります。")

    return (end_value / start_value - 1) * 100


def calculate_yearly_change_rates(
    start_averages: dict[str, float],
    end_averages: dict[str, float],
) -> dict[str, float]:
    """2時点の年平均から各指標の変化率を算出する。"""

    if set(start_averages) != set(end_averages):
        raise ValueError("比較する年平均の指標が一致していません。")

    return {
        column: calculate_change_rate(
            start_averages[column],
            end_averages[column],
        )
        for column in start_averages
    }


def create_yearly_comparison_summary(
    general_df: pd.DataFrame,
    part_df: pd.DataFrame,
    start_year: int,
    end_year: int,
    columns: list[str],
) -> pd.DataFrame:
    """一般労働者とパートの年平均・変化率を比較用DataFrameにまとめる。"""

    rows = []

    for employment_type, df in [
        ("一般労働者", general_df),
        ("パートタイム労働者", part_df),
    ]:
        start_averages = calculate_yearly_averages(
            df,
            year=start_year,
            columns=columns,
        )

        end_averages = calculate_yearly_averages(
            df,
            year=end_year,
            columns=columns,
        )

        change_rates = calculate_yearly_change_rates(
            start_averages,
            end_averages,
        )

        for column in columns:
            rows.append(
                {
                    "employment_type": employment_type,
                    "indicator": column,
                    "start_year": start_year,
                    "start_value": start_averages[column],
                    "end_year": end_year,
                    "end_value": end_averages[column],
                    "change_rate_pct": change_rates[column],
                }
            )

    return pd.DataFrame(rows)


def compare_employment_change_rates(
    summary_df: pd.DataFrame,
) -> pd.DataFrame:
    """各指標について一般労働者とパートの変化率を比較する。"""

    required_columns = {
        "employment_type",
        "indicator",
        "change_rate_pct",
    }

    if not required_columns.issubset(summary_df.columns):
        missing = required_columns - set(summary_df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    pivot_df = summary_df.pivot(
        index="indicator",
        columns="employment_type",
        values="change_rate_pct",
    )

    required_employment_types = {
        "一般労働者",
        "パートタイム労働者",
    }

    if not required_employment_types.issubset(pivot_df.columns):
        raise ValueError("一般労働者とパートタイム労働者の両方のデータが必要です。")

    result = pivot_df.reset_index()

    result["difference_pct_point"] = result["パートタイム労働者"] - result["一般労働者"]

    result["larger_change"] = result["difference_pct_point"].map(
        lambda diff: (
            "パートタイム労働者" if diff > 0 else "一般労働者" if diff < 0 else "同程度"
        )
    )

    return result[
        [
            "indicator",
            "一般労働者",
            "パートタイム労働者",
            "difference_pct_point",
            "larger_change",
        ]
    ]


def describe_change_direction(
    value: float,
    tolerance: float = 0.1,
) -> str:
    """変化率を上昇・低下・横ばいに分類する。"""

    if value > tolerance:
        return "上昇"

    if value < -tolerance:
        return "低下"

    return "横ばい"


def create_employment_analysis_discussion(
    summary_df: pd.DataFrame,
    tolerance: float = 0.1,
) -> list[str]:
    """一般労働者とパートタイム労働者の比較結果から総合考察を生成する。"""

    def get_rate(
        employment_type: str,
        indicator: str,
    ) -> float:
        matched = summary_df[
            (summary_df["employment_type"] == employment_type)
            & (summary_df["indicator"] == indicator)
        ]

        if len(matched) != 1:
            raise ValueError(
                f"比較結果を一意に取得できません: {employment_type}, {indicator}"
            )

        return float(matched.iloc[0]["change_rate_pct"])

    general_wage = get_rate(
        "一般労働者",
        "nominal_wage_amount",
    )
    part_wage = get_rate(
        "パートタイム労働者",
        "nominal_wage_amount",
    )

    general_hours = get_rate(
        "一般労働者",
        "working_hours",
    )
    part_hours = get_rate(
        "パートタイム労働者",
        "working_hours",
    )

    general_hourly = get_rate(
        "一般労働者",
        "approx_hourly_wage",
    )
    part_hourly = get_rate(
        "パートタイム労働者",
        "approx_hourly_wage",
    )

    general_real_wage = get_rate(
        "一般労働者",
        "real_regular_wage",
    )
    part_real_wage = get_rate(
        "パートタイム労働者",
        "real_regular_wage",
    )

    discussions = []

    if (
        general_hourly > tolerance
        and part_hourly > tolerance
        and general_hours < -tolerance
        and part_hours < -tolerance
    ):
        discussions.append(
            "両就業形態とも、時間当たり賃金が上昇する一方で"
            "総実労働時間は減少しています。"
            "このため、時間当たり賃金の改善が月額賃金を押し上げる一方、"
            "労働時間の減少はその伸びを抑える方向に働いたと考えられます。"
        )

    hourly_difference = part_hourly - general_hourly
    hours_difference = part_hours - general_hours

    if hourly_difference > tolerance:
        text = "特にパートタイム労働者では、一般労働者より時間当たり賃金の伸びが大きく"

        if hours_difference < -tolerance:
            text += (
                "、同時に労働時間の減少も大きいため、"
                "時間当たり賃金の改善ほど月額賃金は伸びていません。"
            )
        else:
            text += "なっています。"

        discussions.append(text)

    if (
        general_wage > tolerance
        and part_wage > tolerance
        and general_real_wage < general_wage - tolerance
        and part_real_wage < part_wage - tolerance
    ):
        discussions.append(
            "また、両就業形態とも名目月額賃金の伸びに比べて"
            "実質月額賃金の伸びは小さく、"
            "物価上昇によって名目賃金の改善の一部が相殺されています。"
        )

    return discussions


def summarize_wage_change_decomposition(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> dict[str, float | int]:
    """指定期間の月額賃金要因分解を要約する。"""

    required_columns = {
        "date",
        "wage_log_change",
        "hourly_wage_log_contribution",
        "working_hours_log_contribution",
    }

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    period_df = df[
        (df["date"].dt.year >= start_year) & (df["date"].dt.year <= end_year)
    ][
        [
            "date",
            "wage_log_change",
            "hourly_wage_log_contribution",
            "working_hours_log_contribution",
        ]
    ].dropna()

    if period_df.empty:
        raise ValueError("指定期間に要因分解データがありません。")

    hourly_abs = period_df["hourly_wage_log_contribution"].abs()
    hours_abs = period_df["working_hours_log_contribution"].abs()

    return {
        "n_months": len(period_df),
        "mean_wage_log_change": float(period_df["wage_log_change"].mean()),
        "mean_hourly_wage_contribution": float(
            period_df["hourly_wage_log_contribution"].mean()
        ),
        "mean_working_hours_contribution": float(
            period_df["working_hours_log_contribution"].mean()
        ),
        "hourly_positive_share_pct": float(
            (period_df["hourly_wage_log_contribution"] > 0).mean() * 100
        ),
        "hours_negative_share_pct": float(
            (period_df["working_hours_log_contribution"] < 0).mean() * 100
        ),
        "hourly_dominant_share_pct": float((hourly_abs > hours_abs).mean() * 100),
    }
