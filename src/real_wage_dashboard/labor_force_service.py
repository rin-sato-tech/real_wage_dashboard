from typing import Any
from pathlib import Path

import pandas as pd

from real_wage_dashboard.config import (
    LFS_WORKING_HOURS_AGE_CODES,
    LFS_WORKING_HOURS_CATEGORY_CODES,
    LFS_WORKING_HOURS_DISTRIBUTION_BASE_FILTERS,
    LFS_WORKING_HOURS_DISTRIBUTION_STATS_DATA_ID,
)
from real_wage_dashboard.estat_client import (
    get_meta_info,
    get_stats_data,
)
from real_wage_dashboard.estat_response import (
    ensure_list,
)

AGE_GROUPS = [
    "15～24歳",
    "25～34歳",
    "35～44歳",
    "45～54歳",
    "55～64歳",
    "65歳以上",
]

EMPLOYMENT_COUNT_COLUMNS = {
    4: "15～24歳",
    5: "25～34歳",
    6: "35～44歳",
    7: "45～54歳",
    8: "55～64歳",
    9: "65歳以上",
}

EMPLOYMENT_RATE_COLUMNS = {
    15: "15～24歳",
    16: "25～34歳",
    17: "35～44歳",
    18: "45～54歳",
    19: "55～64歳",
    20: "65歳以上",
}

HOURS_AGE_COLUMNS = {
    "15～24歳": "15～24歳",
    "25～34歳": "25～34歳",
    "35～44歳": "35～44歳",
    "45～54歳": "45～54歳",
    "55～64歳": "55～64歳",
    "65歳以上": "65歳以上",
}


def load_lfs_employment_by_age(
    file_path: str | Path,
    start_year: int = 2000,
    end_year: int = 2025,
) -> pd.DataFrame:
    """労働力調査の年齢別就業者数・就業率をlong形式で読み込む。"""

    raw = pd.read_excel(
        file_path,
        sheet_name="総数",
        header=None,
    )

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

        for count_col, age_group in EMPLOYMENT_COUNT_COLUMNS.items():
            rate_col = next(
                column
                for column, group in EMPLOYMENT_RATE_COLUMNS.items()
                if group == age_group
            )

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

    return result.sort_values(["year", "age_group"]).reset_index(drop=True)


def load_lfs_hours_by_age(
    file_path: str | Path,
) -> pd.DataFrame:
    """年齢別の平均週間就業時間・延週間就業時間をlong形式で読み込む。"""

    raw = pd.read_csv(
        file_path,
        encoding="utf-8-sig",
        skiprows=13,
    )

    raw["year"] = raw["時間軸（年次）"].astype(str).str.extract(r"(\d{4})")[0]

    raw["year"] = pd.to_numeric(
        raw["year"],
        errors="coerce",
    )

    data = raw.loc[
        raw["表章項目"].isin(
            [
                "平均週間就業時間【時間】",
                "延週間就業時間【万時間】",
            ]
        )
    ].copy()

    long = data.melt(
        id_vars=[
            "year",
            "表章項目",
        ],
        value_vars=list(HOURS_AGE_COLUMNS),
        var_name="age_group",
        value_name="value",
    )

    long["value"] = pd.to_numeric(
        long["value"],
        errors="coerce",
    )

    long["metric"] = long["表章項目"].replace(
        {
            "平均週間就業時間【時間】": "average_weekly_hours",
            "延週間就業時間【万時間】": "aggregate_weekly_hours",
        }
    )

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
            index=[
                "year",
                "age_group",
            ],
            columns="metric",
            values="value",
        )
        .reset_index()
    )

    result.columns.name = None

    result["year"] = result["year"].astype(int)

    result["implied_persons_at_work"] = (
        result["aggregate_weekly_hours"] / result["average_weekly_hours"]
    )

    yearly_total = result.groupby("year")["implied_persons_at_work"].transform(
        lambda x: x.sum(min_count=1)
    )

    result["worker_share"] = result["implied_persons_at_work"] / yearly_total

    return result.sort_values(["year", "age_group"]).reset_index(drop=True)


def create_lfs_age_dataframe(
    employment_path: str | Path,
    hours_path: str | Path,
) -> pd.DataFrame:
    """年齢別就業構造と就業時間を結合する。"""

    employment = load_lfs_employment_by_age(
        employment_path,
    )

    hours = load_lfs_hours_by_age(
        hours_path,
    )

    return employment.merge(
        hours,
        on=[
            "year",
            "age_group",
        ],
        how="left",
        validate="one_to_one",
    )


def create_lfs_working_hours_time_codes(
    start_year: int = 2000,
    end_year: int = 2025,
) -> list[str]:
    """労働力調査・年次表の時間コードを作成する。"""

    if start_year > end_year:
        raise ValueError(
            "開始年は終了年以下である必要があります。"
        )

    return [
        f"{year}000000"
        for year in range(start_year, end_year + 1)
    ]


def create_lfs_working_hours_distribution_dataframe(
    response: dict[str, Any],
) -> pd.DataFrame:
    """e-Stat表3-3レスポンスを年齢別就業時間分布に変換する。"""

    values = (
        response["GET_STATS_DATA"]
        ["STATISTICAL_DATA"]
        ["DATA_INF"]
        ["VALUE"]
    )

    age_mapping = {
        code: name
        for name, code
        in LFS_WORKING_HOURS_AGE_CODES.items()
    }

    hours_mapping = {
        code: name
        for name, code
        in LFS_WORKING_HOURS_CATEGORY_CODES.items()
    }

    rows = []

    for item in ensure_list(values):
        age_code = item.get("@cat02")
        hours_code = item.get("@cat04")
        time_code = item.get("@time")

        age_group = age_mapping.get(age_code)
        metric = hours_mapping.get(hours_code)

        if (
            age_group is None
            or metric is None
            or time_code is None
        ):
            continue

        rows.append(
            {
                "year": int(time_code[:4]),
                "age_group": age_group,
                "metric": metric,
                "value": item.get("$"),
            }
        )

    long_df = pd.DataFrame(rows)

    if long_df.empty:
        return pd.DataFrame()

    long_df["value"] = pd.to_numeric(
        long_df["value"],
        errors="coerce",
    )

    duplicate = long_df.duplicated(
        subset=[
            "year",
            "age_group",
            "metric",
        ]
    )

    if duplicate.any():
        raise ValueError(
            "同じ年・年齢階級・就業時間区分のデータが重複しています。"
        )

    result = (
        long_df.pivot(
            index=[
                "year",
                "age_group",
            ],
            columns="metric",
            values="value",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    # --------------------------------------------------------
    # 必要な指標列を保証する
    # --------------------------------------------------------

    metric_columns = [
        "persons_at_work",
        "hours_1_34",
        "hours_35_48",
        "hours_49_plus",
        "hours_1_14",
        "hours_15_29",
        "hours_30_34",
        "hours_35_39",
        "hours_40_48",
        "hours_49_59",
        "hours_60_plus",
    ]

    for column in metric_columns:
        if column not in result.columns:
            result[column] = float("nan")

    # --------------------------------------------------------
    # 細区分から上位区分を再構成
    # --------------------------------------------------------

    result["hours_1_34_reconstructed"] = (
        result[
            [
                "hours_1_14",
                "hours_15_29",
                "hours_30_34",
            ]
        ]
        .sum(
            axis=1,
            min_count=3,
        )
    )

    result["hours_35_48_reconstructed"] = (
        result[
            [
                "hours_35_39",
                "hours_40_48",
            ]
        ]
        .sum(
            axis=1,
            min_count=2,
        )
    )

    result["hours_49_plus_reconstructed"] = (
        result[
            [
                "hours_49_59",
                "hours_60_plus",
            ]
        ]
        .sum(
            axis=1,
            min_count=2,
        )
    )

    # --------------------------------------------------------
    # 長期比較用3区分を調和
    #
    # 公式上位区分がある場合は公式値を優先。
    # 欠測している年のみ細区分合計で補完する。
    # --------------------------------------------------------

    result["hours_1_34_harmonized"] = (
        result["hours_1_34"]
        .combine_first(
            result["hours_1_34_reconstructed"]
        )
    )

    result["hours_35_48_harmonized"] = (
        result["hours_35_48"]
        .combine_first(
            result["hours_35_48_reconstructed"]
        )
    )

    result["hours_49_plus_harmonized"] = (
        result["hours_49_plus"]
        .combine_first(
            result["hours_49_plus_reconstructed"]
        )
    )

    harmonized_columns = [
        "hours_1_34_harmonized",
        "hours_35_48_harmonized",
        "hours_49_plus_harmonized",
    ]

    # --------------------------------------------------------
    # 長期3区分のカバレッジ
    # --------------------------------------------------------

    result["classified_workers"] = (
        result[harmonized_columns]
        .sum(
            axis=1,
            min_count=len(harmonized_columns),
        )
    )

    result["unclassified_workers"] = (
        result["persons_at_work"] - result["classified_workers"]
    )

    result["coverage"] = (
        result["classified_workers"] / result["persons_at_work"]
    )

    result["unclassified_share"] = (
        result["unclassified_workers"] / result["persons_at_work"]
    )

    # 構成比は「従業者総数」を分母にする。
    for column in harmonized_columns:
        result[f"{column}_share"] = (
            result[column] / result["persons_at_work"]
        )

    # --------------------------------------------------------
    # 詳細7区分
    # --------------------------------------------------------

    detail_columns = [
        "hours_1_14",
        "hours_15_29",
        "hours_30_34",
        "hours_35_39",
        "hours_40_48",
        "hours_49_59",
        "hours_60_plus",
    ]

    result["detailed_classified_workers"] = (
        result[detail_columns]
        .sum(
            axis=1,
            min_count=len(detail_columns),
        )
    )

    result["detailed_coverage"] = (
        result["detailed_classified_workers"] / result["persons_at_work"]
    )

    # 詳細区分も従業者総数を分母にする。
    for column in detail_columns:
        result[f"{column}_share"] = (
            result[column] / result["persons_at_work"]
        )

    return (
        result.sort_values(
            [
                "year",
                "age_group",
            ]
        )
        .reset_index(drop=True)
    )


def load_lfs_working_hours_distribution_from_api(
    app_id: str,
    start_year: int = 2000,
    end_year: int = 2025,
) -> pd.DataFrame:
    """e-Stat APIから表3-3の就業時間分布を取得する。"""

    age_codes = ",".join(
        LFS_WORKING_HOURS_AGE_CODES.values()
    )

    hours_codes = ",".join(
        LFS_WORKING_HOURS_CATEGORY_CODES.values()
    )

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
        stats_data_id=(
            LFS_WORKING_HOURS_DISTRIBUTION_STATS_DATA_ID
        ),
        filters=filters,
    )

    return create_lfs_working_hours_distribution_dataframe(
        response
    )
