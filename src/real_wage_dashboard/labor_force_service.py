from pathlib import Path
from typing import Any

import pandas as pd

from real_wage_dashboard.config import (
    LFS_EMPLOYMENT_TYPE_AGE_CODES,
    LFS_EMPLOYMENT_TYPE_CODES,
    LFS_EMPLOYMENT_TYPE_HOURS_BASE_FILTERS,
    LFS_EMPLOYMENT_TYPE_HOURS_CODES,
    LFS_EMPLOYMENT_TYPE_HOURS_STATS_DATA_ID,
    LFS_HOURS_BY_AGE_SEX_BASE_FILTERS,
    LFS_HOURS_BY_AGE_SEX_CODES,
    LFS_HOURS_BY_AGE_SEX_STATS_DATA_ID,
    LFS_HOURS_BY_AGE_SEX_TAB_CODES,
    LFS_WORKING_HOURS_AGE_CODES,
    LFS_WORKING_HOURS_CATEGORY_CODES,
    LFS_WORKING_HOURS_DISTRIBUTION_BASE_FILTERS,
    LFS_WORKING_HOURS_DISTRIBUTION_STATS_DATA_ID,
)
from real_wage_dashboard.estat_client import get_stats_data
from real_wage_dashboard.estat_response import (
    ensure_list,
)

# Excel元表では、年齢階級ごとに就業者数と就業率が別の列に格納されている。
# タプルは (年齢階級名, 就業者数の列位置, 就業率の列位置) を表す。
EMPLOYMENT_AGE_COLUMNS = (
    ("15～24歳", 4, 15),
    ("25～34歳", 5, 16),
    ("35～44歳", 6, 17),
    ("45～54歳", 7, 18),
    ("55～64歳", 8, 19),
    ("65歳以上", 9, 20),
)

# 就業時間CSVで使用する年齢階級を、就業構造データと同じ定義にそろえる。
AGE_GROUPS = [age_group for age_group, _, _ in EMPLOYMENT_AGE_COLUMNS]

# e-Statの表章項目名を、分析コード内で使用する列名へ変換する。
LFS_HOURS_METRICS = {
    "平均週間就業時間【時間】": "average_weekly_hours",
    "延週間就業時間【万時間】": "aggregate_weekly_hours",
}

# 長期比較用の3区分を、より細かな就業時間区分から再構成する際の対応関係。
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

# 詳細分析で使用する週間就業時間7区分。
LFS_DETAILED_HOURS_COLUMNS = (
    "hours_1_14",
    "hours_15_29",
    "hours_30_34",
    "hours_35_39",
    "hours_40_48",
    "hours_49_59",
    "hours_60_plus",
)

# pivot後に必ず用意しておく就業時間分布の基本列。
# APIレスポンスに特定区分が存在しない場合も、欠損列としてスキーマを維持する。
LFS_DISTRIBUTION_METRIC_COLUMNS = (
    "persons_at_work",
    *LFS_HOURS_RECONSTRUCTION_COMPONENTS,
    *LFS_DETAILED_HOURS_COLUMNS,
)

# ============================================================
# 1. 年齢別就業構造
# ============================================================


# 1-1
def _reshape_lfs_employment_by_age(
    raw: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """労働力調査の年齢別就業者数・就業率を分析用DataFrameへ整形する。"""

    # 元Excelはヘッダーを固定して読み込んでいないため、
    # 第2列から数値として解釈できる年だけを抽出する。
    years = pd.to_numeric(
        raw.iloc[:, 1],
        errors="coerce",
    )

    # betweenでbooleanにして、locで指定期間に該当する年次データの行だけを抽出する。
    data = raw.loc[years.between(start_year, end_year)].copy()

    # 元表の年列を数値化し、分析用のyear列として保持する。
    data["year"] = pd.to_numeric(
        data.iloc[:, 1],
        errors="coerce",
    ).astype(int)

    records: list[dict[str, int | float | str]] = []

    # 元表は1年が1行、年齢階級が列方向に並ぶwide形式。
    # 分析しやすい「1年 × 1年齢階級 = 1行」のlong形式へ展開する。
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


# 1-2
def load_lfs_employment_by_age(
    file_path: str | Path,
    start_year: int = 2000,
    end_year: int = 2025,
) -> pd.DataFrame:
    """年齢別就業者数・就業率を分析用DataFrameとして読み込む。"""

    # 元Excelは複雑な表形式のため、列名として解釈せず位置ベースで読み込む。
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


# ============================================================
# 2. 年齢別就業時間
# ============================================================


# 2-1
def _reshape_lfs_hours_by_age(raw: pd.DataFrame) -> pd.DataFrame:
    """労働力調査の年齢別就業時間データを分析用のwide形式に整形する。"""

    data = raw.copy()

    # 「2025年」などの時間軸文字列から4桁の西暦部分だけを取り出す。
    data["year"] = data["時間軸（年次）"].astype(str).str.extract(r"(\d{4})")[0]

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    # 元CSVには多数の表章項目があるため、
    # 平均週間就業時間と延週間就業時間だけを分析対象とする。
    data = data.loc[data["表章項目"].isin(LFS_HOURS_METRICS)].copy()

    # 年齢階級が列方向に並ぶ元表を、
    # year × 表章項目 × age_group のlong形式へ変換する。
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

    # 日本語の表章項目名を分析用の内部列名へ置き換える。
    long["metric"] = long["表章項目"].replace(LFS_HOURS_METRICS)

    # 平均週間就業時間と延週間就業時間を再び列方向へ展開し、
    # 1年 × 1年齢階級を1行とする分析用形式にする。
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


# 2-2
def _add_lfs_hours_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """年齢別就業時間データに従業者数推計と構成比を追加する。"""

    result = df.copy()

    # 延週間就業時間 = 従業者数 × 1人当たり平均週間就業時間
    # という恒等関係を使って従業者数を逆算する。
    #
    # aggregate_weekly_hours の単位は「万時間」なので、
    # implied_persons_at_work の単位は「万人」となる。
    #
    # これは別データから取得する employed_persons とは異なる系列であり、
    # 就業時間データ内部で整合する人数指標として使用する。
    result["implied_persons_at_work"] = (
        result["aggregate_weekly_hours"] / result["average_weekly_hours"]
    )

    # 各年について、年齢階級別の逆算従業者数を合計する。
    yearly_total = result.groupby("year")["implied_persons_at_work"].transform(
        lambda x: x.sum(min_count=1)
    )

    # 平均週間就業時間の年齢構成分解で使用する従業者構成比。
    # employed_persons ベースの構成比ではない点に注意する。
    result["worker_share"] = result["implied_persons_at_work"] / yearly_total

    return result


# 2-3
def load_lfs_hours_by_age(file_path: str | Path) -> pd.DataFrame:
    """年齢別の平均・延週間就業時間を分析用DataFrameとして読み込む。"""

    # e-Stat CSVの先頭13行は表題・注記等のメタデータなので読み飛ばす。
    raw = pd.read_csv(
        file_path,
        encoding="utf-8-sig",
        skiprows=13,
    )

    result = _reshape_lfs_hours_by_age(raw)
    result = _add_lfs_hours_derived_metrics(result)

    return result.sort_values(["year", "age_group"]).reset_index(drop=True)


# ============================================================
# 3. 年齢別統合dataframe
# ============================================================


# 3-1
def create_lfs_age_dataframe(
    employment_path: str | Path,
    hours_path: str | Path,
) -> pd.DataFrame:
    """年齢別就業構造と就業時間を結合する。"""

    employment = load_lfs_employment_by_age(employment_path)

    hours = load_lfs_hours_by_age(hours_path)

    # 就業構造データを基準にして結合する。
    # 対応する就業時間データが存在しない年・年齢階級は削除せず、
    # 就業時間側を欠損として残す。
    #
    # year × age_group は双方で一意であることを前提とする。
    return employment.merge(
        hours,
        on=["year", "age_group"],
        how="left",
        validate="one_to_one",
    )


# ============================================================
# 4. 男女・年齢別就業時間
# ============================================================


def _create_lfs_hours_by_age_sex_long_dataframe(
    response: dict[str, Any],
) -> pd.DataFrame:
    """表3-5のAPIレスポンスを男女・年齢別就業時間のlong形式へ変換する。"""

    try:
        values = response["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
    except (KeyError, TypeError):
        raise ValueError("e-StatレスポンスからVALUEを取得できません。") from None

    age_mapping = {
        code: name
        for name, code in LFS_WORKING_HOURS_AGE_CODES.items()
        if name in AGE_GROUPS
    }

    sex_mapping = {code: name for name, code in LFS_HOURS_BY_AGE_SEX_CODES.items()}

    metric_mapping = {
        code: name for name, code in LFS_HOURS_BY_AGE_SEX_TAB_CODES.items()
    }

    rows: list[dict[str, int | float | str]] = []

    for item in ensure_list(values):
        metric = metric_mapping.get(item.get("@tab"))
        sex = sex_mapping.get(item.get("@cat01"))
        age_group = age_mapping.get(item.get("@cat02"))
        time_code = item.get("@time")

        if metric is None or sex is None or age_group is None or time_code is None:
            continue

        time_code = str(time_code)

        if len(time_code) < 4 or not time_code[:4].isdigit():
            raise ValueError(f"不正な時間コードです: {time_code}")

        rows.append(
            {
                "year": int(time_code[:4]),
                "age_group": age_group,
                "sex": sex,
                "metric": metric,
                "value": item.get("$"),
            }
        )

    result = pd.DataFrame(
        rows,
        columns=[
            "year",
            "age_group",
            "sex",
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


def _pivot_lfs_hours_by_age_sex(
    long_df: pd.DataFrame,
) -> pd.DataFrame:
    """男女・年齢別就業時間をwide形式へ変換する。"""

    duplicate = long_df.duplicated(
        subset=[
            "year",
            "age_group",
            "sex",
            "metric",
        ]
    )

    if duplicate.any():
        raise ValueError("同じ年・年齢階級・性別・表章項目のデータが重複しています。")

    result = (
        long_df.pivot(
            index=[
                "year",
                "age_group",
                "sex",
            ],
            columns="metric",
            values="value",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    for column in LFS_HOURS_BY_AGE_SEX_TAB_CODES:
        if column not in result.columns:
            result[column] = float("nan")

    return result


def _add_lfs_hours_by_age_sex_derived_metrics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """男女・年齢別就業時間に逆算従業者数と性別構成比を追加する。"""

    result = df.copy()

    valid_hours = result["average_weekly_hours"].dropna()

    if valid_hours.le(0).any():
        raise ValueError("平均週間就業時間は0より大きい必要があります。")

    result["implied_persons_at_work"] = (
        result["aggregate_weekly_hours"] / result["average_weekly_hours"]
    )

    # 性別構成比は男・女だけを分母にする。
    sex_mask = result["sex"].isin(["male", "female"])

    result["sex_share_within_age"] = float("nan")

    sex_totals = (
        result.loc[sex_mask]
        .groupby(
            [
                "year",
                "age_group",
            ]
        )["implied_persons_at_work"]
        .transform(lambda x: x.sum(min_count=1))
    )

    result.loc[
        sex_mask,
        "sex_share_within_age",
    ] = (
        result.loc[
            sex_mask,
            "implied_persons_at_work",
        ]
        / sex_totals
    )

    return result


def create_lfs_hours_by_age_sex_dataframe(
    response: dict[str, Any],
) -> pd.DataFrame:
    """e-Stat表3-5を男女・年齢別就業時間DataFrameへ変換する。"""

    long_df = _create_lfs_hours_by_age_sex_long_dataframe(response)

    if long_df.empty:
        return pd.DataFrame()

    result = _pivot_lfs_hours_by_age_sex(long_df)

    result = _add_lfs_hours_by_age_sex_derived_metrics(result)

    return result.sort_values(
        [
            "year",
            "age_group",
            "sex",
        ]
    ).reset_index(drop=True)


def load_lfs_hours_by_age_sex_from_api(
    app_id: str,
    start_year: int = 2000,
    end_year: int = 2025,
) -> pd.DataFrame:
    """e-Stat APIから表3-5の男女・年齢別就業時間を取得する。"""

    age_codes = ",".join(
        LFS_WORKING_HOURS_AGE_CODES[age_group] for age_group in AGE_GROUPS
    )

    sex_codes = ",".join(LFS_HOURS_BY_AGE_SEX_CODES.values())

    tab_codes = ",".join(LFS_HOURS_BY_AGE_SEX_TAB_CODES.values())

    time_codes = ",".join(
        create_lfs_working_hours_time_codes(
            start_year=start_year,
            end_year=end_year,
        )
    )

    filters = {
        **LFS_HOURS_BY_AGE_SEX_BASE_FILTERS,
        "cdTab": tab_codes,
        "cdCat01": sex_codes,
        "cdCat02": age_codes,
        "cdTime": time_codes,
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=LFS_HOURS_BY_AGE_SEX_STATS_DATA_ID,
        filters=filters,
    )

    return create_lfs_hours_by_age_sex_dataframe(response)


# ============================================================
# 4. e-Stat就業時間分布のサービスフロー
# ============================================================


# 4-1
def create_lfs_working_hours_time_codes(
    start_year: int = 2000,
    end_year: int = 2025,
) -> list[str]:
    """労働力調査・年次表の時間コードを作成する。"""

    if start_year > end_year:
        raise ValueError("開始年は終了年以下である必要があります。")

    # e-Statの年次表では、年を YYYY000000 形式の時間コードで指定する。
    return [f"{year}000000" for year in range(start_year, end_year + 1)]


# 4-2
def _create_lfs_distribution_long_dataframe(response: dict[str, Any]) -> pd.DataFrame:
    """e-Statレスポンスを年・年齢階級・就業時間区分のlong形式へ変換する。"""

    try:
        # e-Statレスポンスの実測値は DATA_INF.VALUE に格納される。
        values = response["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
    except (KeyError, TypeError):
        raise ValueError("e-StatレスポンスからVALUEを取得できません。") from None

    # config側は「名称 -> e-Statコード」なので、
    # APIレスポンスのコードを名称へ戻すため逆引き辞書を作る。
    age_mapping = {code: name for name, code in LFS_WORKING_HOURS_AGE_CODES.items()}

    hours_mapping = {
        code: name for name, code in LFS_WORKING_HOURS_CATEGORY_CODES.items()
    }

    rows: list[dict[str, int | float | str]] = []

    # VALUEは取得件数によってdictまたはlistになり得るため、
    # ensure_list()で常に反復可能なlistへ正規化する。
    for item in ensure_list(values):
        age_code = item.get("@cat02")
        hours_code = item.get("@cat04")
        time_code = item.get("@time")

        age_group = age_mapping.get(age_code)
        metric = hours_mapping.get(hours_code)

        # 今回の分析対象として定義していない区分は取り込まない。
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
                # e-Statでは観測値本体が "$" キーに格納されている。
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


# 4-3
def _pivot_lfs_distribution(long_df: pd.DataFrame) -> pd.DataFrame:
    """long形式の就業時間分布を年・年齢階級単位のwide形式へ変換する。"""

    # pivotでは year × age_group × metric が一意である必要がある。
    # 重複があれば、API条件または元データの想定が崩れているため明示的に失敗させる。
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

    # 年代によって存在しない区分があっても、
    # 後続処理が常に同じ列構成を前提にできるよう欠損列を補う。
    for column in LFS_DISTRIBUTION_METRIC_COLUMNS:
        if column not in result.columns:
            result[column] = float("nan")

    return result


# 4-4
def _add_reconstructed_hours_bands(df: pd.DataFrame) -> pd.DataFrame:
    """詳細就業時間区分から長期比較用3区分を再構成する。"""

    result = df.copy()

    for band, components in LFS_HOURS_RECONSTRUCTION_COMPONENTS.items():
        # 構成する詳細区分がすべて存在する場合だけ合計する。
        # 一部区分が欠損した状態で部分合計を作ることを防ぐため、
        # min_count を構成区分数と同じ値にする。
        result[f"{band}_reconstructed"] = result[list(components)].sum(
            axis=1,
            min_count=len(components),
        )

    return result


# 4-5
def _add_harmonized_hours_bands(df: pd.DataFrame) -> pd.DataFrame:
    """公式上位区分を優先し、欠測時のみ再構成値で補完する。"""

    result = df.copy()

    for band in LFS_HOURS_RECONSTRUCTION_COMPONENTS:
        # 同じ3区分でも、年代によって公式上位区分の有無が異なる。
        # 比較可能な長期系列を作るため、
        # 公式値があればそれを使い、存在しない場合だけ詳細区分の合計で補う。
        result[f"{band}_harmonized"] = result[band].combine_first(
            result[f"{band}_reconstructed"]
        )

    return result


# 4-6
def _validate_persons_at_work(df: pd.DataFrame) -> None:
    """値が存在する従業者総数が正であることを確認する。"""

    persons = df["persons_at_work"].dropna()

    if persons.le(0).any():
        raise ValueError("従業者総数は0より大きい必要があります。")


# 4-7
def _add_harmonized_distribution_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """調和済み3区分についてカバレッジと構成比を追加する。"""

    result = df.copy()

    _validate_persons_at_work(result)

    harmonized_columns = [
        f"{band}_harmonized" for band in LFS_HOURS_RECONSTRUCTION_COMPONENTS
    ]

    # 3区分すべてが利用可能な場合だけ分類済み人数を算出する。
    result["classified_workers"] = result[harmonized_columns].sum(
        axis=1,
        min_count=len(harmonized_columns),
    )

    # persons_at_work のうち3区分へ分類できなかった人数を残差として求める。
    result["unclassified_workers"] = (
        result["persons_at_work"] - result["classified_workers"]
    )

    # coverage は従業者総数のうち3区分で説明できる割合。
    result["coverage"] = result["classified_workers"] / result["persons_at_work"]

    result["unclassified_share"] = (
        result["unclassified_workers"] / result["persons_at_work"]
    )

    # 各区分の構成比は「分類済み人数」ではなく persons_at_work を分母とする。
    # したがって3区分のshare合計は coverage と一致する。
    for column in harmonized_columns:
        result[f"{column}_share"] = result[column] / result["persons_at_work"]

    return result


# 4-8
def _add_detailed_distribution_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """詳細7区分についてカバレッジと構成比を追加する。"""

    result = df.copy()

    _validate_persons_at_work(result)

    # 7区分がすべて存在する場合のみ分類済み人数を計算し、
    # 一部欠損を0扱いした部分合計は作らない。
    result["detailed_classified_workers"] = result[
        list(LFS_DETAILED_HOURS_COLUMNS)
    ].sum(
        axis=1,
        min_count=len(LFS_DETAILED_HOURS_COLUMNS),
    )

    result["detailed_coverage"] = (
        result["detailed_classified_workers"] / result["persons_at_work"]
    )

    # 3区分と同様、構成比の分母には従業者総数を使う。
    for column in LFS_DETAILED_HOURS_COLUMNS:
        result[f"{column}_share"] = result[column] / result["persons_at_work"]

    return result


# 4-9
def create_lfs_working_hours_distribution_dataframe(
    response: dict[str, Any],
) -> pd.DataFrame:
    """e-Stat表3-3レスポンスを年齢別就業時間分布に変換する。"""

    # 1. APIレスポンスを year × age_group × metric のlong形式へ変換
    long_df = _create_lfs_distribution_long_dataframe(response)

    if long_df.empty:
        return pd.DataFrame()

    # 2. 1行を year × age_group とするwide形式へ変換
    result = _pivot_lfs_distribution(long_df)

    # 3. 詳細区分から長期比較用3区分を再構成
    result = _add_reconstructed_hours_bands(result)

    # 4. 公式値を優先して長期比較用の調和済み3区分を作成
    result = _add_harmonized_hours_bands(result)

    # 5. 3区分・詳細7区分それぞれのカバレッジと構成比を追加
    result = _add_harmonized_distribution_metrics(result)
    result = _add_detailed_distribution_metrics(result)

    return result.sort_values(["year", "age_group"]).reset_index(drop=True)


# 4-10
def load_lfs_working_hours_distribution_from_api(
    app_id: str,
    start_year: int = 2000,
    end_year: int = 2025,
) -> pd.DataFrame:
    """e-Stat APIから表3-3の就業時間分布を取得する。"""

    # e-Stat APIでは複数コードをカンマ区切りで指定する。
    age_codes = ",".join(LFS_WORKING_HOURS_AGE_CODES.values())
    hours_codes = ",".join(LFS_WORKING_HOURS_CATEGORY_CODES.values())

    time_codes = ",".join(
        create_lfs_working_hours_time_codes(
            start_year=start_year,
            end_year=end_year,
        )
    )

    # 表そのものを特定する基本条件に、
    # 今回取得する年齢階級・就業時間区分・対象年を追加する。
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

    # API固有のレスポンス構造を、このモジュール内で分析用DataFrameへ変換して返す。
    return create_lfs_working_hours_distribution_dataframe(response)


def _create_lfs_employment_type_hours_long_dataframe(
    response: dict[str, Any],
) -> pd.DataFrame:
    """表2-10-1を年齢・雇用形態・就業時間区分のlong形式へ変換する。"""

    try:
        values = response["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
    except (KeyError, TypeError):
        raise ValueError("e-StatレスポンスからVALUEを取得できません。") from None

    employment_mapping = {
        code: name for name, code in LFS_EMPLOYMENT_TYPE_CODES.items()
    }

    age_mapping = {code: name for name, code in LFS_EMPLOYMENT_TYPE_AGE_CODES.items()}

    hours_mapping = {
        code: name for name, code in LFS_EMPLOYMENT_TYPE_HOURS_CODES.items()
    }

    rows: list[dict[str, int | float | str]] = []

    for item in ensure_list(values):
        employment_type = employment_mapping.get(item.get("@cat01"))
        age_group = age_mapping.get(item.get("@cat02"))
        metric = hours_mapping.get(item.get("@cat04"))
        time_code = item.get("@time")

        if (
            employment_type is None
            or age_group is None
            or metric is None
            or time_code is None
        ):
            continue

        time_code = str(time_code)

        if len(time_code) < 4 or not time_code[:4].isdigit():
            raise ValueError(f"不正な時間コードです: {time_code}")

        rows.append(
            {
                "year": int(time_code[:4]),
                "age_group": age_group,
                "employment_type": employment_type,
                "metric": metric,
                "value": item.get("$"),
            }
        )

    result = pd.DataFrame(
        rows,
        columns=[
            "year",
            "age_group",
            "employment_type",
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


def _pivot_lfs_employment_type_hours(
    long_df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態別就業時間データをwide形式へ変換する。"""

    duplicate = long_df.duplicated(
        subset=[
            "year",
            "age_group",
            "employment_type",
            "metric",
        ]
    )

    if duplicate.any():
        raise ValueError(
            "同じ年・年齢階級・雇用形態・就業時間区分のデータが重複しています。"
        )

    result = (
        long_df.pivot(
            index=[
                "year",
                "age_group",
                "employment_type",
            ],
            columns="metric",
            values="value",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    for column in LFS_EMPLOYMENT_TYPE_HOURS_CODES:
        if column not in result.columns:
            result[column] = float("nan")

    return result


def _add_lfs_employment_type_hours_metrics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """雇用形態別就業時間に構成比と時間区分割合を追加する。"""

    result = df.copy()

    persons = result["persons_at_work"].dropna()

    if persons.le(0).any():
        raise ValueError("従業者数は0より大きい必要があります。")

    # 追加の時間区分
    result["hours_30_34"] = result["hours_1_34"] - result["hours_1_29"]

    result["hours_35_48"] = result["hours_35_plus"] - result["hours_49_plus"]

    # 雇用形態別の短時間・長時間割合
    result["hours_1_34_share"] = result["hours_1_34"] / result["persons_at_work"]

    result["hours_49_plus_share"] = result["hours_49_plus"] / result["persons_at_work"]

    # 正規・非正規だけで年齢階級内構成比を計算
    employment_mask = result["employment_type"].isin(["regular", "nonregular"])

    result["employment_share_within_age"] = float("nan")

    totals = (
        result.loc[employment_mask]
        .groupby(
            [
                "year",
                "age_group",
            ]
        )["persons_at_work"]
        .transform(lambda x: x.sum(min_count=1))
    )

    result.loc[
        employment_mask,
        "employment_share_within_age",
    ] = (
        result.loc[
            employment_mask,
            "persons_at_work",
        ]
        / totals
    )

    return result


def create_lfs_employment_type_hours_dataframe(
    response: dict[str, Any],
) -> pd.DataFrame:
    """表2-10-1を雇用形態別就業時間DataFrameへ変換する。"""

    long_df = _create_lfs_employment_type_hours_long_dataframe(response)

    if long_df.empty:
        return pd.DataFrame()

    result = _pivot_lfs_employment_type_hours(long_df)

    result = _add_lfs_employment_type_hours_metrics(result)

    return result.sort_values(
        [
            "year",
            "age_group",
            "employment_type",
        ]
    ).reset_index(drop=True)


def load_lfs_employment_type_hours_from_api(
    app_id: str,
    start_year: int = 2012,
    end_year: int = 2025,
) -> pd.DataFrame:
    """e-Stat APIから表2-10-1を取得する。"""

    if start_year > end_year:
        raise ValueError("開始年は終了年以下である必要があります。")

    employment_codes = ",".join(LFS_EMPLOYMENT_TYPE_CODES.values())

    age_codes = ",".join(LFS_EMPLOYMENT_TYPE_AGE_CODES.values())

    hours_codes = ",".join(LFS_EMPLOYMENT_TYPE_HOURS_CODES.values())

    time_codes = ",".join(
        create_lfs_working_hours_time_codes(
            start_year=start_year,
            end_year=end_year,
        )
    )

    filters = {
        **LFS_EMPLOYMENT_TYPE_HOURS_BASE_FILTERS,
        "cdCat01": employment_codes,
        "cdCat02": age_codes,
        "cdCat04": hours_codes,
        "cdTime": time_codes,
    }

    response = get_stats_data(
        app_id=app_id,
        stats_data_id=LFS_EMPLOYMENT_TYPE_HOURS_STATS_DATA_ID,
        filters=filters,
    )

    return create_lfs_employment_type_hours_dataframe(response)
