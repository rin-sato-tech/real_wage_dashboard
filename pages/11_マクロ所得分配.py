from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from real_wage_dashboard.macro_distribution_ui import (
    SECTOR_LABELS,
    create_disposable_income_ratio_chart,
    create_household_net_saving_chart,
    create_household_primary_income_chart,
    create_household_saving_rate_chart,
    create_income_generation_chart,
    create_net_lending_decomposition_chart,
    create_nonfinancial_capital_account_chart,
    create_redistribution_components_chart,
    create_sector_net_lending_chart,
)

SNAPSHOT_DIR = Path("data/snapshots/macro_distribution")

START_YEAR = 1994
END_YEAR = 2024


st.set_page_config(
    page_title="マクロ所得分配分析",
    page_icon="🏦",
    layout="wide",
)


@st.cache_data
def load_snapshot(filename: str) -> pd.DataFrame:
    """マクロ所得分配分析の保存済みCSVを読み込む。"""

    path = SNAPSHOT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"分析結果がありません: {path}")

    df = pd.read_csv(path)

    if "fiscal_year" in df.columns:
        df["fiscal_year"] = pd.to_numeric(
            df["fiscal_year"],
            errors="raise",
        ).astype(int)

        df = (
            df.sort_values("fiscal_year")
            .reset_index(drop=True)
        )

    return df


def get_year_row(
    df: pd.DataFrame,
    year: int,
) -> pd.Series:
    """指定年度の行を取得する。"""

    selected = df.loc[df["fiscal_year"] == year]

    if len(selected) != 1:
        raise ValueError(f"{year}年度のデータを一意に取得できません。")

    return selected.iloc[0]


def render_economic_glossary() -> None:
    """ページ内で使用する主要な経済用語を説明する。"""

    with st.expander(
        "📘 経済用語の解説",
        expanded=False,
    ):
        st.markdown(
            """
            **GDP（国内総生産）**  
            国内で一定期間に新たに生み出された付加価値の合計です。このページでは、所得や資金余剰が経済全体に対してどの程度の規模かを見るため、GDP比も使用します。

            **雇用者報酬**  
            企業や政府などが雇用者に対して支払う給与・賞与や、事業主負担の社会保険料などを含む労働の対価です。

            **営業余剰**  
            生産によって生じた付加価値から、雇用者報酬や生産に関する税などを差し引いた後に企業などに残る所得です。企業会計上の「営業利益」と同じものではありません。

            **混合所得**  
            個人事業主などについて、労働の対価と事業に投じた資本からの所得を明確に分離できないため、まとめて計上される所得です。

            **純生産・輸入税**  
            生産や輸入に課される税から、政府が支払う補助金を差し引いたものです。

            ---

            **第1次所得**  
            労働、事業、資産の保有などを通じて、市場取引から最初に得られる所得です。家計では主に雇用者報酬、営業余剰・混合所得、財産所得から構成されます。

            **財産所得**  
            利子、配当、賃貸料など、金融資産や土地などの保有によって発生する所得です。このページでは受取額から支払額を差し引いた「純財産所得」も使用します。

            **純可処分所得**  
            第1次所得から税や社会負担を支払い、社会給付などを受け取った後、家計が消費や貯蓄に使える所得です。

            **経常税**  
            所得税など、所得や財産等に対して継続的に課される税です。

            **社会負担**  
            年金・医療などの社会保障制度へ支払う保険料等です。

            **社会給付**  
            年金、医療・福祉関連の給付など、社会保障制度等から家計へ支払われる給付です。

            ---

            **純貯蓄**  
            可処分所得等のうち、消費されずに残った部分です。

            **家計貯蓄率**  
            家計が利用可能な所得のうち、純貯蓄として残した割合です。

            **制度部門**  
            経済主体を性質ごとにまとめた区分です。このページでは、非金融法人企業、金融機関、一般政府、家計、対家計民間非営利団体、海外部門を扱います。

            **純貸出・純借入**  
            貯蓄などによって得た資金から設備投資等を差し引いた後の資金余剰・不足です。

            - プラス：純貸出＝資金余剰
            - マイナス：純借入＝資金不足

            **非金融法人企業**  
            銀行・保険などの金融機関を除く法人企業部門です。

            **純資本形成**  
            設備・建物などへの投資から固定資本の減耗を差し引き、在庫変動や土地購入等を加味したものです。このページでは、純貸出を計算する際の資金使用側として扱います。

            **純資本移転**  
            投資補助金など、資本形成や資産に関係する移転の受取と支払の差額です。

            ---

            **名目額**  
            その年度の価格で評価した金額です。物価変動の影響を含むため、1994年度と2024年度の名目額だけを比較して実質的な増減とは判断しません。

            **GDP比**  
            各金額をGDPで割った割合です。経済全体の規模が変化しても比較しやすいため、長期的な構造変化を見る際に使用します。

            **pt（パーセントポイント）**  
            割合同士の差です。例えば10%から15%への上昇は「+5%」ではなく「+5pt」と表します。
            """
        )


def main() -> None:
    st.title("マクロ所得分配分析")

    st.caption(
        "1994～2024年度の国民経済計算を用いて、"
        "生産された所得が家計・企業等へどのように分配され、"
        "貯蓄・投資・資金余剰へつながったかを確認します。"
    )

    render_economic_glossary()

    try:
        income_generation = load_snapshot(
            "01_income_generation.csv"
        )

        household_primary = load_snapshot(
            "02_household_primary_income.csv"
        )

        household_redistribution = load_snapshot(
            "03_household_redistribution.csv"
        )

        household_saving = load_snapshot(
            "04_household_saving.csv"
        )

        sector_amount = load_snapshot(
            "05_sector_net_lending_amount_wide.csv"
        )

        sector_ratio = load_snapshot(
            "05_sector_net_lending_ratio_wide.csv"
        )

        nonfinancial_capital = load_snapshot(
            "06_nonfinancial_capital_account.csv"
        )

        net_lending_decomposition = load_snapshot(
            "07_nonfinancial_net_lending_decomposition.csv"
        )

    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        st.error(str(exc))
        st.stop()

    # ==========================================
    # 主要結果
    # ==========================================

    st.subheader("主要結果")

    start_income = get_year_row(
        income_generation,
        START_YEAR,
    )

    end_income = get_year_row(
        income_generation,
        END_YEAR,
    )

    start_sector_ratio = get_year_row(
        sector_ratio,
        START_YEAR,
    )

    end_sector_ratio = get_year_row(
        sector_ratio,
        END_YEAR,
    )

    end_sector_amount = get_year_row(
        sector_amount,
        END_YEAR,
    )

    metric1, metric2, metric3, metric4 = (
        st.columns(4)
    )

    metric1.metric(
        label="雇用者報酬 / GDP",
        value=(
            f"{end_income['employee_compensation_share']:.1f}%"
        ),
        delta=(
            f"{end_income['employee_compensation_share'] - start_income['employee_compensation_share']:+.1f}pt"
            "（1994年度比）"
        ),
    )

    metric2.metric(
        label="営業余剰 / GDP",
        value=(
            f"{end_income['gross_operating_surplus_share']:.1f}%"
        ),
        delta=(
            f"{end_income['gross_operating_surplus_share'] - start_income['gross_operating_surplus_share']:+.1f}pt"
            "（1994年度比）"
        ),
    )

    metric3.metric(
        label="非金融法人企業 純貸出",
        value=(
            f"{end_sector_amount['capital_nonfinancial_corporations'] / 1000:.1f}兆円"
        ),
        delta=(
            f"GDP比 "
            f"{end_sector_ratio['capital_nonfinancial_corporations']:.1f}%"
        ),
        delta_color="off",
    )

    metric4.metric(
        label="家計 純貸出",
        value=(
            f"{end_sector_amount['capital_households'] / 1000:.1f}兆円"
        ),
        delta=(
            f"GDP比 "
            f"{end_sector_ratio['capital_households']:.1f}%"
        ),
        delta_color="off",
    )

    st.caption(
        "金額は名目値。"
        "長期的な分配構造の比較にはGDP比・構成比を用います。"
    )

    st.divider()

    # ==========================================
    # 1. GDP所得面
    # ==========================================

    st.subheader("1. GDP所得面構成")

    st.caption(
        "GDPを所得の発生側から見て、国内で生み出された付加価値が"
        "雇用者報酬・営業余剰・混合所得・純生産／輸入税に"
        "どのように分配されたかを確認します。"
    )

    income_display_mode = st.radio(
        "表示単位",
        options=[
            "GDP比",
            "名目額",
        ],
        horizontal=True,
        key="income_display_mode",
    )

    st.altair_chart(
        create_income_generation_chart(
            income_generation,
            income_display_mode,
        ),
        width='stretch',
    )

    if income_display_mode == "GDP比":
        st.caption(
            "1994年度から2024年度では、"
            "雇用者報酬比率は概ね同水準ですが、"
            "営業余剰比率が上昇し、"
            "混合所得比率が大きく低下しています。"
        )
    else:
        st.caption(
            "名目額には物価・経済規模の変化が含まれるため、"
            "長期的な分配構造の判断にはGDP比を併せて確認してください。"
        )

    comparison_years = [
        1994,
        2015,
        2024,
    ]

    income_comparison = (
        income_generation[
            income_generation[
                "fiscal_year"
            ].isin(comparison_years)
        ][
            [
                "fiscal_year",
                "employee_compensation_share",
                "gross_operating_surplus_share",
                "gross_mixed_income_share",
                "net_production_tax_share",
            ]
        ]
        .rename(
            columns={
                "fiscal_year": "年度",
                "employee_compensation_share": "雇用者報酬",
                "gross_operating_surplus_share": "営業余剰",
                "gross_mixed_income_share": "混合所得",
                "net_production_tax_share": "純生産・輸入税",
            }
        )
    )

    st.dataframe(
        income_comparison.style.format(
            {
                "雇用者報酬": "{:.2f}%",
                "営業余剰": "{:.2f}%",
                "混合所得": "{:.2f}%",
                "純生産・輸入税": "{:.2f}%",
            }
        ),
        width='stretch',
        hide_index=True,
    )

    st.divider()

    # ==========================================
    # 2. 家計第1次所得
    # ==========================================

    st.subheader("2. 家計第1次所得")

    st.caption(
        "第1次所得は、税や社会保障による再分配を受ける前に、"
        "労働・事業・資産保有などから得られる所得です。"
        "ここでは家計部門の所得源の構成を確認します。"
    )

    primary_display_mode = st.radio(
        "表示単位",
        options=[
            "構成比",
            "名目額",
        ],
        horizontal=True,
        key="primary_display_mode",
    )

    st.altair_chart(
        create_household_primary_income_chart(
            household_primary,
            primary_display_mode,
        ),
        width='stretch',
    )

    st.info(
        "1994～2024年度では、家計の第1次所得に占める"
        "雇用者報酬の比率が上昇しています。"
        "純財産所得比率は長期では低下しており、"
        "家計部門全体が資産所得中心へ移行したとはいえません。"
    )

    st.divider()

    # ==========================================
    # 3. 第1次所得から可処分所得
    # ==========================================

    st.subheader("3. 第1次所得から可処分所得")

    st.caption(
        "家計の第1次所得から税・社会負担を差し引き、"
        "社会給付やその他の経常移転を加えると純可処分所得になります。"
        "家計からの支払は負方向、家計への受取は正方向に表示します。"
    )

    st.markdown("#### 可処分所得 / 第1次所得")

    st.altair_chart(
        create_disposable_income_ratio_chart(
            household_redistribution
        ),
        width='stretch',
    )

    redistribution_display_mode = st.radio(
        "移転項目の表示単位",
        options=[
            "第1次所得比",
            "名目額",
        ],
        horizontal=True,
        key="redistribution_display_mode",
    )

    st.altair_chart(
        create_redistribution_components_chart(
            household_redistribution,
            redistribution_display_mode,
        ),
        width='stretch',
    )

    st.caption(
        "経常税・純社会負担は家計からの支払として"
        "負方向に表示しています。"
        "社会給付は家計への受取として正方向に表示しています。"
    )

    st.info(
        "1994～2024年度では、社会負担と社会給付の"
        "双方が大幅に拡大しました。"
        "そのため、可処分所得 / 第1次所得比率は"
        "長期の両端ではほぼ同水準ですが、"
        "2015年度以降に限ると低下しています。"
    )

    st.divider()

    # ==========================================
    # 4. 家計消費・貯蓄
    # ==========================================

    st.subheader("4. 家計の消費と貯蓄")

    st.caption(
        "家計が利用できる所得のうち、消費されずに残った部分が純貯蓄です。"
        "貯蓄率は、その所得のうちどの程度を貯蓄として残したかを表します。"
    )

    st.markdown("#### 家計貯蓄率")

    st.altair_chart(
        create_household_saving_rate_chart(
            household_saving
        ),
        width='stretch',
    )

    st.markdown("#### 純貯蓄額")

    st.altair_chart(
        create_household_net_saving_chart(
            household_saving
        ),
        width='stretch',
    )

    st.caption("金額は名目値。貯蓄率の長期変化と併せて確認してください。")

    st.info(
        "家計貯蓄率は1990年代の高水準から長期的に低下し、"
        "2010年代にはゼロ近辺となる年度が増えました。"
        "2020年度には一時的に大幅上昇しましたが、"
        "その後は再び低水準へ戻っています。"
    )

    st.divider()

    # ==========================================
    # 2. 制度部門別純貸出
    # ==========================================

    st.subheader("5. 制度部門別純貸出・純借入")

    st.caption(
        "純貸出・純借入は、各部門の貯蓄等と投資等の差から生じる"
        "資金余剰・資金不足を表します。"
        "0より上は資金余剰、0より下は資金不足です。"
    )

    selected_sectors = st.multiselect(
        "表示する制度部門",
        options=list(
            SECTOR_LABELS.values()
        ),
        default=[
            "非金融法人企業",
            "一般政府",
            "家計",
            "海外部門",
        ],
    )

    sector_display_mode = st.radio(
        "表示単位",
        options=[
            "GDP比",
            "名目額",
        ],
        horizontal=True,
        key="sector_display_mode",
    )

    if not selected_sectors:
        st.info(
            "表示する制度部門を1つ以上選択してください。"
        )
    else:
        st.altair_chart(
            create_sector_net_lending_chart(
                amount_df=sector_amount,
                ratio_df=sector_ratio,
                selected_sectors=selected_sectors,
                display_mode=sector_display_mode,
            ),
            width='stretch',
        )

    st.caption(
        "海外部門は海外側から見た値です。"
        "海外部門の純借入は、日本側からみると"
        "対外的な純貸出に対応します。"
    )

    st.info(
        "1990年代には家計が主要な資金余剰部門でしたが、"
        "2000年代以降は非金融法人企業の資金余剰が大幅に拡大しました。"
        "ただし企業の資金余剰は2010年代前半をピークに縮小しています。"
    )

    st.divider()

    # ==========================================
    # 6. 非金融法人企業の資本勘定
    # ==========================================

    st.subheader("6. 非金融法人企業の資金余剰")

    st.caption(
        "非金融法人企業の純貸出は、純貯蓄と純資本移転から"
        "純資本形成を差し引いて求められます。"
        "純資本形成は資金使用側なので、グラフでは控除方向に表示します。"
    )

    st.latex(
        r"""\mathrm{純貸出} = \mathrm{純貯蓄} + \mathrm{純資本移転} - \mathrm{純資本形成}"""
    )

    capital_display_mode = st.radio(
        "表示単位",
        options=[
            "GDP比",
            "名目額",
        ],
        horizontal=True,
        key="capital_display_mode",
    )

    st.altair_chart(
        create_nonfinancial_capital_account_chart(
            nonfinancial_capital,
            capital_display_mode,
        ),
        width='stretch',
    )

    st.caption(
        "純資本形成は純貸出から控除されるため、"
        "グラフでは恒等式上の寄与方向に合わせて"
        "符号を反転して表示しています。"
    )

    st.info(
        "非金融法人企業は1990年代には小幅な資金余剰でしたが、"
        "2000年代から2010年代前半にかけて"
        "大幅な資金余剰部門となりました。"
        "その後は純貯蓄の低下や純資本形成の増加によって、"
        "純貸出が縮小しています。"
    )

    st.markdown("#### 主要年度の比較")

    capital_comparison_years = [
        1994,
        2010,
        2015,
        2024,
    ]

    capital_comparison = (
        nonfinancial_capital.loc[
            nonfinancial_capital[
                "fiscal_year"
            ].isin(capital_comparison_years),
            [
                "fiscal_year",
                "net_saving",
                "net_saving_ratio",
                "net_capital_formation",
                "net_capital_formation_ratio",
                "net_lending_capital_account",
                "net_lending_capital_account_ratio",
            ],
        ]
        .copy()
    )

    for column in [
        "net_saving",
        "net_capital_formation",
        "net_lending_capital_account",
    ]:
        capital_comparison[column] = (
            capital_comparison[column] / 1000
        )

    capital_comparison = (
        capital_comparison.rename(
            columns={
                "fiscal_year": "年度",
                "net_saving": "純貯蓄（兆円）",
                "net_saving_ratio": "純貯蓄（GDP比）",
                "net_capital_formation": "純資本形成（兆円）",
                "net_capital_formation_ratio": "純資本形成（GDP比）",
                "net_lending_capital_account": "純貸出（兆円）",
                "net_lending_capital_account_ratio": "純貸出（GDP比）",
            }
        )
    )

    st.dataframe(
        capital_comparison.style.format(
            {
                "純貯蓄（兆円）": "{:.1f}",
                "純貯蓄（GDP比）": "{:.2f}%",
                "純資本形成（兆円）": "{:.1f}",
                "純資本形成（GDP比）": "{:.2f}%",
                "純貸出（兆円）": "{:.1f}",
                "純貸出（GDP比）": "{:.2f}%",
            }
        ),
        width='stretch',
        hide_index=True,
    )

    st.divider()

    # ==========================================
    # 7. 純貸出変化の期間別分解
    # ==========================================

    st.subheader("7. 非金融法人企業の純貸出変化")

    st.caption(
        "純貸出GDP比の変化を、純貯蓄・純資本移転・純資本形成の"
        "3要因に分解します。"
        "正の値は純貸出を押し上げ、負の値は押し下げる寄与を表します。"
    )

    period_options = {
        "2015 → 2019（コロナ前）": (
            2015,
            2019,
        ),
        "2019 → 2020（コロナショック）": (
            2019,
            2020,
        ),
        "2020 → 2024（コロナ後）": (
            2020,
            2024,
        ),
        "2015 → 2024（全期間）": (
            2015,
            2024,
        ),
    }

    selected_period_label = st.selectbox(
        "分解期間",
        options=list(
            period_options.keys()
        ),
        index=3,
    )

    start_year, end_year = (
        period_options[
            selected_period_label
        ]
    )

    period_df = (
        net_lending_decomposition.loc[
            (
                net_lending_decomposition[
                    "start_year"
                ]
                == start_year
            )
            & (
                net_lending_decomposition[
                    "end_year"
                ]
                == end_year
            )
        ]
    )

    if period_df.empty:
        st.error(f"{start_year}→{end_year}年度の分解結果がありません。")
    else:
        first_row = period_df.iloc[0]

        start_capital = get_year_row(
            nonfinancial_capital,
            start_year,
        )

        end_capital = get_year_row(
            nonfinancial_capital,
            end_year,
        )

        metric1, metric2, metric3 = (
            st.columns(3)
        )

        metric1.metric(
            "純貸出額",
            (
                f"{start_capital['net_lending_capital_account'] / 1000:.1f}"
                "兆円"
                " → "
                f"{end_capital['net_lending_capital_account'] / 1000:.1f}"
                "兆円"
            ),
        )

        metric2.metric(
            "純貸出GDP比",
            (
                f"{start_capital['net_lending_capital_account_ratio']:.2f}%"
                " → "
                f"{end_capital['net_lending_capital_account_ratio']:.2f}%"
            ),
        )

        metric3.metric(
            "GDP比変化",
            f"{first_row['actual_change_pt']:+.2f}pt",
        )

        left_space, chart_column, right_space = st.columns(
            [1, 2, 1]
        )

        with chart_column:
            st.altair_chart(
                create_net_lending_decomposition_chart(
                    net_lending_decomposition,
                    start_year=start_year,
                    end_year=end_year,
                ),
                width='stretch',
            )

        st.caption(
            "純資本形成は増加すると純貸出を減少させるため、"
            "分解では符号を反転した寄与として表示しています。"
        )

    period_notes = {
        (2015, 2019): (
            "コロナ前から企業の資金余剰は縮小していました。"
            "この期間では純貯蓄の低下が最大の要因です。"
        ),
        (2019, 2020): (
            "純貯蓄は低下しましたが、"
            "純資本形成の急減がそれを上回り、"
            "純貸出は一時的に拡大しました。"
        ),
        (2020, 2024): (
            "コロナ後は純資本形成の回復が"
            "純貸出縮小の最大要因となっています。"
        ),
        (2015, 2024): (
            "全期間では純貸出GDP比が大幅に縮小し、"
            "その中心的要因は純貯蓄比率の低下です。"
        ),
    }

    st.info(
        period_notes[
            (start_year, end_year)
        ]
    )

    st.divider()

    st.subheader("分析上の注意")

    st.markdown(
        """
        - 金額はすべて名目値です。
        - 長期的な構造比較では、名目額だけでなく構成比・GDP比を確認してください。
        - 家計部門の集計値は、家計間の所得・資産格差を表すものではありません。
        - 海外部門の符号は海外側から見た純貸出・純借入です。
        - 資本勘定と金融勘定には統計上の不突合があります。
        """
    )


if __name__ == "__main__":
    main()
