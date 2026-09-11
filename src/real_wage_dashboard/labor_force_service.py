from pathlib import Path

import pandas as pd

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
