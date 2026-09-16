from datetime import date

import pandas as pd


def _select_effective_rules(
    df: pd.DataFrame,
    target_date: str | date | pd.Timestamp,
) -> pd.DataFrame:
    """指定日に有効な制度ルールだけを抽出する。"""

    required_columns = {
        "effective_from",
        "effective_to",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"制度期間の選択に必要な列がありません: {sorted(missing)}"
        )

    target = pd.Timestamp(target_date)

    effective_from = pd.to_datetime(
        df["effective_from"],
        errors="coerce",
    )
    effective_to = pd.to_datetime(
        df["effective_to"],
        errors="coerce",
    )

    if effective_from.isna().any():
        raise ValueError("effective_from に不正な日付があります。")

    mask = (
        (effective_from <= target)
        & (
            effective_to.isna()
            | (target <= effective_to)
        )
    )

    return df.loc[mask].copy().reset_index(drop=True)


def _select_assessment_year_rules(
    df: pd.DataFrame,
    assessment_year: int,
) -> pd.DataFrame:
    """指定された賦課年度に有効な住民税ルールだけを抽出する。"""

    required_columns = {
        "assessment_year_from",
        "assessment_year_to",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"賦課年度の選択に必要な列がありません: {sorted(missing)}"
        )

    year_from = pd.to_numeric(
        df["assessment_year_from"],
        errors="coerce",
    )
    year_to = pd.to_numeric(
        df["assessment_year_to"],
        errors="coerce",
    )

    if year_from.isna().any():
        raise ValueError(
            "assessment_year_from に不正な年度があります。"
        )

    mask = (
        (year_from <= assessment_year)
        & (
            year_to.isna()
            | (assessment_year <= year_to)
        )
    )

    return df.loc[mask].copy().reset_index(drop=True)


def _select_single_effective_rule(
    df: pd.DataFrame,
    target_date: str | date | pd.Timestamp,
    filters: dict[str, object] | None = None,
) -> pd.Series:
    """指定日時点で条件に一致する制度ルールを1行取得する。"""

    selected = _select_effective_rules(
        df,
        target_date=target_date,
    )

    if filters:
        for column, value in filters.items():
            if column not in selected.columns:
                raise ValueError(
                    f"フィルタ対象列がありません: {column}"
                )

            selected = selected.loc[
                selected[column] == value
            ]

    if len(selected) != 1:
        raise ValueError(
            "制度ルールを一意に取得できません。"
            f" date={pd.Timestamp(target_date).date()},"
            f" filters={filters},"
            f" rows={len(selected)}"
        )

    return selected.iloc[0]


def _select_single_assessment_year_rule(
    df: pd.DataFrame,
    assessment_year: int,
    filters: dict[str, object] | None = None,
) -> pd.Series:
    """指定賦課年度で条件に一致する制度ルールを1行取得する。"""

    selected = _select_assessment_year_rules(
        df,
        assessment_year=assessment_year,
    )

    if filters:
        for column, value in filters.items():
            if column not in selected.columns:
                raise ValueError(
                    f"フィルタ対象列がありません: {column}"
                )

            selected = selected.loc[
                selected[column] == value
            ]

    if len(selected) != 1:
        raise ValueError(
            "住民税ルールを一意に取得できません。"
            f" assessment_year={assessment_year},"
            f" filters={filters},"
            f" rows={len(selected)}"
        )

    return selected.iloc[0]
