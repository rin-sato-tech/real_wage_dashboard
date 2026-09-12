from pathlib import Path
from typing import Any

import pandas as pd

from real_wage_dashboard.config import (
    LFS_WORKING_HOURS_AGE_CODES,
    LFS_WORKING_HOURS_CATEGORY_CODES,
    LFS_WORKING_HOURS_DISTRIBUTION_BASE_FILTERS,
    LFS_WORKING_HOURS_DISTRIBUTION_STATS_DATA_ID,
)
from real_wage_dashboard.estat_client import get_stats_data
from real_wage_dashboard.estat_response import (
    ensure_list,
)

EMPLOYMENT_AGE_COLUMNS = (
    ("15～24歳", 4, 15),
    ("25～34歳", 5, 16),
    ("35～44歳", 6, 17),
    ("45～54歳", 7, 18),
    ("55～64歳", 8, 19),
    ("65歳以上", 9, 20),
)

AGE_GROUPS = [age_group for age_group, _, _ in EMPLOYMENT_AGE_COLUMNS]

LFS_HOURS_METRICS = {
    "平均週間就業時間【時間】": "average_weekly_hours",
    "延週間就業時間【万時間】": "aggregate_weekly_hours",
}

LFS_HOURS_RECONSTRUCTION_COMPONENTS = {
    "hours_1_34": (
        "hours_1_14",
        "hours_15_29",
        "hours_30_34",
    ),
    "hours_35_48": (
        "hours_35_39",
        "hours_40_48",
    ),
    "hours_49_plus": (
        "hours_49_59",
        "hours_60_plus",
    ),
}

LFS_DETAILED_HOURS_COLUMNS = (
    "hours_1_14",
    "hours_15_29",
    "hours_30_34",
    "hours_35_39",
    "hours_40_48",
    "hours_49_59",
    "hours_60_plus",
)

LFS_DISTRIBUTION_METRIC_COLUMNS = (
    "persons_at_work",
    *LFS_HOURS_RECONSTRUCTION_COMPONENTS,
    *LFS_DETAILED_HOURS_COLUMNS,
)


def _reshape_lfs_employment_by_age(
    raw: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """労働力調査の年齢別就業者数・就業率を分析用DataFrameへ整形する。"""

    years = pd.to_numeric(
        raw.iloc[:, 1],
        errors="coerce",
    )

    data = raw.loc[years.between(start_year, end_year)].copy()

    data["year"] = pd.to_numeric(
        data.iloc[:, 1],
        errors="coerce",
    ).astype(int)

    records: list[dict[str, int | float | str]] = []

    for _, row in data.iterrows():
        year = int(row["year"])

        for age_group, count_col, rate_col in EMPLOYMENT_AGE_COLUMNS:
            records.append(
                {
                    "year": year,
                    "age_group": age_group,
                    "employed_persons": pd.to_numeric(
                        row.iloc[count_col],
                        errors="coerce",
                    ),
                    "employment_rate": pd.to_numeric(
                        row.iloc[rate_col],
                        errors="coerce",
                    ),
                }
            )

    result = pd.DataFrame(records)

    result["employed_persons"] = pd.to_numeric(
        result["employed_persons"],
        errors="coerce",
    )

    result["employment_rate"] = pd.to_numeric(
        result["employment_rate"],
        errors="coerce",
    )

    return result


def load_lfs_employment_by_age(
    file_path: str | Path,
    start_year: int = 2000,
    end_year: int = 2025,
) -> pd.DataFrame:
    """年齢別就業者数・就業率を分析用DataFrameとして読み込む。"""

    raw = pd.read_excel(
        file_path,
        sheet_name="総数",
        header=None,
    )

    result = _reshape_lfs_employment_by_age(
        raw,
        start_year=start_year,
        end_year=end_year,
    )

    return result.sort_values(["year", "age_group"]).reset_index(drop=True)


def _reshape_lfs_hours_by_age(raw: pd.DataFrame) -> pd.DataFrame:
    """労働力調査の年齢別就業時間データを分析用のwide形式に整形する。"""

    data = raw.copy()

    data["year"] = data["時間軸（年次）"].astype(str).str.extract(r"(\d{4})")[0]

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    data = data.loc[data["表章項目"].isin(LFS_HOURS_METRICS)].copy()

    long = data.melt(
        id_vars=["year", "表章項目"],
        value_vars=AGE_GROUPS,
        var_name="age_group",
        value_name="value",
    )

    long["value"] = pd.to_numeric(
        long["value"],
        errors="coerce",
    )

    long["metric"] = long["表章項目"].replace(LFS_HOURS_METRICS)

    result = (
        long[
            [
                "year",
                "age_group",
                "metric",
                "value",
            ]
        ]
        .pivot(
            index=["year", "age_group"],
            columns="metric",
            values="value",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    result["year"] = result["year"].astype(int)

    return result


def _add_lfs_hours_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """年齢別就業時間データに従業者数推計と構成比を追加する。"""

    result = df.copy()

    result["implied_persons_at_work"] = (
        result["aggregate_weekly_hours"] / result["average_weekly_hours"]
    )

    yearly_total = result.groupby("year")["implied_persons_at_work"].transform(
        lambda x: x.sum(min_count=1)
    )

    result["worker_share"] = result["implied_persons_at_work"] / yearly_total

    return result


def load_lfs_hours_by_age(file_path: str | Path) -> pd.DataFrame:
    """年齢別の平均・延週間就業時間を分析用DataFrameとして読み込む。"""

    raw = pd.read_csv(
        file_path,
        encoding="utf-8-sig",
        skiprows=13,
    )

    result = _reshape_lfs_hours_by_age(raw)
    result = _add_lfs_hours_derived_metrics(result)

    return result.sort_values(["year", "age_group"]).reset_index(drop=True)


def create_lfs_age_dataframe(
    employment_path: str | Path,
    hours_path: str | Path,
) -> pd.DataFrame:
    """年齢別就業構造と就業時間を結合する。"""

    employment = load_lfs_employment_by_age(employment_path)

    hours = load_lfs_hours_by_age(hours_path)

    return employment.merge(
        hours,
        on=["year", "age_group"],
        how="left",
        validate="one_to_one",
    )


def create_lfs_working_hours_time_codes(
    start_year: int = 2000,
    end_year: int = 2025,
) -> list[str]:
    """労働力調査・年次表の時間コードを作成する。"""

    if start_year > end_year:
        raise ValueError("開始年は終了年以下である必要があります。")

    return [f"{year}000000" for year in range(start_year, end_year + 1)]


def _create_lfs_distribution_long_dataframe(response: dict[str, Any]) -> pd.DataFrame:
    """e-Statレスポンスを年・年齢階級・就業時間区分のlong形式へ変換する。"""

    try:
        values = response["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
    except (KeyError, TypeError):
        raise ValueError("e-StatレスポンスからVALUEを取得できません。") from None

    age_mapping = {code: name for name, code in LFS_WORKING_HOURS_AGE_CODES.items()}

    hours_mapping = {
        code: name for name, code in LFS_WORKING_HOURS_CATEGORY_CODES.items()
    }

    rows: list[dict[str, int | float | str]] = []

    for item in ensure_list(values):
        age_code = item.get("@cat02")
        hours_code = item.get("@cat04")
        time_code = item.get("@time")

        age_group = age_mapping.get(age_code)
        metric = hours_mapping.get(hours_code)

        if age_group is None or metric is None or time_code is None:
            continue

        time_code = str(time_code)

        if len(time_code) < 4 or not time_code[:4].isdigit():
            raise ValueError(f"不正な時間コードです: {time_code}")

        rows.append(
            {
                "year": int(time_code[:4]),
                "age_group": age_group,
                "metric": metric,
                "value": item.get("$"),
            }
        )

    result = pd.DataFrame(
        rows,
        columns=[
            "year",
            "age_group",
            "metric",
            "value",
        ],
    )

    if result.empty:
        return result

    result["value"] = pd.to_numeric(
        result["value"],
        errors="coerce",
    )

    return result


def _pivot_lfs_distribution(long_df: pd.DataFrame) -> pd.DataFrame:
    """long形式の就業時間分布を年・年齢階級単位のwide形式へ変換する。"""

    duplicate = long_df.duplicated(
        subset=[
            "year",
            "age_group",
            "metric",
        ]
    )

    if duplicate.any():
        raise ValueError("同じ年・年齢階級・就業時間区分のデータが重複しています。")

    result = (
        long_df.pivot(
            index=["year", "age_group"],
            columns="metric",
            values="value",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    for column in LFS_DISTRIBUTION_METRIC_COLUMNS:
        if column not in result.columns:
            result[column] = float("nan")

    return result


def _add_reconstructed_hours_bands(df: pd.DataFrame) -> pd.DataFrame:
    """詳細就業時間区分から長期比較用3区分を再構成する。"""

    result = df.copy()

    for band, components in LFS_HOURS_RECONSTRUCTION_COMPONENTS.items():
        result[f"{band}_reconstructed"] = result[list(components)].sum(
            axis=1,
            min_count=len(components),
        )

    return result


def _add_harmonized_hours_bands(df: pd.DataFrame) -> pd.DataFrame:
    """公式上位区分を優先し、欠測時のみ再構成値で補完する。"""

    result = df.copy()

    for band in LFS_HOURS_RECONSTRUCTION_COMPONENTS:
        result[f"{band}_harmonized"] = result[band].combine_first(
            result[f"{band}_reconstructed"]
        )

    return result


def _validate_persons_at_work(
    df: pd.DataFrame,
) -> None:
    """構成比計算の分母となる従業者総数を検証する。"""

    if df["persons_at_work"].isna().any():
        raise ValueError("従業者総数に欠損があります。")

    if df["persons_at_work"].le(0).any():
        raise ValueError("従業者総数は0より大きい必要があります。")


def _add_harmonized_distribution_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """調和済み3区分についてカバレッジと構成比を追加する。"""

    result = df.copy()

    _validate_persons_at_work(result)

    harmonized_columns = [
        f"{band}_harmonized" for band in LFS_HOURS_RECONSTRUCTION_COMPONENTS
    ]

    result["classified_workers"] = result[harmonized_columns].sum(
        axis=1,
        min_count=len(harmonized_columns),
    )

    result["unclassified_workers"] = (
        result["persons_at_work"] - result["classified_workers"]
    )

    result["coverage"] = result["classified_workers"] / result["persons_at_work"]

    result["unclassified_share"] = (
        result["unclassified_workers"] / result["persons_at_work"]
    )

    for column in harmonized_columns:
        result[f"{column}_share"] = result[column] / result["persons_at_work"]

    return result


def _add_detailed_distribution_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """詳細7区分についてカバレッジと構成比を追加する。"""

    result = df.copy()

    _validate_persons_at_work(result)

    result["detailed_classified_workers"] = result[
        list(LFS_DETAILED_HOURS_COLUMNS)
    ].sum(
        axis=1,
        min_count=len(LFS_DETAILED_HOURS_COLUMNS),
    )

    result["detailed_coverage"] = (
        result["detailed_classified_workers"] / result["persons_at_work"]
    )

    for column in LFS_DETAILED_HOURS_COLUMNS:
        result[f"{column}_share"] = result[column] / result["persons_at_work"]

    return result


def create_lfs_working_hours_distribution_dataframe(
    response: dict[str, Any],
) -> pd.DataFrame:
    """e-Stat表3-3レスポンスを年齢別就業時間分布に変換する。"""

    long_df = _create_lfs_distribution_long_dataframe(response)

    if long_df.empty:
        return pd.DataFrame()

    long_df["value"] = pd.to_numeric(
        long_df["value"],
        errors="coerce",
    )

    result = _pivot_lfs_distribution(long_df)

    result = _add_reconstructed_hours_bands(result)
    result = _add_harmonized_hours_bands(result)
    result = _add_harmonized_distribution_metrics(result)
    result = _add_detailed_distribution_metrics(result)

    return result.sort_values(["year", "age_group"]).reset_index(drop=True)


def load_lfs_working_hours_distribution_from_api(
    app_id: str,
    start_year: int = 2000,
    end_year: int = 2025,
) -> pd.DataFrame:
    """e-Stat APIから表3-3の就業時間分布を取得する。"""

    age_codes = ",".join(LFS_WORKING_HOURS_AGE_CODES.values())

    hours_codes = ",".join(LFS_WORKING_HOURS_CATEGORY_CODES.values())

    time_codes = ",".join(
        create_lfs_working_hours_time_codes(
            start_year=start_year,
            end_year=end_year,
        )
    )

    filters = {
        **LFS_WORKING_HOURS_DISTRIBUTION_BASE_FILTERS,
        "cdCat02": age_codes,
        "cdCat04": hours_codes,
        "cdTime": time_codes,
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=(LFS_WORKING_HOURS_DISTRIBUTION_STATS_DATA_ID),
        filters=filters,
    )

    return create_lfs_working_hours_distribution_dataframe(response)
