import numpy as np
import pandas as pd


def _align_previous_year(
    df: pd.DataFrame,
    columns: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """年月を照合し、各行に対応する前年同月の値を取得する。"""

    required_columns = {"date", *columns}

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.sort_values("date").reset_index(drop=True).copy()

    if result["date"].isna().any():
        raise ValueError("年月に欠損があります。")

    # 年月だけをPeriodIndexに変換
    months = pd.PeriodIndex(result["date"], freq="M")

    if months.has_duplicates:
        raise ValueError("同じ年月のデータが重複しています。")

    # 年月をインデックスにしたdfを作成
    monthly_values = result[columns].copy()
    monthly_values.index = months

    # 各行の前年同月を検索する。存在しない月の値はNaN。
    previous = monthly_values.reindex(months - 12)

    # result / previousで前年比を算出できるよう、行インデックスを合わせる。
    previous.index = result.index

    return result, previous


# ============================================================
# 1. 基礎データ作成
# ============================================================


# 1-1
def merge_wage_and_working_hours(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
) -> pd.DataFrame:
    """賃金の対象月を保持し、同じ年月の労働時間を左結合する。"""

    wage_required = {"date", "nominal_wage_amount"}
    hours_required = {"date", "working_hours"}

    missing = wage_required - set(wage_df.columns)
    if missing:
        raise ValueError(f"賃金データに必要な列がありません: {sorted(missing)}")

    missing = hours_required - set(working_hours_df.columns)
    if missing:
        raise ValueError(f"労働時間データに必要な列がありません: {sorted(missing)}")

    wage = wage_df[["date", "nominal_wage_amount"]].copy()
    hours = working_hours_df[["date", "working_hours"]].copy()

    for label, frame in [
        ("賃金データ", wage),
        ("労働時間データ", hours),
    ]:
        if frame["date"].isna().any():
            raise ValueError(f"{label}の年月に欠損があります。")

        months = pd.PeriodIndex(frame["date"], freq="M")
        if months.has_duplicates:
            raise ValueError(f"{label}に同じ年月の重複があります。")

        # 日付の日部分を月初に統一する。
        frame["date"] = months.to_timestamp()

    result = wage.merge(
        hours,
        on="date",
        how="left",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


# 1-2
def add_approx_hourly_wage(df: pd.DataFrame) -> pd.DataFrame:
    """月額賃金と総実労働時間から概算時間当たり賃金を算出する。"""

    required_columns = {
        "nominal_wage_amount",
        "working_hours",
    }

    # 必要列が揃っているか確認
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


# 1-3
def create_employment_analysis_dataframe(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
) -> pd.DataFrame:
    """賃金・労働時間・概算時間当たり賃金をまとめたDataFrameを作成する。"""

    # 1-1. 賃金と労働時間を年月で結合
    result = merge_wage_and_working_hours(
        wage_df,
        working_hours_df,
    )

    # 1-2. 月額賃金 ÷ 総実労働時間で概算時間当たり賃金を追加
    result = add_approx_hourly_wage(result)

    return result


# ============================================================
# 2. 名目指標の指数化・前年同月比
# ============================================================


# 2-1
def add_base_year_index(
    df: pd.DataFrame,
    column: str,
    output_column: str,
    base_year: int = 2020,
) -> pd.DataFrame:
    """有効な基準年12か月の平均を100として指数化する。"""

    required_columns = {"date", column}

    # 欠損・重複のチェック
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()
    if result["date"].isna().any():
        raise ValueError("年月に欠損があります。")

    months = pd.PeriodIndex(result["date"], freq="M")
    if months.has_duplicates:
        raise ValueError("同じ年月のデータが重複しています。")

    base_df = result.loc[months.year == base_year]
    if len(base_df) != 12:
        raise ValueError(f"{base_year}年の基準データが12か月揃っていません。")

    base_values = base_df[column]
    if base_values.isna().any():
        raise ValueError(f"{base_year}年の基準データに欠損値があります: {column}")

    if (
        not np.isfinite(base_values).all()
        or (base_values <= 0).any()
    ):
        raise ValueError("基準年の値はすべて0より大きい有限値である必要があります。")

    # 基準年以外も無限大は認めない。欠測値は保持する。
    observed_values = result[column].dropna()
    if not np.isfinite(observed_values).all():
        raise ValueError(f"分析対象データに無限大があります: {column}")

    base_value = base_values.mean()
    if not np.isfinite(base_value) or base_value <= 0:
        raise ValueError("基準年平均は0より大きい有限値である必要があります。")

    result[output_column] = result[column] / base_value * 100

    return result


# 2-2
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


# 2-3
def add_employment_changes(df: pd.DataFrame) -> pd.DataFrame:
    """主要指標の前年同月比を、年月を照合して算出する。"""

    output_columns = {
        "nominal_wage_amount": "regular_wage_yoy_pct",
        "working_hours": "working_hours_yoy_pct",
        "approx_hourly_wage": "approx_hourly_wage_yoy_pct",
    }

    result, previous = _align_previous_year(
        df,
        columns=list(output_columns),
    )

    for column, output_column in output_columns.items():
        # 前年値が0の場合、変化率は定義できないためNaNとする。NaNになるのはwhereの仕様。
        denominator = previous[column].where(previous[column] != 0)

        result[output_column] = (result[column] / denominator - 1) * 100

    return result


# ============================================================
# 3. CPI結合・実質値の作成
# ============================================================


# 3-1
def merge_employment_analysis_with_cpi(
    df: pd.DataFrame,
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """分析対象月を保持し、同じ年月のCPIを左結合する。"""

    analysis_required = {
        "date",
        "nominal_wage_amount",
        "working_hours",
        "approx_hourly_wage",
    }
    cpi_required = {"date", "index_value"}

    missing = analysis_required - set(df.columns)
    if missing:
        raise ValueError(f"雇用形態比較データに必要な列がありません: {sorted(missing)}")

    missing = cpi_required - set(cpi_df.columns)
    if missing:
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing)}")

    if "index_value" in df.columns:
        raise ValueError("分析データには既にCPI列があります。")

    analysis = df.copy()
    cpi = cpi_df[["date", "index_value"]].copy()

    # 年月の欠損や重複をチェック
    for label, frame in [
        ("分析データ", analysis),
        ("CPIデータ", cpi),
    ]:
        if frame["date"].isna().any():
            raise ValueError(f"{label}の年月に欠損があります。")

        months = pd.PeriodIndex(frame["date"], freq="M")

        if months.has_duplicates:
            raise ValueError(f"{label}に同じ年月の重複があります。")

        # 日付の日部分を月初に統一する。
        frame["date"] = months.to_timestamp()

    # left結合で、分析対象月を保持しつつCPIを結合する。重複のときはエラー。
    result = analysis.merge(
        cpi,
        on="date",
        how="left",
        validate="one_to_one",
    )

    return result.sort_values("date").reset_index(drop=True)


# 3-2
def add_real_employment_values(df: pd.DataFrame) -> pd.DataFrame:
    """CPIで実質月額賃金と実質時間当たり賃金を算出する。"""

    required_columns = {
        "nominal_wage_amount",
        "approx_hourly_wage",
        "index_value",
    }

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = df.copy()

    # CPIの欠測値は保持するが、0以下や無限大はエラーとする。
    observed_cpi = result["index_value"].dropna()
    if (
        not np.isfinite(observed_cpi).all()
        or (observed_cpi <= 0).any()
    ):
        raise ValueError("CPIには0より大きい有限値が必要です。")

    for column in ["nominal_wage_amount", "approx_hourly_wage"]:
        observed_values = result[column].dropna()

        if not np.isfinite(observed_values).all():
            raise ValueError(f"賃金データに無限大があります: {column}")

    result["real_regular_wage"] = (
        result["nominal_wage_amount"] / result["index_value"] * 100
    )

    result["real_approx_hourly_wage"] = (
        result["approx_hourly_wage"] / result["index_value"] * 100
    )

    return result


# 3-3
def add_real_employment_analysis(
    df: pd.DataFrame,
    cpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態比較データにCPIと実質値を追加する。"""

    # 3-1. 月次分析データとCPIを結合
    result = merge_employment_analysis_with_cpi(
        df,
        cpi_df,
    )

    # 3-2. 名目値をCPIで実質化
    result = add_real_employment_values(result)

    return result


# 3-4
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


# 3-5
def add_real_employment_changes(df: pd.DataFrame) -> pd.DataFrame:
    """実質指標の前年同月比を、年月を照合して算出する。"""

    output_columns = {
        "real_regular_wage": "real_regular_wage_yoy_pct",
        "real_approx_hourly_wage": "real_approx_hourly_wage_yoy_pct",
    }

    # 前年同月比を算出するために、年月を照合して前年同月の値を取得
    result, previous = _align_previous_year(
        df,
        columns=list(output_columns),
    )

    # 前年同月比を算出する。前年値が0の場合、変化率は定義できないためNaNとする。
    for column, output_column in output_columns.items():
        denominator = previous[column].where(previous[column] != 0)

        result[output_column] = (result[column] / denominator - 1) * 100

    return result


# ============================================================
# 4. 月額賃金変化の要因分解
# ============================================================


def add_wage_change_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    """月額賃金の前年同月変化を時間当たり賃金と労働時間に分解する。"""

    output_columns = {
        "nominal_wage_amount": "wage_log_change",
        "approx_hourly_wage": "hourly_wage_log_contribution",
        "working_hours": "working_hours_log_contribution",
    }

    result, previous = _align_previous_year(
        df,
        columns=list(output_columns),
    )

    values = result[list(output_columns)]

    invalid = values.notna() & (
        (values <= 0) | ~np.isfinite(values)
    )

    if invalid.any().any():
        raise ValueError("要因分解には0より大きい有限の賃金・労働時間データが必要です。")

    for column, output_column in output_columns.items():
        result[output_column] = (
            np.log(result[column]) - np.log(previous[column])
        ) * 100

    return result


'''
ここまでの列（総数20列）:
    # 基本指標
    date, nominal_wage_amount, working_hours, approx_hourly_wage,

    # CPI・実質値
    index_value, real_regular_wage, real_approx_hourly_wage,

    # 名目指標の基準年指数
    regular_wage_index, working_hours_index, approx_hourly_wage_index

    # 実質指標の基準年指数
    real_regular_wage_index, real_approx_hourly_wage_index

    # 名目指標の前年同月比（%）
    regular_wage_yoy_pct, working_hours_yoy_pct, approx_hourly_wage_yoy_pct

    # 実質指標の前年同月比（%）
    real_regular_wage_yoy_pct, real_approx_hourly_wage_yoy_pct

    # 月額賃金変化の要因分解（前年同月との自然対数差 × 100）
    wage_log_change, hourly_wage_log_contribution, working_hours_log_contribution

基準年指数は、指定した基準年の平均を100とする（既定：2020年）。
CPI欠測月も保持し、その月の実質値・実質指数は欠損となる。
前年同月比・要因分解は年月を照合し、必要な値が欠測なら欠損となる。
ただし、基準年に必要な値が欠測している場合はエラーとする。
'''

# ============================================================
# 5. 月次分析パイプライン
# ============================================================


def create_full_employment_analysis_dataframe(
    wage_df: pd.DataFrame,
    working_hours_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    base_year: int = 2020,
) -> pd.DataFrame:
    """雇用形態比較に必要な月次指標を作成する。"""

    # 1. 賃金・労働時間・時間当たり賃金を作成する。
    result = create_employment_analysis_dataframe(
        wage_df,
        working_hours_df,
    )

    # 2. 分析対象月を保持してCPIを結合し、実質値を作成する。
    result = add_real_employment_analysis(
        result,
        cpi_df,
    )

    # 3. 名目指標・実質指標を基準年平均=100で指数化する。
    result = add_employment_comparison_indices(
        result,
        base_year=base_year,
    )
    result = add_real_employment_indices(
        result,
        base_year=base_year,
    )

    # 4. 年月を照合して前年同月比を算出する。
    result = add_employment_changes(result)
    result = add_real_employment_changes(result)

    # 5. 名目月額賃金の前年同月変化を対数分解する。
    result = add_wage_change_decomposition(result)

    return result


# ============================================================
# 6. 年平均・期間変化の比較
# ============================================================


# 6-1
def calculate_yearly_averages(
    df: pd.DataFrame,
    year: int,
    columns: list[str],
) -> dict[str, float]:
    """指定年の有効な12か月について、各指標の単純平均を算出する。"""

    required_columns = {"date", *columns}

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    if df["date"].isna().any():
        raise ValueError("年月に欠損があります。")

    months = pd.PeriodIndex(df["date"], freq="M")
    year_mask = months.year == year

    # 指定年のデータを抽出し、12か月揃っているか確認
    year_df = df.loc[year_mask]
    year_months = months[year_mask]
    if len(year_df) != 12 or year_months.nunique() != 12:
        raise ValueError(f"{year}年のデータが12か月揃っていません。")

    # 指定列の欠損・無限大をチェック
    values = year_df[columns]
    if values.isna().any().any():
        raise ValueError(f"{year}年の分析対象データに欠損値があります。")
    if not np.isfinite(values).all().all():
        raise ValueError(f"{year}年の分析対象データに無限大があります。")

    averages = values.mean()
    if not np.isfinite(averages).all():
        raise ValueError(f"{year}年の年平均を有限値として算出できません。")

    return {
        column: float(averages[column])
        for column in columns
    }

'''
{
    'nominal_wage_amount': 123456.78,
    'working_hours': 160.0,
    'approx_hourly_wage': 771.6,
    ...
}
'''


# 6-2
def calculate_change_rate(start_value: float, end_value: float) -> float:
    """開始値から終了値までの変化率（%）を算出する。"""

    if pd.isna(start_value) or pd.isna(end_value):
        raise ValueError("開始値・終了値に欠損があります。")

    if not np.isfinite(start_value) or not np.isfinite(end_value):
        raise ValueError("開始値・終了値は有限値である必要があります。")

    if start_value <= 0:
        raise ValueError("開始値は0より大きい必要があります。")

    change_rate = (end_value / start_value - 1) * 100

    if not np.isfinite(change_rate):
        raise ValueError("変化率を有限値として算出できません。")

    return float(change_rate)

# 6-3
def calculate_yearly_change_rates(
    start_averages: dict[str, float],
    end_averages: dict[str, float],
) -> dict[str, float]:
    """2時点の年平均から各指標の変化率を算出する。"""

    if set(start_averages) != set(end_averages):
        raise ValueError("比較する年平均の指標が一致していません。")

    return {
        # for文でkeyを取り出し、calculate_change_rate()に数値を渡す
        column: calculate_change_rate(
            start_averages[column],
            end_averages[column],
        )
        for column in start_averages
    }


'''
ANALYSIS_INDICATORS = [
    ["nominal_wage_amount", "working_hours", "approx_hourly_wage"],
    ["real_regular_wage", "real_approx_hourly_wage"]
]
'''


# 6-4
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
        # 指定年の年平均を算出
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

        # 指定年の年平均から変化率を算出
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


# ============================================================
# 7. 雇用形態間の比較・考察
# ============================================================


# 7-1
def compare_employment_change_rates(summary_df: pd.DataFrame) -> pd.DataFrame:
    """一般・パートの変化率を比較し、欠測時は判定不可とする。"""

    required_columns = {
        "employment_type",
        "indicator",
        "change_rate_pct",
    }

    missing = required_columns - set(summary_df.columns)
    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    key_columns = ["indicator", "employment_type"]
    if summary_df[key_columns].isna().any().any():
        raise ValueError("指標名または就業形態に欠損があります。")

    if summary_df.duplicated(subset=key_columns).any():
        raise ValueError("同じ指標・就業形態の比較結果が重複しています。")

    observed_rates = summary_df["change_rate_pct"].dropna()

    if not np.isfinite(observed_rates).all():
        raise ValueError("変化率に無限大があります。")

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

    result["difference_pct_point"] = (
        result["パートタイム労働者"] - result["一般労働者"]
    )

    comparable = result[
        ["一般労働者", "パートタイム労働者"]
    ].notna().all(axis=1)

    difference = result["difference_pct_point"]

    result["larger_change"] = "判定不可"

    result.loc[
        comparable & (difference > 0),
        "larger_change",
    ] = "パートタイム労働者"

    result.loc[
        comparable & (difference < 0),
        "larger_change",
    ] = "一般労働者"

    result.loc[
        comparable & (difference == 0),
        "larger_change",
    ] = "同程度"

    return result[
        [
            "indicator",
            "一般労働者",
            "パートタイム労働者",
            "difference_pct_point",
            "larger_change",
        ]
    ]


# 7-2
def describe_change_direction(value: float, tolerance: float = 0.1) -> str:
    """変化率を上昇・低下・横ばいに分類し、欠測時は判定不可とする。"""

    if (
        pd.isna(tolerance)
        or not np.isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError("許容幅は0以上の有限値である必要があります。")

    if pd.isna(value):
        return "判定不可"

    if not np.isfinite(value):
        raise ValueError("変化率は有限値である必要があります。")

    if value > tolerance:
        return "上昇"

    if value < -tolerance:
        return "低下"

    return "横ばい"


# 7-3
def create_employment_analysis_discussion(
    summary_df: pd.DataFrame,
    tolerance: float = 0.1,
) -> list[str]:
    """一般・パートの比較結果から、観測事実に基づく考察を生成する。"""

    required_columns = {
        "employment_type",
        "indicator",
        "change_rate_pct",
    }

    missing = required_columns - set(summary_df.columns)
    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    if (
        pd.isna(tolerance)
        or not np.isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError("許容幅は0以上の有限値である必要があります。")

    def get_rate(
        employment_type: str,
        indicator: str,
    ) -> float:
        matched = summary_df.loc[
            (summary_df["employment_type"] == employment_type)
            & (summary_df["indicator"] == indicator),
            "change_rate_pct",
        ]

        if len(matched) != 1:
            raise ValueError(
                f"比較結果を一意に取得できません: {employment_type}, {indicator}"
            )

        value = matched.iloc[0]

        if pd.isna(value):
            return float("nan")

        if not np.isfinite(value):
            raise ValueError(
                f"変化率は有限値である必要があります: {employment_type}, {indicator}"
            )

        return float(value)

    indicators = {
        "wage": "nominal_wage_amount",
        "hours": "working_hours",
        "hourly": "approx_hourly_wage",
        "real_wage": "real_regular_wage",
    }

    rates = {
        employment_type: {
            key: get_rate(employment_type, indicator)
            for key, indicator in indicators.items()
        }
        for employment_type in [
            "一般労働者",
            "パートタイム労働者",
        ]
    }

    discussions = []

    # 1. 各就業形態で、時間当たり賃金と労働時間の方向を確認する。
    for employment_type, values in rates.items():
        hourly = values["hourly"]
        hours = values["hours"]
        wage = values["wage"]

        if (
            pd.notna(hourly)
            and pd.notna(hours)
            and hourly > tolerance
            and hours < -tolerance
        ):
            discussions.append(
                f"{employment_type}では、時間当たり賃金が上昇する一方、"
                "総実労働時間は減少しています。"
            )

        # 月額賃金との大小関係を直接確認する。
        if (
            pd.notna(hourly)
            and pd.notna(wage)
            and hourly > tolerance
            and wage < hourly - tolerance
        ):
            discussions.append(
                f"{employment_type}の月額賃金の変化率は、"
                "時間当たり賃金の変化率を下回っています。"
            )

    # 2. 一般・パートの時間当たり賃金の変化率を比較する。
    general = rates["一般労働者"]
    part = rates["パートタイム労働者"]

    if pd.notna(general["hourly"]) and pd.notna(part["hourly"]):
        difference = part["hourly"] - general["hourly"]

        if difference > tolerance:
            discussions.append(
                "パートタイム労働者の時間当たり賃金の変化率は、"
                "一般労働者を上回っています。"
            )
        elif difference < -tolerance:
            discussions.append(
                "一般労働者の時間当たり賃金の変化率は、"
                "パートタイム労働者を上回っています。"
            )

    # 3. 両者とも労働時間が減っている場合だけ、減少幅を比較する。
    if (
        pd.notna(general["hours"])
        and pd.notna(part["hours"])
        and general["hours"] < -tolerance
        and part["hours"] < -tolerance
    ):
        difference = part["hours"] - general["hours"]

        if difference < -tolerance:
            discussions.append(
                "総実労働時間の減少率は、"
                "パートタイム労働者の方が大きくなっています。"
            )
        elif difference > tolerance:
            discussions.append(
                "総実労働時間の減少率は、"
                "一般労働者の方が大きくなっています。"
            )

    # 4. 各就業形態の名目・実質月額賃金を比較する。
    for employment_type, values in rates.items():
        wage = values["wage"]
        real_wage = values["real_wage"]

        if pd.notna(wage) and pd.notna(real_wage):
            if real_wage < wage - tolerance:
                discussions.append(
                    f"{employment_type}では、物価調整後の実質月額賃金の"
                    "変化率が、名目月額賃金の変化率を下回っています。"
                )

        if pd.notna(real_wage):
            direction = describe_change_direction(
                real_wage,
                tolerance=tolerance,
            )
            discussions.append(
                f"{employment_type}の実質月額賃金は、"
                f"比較開始年に対して{direction}です。"
            )

    # 5. 欠測による考察の省略を明示する。
    has_missing = any(
        pd.isna(value)
        for values in rates.values()
        for value in values.values()
    )

    if has_missing:
        discussions.append(
            "一部の指標が欠測しているため、"
            "該当する指標についての考察は省略しています。"
        )

    discussions.append(
        "これらは集団平均の変化であり、"
        "同一労働者の賃上げや労働時間の変化、"
        "それらの原因を直接示すものではありません。"
    )

    return discussions


# ============================================================
# 8. 要因分解の期間要約
# ============================================================


# 8-1
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
