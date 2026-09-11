import pandas as pd


def create_age_hours_decomposition(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """平均週間就業時間の変化を年齢層内効果と構成効果に分解する。"""

    required_columns = {
        "year",
        "age_group",
        "average_weekly_hours",
        "worker_share",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    start = df.loc[
        df["year"] == start_year,
        [
            "age_group",
            "average_weekly_hours",
            "worker_share",
        ],
    ].rename(
        columns={
            "average_weekly_hours": "start_hours",
            "worker_share": "start_share",
        }
    )

    end = df.loc[
        df["year"] == end_year,
        [
            "age_group",
            "average_weekly_hours",
            "worker_share",
        ],
    ].rename(
        columns={
            "average_weekly_hours": "end_hours",
            "worker_share": "end_share",
        }
    )

    result = start.merge(
        end,
        on="age_group",
        how="inner",
        validate="one_to_one",
    )

    if result.empty:
        raise ValueError("比較対象となる年齢階級データがありません。")

    if (
        result[
            [
                "start_hours",
                "start_share",
                "end_hours",
                "end_share",
            ]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("比較対象年に就業時間または構成比の欠損があります。")

    result["within_effect"] = (
        (result["start_share"] + result["end_share"])
        / 2
        * (result["end_hours"] - result["start_hours"])
    )

    result["composition_effect"] = (
        (result["start_hours"] + result["end_hours"])
        / 2
        * (result["end_share"] - result["start_share"])
    )

    return result


def summarize_age_hours_decomposition(
    decomposition_df: pd.DataFrame,
) -> dict[str, float]:
    """年齢別分解結果を全体効果へ集約する。"""

    start_average = float(
        (decomposition_df["start_hours"] * decomposition_df["start_share"]).sum()
    )

    end_average = float(
        (decomposition_df["end_hours"] * decomposition_df["end_share"]).sum()
    )

    within_effect = float(decomposition_df["within_effect"].sum())

    composition_effect = float(decomposition_df["composition_effect"].sum())

    total_change = end_average - start_average

    decomposition_error = total_change - within_effect - composition_effect

    return {
        "start_average_weekly_hours": start_average,
        "end_average_weekly_hours": end_average,
        "total_change_hours": total_change,
        "within_effect_hours": within_effect,
        "composition_effect_hours": composition_effect,
        "decomposition_error": decomposition_error,
    }


def add_centered_composition_effect(
    decomposition_df: pd.DataFrame,
) -> pd.DataFrame:
    """年齢別構成効果を全体平均時間を基準に中心化する。"""

    result = decomposition_df.copy()

    start_average = (result["start_hours"] * result["start_share"]).sum()

    end_average = (result["end_hours"] * result["end_share"]).sum()

    reference_hours = (start_average + end_average) / 2

    result["average_hours"] = (result["start_hours"] + result["end_hours"]) / 2

    result["share_change"] = result["end_share"] - result["start_share"]

    result["centered_composition_effect"] = (
        result["average_hours"] - reference_hours
    ) * result["share_change"]

    return result


def create_age_hours_period_summary(
    df: pd.DataFrame,
    periods: list[tuple[int, int]],
) -> pd.DataFrame:
    """複数期間について年齢構成・年齢層内効果を一括集計する。"""

    records: list[dict[str, float | int]] = []

    for start_year, end_year in periods:
        decomposition = create_age_hours_decomposition(
            df,
            start_year=start_year,
            end_year=end_year,
        )

        summary = summarize_age_hours_decomposition(decomposition)

        records.append(
            {
                "start_year": start_year,
                "end_year": end_year,
                "start_average_weekly_hours": (summary["start_average_weekly_hours"]),
                "end_average_weekly_hours": (summary["end_average_weekly_hours"]),
                "total_change_hours": (summary["total_change_hours"]),
                "within_effect_hours": (summary["within_effect_hours"]),
                "composition_effect_hours": (summary["composition_effect_hours"]),
            }
        )

    return pd.DataFrame(records)


def create_employment_structure_summary(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """年齢別の就業者数・就業率・就業者シェアの変化をまとめる。"""

    data = df.copy()

    total_employed = data.groupby("year")["employed_persons"].transform("sum")

    data["employed_share"] = data["employed_persons"] / total_employed

    start = data.loc[
        data["year"] == start_year,
        [
            "age_group",
            "employed_persons",
            "employment_rate",
            "employed_share",
        ],
    ].rename(
        columns={
            "employed_persons": "start_employed_persons",
            "employment_rate": "start_employment_rate",
            "employed_share": "start_employed_share",
        }
    )

    end = data.loc[
        data["year"] == end_year,
        [
            "age_group",
            "employed_persons",
            "employment_rate",
            "employed_share",
        ],
    ].rename(
        columns={
            "employed_persons": "end_employed_persons",
            "employment_rate": "end_employment_rate",
            "employed_share": "end_employed_share",
        }
    )

    result = start.merge(
        end,
        on="age_group",
        how="inner",
        validate="one_to_one",
    )

    result["employed_persons_change"] = (
        result["end_employed_persons"] - result["start_employed_persons"]
    )

    result["employment_rate_change_pt"] = (
        result["end_employment_rate"] - result["start_employment_rate"]
    )

    result["employed_share_change_pt"] = (
        result["end_employed_share"] - result["start_employed_share"]
    ) * 100

    return result


def create_employment_count_decomposition(
    structure_df: pd.DataFrame,
) -> pd.DataFrame:
    """就業者数変化を人口要因と就業率要因に分解する。"""

    result = structure_df.copy()

    start_rate = result["start_employment_rate"] / 100
    end_rate = result["end_employment_rate"] / 100

    # 就業者数 / 就業率から人口を逆算
    result["start_population"] = result["start_employed_persons"] / start_rate

    result["end_population"] = result["end_employed_persons"] / end_rate

    result["population_change"] = result["end_population"] - result["start_population"]

    # 対称分解
    result["population_effect"] = (
        (start_rate + end_rate) / 2 * result["population_change"]
    )

    result["employment_rate_effect"] = (
        (result["start_population"] + result["end_population"])
        / 2
        * (end_rate - start_rate)
    )

    result["decomposition_error"] = (
        result["employed_persons_change"]
        - result["population_effect"]
        - result["employment_rate_effect"]
    )

    return result


def create_working_hours_distribution_change(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """就業時間3区分の構成比変化を年齢階級別に比較する。"""

    columns = [
        "age_group",
        "persons_at_work",
        "hours_1_34_harmonized",
        "hours_35_48_harmonized",
        "hours_49_plus_harmonized",
        "hours_1_34_harmonized_share",
        "hours_35_48_harmonized_share",
        "hours_49_plus_harmonized_share",
        "unclassified_share",
    ]

    start = df.loc[
        df["year"] == start_year,
        columns,
    ].rename(
        columns={
            column: f"start_{column}" for column in columns if column != "age_group"
        }
    )

    end = df.loc[
        df["year"] == end_year,
        columns,
    ].rename(
        columns={column: f"end_{column}" for column in columns if column != "age_group"}
    )

    result = start.merge(
        end,
        on="age_group",
        how="inner",
        validate="one_to_one",
    )

    for name in [
        "hours_1_34",
        "hours_35_48",
        "hours_49_plus",
    ]:
        share_column = f"{name}_harmonized_share"

        result[f"{name}_share_change_pt"] = (
            result[f"end_{share_column}"] - result[f"start_{share_column}"]
        ) * 100

    result["persons_at_work_change"] = (
        result["end_persons_at_work"] - result["start_persons_at_work"]
    )

    result["hours_1_34_workers_change"] = (
        result["end_hours_1_34_harmonized"] - result["start_hours_1_34_harmonized"]
    )

    result["hours_35_48_workers_change"] = (
        result["end_hours_35_48_harmonized"] - result["start_hours_35_48_harmonized"]
    )

    result["hours_49_plus_workers_change"] = (
        result["end_hours_49_plus_harmonized"]
        - result["start_hours_49_plus_harmonized"]
    )

    return result


def create_working_hours_distribution_trend(
    df: pd.DataFrame,
    age_group: str = "15歳以上",
) -> pd.DataFrame:
    """調和済み3区分の就業時間構成比を時系列で返す。"""

    required_columns = {
        "year",
        "age_group",
        "hours_1_34_harmonized_share",
        "hours_35_48_harmonized_share",
        "hours_49_plus_harmonized_share",
        "unclassified_share",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    result = (
        df.loc[
            df["age_group"] == age_group,
            [
                "year",
                "hours_1_34_harmonized_share",
                "hours_35_48_harmonized_share",
                "hours_49_plus_harmonized_share",
                "unclassified_share",
            ],
        ]
        .sort_values("year")
        .reset_index(drop=True)
    )

    return result


def create_working_hours_distribution_period_summary(
    df: pd.DataFrame,
    periods: list[tuple[int, int]],
    age_group: str = "15歳以上",
) -> pd.DataFrame:
    """就業時間3区分の構成比変化を複数期間で要約する。"""

    records = []

    for start_year, end_year in periods:
        result = create_working_hours_distribution_change(
            df,
            start_year=start_year,
            end_year=end_year,
        )

        matched = result.loc[result["age_group"] == age_group]

        if len(matched) != 1:
            raise ValueError(f"年齢階級を一意に取得できません: {age_group}")

        row = matched.iloc[0]

        records.append(
            {
                "start_year": start_year,
                "end_year": end_year,
                "hours_1_34_change_pt": (row["hours_1_34_share_change_pt"]),
                "hours_35_48_change_pt": (row["hours_35_48_share_change_pt"]),
                "hours_49_plus_change_pt": (row["hours_49_plus_share_change_pt"]),
            }
        )

    return pd.DataFrame(records)


def create_detailed_working_hours_distribution_change(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """詳細7区分の就業時間構成比変化を年齢階級別に比較する。"""

    detail_columns = [
        "hours_1_14",
        "hours_15_29",
        "hours_30_34",
        "hours_35_39",
        "hours_40_48",
        "hours_49_59",
        "hours_60_plus",
    ]

    share_columns = [f"{column}_share" for column in detail_columns]

    columns = [
        "age_group",
        "persons_at_work",
        *detail_columns,
        *share_columns,
        "detailed_coverage",
    ]

    start = df.loc[
        df["year"] == start_year,
        columns,
    ].rename(
        columns={
            column: f"start_{column}" for column in columns if column != "age_group"
        }
    )

    end = df.loc[
        df["year"] == end_year,
        columns,
    ].rename(
        columns={column: f"end_{column}" for column in columns if column != "age_group"}
    )

    result = start.merge(
        end,
        on="age_group",
        how="inner",
        validate="one_to_one",
    )

    for column in detail_columns:
        result[f"{column}_share_change_pt"] = (
            result[f"end_{column}_share"] - result[f"start_{column}_share"]
        ) * 100

        result[f"{column}_workers_change"] = (
            result[f"end_{column}"] - result[f"start_{column}"]
        )

    return result
