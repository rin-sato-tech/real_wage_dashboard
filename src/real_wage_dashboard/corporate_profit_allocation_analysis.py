from __future__ import annotations

import pandas as pd

from real_wage_dashboard.macro_distribution_analysis import (
    add_nonfinancial_capital_account_identity,
)

SNA_IDENTITY_TOLERANCE = 0.5

PRIMARY_INCOME_REQUIRED_COLUMNS = {
    "fiscal_year",
    "net_operating_surplus",
    "property_income_received",
    "property_income_paid",
    "net_primary_income_balance",
    "interest_received",
    "interest_paid",
    "dividends_received",
    "dividends_paid",
    "reinvested_earnings_received",
    "reinvested_earnings_paid",
}

SECONDARY_DISTRIBUTION_REQUIRED_COLUMNS = {
    "fiscal_year",
    "net_primary_income_balance",
    "current_taxes_paid",
    "income_taxes_paid",
    "other_current_taxes_paid",
    "other_social_insurance_nonpension_benefits_paid",
    "other_current_transfers_paid",
    "imputed_employer_social_contributions_received",
    "other_current_transfers_received",
    "net_disposable_income",
}

USE_INCOME_REQUIRED_COLUMNS = {
    "fiscal_year",
    "net_disposable_income",
    "gross_disposable_income",
    "net_saving",
    "gross_saving",
    "consumption_fixed_capital",
}

CUMULATIVE_CAPITAL_ACCOUNT_COLUMNS = [
    "net_saving",
    "net_capital_transfers",
    "net_fixed_capital_formation",
    "changes_in_inventories",
    "net_land_purchases",
    "net_capital_formation",
    "net_lending_capital_account",
]

FINANCIAL_ASSET_COMPONENTS = [
    "monetary_gold_sdr_assets",
    "cash_deposits_assets",
    "loans_assets",
    "debt_securities_assets",
    "equity_investment_fund_assets",
    "insurance_pension_guarantee_assets",
    "financial_derivatives_assets",
    "other_financial_assets",
]

FINANCIAL_LIABILITY_COMPONENTS = [
    "monetary_gold_sdr_liabilities",
    "cash_deposits_liabilities",
    "loans_liabilities",
    "debt_securities_liabilities",
    "equity_investment_fund_liabilities",
    "insurance_pension_guarantee_liabilities",
    "financial_derivatives_liabilities",
    "other_liabilities",
]

FINANCIAL_ACCOUNT_REQUIRED_COLUMNS = {
    "fiscal_year",
    "financial_assets_change",
    "net_lending_financial_account",
    "net_lending_plus_liabilities_change",
    *FINANCIAL_ASSET_COMPONENTS,
    *FINANCIAL_LIABILITY_COMPONENTS,
}

FINANCIAL_ASSET_DISPLAY_NAMES = {
    "monetary_gold_sdr_assets": "貨幣用金・SDR",
    "cash_deposits_assets": "現金・預金",
    "loans_assets": "貸出",
    "debt_securities_assets": "債務証券",
    "equity_investment_fund_assets": "持分・投資信託受益証券",
    "insurance_pension_guarantee_assets": "保険・年金・定型保証",
    "financial_derivatives_assets": "金融派生商品等",
    "other_financial_assets": "その他の金融資産",
}

FINANCIAL_LIABILITY_DISPLAY_NAMES = {
    "monetary_gold_sdr_liabilities": "貨幣用金・SDR",
    "cash_deposits_liabilities": "現金・預金",
    "loans_liabilities": "借入",
    "debt_securities_liabilities": "債務証券",
    "equity_investment_fund_liabilities": "持分・投資信託受益証券",
    "insurance_pension_guarantee_liabilities": "保険・年金・定型保証",
    "financial_derivatives_liabilities": "金融派生商品等",
    "other_liabilities": "その他の負債",
}

STOCK_RECONCILIATION_ITEMS = [
    "nonfinancial_assets",
    "fixed_assets",
    "inventories",
    "land",
    "financial_assets",
    "shares_assets",
    "liabilities",
    "shares_liabilities",
]

CORPORATE_ACCOUNTING_REQUIRED_COLUMNS = {
    "fiscal_year",
    "net_income",
    "total_dividends",
    "cash_deposits_begin",
    "cash_deposits_end",
    "fixed_assets_begin",
    "fixed_assets_end",
    "investment_securities_begin",
    "investment_securities_end",
    "short_term_borrowings_begin",
    "short_term_borrowings_end",
    "long_term_borrowings_begin",
    "long_term_borrowings_end",
    "liabilities_begin",
    "liabilities_end",
    "net_assets_begin",
    "net_assets_end",
    "retained_earnings_begin",
    "retained_earnings_end",
}

CORPORATE_STOCK_BRIDGE_ITEMS = [
    "retained_earnings",
    "cash_deposits",
    "fixed_assets",
    "investment_securities",
    "short_term_borrowings",
    "long_term_borrowings",
    "liabilities",
    "net_assets",
]

def _validate_columns(
    df: pd.DataFrame,
    required_columns: set[str],
    label: str,
) -> None:
    """分析に必要な列が存在することを確認する。"""

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{label}に必要な列がありません: "
            f"{sorted(missing_columns)}"
        )


def add_nonfinancial_primary_income_metrics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """非金融法人企業の第1次所得関連指標を追加する。"""

    _validate_columns(
        df,
        PRIMARY_INCOME_REQUIRED_COLUMNS,
        "非金融法人企業第1次所得分析",
    )

    result = df.copy()

    # 財産所得全体の純受取
    result["net_property_income"] = (
        result["property_income_received"]
        - result["property_income_paid"]
    )

    # 個別財産所得項目
    result["net_interest_income"] = (
        result["interest_received"]
        - result["interest_paid"]
    )

    result["net_dividend_income"] = (
        result["dividends_received"]
        - result["dividends_paid"]
    )

    result["net_dividend_payment"] = (
        result["dividends_paid"]
        - result["dividends_received"]
    )

    result["net_reinvested_earnings_income"] = (
        result["reinvested_earnings_received"]
        - result["reinvested_earnings_paid"]
    )

    # 第1次所得恒等式
    result["calculated_net_primary_income"] = (
        result["net_operating_surplus"]
        + result["net_property_income"]
    )

    result["primary_income_identity_residual"] = (
        result["calculated_net_primary_income"]
        - result["net_primary_income_balance"]
    )

    return result


def validate_nonfinancial_primary_income_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """非金融法人企業の第1次所得恒等式を検証する。"""

    result = add_nonfinancial_primary_income_metrics(df)

    invalid = result[
        result["primary_income_identity_residual"].abs()
        > tolerance
    ]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "net_primary_income_balance",
                "calculated_net_primary_income",
                "primary_income_identity_residual",
            ]
        ].to_dict("records")

        raise ValueError(
            "非金融法人企業の第1次所得恒等式が"
            f"許容誤差を超えています: {details}"
        )


def add_nonfinancial_disposable_income_identity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """第1次所得から純可処分所得を再構成する。"""

    _validate_columns(
        df,
        SECONDARY_DISTRIBUTION_REQUIRED_COLUMNS,
        "非金融法人企業第2次所得分配分析",
    )

    result = df.copy()

    result["net_other_current_transfers"] = (
        result["other_current_transfers_received"]
        - result["other_current_transfers_paid"]
    )

    result["net_social_insurance_transfer"] = (
        result[
            "imputed_employer_social_contributions_received"
        ]
        - result[
            "other_social_insurance_nonpension_benefits_paid"
        ]
    )

    result["calculated_current_taxes"] = (
        result["income_taxes_paid"]
        + result["other_current_taxes_paid"]
    )

    result["current_tax_identity_residual"] = (
        result["calculated_current_taxes"]
        - result["current_taxes_paid"]
    )

    result["calculated_net_disposable_income"] = (
        result["net_primary_income_balance"]
        + result[
            "imputed_employer_social_contributions_received"
        ]
        + result["other_current_transfers_received"]
        - result["current_taxes_paid"]
        - result[
            "other_social_insurance_nonpension_benefits_paid"
        ]
        - result["other_current_transfers_paid"]
    )

    result["disposable_income_identity_residual"] = (
        result["calculated_net_disposable_income"]
        - result["net_disposable_income"]
    )

    return result


def validate_nonfinancial_disposable_income_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """非金融法人企業の純可処分所得恒等式を検証する。"""

    result = add_nonfinancial_disposable_income_identity(df)

    invalid = result[
        result["disposable_income_identity_residual"].abs()
        > tolerance
    ]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "net_disposable_income",
                "calculated_net_disposable_income",
                "disposable_income_identity_residual",
            ]
        ].to_dict("records")

        raise ValueError(
            "非金融法人企業の純可処分所得恒等式が"
            f"許容誤差を超えています: {details}"
        )


def validate_nonfinancial_current_tax_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """経常税の内訳合計を検証する。"""

    result = add_nonfinancial_disposable_income_identity(df)

    invalid = result[
        result["current_tax_identity_residual"].abs()
        > tolerance
    ]

    if not invalid.empty:
        details = invalid[
            [
                "fiscal_year",
                "current_taxes_paid",
                "calculated_current_taxes",
                "current_tax_identity_residual",
            ]
        ].to_dict("records")

        raise ValueError(
            "経常税の内訳合計が許容誤差を超えています: "
            f"{details}"
        )


def add_nonfinancial_saving_identity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """非金融法人企業の可処分所得と貯蓄の関係を検証する。"""

    _validate_columns(
        df,
        USE_INCOME_REQUIRED_COLUMNS,
        "非金融法人企業所得使用分析",
    )

    result = df.copy()

    # 非金融法人企業には最終消費支出がないため、
    # 可処分所得はそのまま貯蓄となる。
    result["calculated_net_saving"] = (
        result["net_disposable_income"]
    )

    result["net_saving_identity_residual"] = (
        result["calculated_net_saving"]
        - result["net_saving"]
    )

    result["calculated_gross_saving"] = (
        result["gross_disposable_income"]
    )

    result["gross_saving_identity_residual"] = (
        result["calculated_gross_saving"]
        - result["gross_saving"]
    )

    # 総額－純額 = 固定資本減耗
    result["disposable_income_gross_net_residual"] = (
        result["gross_disposable_income"]
        - result["net_disposable_income"]
        - result["consumption_fixed_capital"]
    )

    result["saving_gross_net_residual"] = (
        result["gross_saving"]
        - result["net_saving"]
        - result["consumption_fixed_capital"]
    )

    return result


def validate_nonfinancial_saving_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """非金融法人企業の貯蓄恒等式を検証する。"""

    result = add_nonfinancial_saving_identity(df)

    residual_columns = [
        "net_saving_identity_residual",
        "gross_saving_identity_residual",
        "disposable_income_gross_net_residual",
        "saving_gross_net_residual",
    ]

    invalid_mask = (
        result[residual_columns]
        .abs()
        .gt(tolerance)
        .any(axis=1)
    )

    invalid = result.loc[
        invalid_mask,
        ["fiscal_year", *residual_columns],
    ]

    if not invalid.empty:
        raise ValueError(
            "非金融法人企業の貯蓄恒等式が"
            "許容誤差を超えています: "
            f"{invalid.to_dict('records')}"
        )


def calculate_cumulative_capital_account(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2024,
) -> pd.DataFrame:
    """指定期間の非金融法人企業・資本勘定フローを累積する。"""

    if start_year > end_year:
        raise ValueError(
            "開始年度は終了年度以下である必要があります。"
        )

    result = add_nonfinancial_capital_account_identity(
        df
    )

    expected_years = set(
        range(
            start_year,
            end_year + 1,
        )
    )

    actual_years = set(
        result.loc[
            result["fiscal_year"].between(
                start_year,
                end_year,
            ),
            "fiscal_year",
        ]
    )

    missing_years = sorted(
        expected_years - actual_years
    )

    if missing_years:
        raise ValueError(
            "累積分析に必要な年度がありません: "
            f"{missing_years}"
        )

    result = (
        result[
            result["fiscal_year"].between(
                start_year,
                end_year,
            )
        ]
        .sort_values("fiscal_year")
        .reset_index(drop=True)
        .copy()
    )

    if (
        result[
            CUMULATIVE_CAPITAL_ACCOUNT_COLUMNS
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError(
            "累積分析対象の資本勘定に欠損値があります。"
        )

    for column in CUMULATIVE_CAPITAL_ACCOUNT_COLUMNS:
        result[f"cumulative_{column}"] = (
            result[column].cumsum()
        )

    result[
        "cumulative_calculated_net_lending"
    ] = (
        result["cumulative_net_saving"]
        + result["cumulative_net_capital_transfers"]
        - result["cumulative_net_capital_formation"]
    )

    result[
        "cumulative_net_lending_identity_residual"
    ] = (
        result["cumulative_calculated_net_lending"]
        - result[
            "cumulative_net_lending_capital_account"
        ]
    )

    return result


def summarize_cumulative_capital_account(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2024,
) -> pd.DataFrame:
    """指定期間の累積資本勘定を1行に要約する。"""

    cumulative = calculate_cumulative_capital_account(
        df=df,
        start_year=start_year,
        end_year=end_year,
    )

    final = cumulative.iloc[-1]

    cumulative_sources = (
        final["cumulative_net_saving"]
        + final["cumulative_net_capital_transfers"]
    )

    if cumulative_sources <= 0:
        raise ValueError(
            "累積純貯蓄＋純資本移転は"
            "正である必要があります。"
        )

    capital_formation_share = (
        final["cumulative_net_capital_formation"]
        / cumulative_sources
        * 100
    )

    net_lending_share = (
        final[
            "cumulative_net_lending_capital_account"
        ]
        / cumulative_sources
        * 100
    )

    return pd.DataFrame(
        [
            {
                "start_year": start_year,
                "end_year": end_year,
                "cumulative_net_saving": (
                    final["cumulative_net_saving"]
                ),
                "cumulative_net_capital_transfers": (
                    final[
                        "cumulative_net_capital_transfers"
                    ]
                ),
                "cumulative_net_fixed_capital_formation": (
                    final[
                        "cumulative_net_fixed_capital_formation"
                    ]
                ),
                "cumulative_changes_in_inventories": (
                    final[
                        "cumulative_changes_in_inventories"
                    ]
                ),
                "cumulative_net_land_purchases": (
                    final[
                        "cumulative_net_land_purchases"
                    ]
                ),
                "cumulative_net_capital_formation": (
                    final[
                        "cumulative_net_capital_formation"
                    ]
                ),
                "cumulative_net_lending": (
                    final[
                        "cumulative_net_lending_capital_account"
                    ]
                ),
                "cumulative_sources": cumulative_sources,
                "capital_formation_share_pct": (
                    capital_formation_share
                ),
                "net_lending_share_pct": (
                    net_lending_share
                ),
                "identity_residual": (
                    final[
                        "cumulative_net_lending_identity_residual"
                    ]
                ),
            }
        ]
    )


def add_nonfinancial_financial_account_identity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """非金融法人企業の金融勘定恒等式を再構成する。"""

    _validate_columns(
        df,
        FINANCIAL_ACCOUNT_REQUIRED_COLUMNS,
        "非金融法人企業金融勘定分析",
    )

    result = df.copy()

    result["calculated_financial_assets_change"] = (
        result[FINANCIAL_ASSET_COMPONENTS]
        .sum(axis=1)
    )

    result["calculated_liabilities_change"] = (
        result[FINANCIAL_LIABILITY_COMPONENTS]
        .sum(axis=1)
    )

    result["calculated_net_lending_financial"] = (
        result["calculated_financial_assets_change"]
        - result["calculated_liabilities_change"]
    )

    result["financial_assets_identity_residual"] = (
        result["calculated_financial_assets_change"]
        - result["financial_assets_change"]
    )

    result["net_lending_financial_identity_residual"] = (
        result["calculated_net_lending_financial"]
        - result["net_lending_financial_account"]
    )

    result["calculated_net_lending_plus_liabilities"] = (
        result["net_lending_financial_account"]
        + result["calculated_liabilities_change"]
    )

    result["liabilities_side_identity_residual"] = (
        result["calculated_net_lending_plus_liabilities"]
        - result["net_lending_plus_liabilities_change"]
    )

    result["financial_account_total_residual"] = (
        result["financial_assets_change"]
        - result["net_lending_plus_liabilities_change"]
    )

    return result


def validate_nonfinancial_financial_account_identity(
    df: pd.DataFrame,
    tolerance: float = SNA_IDENTITY_TOLERANCE,
) -> None:
    """非金融法人企業の金融勘定恒等式を検証する。"""

    result = add_nonfinancial_financial_account_identity(
        df
    )

    residual_columns = [
        "financial_assets_identity_residual",
        "net_lending_financial_identity_residual",
        "liabilities_side_identity_residual",
        "financial_account_total_residual",
    ]

    invalid_mask = (
        result[residual_columns]
        .abs()
        .gt(tolerance)
        .any(axis=1)
    )

    invalid = result.loc[
        invalid_mask,
        [
            "fiscal_year",
            *residual_columns,
        ],
    ]

    if not invalid.empty:
        raise ValueError(
            "非金融法人企業の金融勘定恒等式が"
            "許容誤差を超えています: "
            f"{invalid.to_dict('records')}"
        )


def calculate_capital_financial_net_lending_discrepancy(
    capital_df: pd.DataFrame,
    financial_df: pd.DataFrame,
) -> pd.DataFrame:
    """資本勘定と金融勘定の純貸出開差を算出する。

    両者は概念上は一致するが、実際のSNAでは
    基礎統計・推計方法の違い等により開差が生じるため、
    一致をvalidation条件とはしない。
    """

    capital = add_nonfinancial_capital_account_identity(
        capital_df
    )

    financial = add_nonfinancial_financial_account_identity(
        financial_df
    )

    result = capital[
        [
            "fiscal_year",
            "net_lending_capital_account",
        ]
    ].merge(
        financial[
            [
                "fiscal_year",
                "net_lending_financial_account",
            ]
        ],
        on="fiscal_year",
        how="outer",
        validate="one_to_one",
    )

    if result.isna().any().any():
        raise ValueError(
            "資本勘定と金融勘定で対象年度が一致しません。"
        )

    result["capital_financial_discrepancy"] = (
        result["net_lending_capital_account"]
        - result["net_lending_financial_account"]
    )

    result["cumulative_capital_net_lending"] = (
        result["net_lending_capital_account"].cumsum()
    )

    result["cumulative_financial_net_lending"] = (
        result["net_lending_financial_account"].cumsum()
    )

    result["cumulative_capital_financial_discrepancy"] = (
        result["capital_financial_discrepancy"].cumsum()
    )

    return result


def calculate_cumulative_financial_account(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2024,
) -> pd.DataFrame:
    """金融資産・負債取引を指定期間で累積する。"""

    if start_year > end_year:
        raise ValueError(
            "開始年度は終了年度以下である必要があります。"
        )

    result = add_nonfinancial_financial_account_identity(
        df
    )

    result = (
        result[
            result["fiscal_year"].between(
                start_year,
                end_year,
            )
        ]
        .sort_values("fiscal_year")
        .reset_index(drop=True)
        .copy()
    )

    expected_years = set(
        range(start_year, end_year + 1)
    )

    actual_years = set(result["fiscal_year"])

    missing_years = sorted(
        expected_years - actual_years
    )

    if missing_years:
        raise ValueError(
            "累積金融勘定分析に必要な年度がありません: "
            f"{missing_years}"
        )

    cumulative_columns = [
        *FINANCIAL_ASSET_COMPONENTS,
        *FINANCIAL_LIABILITY_COMPONENTS,
        "financial_assets_change",
        "calculated_liabilities_change",
        "net_lending_financial_account",
    ]

    if (
        result[cumulative_columns]
        .isna()
        .any()
        .any()
    ):
        raise ValueError(
            "累積金融勘定分析対象に欠損があります。"
        )

    for column in cumulative_columns:
        result[f"cumulative_{column}"] = (
            result[column].cumsum()
        )

    result["cumulative_calculated_net_lending"] = (
        result["cumulative_financial_assets_change"]
        - result["cumulative_calculated_liabilities_change"]
    )

    result["cumulative_financial_identity_residual"] = (
        result["cumulative_calculated_net_lending"]
        - result[
            "cumulative_net_lending_financial_account"
        ]
    )

    return result


def summarize_cumulative_financial_account(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2024,
) -> pd.DataFrame:
    """累積金融勘定を1行に要約する。"""

    cumulative = calculate_cumulative_financial_account(
        df=df,
        start_year=start_year,
        end_year=end_year,
    )

    final = cumulative.iloc[-1]

    row = {
        "start_year": start_year,
        "end_year": end_year,
    }

    for column in FINANCIAL_ASSET_COMPONENTS:
        row[f"cumulative_{column}"] = (
            final[f"cumulative_{column}"]
        )

    for column in FINANCIAL_LIABILITY_COMPONENTS:
        row[f"cumulative_{column}"] = (
            final[f"cumulative_{column}"]
        )

    row["cumulative_financial_assets_change"] = (
        final["cumulative_financial_assets_change"]
    )

    row["cumulative_liabilities_change"] = (
        final["cumulative_calculated_liabilities_change"]
    )

    row["cumulative_net_lending"] = (
        final[
            "cumulative_net_lending_financial_account"
        ]
    )

    row["identity_residual"] = (
        final[
            "cumulative_financial_identity_residual"
        ]
    )

    return pd.DataFrame([row])


def summarize_cumulative_financial_components(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2024,
) -> pd.DataFrame:
    """累積金融取引を純貸出への寄与額としてlong形式に整理する。"""

    cumulative = calculate_cumulative_financial_account(
        df=df,
        start_year=start_year,
        end_year=end_year,
    )

    final = cumulative.iloc[-1]

    rows = []

    for column in FINANCIAL_ASSET_COMPONENTS:
        amount = final[f"cumulative_{column}"]

        rows.append(
            {
                "side": "金融資産",
                "component": column,
                "component_name": (
                    FINANCIAL_ASSET_DISPLAY_NAMES[column]
                ),
                "cumulative_amount": amount,
                # 資産取得は純貸出を増やす
                "net_lending_contribution": amount,
            }
        )

    for column in FINANCIAL_LIABILITY_COMPONENTS:
        amount = final[f"cumulative_{column}"]

        rows.append(
            {
                "side": "負債",
                "component": column,
                "component_name": (
                    FINANCIAL_LIABILITY_DISPLAY_NAMES[column]
                ),
                "cumulative_amount": amount,
                # 負債発生は純貸出を減らす
                "net_lending_contribution": -amount,
            }
        )

    result = pd.DataFrame(rows)

    calculated_net_lending = (
        result["net_lending_contribution"].sum()
    )

    published_net_lending = final[
        "cumulative_net_lending_financial_account"
    ]

    result.attrs["calculated_net_lending"] = (
        calculated_net_lending
    )

    result.attrs["published_net_lending"] = (
        published_net_lending
    )

    result.attrs["identity_residual"] = (
        calculated_net_lending
        - published_net_lending
    )

    return result


def calculate_stock_change_reconciliation(
    balance_sheet_df: pd.DataFrame,
    other_volume_df: pd.DataFrame,
    revaluation_df: pd.DataFrame,
    start_year: int = 2014,
    end_year: int = 2024,
) -> pd.DataFrame:
    """期末ストック変化を取引・その他量的変動・再評価へ分解する。"""

    if start_year >= end_year:
        raise ValueError(
            "開始年は終了年より前である必要があります。"
        )

    balance = balance_sheet_df.set_index(
        "calendar_year"
    )

    missing_stock_years = [
        year
        for year in [start_year, end_year]
        if year not in balance.index
    ]

    if missing_stock_years:
        raise ValueError(
            "期末貸借対照表に必要な年がありません: "
            f"{missing_stock_years}"
        )

    adjustment_start_year = start_year + 1

    other = other_volume_df[
        other_volume_df["calendar_year"].between(
            adjustment_start_year,
            end_year,
        )
    ]

    revaluation = revaluation_df[
        revaluation_df["calendar_year"].between(
            adjustment_start_year,
            end_year,
        )
    ]

    expected_years = set(
        range(
            adjustment_start_year,
            end_year + 1,
        )
    )

    for label, df in [
        ("その他の資産量変動", other),
        ("再評価", revaluation),
    ]:
        actual_years = set(df["calendar_year"])

        missing_years = sorted(
            expected_years - actual_years
        )

        if missing_years:
            raise ValueError(
                f"{label}に必要な年がありません: "
                f"{missing_years}"
            )

    rows = []

    for item in STOCK_RECONCILIATION_ITEMS:
        beginning_stock = balance.loc[
            start_year,
            item,
        ]

        ending_stock = balance.loc[
            end_year,
            item,
        ]

        stock_change = (
            ending_stock - beginning_stock
        )

        other_volume_change = (
            other[item].sum()
        )

        revaluation_change = (
            revaluation[item].sum()
        )

        implied_transactions = (
            stock_change
            - other_volume_change
            - revaluation_change
        )

        rows.append(
            {
                "item": item,
                "start_year": start_year,
                "end_year": end_year,
                "beginning_stock": beginning_stock,
                "ending_stock": ending_stock,
                "stock_change": stock_change,
                "implied_transactions": implied_transactions,
                "other_volume_change": other_volume_change,
                "revaluation": revaluation_change,
                "reconciliation_residual": (
                    stock_change
                    - implied_transactions
                    - other_volume_change
                    - revaluation_change
                ),
            }
        )

    return pd.DataFrame(rows)


def add_corporate_accounting_metrics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """法人企業統計から利益配分・BS変化指標を作成する。"""

    _validate_columns(
        df,
        CORPORATE_ACCOUNTING_REQUIRED_COLUMNS,
        "法人企業統計・利益配分分析",
    )

    result = df.copy()

    # -------------------------
    # 利益配分
    # -------------------------

    result["profit_after_dividends"] = (
        result["net_income"]
        - result["total_dividends"]
    )

    result["calculated_dividend_payout_ratio"] = (
        result["total_dividends"]
        / result["net_income"]
        * 100
    )

    if "published_dividend_payout_ratio" in result.columns:
        result["dividend_payout_ratio_difference"] = (
            result["calculated_dividend_payout_ratio"]
            - result["published_dividend_payout_ratio"]
        )

    # -------------------------
    # BS年度内変化
    # -------------------------

    stock_items = [
        "cash_deposits",
        "fixed_assets",
        "investment_securities",
        "short_term_borrowings",
        "long_term_borrowings",
        "liabilities",
        "net_assets",
        "retained_earnings",
    ]

    for item in stock_items:
        result[f"{item}_change"] = (
            result[f"{item}_end"]
            - result[f"{item}_begin"]
        )

    # -------------------------
    # 利益剰余金ブリッジ
    # -------------------------

    result["retained_earnings_bridge_residual"] = (
        result["retained_earnings_change"]
        - result["profit_after_dividends"]
    )

    return result


def calculate_corporate_stock_continuity(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2024,
) -> pd.DataFrame:
    """法人企業統計の年度内BS変化と年度間不連続を分離する。"""

    if start_year > end_year:
        raise ValueError(
            "開始年度は終了年度以下である必要があります。"
        )

    result = (
        df[
            df["fiscal_year"].between(
                start_year,
                end_year,
            )
        ]
        .sort_values("fiscal_year")
        .reset_index(drop=True)
        .copy()
    )

    expected_years = list(
        range(start_year, end_year + 1)
    )

    if result["fiscal_year"].tolist() != expected_years:
        raise ValueError(
            "分析対象年度が連続していません。"
        )

    rows = []

    for item in CORPORATE_STOCK_BRIDGE_ITEMS:
        begin_column = f"{item}_begin"
        end_column = f"{item}_end"

        required = {
            begin_column,
            end_column,
        }

        missing = required - set(result.columns)

        if missing:
            raise ValueError(
                f"{item}に必要な列がありません: "
                f"{sorted(missing)}"
            )

        annual_changes = (
            result[end_column]
            - result[begin_column]
        )

        cumulative_within_year_change = (
            annual_changes.sum()
        )

        interyear_discontinuity = 0.0

        for index in range(1, len(result)):
            current_begin = result.loc[
                index,
                begin_column,
            ]

            previous_end = result.loc[
                index - 1,
                end_column,
            ]

            interyear_discontinuity += (
                current_begin
                - previous_end
            )

        endpoint_change = (
            result.iloc[-1][end_column]
            - result.iloc[0][begin_column]
        )

        calculated_endpoint_change = (
            cumulative_within_year_change
            + interyear_discontinuity
        )

        rows.append(
            {
                "item": item,
                "start_year": start_year,
                "end_year": end_year,
                "start_stock": (
                    result.iloc[0][begin_column]
                ),
                "end_stock": (
                    result.iloc[-1][end_column]
                ),
                "endpoint_change": endpoint_change,
                "cumulative_within_year_change": (
                    cumulative_within_year_change
                ),
                "interyear_discontinuity": (
                    interyear_discontinuity
                ),
                "calculated_endpoint_change": (
                    calculated_endpoint_change
                ),
                "reconciliation_residual": (
                    calculated_endpoint_change
                    - endpoint_change
                ),
            }
        )

    return pd.DataFrame(rows)


def summarize_corporate_retained_earnings_bridge(
    df: pd.DataFrame,
    start_year: int = 2015,
    end_year: int = 2024,
) -> pd.DataFrame:
    """純利益・配当から利益剰余金ストック増加への橋渡しを整理する。"""

    metrics = add_corporate_accounting_metrics(df)

    metrics = (
        metrics[
            metrics["fiscal_year"].between(
                start_year,
                end_year,
            )
        ]
        .sort_values("fiscal_year")
        .reset_index(drop=True)
    )

    continuity = calculate_corporate_stock_continuity(
        df,
        start_year=start_year,
        end_year=end_year,
    )

    retained = continuity.loc[
        continuity["item"] == "retained_earnings"
    ].iloc[0]

    cumulative_net_income = (
        metrics["net_income"].sum()
    )

    cumulative_dividends = (
        metrics["total_dividends"].sum()
    )

    cumulative_profit_after_dividends = (
        metrics["profit_after_dividends"].sum()
    )

    cumulative_bridge_residual = (
        metrics[
            "retained_earnings_bridge_residual"
        ].sum()
    )

    endpoint_change = retained[
        "endpoint_change"
    ]

    interyear_discontinuity = retained[
        "interyear_discontinuity"
    ]

    calculated_endpoint_change = (
        cumulative_profit_after_dividends
        + cumulative_bridge_residual
        + interyear_discontinuity
    )

    return pd.DataFrame(
        [
            {
                "start_year": start_year,
                "end_year": end_year,
                "cumulative_net_income": (
                    cumulative_net_income
                ),
                "cumulative_dividends": (
                    cumulative_dividends
                ),
                "cumulative_profit_after_dividends": (
                    cumulative_profit_after_dividends
                ),
                "cumulative_bridge_residual": (
                    cumulative_bridge_residual
                ),
                "cumulative_within_year_retained_earnings_change": (
                    retained[
                        "cumulative_within_year_change"
                    ]
                ),
                "interyear_discontinuity": (
                    interyear_discontinuity
                ),
                "endpoint_retained_earnings_change": (
                    endpoint_change
                ),
                "calculated_endpoint_change": (
                    calculated_endpoint_change
                ),
                "reconciliation_residual": (
                    calculated_endpoint_change
                    - endpoint_change
                ),
            }
        ]
    )
