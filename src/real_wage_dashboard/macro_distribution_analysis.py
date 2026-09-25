from __future__ import annotations

import pandas as pd

SNA_IDENTITY_TOLERANCE = 0.5
SNA_RATE_TOLERANCE = 0.051

INCOME_GENERATION_REQUIRED_COLUMNS = {
    "fiscal_year",
    "employee_compensation",
    "gross_domestic_product",
    "gross_operating_surplus",
    "gross_mixed_income",
    "taxes_on_production_and_imports",
    "subsidies",
}

HOUSEHOLD_PRIMARY_INCOME_REQUIRED_COLUMNS = {
    "fiscal_year",
    "net_primary_income_balance",
    "net_operating_surplus_mixed_income",
    "employee_compensation_received",
    "property_income_received",
    "property_income_paid",
}

HOUSEHOLD_SECONDARY_DISTRIBUTION_REQUIRED_COLUMNS = {
    "fiscal_year",
    "net_primary_income_balance",
    "current_taxes_paid",
    "net_social_contributions_paid",
    "other_current_transfers_paid",
    "social_benefits_received",
    "other_current_transfers_received",
    "net_disposable_income",
}

HOUSEHOLD_USE_INCOME_REQUIRED_COLUMNS = {
    "fiscal_year",
    "household_final_consumption",
    "net_saving",
    "net_disposable_income",
    "pension_entitlement_adjustment",
    "published_saving_rate",
}

SECTOR_NET_LENDING_AMOUNT_COLUMNS = [
    "capital_nonfinancial_corporations",
    "capital_financial_corporations",
    "capital_general_government",
    "capital_households",
    "capital_npish",
    "capital_rest_of_world",
    "statistical_discrepancy",
    "financial_nonfinancial_corporations",
    "financial_financial_corporations",
    "financial_general_government",
    "financial_households",
    "financial_npish",
    "financial_rest_of_world",
]

CAPITAL_NET_LENDING_COLUMNS = [
    "capital_nonfinancial_corporations",
    "capital_financial_corporations",
    "capital_general_government",
    "capital_households",
    "capital_npish",
    "capital_rest_of_world",
]

FINANCIAL_NET_LENDING_COLUMNS = [
    "financial_nonfinancial_corporations",
    "financial_financial_corporations",
    "financial_general_government",
    "financial_households",
    "financial_npish",
    "financial_rest_of_world",
]

SECTOR_NET_LENDING_PAIRS = {
    "nonfinancial_corporations": (
        "capital_nonfinancial_corporations",
        "financial_nonfinancial_corporations",
    ),
    "financial_corporations": (
        "capital_financial_corporations",
        "financial_financial_corporations",
    ),
    "general_government": (
        "capital_general_government",
        "financial_general_government",
    ),
    "households": (
        "capital_households",
        "financial_households",
    ),
    "npish": (
        "capital_npish",
        "financial_npish",
    ),
    "rest_of_world": (
        "capital_rest_of_world",
        "financial_rest_of_world",
    ),
}

SECTOR_DISPLAY_NAMES = {
    "nonfinancial_corporations": "非金融法人企業",
    "financial_corporations": "金融機関",
    "general_government": "一般政府",
    "households": "家計",
    "npish": "対家計民間非営利団体",
    "rest_of_world": "海外部門",
}

NONFINANCIAL_CAPITAL_ACCOUNT_REQUIRED_COLUMNS = {
    "fiscal_year",
    "gross_fixed_capital_formation",
    "consumption_fixed_capital",
    "changes_in_inventories",
    "net_land_purchases",
    "net_lending_capital_account",
    "net_saving",
    "capital_transfers_received",
    "capital_transfers_paid",
}


def validate_income_generation_columns(
    df: pd.DataFrame,
) -> None:
    """所得発生分析に必要な列が存在することを確認する。"""
    missing_columns = INCOME_GENERATION_REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"所得発生分析に必要な列がありません: {sorted(missing_columns)}"
        )


def add_income_generation_identity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """GDP所得面恒等式の再構成値と残差を追加する。"""
    validate_income_generation_columns(df)

    result = df.copy()

    result["net_taxes_on_production_and_imports"] = (
        result["taxes_on_production_and_imports"] - result["subsidies"]
    )

    result["calculated_gdp"] = (
        result["employee_compensation"]
        + result["gross_operating_surplus"]
        + result["gross_mixed_income"]
        + result["net_taxes_on_production_and_imports"]
    )

    result["gdp_identity_residual"] = (
        result["calculated_gdp"] - result["gross_domestic_product"]
    )

    return result


def validate_income_generation_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """GDP所得面恒等式が許容誤差内で成立することを確認する。"""
    result = add_income_generation_identity(df)

    invalid = result[result["gdp_identity_residual"].abs() > tolerance]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "gross_domestic_product",
                "calculated_gdp",
                "gdp_identity_residual",
            ]
        ].to_dict("records")

        raise ValueError(f"GDP所得面恒等式が許容誤差を超えています: {details}")


def calculate_income_generation_shares(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """GDPに占める所得発生各項目の比率を算出する。"""
    result = add_income_generation_identity(df)

    gdp = result["gross_domestic_product"]

    if gdp.isna().any():
        raise ValueError("GDPに欠損値があります。")

    if (gdp <= 0).any():
        invalid_years = result.loc[
            gdp <= 0,
            "fiscal_year",
        ].tolist()

        raise ValueError(f"GDPは正である必要があります: {invalid_years}")

    result["employee_compensation_share"] = result["employee_compensation"] / gdp * 100

    result["gross_operating_surplus_share"] = (
        result["gross_operating_surplus"] / gdp * 100
    )

    result["gross_mixed_income_share"] = result["gross_mixed_income"] / gdp * 100

    result["net_production_tax_share"] = (
        result["net_taxes_on_production_and_imports"] / gdp * 100
    )

    result["income_component_share_sum"] = (
        result["employee_compensation_share"]
        + result["gross_operating_surplus_share"]
        + result["gross_mixed_income_share"]
        + result["net_production_tax_share"]
    )

    return result


def validate_household_primary_income_columns(
    df: pd.DataFrame,
) -> None:
    """家計第1次所得分析に必要な列を確認する。"""
    missing_columns = HOUSEHOLD_PRIMARY_INCOME_REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"家計第1次所得分析に必要な列がありません: {sorted(missing_columns)}"
        )


def add_household_primary_income_identity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """家計第1次所得の再構成値と恒等式残差を追加する。"""
    validate_household_primary_income_columns(df)

    result = df.copy()

    result["net_property_income"] = (
        result["property_income_received"] - result["property_income_paid"]
    )

    result["calculated_net_primary_income"] = (
        result["net_operating_surplus_mixed_income"]
        + result["employee_compensation_received"]
        + result["net_property_income"]
    )

    result["primary_income_identity_residual"] = (
        result["calculated_net_primary_income"] - result["net_primary_income_balance"]
    )

    return result


def validate_household_primary_income_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """家計第1次所得恒等式が許容誤差内で成立することを確認する。"""
    result = add_household_primary_income_identity(df)

    invalid = result[result["primary_income_identity_residual"].abs() > tolerance]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "net_primary_income_balance",
                "calculated_net_primary_income",
                "primary_income_identity_residual",
            ]
        ].to_dict("records")

        raise ValueError(f"家計第1次所得恒等式が許容誤差を超えています: {details}")


def calculate_household_primary_income_components(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """家計第1次所得に対する主要所得項目の比率を算出する。"""
    result = add_household_primary_income_identity(df)

    primary_income = result["net_primary_income_balance"]

    if primary_income.isna().any():
        raise ValueError("家計第1次所得に欠損値があります。")

    if (primary_income <= 0).any():
        invalid_years = result.loc[
            primary_income <= 0,
            "fiscal_year",
        ].tolist()

        raise ValueError(f"家計第1次所得は正である必要があります: {invalid_years}")

    result["employee_compensation_ratio"] = (
        result["employee_compensation_received"] / primary_income * 100
    )

    result["operating_mixed_income_ratio"] = (
        result["net_operating_surplus_mixed_income"] / primary_income * 100
    )

    result["net_property_income_ratio"] = (
        result["net_property_income"] / primary_income * 100
    )

    result["primary_income_component_ratio_sum"] = (
        result["employee_compensation_ratio"]
        + result["operating_mixed_income_ratio"]
        + result["net_property_income_ratio"]
    )

    return result


def validate_household_secondary_distribution_columns(
    df: pd.DataFrame,
) -> None:
    """家計第2次所得分配分析に必要な列を確認する。"""
    missing_columns = HOUSEHOLD_SECONDARY_DISTRIBUTION_REQUIRED_COLUMNS - set(
        df.columns
    )

    if missing_columns:
        raise ValueError(
            f"家計第2次所得分配分析に必要な列がありません: {sorted(missing_columns)}"
        )


def add_household_disposable_income_identity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """第1次所得から可処分所得を再構成し、恒等式残差を追加する。"""
    validate_household_secondary_distribution_columns(df)

    result = df.copy()

    result["net_other_current_transfers"] = (
        result["other_current_transfers_received"]
        - result["other_current_transfers_paid"]
    )

    result["calculated_net_disposable_income"] = (
        result["net_primary_income_balance"]
        - result["current_taxes_paid"]
        - result["net_social_contributions_paid"]
        + result["social_benefits_received"]
        + result["net_other_current_transfers"]
    )

    result["disposable_income_identity_residual"] = (
        result["calculated_net_disposable_income"] - result["net_disposable_income"]
    )

    return result


def validate_household_disposable_income_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """可処分所得恒等式が許容誤差内で成立することを確認する。"""
    result = add_household_disposable_income_identity(df)

    invalid = result[result["disposable_income_identity_residual"].abs() > tolerance]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "net_disposable_income",
                "calculated_net_disposable_income",
                "disposable_income_identity_residual",
            ]
        ].to_dict("records")

        raise ValueError(f"家計可処分所得恒等式が許容誤差を超えています: {details}")


def calculate_household_redistribution_components(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """第1次所得から可処分所得への各再分配項目を比率化する。"""
    result = add_household_disposable_income_identity(df)

    primary_income = result["net_primary_income_balance"]

    if primary_income.isna().any():
        raise ValueError("家計第1次所得に欠損値があります。")

    if (primary_income <= 0).any():
        invalid_years = result.loc[
            primary_income <= 0,
            "fiscal_year",
        ].tolist()

        raise ValueError(f"家計第1次所得は正である必要があります: {invalid_years}")

    result["current_taxes_ratio"] = result["current_taxes_paid"] / primary_income * 100

    result["net_social_contributions_ratio"] = (
        result["net_social_contributions_paid"] / primary_income * 100
    )

    result["social_benefits_ratio"] = (
        result["social_benefits_received"] / primary_income * 100
    )

    result["net_other_current_transfers_ratio"] = (
        result["net_other_current_transfers"] / primary_income * 100
    )

    result["disposable_income_to_primary_income_ratio"] = (
        result["net_disposable_income"] / primary_income * 100
    )

    result["net_redistribution"] = (
        result["net_disposable_income"] - result["net_primary_income_balance"]
    )

    result["net_redistribution_ratio"] = (
        result["net_redistribution"] / primary_income * 100
    )

    return result


def validate_household_use_income_columns(
    df: pd.DataFrame,
) -> None:
    """家計所得使用分析に必要な列を確認する。"""
    missing_columns = HOUSEHOLD_USE_INCOME_REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"家計所得使用分析に必要な列がありません: {sorted(missing_columns)}"
        )


def add_household_saving_identity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """可処分所得から純貯蓄を再構成し、恒等式残差を追加する。"""
    validate_household_use_income_columns(df)

    result = df.copy()

    result["adjusted_disposable_income"] = (
        result["net_disposable_income"] + result["pension_entitlement_adjustment"]
    )

    result["calculated_net_saving"] = (
        result["adjusted_disposable_income"] - result["household_final_consumption"]
    )

    result["saving_identity_residual"] = (
        result["calculated_net_saving"] - result["net_saving"]
    )

    return result


def validate_household_saving_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """家計純貯蓄恒等式が許容誤差内で成立することを確認する。"""
    result = add_household_saving_identity(df)

    invalid = result[result["saving_identity_residual"].abs() > tolerance]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "net_saving",
                "calculated_net_saving",
                "saving_identity_residual",
            ]
        ].to_dict("records")

        raise ValueError(f"家計純貯蓄恒等式が許容誤差を超えています: {details}")


def calculate_household_saving_metrics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """家計貯蓄率など所得使用に関する指標を算出する。"""
    result = add_household_saving_identity(df)

    denominator = result["adjusted_disposable_income"]

    if denominator.isna().any():
        raise ValueError("調整後可処分所得に欠損値があります。")

    if (denominator <= 0).any():
        invalid_years = result.loc[
            denominator <= 0,
            "fiscal_year",
        ].tolist()

        raise ValueError(f"調整後可処分所得は正である必要があります: {invalid_years}")

    result["calculated_saving_rate"] = result["net_saving"] / denominator * 100

    result["saving_rate_difference"] = (
        result["calculated_saving_rate"] - result["published_saving_rate"]
    )

    result["consumption_ratio"] = (
        result["household_final_consumption"] / denominator * 100
    )

    result["saving_consumption_ratio_sum"] = (
        result["calculated_saving_rate"] + result["consumption_ratio"]
    )

    return result


def validate_published_saving_rate(
    df: pd.DataFrame,
    tolerance: float = SNA_RATE_TOLERANCE,
) -> None:
    """再計算した家計貯蓄率と公表値を照合する。"""
    result = calculate_household_saving_metrics(df)

    invalid = result[result["saving_rate_difference"].abs() > tolerance]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "published_saving_rate",
                "calculated_saving_rate",
                "saving_rate_difference",
            ]
        ].to_dict("records")

        raise ValueError(
            f"家計貯蓄率の再計算値と公表値の差が許容範囲を超えています: {details}"
        )


def calculate_sector_net_lending_ratios(
    amount_df: pd.DataFrame,
    income_generation_df: pd.DataFrame,
) -> pd.DataFrame:
    """純貸出・純借入金額から公表定義に沿ったGDP比を再計算する。"""
    required_amount_columns = {
        "fiscal_year",
        *SECTOR_NET_LENDING_AMOUNT_COLUMNS,
    }

    missing_amount = required_amount_columns - set(amount_df.columns)

    if missing_amount:
        raise ValueError(
            f"制度部門別純貸出金額に必要な列がありません: {sorted(missing_amount)}"
        )

    required_gdp_columns = {
        "fiscal_year",
        "gross_domestic_product",
    }

    missing_gdp = required_gdp_columns - set(income_generation_df.columns)

    if missing_gdp:
        raise ValueError(f"GDPデータに必要な列がありません: {sorted(missing_gdp)}")

    result = amount_df.merge(
        income_generation_df[
            [
                "fiscal_year",
                "gross_domestic_product",
            ]
        ],
        on="fiscal_year",
        how="left",
        validate="one_to_one",
    )

    if result["gross_domestic_product"].isna().any():
        missing_years = result.loc[
            result["gross_domestic_product"].isna(),
            "fiscal_year",
        ].tolist()

        raise ValueError(f"GDPを結合できない年度があります: {missing_years}")

    # 所得発生勘定のGDPは生産・分配側。
    # 純貸出/GDPの公表値は支出側GDPを分母としているため、
    # 統計上の不突合を加えて支出側GDPを再構成する。
    result["expenditure_side_gdp"] = (
        result["gross_domestic_product"] + result["statistical_discrepancy"]
    )

    if (result["expenditure_side_gdp"] <= 0).any():
        invalid_years = result.loc[
            result["expenditure_side_gdp"] <= 0,
            "fiscal_year",
        ].tolist()

        raise ValueError(f"支出側GDPは正である必要があります: {invalid_years}")

    for column in SECTOR_NET_LENDING_AMOUNT_COLUMNS:
        result[column] = result[column] / result["expenditure_side_gdp"] * 100

    return result


def compare_sector_net_lending_ratios(
    amount_df: pd.DataFrame,
    published_ratio_df: pd.DataFrame,
    income_generation_df: pd.DataFrame,
) -> pd.DataFrame:
    """再計算GDP比と公表GDP比の差を算出する。"""
    calculated = calculate_sector_net_lending_ratios(
        amount_df=amount_df,
        income_generation_df=income_generation_df,
    )

    result = calculated[["fiscal_year"]].copy()

    for column in SECTOR_NET_LENDING_AMOUNT_COLUMNS:
        result[f"{column}_calculated"] = calculated[column]

        result[f"{column}_published"] = (
            published_ratio_df.set_index("fiscal_year")
            .loc[
                calculated["fiscal_year"],
                column,
            ]
            .to_numpy()
        )

        result[f"{column}_difference"] = (
            result[f"{column}_calculated"] - result[f"{column}_published"]
        )

    return result


def validate_sector_net_lending_ratios(
    amount_df: pd.DataFrame,
    published_ratio_df: pd.DataFrame,
    income_generation_df: pd.DataFrame,
    tolerance: float = SNA_RATE_TOLERANCE,
) -> None:
    """金額から再計算したGDP比と公表GDP比を照合する。"""
    result = compare_sector_net_lending_ratios(
        amount_df=amount_df,
        published_ratio_df=published_ratio_df,
        income_generation_df=income_generation_df,
    )

    difference_columns = [
        column for column in result.columns if column.endswith("_difference")
    ]

    max_difference = result[difference_columns].abs().max().max()

    if max_difference > tolerance:
        raise ValueError(
            "制度部門別純貸出のGDP比が"
            "公表値と許容範囲を超えて異なります: "
            f"max_difference={max_difference}"
        )


def add_sector_net_lending_balance_checks(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """制度部門別純貸出の部門間合計残差を追加する。"""
    result = df.copy()

    result["capital_account_balance_residual"] = (
        result[CAPITAL_NET_LENDING_COLUMNS].sum(axis=1)
        + result["statistical_discrepancy"]
    )

    result["financial_account_balance_residual"] = result[
        FINANCIAL_NET_LENDING_COLUMNS
    ].sum(axis=1)

    return result


def validate_sector_net_lending_balances(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """資本勘定・金融勘定の部門間合計を検証する。"""
    result = add_sector_net_lending_balance_checks(df)

    for column in [
        "capital_account_balance_residual",
        "financial_account_balance_residual",
    ]:
        invalid = result[result[column].abs() > tolerance]

        if not invalid.empty:
            details = invalid[
                [
                    "fiscal_year",
                    column,
                ]
            ].to_dict("records")

            raise ValueError(
                f"制度部門別純貸出の会計整合性が許容誤差を超えています: {details}"
            )


def calculate_capital_financial_discrepancies(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """資本勘定側と金融勘定側の純貸出差を算出する。"""
    result = df[["fiscal_year"]].copy()

    for sector, (
        capital_column,
        financial_column,
    ) in SECTOR_NET_LENDING_PAIRS.items():
        result[f"{sector}_difference"] = df[capital_column] - df[financial_column]

    result["difference_sum"] = result[
        [f"{sector}_difference" for sector in SECTOR_NET_LENDING_PAIRS]
    ].sum(axis=1)

    result["statistical_discrepancy"] = df["statistical_discrepancy"]

    result["discrepancy_reconciliation_residual"] = (
        result["difference_sum"] + result["statistical_discrepancy"]
    )

    return result


def validate_capital_financial_reconciliation(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """資本・金融勘定差と統計上の不突合の整合性を確認する。"""
    result = calculate_capital_financial_discrepancies(df)

    invalid = result[result["discrepancy_reconciliation_residual"].abs() > tolerance]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "difference_sum",
                "statistical_discrepancy",
                "discrepancy_reconciliation_residual",
            ]
        ].to_dict("records")

        raise ValueError(
            f"資本勘定・金融勘定差と統計上の不突合が整合しません: {details}"
        )


def prepare_sector_net_lending_long(
    amount_df: pd.DataFrame,
    ratio_df: pd.DataFrame,
) -> pd.DataFrame:
    """制度部門別純貸出を分析用long形式へ変換する。"""
    rows = []

    amount_indexed = amount_df.set_index("fiscal_year")
    ratio_indexed = ratio_df.set_index("fiscal_year")

    for fiscal_year in amount_indexed.index:
        for sector, (
            capital_column,
            financial_column,
        ) in SECTOR_NET_LENDING_PAIRS.items():
            capital_amount = amount_indexed.loc[
                fiscal_year,
                capital_column,
            ]

            financial_amount = amount_indexed.loc[
                fiscal_year,
                financial_column,
            ]

            rows.append(
                {
                    "fiscal_year": fiscal_year,
                    "sector": sector,
                    "sector_name": SECTOR_DISPLAY_NAMES[sector],
                    "capital_net_lending": capital_amount,
                    "financial_net_lending": financial_amount,
                    "capital_net_lending_ratio": (
                        ratio_indexed.loc[
                            fiscal_year,
                            capital_column,
                        ]
                    ),
                    "financial_net_lending_ratio": (
                        ratio_indexed.loc[
                            fiscal_year,
                            financial_column,
                        ]
                    ),
                    "capital_financial_difference": (capital_amount - financial_amount),
                }
            )

    return pd.DataFrame(rows)


def validate_nonfinancial_capital_account_columns(
    df: pd.DataFrame,
) -> None:
    """非金融法人企業の資本勘定分析に必要な列を確認する。"""
    missing_columns = NONFINANCIAL_CAPITAL_ACCOUNT_REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            "非金融法人企業の資本勘定分析に必要な列がありません: "
            f"{sorted(missing_columns)}"
        )


def add_nonfinancial_capital_account_identity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """純資本形成・純資本移転と純貸出恒等式を追加する。"""
    validate_nonfinancial_capital_account_columns(df)

    result = df.copy()

    result["net_fixed_capital_formation"] = (
        result["gross_fixed_capital_formation"] - result["consumption_fixed_capital"]
    )

    result["net_capital_formation"] = (
        result["net_fixed_capital_formation"]
        + result["changes_in_inventories"]
        + result["net_land_purchases"]
    )

    result["net_capital_transfers"] = (
        result["capital_transfers_received"] - result["capital_transfers_paid"]
    )

    result["calculated_net_lending"] = (
        result["net_saving"]
        + result["net_capital_transfers"]
        - result["net_capital_formation"]
    )

    result["net_lending_identity_residual"] = (
        result["calculated_net_lending"] - result["net_lending_capital_account"]
    )

    return result


def validate_nonfinancial_capital_account_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """非金融法人企業の資本勘定恒等式を検証する。"""
    result = add_nonfinancial_capital_account_identity(df)

    invalid = result[result["net_lending_identity_residual"].abs() > tolerance]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "net_lending_capital_account",
                "calculated_net_lending",
                "net_lending_identity_residual",
            ]
        ].to_dict("records")

        raise ValueError(
            f"非金融法人企業の資本勘定恒等式が許容誤差を超えています: {details}"
        )


def calculate_nonfinancial_capital_account_metrics(
    df: pd.DataFrame,
    income_generation_df: pd.DataFrame,
    statistical_discrepancy_df: pd.DataFrame,
) -> pd.DataFrame:
    """非金融法人企業の資本勘定をGDP比へ変換する。"""
    result = add_nonfinancial_capital_account_identity(df)

    gdp = income_generation_df[
        [
            "fiscal_year",
            "gross_domestic_product",
        ]
    ].copy()

    discrepancy = statistical_discrepancy_df[
        [
            "fiscal_year",
            "statistical_discrepancy",
        ]
    ].copy()

    result = result.merge(
        gdp,
        on="fiscal_year",
        how="left",
        validate="one_to_one",
    )

    result = result.merge(
        discrepancy,
        on="fiscal_year",
        how="left",
        validate="one_to_one",
    )

    if (
        result[
            [
                "gross_domestic_product",
                "statistical_discrepancy",
            ]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("支出側GDPの計算に必要なデータが欠けています。")

    result["expenditure_side_gdp"] = (
        result["gross_domestic_product"] + result["statistical_discrepancy"]
    )

    if (result["expenditure_side_gdp"] <= 0).any():
        raise ValueError("支出側GDPは正である必要があります。")

    ratio_columns = [
        "net_saving",
        "net_capital_transfers",
        "net_fixed_capital_formation",
        "changes_in_inventories",
        "net_land_purchases",
        "net_capital_formation",
        "net_lending_capital_account",
    ]

    for column in ratio_columns:
        result[f"{column}_ratio"] = (
            result[column] / result["expenditure_side_gdp"] * 100
        )

    return result


def decompose_net_lending_change(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """非金融法人企業の純貸出GDP比変化を恒等分解する。"""
    required_columns = {
        "fiscal_year",
        "net_saving_ratio",
        "net_capital_transfers_ratio",
        "net_capital_formation_ratio",
        "net_lending_capital_account_ratio",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"純貸出変化分解に必要な列がありません: {sorted(missing_columns)}"
        )

    indexed = df.set_index("fiscal_year")

    missing_years = [
        year for year in [start_year, end_year] if year not in indexed.index
    ]

    if missing_years:
        raise ValueError(f"比較年度がありません: {missing_years}")

    start = indexed.loc[start_year]
    end = indexed.loc[end_year]

    saving_effect = end["net_saving_ratio"] - start["net_saving_ratio"]

    capital_transfer_effect = (
        end["net_capital_transfers_ratio"] - start["net_capital_transfers_ratio"]
    )

    capital_formation_effect = -(
        end["net_capital_formation_ratio"] - start["net_capital_formation_ratio"]
    )

    actual_change = (
        end["net_lending_capital_account_ratio"]
        - start["net_lending_capital_account_ratio"]
    )

    calculated_change = (
        saving_effect + capital_transfer_effect + capital_formation_effect
    )

    return pd.DataFrame(
        {
            "component": [
                "net_saving",
                "net_capital_transfers",
                "net_capital_formation",
            ],
            "contribution_pt": [
                saving_effect,
                capital_transfer_effect,
                capital_formation_effect,
            ],
            "start_year": start_year,
            "end_year": end_year,
            "actual_change_pt": actual_change,
            "calculated_change_pt": calculated_change,
            "decomposition_residual": (calculated_change - actual_change),
        }
    )


def validate_nonfinancial_net_lending_crosscheck(
    capital_account_df: pd.DataFrame,
    sector_net_lending_df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """非金融法人企業の純貸出を個別資本勘定と制度部門表で照合する。"""
    comparison = capital_account_df[
        [
            "fiscal_year",
            "net_lending_capital_account",
        ]
    ].merge(
        sector_net_lending_df[
            [
                "fiscal_year",
                "capital_nonfinancial_corporations",
            ]
        ],
        on="fiscal_year",
        how="outer",
        validate="one_to_one",
    )

    if comparison.isna().any().any():
        raise ValueError("非金融法人企業の純貸出照合に必要な年度が一致しません。")

    comparison["difference"] = (
        comparison["net_lending_capital_account"]
        - comparison["capital_nonfinancial_corporations"]
    )

    invalid = comparison[comparison["difference"].abs() > tolerance]

    if not invalid.empty:
        raise ValueError(
            "非金融法人企業の純貸出が制度部門表と一致しません: "
            f"{invalid.to_dict('records')}"
        )
