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


def calculate_employment_insurance(
    wage_yen: float,
    target_date: str | date | pd.Timestamp,
    employment_insurance_rates: pd.DataFrame,
    business_type: str = "general",
) -> float:
    """賃金額と適用日時点の本人負担率から雇用保険料を計算する。"""

    if wage_yen < 0:
        raise ValueError(
            "雇用保険の対象賃金は0以上である必要があります。"
        )

    rule = _select_single_effective_rule(
        employment_insurance_rates,
        target_date=target_date,
        filters={
            "business_type": business_type,
        },
    )

    employee_rate = pd.to_numeric(
        pd.Series([rule["employee_rate"]]),
        errors="coerce",
    ).iloc[0]

    if pd.isna(employee_rate):
        raise ValueError(
            "雇用保険ルールの employee_rate に"
            "不正な値があります。"
        )

    if employee_rate < 0:
        raise ValueError(
            "雇用保険の本人負担率は0以上である必要があります。"
        )

    return float(
        wage_yen * float(employee_rate)
    )


def calculate_annual_employment_insurance(
    monthly_wages: pd.DataFrame,
    employment_insurance_rates: pd.DataFrame,
    business_type: str = "general",
) -> float:
    """月次賃金から年間の雇用保険本人負担額を計算する。"""

    required_columns = {
        "date",
        "cash_earnings_yen",
    }

    missing = required_columns - set(monthly_wages.columns)

    if missing:
        raise ValueError(
            "年間雇用保険料の計算に必要な列がありません: "
            f"{sorted(missing)}"
        )

    if monthly_wages.empty:
        raise ValueError(
            "月次賃金データが空です。"
        )

    wages = monthly_wages.copy()

    wages["date"] = pd.to_datetime(
        wages["date"],
        errors="coerce",
    )

    if wages["date"].isna().any():
        raise ValueError(
            "月次賃金データの date に不正な値があります。"
        )

    wages["cash_earnings_yen"] = pd.to_numeric(
        wages["cash_earnings_yen"],
        errors="coerce",
    )

    if wages["cash_earnings_yen"].isna().any():
        raise ValueError(
            "cash_earnings_yen に不正な値があります。"
        )

    if (wages["cash_earnings_yen"] < 0).any():
        raise ValueError(
            "雇用保険の対象賃金は0以上である必要があります。"
        )

    premiums = [
        calculate_employment_insurance(
            wage_yen=float(row.cash_earnings_yen),
            target_date=row.date,
            employment_insurance_rates=(
                employment_insurance_rates
            ),
            business_type=business_type,
        )
        for row in wages.itertuples(index=False)
    ]

    return float(sum(premiums))


def _select_standard_monthly_remuneration_rule(
    remuneration_yen: float,
    target_date: str | date | pd.Timestamp,
    standard_monthly_rules: pd.DataFrame,
) -> pd.Series:
    """報酬月額と適用日から標準報酬月額の等級を取得する。"""

    if remuneration_yen < 0:
        raise ValueError(
            "報酬月額は0以上である必要があります。"
        )

    rules = _select_effective_rules(
        standard_monthly_rules,
        target_date=target_date,
    )

    if rules.empty:
        raise ValueError(
            "指定日に有効な標準報酬月額ルールがありません。"
        )

    lower = pd.to_numeric(
        rules["remuneration_lower_yen"],
        errors="coerce",
    )

    upper = pd.to_numeric(
        rules["remuneration_upper_yen"],
        errors="coerce",
    )

    standard_monthly = pd.to_numeric(
        rules["standard_monthly_yen"],
        errors="coerce",
    )

    if standard_monthly.isna().any():
        raise ValueError(
            "standard_monthly_yen に不正な値があります。"
        )

    # 下限なしの最下位等級、
    # 上限なしの最上位等級も扱う。
    #
    # 等級境界は
    # lower <= remuneration < upper
    # とする。
    mask = (
        (
            lower.isna()
            | (lower <= remuneration_yen)
        )
        & (
            upper.isna()
            | (remuneration_yen < upper)
        )
    )

    matched = rules.loc[mask].copy()

    if len(matched) != 1:
        raise ValueError(
            "標準報酬月額の等級を一意に取得できません。"
            f" remuneration_yen={remuneration_yen},"
            f" date={pd.Timestamp(target_date).date()},"
            f" rows={len(matched)}"
        )

    return matched.iloc[0]


def calculate_standard_monthly_remuneration(
    remuneration_yen: float,
    target_date: str | date | pd.Timestamp,
    standard_monthly_rules: pd.DataFrame,
) -> float:
    """実際の報酬月額から標準報酬月額を取得する。"""

    rule = _select_standard_monthly_remuneration_rule(
        remuneration_yen=remuneration_yen,
        target_date=target_date,
        standard_monthly_rules=standard_monthly_rules,
    )

    standard_monthly_yen = pd.to_numeric(
        pd.Series(
            [rule["standard_monthly_yen"]]
        ),
        errors="coerce",
    ).iloc[0]

    if pd.isna(standard_monthly_yen):
        raise ValueError(
            "standard_monthly_yen に不正な値があります。"
        )

    return float(standard_monthly_yen)


def _select_pension_rate_rule(
    target_date: str | date | pd.Timestamp,
    pension_rates: pd.DataFrame,
    sex: str = "male",
) -> pd.Series:
    """適用日時点の厚生年金保険料率ルールを取得する。"""

    if sex not in {
        "male",
        "female",
    }:
        raise ValueError(
            "sex は male または female である必要があります。"
        )

    rules = _select_effective_rules(
        pension_rates,
        target_date=target_date,
    )

    if rules.empty:
        raise ValueError(
            "指定日に有効な厚生年金保険料率がありません。"
        )

    if "insured_category" not in rules.columns:
        raise ValueError(
            "厚生年金保険料率データに "
            "insured_category 列がありません。"
        )

    # 男女別料率が設定されている時期は
    # general_male / general_female を使用する。
    sex_category = f"general_{sex}"

    sex_rules = rules.loc[
        rules["insured_category"] == sex_category
    ]

    if not sex_rules.empty:
        rules = sex_rules
    else:
        # 男女共通化後は general を使用する。
        rules = rules.loc[
            rules["insured_category"] == "general"
        ]

    if len(rules) != 1:
        raise ValueError(
            "厚生年金保険料率を一意に取得できません。"
            f" date={pd.Timestamp(target_date).date()},"
            f" sex={sex},"
            f" rows={len(rules)}"
        )

    return rules.iloc[0]


def calculate_monthly_pension_contribution(
    remuneration_yen: float,
    target_date: str | date | pd.Timestamp,
    standard_monthly_rules: pd.DataFrame,
    pension_rates: pd.DataFrame,
    sex: str = "male",
) -> float:
    """月額報酬から厚生年金の月額本人負担額を計算する。"""

    if remuneration_yen < 0:
        raise ValueError(
            "報酬月額は0以上である必要があります。"
        )

    standard_monthly_yen = (
        calculate_standard_monthly_remuneration(
            remuneration_yen=remuneration_yen,
            target_date=target_date,
            standard_monthly_rules=standard_monthly_rules,
        )
    )

    rule = _select_pension_rate_rule(
        target_date=target_date,
        pension_rates=pension_rates,
        sex=sex,
    )

    total_rate = pd.to_numeric(
        pd.Series(
            [rule["regular_total_rate"]]
        ),
        errors="coerce",
    ).iloc[0]

    employee_share = pd.to_numeric(
        pd.Series(
            [rule["employee_share"]]
        ),
        errors="coerce",
    ).iloc[0]

    if pd.isna(total_rate):
        raise ValueError(
            "厚生年金の regular_total_rate に"
            "不正な値があります。"
        )

    if pd.isna(employee_share):
        raise ValueError(
            "厚生年金の employee_share に"
            "不正な値があります。"
        )

    if total_rate < 0:
        raise ValueError(
            "厚生年金保険料率は0以上である必要があります。"
        )

    if not 0 <= employee_share <= 1:
        raise ValueError(
            "厚生年金の本人負担割合は"
            "0以上1以下である必要があります。"
        )

    contribution = (
        standard_monthly_yen
        * float(total_rate)
        * float(employee_share)
    )

    # float演算に伴う 14299.999999999998 のような
    # 微小な数値誤差を除去する。
    return float(
        round(
            contribution,
            10,
        )
    )


def calculate_annual_regular_pension_contribution(
    monthly_remuneration: pd.DataFrame,
    standard_monthly_rules: pd.DataFrame,
    pension_rates: pd.DataFrame,
    sex: str = "male",
) -> float:
    """月次報酬から厚生年金の年間本人負担額（月給部分）を計算する。"""

    required_columns = {
        "date",
        "regular_pay_yen",
    }

    missing = required_columns - set(
        monthly_remuneration.columns
    )

    if missing:
        raise ValueError(
            "年間厚生年金保険料の計算に必要な列がありません: "
            f"{sorted(missing)}"
        )

    if monthly_remuneration.empty:
        raise ValueError(
            "月次報酬データが空です。"
        )

    data = monthly_remuneration.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    if data["date"].isna().any():
        raise ValueError(
            "月次報酬データの date に不正な値があります。"
        )

    data["regular_pay_yen"] = pd.to_numeric(
        data["regular_pay_yen"],
        errors="coerce",
    )

    if data["regular_pay_yen"].isna().any():
        raise ValueError(
            "regular_pay_yen に不正な値があります。"
        )

    if (data["regular_pay_yen"] < 0).any():
        raise ValueError(
            "報酬月額は0以上である必要があります。"
        )

    contributions = [
        calculate_monthly_pension_contribution(
            remuneration_yen=float(
                row.regular_pay_yen
            ),
            target_date=row.date,
            standard_monthly_rules=(
                standard_monthly_rules
            ),
            pension_rates=pension_rates,
            sex=sex,
        )
        for row in data.itertuples(
            index=False
        )
    ]

    return float(
        sum(contributions)
    )


def calculate_pension_bonus_base(
    bonus_yen: float,
    target_date: str | date | pd.Timestamp,
    bonus_rules: pd.DataFrame,
) -> float:
    """賞与額から厚生年金保険料の算定基礎額を計算する。"""

    if bonus_yen < 0:
        raise ValueError(
            "賞与額は0以上である必要があります。"
        )

    rules = _select_effective_rules(
        bonus_rules,
        target_date=target_date,
    )

    rules = rules.loc[
        rules["scheme"] == "pension"
    ].copy()

    if len(rules) != 1:
        raise ValueError(
            "厚生年金の賞与ルールを一意に取得できません。"
            f" date={pd.Timestamp(target_date).date()},"
            f" rows={len(rules)}"
        )

    rule = rules.iloc[0]

    rounding_unit = pd.to_numeric(
        pd.Series([rule["rounding_unit_yen"]]),
        errors="coerce",
    ).iloc[0]

    if (
        pd.isna(rounding_unit)
        or rounding_unit <= 0
    ):
        raise ValueError(
            "賞与ルールの rounding_unit_yen に"
            "不正な値があります。"
        )

    bonus_base = (
        math.floor(
            bonus_yen / float(rounding_unit)
        )
        * float(rounding_unit)
    )

    cap_type = str(rule["cap_type"])

    if cap_type == "none":
        return float(bonus_base)

    if cap_type in {
        "per_payment",
        "per_month",
    }:
        cap_yen = pd.to_numeric(
            pd.Series([rule["cap_yen"]]),
            errors="coerce",
        ).iloc[0]

        if pd.isna(cap_yen):
            raise ValueError(
                "賞与上限額が設定されていません。"
            )

        return float(
            min(
                bonus_base,
                float(cap_yen),
            )
        )

    raise ValueError(
        f"未対応の賞与上限方式です: {cap_type}"
    )


def calculate_pension_bonus_contribution(
    bonus_yen: float,
    target_date: str | date | pd.Timestamp,
    pension_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
    sex: str = "male",
) -> float:
    """1回の賞与にかかる厚生年金本人負担額を計算する。"""

    if bonus_yen < 0:
        raise ValueError(
            "賞与額は0以上である必要があります。"
        )

    rate_rule = _select_pension_rate_rule(
        target_date=target_date,
        pension_rates=pension_rates,
        sex=sex,
    )

    bonus_total_rate = pd.to_numeric(
        pd.Series(
            [rate_rule["bonus_total_rate"]]
        ),
        errors="coerce",
    ).iloc[0]

    employee_share = pd.to_numeric(
        pd.Series(
            [rate_rule["employee_share"]]
        ),
        errors="coerce",
    ).iloc[0]

    if pd.isna(bonus_total_rate):
        raise ValueError(
            "厚生年金の bonus_total_rate に"
            "不正な値があります。"
        )

    if pd.isna(employee_share):
        raise ValueError(
            "厚生年金の employee_share に"
            "不正な値があります。"
        )

    if bonus_total_rate < 0:
        raise ValueError(
            "厚生年金の賞与保険料率は"
            "0以上である必要があります。"
        )

    if not 0 <= employee_share <= 1:
        raise ValueError(
            "厚生年金の本人負担割合は"
            "0以上1以下である必要があります。"
        )

    # 1995年3月以前は賞与保険料なし。
    if bonus_total_rate == 0:
        return 0.0

    bonus_base = calculate_pension_bonus_base(
        bonus_yen=bonus_yen,
        target_date=target_date,
        bonus_rules=bonus_rules,
    )

    contribution = (
        bonus_base
        * float(bonus_total_rate)
        * float(employee_share)
    )

    return float(
        round(
            contribution,
            10,
        )
    )


def calculate_annual_pension_bonus_contribution(
    bonus_payments: pd.DataFrame,
    pension_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
    sex: str = "male",
) -> float:
    """賞与支給データから年間の厚生年金本人負担額を計算する。"""

    required_columns = {
        "date",
        "bonus_yen",
    }

    missing = required_columns - set(
        bonus_payments.columns
    )

    if missing:
        raise ValueError(
            "年間賞与厚生年金の計算に必要な列がありません: "
            f"{sorted(missing)}"
        )

    if bonus_payments.empty:
        return 0.0

    data = bonus_payments.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    if data["date"].isna().any():
        raise ValueError(
            "賞与データの date に不正な値があります。"
        )

    data["bonus_yen"] = pd.to_numeric(
        data["bonus_yen"],
        errors="coerce",
    )

    if data["bonus_yen"].isna().any():
        raise ValueError(
            "bonus_yen に不正な値があります。"
        )

    if (data["bonus_yen"] < 0).any():
        raise ValueError(
            "賞与額は0以上である必要があります。"
        )

    # 標準賞与額の上限は同一月の賞与合計に対して適用されるため、
    # 同じ月に複数回支給されている場合は先に月単位へ集約する。
    data["month"] = data["date"].dt.to_period("M")

    monthly_bonus = (
        data.groupby(
            "month",
            as_index=False,
        )
        .agg(
            bonus_yen=("bonus_yen", "sum"),
        )
    )

    monthly_bonus["date"] = (
        monthly_bonus["month"]
        .dt.to_timestamp()
    )

    contributions = [
        calculate_pension_bonus_contribution(
            bonus_yen=float(row.bonus_yen),
            target_date=row.date,
            pension_rates=pension_rates,
            bonus_rules=bonus_rules,
            sex=sex,
        )
        for row in monthly_bonus.itertuples(
            index=False
        )
    ]

    return float(
        round(
            sum(contributions),
            10,
        )
    )


def calculate_annual_pension_contribution(
    monthly_remuneration: pd.DataFrame,
    bonus_payments: pd.DataFrame,
    standard_monthly_rules: pd.DataFrame,
    pension_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
    sex: str = "male",
) -> dict[str, float]:
    """月給・賞与を合わせた年間厚生年金本人負担額を計算する。"""

    regular_contribution = (
        calculate_annual_regular_pension_contribution(
            monthly_remuneration=monthly_remuneration,
            standard_monthly_rules=standard_monthly_rules,
            pension_rates=pension_rates,
            sex=sex,
        )
    )

    bonus_contribution = (
        calculate_annual_pension_bonus_contribution(
            bonus_payments=bonus_payments,
            pension_rates=pension_rates,
            bonus_rules=bonus_rules,
            sex=sex,
        )
    )

    total_contribution = (
        regular_contribution
        + bonus_contribution
    )

    return {
        "regular_pension_yen": float(
            round(
                regular_contribution,
                10,
            )
        ),
        "bonus_pension_yen": float(
            round(
                bonus_contribution,
                10,
            )
        ),
        "total_pension_yen": float(
            round(
                total_contribution,
                10,
            )
        ),
    }


def create_semiannual_bonus_payments(
    year: int,
    annual_bonus_yen: float,
) -> pd.DataFrame:
    """年間賞与を6月・12月に均等支給する標準モデルを作成する。"""

    if annual_bonus_yen < 0:
        raise ValueError(
            "年間賞与額は0以上である必要があります。"
        )

    half_bonus = annual_bonus_yen / 2

    return pd.DataFrame(
        {
            "date": [
                pd.Timestamp(
                    year=year,
                    month=6,
                    day=1,
                ),
                pd.Timestamp(
                    year=year,
                    month=12,
                    day=1,
                ),
            ],
            "bonus_yen": [
                half_bonus,
                half_bonus,
            ],
        }
    )


def _select_health_insurance_rate_rule(
    target_date: str | date | pd.Timestamp,
    health_insurance_rates: pd.DataFrame,
) -> pd.Series:
    """適用日時点の健康保険料率ルールを取得する。"""

    rules = _select_effective_rules(
        health_insurance_rates,
        target_date=target_date,
    )

    if len(rules) != 1:
        raise ValueError(
            "健康保険料率を一意に取得できません。"
            f" date={pd.Timestamp(target_date).date()},"
            f" rows={len(rules)}"
        )

    return rules.iloc[0]


def calculate_monthly_health_insurance_contribution(
    remuneration_yen: float,
    target_date: str | date | pd.Timestamp,
    standard_monthly_rules: pd.DataFrame,
    health_insurance_rates: pd.DataFrame,
) -> float:
    """月額報酬から健康保険の月額本人負担額を計算する。"""

    if remuneration_yen < 0:
        raise ValueError(
            "報酬月額は0以上である必要があります。"
        )

    standard_monthly_yen = (
        calculate_standard_monthly_remuneration(
            remuneration_yen=remuneration_yen,
            target_date=target_date,
            standard_monthly_rules=standard_monthly_rules,
        )
    )

    rule = _select_health_insurance_rate_rule(
        target_date=target_date,
        health_insurance_rates=health_insurance_rates,
    )

    total_rate = pd.to_numeric(
        pd.Series(
            [rule["regular_total_rate"]]
        ),
        errors="coerce",
    ).iloc[0]

    employee_share = pd.to_numeric(
        pd.Series(
            [rule["employee_share"]]
        ),
        errors="coerce",
    ).iloc[0]

    if pd.isna(total_rate):
        raise ValueError(
            "健康保険の regular_total_rate に"
            "不正な値があります。"
        )

    if pd.isna(employee_share):
        raise ValueError(
            "健康保険の employee_share に"
            "不正な値があります。"
        )

    if total_rate < 0:
        raise ValueError(
            "健康保険料率は0以上である必要があります。"
        )

    if not 0 <= employee_share <= 1:
        raise ValueError(
            "健康保険の本人負担割合は"
            "0以上1以下である必要があります。"
        )

    contribution = (
        standard_monthly_yen
        * float(total_rate)
        * float(employee_share)
    )

    # float演算由来の微小誤差のみ除去する。
    return float(
        round(
            contribution,
            10,
        )
    )


def calculate_annual_regular_health_insurance_contribution(
    monthly_remuneration: pd.DataFrame,
    standard_monthly_rules: pd.DataFrame,
    health_insurance_rates: pd.DataFrame,
) -> float:
    """月次報酬から年間健康保険本人負担額（月給部分）を計算する。"""

    required_columns = {
        "date",
        "regular_pay_yen",
    }

    missing = required_columns - set(
        monthly_remuneration.columns
    )

    if missing:
        raise ValueError(
            "年間健康保険料の計算に必要な列がありません: "
            f"{sorted(missing)}"
        )

    if monthly_remuneration.empty:
        raise ValueError(
            "月次報酬データが空です。"
        )

    data = monthly_remuneration.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    if data["date"].isna().any():
        raise ValueError(
            "月次報酬データの date に不正な値があります。"
        )

    data["regular_pay_yen"] = pd.to_numeric(
        data["regular_pay_yen"],
        errors="coerce",
    )

    if data["regular_pay_yen"].isna().any():
        raise ValueError(
            "regular_pay_yen に不正な値があります。"
        )

    if (data["regular_pay_yen"] < 0).any():
        raise ValueError(
            "報酬月額は0以上である必要があります。"
        )

    contributions = [
        calculate_monthly_health_insurance_contribution(
            remuneration_yen=float(
                row.regular_pay_yen
            ),
            target_date=row.date,
            standard_monthly_rules=(
                standard_monthly_rules
            ),
            health_insurance_rates=(
                health_insurance_rates
            ),
        )
        for row in data.itertuples(
            index=False
        )
    ]

    return float(
        round(
            sum(contributions),
            10,
        )
    )


def calculate_health_bonus_base(
    bonus_yen: float,
    target_date: str | date | pd.Timestamp,
    bonus_rules: pd.DataFrame,
    prior_fiscal_year_standard_bonus_yen: float = 0.0,
) -> float:
    """健康保険の賞与保険料算定基礎額を計算する。"""

    if bonus_yen < 0:
        raise ValueError(
            "賞与額は0以上である必要があります。"
        )

    if prior_fiscal_year_standard_bonus_yen < 0:
        raise ValueError(
            "年度累計標準賞与額は0以上である必要があります。"
        )

    rules = _select_effective_rules(
        bonus_rules,
        target_date=target_date,
    )

    rules = rules.loc[
        rules["scheme"] == "health"
    ].copy()

    if len(rules) != 1:
        raise ValueError(
            "健康保険の賞与ルールを一意に取得できません。"
            f" date={pd.Timestamp(target_date).date()},"
            f" rows={len(rules)}"
        )

    rule = rules.iloc[0]

    rounding_unit = pd.to_numeric(
        pd.Series([rule["rounding_unit_yen"]]),
        errors="coerce",
    ).iloc[0]

    if (
        pd.isna(rounding_unit)
        or rounding_unit <= 0
    ):
        raise ValueError(
            "健康保険賞与ルールの rounding_unit_yen に"
            "不正な値があります。"
        )

    bonus_base = (
        math.floor(
            bonus_yen / float(rounding_unit)
        )
        * float(rounding_unit)
    )

    cap_type = str(
        rule["cap_type"]
    )

    if cap_type == "none":
        return float(bonus_base)

    cap_yen = pd.to_numeric(
        pd.Series([rule["cap_yen"]]),
        errors="coerce",
    ).iloc[0]

    if pd.isna(cap_yen):
        raise ValueError(
            "健康保険の賞与上限額が設定されていません。"
        )

    cap_yen = float(cap_yen)

    if cap_type == "per_payment":
        return float(
            min(
                bonus_base,
                cap_yen,
            )
        )

    if cap_type == "fiscal_year":
        remaining_cap = max(
            cap_yen
            - prior_fiscal_year_standard_bonus_yen,
            0.0,
        )

        return float(
            min(
                bonus_base,
                remaining_cap,
            )
        )

    raise ValueError(
        f"未対応の健康保険賞与上限方式です: {cap_type}"
    )


def calculate_health_bonus_contribution(
    bonus_yen: float,
    target_date: str | date | pd.Timestamp,
    health_insurance_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
    prior_fiscal_year_standard_bonus_yen: float = 0.0,
) -> float:
    """賞与にかかる健康保険本人負担額を計算する。"""

    if bonus_yen < 0:
        raise ValueError(
            "賞与額は0以上である必要があります。"
        )

    rule = _select_health_insurance_rate_rule(
        target_date=target_date,
        health_insurance_rates=health_insurance_rates,
    )

    bonus_base = calculate_health_bonus_base(
        bonus_yen=bonus_yen,
        target_date=target_date,
        bonus_rules=bonus_rules,
        prior_fiscal_year_standard_bonus_yen=(
            prior_fiscal_year_standard_bonus_yen
        ),
    )

    target = pd.Timestamp(
        target_date
    )

    # 総報酬制導入前：
    # 月給保険料率とは別に賞与特別保険料の本人率を直接適用。
    if target < pd.Timestamp("2003-04-01"):
        bonus_employee_rate = pd.to_numeric(
            pd.Series(
                [rule["bonus_employee_rate"]]
            ),
            errors="coerce",
        ).iloc[0]

        if pd.isna(bonus_employee_rate):
            raise ValueError(
                "総報酬制導入前の"
                " bonus_employee_rate がありません。"
            )

        if bonus_employee_rate < 0:
            raise ValueError(
                "健康保険の賞与本人負担率は"
                "0以上である必要があります。"
            )

        contribution = (
            bonus_base
            * float(bonus_employee_rate)
        )

    else:
        total_rate = pd.to_numeric(
            pd.Series(
                [rule["regular_total_rate"]]
            ),
            errors="coerce",
        ).iloc[0]

        employee_share = pd.to_numeric(
            pd.Series(
                [rule["employee_share"]]
            ),
            errors="coerce",
        ).iloc[0]

        if pd.isna(total_rate):
            raise ValueError(
                "健康保険料率に不正な値があります。"
            )

        if pd.isna(employee_share):
            raise ValueError(
                "健康保険本人負担割合に不正な値があります。"
            )

        contribution = (
            bonus_base
            * float(total_rate)
            * float(employee_share)
        )

    return float(
        round(
            contribution,
            10,
        )
    )


def _get_fiscal_year(
    target_date: str | date | pd.Timestamp,
) -> int:
    """4月始まりの年度を返す。"""

    target = pd.Timestamp(
        target_date
    )

    if target.month >= 4:
        return target.year

    return target.year - 1


def calculate_annual_health_bonus_contribution(
    bonus_payments: pd.DataFrame,
    health_insurance_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
) -> float:
    """年間の賞与にかかる健康保険本人負担額を計算する。

    標準労働者モデルでは賞与を6月・12月に支給するため、
    暦年データ内で健康保険の年度累計上限を完結して計算できる。
    1～3月にも賞与がある一般ケースでは、前暦年4～12月分を含む
    当該年度全体の賞与履歴を渡す必要がある。
    """

    required_columns = {
        "date",
        "bonus_yen",
    }

    missing = required_columns - set(
        bonus_payments.columns
    )

    if missing:
        raise ValueError(
            "年間健康保険賞与計算に必要な列がありません: "
            f"{sorted(missing)}"
        )

    if bonus_payments.empty:
        return 0.0

    data = bonus_payments.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    if data["date"].isna().any():
        raise ValueError(
            "賞与データの date に不正な値があります。"
        )

    data["bonus_yen"] = pd.to_numeric(
        data["bonus_yen"],
        errors="coerce",
    )

    if data["bonus_yen"].isna().any():
        raise ValueError(
            "bonus_yen に不正な値があります。"
        )

    if (data["bonus_yen"] < 0).any():
        raise ValueError(
            "賞与額は0以上である必要があります。"
        )

    data = data.sort_values(
        "date"
    ).reset_index(drop=True)

    fiscal_year_cumulative: dict[int, float] = {}
    contributions: list[float] = []

    for row in data.itertuples(
        index=False
    ):
        fiscal_year = _get_fiscal_year(
            row.date
        )

        prior = fiscal_year_cumulative.get(
            fiscal_year,
            0.0,
        )

        bonus_base = calculate_health_bonus_base(
            bonus_yen=float(row.bonus_yen),
            target_date=row.date,
            bonus_rules=bonus_rules,
            prior_fiscal_year_standard_bonus_yen=prior,
        )

        contribution = (
            calculate_health_bonus_contribution(
                bonus_yen=float(row.bonus_yen),
                target_date=row.date,
                health_insurance_rates=(
                    health_insurance_rates
                ),
                bonus_rules=bonus_rules,
                prior_fiscal_year_standard_bonus_yen=prior,
            )
        )

        contributions.append(
            contribution
        )

        fiscal_year_cumulative[
            fiscal_year
        ] = (
            prior
            + bonus_base
        )

    return float(
        round(
            sum(contributions),
            10,
        )
    )


def calculate_annual_health_insurance_contribution(
    monthly_remuneration: pd.DataFrame,
    bonus_payments: pd.DataFrame,
    standard_monthly_rules: pd.DataFrame,
    health_insurance_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
) -> dict[str, float]:
    """月給・賞与を合わせた年間健康保険本人負担額を計算する。"""

    regular_contribution = (
        calculate_annual_regular_health_insurance_contribution(
            monthly_remuneration=monthly_remuneration,
            standard_monthly_rules=standard_monthly_rules,
            health_insurance_rates=health_insurance_rates,
        )
    )

    bonus_contribution = (
        calculate_annual_health_bonus_contribution(
            bonus_payments=bonus_payments,
            health_insurance_rates=health_insurance_rates,
            bonus_rules=bonus_rules,
        )
    )

    total_contribution = (
        regular_contribution
        + bonus_contribution
    )

    return {
        "regular_health_yen": float(
            round(
                regular_contribution,
                10,
            )
        ),
        "bonus_health_yen": float(
            round(
                bonus_contribution,
                10,
            )
        ),
        "total_health_yen": float(
            round(
                total_contribution,
                10,
            )
        ),
    }


def _create_employment_insurance_wage_payments(
    monthly_remuneration: pd.DataFrame,
    bonus_payments: pd.DataFrame,
) -> pd.DataFrame:
    """月給・賞与から雇用保険料計算用の賃金支払データを作成する。"""

    required_monthly_columns = {
        "date",
        "regular_pay_yen",
    }

    missing_monthly = (
        required_monthly_columns
        - set(monthly_remuneration.columns)
    )

    if missing_monthly:
        raise ValueError(
            "雇用保険用月次賃金データに"
            "必要な列がありません: "
            f"{sorted(missing_monthly)}"
        )

    if monthly_remuneration.empty:
        raise ValueError(
            "月次報酬データが空です。"
        )

    monthly = monthly_remuneration.copy()

    monthly["date"] = pd.to_datetime(
        monthly["date"],
        errors="coerce",
    )

    if monthly["date"].isna().any():
        raise ValueError(
            "月次報酬データの date に不正な値があります。"
        )

    monthly["regular_pay_yen"] = pd.to_numeric(
        monthly["regular_pay_yen"],
        errors="coerce",
    )

    if monthly["regular_pay_yen"].isna().any():
        raise ValueError(
            "regular_pay_yen に不正な値があります。"
        )

    if (
        monthly["regular_pay_yen"] < 0
    ).any():
        raise ValueError(
            "報酬月額は0以上である必要があります。"
        )

    regular_wages = (
        monthly[
            [
                "date",
                "regular_pay_yen",
            ]
        ]
        .rename(
            columns={
                "regular_pay_yen": (
                    "cash_earnings_yen"
                ),
            }
        )
    )

    required_bonus_columns = {
        "date",
        "bonus_yen",
    }

    missing_bonus = (
        required_bonus_columns
        - set(bonus_payments.columns)
    )

    if missing_bonus:
        raise ValueError(
            "雇用保険用賞与データに"
            "必要な列がありません: "
            f"{sorted(missing_bonus)}"
        )

    if bonus_payments.empty:
        return (
            regular_wages
            .sort_values("date")
            .reset_index(drop=True)
        )

    bonuses = bonus_payments.copy()

    bonuses["date"] = pd.to_datetime(
        bonuses["date"],
        errors="coerce",
    )

    if bonuses["date"].isna().any():
        raise ValueError(
            "賞与データの date に不正な値があります。"
        )

    bonuses["bonus_yen"] = pd.to_numeric(
        bonuses["bonus_yen"],
        errors="coerce",
    )

    if bonuses["bonus_yen"].isna().any():
        raise ValueError(
            "bonus_yen に不正な値があります。"
        )

    if (
        bonuses["bonus_yen"] < 0
    ).any():
        raise ValueError(
            "賞与額は0以上である必要があります。"
        )

    bonus_wages = (
        bonuses[
            [
                "date",
                "bonus_yen",
            ]
        ]
        .rename(
            columns={
                "bonus_yen": (
                    "cash_earnings_yen"
                ),
            }
        )
    )

    result = pd.concat(
        [
            regular_wages,
            bonus_wages,
        ],
        ignore_index=True,
    )

    return (
        result
        .sort_values("date")
        .reset_index(drop=True)
    )


def calculate_annual_social_insurance(
    monthly_remuneration: pd.DataFrame,
    bonus_payments: pd.DataFrame,
    pension_standard_monthly_rules: pd.DataFrame,
    pension_rates: pd.DataFrame,
    health_standard_monthly_rules: pd.DataFrame,
    health_insurance_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
    employment_insurance_rates: pd.DataFrame,
    sex: str = "male",
    business_type: str = "general",
) -> dict[str, float]:
    """標準労働者の年間社会保険本人負担額を計算する。"""

    pension = calculate_annual_pension_contribution(
        monthly_remuneration=monthly_remuneration,
        bonus_payments=bonus_payments,
        standard_monthly_rules=(
            pension_standard_monthly_rules
        ),
        pension_rates=pension_rates,
        bonus_rules=bonus_rules,
        sex=sex,
    )

    health = (
        calculate_annual_health_insurance_contribution(
            monthly_remuneration=monthly_remuneration,
            bonus_payments=bonus_payments,
            standard_monthly_rules=(
                health_standard_monthly_rules
            ),
            health_insurance_rates=(
                health_insurance_rates
            ),
            bonus_rules=bonus_rules,
        )
    )

    employment_wages = (
        _create_employment_insurance_wage_payments(
            monthly_remuneration=monthly_remuneration,
            bonus_payments=bonus_payments,
        )
    )

    employment = (
        calculate_annual_employment_insurance(
            monthly_wages=employment_wages,
            employment_insurance_rates=(
                employment_insurance_rates
            ),
            business_type=business_type,
        )
    )

    total = (
        pension["total_pension_yen"]
        + health["total_health_yen"]
        + employment
    )

    return {
        "regular_pension_yen": float(
            round(
                pension["regular_pension_yen"],
                10,
            )
        ),
        "bonus_pension_yen": float(
            round(
                pension["bonus_pension_yen"],
                10,
            )
        ),
        "total_pension_yen": float(
            round(
                pension["total_pension_yen"],
                10,
            )
        ),
        "regular_health_yen": float(
            round(
                health["regular_health_yen"],
                10,
            )
        ),
        "bonus_health_yen": float(
            round(
                health["bonus_health_yen"],
                10,
            )
        ),
        "total_health_yen": float(
            round(
                health["total_health_yen"],
                10,
            )
        ),
        "employment_insurance_yen": float(
            round(
                employment,
                10,
            )
        ),
        "total_social_insurance_yen": float(
            round(
                total,
                10,
            )
        ),
    }


def create_constant_monthly_remuneration(
    year: int,
    monthly_regular_pay_yen: float,
) -> pd.DataFrame:
    """年間を通じて一定の月例賃金を受け取る標準モデルを作成する。"""

    if not isinstance(year, int):
        raise ValueError(
            "year は整数である必要があります。"
        )

    if monthly_regular_pay_yen < 0:
        raise ValueError(
            "月例賃金は0以上である必要があります。"
        )

    return pd.DataFrame(
        {
            "date": pd.date_range(
                start=f"{year}-01-01",
                periods=12,
                freq="MS",
            ),
            "regular_pay_yen": [
                float(monthly_regular_pay_yen)
            ] * 12,
        }
    )


def calculate_standard_worker_income_tax(
    year: int,
    monthly_regular_pay_yen: float,
    annual_bonus_yen: float,
    income_tax_deductions: pd.DataFrame,
    income_tax_brackets: pd.DataFrame,
    income_tax_adjustments: pd.DataFrame,
    pension_standard_monthly_rules: pd.DataFrame,
    pension_rates: pd.DataFrame,
    health_standard_monthly_rules: pd.DataFrame,
    health_insurance_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
    employment_insurance_rates: pd.DataFrame,
    sex: str = "male",
    business_type: str = "general",
    dependent_count: int = 0,
    other_income_deductions_yen: float = 0.0,
    policy_mode: str = "actual_policy",
) -> dict[str, float]:
    """標準労働者モデルの年間所得税までの計算を行う。

    想定する所得は給与所得のみ。
    住民税はこの関数には含めない。
    """

    if annual_bonus_yen < 0:
        raise ValueError(
            "年間賞与額は0以上である必要があります。"
        )

    if other_income_deductions_yen < 0:
        raise ValueError(
            "その他所得控除は0以上である必要があります。"
        )

    monthly_remuneration = (
        create_constant_monthly_remuneration(
            year=year,
            monthly_regular_pay_yen=(
                monthly_regular_pay_yen
            ),
        )
    )

    bonus_payments = (
        create_semiannual_bonus_payments(
            year=year,
            annual_bonus_yen=annual_bonus_yen,
        )
    )

    annual_regular_pay_yen = float(
        monthly_remuneration[
            "regular_pay_yen"
        ].sum()
    )

    gross_salary_yen = (
        annual_regular_pay_yen
        + float(annual_bonus_yen)
    )

    social_insurance = (
        calculate_annual_social_insurance(
            monthly_remuneration=monthly_remuneration,
            bonus_payments=bonus_payments,
            pension_standard_monthly_rules=(
                pension_standard_monthly_rules
            ),
            pension_rates=pension_rates,
            health_standard_monthly_rules=(
                health_standard_monthly_rules
            ),
            health_insurance_rates=(
                health_insurance_rates
            ),
            bonus_rules=bonus_rules,
            employment_insurance_rates=(
                employment_insurance_rates
            ),
            sex=sex,
            business_type=business_type,
        )
    )

    social_insurance_yen = (
        social_insurance[
            "total_social_insurance_yen"
        ]
    )

    # 所得税は暦年単位なので、
    # 当該年末時点でその年の税制ルールを選択する。
    tax_date = pd.Timestamp(
        year=year,
        month=12,
        day=31,
    )

    salary_income_deduction_yen = (
        calculate_salary_income_deduction(
            gross_salary_yen=gross_salary_yen,
            target_date=tax_date,
            deduction_rules=income_tax_deductions,
        )
    )

    salary_income_yen = max(
        gross_salary_yen
        - salary_income_deduction_yen,
        0.0,
    )

    basic_deduction_yen = (
        calculate_basic_deduction(
            total_income_yen=salary_income_yen,
            target_date=tax_date,
            deduction_rules=income_tax_deductions,
        )
    )

    taxable_income_yen = (
        calculate_taxable_income(
            salary_income_yen=salary_income_yen,
            basic_deduction_yen=(
                basic_deduction_yen
            ),
            social_insurance_deduction_yen=(
                social_insurance_yen
            ),
            other_income_deductions_yen=(
                other_income_deductions_yen
            ),
        )
    )

    base_income_tax_yen = (
        calculate_base_income_tax(
            taxable_income_yen=taxable_income_yen,
            target_date=tax_date,
            tax_brackets=income_tax_brackets,
        )
    )

    income_tax_yen = (
        calculate_total_income_tax(
            base_income_tax_yen=base_income_tax_yen,
            total_income_yen=salary_income_yen,
            target_date=tax_date,
            adjustment_rules=income_tax_adjustments,
            dependent_count=dependent_count,
            policy_mode=policy_mode,
        )
    )

    after_income_tax_and_social_insurance_yen = (
        gross_salary_yen
        - social_insurance_yen
        - income_tax_yen
    )

    return {
        "annual_regular_pay_yen": float(
            annual_regular_pay_yen
        ),
        "annual_bonus_yen": float(
            annual_bonus_yen
        ),
        "gross_salary_yen": float(
            gross_salary_yen
        ),
        "pension_yen": float(
            social_insurance[
                "total_pension_yen"
            ]
        ),
        "health_insurance_yen": float(
            social_insurance[
                "total_health_yen"
            ]
        ),
        "employment_insurance_yen": float(
            social_insurance[
                "employment_insurance_yen"
            ]
        ),
        "social_insurance_yen": float(
            social_insurance_yen
        ),
        "salary_income_deduction_yen": float(
            salary_income_deduction_yen
        ),
        "salary_income_yen": float(
            salary_income_yen
        ),
        "basic_deduction_yen": float(
            basic_deduction_yen
        ),
        "other_income_deductions_yen": float(
            other_income_deductions_yen
        ),
        "taxable_income_yen": float(
            taxable_income_yen
        ),
        "base_income_tax_yen": float(
            base_income_tax_yen
        ),
        "income_tax_yen": float(
            income_tax_yen
        ),
        "after_income_tax_and_social_insurance_yen": float(
            after_income_tax_and_social_insurance_yen
        ),
    }


def calculate_resident_basic_deduction(
    total_income_yen: float,
    assessment_year: int,
    deduction_rules: pd.DataFrame,
) -> float:
    """合計所得金額から住民税の基礎控除額を取得する。"""

    if total_income_yen < 0:
        raise ValueError(
            "合計所得金額は0以上である必要があります。"
        )

    rules = _select_assessment_year_rules(
        deduction_rules,
        assessment_year=assessment_year,
    )

    rules = rules.loc[
        rules["deduction_type"] == "basic"
    ].copy()

    if rules.empty:
        raise ValueError(
            "指定課税年度に有効な"
            "住民税基礎控除ルールがありません。"
            f" assessment_year={assessment_year}"
        )

    lower = pd.to_numeric(
        rules["lower_bound_yen"],
        errors="coerce",
    )

    upper = pd.to_numeric(
        rules["upper_bound_yen"],
        errors="coerce",
    )

    fixed = pd.to_numeric(
        rules["fixed_yen"],
        errors="coerce",
    )

    if lower.isna().any():
        raise ValueError(
            "住民税基礎控除ルールの "
            "lower_bound_yen に不正な値があります。"
        )

    if fixed.isna().any():
        raise ValueError(
            "住民税基礎控除ルールの "
            "fixed_yen に不正な値があります。"
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
            "住民税基礎控除ルールを一意に取得できません。"
            f" total_income_yen={total_income_yen},"
            f" assessment_year={assessment_year},"
            f" rows={len(matched)}"
        )

    return float(
        pd.to_numeric(
            matched.iloc[0]["fixed_yen"]
        )
    )


def calculate_resident_taxable_income(
    salary_income_yen: float,
    social_insurance_deduction_yen: float,
    assessment_year: int,
    resident_tax_deductions: pd.DataFrame,
    other_income_deductions_yen: float = 0.0,
) -> dict[str, float]:
    """給与所得から住民税の課税所得を計算する。"""

    if salary_income_yen < 0:
        raise ValueError(
            "給与所得は0以上である必要があります。"
        )

    if social_insurance_deduction_yen < 0:
        raise ValueError(
            "社会保険料控除は0以上である必要があります。"
        )

    if other_income_deductions_yen < 0:
        raise ValueError(
            "その他所得控除は0以上である必要があります。"
        )

    basic_deduction_yen = (
        calculate_resident_basic_deduction(
            total_income_yen=salary_income_yen,
            assessment_year=assessment_year,
            deduction_rules=resident_tax_deductions,
        )
    )

    taxable_income_yen = calculate_taxable_income(
        salary_income_yen=salary_income_yen,
        basic_deduction_yen=basic_deduction_yen,
        social_insurance_deduction_yen=(
            social_insurance_deduction_yen
        ),
        other_income_deductions_yen=(
            other_income_deductions_yen
        ),
    )

    return {
        "resident_basic_deduction_yen": float(
            basic_deduction_yen
        ),
        "resident_taxable_income_yen": float(
            taxable_income_yen
        ),
    }


def calculate_base_resident_income_levy(
    taxable_income_yen: float,
    assessment_year: int,
    income_rate_rules: pd.DataFrame,
) -> float:
    """住民税の課税所得から控除前所得割額を計算する。"""

    if taxable_income_yen < 0:
        raise ValueError(
            "住民税課税所得は0以上である必要があります。"
        )

    taxable_income = _floor_to_thousand_yen(
        taxable_income_yen
    )

    rules = _select_assessment_year_rules(
        income_rate_rules,
        assessment_year=assessment_year,
    )

    if rules.empty:
        raise ValueError(
            "指定課税年度に有効な"
            "住民税所得割率ルールがありません。"
            f" assessment_year={assessment_year}"
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
            "住民税所得割率ルールの "
            "lower_bound_yen に不正な値があります。"
        )

    if rate.isna().any():
        raise ValueError(
            "住民税所得割率ルールの "
            "marginal_rate に不正な値があります。"
        )

    if quick_deduction.isna().any():
        raise ValueError(
            "住民税所得割率ルールの "
            "quick_deduction_yen に不正な値があります。"
        )

    # 税率表は下限以上・上限未満として扱う。
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
            "住民税所得割率ルールを一意に取得できません。"
            f" taxable_income_yen={taxable_income},"
            f" assessment_year={assessment_year},"
            f" rows={len(matched)}"
        )

    rule = matched.iloc[0]

    marginal_rate = float(
        pd.to_numeric(
            rule["marginal_rate"]
        )
    )

    deduction_yen = float(
        pd.to_numeric(
            rule["quick_deduction_yen"]
        )
    )

    tax = (
        taxable_income
        * marginal_rate
        - deduction_yen
    )

    return float(
        max(
            round(tax, 10),
            0.0,
        )
    )


def calculate_resident_adjustment_credit(
    taxable_income_yen: float,
    total_income_yen: float,
    assessment_year: int,
    adjustment_rules: pd.DataFrame,
    human_deduction_difference_yen: float = 50_000.0,
) -> float:
    """住民税の調整控除額を計算する。"""

    if taxable_income_yen < 0:
        raise ValueError(
            "住民税課税所得は0以上である必要があります。"
        )

    if total_income_yen < 0:
        raise ValueError(
            "合計所得金額は0以上である必要があります。"
        )

    if human_deduction_difference_yen < 0:
        raise ValueError(
            "人的控除額の差は0以上である必要があります。"
        )

    rules = _select_assessment_year_rules(
        adjustment_rules,
        assessment_year=assessment_year,
    )

    rules = rules.loc[
        rules["operation"] == "adjustment_credit"
    ].copy()

    if rules.empty:
        return 0.0

    if len(rules) != 1:
        raise ValueError(
            "住民税の調整控除ルールを"
            "一意に取得できません。"
            f" assessment_year={assessment_year},"
            f" rows={len(rules)}"
        )

    rule = rules.iloc[0]

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
        return 0.0

    if taxable_income_yen <= 2_000_000:
        credit_base = min(
            human_deduction_difference_yen,
            taxable_income_yen,
        )

    else:
        credit_base = max(
            human_deduction_difference_yen
            - (
                taxable_income_yen
                - 2_000_000
            ),
            50_000.0,
        )

    adjustment_credit = (
        credit_base
        * 0.05
    )

    return float(
        round(
            adjustment_credit,
            10,
        )
    )


def calculate_resident_income_levy_after_adjustments(
    base_income_levy_yen: float,
    taxable_income_yen: float,
    total_income_yen: float,
    assessment_year: int,
    adjustment_rules: pd.DataFrame,
    dependent_count: int = 0,
    human_deduction_difference_yen: float = 50_000.0,
    policy_mode: str = "actual_policy",
) -> dict[str, float]:
    """住民税所得割に調整控除・減税措置を適用する。"""

    if base_income_levy_yen < 0:
        raise ValueError(
            "控除前住民税所得割額は"
            "0以上である必要があります。"
        )

    if taxable_income_yen < 0:
        raise ValueError(
            "住民税課税所得は0以上である必要があります。"
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

    # まず調整控除。
    adjustment_credit_yen = (
        calculate_resident_adjustment_credit(
            taxable_income_yen=taxable_income_yen,
            total_income_yen=total_income_yen,
            assessment_year=assessment_year,
            adjustment_rules=adjustment_rules,
            human_deduction_difference_yen=(
                human_deduction_difference_yen
            ),
        )
    )

    levy = max(
        base_income_levy_yen
        - adjustment_credit_yen,
        0.0,
    )

    rules = _select_assessment_year_rules(
        adjustment_rules,
        assessment_year=assessment_year,
    )

    rules = rules.loc[
        rules["operation"].isin(
            [
                "subtract_rate",
                "subtract_fixed",
            ]
        )
    ].copy()

    if policy_mode == "structural_policy":
        rules = rules.loc[
            rules["policy_class"] != "temporary"
        ].copy()

    total_other_reduction = 0.0

    for _, rule in rules.sort_values(
        "policy_id"
    ).iterrows():
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
                pd.Series(
                    [rule.get("rate")]
                ),
                errors="coerce",
            ).iloc[0]

            if pd.isna(rate):
                raise ValueError(
                    "住民税 subtract_rate ルールに"
                    " rate が設定されていません。"
                )

            reduction = (
                levy
                * float(rate)
            )

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
                    "住民税 subtract_fixed ルールに"
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
                f"未対応の住民税調整です: {operation}"
            )

        cap_yen = pd.to_numeric(
            pd.Series(
                [rule.get("cap_yen")]
            ),
            errors="coerce",
        ).iloc[0]

        if pd.notna(cap_yen):
            reduction = min(
                reduction,
                float(cap_yen),
            )

        reduction = min(
            reduction,
            levy,
        )

        levy -= reduction
        total_other_reduction += reduction

    return {
        "base_resident_income_levy_yen": float(
            round(
                base_income_levy_yen,
                10,
            )
        ),
        "resident_adjustment_credit_yen": float(
            round(
                adjustment_credit_yen,
                10,
            )
        ),
        "resident_other_reduction_yen": float(
            round(
                total_other_reduction,
                10,
            )
        ),
        "resident_income_levy_after_adjustments_yen": float(
            round(
                max(levy, 0.0),
                10,
            )
        ),
    }


def calculate_resident_per_capita_tax(
    assessment_year: int,
    per_capita_rules: pd.DataFrame,
    municipality_band: str | None = None,
) -> dict[str, float]:
    """住民税均等割と森林環境税を取得する。"""

    rules = _select_assessment_year_rules(
        per_capita_rules,
        assessment_year=assessment_year,
    )

    if municipality_band is not None:
        rules = rules.loc[
            rules["municipality_band"]
            == municipality_band
        ].copy()

    if len(rules) != 1:
        raise ValueError(
            "住民税均等割ルールを一意に取得できません。"
            f" assessment_year={assessment_year},"
            f" municipality_band={municipality_band},"
            f" rows={len(rules)}"
        )

    rule = rules.iloc[0]

    prefectural_yen = pd.to_numeric(
        pd.Series(
            [rule["prefectural_yen"]]
        ),
        errors="coerce",
    ).iloc[0]

    municipal_yen = pd.to_numeric(
        pd.Series(
            [rule["municipal_yen"]]
        ),
        errors="coerce",
    ).iloc[0]

    forest_environment_tax_yen = pd.to_numeric(
        pd.Series(
            [rule["forest_environment_tax_yen"]]
        ),
        errors="coerce",
    ).iloc[0]

    values = {
        "prefectural_yen": prefectural_yen,
        "municipal_yen": municipal_yen,
        "forest_environment_tax_yen": (
            forest_environment_tax_yen
        ),
    }

    for name, value in values.items():
        if pd.isna(value):
            raise ValueError(
                f"{name} に不正な値があります。"
            )

        if value < 0:
            raise ValueError(
                f"{name} は0以上である必要があります。"
            )

    resident_per_capita_yen = (
        float(prefectural_yen)
        + float(municipal_yen)
    )

    return {
        "prefectural_per_capita_yen": float(
            prefectural_yen
        ),
        "municipal_per_capita_yen": float(
            municipal_yen
        ),
        "resident_per_capita_yen": float(
            resident_per_capita_yen
        ),
        "forest_environment_tax_yen": float(
            forest_environment_tax_yen
        ),
    }


def calculate_total_resident_tax(
    income_levy_after_adjustments_yen: float,
    assessment_year: int,
    per_capita_rules: pd.DataFrame,
    municipality_band: str | None = None,
) -> dict[str, float]:
    """所得割・均等割・森林環境税から年間住民税額を計算する。"""

    if income_levy_after_adjustments_yen < 0:
        raise ValueError(
            "調整後住民税所得割額は"
            "0以上である必要があります。"
        )

    income_levy_yen = _floor_to_hundred_yen(
        income_levy_after_adjustments_yen
    )

    per_capita = calculate_resident_per_capita_tax(
        assessment_year=assessment_year,
        per_capita_rules=per_capita_rules,
        municipality_band=municipality_band,
    )

    total_resident_tax_yen = (
        income_levy_yen
        + per_capita["resident_per_capita_yen"]
        + per_capita["forest_environment_tax_yen"]
    )

    return {
        "resident_income_levy_yen": float(
            income_levy_yen
        ),
        "prefectural_per_capita_yen": (
            per_capita[
                "prefectural_per_capita_yen"
            ]
        ),
        "municipal_per_capita_yen": (
            per_capita[
                "municipal_per_capita_yen"
            ]
        ),
        "resident_per_capita_yen": (
            per_capita[
                "resident_per_capita_yen"
            ]
        ),
        "forest_environment_tax_yen": (
            per_capita[
                "forest_environment_tax_yen"
            ]
        ),
        "total_resident_tax_yen": float(
            total_resident_tax_yen
        ),
    }


def calculate_standard_worker_take_home(
    year: int,
    monthly_regular_pay_yen: float,
    annual_bonus_yen: float,
    income_tax_deductions: pd.DataFrame,
    income_tax_brackets: pd.DataFrame,
    income_tax_adjustments: pd.DataFrame,
    pension_standard_monthly_rules: pd.DataFrame,
    pension_rates: pd.DataFrame,
    health_standard_monthly_rules: pd.DataFrame,
    health_insurance_rates: pd.DataFrame,
    bonus_rules: pd.DataFrame,
    employment_insurance_rates: pd.DataFrame,
    resident_tax_deductions: pd.DataFrame,
    resident_tax_income_rates: pd.DataFrame,
    resident_tax_adjustments: pd.DataFrame,
    resident_tax_per_capita: pd.DataFrame,
    sex: str = "male",
    business_type: str = "general",
    dependent_count: int = 0,
    other_income_deductions_yen: float = 0.0,
    resident_other_income_deductions_yen: float = 0.0,
    human_deduction_difference_yen: float = 50_000.0,
    municipality_band: str | None = None,
    policy_mode: str = "actual_policy",
) -> dict[str, float | int]:
    """標準労働者モデルの名目手取り賃金を計算する。

    住民税は所得年対応ベースとし、
    所得年 year に対して assessment_year = year + 1
    の制度を適用する。

    これは実際の年内キャッシュフローではなく、
    各所得年に対応する税・社会保険負担を比較するための
    分析上の対応付けである。
    """

    # ----------------------------------------
    # 1. 所得税・社会保険料
    # ----------------------------------------

    income_tax_result = calculate_standard_worker_income_tax(
        year=year,
        monthly_regular_pay_yen=monthly_regular_pay_yen,
        annual_bonus_yen=annual_bonus_yen,
        income_tax_deductions=income_tax_deductions,
        income_tax_brackets=income_tax_brackets,
        income_tax_adjustments=income_tax_adjustments,
        pension_standard_monthly_rules=(
            pension_standard_monthly_rules
        ),
        pension_rates=pension_rates,
        health_standard_monthly_rules=(
            health_standard_monthly_rules
        ),
        health_insurance_rates=(
            health_insurance_rates
        ),
        bonus_rules=bonus_rules,
        employment_insurance_rates=(
            employment_insurance_rates
        ),
        sex=sex,
        business_type=business_type,
        dependent_count=dependent_count,
        other_income_deductions_yen=(
            other_income_deductions_yen
        ),
        policy_mode=policy_mode,
    )

    # ----------------------------------------
    # 2. 住民税
    #
    # 所得年 t に対応する住民税として、
    # 翌年度 t+1 の制度を適用する。
    # ----------------------------------------

    assessment_year = year + 1

    resident_tax_result = (
        calculate_standard_worker_resident_tax(
            salary_income_yen=(
                income_tax_result[
                    "salary_income_yen"
                ]
            ),
            social_insurance_deduction_yen=(
                income_tax_result[
                    "social_insurance_yen"
                ]
            ),
            assessment_year=assessment_year,
            resident_tax_deductions=(
                resident_tax_deductions
            ),
            resident_tax_income_rates=(
                resident_tax_income_rates
            ),
            resident_tax_adjustments=(
                resident_tax_adjustments
            ),
            resident_tax_per_capita=(
                resident_tax_per_capita
            ),
            dependent_count=dependent_count,
            other_income_deductions_yen=(
                resident_other_income_deductions_yen
            ),
            human_deduction_difference_yen=(
                human_deduction_difference_yen
            ),
            municipality_band=(
                municipality_band
            ),
            policy_mode=policy_mode,
        )
    )

    # ----------------------------------------
    # 3. 総控除額
    # ----------------------------------------

    gross_salary_yen = float(
        income_tax_result[
            "gross_salary_yen"
        ]
    )

    social_insurance_yen = float(
        income_tax_result[
            "social_insurance_yen"
        ]
    )

    income_tax_yen = float(
        income_tax_result[
            "income_tax_yen"
        ]
    )

    resident_tax_yen = float(
        resident_tax_result[
            "resident_tax_yen"
        ]
    )

    total_deductions_yen = (
        social_insurance_yen
        + income_tax_yen
        + resident_tax_yen
    )

    # ----------------------------------------
    # 4. 名目手取り
    # ----------------------------------------

    nominal_take_home_yen = (
        gross_salary_yen
        - total_deductions_yen
    )

    # ----------------------------------------
    # 5. 実効負担率・手取り率
    # ----------------------------------------

    if gross_salary_yen > 0:
        effective_burden_rate = (
            total_deductions_yen
            / gross_salary_yen
        )

        take_home_rate = (
            nominal_take_home_yen
            / gross_salary_yen
        )

    else:
        effective_burden_rate = 0.0
        take_home_rate = 0.0

    # ----------------------------------------
    # 6. 結果
    # ----------------------------------------

    return {
        **income_tax_result,
        **resident_tax_result,
        "total_deductions_yen": float(
            round(
                total_deductions_yen,
                10,
            )
        ),
        "nominal_take_home_yen": float(
            round(
                nominal_take_home_yen,
                10,
            )
        ),
        "effective_burden_rate": float(
            effective_burden_rate
        ),
        "take_home_rate": float(
            take_home_rate
        ),
    }


def calculate_take_home_time_series(
    annual_wage_df: pd.DataFrame,
    rule_tables: dict[str, pd.DataFrame],
    start_year: int = 1990,
    end_year: int = 2025,
    sex: str = "male",
    business_type: str = "general",
    dependent_count: int = 0,
    other_income_deductions_yen: float = 0.0,
    resident_other_income_deductions_yen: float = 0.0,
    human_deduction_difference_yen: float = 50_000.0,
    municipality_band: str | None = None,
    policy_mode: str = "actual_policy",
    timing: str = "income_year",
) -> pd.DataFrame:
    """年平均賃金から標準労働者の手取り時系列を作成する。

    Parameters
    ----------
    timing:
        "income_year"
            所得年 t の所得に対して、
            assessment_year = t + 1 の住民税を対応させる。
            制度負担を所得年に帰属させる主分析用系列。

        "cash_flow"
            年 t の給与・所得税・社会保険料に対して、
            前年 t - 1 の所得を基礎として
            assessment_year = t に課される住民税を対応させる。

            これは年税額ベースのキャッシュフロー近似であり、
            6月～翌5月の月別特別徴収そのものは再現しない。

    Notes
    -----
    annual_wage_df は毎月勤労統計の年平均値を想定し、
    regular_earnings を月例賃金、
    special_earnings × 12 を年間賞与として使用する。
    """

    # ----------------------------------------
    # 1. 入力検証
    # ----------------------------------------

    required_columns = {
        "year",
        "total_cash_earnings",
        "regular_earnings",
        "special_earnings",
    }

    missing = (
        required_columns
        - set(annual_wage_df.columns)
    )

    if missing:
        raise ValueError(
            "手取り時系列の作成に必要な"
            "賃金列がありません: "
            f"{sorted(missing)}"
        )

    required_rule_tables = {
        "income_tax_deductions",
        "income_tax_brackets",
        "income_tax_adjustments",
        "pension_standard_monthly",
        "pension_rates",
        "health_standard_monthly",
        "health_insurance_rates",
        "social_insurance_bonus_rules",
        "employment_insurance_rates",
        "resident_tax_deductions",
        "resident_tax_income_rates",
        "resident_tax_adjustments",
        "resident_tax_per_capita",
    }

    missing_rules = (
        required_rule_tables
        - set(rule_tables)
    )

    if missing_rules:
        raise ValueError(
            "手取り計算に必要な制度表がありません: "
            f"{sorted(missing_rules)}"
        )

    if start_year > end_year:
        raise ValueError(
            "start_year は end_year 以下で"
            "ある必要があります。"
        )

    if timing not in {
        "income_year",
        "cash_flow",
    }:
        raise ValueError(
            "timing は income_year または "
            "cash_flow である必要があります。"
        )

    # ----------------------------------------
    # 2. 年平均賃金を正規化
    # ----------------------------------------

    data = annual_wage_df.copy()

    numeric_columns = [
        "year",
        "total_cash_earnings",
        "regular_earnings",
        "special_earnings",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    if data[numeric_columns].isna().any().any():
        raise ValueError(
            "年平均賃金データに不正な数値があります。"
        )

    if (
        data[
            [
                "total_cash_earnings",
                "regular_earnings",
                "special_earnings",
            ]
        ]
        < 0
    ).any().any():
        raise ValueError(
            "賃金額は0以上である必要があります。"
        )

    if (
        data["year"]
        != data["year"].astype(int)
    ).any():
        raise ValueError(
            "year は整数である必要があります。"
        )

    data["year"] = (
        data["year"]
        .astype(int)
    )

    if data["year"].duplicated().any():
        duplicated = (
            data.loc[
                data["year"].duplicated(
                    keep=False
                ),
                "year",
            ]
            .sort_values()
            .unique()
            .tolist()
        )

        raise ValueError(
            "年平均賃金データに重複年があります: "
            f"{duplicated}"
        )

    # ----------------------------------------
    # 3. 計算に必要な期間を決定
    #
    # cash_flow の場合、
    # start_year の住民税計算に
    # start_year - 1 の所得が必要。
    # ----------------------------------------

    if timing == "income_year":
        required_start_year = start_year
    else:
        required_start_year = start_year - 1

    required_years = set(
        range(
            required_start_year,
            end_year + 1,
        )
    )

    actual_years = set(
        data["year"].tolist()
    )

    missing_years = sorted(
        required_years
        - actual_years
    )

    if missing_years:
        raise ValueError(
            "手取り時系列に必要な年が"
            "欠けています: "
            f"{missing_years}"
        )

    calculation_data = data.loc[
        data["year"].between(
            required_start_year,
            end_year,
        )
    ].copy()

    calculation_data = (
        calculation_data
        .sort_values("year")
        .reset_index(drop=True)
    )

    # ----------------------------------------
    # 4. 給与構成恒等式
    # ----------------------------------------

    identity_diff = (
        calculation_data[
            "total_cash_earnings"
        ]
        - (
            calculation_data[
                "regular_earnings"
            ]
            + calculation_data[
                "special_earnings"
            ]
        )
    )

    invalid_identity = (
        identity_diff.abs() > 1e-6
    )

    if invalid_identity.any():
        bad = calculation_data.loc[
            invalid_identity,
            [
                "year",
                "total_cash_earnings",
                "regular_earnings",
                "special_earnings",
            ],
        ].copy()

        raise ValueError(
            "給与構成の恒等式が成立しません: "
            f"{bad.to_dict('records')}"
        )

    # ----------------------------------------
    # 5. 各所得年について
    #    所得税・社会保険料を先に計算
    #
    # cash_flow では前年所得を住民税計算に
    # 使用するため、2段階計算とする。
    # ----------------------------------------

    core_results: dict[
        int,
        dict[str, float | int],
    ] = {}

    wage_inputs: dict[
        int,
        dict[str, float],
    ] = {}

    for row in calculation_data.itertuples(
        index=False
    ):
        year = int(row.year)

        monthly_total_cash_earnings_yen = float(
            row.total_cash_earnings
        )

        monthly_regular_pay_yen = float(
            row.regular_earnings
        )

        monthly_special_earnings_yen = float(
            row.special_earnings
        )

        annual_bonus_yen = (
            monthly_special_earnings_yen
            * 12
        )

        expected_gross_yen = (
            monthly_total_cash_earnings_yen
            * 12
        )

        core = calculate_standard_worker_income_tax(
            year=year,
            monthly_regular_pay_yen=(
                monthly_regular_pay_yen
            ),
            annual_bonus_yen=(
                annual_bonus_yen
            ),
            income_tax_deductions=(
                rule_tables[
                    "income_tax_deductions"
                ]
            ),
            income_tax_brackets=(
                rule_tables[
                    "income_tax_brackets"
                ]
            ),
            income_tax_adjustments=(
                rule_tables[
                    "income_tax_adjustments"
                ]
            ),
            pension_standard_monthly_rules=(
                rule_tables[
                    "pension_standard_monthly"
                ]
            ),
            pension_rates=(
                rule_tables[
                    "pension_rates"
                ]
            ),
            health_standard_monthly_rules=(
                rule_tables[
                    "health_standard_monthly"
                ]
            ),
            health_insurance_rates=(
                rule_tables[
                    "health_insurance_rates"
                ]
            ),
            bonus_rules=(
                rule_tables[
                    "social_insurance_bonus_rules"
                ]
            ),
            employment_insurance_rates=(
                rule_tables[
                    "employment_insurance_rates"
                ]
            ),
            sex=sex,
            business_type=business_type,
            dependent_count=dependent_count,
            other_income_deductions_yen=(
                other_income_deductions_yen
            ),
            policy_mode=policy_mode,
        )

        if not math.isclose(
            float(
                core["gross_salary_yen"]
            ),
            expected_gross_yen,
            rel_tol=0.0,
            abs_tol=1e-6,
        ):
            raise ValueError(
                "年間額面賃金の恒等式が"
                "成立しません。"
                f" year={year},"
                f" expected={expected_gross_yen},"
                f" calculated="
                f"{core['gross_salary_yen']}"
            )

        core_results[year] = core

        wage_inputs[year] = {
            "monthly_total_cash_earnings_yen": (
                monthly_total_cash_earnings_yen
            ),
            "monthly_regular_earnings_yen": (
                monthly_regular_pay_yen
            ),
            "monthly_special_earnings_yen": (
                monthly_special_earnings_yen
            ),
        }

    # ----------------------------------------
    # 6. 各年の住民税を対応させ、
    #    最終的な手取りを計算
    # ----------------------------------------

    result_rows: list[
        dict[str, float | int | str]
    ] = []

    for year in range(
        start_year,
        end_year + 1,
    ):
        current = core_results[year]

        if timing == "income_year":
            # 所得年 t の所得に
            # 課税年度 t+1 を対応。
            resident_tax_income_year = year
            assessment_year = year + 1

        else:
            # 年 t に対応する住民税として、
            # t-1 年所得に基づく
            # 課税年度 t の年税額を使用。
            resident_tax_income_year = year - 1
            assessment_year = year

        resident_source = core_results[
            resident_tax_income_year
        ]

        resident = (
            calculate_standard_worker_resident_tax(
                salary_income_yen=float(
                    resident_source[
                        "salary_income_yen"
                    ]
                ),
                social_insurance_deduction_yen=float(
                    resident_source[
                        "social_insurance_yen"
                    ]
                ),
                assessment_year=assessment_year,
                resident_tax_deductions=(
                    rule_tables[
                        "resident_tax_deductions"
                    ]
                ),
                resident_tax_income_rates=(
                    rule_tables[
                        "resident_tax_income_rates"
                    ]
                ),
                resident_tax_adjustments=(
                    rule_tables[
                        "resident_tax_adjustments"
                    ]
                ),
                resident_tax_per_capita=(
                    rule_tables[
                        "resident_tax_per_capita"
                    ]
                ),
                dependent_count=dependent_count,
                other_income_deductions_yen=(
                    resident_other_income_deductions_yen
                ),
                human_deduction_difference_yen=(
                    human_deduction_difference_yen
                ),
                municipality_band=(
                    municipality_band
                ),
                policy_mode=policy_mode,
            )
        )

        gross_salary_yen = float(
            current[
                "gross_salary_yen"
            ]
        )

        social_insurance_yen = float(
            current[
                "social_insurance_yen"
            ]
        )

        income_tax_yen = float(
            current[
                "income_tax_yen"
            ]
        )

        resident_tax_yen = float(
            resident[
                "resident_tax_yen"
            ]
        )

        total_deductions_yen = (
            social_insurance_yen
            + income_tax_yen
            + resident_tax_yen
        )

        nominal_take_home_yen = (
            gross_salary_yen
            - total_deductions_yen
        )

        if gross_salary_yen > 0:
            effective_burden_rate = (
                total_deductions_yen
                / gross_salary_yen
            )

            take_home_rate = (
                nominal_take_home_yen
                / gross_salary_yen
            )

        else:
            effective_burden_rate = 0.0
            take_home_rate = 0.0

        result_rows.append(
            {
                "year": year,
                "timing": timing,
                "resident_tax_income_year": (
                    resident_tax_income_year
                ),
                **wage_inputs[year],
                **current,
                **resident,
                "total_deductions_yen": float(
                    round(
                        total_deductions_yen,
                        10,
                    )
                ),
                "nominal_take_home_yen": float(
                    round(
                        nominal_take_home_yen,
                        10,
                    )
                ),
                "effective_burden_rate": float(
                    effective_burden_rate
                ),
                "take_home_rate": float(
                    take_home_rate
                ),
            }
        )

    return pd.DataFrame(
        result_rows
    ).sort_values(
        "year"
    ).reset_index(
        drop=True
    )


def calculate_standard_worker_resident_tax(
    salary_income_yen: float,
    social_insurance_deduction_yen: float,
    assessment_year: int,
    resident_tax_deductions: pd.DataFrame,
    resident_tax_income_rates: pd.DataFrame,
    resident_tax_adjustments: pd.DataFrame,
    resident_tax_per_capita: pd.DataFrame,
    dependent_count: int = 0,
    other_income_deductions_yen: float = 0.0,
    human_deduction_difference_yen: float = 50_000.0,
    municipality_band: str | None = None,
    policy_mode: str = "actual_policy",
) -> dict[str, float | int]:
    """ある所得を基礎とする年間住民税を計算する。"""

    resident_taxable = calculate_resident_taxable_income(
        salary_income_yen=salary_income_yen,
        social_insurance_deduction_yen=(
            social_insurance_deduction_yen
        ),
        assessment_year=assessment_year,
        resident_tax_deductions=(
            resident_tax_deductions
        ),
        other_income_deductions_yen=(
            other_income_deductions_yen
        ),
    )

    taxable_income_yen = resident_taxable[
        "resident_taxable_income_yen"
    ]

    base_income_levy_yen = (
        calculate_base_resident_income_levy(
            taxable_income_yen=taxable_income_yen,
            assessment_year=assessment_year,
            income_rate_rules=(
                resident_tax_income_rates
            ),
        )
    )

    adjusted = (
        calculate_resident_income_levy_after_adjustments(
            base_income_levy_yen=(
                base_income_levy_yen
            ),
            taxable_income_yen=(
                taxable_income_yen
            ),
            total_income_yen=(
                salary_income_yen
            ),
            assessment_year=assessment_year,
            adjustment_rules=(
                resident_tax_adjustments
            ),
            dependent_count=dependent_count,
            human_deduction_difference_yen=(
                human_deduction_difference_yen
            ),
            policy_mode=policy_mode,
        )
    )

    total = calculate_total_resident_tax(
        income_levy_after_adjustments_yen=(
            adjusted[
                "resident_income_levy_after_adjustments_yen"
            ]
        ),
        assessment_year=assessment_year,
        per_capita_rules=(
            resident_tax_per_capita
        ),
        municipality_band=municipality_band,
    )

    return {
        "resident_tax_assessment_year": (
            assessment_year
        ),
        "resident_basic_deduction_yen": float(
            resident_taxable[
                "resident_basic_deduction_yen"
            ]
        ),
        "resident_taxable_income_yen": float(
            taxable_income_yen
        ),
        "base_resident_income_levy_yen": float(
            base_income_levy_yen
        ),
        "resident_adjustment_credit_yen": float(
            adjusted[
                "resident_adjustment_credit_yen"
            ]
        ),
        "resident_other_reduction_yen": float(
            adjusted[
                "resident_other_reduction_yen"
            ]
        ),
        "resident_income_levy_yen": float(
            total[
                "resident_income_levy_yen"
            ]
        ),
        "resident_per_capita_yen": float(
            total[
                "resident_per_capita_yen"
            ]
        ),
        "forest_environment_tax_yen": float(
            total[
                "forest_environment_tax_yen"
            ]
        ),
        "resident_tax_yen": float(
            total[
                "total_resident_tax_yen"
            ]
        ),
    }


def add_real_take_home_metrics(
    take_home_df: pd.DataFrame,
    annual_cpi_df: pd.DataFrame,
    base_year: int = 1990,
) -> pd.DataFrame:
    """手取り時系列に実質額と基準年指数を追加する。"""

    take_home_required = {
        "year",
        "gross_salary_yen",
        "nominal_take_home_yen",
    }

    cpi_required = {
        "year",
        "cpi",
    }

    missing_take_home = (
        take_home_required
        - set(take_home_df.columns)
    )

    if missing_take_home:
        raise ValueError(
            "手取りデータに必要な列がありません: "
            f"{sorted(missing_take_home)}"
        )

    missing_cpi = (
        cpi_required
        - set(annual_cpi_df.columns)
    )

    if missing_cpi:
        raise ValueError(
            "CPIデータに必要な列がありません: "
            f"{sorted(missing_cpi)}"
        )

    take_home = take_home_df.copy()
    cpi = annual_cpi_df.copy()

    take_home["year"] = pd.to_numeric(
        take_home["year"],
        errors="coerce",
    )

    cpi["year"] = pd.to_numeric(
        cpi["year"],
        errors="coerce",
    )

    cpi["cpi"] = pd.to_numeric(
        cpi["cpi"],
        errors="coerce",
    )

    if take_home["year"].isna().any():
        raise ValueError(
            "手取りデータの year に不正な値があります。"
        )

    if cpi[
        [
            "year",
            "cpi",
        ]
    ].isna().any().any():
        raise ValueError(
            "CPIデータに不正な値があります。"
        )

    if (cpi["cpi"] <= 0).any():
        raise ValueError(
            "CPIは0より大きい必要があります。"
        )

    if take_home["year"].duplicated().any():
        raise ValueError(
            "手取りデータに重複年があります。"
        )

    if cpi["year"].duplicated().any():
        raise ValueError(
            "CPIデータに重複年があります。"
        )

    take_home["year"] = (
        take_home["year"].astype(int)
    )

    cpi["year"] = (
        cpi["year"].astype(int)
    )

    missing_cpi_years = sorted(
        set(take_home["year"])
        - set(cpi["year"])
    )

    if missing_cpi_years:
        raise ValueError(
            "手取り実質化に必要なCPI年が"
            "欠けています: "
            f"{missing_cpi_years}"
        )

    result = take_home.merge(
        cpi[
            [
                "year",
                "cpi",
            ]
        ],
        on="year",
        how="left",
        validate="one_to_one",
    )

    result["real_gross_salary_yen"] = (
        result["gross_salary_yen"]
        / result["cpi"]
        * 100
    )

    result["real_take_home_yen"] = (
        result["nominal_take_home_yen"]
        / result["cpi"]
        * 100
    )

    base = result.loc[
        result["year"] == base_year
    ]

    if len(base) != 1:
        raise ValueError(
            f"{base_year}年の基準データを"
            "一意に取得できません。"
        )

    base_row = base.iloc[0]

    base_values = {
        "gross_salary_yen":
            base_row["gross_salary_yen"],
        "nominal_take_home_yen":
            base_row["nominal_take_home_yen"],
        "real_gross_salary_yen":
            base_row["real_gross_salary_yen"],
        "real_take_home_yen":
            base_row["real_take_home_yen"],
    }

    for name, value in base_values.items():
        if value <= 0:
            raise ValueError(
                f"基準年の{name}は"
                "0より大きい必要があります。"
            )

    result["gross_salary_index"] = (
        result["gross_salary_yen"]
        / base_values["gross_salary_yen"]
        * 100
    )

    result["nominal_take_home_index"] = (
        result["nominal_take_home_yen"]
        / base_values["nominal_take_home_yen"]
        * 100
    )

    result["real_gross_salary_index"] = (
        result["real_gross_salary_yen"]
        / base_values["real_gross_salary_yen"]
        * 100
    )

    result["real_take_home_index"] = (
        result["real_take_home_yen"]
        / base_values["real_take_home_yen"]
        * 100
    )

    return (
        result
        .sort_values("year")
        .reset_index(drop=True)
    )


def create_take_home_period_log_decomposition(
    df: pd.DataFrame,
    periods: list[tuple[int, int]],
) -> pd.DataFrame:
    """実質手取りの期間変化を賃金・負担率・物価に対数分解する。

    R = W * q / P

    W: 額面賃金
    q: 手取り率 = 1 - 実効負担率
    P: CPI

    よって、

    Δln(R)
        = Δln(W)
        + Δln(q)
        - Δln(P)

    と分解する。
    """

    required_columns = {
        "year",
        "gross_salary_yen",
        "take_home_rate",
        "cpi",
        "real_take_home_yen",
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "期間分解に必要な列がありません: "
            f"{sorted(missing)}"
        )

    data = df.copy()

    if data["year"].duplicated().any():
        raise ValueError(
            "年次データに重複年があります。"
        )

    positive_columns = [
        "gross_salary_yen",
        "take_home_rate",
        "cpi",
        "real_take_home_yen",
    ]

    for column in positive_columns:
        if (data[column] <= 0).any():
            raise ValueError(
                f"{column} は0より大きい"
                "必要があります。"
            )

    rows = []

    for start_year, end_year in periods:
        if start_year >= end_year:
            raise ValueError(
                "期間の開始年は終了年より"
                "前である必要があります。"
            )

        start = data.loc[
            data["year"] == start_year
        ]

        end = data.loc[
            data["year"] == end_year
        ]

        if len(start) != 1:
            raise ValueError(
                f"{start_year}年のデータを"
                "一意に取得できません。"
            )

        if len(end) != 1:
            raise ValueError(
                f"{end_year}年のデータを"
                "一意に取得できません。"
            )

        start = start.iloc[0]
        end = end.iloc[0]

        wage_log_contribution = (
            math.log(
                end["gross_salary_yen"]
                / start["gross_salary_yen"]
            )
            * 100
        )

        burden_log_contribution = (
            math.log(
                end["take_home_rate"]
                / start["take_home_rate"]
            )
            * 100
        )

        price_log_contribution = (
            -math.log(
                end["cpi"]
                / start["cpi"]
            )
            * 100
        )

        decomposition_total = (
            wage_log_contribution
            + burden_log_contribution
            + price_log_contribution
        )

        observed_log_change = (
            math.log(
                end["real_take_home_yen"]
                / start["real_take_home_yen"]
            )
            * 100
        )

        observed_pct_change = (
            end["real_take_home_yen"]
            / start["real_take_home_yen"]
            - 1
        ) * 100

        rows.append(
            {
                "period": (
                    f"{start_year}"
                    f"→{end_year}"
                ),
                "start_year": start_year,
                "end_year": end_year,
                "wage_log_contribution_pt": (
                    wage_log_contribution
                ),
                "burden_log_contribution_pt": (
                    burden_log_contribution
                ),
                "price_log_contribution_pt": (
                    price_log_contribution
                ),
                "real_take_home_log_change_pt": (
                    observed_log_change
                ),
                "decomposition_total_pt": (
                    decomposition_total
                ),
                "decomposition_error_pt": (
                    observed_log_change
                    - decomposition_total
                ),
                "real_take_home_pct_change": (
                    observed_pct_change
                ),
                "burden_change_pt": (
                    (
                        (
                            1
                            - end["take_home_rate"]
                        )
                        - (
                            1
                            - start["take_home_rate"]
                        )
                    )
                    * 100
                ),
            }
        )

    return pd.DataFrame(rows)


def add_deduction_component_rates(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """額面賃金に対する税・社会保険料各項目の負担率を追加する。"""

    required_columns = {
        "gross_salary_yen",
        "income_tax_yen",
        "resident_tax_yen",
        "pension_yen",
        "health_insurance_yen",
        "employment_insurance_yen",
        "total_deductions_yen",
        "effective_burden_rate",
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "控除項目別負担率の計算に必要な列がありません: "
            f"{sorted(missing)}"
        )

    result = df.copy()

    if (
        result["gross_salary_yen"]
        <= 0
    ).any():
        raise ValueError(
            "額面賃金は0より大きい必要があります。"
        )

    deduction_columns = {
        "income_tax_yen":
            "income_tax_rate",
        "resident_tax_yen":
            "resident_tax_rate",
        "pension_yen":
            "pension_rate_effective",
        "health_insurance_yen":
            "health_insurance_rate_effective",
        "employment_insurance_yen":
            "employment_insurance_rate_effective",
    }

    for amount_column, rate_column in (
        deduction_columns.items()
    ):
        if (
            result[amount_column]
            < 0
        ).any():
            raise ValueError(
                f"{amount_column} は"
                "0以上である必要があります。"
            )

        result[rate_column] = (
            result[amount_column]
            / result["gross_salary_yen"]
        )

    rate_columns = list(
        deduction_columns.values()
    )

    result[
        "component_burden_rate_sum"
    ] = (
        result[rate_columns]
        .sum(axis=1)
    )

    result[
        "component_burden_rate_error"
    ] = (
        result[
            "effective_burden_rate"
        ]
        - result[
            "component_burden_rate_sum"
        ]
    )

    return result


def create_deduction_burden_change_summary(
    df: pd.DataFrame,
    periods: list[tuple[int, int]],
) -> pd.DataFrame:
    """期間ごとの実効負担率変化を控除項目別に分解する。"""

    required_columns = {
        "year",
        "effective_burden_rate",
        "income_tax_rate",
        "resident_tax_rate",
        "pension_rate_effective",
        "health_insurance_rate_effective",
        "employment_insurance_rate_effective",
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "負担率変化分解に必要な列がありません: "
            f"{sorted(missing)}"
        )

    if df["year"].duplicated().any():
        raise ValueError(
            "年次データに重複年があります。"
        )

    components = [
        "income_tax_rate",
        "resident_tax_rate",
        "pension_rate_effective",
        "health_insurance_rate_effective",
        "employment_insurance_rate_effective",
    ]

    rows = []

    for start_year, end_year in periods:
        if start_year >= end_year:
            raise ValueError(
                "期間の開始年は終了年より"
                "前である必要があります。"
            )

        start = df.loc[
            df["year"] == start_year
        ]

        end = df.loc[
            df["year"] == end_year
        ]

        if len(start) != 1:
            raise ValueError(
                f"{start_year}年のデータを"
                "一意に取得できません。"
            )

        if len(end) != 1:
            raise ValueError(
                f"{end_year}年のデータを"
                "一意に取得できません。"
            )

        start = start.iloc[0]
        end = end.iloc[0]

        changes = {
            column: (
                end[column]
                - start[column]
            )
            * 100
            for column in components
        }

        component_sum = sum(
            changes.values()
        )

        total_change = (
            end["effective_burden_rate"]
            - start["effective_burden_rate"]
        ) * 100

        rows.append(
            {
                "period":
                    f"{start_year}→{end_year}",
                "start_year":
                    start_year,
                "end_year":
                    end_year,
                "income_tax_change_pt":
                    changes[
                        "income_tax_rate"
                    ],
                "resident_tax_change_pt":
                    changes[
                        "resident_tax_rate"
                    ],
                "pension_change_pt":
                    changes[
                        "pension_rate_effective"
                    ],
                "health_insurance_change_pt":
                    changes[
                        "health_insurance_rate_effective"
                    ],
                "employment_insurance_change_pt":
                    changes[
                        "employment_insurance_rate_effective"
                    ],
                "component_sum_change_pt":
                    component_sum,
                "total_burden_change_pt":
                    total_change,
                "decomposition_error_pt":
                    total_change
                    - component_sum,
            }
        )

    return pd.DataFrame(rows)
