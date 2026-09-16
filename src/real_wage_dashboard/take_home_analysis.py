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


def calculate_salary_income_deduction(
    gross_salary_yen: float,
    target_date: str | date | pd.Timestamp,
    deduction_rules: pd.DataFrame,
) -> float:
    """給与収入と適用年から給与所得控除額を計算する。"""

    if gross_salary_yen < 0:
        raise ValueError("給与収入は0以上である必要があります。")

    rules = _select_effective_rules(
        deduction_rules,
        target_date=target_date,
    )

    rules = rules.loc[
        rules["deduction_type"] == "salary_income"
    ].copy()

    if rules.empty:
        raise ValueError(
            "指定日に有効な給与所得控除ルールがありません。"
        )

    lower = pd.to_numeric(
        rules["lower_bound_yen"],
        errors="coerce",
    )
    upper = pd.to_numeric(
        rules["upper_bound_yen"],
        errors="coerce",
    )

    if lower.isna().any():
        raise ValueError(
            "給与所得控除ルールの lower_bound_yen に"
            "不正な値があります。"
        )

    mask = (
        (lower <= gross_salary_yen)
        & (
            upper.isna()
            | (gross_salary_yen <= upper)
        )
    )

    matched = rules.loc[mask].copy()

    if len(matched) != 1:
        raise ValueError(
            "給与所得控除ルールを一意に取得できません。"
            f" gross_salary_yen={gross_salary_yen},"
            f" date={pd.Timestamp(target_date).date()},"
            f" rows={len(matched)}"
        )

    rule = matched.iloc[0]

    fixed_yen = pd.to_numeric(
        pd.Series([rule["fixed_yen"]]),
        errors="coerce",
    ).iloc[0]

    if pd.notna(fixed_yen):
        deduction = float(fixed_yen)

    else:
        rate = pd.to_numeric(
            pd.Series([rule["rate"]]),
            errors="coerce",
        ).iloc[0]

        add_yen = pd.to_numeric(
            pd.Series([rule["add_yen"]]),
            errors="coerce",
        ).iloc[0]

        if pd.isna(rate) or pd.isna(add_yen):
            raise ValueError(
                "給与所得控除ルールに rate / add_yen "
                "または fixed_yen が設定されていません。"
            )

        deduction = (
            gross_salary_yen * float(rate)
            + float(add_yen)
        )

    # 最低保障額が給与収入そのものを上回る場合でも、
    # 給与所得を負にはしない。
    deduction = min(
        deduction,
        gross_salary_yen,
    )

    return float(deduction)


def calculate_salary_income(
    gross_salary_yen: float,
    target_date: str | date | pd.Timestamp,
    deduction_rules: pd.DataFrame,
) -> float:
    """給与収入から給与所得を計算する。"""

    deduction = calculate_salary_income_deduction(
        gross_salary_yen=gross_salary_yen,
        target_date=target_date,
        deduction_rules=deduction_rules,
    )

    return float(
        max(
            gross_salary_yen - deduction,
            0,
        )
    )
