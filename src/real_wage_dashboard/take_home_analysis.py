import math
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


def calculate_basic_deduction(
    total_income_yen: float,
    target_date: str | date | pd.Timestamp,
    deduction_rules: pd.DataFrame,
) -> float:
    """合計所得金額と適用年から所得税の基礎控除額を計算する。"""

    if total_income_yen < 0:
        raise ValueError(
            "合計所得金額は0以上である必要があります。"
        )

    rules = _select_effective_rules(
        deduction_rules,
        target_date=target_date,
    )

    rules = rules.loc[
        rules["deduction_type"] == "basic"
    ].copy()

    if rules.empty:
        raise ValueError(
            "指定日に有効な基礎控除ルールがありません。"
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
            "基礎控除ルールの lower_bound_yen に"
            "不正な値があります。"
        )

    mask = (
        (lower <= total_income_yen)
        & (
            upper.isna()
            | (total_income_yen <= upper)
        )
    )

    matched = rules.loc[mask].copy()

    if len(matched) != 1:
        raise ValueError(
            "基礎控除ルールを一意に取得できません。"
            f" total_income_yen={total_income_yen},"
            f" date={pd.Timestamp(target_date).date()},"
            f" rows={len(matched)}"
        )

    fixed_yen = pd.to_numeric(
        pd.Series([matched.iloc[0]["fixed_yen"]]),
        errors="coerce",
    ).iloc[0]

    if pd.isna(fixed_yen):
        raise ValueError(
            "基礎控除ルールの fixed_yen に"
            "不正な値があります。"
        )

    return float(fixed_yen)


def _floor_to_thousand_yen(
    amount_yen: float,
) -> float:
    """金額の1,000円未満を切り捨てる。"""

    if amount_yen < 0:
        raise ValueError(
            "切り捨て対象金額は0以上である必要があります。"
        )

    return float(
        math.floor(amount_yen / 1_000) * 1_000
    )


def calculate_taxable_income(
    salary_income_yen: float,
    basic_deduction_yen: float,
    social_insurance_deduction_yen: float,
    other_income_deductions_yen: float = 0.0,
) -> float:
    """給与所得と所得控除から所得税の課税所得金額を計算する。"""

    values = {
        "給与所得": salary_income_yen,
        "基礎控除": basic_deduction_yen,
        "社会保険料控除": social_insurance_deduction_yen,
        "その他所得控除": other_income_deductions_yen,
    }

    for name, value in values.items():
        if value < 0:
            raise ValueError(
                f"{name}は0以上である必要があります。"
            )

    total_deductions = (
        basic_deduction_yen
        + social_insurance_deduction_yen
        + other_income_deductions_yen
    )

    taxable_before_rounding = max(
        salary_income_yen - total_deductions,
        0,
    )

    return _floor_to_thousand_yen(
        taxable_before_rounding
    )


def calculate_base_income_tax(
    taxable_income_yen: float,
    target_date: str | date | pd.Timestamp,
    tax_brackets: pd.DataFrame,
) -> float:
    """課税所得に所得税率表を適用し、算出所得税額を計算する。"""

    if taxable_income_yen < 0:
        raise ValueError(
            "課税所得は0以上である必要があります。"
        )

    # 所得税率表を適用する前に1,000円未満を切り捨てる。
    taxable_income = _floor_to_thousand_yen(
        taxable_income_yen
    )

    rules = _select_effective_rules(
        tax_brackets,
        target_date=target_date,
    )

    if rules.empty:
        raise ValueError(
            "指定日に有効な所得税率ルールがありません。"
        )

    lower = pd.to_numeric(
        rules["lower_bound_yen"],
        errors="coerce",
    )

    upper = pd.to_numeric(
        rules["upper_bound_yen"],
        errors="coerce",
    )

    rate = pd.to_numeric(
        rules["marginal_rate"],
        errors="coerce",
    )

    quick_deduction = pd.to_numeric(
        rules["quick_deduction_yen"],
        errors="coerce",
    )

    if lower.isna().any():
        raise ValueError(
            "所得税率ルールの lower_bound_yen に"
            "不正な値があります。"
        )

    if rate.isna().any():
        raise ValueError(
            "所得税率ルールの marginal_rate に"
            "不正な値があります。"
        )

    if quick_deduction.isna().any():
        raise ValueError(
            "所得税率ルールの quick_deduction_yen に"
            "不正な値があります。"
        )

    # 税率表の区間は
    # lower_bound_yen <= taxable_income < upper_bound_yen
    # として扱う。
    #
    # upper_bound_yen が欠損している最終区分は上限なし。
    mask = (
        (lower <= taxable_income)
        & (
            upper.isna()
            | (taxable_income < upper)
        )
    )

    matched = rules.loc[mask].copy()

    if len(matched) != 1:
        raise ValueError(
            "所得税率ルールを一意に取得できません。"
            f" taxable_income_yen={taxable_income},"
            f" date={pd.Timestamp(target_date).date()},"
            f" rows={len(matched)}"
        )

    rule = matched.iloc[0]

    marginal_rate = float(
        pd.to_numeric(rule["marginal_rate"])
    )

    deduction_yen = float(
        pd.to_numeric(rule["quick_deduction_yen"])
    )

    tax = (
        taxable_income * marginal_rate
        - deduction_yen
    )

    return float(
        max(tax, 0)
    )


def calculate_income_tax_after_adjustments(
    base_income_tax_yen: float,
    total_income_yen: float,
    target_date: str | date | pd.Timestamp,
    adjustment_rules: pd.DataFrame,
    dependent_count: int = 0,
    policy_mode: str = "actual_policy",
) -> float:
    """算出所得税額に減税措置を適用する。"""

    if base_income_tax_yen < 0:
        raise ValueError(
            "算出所得税額は0以上である必要があります。"
        )

    if total_income_yen < 0:
        raise ValueError(
            "合計所得金額は0以上である必要があります。"
        )

    if (
        not isinstance(dependent_count, int)
        or dependent_count < 0
    ):
        raise ValueError(
            "扶養人数は0以上の整数である必要があります。"
        )

    if policy_mode not in {
        "actual_policy",
        "structural_policy",
    }:
        raise ValueError(
            "policy_mode は actual_policy または "
            "structural_policy である必要があります。"
        )

    rules = _select_effective_rules(
        adjustment_rules,
        target_date=target_date,
    )

    # 復興特別所得税などの加算措置はここでは扱わない。
    rules = rules.loc[
        rules["operation"].isin(
            [
                "subtract_rate",
                "subtract_fixed",
            ]
        )
    ].copy()

    # structural_policy では、一時的な景気対策等を除外する。
    # 1999～2006年の定率減税のような multi_year_general は残す。
    if policy_mode == "structural_policy":
        rules = rules.loc[
            rules["policy_class"] != "temporary"
        ].copy()

    if rules.empty:
        return float(base_income_tax_yen)

    apply_order = pd.to_numeric(
        rules["apply_order"],
        errors="coerce",
    )

    if apply_order.isna().any():
        raise ValueError(
            "所得税調整ルールの apply_order に"
            "不正な値があります。"
        )

    rules = (
        rules.assign(_apply_order=apply_order)
        .sort_values(
            [
                "_apply_order",
                "policy_id",
            ]
        )
        .reset_index(drop=True)
    )

    tax = float(base_income_tax_yen)

    for _, rule in rules.iterrows():
        total_income_limit = pd.to_numeric(
            pd.Series(
                [rule.get("total_income_limit_yen")]
            ),
            errors="coerce",
        ).iloc[0]

        if (
            pd.notna(total_income_limit)
            and total_income_yen
            > float(total_income_limit)
        ):
            continue

        operation = rule["operation"]

        if operation == "subtract_rate":
            rate = pd.to_numeric(
                pd.Series([rule.get("rate")]),
                errors="coerce",
            ).iloc[0]

            if pd.isna(rate):
                raise ValueError(
                    "subtract_rate ルールに"
                    " rate が設定されていません。"
                )

            reduction = tax * float(rate)

        elif operation == "subtract_fixed":
            fixed_taxpayer = pd.to_numeric(
                pd.Series(
                    [rule.get("fixed_taxpayer_yen")]
                ),
                errors="coerce",
            ).iloc[0]

            fixed_dependent = pd.to_numeric(
                pd.Series(
                    [rule.get("fixed_dependent_yen")]
                ),
                errors="coerce",
            ).iloc[0]

            if pd.isna(fixed_taxpayer):
                raise ValueError(
                    "subtract_fixed ルールに"
                    " fixed_taxpayer_yen が"
                    "設定されていません。"
                )

            if pd.isna(fixed_dependent):
                fixed_dependent = 0.0

            reduction = (
                float(fixed_taxpayer)
                + float(fixed_dependent)
                * dependent_count
            )

        else:
            raise ValueError(
                f"未対応の所得税調整です: {operation}"
            )

        cap_yen = pd.to_numeric(
            pd.Series([rule.get("cap_yen")]),
            errors="coerce",
        ).iloc[0]

        if pd.notna(cap_yen):
            reduction = min(
                reduction,
                float(cap_yen),
            )

        # 減税額が税額そのものを超えることはできない。
        reduction = min(
            reduction,
            tax,
        )

        tax -= reduction

    return float(
        max(tax, 0)
    )


def calculate_reconstruction_special_income_tax(
    income_tax_after_adjustments_yen: float,
    target_date: str | date | pd.Timestamp,
    adjustment_rules: pd.DataFrame,
    policy_mode: str = "actual_policy",
) -> float:
    """減税等適用後の所得税額から復興特別所得税を計算する。"""

    if income_tax_after_adjustments_yen < 0:
        raise ValueError(
            "調整後所得税額は0以上である必要があります。"
        )

    if policy_mode not in {
        "actual_policy",
        "structural_policy",
    }:
        raise ValueError(
            "policy_mode は actual_policy または "
            "structural_policy である必要があります。"
        )

    rules = _select_effective_rules(
        adjustment_rules,
        target_date=target_date,
    )

    rules = rules.loc[
        rules["operation"] == "add_rate"
    ].copy()

    if policy_mode == "structural_policy":
        rules = rules.loc[
            rules["policy_class"] != "temporary"
        ].copy()

    if rules.empty:
        return 0.0

    if len(rules) != 1:
        raise ValueError(
            "復興特別所得税ルールを一意に取得できません。"
            f" date={pd.Timestamp(target_date).date()},"
            f" rows={len(rules)}"
        )

    rule = rules.iloc[0]

    if rule["base"] != "post_credit_income_tax":
        raise ValueError(
            "復興特別所得税の課税標準が"
            "想定と一致しません。"
        )

    rate = pd.to_numeric(
        pd.Series([rule.get("rate")]),
        errors="coerce",
    ).iloc[0]

    if pd.isna(rate):
        raise ValueError(
            "復興特別所得税率が設定されていません。"
        )

    surtax = (
        income_tax_after_adjustments_yen
        * float(rate)
    )

    # 復興特別所得税額は1円未満切捨て。
    return float(
        math.floor(surtax)
    )


def _floor_to_hundred_yen(
    amount_yen: float,
) -> float:
    """金額の100円未満を切り捨てる。"""

    if amount_yen < 0:
        raise ValueError(
            "切り捨て対象金額は0以上である必要があります。"
        )

    return float(
        math.floor(amount_yen / 100) * 100
    )


def calculate_total_income_tax(
    base_income_tax_yen: float,
    total_income_yen: float,
    target_date: str | date | pd.Timestamp,
    adjustment_rules: pd.DataFrame,
    dependent_count: int = 0,
    policy_mode: str = "actual_policy",
) -> float:
    """減税・復興特別所得税を含む年間所得税額を計算する。"""

    income_tax_after_adjustments = (
        calculate_income_tax_after_adjustments(
            base_income_tax_yen=base_income_tax_yen,
            total_income_yen=total_income_yen,
            target_date=target_date,
            adjustment_rules=adjustment_rules,
            dependent_count=dependent_count,
            policy_mode=policy_mode,
        )
    )

    reconstruction_tax = (
        calculate_reconstruction_special_income_tax(
            income_tax_after_adjustments_yen=(
                income_tax_after_adjustments
            ),
            target_date=target_date,
            adjustment_rules=adjustment_rules,
            policy_mode=policy_mode,
        )
    )

    total_tax = (
        income_tax_after_adjustments
        + reconstruction_tax
    )

    return _floor_to_hundred_yen(
        total_tax
    )
