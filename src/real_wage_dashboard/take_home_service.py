from pathlib import Path

import pandas as pd

PENSION_STANDARD_MONTHLY_PERIODS = {
    10: (
        pd.Timestamp("1989-12-01"),
        pd.Timestamp("1994-10-31"),
    ),
    11: (
        pd.Timestamp("1994-11-01"),
        pd.Timestamp("2000-09-30"),
    ),
    12: (
        pd.Timestamp("2000-10-01"),
        pd.Timestamp("2016-09-30"),
    ),
    13: (
        pd.Timestamp("2016-10-01"),
        pd.Timestamp("2020-08-31"),
    ),
    14: (
        pd.Timestamp("2020-09-01"),
        pd.NaT,
    ),
}

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

HEALTH_STANDARD_MONTHLY_HISTORY_PATH = (
    DATA_DIR / "health_standard_monthly_history.csv"
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
    """健康保険料率の履歴を読み込む。"""

    required_columns = {
        "effective_from",
        "effective_to",
        "regular_total_rate",
        "employee_share",
        "bonus_employee_rate",
        "source_key",
        "notes",
    }

    return _load_rule_csv(
        path=path,
        required_columns=required_columns,
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
        "income_tax_brackets": (
            load_income_tax_brackets()
        ),
        "income_tax_deductions": (
            load_income_tax_deductions()
        ),
        "income_tax_adjustments": (
            load_income_tax_adjustments()
        ),
        "pension_rates": (
            load_pension_rates()
        ),
        "pension_standard_monthly": (
            load_pension_standard_monthly_history()
        ),
        "health_insurance_rates": (
            load_health_insurance_rates()
        ),
        "health_standard_monthly": (
            load_health_standard_monthly_history()
        ),
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


def _create_standard_monthly_brackets(
    standard_monthly_values: list[int],
    effective_from: pd.Timestamp,
    effective_to: pd.Timestamp | None,
) -> pd.DataFrame:
    """標準報酬月額一覧から報酬月額の等級境界を作成する。"""

    if not standard_monthly_values:
        raise ValueError(
            "標準報酬月額の一覧が空です。"
        )

    if any(value <= 0 for value in standard_monthly_values):
        raise ValueError(
            "標準報酬月額は正の値である必要があります。"
        )

    if len(standard_monthly_values) != len(
        set(standard_monthly_values)
    ):
        raise ValueError(
            "標準報酬月額に重複があります。"
        )

    values = sorted(
        standard_monthly_values
    )

    records: list[dict[str, object]] = []

    for index, standard_monthly_yen in enumerate(values):
        if index == 0:
            lower_bound = None
        else:
            previous = values[index - 1]

            lower_bound = int(
                (
                    previous
                    + standard_monthly_yen
                )
                / 2
            )

        if index == len(values) - 1:
            upper_bound = None
        else:
            following = values[index + 1]

            upper_bound = int(
                (
                    standard_monthly_yen
                    + following
                )
                / 2
            )

        records.append(
            {
                "effective_from": effective_from,
                "effective_to": effective_to,
                "grade": index + 1,
                "standard_monthly_yen": (
                    standard_monthly_yen
                ),
                "remuneration_lower_yen": lower_bound,
                "remuneration_upper_yen": upper_bound,
            }
        )

    return pd.DataFrame(records)


def load_pension_standard_monthly_history(
    path: str | Path = PENSION_STANDARD_MONTHLY_HISTORY_PATH,
) -> pd.DataFrame:
    """厚生年金の標準報酬月額等級の変遷表をlong形式で読み込む。"""

    raw = pd.read_excel(
        path,
        sheet_name="厚生年金保険　標準報酬月額等級の変遷",
        header=None,
    )

    period_frames: list[pd.DataFrame] = []

    for (
        column_index,
        (
            effective_from,
            effective_to,
        ),
    ) in PENSION_STANDARD_MONTHLY_PERIODS.items():
        values = pd.to_numeric(
            raw.iloc[:, column_index],
            errors="coerce",
        ).dropna()

        # 原表の単位は千円なので円へ変換する。
        standard_monthly_values = (
            values
            .astype(int)
            .mul(1_000)
            .tolist()
        )

        if not standard_monthly_values:
            raise ValueError(
                "標準報酬月額を取得できません。"
                f" column={column_index}"
            )

        period = _create_standard_monthly_brackets(
            standard_monthly_values=(
                standard_monthly_values
            ),
            effective_from=effective_from,
            effective_to=effective_to,
        )

        period_frames.append(period)

    result = pd.concat(
        period_frames,
        ignore_index=True,
    )

    _validate_pension_standard_monthly_history(
        result
    )

    return result


def _validate_pension_standard_monthly_history(
    df: pd.DataFrame,
) -> None:
    """厚生年金の標準報酬月額等級データを検証する。"""

    required_columns = {
        "effective_from",
        "effective_to",
        "grade",
        "standard_monthly_yen",
        "remuneration_lower_yen",
        "remuneration_upper_yen",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            "標準報酬月額データに必要な列がありません: "
            f"{sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "標準報酬月額データが空です。"
        )

    if df[
        [
            "effective_from",
            "grade",
            "standard_monthly_yen",
        ]
    ].isna().any().any():
        raise ValueError(
            "標準報酬月額データの必須項目に欠損があります。"
        )

    if (
        df["standard_monthly_yen"]
        <= 0
    ).any():
        raise ValueError(
            "標準報酬月額は正の値である必要があります。"
        )

    if df.duplicated(
        subset=[
            "effective_from",
            "grade",
        ]
    ).any():
        raise ValueError(
            "同一制度期間内で等級が重複しています。"
        )

    if df.duplicated(
        subset=[
            "effective_from",
            "standard_monthly_yen",
        ]
    ).any():
        raise ValueError(
            "同一制度期間内で標準報酬月額が"
            "重複しています。"
        )

    for effective_from, group in df.groupby(
        "effective_from",
        sort=False,
    ):
        group = group.sort_values(
            "grade"
        ).reset_index(drop=True)

        expected_grades = list(
            range(
                1,
                len(group) + 1,
            )
        )

        if group["grade"].tolist() != expected_grades:
            raise ValueError(
                "標準報酬月額の等級が連続していません。"
                f" effective_from={effective_from}"
            )

        if not group[
            "standard_monthly_yen"
        ].is_monotonic_increasing:
            raise ValueError(
                "標準報酬月額が昇順ではありません。"
                f" effective_from={effective_from}"
            )

        for index in range(
            len(group) - 1
        ):
            current_upper = group.loc[
                index,
                "remuneration_upper_yen",
            ]

            next_lower = group.loc[
                index + 1,
                "remuneration_lower_yen",
            ]

            if current_upper != next_lower:
                raise ValueError(
                    "標準報酬月額の等級境界が"
                    "連続していません。"
                    f" effective_from={effective_from},"
                    f" grade={index + 1}"
                )


def load_health_standard_monthly_history(
    path: str | Path = HEALTH_STANDARD_MONTHLY_HISTORY_PATH,
) -> pd.DataFrame:
    """健康保険の標準報酬月額等級履歴を読み込む。"""

    required_columns = {
        "effective_from",
        "effective_to",
        "grade",
        "standard_monthly_yen",
        "remuneration_lower_yen",
        "remuneration_upper_yen",
        "source_key",
        "notes",
    }

    df = _load_rule_csv(
        path=path,
        required_columns=required_columns,
        date_columns=(
            "effective_from",
            "effective_to",
        ),
    )

    numeric_columns = [
        "grade",
        "standard_monthly_yen",
        "remuneration_lower_yen",
        "remuneration_upper_yen",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    _validate_health_standard_monthly_history(
        df
    )

    return df.reset_index(
        drop=True
    )


def _validate_health_standard_monthly_history(
    df: pd.DataFrame,
) -> None:
    """健康保険の標準報酬月額等級データを検証する。"""

    required_columns = {
        "effective_from",
        "effective_to",
        "grade",
        "standard_monthly_yen",
        "remuneration_lower_yen",
        "remuneration_upper_yen",
    }

    missing = required_columns - set(
        df.columns
    )

    if missing:
        raise ValueError(
            "健康保険標準報酬月額データに"
            "必要な列がありません: "
            f"{sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "健康保険標準報酬月額データが空です。"
        )

    if df[
        [
            "effective_from",
            "grade",
            "standard_monthly_yen",
        ]
    ].isna().any().any():
        raise ValueError(
            "健康保険標準報酬月額データの"
            "必須項目に欠損があります。"
        )

    if (
        df["grade"] <= 0
    ).any():
        raise ValueError(
            "健康保険の等級は"
            "正の値である必要があります。"
        )

    if (
        df["standard_monthly_yen"] <= 0
    ).any():
        raise ValueError(
            "健康保険の標準報酬月額は"
            "正の値である必要があります。"
        )

    if df.duplicated(
        subset=[
            "effective_from",
            "grade",
        ]
    ).any():
        raise ValueError(
            "同一制度期間内で"
            "健康保険の等級が重複しています。"
        )

    if df.duplicated(
        subset=[
            "effective_from",
            "standard_monthly_yen",
        ]
    ).any():
        raise ValueError(
            "同一制度期間内で"
            "健康保険の標準報酬月額が"
            "重複しています。"
        )

    periods = (
        df[
            [
                "effective_from",
                "effective_to",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "effective_from"
        )
        .reset_index(drop=True)
    )

    for index in range(
        len(periods) - 1
    ):
        current_end = periods.loc[
            index,
            "effective_to",
        ]

        next_start = periods.loc[
            index + 1,
            "effective_from",
        ]

        if pd.isna(current_end):
            raise ValueError(
                "最終期間以外の effective_to が"
                "欠損しています。"
            )

        expected_next = (
            current_end
            + pd.Timedelta(days=1)
        )

        if next_start != expected_next:
            raise ValueError(
                "健康保険標準報酬月額の"
                "制度期間が連続していません。"
                f" current_end={current_end.date()},"
                f" next_start={next_start.date()}"
            )

    for effective_from, group in df.groupby(
        "effective_from",
        sort=False,
    ):
        group = (
            group.sort_values(
                "grade"
            )
            .reset_index(drop=True)
        )

        expected_grades = list(
            range(
                1,
                len(group) + 1,
            )
        )

        actual_grades = (
            group["grade"]
            .astype(int)
            .tolist()
        )

        if actual_grades != expected_grades:
            raise ValueError(
                "健康保険標準報酬月額の"
                "等級が連続していません。"
                f" effective_from={effective_from}"
            )

        if not group[
            "standard_monthly_yen"
        ].is_monotonic_increasing:
            raise ValueError(
                "健康保険の標準報酬月額が"
                "昇順ではありません。"
                f" effective_from={effective_from}"
            )

        # 最下位等級には下限なし。
        if pd.notna(
            group.loc[
                0,
                "remuneration_lower_yen",
            ]
        ):
            raise ValueError(
                "健康保険の最下位等級には"
                "報酬月額下限を設定しません。"
            )

        # 最上位等級には上限なし。
        if pd.notna(
            group.loc[
                len(group) - 1,
                "remuneration_upper_yen",
            ]
        ):
            raise ValueError(
                "健康保険の最上位等級には"
                "報酬月額上限を設定しません。"
            )

        for index in range(
            len(group) - 1
        ):
            current_upper = group.loc[
                index,
                "remuneration_upper_yen",
            ]

            next_lower = group.loc[
                index + 1,
                "remuneration_lower_yen",
            ]

            if (
                pd.isna(current_upper)
                or pd.isna(next_lower)
                or current_upper != next_lower
            ):
                raise ValueError(
                    "健康保険標準報酬月額の"
                    "等級境界が連続していません。"
                    f" effective_from={effective_from},"
                    f" grade={index + 1}"
                )
