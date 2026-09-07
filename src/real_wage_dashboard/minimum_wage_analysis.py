import pandas as pd

from real_wage_dashboard import cpi_analysis

BASE_YEAR = 2015


TARGET_SIZES = {
    "5人以上": "T",
    "30人以上": "0",
}

TARGET_EMPLOYMENT_TYPES = {
    "就業形態計": "0",
    "一般労働者": "1",
    "パートタイム労働者": "2",
}


def prepare_minimum_wage_wage_data(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
    industry_code: str = "TL",
) -> pd.DataFrame:
    """最低賃金分析用の年次時間当たり賃金系列を作成する。"""

    work = df.copy()

    required_columns = {
        "産業分類",
        "規模",
        "就業形態",
        "月",
        "年",
        "所定内給与",
        "所定内労働時間",
    }

    missing = required_columns - set(work.columns)

    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    for column in [
        "産業分類",
        "規模",
        "就業形態",
        "月",
    ]:
        work[column] = work[column].astype(str).str.strip()

    work = work[
        (work["産業分類"] == industry_code)
        & (work["規模"].isin(TARGET_SIZES.values()))
        & (work["就業形態"].isin(TARGET_EMPLOYMENT_TYPES.values()))
        & (work["月"] == "CY")
    ].copy()

    work["year"] = pd.to_numeric(
        work["年"],
        errors="coerce",
    )

    work = work.loc[
        work["year"].between(
            start_year,
            end_year,
        )
    ].copy()

    size_map = {code: name for name, code in TARGET_SIZES.items()}

    employment_map = {code: name for name, code in TARGET_EMPLOYMENT_TYPES.items()}

    work["size_name"] = work["規模"].map(size_map)

    work["employment_name"] = work["就業形態"].map(employment_map)

    work["scheduled_hourly_wage"] = work["所定内給与"] / work["所定内労働時間"]

    result = (
        work[
            [
                "year",
                "size_name",
                "employment_name",
                "所定内給与",
                "所定内労働時間",
                "scheduled_hourly_wage",
            ]
        ]
        .sort_values(
            [
                "size_name",
                "employment_name",
                "year",
            ]
        )
        .reset_index(drop=True)
    )

    return result


def build_minimum_wage_analysis(
    minimum_wage_df: pd.DataFrame,
    wage_df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    """最低賃金と時間当たり賃金を結合し、分析指標を作成する。"""

    _validate_input_columns(
        minimum_wage_df=minimum_wage_df,
        wage_df=wage_df,
    )

    result = wage_df.merge(
        minimum_wage_df[
            [
                "year",
                "minimum_wage",
                "minimum_wage_yoy",
            ]
        ],
        on="year",
        how="inner",
        validate="many_to_one",
    )

    result = result.sort_values(
        [
            "size_name",
            "employment_name",
            "year",
        ]
    ).reset_index(drop=True)

    result["scheduled_hourly_wage_yoy"] = result.groupby(
        [
            "size_name",
            "employment_name",
        ]
    )["scheduled_hourly_wage"].pct_change()

    result["simple_kaitz"] = result["minimum_wage"] / result["scheduled_hourly_wage"]

    result["wage_to_minimum_ratio"] = (
        result["scheduled_hourly_wage"] / result["minimum_wage"]
    )

    result = _add_index_columns(
        result,
        base_year=base_year,
    )

    _validate_analysis_data(
        result,
        base_year=base_year,
    )

    return result.drop(columns=["scheduled_hourly_wage_base"])


def _add_index_columns(
    df: pd.DataFrame,
    base_year: int,
) -> pd.DataFrame:
    """最低賃金と各賃金系列を基準年=100に指数化する。"""

    result = df.copy()

    minimum_wage_base = result.loc[
        result["year"] == base_year,
        "minimum_wage",
    ].drop_duplicates()

    if len(minimum_wage_base) != 1:
        raise ValueError(f"{base_year}年の最低賃金基準値を一意に取得できません。")

    result["minimum_wage_index"] = (
        result["minimum_wage"] / minimum_wage_base.iloc[0] * 100
    )

    base_wages = result.loc[
        result["year"] == base_year,
        [
            "size_name",
            "employment_name",
            "scheduled_hourly_wage",
        ],
    ].rename(columns={"scheduled_hourly_wage": "scheduled_hourly_wage_base"})

    if base_wages.duplicated(
        subset=[
            "size_name",
            "employment_name",
        ]
    ).any():
        raise ValueError(f"{base_year}年の賃金基準値が重複しています。")

    result = result.merge(
        base_wages,
        on=[
            "size_name",
            "employment_name",
        ],
        how="left",
        validate="many_to_one",
    )

    result["wage_index"] = (
        result["scheduled_hourly_wage"] / result["scheduled_hourly_wage_base"] * 100
    )

    return result


def _validate_input_columns(
    minimum_wage_df: pd.DataFrame,
    wage_df: pd.DataFrame,
) -> None:
    """入力DataFrameに必要な列が存在することを確認する。"""

    required_minimum_wage_columns = {
        "year",
        "minimum_wage",
        "minimum_wage_yoy",
    }

    required_wage_columns = {
        "year",
        "size_name",
        "employment_name",
        "scheduled_hourly_wage",
    }

    missing_minimum_wage = required_minimum_wage_columns - set(minimum_wage_df.columns)

    if missing_minimum_wage:
        raise ValueError(
            f"最低賃金データに必要な列がありません: {sorted(missing_minimum_wage)}"
        )

    missing_wage = required_wage_columns - set(wage_df.columns)

    if missing_wage:
        raise ValueError(f"賃金データに必要な列がありません: {sorted(missing_wage)}")


def _validate_analysis_data(
    df: pd.DataFrame,
    base_year: int,
) -> None:
    """分析用DataFrameの完全性を検証する。"""

    if df.empty:
        raise ValueError("最低賃金分析データが空です。")

    duplicate_columns = [
        "year",
        "size_name",
        "employment_name",
    ]

    if df.duplicated(subset=duplicate_columns).any():
        raise ValueError("年・事業所規模・就業形態の組み合わせが重複しています。")

    required_value_columns = [
        "minimum_wage",
        "scheduled_hourly_wage",
        "simple_kaitz",
        "wage_to_minimum_ratio",
        "minimum_wage_index",
        "wage_index",
    ]

    if df[required_value_columns].isna().any().any():
        raise ValueError("最低賃金分析の主要指標に欠損があります。")

    if (df[required_value_columns] <= 0).any().any():
        raise ValueError("最低賃金分析の主要指標に0以下の値があります。")

    base_rows = df[df["year"] == base_year]

    if base_rows.empty:
        raise ValueError(f"{base_year}年の基準データがありません。")

    minimum_index_error = (base_rows["minimum_wage_index"] - 100).abs().max()

    wage_index_error = (base_rows["wage_index"] - 100).abs().max()

    if minimum_index_error > 1e-10:
        raise ValueError("最低賃金指数の基準年が100になっていません。")

    if wage_index_error > 1e-10:
        raise ValueError("賃金指数の基準年が100になっていません。")

    ratio_error = (df["simple_kaitz"] * df["wage_to_minimum_ratio"] - 1).abs().max()

    if ratio_error > 1e-10:
        raise ValueError(
            "簡易Kaitz指数と賃金/最低賃金比の"
            f"逆数関係が成立しません。最大誤差={ratio_error:.12f}"
        )


def add_real_minimum_wage(
    analysis_df: pd.DataFrame,
    annual_cpi_df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    """CPIを結合し、実質最低賃金と指数を計算する。"""

    required_analysis_columns = {
        "year",
        "minimum_wage",
        "minimum_wage_index",
    }

    required_cpi_columns = {
        "year",
        "cpi",
    }

    missing_analysis = required_analysis_columns - set(analysis_df.columns)

    if missing_analysis:
        raise ValueError(
            f"最低賃金分析データに必要な列がありません: {sorted(missing_analysis)}"
        )

    missing_cpi = required_cpi_columns - set(annual_cpi_df.columns)

    if missing_cpi:
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing_cpi)}")

    result = analysis_df.merge(
        annual_cpi_df,
        on="year",
        how="inner",
        validate="many_to_one",
    )

    result["real_minimum_wage"] = result["minimum_wage"] / (result["cpi"] / 100)

    base_real = result.loc[
        result["year"] == base_year,
        [
            "real_minimum_wage",
        ],
    ].drop_duplicates()

    if len(base_real) != 1:
        raise ValueError(f"{base_year}年の実質最低賃金を一意に取得できません。")

    result["real_minimum_wage_index"] = (
        result["real_minimum_wage"] / base_real.iloc[0]["real_minimum_wage"] * 100
    )

    return result


def _spearman_correlation(
    x: pd.Series,
    y: pd.Series,
) -> float:
    """SciPyに依存せずSpearman順位相関を計算する。"""

    return x.rank().corr(
        y.rank(),
        method="pearson",
    )


def summarize_minimum_wage_correlations(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """最低賃金前年比と時間当たり賃金前年比の相関を系列別に集計する。"""

    required_columns = {
        "year",
        "size_name",
        "employment_name",
        "minimum_wage_yoy",
        "scheduled_hourly_wage_yoy",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"相関分析に必要な列がありません: {sorted(missing)}")

    records: list[dict[str, object]] = []

    for (
        size_name,
        employment_name,
    ), group in df.groupby(
        [
            "size_name",
            "employment_name",
        ]
    ):
        work = (
            group[
                [
                    "year",
                    "minimum_wage_yoy",
                    "scheduled_hourly_wage_yoy",
                ]
            ]
            .dropna()
            .sort_values("year")
            .reset_index(drop=True)
        )

        if len(work) < 3:
            raise ValueError(
                "相関分析に必要な観測数が不足しています: "
                f"{size_name} / {employment_name}"
            )

        pearson = work["minimum_wage_yoy"].corr(
            work["scheduled_hourly_wage_yoy"],
            method="pearson",
        )

        spearman = _spearman_correlation(
            work["minimum_wage_yoy"],
            work["scheduled_hourly_wage_yoy"],
        )

        records.append(
            {
                "size_name": size_name,
                "employment_name": employment_name,
                "lag_years": 0,
                "pearson": pearson,
                "spearman": spearman,
                "observation_count": len(work),
            }
        )

    return (
        pd.DataFrame(records)
        .sort_values(
            [
                "size_name",
                "employment_name",
            ]
        )
        .reset_index(drop=True)
    )


def summarize_minimum_wage_lag_correlations(
    df: pd.DataFrame,
    max_lag_years: int = 1,
) -> pd.DataFrame:
    """最低賃金前年比と賃金前年比のラグ相関を系列別に集計する。"""

    required_columns = {
        "year",
        "size_name",
        "employment_name",
        "minimum_wage_yoy",
        "scheduled_hourly_wage_yoy",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"ラグ相関分析に必要な列がありません: {sorted(missing)}")

    records: list[dict[str, object]] = []

    for (
        size_name,
        employment_name,
    ), group in df.groupby(
        [
            "size_name",
            "employment_name",
        ]
    ):
        work = (
            group[
                [
                    "year",
                    "minimum_wage_yoy",
                    "scheduled_hourly_wage_yoy",
                ]
            ]
            .sort_values("year")
            .reset_index(drop=True)
        )

        minimum_wage_data = work[
            [
                "year",
                "minimum_wage_yoy",
            ]
        ].copy()

        for lag_years in range(max_lag_years + 1):
            wage_data = work[
                [
                    "year",
                    "scheduled_hourly_wage_yoy",
                ]
            ].copy()

            # t年の最低賃金を、t + lag年の賃金と対応させる
            wage_data["year"] = wage_data["year"] - lag_years

            pair = minimum_wage_data.merge(
                wage_data,
                on="year",
                how="inner",
                validate="one_to_one",
            ).dropna(
                subset=[
                    "minimum_wage_yoy",
                    "scheduled_hourly_wage_yoy",
                ]
            )

            if len(pair) < 3:
                continue

            pearson = pair["minimum_wage_yoy"].corr(
                pair["scheduled_hourly_wage_yoy"],
                method="pearson",
            )

            spearman = _spearman_correlation(
                pair["minimum_wage_yoy"],
                pair["scheduled_hourly_wage_yoy"],
            )

            records.append(
                {
                    "size_name": size_name,
                    "employment_name": employment_name,
                    "lag_years": lag_years,
                    "pearson": pearson,
                    "spearman": spearman,
                    "observation_count": len(pair),
                }
            )

    return (
        pd.DataFrame(records)
        .sort_values(
            [
                "size_name",
                "employment_name",
                "lag_years",
            ]
        )
        .reset_index(drop=True)
    )


def prepare_annual_cpi(
    cpi_df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> pd.DataFrame:
    """旧importとの互換用。新規コードはcpi_analysisを直接参照する。"""
    return cpi_analysis.prepare_annual_cpi(cpi_df, start_year, end_year)
