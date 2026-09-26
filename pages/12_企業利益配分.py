from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from real_wage_dashboard.corporate_profit_allocation_ui import (
    STOCK_RECONCILIATION_LABELS,
    create_capital_allocation_chart,
    create_capital_financial_net_lending_chart,
    create_corporate_profit_dividend_chart,
    create_corporate_stock_change_chart,
    create_financial_account_components_chart,
    create_financial_asset_detail_chart,
    create_income_chain_chart,
    create_retained_earnings_bridge_chart,
    create_stock_reconciliation_chart,
)


SNAPSHOT_DIR = Path(
    "data/snapshots/corporate_profit_allocation"
)

START_YEAR = 2015
END_YEAR = 2024


st.set_page_config(
    page_title="企業利益配分・資産蓄積分析",
    page_icon="🏢",
    layout="wide",
)


@st.cache_data
def load_snapshot(
    filename: str,
) -> pd.DataFrame:
    """企業利益配分分析の保存済みCSVを読み込む。"""
    path = SNAPSHOT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"分析結果がありません: {path}"
        )

    df = pd.read_csv(path)

    for column in (
        "fiscal_year",
        "start_year",
        "end_year",
    ):
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="raise",
            ).astype(int)

    if "fiscal_year" in df.columns:
        df = (
            df.sort_values("fiscal_year")
            .reset_index(drop=True)
        )

    return df


def render_glossary() -> None:
    """ページ内の主要概念を説明する。"""
    with st.expander(
        "📘 用語の解説",
        expanded=False,
    ):
        st.markdown(
            """
            **純貯蓄**  
            非金融法人企業の純可処分所得のうち企業部門に残る所得です。企業会計上の当期純利益や利益剰余金とは同一ではありません。

            **純資本形成**  
            総固定資本形成から固定資本減耗を差し引き、在庫変動や土地純購入を加えたネットの実物投資です。

            **純貸出**  
            貯蓄等から実物投資等を差し引いた後の資金余剰です。現金保有額そのものではありません。

            **金融資産の純取得**  
            金融資産の取得から処分を差し引いた純取引額です。

            **再評価**  
            株価、地価、為替等の変化によって、取引を伴わず資産・負債の評価額が変化することです。

            **利益剰余金**  
            純資産側の会計項目であり、現金・預金とは別の概念です。
            """
        )


def main() -> None:
    st.title(
        "企業利益の配分・資産蓄積分析"
    )

    st.caption(
        "2015～2024年度を中心に、"
        "非金融法人企業の利益・貯蓄が"
        "実物投資、金融資産、負債へ"
        "どのように対応し、"
        "資産・負債ストックへ"
        "つながったかを確認します。"
    )

    render_glossary()

    try:
        income_chain = load_snapshot(
            "01_income_chain.csv"
        )
        capital_summary = load_snapshot(
            "02b_capital_account_summary.csv"
        )
        capital_financial = load_snapshot(
            "03_capital_financial_discrepancy.csv"
        )
        financial_components = load_snapshot(
            "04_financial_account_components.csv"
        )
        financial_assets_detail = load_snapshot(
            "05_financial_detail_assets.csv"
        )
        stock_reconciliation = load_snapshot(
            "07_stock_reconciliation.csv"
        )
        corporate_accounting = load_snapshot(
            "08_corporate_accounting.csv"
        )
        corporate_continuity = load_snapshot(
            "09_corporate_stock_continuity.csv"
        )
        retained_bridge = load_snapshot(
            "10_retained_earnings_bridge.csv"
        )

    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        st.error(str(exc))
        st.stop()

    capital_row = (
        capital_summary.iloc[0]
    )

    final_financial = (
        capital_financial.iloc[-1]
    )

    bridge_row = (
        retained_bridge.iloc[0]
    )

    # ==========================================
    # 主要結果
    # ==========================================

    st.subheader("主要結果")

    c1, c2, c3, c4 = (
        st.columns(4)
    )

    c1.metric(
        "累積純貯蓄",
        (
            f"{capital_row['cumulative_net_saving'] / 1000:.1f}"
            "兆円"
        ),
        "2015～2024年度",
        delta_color="off",
    )

    c2.metric(
        "累積純資本形成",
        (
            f"{capital_row['cumulative_net_capital_formation'] / 1000:.1f}"
            "兆円"
        ),
        (
            "資金源の "
            f"{capital_row['capital_formation_share_pct']:.1f}%"
        ),
        delta_color="off",
    )

    c3.metric(
        "資本勘定 累積純貸出",
        (
            f"{capital_row['cumulative_net_lending'] / 1000:.1f}"
            "兆円"
        ),
        (
            "資金源の "
            f"{capital_row['net_lending_share_pct']:.1f}%"
        ),
        delta_color="off",
    )

    c4.metric(
        "金融勘定 累積純貸出",
        (
            f"{final_financial['cumulative_financial_net_lending'] / 1000:.1f}"
            "兆円"
        ),
        (
            "資本勘定との差 "
            f"{final_financial['cumulative_capital_financial_discrepancy'] / 1000:.1f}"
            "兆円"
        ),
        delta_color="off",
    )

    st.markdown(
        "### この分析から端的に言えること"
    )

    st.success(
        """
        - **企業の資金余剰は、現預金の積み上げだけでは説明できません。** 2015～2024年度の金融資産の純取得では、直接投資154.9兆円が現金・預金131.9兆円を上回りました。
        - **資金余剰と借入増加は両立します。** 同期間には借入も182.1兆円純増しており、企業は負債を増やしながら、それを上回る金融資産を取得していました。
        - **資産残高の増加は新規投資だけではありません。** 金融資産のうち株式の残高増加177.6兆円は、ほぼ再評価178.0兆円によるものでした。
        - **利益剰余金は現預金ではありません。** 利益剰余金の端点増加286.2兆円に対し、現金・預金の端点増加は114.2兆円でした。
        """
    )

    st.info(
        "純貸出は「現金の積み上がり」ではありません。"
        "金融資産の純取得と負債の純発生を"
        "同時に見る必要があります。"
    )

    # ==========================================
    # 1
    # ==========================================

    st.divider()

    st.subheader(
        "1. 営業余剰から純貯蓄まで"
    )

    st.altair_chart(
        create_income_chain_chart(
            income_chain
        ),
        width="stretch",
    )

    start_income = (
        income_chain.iloc[0]
    )

    end_income = (
        income_chain.iloc[-1]
    )

    comparison = pd.DataFrame(
        {
            "年度": [
                START_YEAR,
                END_YEAR,
            ],
            "純営業余剰": [
                (
                    start_income[
                        "net_operating_surplus"
                    ]
                    / 1000
                ),
                (
                    end_income[
                        "net_operating_surplus"
                    ]
                    / 1000
                ),
            ],
            "純第1次所得": [
                (
                    start_income[
                        "net_primary_income_balance"
                    ]
                    / 1000
                ),
                (
                    end_income[
                        "net_primary_income_balance"
                    ]
                    / 1000
                ),
            ],
            "純貯蓄": [
                (
                    start_income[
                        "net_saving"
                    ]
                    / 1000
                ),
                (
                    end_income[
                        "net_saving"
                    ]
                    / 1000
                ),
            ],
        }
    )

    st.dataframe(
        comparison.style.format(
            {
                "純営業余剰": "{:.1f}兆円",
                "純第1次所得": "{:.1f}兆円",
                "純貯蓄": "{:.1f}兆円",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    # ==========================================
    # 2
    # ==========================================

    st.divider()

    st.subheader(
        "2. 純貯蓄は実物投資と純貸出へ"
        "どう分かれたか"
    )

    st.latex(
        r"""\mathrm{純貸出}
        =
        \mathrm{純貯蓄}
        +
        \mathrm{純資本移転}
        -
        \mathrm{純資本形成}"""
    )

    st.altair_chart(
        create_capital_allocation_chart(
            capital_summary
        ),
        width="stretch",
    )

    st.caption(
        "上段は資金源、下段はその資金使途です。"
        f"純貯蓄{capital_row['cumulative_net_saving'] / 1000:.1f}兆円"
        f"＋純資本移転{capital_row['cumulative_net_capital_transfers'] / 1000:.1f}兆円"
        f"＝資金源{capital_row['cumulative_sources'] / 1000:.1f}兆円。"
        "これに対し、"
        f"純資本形成{capital_row['cumulative_net_capital_formation'] / 1000:.1f}兆円"
        f"＋純貸出{capital_row['cumulative_net_lending'] / 1000:.1f}兆円"
        "となります。"
    )

    # ==========================================
    # 3
    # ==========================================

    st.divider()

    st.subheader(
        "3. 資本勘定と金融勘定の純貸出"
    )

    st.altair_chart(
        create_capital_financial_net_lending_chart(
            capital_financial
        ),
        width="stretch",
    )

    st.info(
        "2015～2024年度累計では、"
        "資本勘定253.1兆円、"
        "金融勘定141.3兆円、"
        "開差111.9兆円です。"
    )

    # ==========================================
    # 4
    # ==========================================

    st.divider()

    st.subheader(
        "4. 金融資産の純取得と負債の純発生"
    )

    asset_tab, liability_tab = (
        st.tabs(
            [
                "金融資産",
                "負債",
            ]
        )
    )

    with asset_tab:
        st.altair_chart(
            create_financial_account_components_chart(
                financial_components,
                "金融資産",
            ),
            width="stretch",
        )

    with liability_tab:
        st.altair_chart(
            create_financial_account_components_chart(
                financial_components,
                "負債",
            ),
            width="stretch",
        )

    st.markdown(
        "#### 金融資産の詳細"
    )

    st.altair_chart(
        create_financial_asset_detail_chart(
            financial_assets_detail
        ),
        width="stretch",
    )

    st.info(
        "直接投資154.9兆円と"
        "現金・預金131.9兆円が特に大きく、"
        "企業資金余剰を現預金だけで"
        "説明することはできません。"
    )

    # ==========================================
    # 5
    # ==========================================

    st.divider()

    st.subheader(
        "5. 資産・負債ストックはなぜ増えたか"
    )

    label_to_code = {
        label: code
        for code, label in (
            STOCK_RECONCILIATION_LABELS.items()
        )
    }

    selected_label = (
        st.selectbox(
            "表示するストック項目",
            options=list(
                label_to_code
            ),
            index=list(
                label_to_code
            ).index(
                "金融資産"
            ),
        )
    )

    selected_code = (
        label_to_code[
            selected_label
        ]
    )

    selected_stock = (
        stock_reconciliation.loc[
            stock_reconciliation[
                "item"
            ]
            == selected_code
        ].iloc[0]
    )

    s1, s2, s3 = (
        st.columns(3)
    )

    s1.metric(
        "ストック増減",
        (
            f"{selected_stock['stock_change'] / 1000:+.1f}"
            "兆円"
        ),
    )

    s2.metric(
        "取引相当",
        (
            f"{selected_stock['implied_transactions'] / 1000:+.1f}"
            "兆円"
        ),
    )

    s3.metric(
        "再評価",
        (
            f"{selected_stock['revaluation'] / 1000:+.1f}"
            "兆円"
        ),
    )

    left, center, right = (
        st.columns(
            [
                1,
                2,
                1,
            ]
        )
    )

    with center:
        st.altair_chart(
            create_stock_reconciliation_chart(
                stock_reconciliation,
                selected_code,
            ),
            width="stretch",
        )

    st.caption(
        "グラフ内の数値は兆円。"
        "対象期間は2014年末→2024年末です。"
        "年度金融勘定との完全一致は要求しません。"
    )

    # ==========================================
    # 6
    # ==========================================

    st.divider()

    st.subheader(
        "6. 当期純利益・配当・配当控除後利益"
    )

    st.altair_chart(
        create_corporate_profit_dividend_chart(
            corporate_accounting
        ),
        width="stretch",
    )

    p1, p2, p3 = (
        st.columns(3)
    )

    net_income = (
        bridge_row[
            "cumulative_net_income"
        ]
        / 1_000_000
    )

    dividends = (
        bridge_row[
            "cumulative_dividends"
        ]
        / 1_000_000
    )

    after = (
        bridge_row[
            "cumulative_profit_after_dividends"
        ]
        / 1_000_000
    )

    p1.metric(
        "累積当期純利益",
        f"{net_income:.1f}兆円",
    )

    p2.metric(
        "累積配当",
        f"{dividends:.1f}兆円",
    )

    p3.metric(
        "当期純利益－配当",
        f"{after:.1f}兆円",
    )

    st.caption(
        "期間累積の配当金 / 当期純利益は"
        f"{dividends / net_income * 100:.1f}%です。"
    )

    # ==========================================
    # 7
    # ==========================================

    st.divider()

    st.subheader(
        "7. 利益剰余金は現預金と同じではない"
    )

    st.altair_chart(
        create_corporate_stock_change_chart(
            corporate_continuity
        ),
        width="stretch",
    )

    retained = (
        corporate_continuity.loc[
            corporate_continuity[
                "item"
            ]
            == "retained_earnings"
        ].iloc[0]
    )

    cash = (
        corporate_continuity.loc[
            corporate_continuity[
                "item"
            ]
            == "cash_deposits"
        ].iloc[0]
    )

    b1, b2 = (
        st.columns(2)
    )

    b1.metric(
        "利益剰余金の端点増加",
        (
            f"{retained['endpoint_change'] / 1_000_000:.1f}"
            "兆円"
        ),
    )

    b2.metric(
        "現金・預金の端点増加",
        (
            f"{cash['endpoint_change'] / 1_000_000:.1f}"
            "兆円"
        ),
    )

    st.markdown(
        "#### 利益剰余金の長期ブリッジ"
    )

    bridge_left, bridge_center, bridge_right = (
        st.columns(
            [
                1,
                2,
                1,
            ]
        )
    )

    with bridge_center:
        st.altair_chart(
            create_retained_earnings_bridge_chart(
                retained_bridge
            ),
            width="stretch",
        )

    st.caption(
        "当期純利益－配当325.4兆円"
        "＋年度内その他差額27.2兆円"
        "－年度間不連続66.4兆円"
        "＝利益剰余金端点増加286.2兆円。"
    )

    st.info(
        "利益剰余金は純資産側、"
        "現金・預金は資産側の項目です。"
        "「内部留保＝現預金」とは"
        "解釈しません。"
    )

    # ==========================================
    # 8
    # ==========================================

    st.divider()

    st.subheader(
        "8. 出典・分析上の注意"
    )

    with st.expander(
        "データ出典・分析方法",
        expanded=False,
    ):
        st.markdown(
            """
            - **SNA**：内閣府「2024年度国民経済計算（2020年基準・2008SNA）」
            - **法人企業統計**：財務省「法人企業統計調査」
            - **主期間**：2015～2024年度
            - **ストック比較**：2014年末→2024年末
            - **法人企業統計ストック**：2015年度前期末→2024年度当期末

            SNAと法人企業統計では対象範囲・会計概念・評価方法が異なるため、両統計の値が一致することは前提としていません。
            """
        )

    st.caption(
        "詳細な定義、会計恒等式、検証結果は"
        " docs/analysis/15_corporate_profit_allocation.md"
        " にまとめています。"
    )


if __name__ == "__main__":
    main()
