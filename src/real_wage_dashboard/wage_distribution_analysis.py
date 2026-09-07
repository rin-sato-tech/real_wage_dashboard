from __future__ import annotations

import pandas as pd

BASE_YEAR = 2015

QUANTILE_COLUMNS = [
    "p10",
    "p25",
    "p50",
    "p75",
    "p90",
]


def validate_wage_distribution_data(
    df: pd.DataFrame,
) -> None:
    required_columns = {
        "year",
        *QUANTILE_COLUMNS,
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"必要な列がありません: {sorted(missing_columns)}")

    if df.empty:
        raise ValueError("賃金分布データが空です。")

    if df["year"].duplicated().any():
        raise ValueError("year が重複しています。")

    if df[QUANTILE_COLUMNS].isna().any().any():
        raise ValueError("分位値に欠損があります。")

    if (df[QUANTILE_COLUMNS] <= 0).any().any():
        raise ValueError("分位値には正の値が必要です。")

    ordered = (
        (df["p10"] <= df["p25"])
        & (df["p25"] <= df["p50"])
        & (df["p50"] <= df["p75"])
        & (df["p75"] <= df["p90"])
    )

    if not ordered.all():
        raise ValueError("P10 <= P25 <= P50 <= P75 <= P90 を満たさない年があります。")


def build_wage_distribution_analysis(
    df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    validate_wage_distribution_data(df)

    result = df.copy().sort_values("year").reset_index(drop=True)

    base_rows = result[result["year"] == base_year]

    if len(base_rows) != 1:
        raise ValueError(f"基準年 {base_year} が一意に存在しません。")

    base_row = base_rows.iloc[0]

    for column in QUANTILE_COLUMNS:
        result[f"{column}_index"] = result[column] / base_row[column] * 100

    result["p90_p10"] = result["p90"] / result["p10"]
    result["p90_p50"] = result["p90"] / result["p50"]
    result["p50_p10"] = result["p50"] / result["p10"]

    return result


def summarize_wage_distribution_change(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2025,
) -> pd.DataFrame:
    validate_wage_distribution_data(df)

    start_rows = df[df["year"] == start_year]
    end_rows = df[df["year"] == end_year]

    if len(start_rows) != 1:
        raise ValueError(f"開始年 {start_year} が一意に存在しません。")

    if len(end_rows) != 1:
        raise ValueError(f"終了年 {end_year} が一意に存在しません。")

    start_row = start_rows.iloc[0]
    end_row = end_rows.iloc[0]

    rows = []

    for column in QUANTILE_COLUMNS:
        start_value = float(start_row[column])
        end_value = float(end_row[column])

        rows.append(
            {
                "quantile": column.upper(),
                "start_year": start_year,
                "end_year": end_year,
                "start_value": start_value,
                "end_value": end_value,
                "change_rate": (end_value / start_value - 1),
            }
        )

    return pd.DataFrame(rows)


REAL_QUANTILE_COLUMNS = [
    "p10",
    "p25",
    "p50",
    "p75",
    "p90",
]


def add_real_wage_distribution(
    df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    """
    賃金分位をCPIで実質化し、基準年=100の実質指数を追加する。

    cpi_df は少なくとも以下を持つことを想定する。
    - year
    - cpi
    """
    required_cpi_columns = {
        "year",
        "cpi",
    }

    missing = required_cpi_columns - set(cpi_df.columns)

    if missing:
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing)}")

    if cpi_df["year"].duplicated().any():
        raise ValueError("CPIデータの year が重複しています。")

    if cpi_df["cpi"].isna().any():
        raise ValueError("CPIに欠損があります。")

    if (cpi_df["cpi"] <= 0).any():
        raise ValueError("CPIには正の値が必要です。")

    result = df.merge(
        cpi_df[["year", "cpi"]],
        on="year",
        how="left",
        validate="one_to_one",
    )

    if result["cpi"].isna().any():
        missing_years = result.loc[result["cpi"].isna(), "year"].astype(int).tolist()

        raise ValueError(f"CPIが存在しない年があります: {missing_years}")

    for column in REAL_QUANTILE_COLUMNS:
        real_column = f"real_{column}"

        result[real_column] = result[column] / (result["cpi"] / 100)

    base_rows = result[result["year"] == base_year]

    if len(base_rows) != 1:
        raise ValueError(f"基準年 {base_year} が一意に存在しません。")

    base_row = base_rows.iloc[0]

    for column in REAL_QUANTILE_COLUMNS:
        real_column = f"real_{column}"

        result[f"{real_column}_index"] = (
            result[real_column] / base_row[real_column] * 100
        )

    return result


def build_wage_distribution_analysis_by_sex(
    df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    return build_wage_distribution_analysis_by_group(
        df,
        group_columns=["sex"],
        base_year=base_year,
    )


def build_gender_wage_ratio(
    df: pd.DataFrame,
) -> pd.DataFrame:
    required_sexes = {
        "male",
        "female",
    }

    available_sexes = set(df["sex"])

    missing = required_sexes - available_sexes

    if missing:
        raise ValueError(f"必要な性別がありません: {sorted(missing)}")

    male = df[df["sex"] == "male"].set_index("year")

    female = df[df["sex"] == "female"].set_index("year")

    years = male.index.intersection(female.index)

    result = pd.DataFrame(
        {
            "year": years,
        }
    )

    for column in QUANTILE_COLUMNS:
        result[f"female_male_{column}_ratio"] = (
            female.loc[years, column].to_numpy() / male.loc[years, column].to_numpy()
        )

    return result.reset_index(drop=True)


def add_real_wage_distribution_by_group(
    df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    group_columns: list[str],
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    required_columns = {
        "year",
        *group_columns,
        *QUANTILE_COLUMNS,
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"必要な列がありません: {sorted(missing)}")

    required_cpi_columns = {
        "year",
        "cpi",
    }

    missing_cpi = required_cpi_columns - set(cpi_df.columns)

    if missing_cpi:
        raise ValueError(f"CPIデータに必要な列がありません: {sorted(missing_cpi)}")

    if cpi_df["year"].duplicated().any():
        raise ValueError("CPIデータの year が重複しています。")

    if cpi_df["cpi"].isna().any():
        raise ValueError("CPIに欠損があります。")

    if (cpi_df["cpi"] <= 0).any():
        raise ValueError("CPIには正の値が必要です。")

    result = df.merge(
        cpi_df[["year", "cpi"]],
        on="year",
        how="left",
        validate="many_to_one",
    )

    if result["cpi"].isna().any():
        missing_years = (
            result.loc[result["cpi"].isna(), "year"]
            .drop_duplicates()
            .astype(int)
            .tolist()
        )

        raise ValueError(f"CPIが存在しない年があります: {missing_years}")

    for column in QUANTILE_COLUMNS:
        real_column = f"real_{column}"

        result[real_column] = result[column] / (result["cpi"] / 100)

    for group_values, group in result.groupby(
        group_columns,
        dropna=False,
    ):
        base_rows = group[group["year"] == base_year]

        if len(base_rows) != 1:
            raise ValueError(
                f"{group_values}: 基準年 {base_year} が一意に存在しません。"
            )

        base_row = base_rows.iloc[0]

        # group_values を必ずタプルに統一
        if not isinstance(group_values, tuple):
            group_values = (group_values,)

        mask = pd.Series(
            True,
            index=result.index,
        )

        for column_name, value in zip(
            group_columns,
            group_values,
            strict=True,
        ):
            mask &= result[column_name] == value

        for column in QUANTILE_COLUMNS:
            real_column = f"real_{column}"

            result.loc[
                mask,
                f"{real_column}_index",
            ] = result.loc[mask, real_column] / base_row[real_column] * 100

    return result


def build_wage_distribution_analysis_by_employment(
    df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    return build_wage_distribution_analysis_by_group(
        df,
        group_columns=["employment"],
        base_year=base_year,
    )


def build_wage_distribution_analysis_by_company_size(
    df: pd.DataFrame,
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    return build_wage_distribution_analysis_by_group(
        df,
        group_columns=["company_size"],
        base_year=base_year,
    )


def build_wage_distribution_analysis_by_group(
    df: pd.DataFrame,
    group_columns: list[str],
    base_year: int = BASE_YEAR,
) -> pd.DataFrame:
    required_columns = {
        "year",
        *group_columns,
        *QUANTILE_COLUMNS,
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    result = df.copy()

    group_key: str | list[str]

    if len(group_columns) == 1:
        group_key = group_columns[0]
    else:
        group_key = group_columns

    for group_values, group in result.groupby(
        group_key,
        dropna=False,
    ):
        if not isinstance(group_values, tuple):
            group_values = (group_values,)

        base_rows = group[group["year"] == base_year]

        if len(base_rows) != 1:
            raise ValueError(f"{group_values}: base year {base_year} is not unique")

        base_row = base_rows.iloc[0]

        mask = pd.Series(
            True,
            index=result.index,
        )

        for column_name, value in zip(
            group_columns,
            group_values,
            strict=True,
        ):
            mask &= result[column_name] == value

        for column in QUANTILE_COLUMNS:
            result.loc[
                mask,
                f"{column}_index",
            ] = result.loc[mask, column] / base_row[column] * 100

    result["p90_p10"] = result["p90"] / result["p10"]

    result["p90_p50"] = result["p90"] / result["p50"]

    result["p50_p10"] = result["p50"] / result["p10"]

    return result
