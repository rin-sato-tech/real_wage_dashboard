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
