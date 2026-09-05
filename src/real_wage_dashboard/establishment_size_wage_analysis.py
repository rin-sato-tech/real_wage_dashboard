import numpy as np
import pandas as pd

TARGET_SIZES = {
    "5人以上": "T",
    "30人以上": "0",
}

TARGET_EMPLOYMENT_TYPES = {
    "就業形態計": "0",
    "一般労働者": "1",
    "パートタイム労働者": "2",
}


def prepare_establishment_size_annual_data(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
    industry_code: str = "TL",
) -> pd.DataFrame:
    """毎月勤労統計CSVから事業所規模別のCY年平均データを作成する。"""
    work = df.copy()

    required_columns = {
        "産業分類",
        "規模",
        "就業形態",
        "月",
        "年",
        "現金給与総額",
        "総実労働時間",
    }

    missing = required_columns - set(work.columns)

    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    for column in ["産業分類", "規模", "就業形態", "月"]:
        work[column] = work[column].astype(str).str.strip()

    work = work[
        (work["産業分類"] == industry_code)
        & (work["規模"].isin(TARGET_SIZES.values()))
        & (work["就業形態"].isin(TARGET_EMPLOYMENT_TYPES.values()))
        & (work["月"] == "CY")
    ].copy()

    work["year"] = pd.to_numeric(work["年"], errors="coerce")

    work = work.loc[work["year"].between(start_year, end_year)].copy()

    size_map = {code: name for name, code in TARGET_SIZES.items()}
    employment_map = {code: name for name, code in TARGET_EMPLOYMENT_TYPES.items()}

    work["size_name"] = work["規模"].map(size_map)
    work["employment_name"] = work["就業形態"].map(employment_map)

    work["hourly_wage"] = work["現金給与総額"] / work["総実労働時間"]

    result = (
        work[
            [
                "year",
                "size_name",
                "employment_name",
                "現金給与総額",
                "総実労働時間",
                "hourly_wage",
            ]
        ]
        .sort_values(["employment_name", "year", "size_name"])
        .reset_index(drop=True)
    )

    return result


def build_establishment_size_comparison(
    annual_df: pd.DataFrame,
) -> pd.DataFrame:
    """5人以上と30人以上を年・就業形態ごとに比較する。"""
    rows = []

    for employment_name in TARGET_EMPLOYMENT_TYPES:
        subset = annual_df[annual_df["employment_name"] == employment_name].copy()

        pivot = subset.pivot(
            index="year",
            columns="size_name",
            values=[
                "現金給与総額",
                "総実労働時間",
                "hourly_wage",
            ],
        )

        required_columns = [
            ("現金給与総額", "5人以上"),
            ("現金給与総額", "30人以上"),
            ("総実労働時間", "5人以上"),
            ("総実労働時間", "30人以上"),
            ("hourly_wage", "5人以上"),
            ("hourly_wage", "30人以上"),
        ]

        missing = [column for column in required_columns if column not in pivot.columns]

        if missing:
            raise ValueError(
                f"{employment_name}: 比較に必要な系列が不足しています: {missing}"
            )

        for year in pivot.index:
            wage_5 = pivot.loc[year, ("現金給与総額", "5人以上")]
            wage_30 = pivot.loc[year, ("現金給与総額", "30人以上")]

            hours_5 = pivot.loc[year, ("総実労働時間", "5人以上")]
            hours_30 = pivot.loc[year, ("総実労働時間", "30人以上")]

            hourly_5 = pivot.loc[year, ("hourly_wage", "5人以上")]
            hourly_30 = pivot.loc[year, ("hourly_wage", "30人以上")]

            rows.append(
                {
                    "year": int(year),
                    "employment_name": employment_name,
                    "wage_5plus": wage_5,
                    "wage_30plus": wage_30,
                    "wage_difference": wage_30 - wage_5,
                    "wage_ratio_30_to_5": wage_30 / wage_5,
                    "hours_5plus": hours_5,
                    "hours_30plus": hours_30,
                    "hours_difference": hours_30 - hours_5,
                    "hours_ratio_30_to_5": hours_30 / hours_5,
                    "hourly_wage_5plus": hourly_5,
                    "hourly_wage_30plus": hourly_30,
                    "hourly_difference": hourly_30 - hourly_5,
                    "hourly_ratio_30_to_5": hourly_30 / hourly_5,
                }
            )

    return (
        pd.DataFrame(rows)
        .sort_values(["employment_name", "year"])
        .reset_index(drop=True)
    )


def summarize_establishment_size_change(
    comparison_df: pd.DataFrame,
    employment_name: str,
    start_year: int,
    end_year: int,
) -> pd.Series:
    """指定期間の賃金・時間・時給比率変化と対数分解を要約する。"""
    subset = comparison_df[comparison_df["employment_name"] == employment_name].copy()

    start = subset.loc[subset["year"] == start_year]
    end = subset.loc[subset["year"] == end_year]

    if len(start) != 1 or len(end) != 1:
        raise ValueError(
            f"{employment_name}: 開始年または終了年を一意に取得できません。"
        )

    start = start.iloc[0]
    end = end.iloc[0]

    def pct_change(start_value: float, end_value: float) -> float:
        return (end_value / start_value - 1) * 100

    wage_ratio_log_change = (
        np.log(end["wage_ratio_30_to_5"]) - np.log(start["wage_ratio_30_to_5"])
    ) * 100

    hourly_ratio_log_contribution = (
        np.log(end["hourly_ratio_30_to_5"]) - np.log(start["hourly_ratio_30_to_5"])
    ) * 100

    hours_ratio_log_contribution = (
        np.log(end["hours_ratio_30_to_5"]) - np.log(start["hours_ratio_30_to_5"])
    ) * 100

    decomposition_error = (
        hourly_ratio_log_contribution
        + hours_ratio_log_contribution
        - wage_ratio_log_change
    )

    return pd.Series(
        {
            "employment_name": employment_name,
            "start_year": start_year,
            "end_year": end_year,
            "wage_5plus_change_pct": pct_change(start["wage_5plus"], end["wage_5plus"]),
            "wage_30plus_change_pct": pct_change(
                start["wage_30plus"], end["wage_30plus"]
            ),
            "wage_ratio_start": start["wage_ratio_30_to_5"],
            "wage_ratio_end": end["wage_ratio_30_to_5"],
            "wage_ratio_change_pct": pct_change(
                start["wage_ratio_30_to_5"],
                end["wage_ratio_30_to_5"],
            ),
            "hours_5plus_change_pct": pct_change(
                start["hours_5plus"], end["hours_5plus"]
            ),
            "hours_30plus_change_pct": pct_change(
                start["hours_30plus"], end["hours_30plus"]
            ),
            "hours_ratio_start": start["hours_ratio_30_to_5"],
            "hours_ratio_end": end["hours_ratio_30_to_5"],
            "hours_ratio_change_pct": pct_change(
                start["hours_ratio_30_to_5"],
                end["hours_ratio_30_to_5"],
            ),
            "hourly_5plus_change_pct": pct_change(
                start["hourly_wage_5plus"],
                end["hourly_wage_5plus"],
            ),
            "hourly_30plus_change_pct": pct_change(
                start["hourly_wage_30plus"],
                end["hourly_wage_30plus"],
            ),
            "hourly_ratio_start": start["hourly_ratio_30_to_5"],
            "hourly_ratio_end": end["hourly_ratio_30_to_5"],
            "hourly_ratio_change_pct": pct_change(
                start["hourly_ratio_30_to_5"],
                end["hourly_ratio_30_to_5"],
            ),
            "wage_ratio_log_change": wage_ratio_log_change,
            "hourly_ratio_log_contribution": hourly_ratio_log_contribution,
            "hours_ratio_log_contribution": hours_ratio_log_contribution,
            "decomposition_error": decomposition_error,
        }
    )


def validate_establishment_size_results(
    annual_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> None:
    """分析用データの完全性と恒等関係を検証する。"""
    expected_rows = (
        len(TARGET_SIZES) * len(TARGET_EMPLOYMENT_TYPES) * (end_year - start_year + 1)
    )

    if len(annual_df) != expected_rows:
        raise AssertionError(
            f"年次データ件数が想定と異なります: {len(annual_df)} != {expected_rows}"
        )

    value_columns = [
        "現金給与総額",
        "総実労働時間",
        "hourly_wage",
    ]

    if annual_df[value_columns].isna().any().any():
        raise AssertionError("年次データに欠損があります。")

    if (annual_df[value_columns] <= 0).any().any():
        raise AssertionError("0以下の値があります。")

    ratio_columns = [
        "wage_ratio_30_to_5",
        "hours_ratio_30_to_5",
        "hourly_ratio_30_to_5",
    ]

    if comparison_df[ratio_columns].isna().any().any():
        raise AssertionError("比率に欠損があります。")

    identity_error = (
        (
            comparison_df["hourly_ratio_30_to_5"] * comparison_df["hours_ratio_30_to_5"]
            - comparison_df["wage_ratio_30_to_5"]
        )
        .abs()
        .max()
    )

    if identity_error > 1e-10:
        raise AssertionError(
            "月額賃金比率 = 時給比率 × 労働時間比率 "
            f"が成立しません。最大誤差={identity_error:.12f}"
        )
