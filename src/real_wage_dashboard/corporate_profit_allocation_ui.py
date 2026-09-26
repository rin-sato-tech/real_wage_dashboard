from __future__ import annotations

import altair as alt
import pandas as pd


INCOME_CHAIN_LABELS = {
    "net_operating_surplus": "純営業余剰",
    "net_primary_income_balance": "純第1次所得",
    "net_saving": "純貯蓄",
}

STOCK_RECONCILIATION_LABELS = {
    "nonfinancial_assets": "非金融資産",
    "fixed_assets": "固定資産",
    "inventories": "在庫",
    "land": "土地",
    "financial_assets": "金融資産",
    "shares_assets": "金融資産のうち株式",
    "liabilities": "負債",
    "shares_liabilities": "負債のうち株式",
}

CORPORATE_STOCK_LABELS = {
    "retained_earnings": "利益剰余金",
    "cash_deposits": "現金・預金",
    "fixed_assets": "固定資産",
    "investment_securities": "投資有価証券",
    "short_term_borrowings": "短期借入金",
    "long_term_borrowings": "長期借入金",
    "liabilities": "負債",
    "net_assets": "純資産",
}

FINANCIAL_ASSET_DETAIL_LABELS = {
    "cash_deposits_assets": "現金・預金",
    "loans_assets": "貸出",
    "debt_securities_assets": "債務証券",
    "equity_investment_fund_assets": "持分・投資信託",
    "insurance_pension_guarantee_assets": "保険・年金等",
    "financial_derivatives_assets": "金融派生商品等",
    "fiscal_investment_fund_deposits_assets": "財政融資資金預託金",
    "entrusted_funds_assets": "預け金",
    "trade_credit_assets": "企業間・貿易信用",
    "accounts_receivable_assets": "未収金",
    "direct_investment_assets": "直接投資",
    "foreign_portfolio_investment_assets": "対外証券投資",
    "other_external_claims_assets": "その他対外債権",
    "other_assets": "その他",
}

FINANCIAL_COMPONENT_SHORT_LABELS = {
    "持分・投資信託受益証券": "持分・投資信託",
    "保険・年金・定型保証": "保険・年金等",
}


def create_income_chain_chart(df: pd.DataFrame) -> alt.Chart:
    """非金融法人企業の所得形成から純貯蓄までを表示する。"""
    columns = list(INCOME_CHAIN_LABELS)

    chart_df = df[
        ["fiscal_year", *columns]
    ].copy()

    chart_df = chart_df.melt(
        id_vars="fiscal_year",
        value_vars=columns,
        var_name="component",
        value_name="value",
    )

    chart_df["component"] = (
        chart_df["component"].map(
            INCOME_CHAIN_LABELS
        )
    )
    chart_df["value_trillion"] = (
        chart_df["value"] / 1000
    )

    return (
        alt.Chart(chart_df)
        .mark_line(
            point=True,
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(format="d"),
            ),
            y=alt.Y(
                "value_trillion:Q",
                title="名目額（兆円）",
            ),
            color=alt.Color(
                "component:N",
                title="項目",
            ),
            tooltip=[
                alt.Tooltip(
                    "fiscal_year:Q",
                    title="年度",
                    format="d",
                ),
                alt.Tooltip(
                    "component:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "value_trillion:Q",
                    title="兆円",
                    format=".1f",
                ),
            ],
        )
        .properties(height=380)
        .interactive()
    )


def prepare_capital_allocation_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """資金源と資金使途を累積額で整理する。"""
    if len(df) != 1:
        raise ValueError(
            "資本勘定サマリーは1行である必要があります。"
        )

    row = df.iloc[0]

    return pd.DataFrame(
        {
            "side": [
                "資金源",
                "資金源",
                "資金使途",
                "資金使途",
            ],
            "component": [
                "純貯蓄",
                "純資本移転",
                "純資本形成",
                "純貸出",
            ],
            "value_trillion": [
                row["cumulative_net_saving"] / 1000,
                row["cumulative_net_capital_transfers"] / 1000,
                row["cumulative_net_capital_formation"] / 1000,
                row["cumulative_net_lending"] / 1000,
            ],
        }
    )


def create_capital_allocation_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """累積資金源と資金使途を2本の積み上げ棒で表示する。"""
    chart_df = prepare_capital_allocation_data(
        df
    )

    bars = (
        alt.Chart(chart_df)
        .mark_bar(
            size=58,
        )
        .encode(
            y=alt.Y(
                "side:N",
                title=None,
                sort=[
                    "資金源",
                    "資金使途",
                ],
                axis=alt.Axis(
                    labelFontSize=13,
                    labelPadding=10,
                ),
            ),
            x=alt.X(
                "value_trillion:Q",
                title="2015～2024年度累積（兆円）",
                stack="zero",
            ),
            color=alt.Color(
                "component:N",
                title="構成項目",
                sort=[
                    "純貯蓄",
                    "純資本移転",
                    "純資本形成",
                    "純貸出",
                ],
            ),
            tooltip=[
                alt.Tooltip(
                    "side:N",
                    title="区分",
                ),
                alt.Tooltip(
                    "component:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "value_trillion:Q",
                    title="兆円",
                    format=".1f",
                ),
            ],
        )
    )

    return bars.properties(
        height=190,
    )


def create_capital_financial_net_lending_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """資本勘定と金融勘定の純貸出を比較する。"""
    chart_df = df[
        [
            "fiscal_year",
            "net_lending_capital_account",
            "net_lending_financial_account",
        ]
    ].copy()

    chart_df = chart_df.rename(
        columns={
            "net_lending_capital_account": "資本勘定",
            "net_lending_financial_account": "金融勘定",
        }
    )

    chart_df = chart_df.melt(
        id_vars="fiscal_year",
        var_name="account",
        value_name="value",
    )

    chart_df["value_trillion"] = (
        chart_df["value"] / 1000
    )

    return (
        alt.Chart(chart_df)
        .mark_line(
            point=True,
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(format="d"),
            ),
            y=alt.Y(
                "value_trillion:Q",
                title="純貸出（兆円）",
            ),
            color=alt.Color(
                "account:N",
                title="勘定",
            ),
            tooltip=[
                alt.Tooltip(
                    "fiscal_year:Q",
                    title="年度",
                    format="d",
                ),
                alt.Tooltip(
                    "account:N",
                    title="勘定",
                ),
                alt.Tooltip(
                    "value_trillion:Q",
                    title="兆円",
                    format=".1f",
                ),
            ],
        )
        .properties(height=380)
        .interactive()
    )


def create_financial_account_components_chart(
    df: pd.DataFrame,
    side: str,
) -> alt.Chart:
    """金融資産または負債の累積純取引額を表示する。"""
    if side not in {
        "金融資産",
        "負債",
    }:
        raise ValueError(
            f"未対応の区分です: {side}"
        )

    chart_df = df.loc[
        df["side"] == side,
        [
            "component_name",
            "cumulative_amount",
        ],
    ].copy()

    chart_df["component_label"] = (
        chart_df["component_name"]
        .replace(
            FINANCIAL_COMPONENT_SHORT_LABELS
        )
    )

    chart_df["value_trillion"] = (
        chart_df["cumulative_amount"]
        / 1000
    )

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "component_label:N",
                title=None,
                sort="-x",
                axis=alt.Axis(
                    labelLimit=240,
                    labelPadding=8,
                ),
            ),
            x=alt.X(
                "value_trillion:Q",
                title="2015～2024年度累積（兆円）",
            ),
            tooltip=[
                alt.Tooltip(
                    "component_name:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "value_trillion:Q",
                    title="兆円",
                    format="+.1f",
                ),
            ],
        )
        .properties(height=350)
    )


def prepare_financial_asset_detail_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """詳細金融資産取引を非重複の構成項目へ集約する。"""
    missing = (
        set(FINANCIAL_ASSET_DETAIL_LABELS)
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "詳細金融資産取引に必要な列がありません: "
            f"{sorted(missing)}"
        )

    return pd.DataFrame(
        [
            {
                "component": label,
                "value_trillion": (
                    df[column].sum()
                    / 1000
                ),
            }
            for column, label in (
                FINANCIAL_ASSET_DETAIL_LABELS.items()
            )
        ]
    )


def create_financial_asset_detail_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """金融資産の純取得を詳細項目へ分解して表示する。"""
    chart_df = (
        prepare_financial_asset_detail_data(
            df
        )
    )

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "component:N",
                title=None,
                sort="-x",
                axis=alt.Axis(
                    labelLimit=240,
                    labelPadding=8,
                ),
            ),
            x=alt.X(
                "value_trillion:Q",
                title="2015～2024年度累積（兆円）",
            ),
            tooltip=[
                alt.Tooltip(
                    "component:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "value_trillion:Q",
                    title="兆円",
                    format="+.1f",
                ),
            ],
        )
        .properties(height=470)
    )


def _add_value_labels(
    chart_df: pd.DataFrame,
    *,
    x_field: str,
    y_field: str,
) -> alt.LayerChart:
    """横棒グラフに符号付きデータラベルを付与する。"""
    chart_df = chart_df.copy()

    chart_df["value_label"] = (
        chart_df[x_field]
        .map(
            lambda value: (
                f"{value:+.1f}"
            )
        )
    )

    bars = (
        alt.Chart(chart_df)
        .mark_bar(
            size=28,
        )
        .encode(
            y=alt.Y(
                f"{y_field}:N",
                title=None,
                sort=None,
                axis=alt.Axis(
                    labelPadding=8,
                ),
            ),
            x=alt.X(
                f"{x_field}:Q",
                title="兆円",
            ),
            tooltip=[
                alt.Tooltip(
                    f"{y_field}:N",
                    title="要因",
                ),
                alt.Tooltip(
                    f"{x_field}:Q",
                    title="兆円",
                    format="+.1f",
                ),
            ],
        )
    )

    labels = (
        alt.Chart(chart_df)
        .mark_text(
            align="left",
            dx=6,
            fontSize=13,
        )
        .encode(
            y=alt.Y(
                f"{y_field}:N",
                sort=None,
            ),
            x=alt.X(
                f"{x_field}:Q",
            ),
            text="value_label:N",
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "zero": [
                        0.0,
                    ],
                }
            )
        )
        .mark_rule(
            strokeDash=[
                4,
                4,
            ],
        )
        .encode(
            x="zero:Q",
        )
    )

    return (
        bars
        + labels
        + zero_line
    )


def create_stock_reconciliation_chart(
    df: pd.DataFrame,
    item: str,
) -> alt.LayerChart:
    """指定ストックの変化を取引・その他量的変動・再評価へ分解する。"""
    selected = df.loc[
        df["item"] == item
    ]

    if len(selected) != 1:
        raise ValueError(
            "ストック項目を一意に"
            f"取得できません: {item}"
        )

    row = selected.iloc[0]

    chart_df = pd.DataFrame(
        {
            "component": [
                "取引相当",
                "その他の資産量変動",
                "再評価",
            ],
            "value_trillion": [
                (
                    row["implied_transactions"]
                    / 1000
                ),
                (
                    row["other_volume_change"]
                    / 1000
                ),
                (
                    row["revaluation"]
                    / 1000
                ),
            ],
        }
    )

    return (
        _add_value_labels(
            chart_df,
            x_field="value_trillion",
            y_field="component",
        )
        .properties(
            height=180,
        )
    )


def create_corporate_profit_dividend_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """法人企業統計の純利益・配当・配当控除後利益を表示する。"""
    chart_df = df[
        [
            "fiscal_year",
            "net_income",
            "total_dividends",
            "profit_after_dividends",
        ]
    ].copy()

    chart_df = chart_df.rename(
        columns={
            "net_income": "当期純利益",
            "total_dividends": "配当",
            "profit_after_dividends": "当期純利益－配当",
        }
    )

    chart_df = chart_df.melt(
        id_vars="fiscal_year",
        var_name="component",
        value_name="value",
    )

    chart_df["value_trillion"] = (
        chart_df["value"]
        / 1_000_000
    )

    return (
        alt.Chart(chart_df)
        .mark_line(
            point=True,
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(format="d"),
            ),
            y=alt.Y(
                "value_trillion:Q",
                title="金額（兆円）",
            ),
            color=alt.Color(
                "component:N",
                title="項目",
            ),
            tooltip=[
                alt.Tooltip(
                    "fiscal_year:Q",
                    title="年度",
                    format="d",
                ),
                alt.Tooltip(
                    "component:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "value_trillion:Q",
                    title="兆円",
                    format=".1f",
                ),
            ],
        )
        .properties(height=380)
        .interactive()
    )


def create_corporate_stock_change_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """法人企業統計の主要BS項目の端点変化を表示する。"""
    chart_df = df[
        [
            "item",
            "endpoint_change",
        ]
    ].copy()

    chart_df["item_label"] = (
        chart_df["item"].map(
            CORPORATE_STOCK_LABELS
        )
    )

    if chart_df["item_label"].isna().any():
        unknown = chart_df.loc[
            chart_df["item_label"].isna(),
            "item",
        ].tolist()

        raise ValueError(
            "未定義のストック項目があります: "
            f"{unknown}"
        )

    chart_df["value_trillion"] = (
        chart_df["endpoint_change"]
        / 1_000_000
    )

    chart_df["highlight"] = "その他"

    chart_df.loc[
        chart_df["item"]
        == "retained_earnings",
        "highlight",
    ] = "利益剰余金"

    chart_df.loc[
        chart_df["item"]
        == "cash_deposits",
        "highlight",
    ] = "現金・預金"

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "item_label:N",
                title=None,
                sort="-x",
                axis=alt.Axis(
                    labelLimit=220,
                    labelPadding=8,
                ),
            ),
            x=alt.X(
                "value_trillion:Q",
                title=(
                    "2015年度前期末→"
                    "2024年度当期末（兆円）"
                ),
            ),
            color=alt.Color(
                "highlight:N",
                title="強調項目",
                scale=alt.Scale(
                    domain=[
                        "利益剰余金",
                        "現金・預金",
                        "その他",
                    ],
                    range=[
                        "#4C78A8",
                        "#F58518",
                        "#B8B8B8",
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "item_label:N",
                    title="項目",
                ),
                alt.Tooltip(
                    "value_trillion:Q",
                    title="兆円",
                    format="+.1f",
                ),
            ],
        )
        .properties(height=350)
    )


def create_retained_earnings_bridge_chart(
    df: pd.DataFrame,
) -> alt.LayerChart:
    """利益剰余金端点増加への橋渡し要因を表示する。"""
    if len(df) != 1:
        raise ValueError(
            "利益剰余金ブリッジは"
            "1行である必要があります。"
        )

    row = df.iloc[0]

    chart_df = pd.DataFrame(
        {
            "component": [
                "当期純利益－配当",
                "年度内その他差額",
                "年度間不連続",
            ],
            "value_trillion": [
                (
                    row[
                        "cumulative_profit_after_dividends"
                    ]
                    / 1_000_000
                ),
                (
                    row[
                        "cumulative_bridge_residual"
                    ]
                    / 1_000_000
                ),
                (
                    row[
                        "interyear_discontinuity"
                    ]
                    / 1_000_000
                ),
            ],
        }
    )

    return (
        _add_value_labels(
            chart_df,
            x_field="value_trillion",
            y_field="component",
        )
        .properties(
            height=180,
        )
    )
