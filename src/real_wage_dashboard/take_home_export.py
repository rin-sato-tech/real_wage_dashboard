import pandas as pd


COMMON_ID_COLUMNS = [
    "year",
    "period",
    "start_year",
    "end_year",
    "check",
    "comparison",
]


def _infer_metric_unit(
    metric: str,
) -> str:
    """指標名からTableau表示用の単位を推定する。"""

    if metric == "cpi":
        return "index"

    if metric.endswith("_yen"):
        return "yen"

    if (
        metric.endswith("_rate")
        or metric.endswith(
            "_rate_effective"
        )
    ):
        return "ratio"

    if metric.endswith("_index"):
        return "index"

    if "_pct" in metric:
        return "pct"

    if metric.endswith("_pt"):
        return "pt"

    return "value"


def _create_long_snapshot(
    df: pd.DataFrame,
    record_type: str,
) -> pd.DataFrame:
    """横持ちの分析結果をTableau向けlong形式に変換する。"""

    data = df.copy()

    id_columns = [
        column
        for column in COMMON_ID_COLUMNS
        if column in data.columns
    ]

    value_columns = []

    for column in data.columns:
        if column in id_columns:
            continue

        if pd.api.types.is_numeric_dtype(
            data[column]
        ):
            value_columns.append(column)

    if not value_columns:
        return pd.DataFrame(
            columns=[
                "record_type",
                *COMMON_ID_COLUMNS,
                "metric",
                "value",
                "unit",
                "note",
            ]
        )

    result = data.melt(
        id_vars=id_columns,
        value_vars=value_columns,
        var_name="metric",
        value_name="value",
    )

    result["record_type"] = record_type

    result["unit"] = (
        result["metric"]
        .map(_infer_metric_unit)
    )

    result["note"] = pd.NA

    for column in COMMON_ID_COLUMNS:
        if column not in result.columns:
            result[column] = pd.NA

    return result[
        [
            "record_type",
            "year",
            "period",
            "start_year",
            "end_year",
            "check",
            "comparison",
            "metric",
            "value",
            "unit",
            "note",
        ]
    ]


def _create_robustness_long(
    robustness_df: pd.DataFrame,
) -> pd.DataFrame:
    """頑健性確認結果を共通Tableau形式へ変換する。"""

    required_columns = {
        "check",
        "comparison",
        "period",
        "metric",
        "value",
        "unit",
        "note",
    }

    missing = (
        required_columns
        - set(robustness_df.columns)
    )

    if missing:
        raise ValueError(
            "頑健性要約に必要な列がありません: "
            f"{sorted(missing)}"
        )

    result = robustness_df.copy()

    result["record_type"] = (
        "robustness"
    )

    result["year"] = pd.NA
    result["start_year"] = pd.NA
    result["end_year"] = pd.NA

    return result[
        [
            "record_type",
            "year",
            "period",
            "start_year",
            "end_year",
            "check",
            "comparison",
            "metric",
            "value",
            "unit",
            "note",
        ]
    ]


def _create_fixed_policy_long(
    fixed_policy_df: pd.DataFrame,
) -> pd.DataFrame:
    """固定制度反実仮想をTableau向けlong形式へ変換する。"""

    paired_metrics = {
        "nominal_take_home_yen": (
            "actual_nominal_take_home_yen",
            "fixed_1990_nominal_take_home_yen",
        ),
        "real_take_home_yen": (
            "actual_real_take_home_yen",
            "fixed_1990_real_take_home_yen",
        ),
        "total_deductions_yen": (
            "actual_total_deductions_yen",
            "fixed_1990_total_deductions_yen",
        ),
        "effective_burden_rate": (
            "actual_effective_burden_rate",
            "fixed_1990_effective_burden_rate",
        ),
        "income_tax_yen": (
            "actual_income_tax_yen",
            "fixed_1990_income_tax_yen",
        ),
        "resident_tax_yen": (
            "actual_resident_tax_yen",
            "fixed_1990_resident_tax_yen",
        ),
        "pension_yen": (
            "actual_pension_yen",
            "fixed_1990_pension_yen",
        ),
        "health_insurance_yen": (
            "actual_health_insurance_yen",
            "fixed_1990_health_insurance_yen",
        ),
        "employment_insurance_yen": (
            "actual_employment_insurance_yen",
            "fixed_1990_employment_insurance_yen",
        ),
    }

    required_columns = {
        "year",
        *[
            column
            for pair in paired_metrics.values()
            for column in pair
        ],
        "nominal_take_home_yen_difference_yen",
        "real_take_home_difference_yen",
        "burden_rate_difference_pt",
    }

    missing = (
        required_columns
        - set(fixed_policy_df.columns)
    )

    if missing:
        raise ValueError(
            "固定制度比較に必要な列がありません: "
            f"{sorted(missing)}"
        )

    rows = []

    for row in fixed_policy_df.itertuples(
        index=False
    ):
        year = int(row.year)

        for (
            metric,
            (
                actual_column,
                fixed_column,
            ),
        ) in paired_metrics.items():

            rows.append(
                {
                    "record_type":
                        "fixed_policy_comparison",
                    "year":
                        year,
                    "period":
                        pd.NA,
                    "start_year":
                        pd.NA,
                    "end_year":
                        pd.NA,
                    "check":
                        "fixed_policy",
                    "comparison":
                        "actual_policy",
                    "metric":
                        metric,
                    "value":
                        float(
                            getattr(
                                row,
                                actual_column,
                            )
                        ),
                    "unit":
                        _infer_metric_unit(
                            metric
                        ),
                    "note":
                        "各年の実際の税・社会保険制度。",
                }
            )

            rows.append(
                {
                    "record_type":
                        "fixed_policy_comparison",
                    "year":
                        year,
                    "period":
                        pd.NA,
                    "start_year":
                        pd.NA,
                    "end_year":
                        pd.NA,
                    "check":
                        "fixed_policy",
                    "comparison":
                        "fixed_1990_policy",
                    "metric":
                        metric,
                    "value":
                        float(
                            getattr(
                                row,
                                fixed_column,
                            )
                        ),
                    "unit":
                        _infer_metric_unit(
                            metric
                        ),
                    "note":
                        (
                            "賃金は各年実績、"
                            "税・社会保険制度を"
                            "1990年に固定。"
                        ),
                }
            )

        difference_metrics = {
            "nominal_take_home_difference_yen":
                float(
                    row.nominal_take_home_yen_difference_yen
                ),
            "real_take_home_difference_yen":
                float(
                    row.real_take_home_difference_yen
                ),
            "burden_rate_difference_pt":
                float(
                    row.burden_rate_difference_pt
                ),
        }

        for (
            metric,
            value,
        ) in difference_metrics.items():
            rows.append(
                {
                    "record_type":
                        "fixed_policy_comparison",
                    "year":
                        year,
                    "period":
                        pd.NA,
                    "start_year":
                        pd.NA,
                    "end_year":
                        pd.NA,
                    "check":
                        "fixed_policy",
                    "comparison":
                        "actual_minus_fixed_1990",
                    "metric":
                        metric,
                    "value":
                        value,
                    "unit":
                        _infer_metric_unit(
                            metric
                        ),
                    "note":
                        (
                            "実際制度－1990年固定制度。"
                        ),
                }
            )

    return pd.DataFrame(rows)


def create_take_home_tableau_export(
    main_series: pd.DataFrame,
    period_log_decomposition: pd.DataFrame,
    burden_change_summary: pd.DataFrame,
    burden_shapley: pd.DataFrame,
    real_shapley: pd.DataFrame,
    fixed_policy_comparison: pd.DataFrame,
    robustness_summary: pd.DataFrame,
) -> pd.DataFrame:
    """手取り分析の主要結果をTableau用long形式へ統合する。"""

    frames = [
        _create_long_snapshot(
            main_series,
            record_type="annual_main",
        ),
        _create_long_snapshot(
            period_log_decomposition,
            record_type="period_log_decomposition",
        ),
        _create_long_snapshot(
            burden_change_summary,
            record_type="burden_change",
        ),
        _create_long_snapshot(
            burden_shapley,
            record_type="burden_shapley",
        ),
        _create_long_snapshot(
            real_shapley,
            record_type="real_take_home_shapley",
        ),
        _create_fixed_policy_long(
            fixed_policy_comparison
        ),
        _create_robustness_long(
            robustness_summary
        ),
    ]

    result = pd.concat(
        frames,
        ignore_index=True,
    )

    result["analysis"] = (
        "take_home_wage"
    )

    result["industry"] = (
        "調査産業計"
    )

    result["establishment_size"] = (
        "5人以上"
    )

    result["employment_type"] = (
        "就業形態計"
    )

    result["model_age"] = 35
    result["model_sex"] = "male"

    result["resident_tax_timing"] = (
        "income_year"
    )

    result["cpi_series"] = (
        "持家の帰属家賃を除く総合"
    )

    result["base_year"] = 1990

    result = result[
        [
            "analysis",
            "record_type",
            "year",
            "period",
            "start_year",
            "end_year",
            "metric",
            "value",
            "unit",
            "check",
            "comparison",
            "note",
            "industry",
            "establishment_size",
            "employment_type",
            "model_age",
            "model_sex",
            "resident_tax_timing",
            "cpi_series",
            "base_year",
        ]
    ]

    return result.reset_index(
        drop=True
    )
