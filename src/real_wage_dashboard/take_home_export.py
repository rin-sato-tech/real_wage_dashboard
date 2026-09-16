import pandas as pd


COMMON_ID_COLUMNS = [
    "year",
    "period",
    "start_year",
    "end_year",
    "check",
    "comparison",
]

TABLEAU_JAPANESE_COLUMNS = {
    "analysis": "分析ID",
    "record_type": "レコード種別ID",
    "year": "年",
    "period": "期間",
    "start_year": "開始年",
    "end_year": "終了年",
    "metric": "指標ID",
    "value": "値",
    "unit": "単位ID",
    "check": "確認項目ID",
    "comparison": "比較ケースID",
    "note": "備考",
    "industry": "産業",
    "establishment_size": "事業所規模",
    "employment_type": "就業形態",
    "model_age": "モデル年齢",
    "model_sex": "モデル性別ID",
    "resident_tax_timing": "住民税対応ID",
    "cpi_series": "CPI系列",
    "base_year": "基準年",
}

TABLEAU_METRIC_LABELS = {
    # ----------------------------------------
    # 主系列
    # ----------------------------------------
    "cpi":
        "CPI",
    "gross_salary_yen":
        "額面賃金",
    "nominal_take_home_yen":
        "名目手取り",
    "real_gross_salary_yen":
        "実質額面賃金",
    "real_take_home_yen":
        "実質手取り",

    "gross_salary_index":
        "額面賃金指数",
    "nominal_take_home_index":
        "名目手取り指数",
    "real_gross_salary_index":
        "実質額面賃金指数",
    "real_take_home_index":
        "実質手取り指数",

    "total_deductions_yen":
        "控除総額",
    "social_insurance_yen":
        "社会保険料総額",
    "income_tax_yen":
        "所得税",
    "resident_tax_yen":
        "住民税",
    "pension_yen":
        "厚生年金保険料",
    "health_insurance_yen":
        "健康保険料",
    "long_term_care_yen":
        "介護保険料",
    "employment_insurance_yen":
        "雇用保険料",

    "effective_burden_rate":
        "実効負担率",
    "take_home_rate":
        "手取り率",
    "income_tax_rate":
        "所得税負担率",
    "resident_tax_rate":
        "住民税負担率",
    "pension_rate_effective":
        "厚生年金負担率",
    "health_insurance_rate_effective":
        "健康保険負担率",
    "long_term_care_rate_effective":
        "介護保険負担率",
    "employment_insurance_rate_effective":
        "雇用保険負担率",

    # ----------------------------------------
    # 賃金入力
    # ----------------------------------------
    "monthly_total_cash_earnings_yen":
        "月間現金給与総額",
    "monthly_regular_earnings_yen":
        "月例賃金",
    "monthly_special_earnings_yen":
        "月間特別給与",

    # ----------------------------------------
    # 課税所得など
    # ----------------------------------------
    "salary_income_yen":
        "給与所得",
    "taxable_income_yen":
        "所得税課税所得",
    "resident_taxable_income_yen":
        "住民税課税所得",

    # ----------------------------------------
    # 期間別対数分解
    # ----------------------------------------
    "wage_log_contribution_pt":
        "額面賃金要因（対数寄与）",
    "burden_log_contribution_pt":
        "負担率要因（対数寄与）",
    "price_log_contribution_pt":
        "物価要因（対数寄与）",
    "total_log_change_pt":
        "実質手取り総変化（対数）",

    # ----------------------------------------
    # 負担率変化
    # ----------------------------------------
    "total_change_pt":
        "実効負担率変化",
    "wage_effect_pt":
        "賃金要因",
    "policy_effect_pt":
        "制度要因",

    # ----------------------------------------
    # 負担率3要因Shapley
    # ----------------------------------------
    "tax_policy_effect_pt":
        "税制度要因",
    "social_insurance_policy_effect_pt":
        "社会保険制度要因",
    "shapley_sum_pt":
        "Shapley寄与合計",
    "actual_change_pt":
        "実際の変化",

    # ----------------------------------------
    # 実質手取り4要因Shapley：円
    # ----------------------------------------
    "wage_effect_yen":
        "額面賃金要因",
    "tax_policy_effect_yen":
        "税制度要因",
    "social_insurance_policy_effect_yen":
        "社会保険制度要因",
    "price_effect_yen":
        "物価要因",
    "shapley_sum_yen":
        "Shapley寄与合計",
    "actual_change_yen":
        "実質手取り実変化",

    # ----------------------------------------
    # 実質手取り4要因Shapley：開始年比
    # ----------------------------------------
    "wage_effect_pct_of_start":
        "額面賃金要因（開始年実質手取り比）",
    "tax_policy_effect_pct_of_start":
        "税制度要因（開始年実質手取り比）",
    "social_insurance_policy_effect_pct_of_start":
        "社会保険制度要因（開始年実質手取り比）",
    "price_effect_pct_of_start":
        "物価要因（開始年実質手取り比）",
    "shapley_sum_pct_of_start":
        "Shapley寄与合計（開始年比）",
    "actual_change_pct_of_start":
        "実質手取り実変化（開始年比）",

    # ----------------------------------------
    # 固定制度比較
    # ----------------------------------------
    "nominal_take_home_difference_yen":
        "名目手取り差（実際－1990年制度固定）",
    "real_take_home_difference_yen":
        "実質手取り差（実際－1990年制度固定）",
    "burden_rate_difference_pt":
        "実効負担率差（実際－1990年制度固定）",

    # ----------------------------------------
    # 頑健性確認で使用する代表指標
    # ----------------------------------------
    "real_take_home_change_pct":
        "実質手取り変化率",
    "real_gross_salary_change_pct":
        "実質額面賃金変化率",
}

TABLEAU_ANALYSIS_LABELS = {
    "take_home_wage":
        "手取り賃金分析",
}


TABLEAU_RECORD_TYPE_LABELS = {
    "annual_main":
        "年次主系列",
    "period_log_decomposition":
        "期間別対数分解",
    "burden_change":
        "実効負担率変化",
    "burden_shapley":
        "負担率3要因Shapley分解",
    "real_take_home_shapley":
        "実質手取り4要因Shapley分解",
    "fixed_policy_comparison":
        "1990年制度固定比較",
    "robustness":
        "頑健性確認",
}


TABLEAU_UNIT_LABELS = {
    "yen":
        "円",
    "ratio":
        "比率",
    "index":
        "指数",
    "pct":
        "%",
    "pt":
        "ポイント",
    "value":
        "数値",
}


TABLEAU_CHECK_LABELS = {
    "fixed_policy":
        "固定制度比較",
    "resident_tax_timing":
        "住民税対応",
    "resident_timing":
        "住民税対応",
    "sex":
        "性別",
    "age":
        "年齢",
    "long_term_care":
        "介護保険",
    "wage_series":
        "賃金系列",
    "temporary_tax_policy":
        "一時的税制",
    "temporary_tax":
        "一時的税制",
}


TABLEAU_COMPARISON_LABELS = {
    "actual_policy":
        "実際制度",
    "fixed_1990_policy":
        "1990年制度固定",
    "actual_minus_fixed_1990":
        "実際制度－1990年制度固定",

    "income_year":
        "所得年対応",
    "cash_flow":
        "キャッシュフロー対応",

    "male":
        "男性",
    "female":
        "女性",

    "age_35":
        "35歳",
    "age_45":
        "45歳",

    "long_term_level":
        "長期水準系列",
    "chained":
        "接続系列",

    "structural_policy":
        "構造的制度",
}


TABLEAU_SEX_LABELS = {
    "male":
        "男性",
    "female":
        "女性",
}


TABLEAU_RESIDENT_TAX_TIMING_LABELS = {
    "income_year":
        "所得年対応",
    "cash_flow":
        "キャッシュフロー対応",
}


def _insert_tableau_label_column(
    df: pd.DataFrame,
    id_column: str,
    label_column: str,
    labels: dict[str, str],
) -> None:
    """ID列の直後にTableau表示用ラベル列を追加する。"""

    position = (
        df.columns.get_loc(
            id_column
        )
        + 1
    )

    mapped = (
        df[id_column]
        .map(labels)
    )

    mapped = mapped.where(
        mapped.notna(),
        df[id_column],
    )

    df.insert(
        position,
        label_column,
        mapped,
    )


def create_japanese_tableau_export(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Tableau用データを日本語表示向けに整形する。

    英語IDは安定した機械可読キーとして残し、
    人間向けの日本語ラベル列を追加する。
    """

    missing = (
        set(TABLEAU_JAPANESE_COLUMNS)
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Tableau用データに必要な列がありません: "
            f"{sorted(missing)}"
        )

    result = df.rename(
        columns=TABLEAU_JAPANESE_COLUMNS
    ).copy()

    _insert_tableau_label_column(
        result,
        id_column="分析ID",
        label_column="分析",
        labels=TABLEAU_ANALYSIS_LABELS,
    )

    _insert_tableau_label_column(
        result,
        id_column="レコード種別ID",
        label_column="レコード種別",
        labels=TABLEAU_RECORD_TYPE_LABELS,
    )

    _insert_tableau_label_column(
        result,
        id_column="指標ID",
        label_column="指標",
        labels=TABLEAU_METRIC_LABELS,
    )

    _insert_tableau_label_column(
        result,
        id_column="単位ID",
        label_column="単位",
        labels=TABLEAU_UNIT_LABELS,
    )

    _insert_tableau_label_column(
        result,
        id_column="確認項目ID",
        label_column="確認項目",
        labels=TABLEAU_CHECK_LABELS,
    )

    _insert_tableau_label_column(
        result,
        id_column="比較ケースID",
        label_column="比較ケース",
        labels=TABLEAU_COMPARISON_LABELS,
    )

    _insert_tableau_label_column(
        result,
        id_column="モデル性別ID",
        label_column="モデル性別",
        labels=TABLEAU_SEX_LABELS,
    )

    _insert_tableau_label_column(
        result,
        id_column="住民税対応ID",
        label_column="住民税対応",
        labels=(
            TABLEAU_RESIDENT_TAX_TIMING_LABELS
        ),
    )

    return result


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
