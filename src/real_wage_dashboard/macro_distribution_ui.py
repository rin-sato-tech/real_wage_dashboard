from __future__ import annotations

import altair as alt
import pandas as pd


INCOME_GENERATION_LABELS = {
    "employee_compensation": "雇用者報酬",
    "gross_operating_surplus": "営業余剰",
    "gross_mixed_income": "混合所得",
    "net_taxes_on_production_and_imports": "純生産・輸入税",
}

INCOME_GENERATION_SHARE_LABELS = {
    "employee_compensation_share": "雇用者報酬",
    "gross_operating_surplus_share": "営業余剰",
    "gross_mixed_income_share": "混合所得",
    "net_production_tax_share": "純生産・輸入税",
}

SECTOR_LABELS = {
    "capital_nonfinancial_corporations": "非金融法人企業",
    "capital_financial_corporations": "金融機関",
    "capital_general_government": "一般政府",
    "capital_households": "家計",
    "capital_npish": "対家計民間非営利団体",
    "capital_rest_of_world": "海外部門",
}

HOUSEHOLD_PRIMARY_AMOUNT_LABELS = {
    "employee_compensation_received": "雇用者報酬",
    "net_operating_surplus_mixed_income": "営業余剰・混合所得",
    "net_property_income": "純財産所得",
}

HOUSEHOLD_PRIMARY_RATIO_LABELS = {
    "employee_compensation_ratio": "雇用者報酬",
    "operating_mixed_income_ratio": "営業余剰・混合所得",
    "net_property_income_ratio": "純財産所得",
}

REDISTRIBUTION_AMOUNT_LABELS = {
    "current_taxes_paid": "経常税",
    "net_social_contributions_paid": "純社会負担",
    "social_benefits_received": "社会給付",
    "net_other_current_transfers": "その他経常移転（純）",
}

REDISTRIBUTION_RATIO_LABELS = {
    "current_taxes_ratio": "経常税",
    "net_social_contributions_ratio": "純社会負担",
    "social_benefits_ratio": "社会給付",
    "net_other_current_transfers_ratio": "その他経常移転（純）",
}

NONFINANCIAL_CAPITAL_LABELS = {
    "net_saving": "純貯蓄",
    "net_capital_transfers": "純資本移転",
    "net_capital_formation": "純資本形成（控除）",
    "net_lending_capital_account": "純貸出",
}

NONFINANCIAL_CAPITAL_RATIO_LABELS = {
    "net_saving_ratio": "純貯蓄",
    "net_capital_transfers_ratio": "純資本移転",
    "net_capital_formation_ratio": "純資本形成（控除）",
    "net_lending_capital_account_ratio": "純貸出",
}

NET_LENDING_DECOMPOSITION_LABELS = {
    "net_saving": "純貯蓄",
    "net_capital_transfers": "純資本移転",
    "net_capital_formation": "純資本形成",
}


def create_income_generation_chart(
    df: pd.DataFrame,
    display_mode: str,
) -> alt.Chart:
    """GDP所得面構成の時系列グラフを作る。"""

    if display_mode == "GDP比":
        columns = list(
            INCOME_GENERATION_SHARE_LABELS.keys()
        )

        chart_df = df[
            ["fiscal_year", *columns]
        ].melt(
            id_vars="fiscal_year",
            var_name="component",
            value_name="value",
        )

        chart_df["component"] = (
            chart_df["component"]
            .map(INCOME_GENERATION_SHARE_LABELS)
        )

        chart = (
            alt.Chart(chart_df)
            .mark_area(
                opacity=0.85,
            )
            .encode(
                x=alt.X(
                    "fiscal_year:Q",
                    title="年度",
                    axis=alt.Axis(
                        format="d",
                    ),
                ),
                y=alt.Y(
                    "value:Q",
                    title="GDP比（%）",
                    stack="zero",
                    scale=alt.Scale(
                        domain=[0, 100],
                    ),
                ),
                color=alt.Color(
                    "component:N",
                    title="所得項目",
                    sort=[
                        "雇用者報酬",
                        "営業余剰",
                        "混合所得",
                        "純生産・輸入税",
                    ],
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
                        "value:Q",
                        title="GDP比",
                        format=".2f",
                    ),
                ],
            )
            .properties(
                height=430,
            )
        )

        return chart

    if display_mode == "名目額":
        columns = list(
            INCOME_GENERATION_LABELS.keys()
        )

        chart_df = df[
            ["fiscal_year", *columns]
        ].copy()

        # 元データ：10億円 → 兆円
        for column in columns:
            chart_df[column] = (
                chart_df[column] / 1000
            )

        chart_df = chart_df.melt(
            id_vars="fiscal_year",
            var_name="component",
            value_name="value",
        )

        chart_df["component"] = (
            chart_df["component"]
            .map(INCOME_GENERATION_LABELS)
        )

        chart = (
            alt.Chart(chart_df)
            .mark_line(
                strokeWidth=2.5,
            )
            .encode(
                x=alt.X(
                    "fiscal_year:Q",
                    title="年度",
                    axis=alt.Axis(
                        format="d",
                    ),
                ),
                y=alt.Y(
                    "value:Q",
                    title="名目額（兆円）",
                    scale=alt.Scale(
                        zero=False,
                    ),
                ),
                color=alt.Color(
                    "component:N",
                    title="所得項目",
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
                        "value:Q",
                        title="名目額（兆円）",
                        format=".1f",
                    ),
                ],
            )
            .properties(
                height=430,
            )
            .interactive()
        )

        return chart

    raise ValueError(
        f"未対応の表示モードです: {display_mode}"
    )


def prepare_sector_net_lending_chart_data(
    amount_df: pd.DataFrame,
    ratio_df: pd.DataFrame,
    selected_sectors: list[str],
    display_mode: str,
) -> pd.DataFrame:
    """制度部門別純貸出のグラフ用longデータを作る。"""

    reverse_labels = {
        label: column
        for column, label in SECTOR_LABELS.items()
    }

    selected_columns = [
        reverse_labels[sector]
        for sector in selected_sectors
    ]

    source_df = (
        ratio_df
        if display_mode == "GDP比"
        else amount_df
    )

    chart_df = source_df[
        [
            "fiscal_year",
            *selected_columns,
        ]
    ].copy()

    if display_mode == "名目額":
        for column in selected_columns:
            chart_df[column] = (
                chart_df[column] / 1000
            )

    chart_df = chart_df.melt(
        id_vars="fiscal_year",
        var_name="sector_code",
        value_name="value",
    )

    chart_df["sector"] = (
        chart_df["sector_code"]
        .map(SECTOR_LABELS)
    )

    return chart_df


def create_sector_net_lending_chart(
    amount_df: pd.DataFrame,
    ratio_df: pd.DataFrame,
    selected_sectors: list[str],
    display_mode: str,
) -> alt.Chart:
    """制度部門別純貸出・純借入の時系列グラフを作る。"""

    chart_df = (
        prepare_sector_net_lending_chart_data(
            amount_df=amount_df,
            ratio_df=ratio_df,
            selected_sectors=selected_sectors,
            display_mode=display_mode,
        )
    )

    if display_mode == "GDP比":
        y_title = "GDP比（%）"
        tooltip_title = "GDP比"
        tooltip_format = ".1f"
    elif display_mode == "名目額":
        y_title = "名目額（兆円）"
        tooltip_title = "名目額（兆円）"
        tooltip_format = ".1f"
    else:
        raise ValueError(
            f"未対応の表示モードです: {display_mode}"
        )

    lines = (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(
                    format="d",
                ),
            ),
            y=alt.Y(
                "value:Q",
                title=y_title,
            ),
            color=alt.Color(
                "sector:N",
                title="制度部門",
            ),
            tooltip=[
                alt.Tooltip(
                    "fiscal_year:Q",
                    title="年度",
                    format="d",
                ),
                alt.Tooltip(
                    "sector:N",
                    title="制度部門",
                ),
                alt.Tooltip(
                    "value:Q",
                    title=tooltip_title,
                    format=tooltip_format,
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "value": [0.0],
                }
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
        )
        .encode(
            y="value:Q",
        )
    )

    return (
        (lines + zero_line)
        .properties(
            height=450,
        )
        .interactive()
    )


def create_household_primary_income_chart(
    df: pd.DataFrame,
    display_mode: str,
) -> alt.Chart:
    """家計第1次所得の構成を表示する。"""

    if display_mode == "構成比":
        labels = HOUSEHOLD_PRIMARY_RATIO_LABELS
        y_title = "第1次所得比（%）"

    elif display_mode == "名目額":
        labels = HOUSEHOLD_PRIMARY_AMOUNT_LABELS
        y_title = "名目額（兆円）"

    else:
        raise ValueError(
            f"未対応の表示モードです: {display_mode}"
        )

    columns = list(labels.keys())

    chart_df = df[
        ["fiscal_year", *columns]
    ].copy()

    if display_mode == "名目額":
        for column in columns:
            chart_df[column] = (
                chart_df[column] / 1000
            )

    chart_df = chart_df.melt(
        id_vars="fiscal_year",
        var_name="component",
        value_name="value",
    )

    chart_df["component"] = (
        chart_df["component"].map(labels)
    )

    if display_mode == "構成比":
        return (
            alt.Chart(chart_df)
            .mark_area(
                opacity=0.85,
            )
            .encode(
                x=alt.X(
                    "fiscal_year:Q",
                    title="年度",
                    axis=alt.Axis(format="d"),
                ),
                y=alt.Y(
                    "value:Q",
                    title=y_title,
                    stack="zero",
                    scale=alt.Scale(
                        domain=[0, 100],
                    ),
                ),
                color=alt.Color(
                    "component:N",
                    title="所得項目",
                    sort=[
                        "雇用者報酬",
                        "営業余剰・混合所得",
                        "純財産所得",
                    ],
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
                        "value:Q",
                        title="構成比",
                        format=".2f",
                    ),
                ],
            )
            .properties(
                height=420,
            )
        )

    return (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(format="d"),
            ),
            y=alt.Y(
                "value:Q",
                title=y_title,
                scale=alt.Scale(
                    zero=False,
                ),
            ),
            color=alt.Color(
                "component:N",
                title="所得項目",
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
                    "value:Q",
                    title="名目額（兆円）",
                    format=".1f",
                ),
            ],
        )
        .properties(
            height=420,
        )
        .interactive()
    )


def create_disposable_income_ratio_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """第1次所得に対する純可処分所得比率を表示する。"""

    chart_df = df[
        [
            "fiscal_year",
            "disposable_income_to_primary_income_ratio",
        ]
    ].copy()

    return (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.5,
            point=True,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(format="d"),
            ),
            y=alt.Y(
                "disposable_income_to_primary_income_ratio:Q",
                title="可処分所得 / 第1次所得（%）",
                scale=alt.Scale(
                    zero=False,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "fiscal_year:Q",
                    title="年度",
                    format="d",
                ),
                alt.Tooltip(
                    "disposable_income_to_primary_income_ratio:Q",
                    title="比率",
                    format=".2f",
                ),
            ],
        )
        .properties(
            height=350,
        )
        .interactive()
    )


def create_redistribution_components_chart(
    df: pd.DataFrame,
    display_mode: str,
) -> alt.Chart:
    """税・社会負担・給付等を正負方向で表示する。"""

    if display_mode == "第1次所得比":
        labels = REDISTRIBUTION_RATIO_LABELS
        y_title = "第1次所得比（%）"
        value_format = ".2f"

    elif display_mode == "名目額":
        labels = REDISTRIBUTION_AMOUNT_LABELS
        y_title = "名目額（兆円）"
        value_format = ".1f"

    else:
        raise ValueError(
            f"未対応の表示モードです: {display_mode}"
        )

    columns = list(labels.keys())

    chart_df = df[
        ["fiscal_year", *columns]
    ].copy()

    if display_mode == "名目額":
        for column in columns:
            chart_df[column] = (
                chart_df[column] / 1000
            )

    # 家計から支払われる項目は負方向に表示する。
    paid_columns = (
        [
            "current_taxes_ratio",
            "net_social_contributions_ratio",
        ]
        if display_mode == "第1次所得比"
        else [
            "current_taxes_paid",
            "net_social_contributions_paid",
        ]
    )

    for column in paid_columns:
        chart_df[column] = (
            -chart_df[column]
        )

    chart_df = chart_df.melt(
        id_vars="fiscal_year",
        var_name="component",
        value_name="value",
    )

    chart_df["component"] = (
        chart_df["component"].map(labels)
    )

    lines = (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.3,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(format="d"),
            ),
            y=alt.Y(
                "value:Q",
                title=y_title,
            ),
            color=alt.Color(
                "component:N",
                title="移転項目",
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
                    "value:Q",
                    title=y_title,
                    format=value_format,
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {"value": [0.0]}
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
        )
        .encode(
            y="value:Q",
        )
    )

    return (
        (lines + zero_line)
        .properties(
            height=400,
        )
        .interactive()
    )


def create_household_saving_rate_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """家計貯蓄率を表示する。"""

    chart_df = df[
        [
            "fiscal_year",
            "calculated_saving_rate",
        ]
    ].copy()

    line = (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.5,
            point=True,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(format="d"),
            ),
            y=alt.Y(
                "calculated_saving_rate:Q",
                title="家計貯蓄率（%）",
            ),
            tooltip=[
                alt.Tooltip(
                    "fiscal_year:Q",
                    title="年度",
                    format="d",
                ),
                alt.Tooltip(
                    "calculated_saving_rate:Q",
                    title="貯蓄率",
                    format=".2f",
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {"value": [0.0]}
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
        )
        .encode(
            y="value:Q",
        )
    )

    return (
        (line + zero_line)
        .properties(
            height=400,
        )
        .interactive()
    )


def create_household_net_saving_chart(
    df: pd.DataFrame,
) -> alt.Chart:
    """家計純貯蓄額を兆円で表示する。"""

    chart_df = df[
        [
            "fiscal_year",
            "net_saving",
        ]
    ].copy()

    chart_df["net_saving_trillion"] = (
        chart_df["net_saving"] / 1000
    )

    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "fiscal_year:O",
                title="年度",
                axis=alt.Axis(
                    labelAngle=-45,
                ),
            ),
            y=alt.Y(
                "net_saving_trillion:Q",
                title="純貯蓄（兆円）",
            ),
            tooltip=[
                alt.Tooltip(
                    "fiscal_year:O",
                    title="年度",
                ),
                alt.Tooltip(
                    "net_saving_trillion:Q",
                    title="純貯蓄（兆円）",
                    format=".1f",
                ),
            ],
        )
        .properties(
            height=350,
        )
    )


def create_nonfinancial_capital_account_chart(
    df: pd.DataFrame,
    display_mode: str,
) -> alt.Chart:
    """非金融法人企業の資本勘定を表示する。"""

    if display_mode == "GDP比":
        labels = NONFINANCIAL_CAPITAL_RATIO_LABELS
        y_title = "GDP比（%）"
        value_format = ".2f"

    elif display_mode == "名目額":
        labels = NONFINANCIAL_CAPITAL_LABELS
        y_title = "名目額（兆円）"
        value_format = ".1f"

    else:
        raise ValueError(
            f"未対応の表示モードです: {display_mode}"
        )

    columns = list(labels.keys())

    chart_df = df[
        ["fiscal_year", *columns]
    ].copy()

    if display_mode == "名目額":
        for column in columns:
            chart_df[column] = (
                chart_df[column] / 1000
            )

    # 純資本形成は純貸出から控除されるため、
    # 恒等式上の寄与方向に合わせて負符号で表示する。
    capital_formation_column = (
        "net_capital_formation_ratio"
        if display_mode == "GDP比"
        else "net_capital_formation"
    )

    chart_df[capital_formation_column] = (
        -chart_df[capital_formation_column]
    )

    chart_df = chart_df.melt(
        id_vars="fiscal_year",
        var_name="component",
        value_name="value",
    )

    chart_df["component"] = (
        chart_df["component"].map(labels)
    )

    lines = (
        alt.Chart(chart_df)
        .mark_line(
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "fiscal_year:Q",
                title="年度",
                axis=alt.Axis(
                    format="d",
                ),
            ),
            y=alt.Y(
                "value:Q",
                title=y_title,
            ),
            color=alt.Color(
                "component:N",
                title="項目",
                sort=[
                    "純貯蓄",
                    "純資本移転",
                    "純資本形成（控除）",
                    "純貸出",
                ],
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
                    "value:Q",
                    title=y_title,
                    format=value_format,
                ),
            ],
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {"value": [0.0]}
            )
        )
        .mark_rule(
            strokeDash=[5, 5],
        )
        .encode(
            y="value:Q",
        )
    )

    return (
        (lines + zero_line)
        .properties(
            height=430,
        )
        .interactive()
    )


def create_net_lending_decomposition_chart(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> alt.Chart:
    """非金融法人企業の純貸出GDP比変化を要因分解する。"""

    chart_df = df.loc[
        (df["start_year"] == start_year)
        & (df["end_year"] == end_year)
    ].copy()

    if chart_df.empty:
        raise ValueError(
            f"{start_year}→{end_year}年度の"
            "分解結果がありません。"
        )

    chart_df["component_label"] = (
        chart_df["component"]
        .map(NET_LENDING_DECOMPOSITION_LABELS)
    )

    if chart_df["component_label"].isna().any():
        unknown = chart_df.loc[
            chart_df["component_label"].isna(),
            "component",
        ].tolist()

        raise ValueError(
            f"未定義の分解要因があります: {unknown}"
        )

    chart_df["direction"] = (
        chart_df["contribution_pt"]
        .ge(0)
        .map(
            {
                True: "押し上げ",
                False: "押し下げ",
            }
        )
    )

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "component_label:N",
                title=None,
                sort=[
                    "純貯蓄",
                    "純資本移転",
                    "純資本形成",
                ],
            ),
            y=alt.Y(
                "contribution_pt:Q",
                title="純貸出GDP比への寄与（pt）",
            ),
            color=alt.Color(
                "direction:N",
                title="寄与方向",
            ),
            tooltip=[
                alt.Tooltip(
                    "component_label:N",
                    title="要因",
                ),
                alt.Tooltip(
                    "contribution_pt:Q",
                    title="寄与",
                    format="+.2f",
                ),
            ],
        )
    )

    labels = (
        alt.Chart(chart_df)
        .mark_text(
            dy=-10,
            fontSize=13,
        )
        .encode(
            x=alt.X(
                "component_label:N",
                sort=[
                    "純貯蓄",
                    "純資本移転",
                    "純資本形成",
                ],
            ),
            y="contribution_pt:Q",
            text=alt.Text(
                "contribution_pt:Q",
                format="+.2f",
            ),
        )
    )

    zero_line = (
        alt.Chart(
            pd.DataFrame(
                {"value": [0.0]}
            )
        )
        .mark_rule()
        .encode(
            y="value:Q",
        )
    )

    return (
        (bars + labels + zero_line)
        .properties(
            height=320,
        )
    )
