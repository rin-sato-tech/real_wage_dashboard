from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/raw/take_home")

INCOME_TAX_BRACKETS_PATH = DATA_DIR / "income_tax_brackets.csv"
INCOME_TAX_DEDUCTIONS_PATH = DATA_DIR / "income_tax_deductions.csv"
INCOME_TAX_ADJUSTMENTS_PATH = DATA_DIR / "income_tax_adjustments.csv"

PENSION_RATES_PATH = DATA_DIR / "pension_rates.csv"
HEALTH_INSURANCE_RATES_PATH = DATA_DIR / "health_insurance_rates.csv"
SOCIAL_INSURANCE_BONUS_RULES_PATH = (
    DATA_DIR / "social_insurance_bonus_rules.csv"
)
EMPLOYMENT_INSURANCE_RATES_PATH = (
    DATA_DIR / "employment_insurance_rates.csv"
)

RESIDENT_TAX_INCOME_RATES_PATH = (
    DATA_DIR / "resident_tax_income_rates.csv"
)
RESIDENT_TAX_DEDUCTIONS_PATH = (
    DATA_DIR / "resident_tax_deductions.csv"
)
RESIDENT_TAX_PER_CAPITA_PATH = (
    DATA_DIR / "resident_tax_per_capita.csv"
)
RESIDENT_TAX_ADJUSTMENTS_PATH = (
    DATA_DIR / "resident_tax_adjustments.csv"
)

PENSION_STANDARD_MONTHLY_HISTORY_PATH = (
    DATA_DIR / "pension_standard_monthly_history.xlsx"
)

def _load_rule_csv(
    path: str | Path,
    required_columns: set[str],
    date_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    """制度パラメータCSVを読み込み、基本的なスキーマを検証する。"""

    df = pd.read_csv(path)

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"{Path(path).name} に必要な列がありません: "
            f"{sorted(missing)}"
        )

    for column in date_columns:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    return df


def load_income_tax_brackets(
    path: str | Path = INCOME_TAX_BRACKETS_PATH,
) -> pd.DataFrame:
    """所得税率表を読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "effective_from",
            "effective_to",
            "bracket_order",
            "lower_bound_yen",
            "upper_bound_yen",
            "marginal_rate",
            "quick_deduction_yen",
            "source_key",
        },
        date_columns=(
            "effective_from",
            "effective_to",
        ),
    )


def load_income_tax_deductions(
    path: str | Path = INCOME_TAX_DEDUCTIONS_PATH,
) -> pd.DataFrame:
    """給与所得控除・基礎控除ルールを読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "deduction_type",
            "effective_from",
            "effective_to",
            "bracket_order",
            "basis",
            "lower_bound_yen",
            "upper_bound_yen",
            "rate",
            "add_yen",
            "fixed_yen",
            "source_key",
        },
        date_columns=(
            "effective_from",
            "effective_to",
        ),
    )


def load_income_tax_adjustments(
    path: str | Path = INCOME_TAX_ADJUSTMENTS_PATH,
) -> pd.DataFrame:
    """所得税の時限減税・付加税等を読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "policy_id",
            "effective_from",
            "effective_to",
            "operation",
            "base",
            "policy_class",
            "apply_order",
            "source_key",
        },
        date_columns=(
            "effective_from",
            "effective_to",
        ),
    )


def load_pension_rates(
    path: str | Path = PENSION_RATES_PATH,
) -> pd.DataFrame:
    """厚生年金保険料率を読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "effective_from",
            "effective_to",
            "insured_category",
            "regular_total_rate",
            "bonus_total_rate",
            "employee_share",
            "source_key",
        },
        date_columns=(
            "effective_from",
            "effective_to",
        ),
    )


def load_health_insurance_rates(
    path: str | Path = HEALTH_INSURANCE_RATES_PATH,
) -> pd.DataFrame:
    """健康保険料率を読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "effective_from",
            "effective_to",
            "scheme",
            "regular_total_rate",
            "regular_employee_share",
            "rate_type",
            "source_key",
        },
        date_columns=(
            "effective_from",
            "effective_to",
        ),
    )


def load_social_insurance_bonus_rules(
    path: str | Path = SOCIAL_INSURANCE_BONUS_RULES_PATH,
) -> pd.DataFrame:
    """健康保険・厚生年金の標準賞与額ルールを読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "scheme",
            "effective_from",
            "effective_to",
            "cap_type",
            "cap_yen",
            "rounding_unit_yen",
        },
        date_columns=(
            "effective_from",
            "effective_to",
        ),
    )


def load_employment_insurance_rates(
    path: str | Path = EMPLOYMENT_INSURANCE_RATES_PATH,
) -> pd.DataFrame:
    """雇用保険の労働者負担率を読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "effective_from",
            "effective_to",
            "business_type",
            "employee_rate",
            "source_key",
        },
        date_columns=(
            "effective_from",
            "effective_to",
        ),
    )


def load_resident_tax_income_rates(
    path: str | Path = RESIDENT_TAX_INCOME_RATES_PATH,
) -> pd.DataFrame:
    """個人住民税の所得割税率を読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "assessment_year_from",
            "assessment_year_to",
            "bracket_order",
            "lower_bound_yen",
            "upper_bound_yen",
            "marginal_rate",
            "quick_deduction_yen",
            "source_key",
        },
    )


def load_resident_tax_deductions(
    path: str | Path = RESIDENT_TAX_DEDUCTIONS_PATH,
) -> pd.DataFrame:
    """個人住民税の所得控除ルールを読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "deduction_type",
            "assessment_year_from",
            "assessment_year_to",
            "bracket_order",
            "basis",
            "lower_bound_yen",
            "upper_bound_yen",
            "fixed_yen",
            "source_key",
        },
    )


def load_resident_tax_per_capita(
    path: str | Path = RESIDENT_TAX_PER_CAPITA_PATH,
) -> pd.DataFrame:
    """個人住民税の均等割・森林環境税ルールを読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "assessment_year_from",
            "assessment_year_to",
            "municipality_band",
            "prefectural_yen",
            "municipal_yen",
            "forest_environment_tax_yen",
            "source_key",
        },
    )


def load_resident_tax_adjustments(
    path: str | Path = RESIDENT_TAX_ADJUSTMENTS_PATH,
) -> pd.DataFrame:
    """個人住民税の減税・調整控除等のルールを読み込む。"""

    return _load_rule_csv(
        path,
        required_columns={
            "policy_id",
            "assessment_year_from",
            "assessment_year_to",
            "operation",
            "base",
            "policy_class",
            "source_key",
        },
    )


def load_take_home_rule_tables() -> dict[str, pd.DataFrame]:
    """手取り分析で使用する制度パラメータを一括で読み込む。"""

    return {
        "income_tax_brackets": load_income_tax_brackets(),
        "income_tax_deductions": load_income_tax_deductions(),
        "income_tax_adjustments": load_income_tax_adjustments(),
        "pension_rates": load_pension_rates(),
        "health_insurance_rates": load_health_insurance_rates(),
        "social_insurance_bonus_rules": (
            load_social_insurance_bonus_rules()
        ),
        "employment_insurance_rates": (
            load_employment_insurance_rates()
        ),
        "resident_tax_income_rates": (
            load_resident_tax_income_rates()
        ),
        "resident_tax_deductions": (
            load_resident_tax_deductions()
        ),
        "resident_tax_per_capita": (
            load_resident_tax_per_capita()
        ),
        "resident_tax_adjustments": (
            load_resident_tax_adjustments()
        ),
    }
