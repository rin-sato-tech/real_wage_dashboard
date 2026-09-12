from collections.abc import Sequence

import pandas as pd

HARMONIZED_HOURS_BANDS = (
    "hours_1_34",
    "hours_35_48",
    "hours_49_plus",
)

DETAILED_HOURS_BANDS = (
    "hours_1_14",
    "hours_15_29",
    "hours_30_34",
    "hours_35_39",
    "hours_40_48",
    "hours_49_59",
    "hours_60_plus",
)


def _validate_required_columns(
    df: pd.DataFrame,
    required_columns: set[str],
) -> None:
    """DataFrameに分析に必要な列が存在することを確認する。"""

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")


def _validate_no_missing(
    df: pd.DataFrame,
    columns: Sequence[str],
    message: str,
) -> None:
    """指定した列に欠損値がないことを確認する。"""

    if df[list(columns)].isna().any().any():
        raise ValueError(message)


def _create_start_end_comparison(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
    columns: Sequence[str],
    aliases: dict[str, str] | None = None,
) -> pd.DataFrame:
    """開始年と終了年のデータを年齢階級単位で横持ちに結合する。"""

    aliases = aliases or {}

    selected_columns = [
        "age_group",
        *columns,
    ]

    start = df.loc[
        df["year"] == start_year,
        selected_columns,
    ]

    if start.empty:
        raise ValueError(f"開始年 {start_year} のデータがありません。")

    end = df.loc[
        df["year"] == end_year,
        selected_columns,
    ]

    if end.empty:
        raise ValueError(f"終了年 {end_year} のデータがありません。")

    start_age_groups = set(start["age_group"])
    end_age_groups = set(end["age_group"])

    if start_age_groups != end_age_groups:
        only_start = sorted(start_age_groups - end_age_groups)
        only_end = sorted(end_age_groups - start_age_groups)

        raise ValueError(
            "開始年と終了年で年齢階級が一致しません。"
            f" 開始年のみ: {only_start}, 終了年のみ: {only_end}"
        )

    start = start.rename(
        columns={column: f"start_{aliases.get(column, column)}" for column in columns}
    )

    end = end.rename(
        columns={column: f"end_{aliases.get(column, column)}" for column in columns}
    )

    result = start.merge(
        end,
        on="age_group",
        how="inner",
        validate="one_to_one",
    )

    return result


# --------------------
# 年齢別平均就業時間
# --------------------
def create_age_hours_decomposition(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """平均週間就業時間の変化を年齢層内効果と構成効果に分解する。"""

    _validate_required_columns(
        df,
        {
            "year",
            "age_group",
            "average_weekly_hours",
            "worker_share",
        },
    )

    result = _create_start_end_comparison(
        df,
        start_year=start_year,
        end_year=end_year,
        columns=[
            "average_weekly_hours",
            "worker_share",
        ],
        aliases={
            "average_weekly_hours": "hours",
            "worker_share": "share",
        },
    )

    _validate_no_missing(
        result,
        [
            "start_hours",
            "start_share",
            "end_hours",
            "end_share",
        ],
        "比較対象年に就業時間または構成比の欠損があります。",
    )

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


def add_centered_composition_effect(decomposition_df: pd.DataFrame) -> pd.DataFrame:
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


# --------------------
# 年齢別就業構造
# --------------------
def create_employment_structure_summary(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """年齢別の就業者数・就業率・就業者シェアの変化をまとめる。"""

    _validate_required_columns(
        df,
        {
            "year",
            "age_group",
            "employed_persons",
            "employment_rate",
        },
    )

    data = df.copy()

    comparison_data = data.loc[data["year"].isin([start_year, end_year])]

    _validate_no_missing(
        comparison_data,
        [
            "employed_persons",
            "employment_rate",
        ],
        "比較対象年に就業者数または就業率の欠損があります。",
    )

    yearly_employed = data.groupby("year")["employed_persons"].transform("sum")

    comparison_mask = data["year"].isin([start_year, end_year])

    if yearly_employed.loc[comparison_mask].le(0).any():
        raise ValueError("比較対象年の就業者総数は0より大きい必要があります。")

    data["employed_share"] = data["employed_persons"] / yearly_employed

    result = _create_start_end_comparison(
        data,
        start_year=start_year,
        end_year=end_year,
        columns=[
            "employed_persons",
            "employment_rate",
            "employed_share",
        ],
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


def create_employment_count_decomposition(structure_df: pd.DataFrame) -> pd.DataFrame:
    """就業者数変化を人口要因と就業率要因に分解する。"""

    _validate_required_columns(
        structure_df,
        {
            "start_employed_persons",
            "end_employed_persons",
            "start_employment_rate",
            "end_employment_rate",
            "employed_persons_change",
        },
    )

    _validate_no_missing(
        structure_df,
        [
            "start_employed_persons",
            "end_employed_persons",
            "start_employment_rate",
            "end_employment_rate",
            "employed_persons_change",
        ],
        "就業者数分解に必要な値に欠損があります。",
    )

    rate_columns = [
        "start_employment_rate",
        "end_employment_rate",
    ]

    if (
        structure_df[rate_columns].le(0).any().any()
        or structure_df[rate_columns].gt(100).any().any()
    ):
        raise ValueError("就業率は0より大きく100以下である必要があります。")

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


# --------------------
# 就業時間分布
# --------------------
def create_working_hours_distribution_change(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """就業時間3区分の構成比変化を年齢階級別に比較する。"""

    _validate_required_columns(
        df,
        {
            "year",
            "age_group",
            "persons_at_work",
            *(f"{band}_harmonized" for band in HARMONIZED_HOURS_BANDS),
            *(f"{band}_harmonized_share" for band in HARMONIZED_HOURS_BANDS),
            "unclassified_share",
        },
    )

    columns = [
        "persons_at_work",
        *(f"{band}_harmonized" for band in HARMONIZED_HOURS_BANDS),
        *(f"{band}_harmonized_share" for band in HARMONIZED_HOURS_BANDS),
        "unclassified_share",
    ]

    result = _create_start_end_comparison(
        df,
        start_year=start_year,
        end_year=end_year,
        columns=columns,
    )

    calculation_columns = [
        "start_persons_at_work",
        "end_persons_at_work",
        *(
            f"{prefix}_{band}_harmonized"
            for prefix in ("start", "end")
            for band in HARMONIZED_HOURS_BANDS
        ),
        *(
            f"{prefix}_{band}_harmonized_share"
            for prefix in ("start", "end")
            for band in HARMONIZED_HOURS_BANDS
        ),
    ]

    _validate_no_missing(
        result,
        calculation_columns,
        "比較対象年の就業時間分布に欠損があります。",
    )

    for band in HARMONIZED_HOURS_BANDS:
        share_column = f"{band}_harmonized_share"

        result[f"{band}_share_change_pt"] = (
            result[f"end_{share_column}"] - result[f"start_{share_column}"]
        ) * 100

    result["persons_at_work_change"] = (
        result["end_persons_at_work"] - result["start_persons_at_work"]
    )

    for band in HARMONIZED_HOURS_BANDS:
        result[f"{band}_workers_change"] = (
            result[f"end_{band}_harmonized"] - result[f"start_{band}_harmonized"]
        )

    return result


def create_working_hours_distribution_trend(
    df: pd.DataFrame,
    age_group: str = "15歳以上",
) -> pd.DataFrame:
    """調和済み3区分の就業時間構成比を時系列で返す。"""

    _validate_required_columns(
        df,
        {
            "year",
            "age_group",
            *(f"{band}_harmonized_share" for band in HARMONIZED_HOURS_BANDS),
            "unclassified_share",
        },
    )

    share_columns = [f"{band}_harmonized_share" for band in HARMONIZED_HOURS_BANDS]

    result = (
        df.loc[
            df["age_group"] == age_group,
            [
                "year",
                *share_columns,
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

    _validate_required_columns(
        df,
        {
            "year",
            "age_group",
            "persons_at_work",
            *DETAILED_HOURS_BANDS,
            *(f"{band}_share" for band in DETAILED_HOURS_BANDS),
            "detailed_coverage",
        },
    )

    share_columns = [f"{band}_share" for band in DETAILED_HOURS_BANDS]

    columns = [
        "persons_at_work",
        *DETAILED_HOURS_BANDS,
        *share_columns,
        "detailed_coverage",
    ]

    result = _create_start_end_comparison(
        df,
        start_year=start_year,
        end_year=end_year,
        columns=columns,
    )

    calculation_columns = [
        *(
            f"{prefix}_{band}"
            for prefix in ("start", "end")
            for band in DETAILED_HOURS_BANDS
        ),
        *(
            f"{prefix}_{band}_share"
            for prefix in ("start", "end")
            for band in DETAILED_HOURS_BANDS
        ),
    ]

    _validate_no_missing(
        result,
        calculation_columns,
        "比較対象年の詳細就業時間分布に欠損があります。",
    )

    for band in DETAILED_HOURS_BANDS:
        result[f"{band}_share_change_pt"] = (
            result[f"end_{band}_share"] - result[f"start_{band}_share"]
        ) * 100

        result[f"{band}_workers_change"] = (
            result[f"end_{band}"] - result[f"start_{band}"]
        )

    return result


# --------------------
# 総労働投入
# --------------------
def create_total_labor_input_decomposition(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """延週間就業時間の変化を従業者数効果と1人当たり時間効果に分解する。"""

    _validate_required_columns(
        df,
        {
            "year",
            "age_group",
            "aggregate_weekly_hours",
            "average_weekly_hours",
            "implied_persons_at_work",
        },
    )

    result = _create_start_end_comparison(
        df,
        start_year=start_year,
        end_year=end_year,
        columns=[
            "aggregate_weekly_hours",
            "average_weekly_hours",
            "implied_persons_at_work",
        ],
        aliases={
            "implied_persons_at_work": "persons_at_work",
        },
    )

    _validate_no_missing(
        result,
        [
            "start_aggregate_weekly_hours",
            "start_average_weekly_hours",
            "start_persons_at_work",
            "end_aggregate_weekly_hours",
            "end_average_weekly_hours",
            "end_persons_at_work",
        ],
        "比較対象年に総労働時間・平均労働時間・従業者数の欠損があります。",
    )

    result["aggregate_weekly_hours_change"] = (
        result["end_aggregate_weekly_hours"] - result["start_aggregate_weekly_hours"]
    )

    result["persons_at_work_change"] = (
        result["end_persons_at_work"] - result["start_persons_at_work"]
    )

    result["average_weekly_hours_change"] = (
        result["end_average_weekly_hours"] - result["start_average_weekly_hours"]
    )

    # 対称分解
    #
    # Δ(NH)
    # = ((H0 + H1) / 2) ΔN
    # + ((N0 + N1) / 2) ΔH
    result["persons_effect"] = (
        (result["start_average_weekly_hours"] + result["end_average_weekly_hours"])
        / 2
        * result["persons_at_work_change"]
    )

    result["hours_effect"] = (
        (result["start_persons_at_work"] + result["end_persons_at_work"])
        / 2
        * result["average_weekly_hours_change"]
    )

    result["decomposition_error"] = (
        result["aggregate_weekly_hours_change"]
        - result["persons_effect"]
        - result["hours_effect"]
    )

    return result


def summarize_total_labor_input_decomposition(
    decomposition_df: pd.DataFrame,
) -> dict[str, float]:
    """総労働投入変化を人数・年齢層内時間・年齢構成へ分解する。"""

    start_total_hours = float(decomposition_df["start_aggregate_weekly_hours"].sum())

    end_total_hours = float(decomposition_df["end_aggregate_weekly_hours"].sum())

    start_total_persons = float(decomposition_df["start_persons_at_work"].sum())

    end_total_persons = float(decomposition_df["end_persons_at_work"].sum())

    if start_total_persons <= 0 or end_total_persons <= 0:
        raise ValueError("総労働投入の集計には従業者数が0より大きい必要があります。")

    start_average_hours = start_total_hours / start_total_persons

    end_average_hours = end_total_hours / end_total_persons

    total_change = end_total_hours - start_total_hours

    average_persons = (start_total_persons + end_total_persons) / 2

    average_hours = (start_average_hours + end_average_hours) / 2

    # --------------------------------------------------------
    # 1. 従業者総数効果
    # --------------------------------------------------------

    persons_effect = average_hours * (end_total_persons - start_total_persons)

    # --------------------------------------------------------
    # 2. 平均時間変化を
    #    年齢層内効果と年齢構成効果へ分解
    # --------------------------------------------------------

    start_share = decomposition_df["start_persons_at_work"] / start_total_persons

    end_share = decomposition_df["end_persons_at_work"] / end_total_persons

    within_hours_change = (
        (start_share + end_share)
        / 2
        * (
            decomposition_df["end_average_weekly_hours"]
            - decomposition_df["start_average_weekly_hours"]
        )
    ).sum()

    composition_hours_change = (
        (
            decomposition_df["start_average_weekly_hours"]
            + decomposition_df["end_average_weekly_hours"]
        )
        / 2
        * (end_share - start_share)
    ).sum()

    within_effect = average_persons * within_hours_change

    composition_effect = average_persons * composition_hours_change

    average_hours_effect = within_effect + composition_effect

    decomposition_error = (
        total_change - persons_effect - within_effect - composition_effect
    )

    return {
        "start_total_weekly_hours": start_total_hours,
        "end_total_weekly_hours": end_total_hours,
        "total_change_weekly_hours": total_change,
        "total_change_pct": ((end_total_hours / start_total_hours - 1) * 100),
        "start_total_persons_at_work": start_total_persons,
        "end_total_persons_at_work": end_total_persons,
        "start_average_weekly_hours": start_average_hours,
        "end_average_weekly_hours": end_average_hours,
        "persons_effect_weekly_hours": persons_effect,
        "average_hours_effect_weekly_hours": (average_hours_effect),
        "within_age_hours_effect_weekly_hours": (within_effect),
        "age_composition_effect_weekly_hours": (composition_effect),
        "decomposition_error": decomposition_error,
    }


def create_total_labor_input_period_summary(
    df: pd.DataFrame,
    periods: list[tuple[int, int]],
) -> pd.DataFrame:
    """複数期間の総労働投入と人数・時間効果を要約する。"""

    records = []

    for start_year, end_year in periods:
        decomposition = create_total_labor_input_decomposition(
            df,
            start_year=start_year,
            end_year=end_year,
        )

        summary = summarize_total_labor_input_decomposition(decomposition)

        records.append(
            {
                "start_year": start_year,
                "end_year": end_year,
                "start_total_weekly_hours": (summary["start_total_weekly_hours"]),
                "end_total_weekly_hours": (summary["end_total_weekly_hours"]),
                "total_change_weekly_hours": (summary["total_change_weekly_hours"]),
                "total_change_pct": (summary["total_change_pct"]),
                "persons_effect_weekly_hours": (summary["persons_effect_weekly_hours"]),
                "within_age_hours_effect_weekly_hours": (
                    summary["within_age_hours_effect_weekly_hours"]
                ),
                "age_composition_effect_weekly_hours": (
                    summary["age_composition_effect_weekly_hours"]
                ),
            }
        )
    return pd.DataFrame(records)


def create_total_labor_input_trend(df: pd.DataFrame) -> pd.DataFrame:
    """年次の総労働投入と従業者数・平均週間就業時間を集計する。"""

    _validate_required_columns(
        df,
        {
            "year",
            "aggregate_weekly_hours",
            "implied_persons_at_work",
            "average_weekly_hours",
        },
    )

    yearly = df.groupby("year", as_index=False).agg(
        total_weekly_hours=(
            "aggregate_weekly_hours",
            lambda x: x.sum(min_count=1),
        ),
        total_persons_at_work=(
            "implied_persons_at_work",
            lambda x: x.sum(min_count=1),
        ),
    )

    if yearly["total_persons_at_work"].le(0).any():
        raise ValueError("年間の従業者数は0より大きい必要があります。")

    yearly["average_weekly_hours"] = (
        yearly["total_weekly_hours"] / yearly["total_persons_at_work"]
    )

    return yearly.sort_values("year").reset_index(drop=True)
